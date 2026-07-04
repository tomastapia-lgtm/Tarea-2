import tkinter as tk
from tkinter import ttk
import numpy as np
import os
from pyniryo import *

# --- 1. REAL ROBOT CONNECTION AND INITIALIZATION ---
ROBOT_IP = "10.10.10.10"
FILENAME = "cmd_joints.txt"

# Default pose to initialize the UI ONLY if the real robot is powered off or disconnected
FALLBACK_POSE_DEG = [0, 29, -72, 0, 0, 0]

try:
    print(f"Connecting to Niryo Ned2 at {ROBOT_IP}...")
    robot = NiryoRobot(ROBOT_IP)
    robot.calibrate_auto()
    robot.update_tool()
    robot.release_with_tool()
    robot_connected = True
    print("Real robot connected and calibrated successfully!")
except Exception as e:
    print(f"Warning: Could not connect to real robot ({e}). Running in SIMULATION ONLY mode.")
    robot_connected = False

# --- 2. JOINT LIMIT CONFIGURATION IN NATIVE DEGREES ---
JOINT_RANGES = [
    (-90, 90),    # J1
    (-50, 30),    # J2
    (-50, 120),  # J3
    (-90, 90),    # J4
    (-80, 80),    # J5
    (-90, 90)     # J6
]

initial_pose_deg = list(FALLBACK_POSE_DEG)

if robot_connected:
    try:
        joints_rad = robot.get_joints()
        initial_pose_deg = [int(np.degrees(j)) for j in joints_rad]
        print(f"Synchronizing interface with the real hardware pose: {initial_pose_deg}")
    except Exception as e:
        print(f"Could not read the robot's initial pose, using default values: {e}")

# --- 3. GRAPHICAL USER INTERFACE CREATION (Tkinter) ---
root = tk.Tk()
root.title("Unified Control Panel - Niryo Digital Twin")
root.geometry("480x600") # Optimally adjusted height without the slider
root.configure(bg='#222222')

style = ttk.Style()
style.configure("TLabel", foreground="white", background="#222222", font=("Arial", 11))

title_lbl = ttk.Label(root, text="Unified Control (Real + MuJoCo)", font=("Arial", 14, "bold"))
title_lbl.pack(pady=15)

sliders = []
label_values = []

current_gripper_val = 0.020

def send_to_txt(*args):
    """Convert slider positions to radians and SWAP J4 and J5 ONLY for MuJoCo (and invert J5)"""
    ui_rad_vals = []
    for i in range(6):
        deg = sliders[i].get()
        label_values[i].config(text=f"{int(deg)}°")
        ui_rad_vals.append(np.radians(deg))
    
    j5_inverted = -ui_rad_vals[4]
    
    mujoco_joints_rad = [
        ui_rad_vals[0],
        ui_rad_vals[1],
        ui_rad_vals[2],
        ui_rad_vals[3], 
        ui_rad_vals[4],  
        ui_rad_vals[5]
    ]
    
    mujoco_joints_rad.append(current_gripper_val)
    
    line = ",".join([f"{x:.6f}" for x in mujoco_joints_rad])
    try:
        with open(FILENAME, "w") as f:
            f.write(line)
    except Exception:
        pass

# Create Sliders for the 6 Joints
joint_names = ["Joint 1", "Joint 2", "Joint 3", "Joint 4", "Joint 5", "Joint 6"]
for i in range(6):
    frame = tk.Frame(root, bg='#222222', pady=5)
    frame.pack(fill='x', padx=20)
    
    lbl = ttk.Label(frame, text=joint_names[i], width=15)
    lbl.pack(side='left')
    
    slider = tk.Scale(frame, from_=JOINT_RANGES[i][0], to=JOINT_RANGES[i][1], orient='horizontal', 
                      bg='#333333', fg='white', highlightbackground='#222222',
                      troughcolor='#555555', command=send_to_txt)
    
    slider.set(initial_pose_deg[i])  
    slider.pack(side='left', fill='x', expand=True, padx=10)
    sliders.append(slider)
    
    val_lbl = ttk.Label(frame, text=f"{initial_pose_deg[i]}°", width=6)
    val_lbl.pack(side='right')
    label_values.append(val_lbl)

