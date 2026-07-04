import tkinter as tk
from tkinter import ttk
import numpy as np
import os

# --- 1. DIGITAL TWIN CONFIGURATION ---
FILENAME = "cmd_joints.txt"

# Default initial pose for the simulator (in degrees)
INITIAL_POSE_DEG = [0, 29, -72, 0, 0, 0]

# Joint movement limits (in degrees)
JOINT_RANGES = [
    (-90, 90),    # J1
    (-50, 30),    # J2
    (-50, 120),  # J3
    (-90, 90),    # J4
    (-80, 80),    # J5
    (-50, 50)     # J6
]

# --- 2. GRAPHICAL USER INTERFACE CREATION (Tkinter) ---
root = tk.Tk()
root.title("Control Panel - Niryo Digital Twin (Simulation)")
root.geometry("480x520")
root.configure(bg='#222222')

style = ttk.Style()
style.configure("TLabel", foreground="white", background="#222222", font=("Arial", 11))

title_lbl = ttk.Label(root, text="Digital Twin Control (MuJoCo)", font=("Arial", 14, "bold"))
title_lbl.pack(pady=15)

sliders = []
label_values = []

# Hidden global variable to retain gripper state (0.020 = Closed by default in this standalone mapping)
current_gripper_val = 0.020

def send_to_txt(*args):
    """Convert slider values to radians and update the MuJoCo text file"""
    rad_vals = []
    
    # Process the 6 arm joints
    for i in range(6):
        deg = sliders[i].get()
        label_values[i].config(text=f"{int(deg)}°")
        rad_vals.append(np.radians(deg))
    
    # Append the current gripper value determined by the buttons
    rad_vals.append(current_gripper_val)
    
    # Format a single comma-separated line for the MuJoCo parser
    line = ",".join([f"{x:.6f}" for x in rad_vals])
    try:
        with open(FILENAME, "w") as f:
            f.write(line)
    except Exception as e:
        print(f"Error writing to simulation file: {e}")

# Create Sliders for the 6 joints
joint_names = ["Joint 1", "Joint 2", "Joint 3", "Joint 4", "Joint 5", "Joint 6"]
for i in range(6):
    frame = tk.Frame(root, bg='#222222', pady=5)
    frame.pack(fill='x', padx=20)
    
    lbl = ttk.Label(frame, text=joint_names[i], width=10)
    lbl.pack(side='left')
    
    slider = tk.Scale(frame, from_=JOINT_RANGES[i][0], to=JOINT_RANGES[i][1], orient='horizontal', 
                      bg='#333333', fg='white', highlightbackground='#222222',
                      troughcolor='#555555', command=send_to_txt)
    
    slider.set(INITIAL_POSE_DEG[i])  
    slider.pack(side='left', fill='x', expand=True, padx=10)
    sliders.append(slider)
    
    val_lbl = ttk.Label(frame, text=f"{INITIAL_POSE_DEG[i]}°", width=6)
    val_lbl.pack(side='right')
    label_values.append(val_lbl)

# --- 3. DISCRETE GRIPPER CONTROL PANEL ---
frame_g_ctrl = tk.Frame(root, bg='#222222', pady=15)
frame_g_ctrl.pack(fill='x', padx=20)

lbl_g_title = ttk.Label(frame_g_ctrl, text="Gripper:", width=10)
lbl_g_title.pack(side='left')

def close_gripper():
    """Modifies the gripper state to closed (0.020) and updates the txt file"""
    global current_gripper_val
    current_gripper_val = 0.020
    val_lbl_g.config(text="0.020 (Closed)")
    send_to_txt()

def open_gripper():
    """Modifies the gripper state to open (0.000) and updates the txt file"""
    global current_gripper_val
    current_gripper_val = 0.000
    val_lbl_g.config(text="0.000 (Open)")
    send_to_txt()

# Action buttons to open and close the gripper
btn_close_g = tk.Button(frame_g_ctrl, text="Close Gripper", width=12, highlightbackground='#222222', command=close_gripper)
btn_close_g.pack(side='left', padx=5, expand=True, fill='x')

btn_open_g = tk.Button(frame_g_ctrl, text="Open Gripper", width=12, highlightbackground='#222222', command=open_gripper)
btn_open_g.pack(side='left', padx=5, expand=True, fill='x')

# Current gripper status indicator (Initialized to match current_gripper_val fallback text)
val_lbl_g = ttk.Label(frame_g_ctrl, text="0.020 (Closed)", width=15, anchor="center")
val_lbl_g.pack(side='right', padx=5)

# --- 4. SAFE CLOSURE AND STARTUP ---
def on_close():
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

# Write initial configuration values to the text file upon starting the interface
send_to_txt()

root.mainloop()