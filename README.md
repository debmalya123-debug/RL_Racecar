# Evolutionary Reinforcement Learning based RaceCar Simulation

This repository implements a hybrid control architecture for autonomous agents in a continuous environment, combining **On-Policy Temporal Difference Learning (SARSA)** with **Genetic Algorithms (GA)**.

## 📖 Theoretical Framework

### Problem Formulation

The environment is modeled as a Partially Observable Markov Decision Process (POMDP) where the agent aims to maximize distance traveled $\sum_{t=0}^{T} d_t$ within a racing track environment.

* **State Space $\mathcal{S}$**: 6-dimensional tuple $(d_1, d_2, d_3, d_4, d_5, v)$, where $d_i$ represents discretized LIDAR sensor distances and $v$ is the agent's velocity.
* **Action Space $\mathcal{A}$**: Discrete set of control tuples $(\delta, \tau)$, where $\delta$ is steering angle and $\tau$ is throttle.
* **Reward Function $R(s,a)$**:

$$R = (v \cdot \lambda) - \beta \cdot |p_{\text{center}}| - \eta \cdot \mathbb{I}_{\text{crash}}$$

Where:
* $\lambda$ rewards speed.
* $\beta$ penalizes deviation from the centerline $p_{\text{center}}$.
* $\eta$ is a large penalty for collision.

### 1. Lifetime Learning: SARSA

Agents utilize SARSA (State-Action-Reward-State-Action) to approximate the optimal value function $Q^*(s,a)$. Unlike Q-Learning, SARSA is an **on-policy** algorithm, meaning it updates the Q-value based on the action actually executed by the policy, incorporating the agent's exploration noise into the learning process.

**Update Rule:**
$$Q(S_t, A_t) \leftarrow Q(S_t, A_t) + \alpha [R_{t+1} + \gamma Q(S_{t+1}, A_{t+1}) - Q(S_t, A_t)]$$

This component enables the agent to develop reactive behaviors (avoidance reflexes) within a single generation.

### 2. Generational Optimization: Genetic Algorithm

To navigate the non-convex optimization landscape and avoid local optima (e.g., safe but static policies), the system employs an evolutionary outer loop.

- **Selection**: Truncation selection retains the top $k$% of agents based on total distance traveled.
- **Crossover & Mutation**: Selected agents are cloned to repopulate the environment.
  - **Weight Perturbation**: $Q'(s,a) = Q(s,a) + \mathcal{N}(0, \sigma)$
  - **Hyperparameter Drift**: $\epsilon' = \epsilon + \mathcal{U}(-\delta, \delta)$

This component optimizes global strategy and hyperparameters over successive generations.

---

## 🛠️ Implementation Details

The architecture is decoupled into a headless physics backend and a decoupled visualization frontend.

### Backend (Python/Pygame)

The core simulation runs on a headless `pygame` instance.

- **Physics**: Rigid body dynamics with simple friction and momentum.
- **Sensor Simulation**: Ray-casting implementation for LIDAR emulation.
- **Agent Logic**: `SarsaAgent` class implements the tabular RL and epsilon-greedy policies.

### Frontend (JavaScript/Canvas)

Real-time state visualization via WebSocket connection.

- **Rendering**: HTML5 Canvas with custom transformation matrices for pseudo-3D perspective.
- **Communication**: `Flask-SocketIO` event emitters synchronize state at 30Hz.

### Project Structure

```bash
RL_Racecar/
├── web_server.py       # Simulation Loop & WebSocket Handler
├── agent.py            # SARSA Implementation & Q-Table Management
├── car.py              # Physics & Sensor Ray-casting
├── track.py            # Collision Masks & Geometry
└── web_viz/            # Frontend Client
```

---

## Usage

### Prerequisites

- Python 3.8+

### Setup & Run

```bash
# 1. Clone & Env Setup
git clone <repo_url>
cd RL_Racecar
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# 2. Install Dependencies
pip install -r requirements.txt

# 3. Execution
python web_server.py
```

Access the dashboard at **`http://localhost:5001`**.

### Controls

- **Speed Slider**: Adjusts physics steps per rendering frame (up to 50x).
- **Reset**: Manually triggers a hard reset of the population and Q-tables.

---

## Credits

**Developer**: Debmalya Paul
- **GitHub**: [@debmalya123-debug](https://github.com/debmalya123-debug)