# --- 4. GRIPPER CONTROL PANEL (BUTTONS ONLY) ---
frame_gripper_ctrl = tk.Frame(root, bg='#222222', pady=15)
frame_gripper_ctrl.pack(fill='x', padx=20)

lbl_gripper_real = ttk.Label(frame_gripper_ctrl, text="Gripper Control:", width=15)
lbl_gripper_real.pack(side='left')

# --- 5. BUTTON ACTIONS ---
def close_gripper_real():
    """Closes the physical gripper and updates the text file to close MuJoCo"""
    global current_gripper_val
    if robot_connected:
        try:
            robot.grasp_with_tool()
            print("Real Gripper: Closed successfully!")
        except Exception as e:
            print(f"Error closing the gripper: {e}")
    else:
        print("Simulation mode: Gripper Closed virtually.")
    
    current_gripper_val = 0.020
    val_lbl_g.config(text="0.020 (Closed)")
    send_to_txt()

def open_gripper_real():
    """Opens the physical gripper and updates the text file to open MuJoCo"""
    global current_gripper_val
    if robot_connected:
        try:
            robot.release_with_tool()
            print("Real Gripper: Opened successfully!")
        except Exception as e:
            print(f"Error opening the gripper: {e}")
    else:
        print("Simulation mode: Gripper Opened virtually.")
        
    current_gripper_val = 0.000
    val_lbl_g.config(text="0.000 (Open)")
    send_to_txt()

# Pack the open and close buttons side by side inside the gripper container
btn_close_g = tk.Button(frame_gripper_ctrl, text="Close Gripper", width=12, highlightbackground='#222222', command=close_gripper_real)
btn_close_g.pack(side='left', padx=5, expand=True, fill='x')

btn_open_g = tk.Button(frame_gripper_ctrl, text="Open Gripper", width=12, highlightbackground='#222222', command=open_gripper_real)
btn_open_g.pack(side='left', padx=5, expand=True, fill='x')

# Dynamic status label showing the value injected into MuJoCo
val_lbl_g = ttk.Label(frame_gripper_ctrl, text="0.020 (Closed)", width=15, anchor="center")
val_lbl_g.pack(side='right', padx=5)


def move_robot():
    """Takes the native values from the sliders and moves the real robot directly"""
    joints_rad = [np.radians(slider.get()) for slider in sliders]
    
    if robot_connected:
        try:
            robot.move_joints(joints_rad)
            print("Real Robot moved successfully in native mode!")
        except Exception as e:
            print(f"Error moving the real robot: {e}")
    else:
        print("Simulation mode active: Real robot is not connected.")
    
    send_to_txt()

def refresh():
    """Reads the hardware pose in native order and reflects it directly on the sliders"""
    if robot_connected:
        try:
            joints_rad = robot.get_joints()
            for i in range(6):
                deg_val = np.degrees(joints_rad[i])
                deg_val = max(JOINT_RANGES[i][0], min(deg_val, JOINT_RANGES[i][1]))
                sliders[i].set(int(deg_val))
            send_to_txt()
        except Exception as e:
            print(f"Error reading the hardware: {e}")
    else:
        print("No real robot connected to read its pose from.")

# Bottom control buttons (General Movement and Pose Reading)
frame_buttons = tk.Frame(root, bg='#222222', pady=15)
frame_buttons.pack()

btn_move = tk.Button(frame_buttons, text="Move Arm", width=15, highlightbackground='#222222', command=move_robot)
btn_move.pack(pady=4)

btn_read = tk.Button(frame_buttons, text="Read Current Pose", width=20, highlightbackground='#222222', command=refresh)
btn_read.pack(pady=4)

# --- 6. SAFE SHUTDOWN ---
def on_close():
    if robot_connected:
        robot.close_connection()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

# Write initial state to text file before entering the main loop
send_to_txt()

root.mainloop()