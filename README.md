# Unified Control Framework for Niryo Ned2 in Mujoco: Digital Twin & Real Hardware


#### This project provides a complete **Digital Twin and Hardware Control ecosystem** for the **Niryo Ned2** robotic arm. It bridges the gap between visual simulation inside **MuJoCo** and real-world physical execution using the `pyniryo` API, enabling standalone simulation, live interactive testing, and automated pick-and-place routines. The stl files used in this project are from the [Niryo Ned2 GitHub repository](https://github.com/NiryoRobotics/ned2).

---

## 🛠️ Project Structure & Component Overview

The repository consists of modular Python scripts and simulation definitions that handle individual layers of the robotic application:

| File | Type | Description |
| :--- | :--- | :--- |
| **`mujocoSimulation.py`** | MuJoCo Engine | The passive viewer simulation loop. Parses `cmd_joints.txt` in real time, rendering joint states and managing dual-gripper behaviors. |
| **`pickandplaceReal.py`** | Automated Routine | Executes a complete hardware-synchronized pick-and-place routine with linear trajectory interpolation for smooth visual-to-physical transitions. |
| **`sim2realSliders.py`** | Manual Unified GUI | A Tkinter control panel that connects to the real robot while simultaneously publishing inverted and swapped joint vectors to MuJoCo. |
| **`pickandplaceSim.py`** | Automated Simulation | Executes the pre-programmed pick-and-place sequence using visual joint interpolation directly inside the standalone simulator. |
| **`justsim.py`** | Standalone GUI | A local manual control interface meant purely for simulation testing without requiring physical robot hardware connections. |
| **`niryo.xml`** | Robot Model | The standardized MuJoCo XML definition compiling the links, meshes, joints, and collision bounds of the Niryo Ned2. |
| **`cmd_joints.txt`** | IPC Pipe | A lightweight shared file acting as an Inter-Process Communication (IPC) vector, piping calculated joint radians from the GUIs to MuJoCo. |

---

## ⚙️ Architecture & Coordinate Mapping

To ensure exact behavioral parity between the physical kinematics of the Niryo Ned2 and the visual representation inside MuJoCo, the control scripts dynamically process and translate joint metrics:

* **Inter-Process Communication:** Control interfaces convert user-facing degree inputs into radians, writing a single comma-separated text string to `cmd_joints.txt`.
* **Joint Swapping ($J_4 \leftrightarrow J_5$):** To account for unique kinematic link configurations within the XML asset layout, the unified controllers map physical Joint 5 values into the MuJoCo index 4 register and physical Joint 4 values into index 5.
* **Orientation Inversion:** The hardware value for Joint 5 is mathematically inverted ($-1 \times \text{value}$) before rendering in MuJoCo to guarantee directional synchronization.

---

## 🚀 Getting Started & Execution Modes

Ensure your Python environment contains the necessary dependencies:
```bash
pip install numpy mujoco pyniryo tkinter
```

Launch the control interface (In a separate terminal session):
* For manual slider control:
     ```bash
     python justsim.py
     ```
   * For the automated smooth trajectory routine:
     ```bash
     python pickandplaceSim.py
     ```

### Mode 2: Unified Digital Twin (Hardware Connected)
To command the physical Niryo Ned2 robot while seeing it mirrored simultaneously in your digital simulation twin environment:

1. **Network Configuration:**
   Connect to the hotspot of niryo-ned2. **(Password: niryorobot)**
2. **Boot up the passive simulator viewport:**
   ```bash
   python mujocoSimulation.py
    ```
(in macos you may need to run `mjpython mujocoSimulation.py`)

3. **Run the tracking application dashboards (In a separate terminal session):**

   ![Sim2Real Dashboard](assets/sim2real.png)

   * For interactive real-time visual mirroring and manual adjustments:
     ```bash
     python sim2realSliders.py
     ```

    A visualization of this mode is shown in the following gif:

    ![Sim2Real GIF](assets/sim2real.gif)

   * For synchronized execution of the physical pick-and-place sequence:
     ```bash
     python pickandplaceReal.py
     ```

## 🔒 Safety & System Defaults

* **Fallback Protocol:** If the `pyniryo` client fails to establish a handshake connection with IP address `10.10.10.10`, hardware calls are bypassed gracefully, allowing scripts to safe-start directly into a **Virtual Simulation Only** environment.
xww