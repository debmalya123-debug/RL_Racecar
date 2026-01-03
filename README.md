# 🏎️ RL-Based Racecar Web Visualizer

A real-time web visualizer for a Reinforcement Learning (RL) agent learning to drive a racecar on a custom track. The project features a Python backend running the physics simulation and a polished JavaScript frontend for 3D-styled visualization.

## 🌟 Features

- **Real-Time Simulation**: Backend physics engine (Pygame) running a genetic algorithm/SARSA based agent.
- **Web Visualization**: Smooth HTML5 Canvas rendering with a "Professional 3D" aesthetic.
- **Active LIDAR Rays**: Visualizes what the agent sees with dynamic color-coded sensor beams and impact markers.
- **Car Trails & Crash Effects**: Path tracking and particle explosions for crashes.
- **Speed Control**: Adjustable simulation speed (1x - 50x) via the frontend slider.
- **Learning Agents**: Watch the cars evolve from crashing into walls to driving perfect laps over generations.

## 🛠️ Tech Stack

- **Backend**: Python, Flask, Flask-SocketIO, Pygame (Headless), Numpy.
- **Frontend**: HTML5, CSS3, JavaScript (Socket.IO Client).
- **Deployment**: Ready for Render, Heroku, or other container-based platforms.

## 🚀 How to Run Locally

1.  **Clone the repository**:

    ```bash
    git clone <your-repo-url>
    cd RL_Racecar
    ```

2.  **Create and activate a virtual environment**:

    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Mac/Linux
    source .venv/bin/activate
    ```

3.  **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the web server**:

    ```bash
    python web_server.py
    ```

5.  **View the Simulation**:
    Open your browser and navigate to `http://localhost:5001`.

## 🧠 How It Works: The Algorithm

This project uses a **Hybrid Evolutionary Reinforcement Learning** approach, combining **SARSA** (on-policy TD learning) with a **Genetic Algorithm**.

### 1. SARSA (State-Action-Reward-State-Action)

During the race, each car acts as an independent agent learning in real-time.

- **State**: The agent perceives the track using 5 LIDAR rays (distances) and its current speed.
- **Action**: It chooses steering (Left, Right, Straight) and throttle (Accelerate, Brake) based on its Q-table.
- **Learning**: At every time step, the agent updates its Q-values using the SARSA update rule:
  $$Q(S, A) \leftarrow Q(S, A) + \alpha [R + \gamma Q(S', A') - Q(S, A)]$$
  This allows the car to immediately learn from mistakes (e.g., hitting a wall) and successes (driving fast) within its own lifetime.

### 2. Genetic Algorithm (Evolution)

To prevent agents from getting stuck in local optima, we apply evolutionary pressure at the end of each generation (when all cars crash or time runs out):

- **Selection**: The top performing cars (based on distance traveled) are selected as "parents".
- **Elitism**: The absolute best agent is carried over unchanged to the next generation to ensure performance never regresses.
- **Mutation**: New agents are created by cloning the parents and slightly mutating their "brains" (exploration parameters or Q-values).

This combination allows for rapid convergence: **SARSA** fine-tunes driving behavior frame-by-frame, while **Evolution** discovers better overall driving strategies over generations.

## 🎮 Controls

- **Speed Slider**: Drag the slider at the top of the screen to speed up training (up to 50x) or slow it down for inspection.
