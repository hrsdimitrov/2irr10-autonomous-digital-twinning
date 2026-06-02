# Nitrobot — Mac Demo Branch

> **Note:** This branch is a Mac-compatible demo. Core navigation limitations apply — see below.

---

## ⚠️ Known Issue: Position Drift

**Root cause**

- Nav2 cannot run properly on macOS — likely due to dependency conflicts (e.g. fastcdr version incompatibility). Multiple approaches were attempted without success.
- Without Nav2, the robot has no intelligent path planning or localisation correction. Navigation falls back to a custom Bug0 wall-following controller using raw odometry only.

**Symptoms**

- The robot's actual position in Gazebo diverges significantly from what RViz displays over time.
- The robot occasionally drifts outside the map boundary in RViz.
- In RViz, the robot appears to reach a target zone and the zone correctly turns green — but in Gazebo, the robot may be nowhere near the correct position.

**Impact**

- Beyond the first 2–3 zones, fertilisation positions in Gazebo become increasingly inaccurate.
- RViz visualisation becomes unreliable over time.
- All decision logic, state tracking, and mission control remain fully functional and unaffected.

---

## ✅ What Is Implemented

### 1. Visualisation
- Gazebo and RViz share the same map frame and perspective.
- RViz displays all 44 zones as coloured markers with zone number labels.
- Zones correctly change from red/yellow to green after fertilisation is confirmed.

### 2. Autonomous Decision-Making
- Automatically dispatches target zones one by one; red zones are prioritised over yellow.
- Zones that time out are skipped and deferred — all reachable zones are completed first.
- After the primary pass, all previously skipped zones are retried one by one.
- Publishes `COMPLETE` and stops dispatching once all zones turn green.

### 3. Navigation & Obstacle Avoidance
- Uses a custom Bug0 wall-following controller (Nav2 unavailable on Mac).
- Switches to right-wall-following mode when an obstacle is detected ahead; resumes straight navigation when the path is clear.
- Detects arrival at target zone (within tolerance) and handles timeout-based zone skipping.
- Robot speed tuned for stable navigation.

### 4. Status Monitoring
- Terminal logs show the current target zone, completion feedback, and a running count of completed zones.
- Zones that timed out are tracked in a retry list; they are not counted as complete until successfully fertilised.
- Battery level is reported in real time.
- When battery is depleted, a mission abort signal is published and the robot stops immediately.

> **Not included in this version:** fertiliser refilling and robot recharging are not implemented. The robot operates on a single battery charge with a fixed fertiliser supply for the duration of the mission.
