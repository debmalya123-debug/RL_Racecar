import random
import numpy as np

# Steering, Throttle
ACTIONS = [
    (0, 0),    # Coast
    (0, 1),    # Forward
    (-0.5, 1), # Soft Left
    (0.5, 1),  # Soft Right
    (-1, 1),   # Hard Left
    (1, 1),    # Hard Right
]

class SarsaAgent:
    def __init__(self):
        self.q = {}
        self.alpha = 0.1
        self.gamma = 0.95
        self.epsilon = 0.2

    def get_state(self, car):
        # State: (Sensor1, Sensor2, Sensor3, Sensor4, Sensor5, Speed)
        # Discretize sensors: 0-10 buckets
        
        state_parts = []
        for r_len, _ in car.radars:
            state_parts.append(int(r_len / 40)) # 5 buckets for 200 max range
            
        state_parts.append(int(car.speed))
        
        # We don't really need absolute X/Y or angle if we have relative sensors!
        return tuple(state_parts)

    def choose_action(self, state):
        if random.random() < self.epsilon:
            return random.randint(0, len(ACTIONS) - 1)

        qs = [self.q.get((state, a), 0) for a in range(len(ACTIONS))]
        return int(np.argmax(qs))

    def update(self, s, a, r, s2, a2):
        old = self.q.get((s, a), 0)
        next_q = self.q.get((s2, a2), 0)
        self.q[(s, a)] = old + self.alpha * (r + self.gamma * next_q - old)

    def clone_mutate(self):
        child = SarsaAgent()
        child.q = self.q.copy()
        
        # Mutate Q-values
        for k in child.q:
            if random.random() < 0.05:
                child.q[k] += random.uniform(-0.5, 0.5)
                
        # Mutate Hyperparameters
        child.epsilon = max(0.01, min(0.5, self.epsilon + random.uniform(-0.05, 0.05)))
        
        return child
