import threading
import time
import traceback
import pygame
import math
import random
import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

# Import existing game logic
from track import Track
from car import Car
from agent import SarsaAgent, ACTIONS

app = Flask(__name__, template_folder='web_viz/templates', static_folder='web_viz/static')
# Use threading for Windows compatibility reliability
socketio = SocketIO(app, async_mode='threading')

# Headless Pygame for Server
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init() 

# --- Simulation State ---
POP_SIZE = 5
track = Track()
agents = [SarsaAgent() for _ in range(POP_SIZE)]
cars = [Car((0,0,0)) for _ in range(POP_SIZE)] # Colors handled by frontend
generation = 1
alive = POP_SIZE
steps = 0
max_steps = 1500

sim_running = True
steps_per_frame = 1 
paused = False
reset_signal = False # Thread-safe flag

COLORS = [
    "#FF0055", "#00FFFF", "#FFFF00", "#39FF14", "#FF00FF", "#FF8000",
    "#8000FF", "#0080FF", "#FFFFFF", "#64FF64", "#FF6464", "#6464FF"
]

@socketio.on('set_speed')
def handle_set_speed(data):
    global steps_per_frame
    try:
        steps_per_frame = int(data['speed'])
        print(f"Speed set to {steps_per_frame}x")
    except:
        pass

@socketio.on('toggle_pause')
def handle_pause():
    global paused
    paused = not paused
    print(f"Simulation Paused: {paused}")
    socketio.emit('pause_state', {'paused': paused})

@socketio.on('restart_sim')
def handle_restart():
    global reset_signal
    reset_signal = True
    print("Restart Signal Received")

def perform_hard_reset():
    global cars, alive, steps, generation, agents
    print("Executing Hard Reset...")
    
    # 1. Reset Counters
    generation = 1
    steps = 0
    
    # 2. Reset Agents & Cars (Wipe Brains)
    agents = [SarsaAgent() for _ in range(POP_SIZE)]
    cars = [Car((0,0,0)) for _ in range(POP_SIZE)]
    alive = POP_SIZE
    
    # 3. Notify Frontend
    socketio.emit('hard_reset', {'generation': 1})

def reset_generation():
    global cars, alive, steps, generation, agents
    
    # Evolution
    if generation > 1:
        ranked = sorted(zip(agents, cars), key=lambda x: x[1].distance, reverse=True)
        best_agent = ranked[0][0]
        best_dist = ranked[0][1].distance
        
        print(f"Gen {generation} Complete. Best Dist: {best_dist:.1f}")
        
        # Emit Log Data
        socketio.emit('gen_log', {
            'generation': generation,
            'distance': round(best_dist, 1),
            'epsilon': round(best_agent.epsilon, 3)
        })
        
        # Elitism & Mutation using top 3 strategy
        new_agents = []
        # 1. Elitism: Keep best exact
        best_clone = best_agent.clone_mutate()
        best_clone.epsilon = best_agent.epsilon
        new_agents.append(best_clone)
        
        # 2. Selection from top 3
        top_slice = ranked[:3]
        top_agents = [r[0] for r in top_slice]
        
        for _ in range(POP_SIZE - 1):
             if top_agents:
                 parent = random.choice(top_agents)
                 new_agents.append(parent.clone_mutate())
             else:
                 new_agents.append(best_agent.clone_mutate())
             
        agents = new_agents

    # Reset Cars
    cars = [Car((0,0,0)) for _ in range(POP_SIZE)]
    alive = POP_SIZE
    steps = 0
    generation += 1
    
    # Notify frontend of reset
    socketio.emit('reset', {'generation': generation})

def run_simulation():
    global alive, steps, generation, reset_signal
    print("Simulation Thread Started")
    
    prev_states = [None] * POP_SIZE
    prev_actions = [None] * POP_SIZE

    try:
        while True:
            # --- Hard Reset Handling (Thread Safe) ---
            if reset_signal:
                perform_hard_reset()
                prev_states = [None] * POP_SIZE
                prev_actions = [None] * POP_SIZE
                reset_signal = False
                time.sleep(0.5)
                continue

            if not sim_running:
                time.sleep(0.1)
                continue
                
            if paused:
                time.sleep(0.1)
                continue
            
            # --- Multi-Step Physics Loop for Speed ---
            for _ in range(steps_per_frame):
                # Check for interrupt
                if reset_signal:
                    break
                    
                if alive == 0 or steps >= max_steps:
                    reset_generation()
                    time.sleep(0.5)
                    # Reset Learning Buffers
                    prev_states = [None] * POP_SIZE
                    prev_actions = [None] * POP_SIZE
                    break 
                
                steps += 1
                
                for i, (car, agent) in enumerate(zip(cars, agents)):
                    if not car.alive:
                        continue
                        
                    # 1. Sensors
                    car.radars = []
                    sensor_angles = [-1.2, -0.6, 0, 0.6, 1.2] 
                    for angle in sensor_angles:
                        dist = track.get_radar(car.x, car.y, car.angle + angle)
                        car.radars.append((dist, angle))
                    
                    # 2. Agent Action
                    state = agent.get_state(car)
                    action = agent.choose_action(state)
                    steering, throttle = ACTIONS[action]
                    
                    prev_x = car.x
                    car.step(steering, throttle)
                    
                    # 3. Rewards
                    reward = car.speed * 0.5
                    offset = track.get_offset_from_center(car.x, car.y)
                    reward -= offset * 0.1
                    
                    # Correctly strip distance for min check (since radars are tuples)
                    start_dists = [r[0] for r in car.radars]
                    min_sensor = min(start_dists) if start_dists else 200
                    if min_sensor < 15:
                        reward -= 2.0
                    
                    hit = False
                    if track.hit_barrier(car.x, car.y):
                        hit = True
                        reward -= 50
                    elif not track.on_track(car.x, car.y):
                        hit = True
                        reward -= 50
                    
                    if hit:
                        car.alive = False
                        alive -= 1
                        car.crashed_this_frame = True
                    elif track.crossed_finish(prev_x, car.x, car.y):
                        reward += 1000
                        car.distance += 2000
                        car.alive = False
                        alive -= 1

                    # 4. LEARN (Critical Fix)
                    if prev_states[i] is not None:
                         agent.update(
                            prev_states[i], 
                            prev_actions[i], 
                            reward, 
                            state, 
                            action
                         )
                    
                    prev_states[i] = state
                    prev_actions[i] = action
            
            # --- Prepare Data for Frontend (Once per frame) ---
            sim_data = []
            for i, car in enumerate(cars):
                 crashed = getattr(car, 'crashed_this_frame', False)
                 if crashed: 
                     car.crashed_this_frame = False 
                     
                 sim_data.append({
                    'id': i,
                    'x': round(car.x, 1),
                    'y': round(car.y, 1),
                    'angle': round(car.angle, 2),
                    'alive': int(car.alive), 
                    'crashed': crashed,
                    'sensors': car.radars, # Send sensor data for visualizer!
                    'color': COLORS[i % len(COLORS)]
                })
            
            socketio.emit('update', {'cars': sim_data, 'alive': alive, 'steps': steps})
            
            # Frame Delay
            time.sleep(1/30) # 30 updates per second for visuals is enough

    except Exception as e:
        print(f"Simulation Error: {e}")
        traceback.print_exc()

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.start_background_task(run_simulation)
    print("Starting Web Server on port 5001...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
