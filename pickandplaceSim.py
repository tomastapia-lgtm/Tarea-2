import tkinter as tk
from tkinter import ttk
import numpy as np

import os

# --- 1. DIGITAL TWIN CONFIGURATION ---
FILENAME = "cmd_joints.txt"

# Joint movement limits (in degrees)
JOINT_RANGES = [
    (-90, 90), (-50, 30), (-50, 120), (-90, 90), (-80, 80), (-50, 50)
]

# --- 2. OPTIMIZED PICK AND PLACE SEQUENCE (Gripper Discrete Values) ---
# Format: [J1, J2, J3, J4, J5, J6, Gripper]
# Open Gripper = 0.000  |  Closed Gripper = 0.020 
SEQUENCE = [
    {"desc": "1. Home / Initial Position", "pose": [0, 29, -72, 0, 0, 0, 0.000]},
    
    # --- APPROACH PHASE TO OBJECT AT -90° ---
    {"desc": "2. Rotate to Pick Zone (-90°)", "pose": [-90, 30, -72, 0, 0, 0, 0.000]},
    {"desc": "3. Descend to Object", "pose": [-90, -25, -55, 0, 0, 0, 0.000]},
    {"desc": "3.1 Descend to Object - Close", "pose": [-90, -25, -55, 0, 0, 0, 0.020]},
    {"desc": "4. Close Gripper! (Pick)", "pose": [-90, 25, -55, 0, 0, 0, 0.020]},
    {"desc": "5. Lift Arm with Object", "pose": [-90, 30, -26, 0, 0, 0, 0.020]},
    {"desc": " Ir al centro", "pose": [0, 30, -30, 0, 0, 0, 0.020]},
    {"desc": " Desciende", "pose": [0, -25, -30, 0, 0, 0, 0.020]},
    {"desc": " abrir Gripper! (Pick)", "pose": [0, -25, -30, 0, 0, 0, 0.000]},
    {"desc": " Levantar", "pose": [0, 30, -72, 0, 0, 0, 0.000]},
    
      # --- SMOOTH AIR TRANSIT TO 90° ---
    {"desc": "6. High Air Travel (-90° to 90°)", "pose": [90, 30, -72, 0, 0, 0, 0.000]},
    
    # --- DISCHARGE PHASE AT 90° ---
    {"desc": "7. Descend over Place Zone", "pose": [90, -25, -55, 0, 0, 0, 0.000]},
    {"desc": "8. Open Gripper! (Place)", "pose": [90, -25, -55, 0, 0, 0, 0.020]},
    
    # --- RETRACTION AND RETURN ---
    {"desc": "9. Lift and Clear Zone", "pose": [90, 30, -26, 0, 0, 0, 0.020]},
    {"desc": "10. Return to Home", "pose": [0, 30, -30, 0, 0, 0, 0.020]},
    {"desc": " Desciende", "pose": [0, -25, -30, 0, 0, 0, 0.020]},
    {"desc": " abrir Gripper! (Pick)", "pose": [0, -25, -30, 0, 0, 0, 0.000]},
    {"desc": " Levantar", "pose": [0, 30, -72, 0, 0, 0, 0.000]},
]

# --- 3. GRAPHICAL USER INTERFACE CREATION (Tkinter) ---
root = tk.Tk()
root.title("Control Panel - Niryo Ned2 SMOOTH")
root.geometry("480x580")
root.configure(bg='#222222')

style = ttk.Style()
style.configure("TLabel", foreground="white", background="#222222", font=("Arial", 11))

title_lbl = ttk.Label(root, text="Niryo Ned2 - Smooth Trajectory", font=("Arial", 14, "bold"))
title_lbl.pack(pady=15)

status_lbl = ttk.Label(root, text="Status: Waiting for command...", font=("Arial", 11, "italic"), foreground="#00FF00")
status_lbl.pack(pady=5)

sliders = []
label_values = []

# Internal state variable for the gripper (Starts open)
current_gripper_val = 0.000

def send_to_txt(*args):
    """Convert current slider positions to radians and write to MuJoCo file"""
    rad_vals = []
    for i in range(6):
        deg = sliders[i].get()
        label_values[i].config(text=f"{int(deg)}°")
        rad_vals.append(np.radians(deg))
    
    # Inject current gripper value
    rad_vals.append(current_gripper_val)
    
    line = ",".join([f"{x:.6f}" for x in rad_vals])
    try:
        with open(FILENAME, "w") as f:
            f.write(line)
    except Exception:
        pass

# --- 4. SMOOTH MOTION INTERPOLATION ENGINE ---
paso_secuencia_actual = 0
sub_paso_actual = 0
total_sub_pasos = 60  # Intermediate steps (60 steps @ 50FPS = 1.2 seconds of smooth transit)
pose_inicial_tramo = []

def interpolar_movimiento():
    global sub_paso_actual, paso_secuencia_actual, pose_inicial_tramo, current_gripper_val
    
    if paso_secuencia_actual >= len(SEQUENCE):
        status_lbl.config(text="Status: Pick & Place Routine Successfully Completed!", foreground="#00FF00")
        btn_start.config(state="normal")
        btn_close_g.config(state="normal")
        btn_open_g.config(state="normal")
        return

    pose_objetivo = SEQUENCE[paso_secuencia_actual]["pose"]
    
    # Capture initial state when starting a new segment of the sequence
    if sub_paso_actual == 0:
        pose_inicial_tramo = [sliders[i].get() for i in range(6)] + [current_gripper_val]
        status_lbl.config(text=f"Executing: {SEQUENCE[paso_secuencia_actual]['desc']}", foreground="#FFCC00")

    # Current progress percentage (0.0 to 1.0)
    t = sub_paso_actual / total_sub_pasos
    
    # Interpolate the 6 axes smoothly
    for i in range(6):
        val_interpolado = pose_inicial_tramo[i] + (pose_objetivo[i] - pose_inicial_tramo[i]) * t
        sliders[i].set(val_interpolado)
        
    # Interpolate gripper value
    current_gripper_val = pose_inicial_tramo[6] + (pose_objetivo[6] - pose_inicial_tramo[6]) * t
    
    # Update visual indicator based on the hardware settings
    if current_gripper_val >= 0.015:
        val_lbl_g.config(text="Closed")
    else:
        val_lbl_g.config(text="Open")
        
    send_to_txt()
    
    sub_paso_actual += 1
    
    if sub_paso_actual <= total_sub_pasos:
        root.after(20, interpolar_movimiento)
    else:
        sub_paso_actual = 0
        paso_secuencia_actual += 1
        # 400ms static pause at destination to ensure stable grasp/release
        root.after(400, interpolar_movimiento)

def comenzar_rutina():
    global paso_secuencia_actual, sub_paso_actual
    btn_start.config(state="disabled")
    btn_close_g.config(state="disabled")
    btn_open_g.config(state="disabled")
    
    paso_secuencia_actual = 0
    sub_paso_actual = 0
    interpolar_movimiento()


# --- 5. BIND SLIDERS IN THE INTERFACE ---
joint_names = ["Joint 1", "Joint 2", "Joint 3", "Joint 4", "Joint 5", "Joint 6"]
for i in range(6):
    frame = tk.Frame(root, bg='#222222', pady=5)
    frame.pack(fill='x', padx=20)
    
    lbl = ttk.Label(frame, text=joint_names[i], width=10)
    lbl.pack(side='left')
    
    slider = tk.Scale(frame, from_=JOINT_RANGES[i][0], to=JOINT_RANGES[i][1], orient='horizontal', 
                      bg='#333333', fg='white', highlightbackground='#222222',
                      troughcolor='#555555', command=send_to_txt, resolution=0.1) # Decimals for smoothness
    slider.set(SEQUENCE[0]["pose"][i])  
    slider.pack(side='left', fill='x', expand=True, padx=10)
    sliders.append(slider)
    
    val_lbl = ttk.Label(frame, text=f"{SEQUENCE[0]['pose'][i]}°", width=6)
    val_lbl.pack(side='right')
    label_values.append(val_lbl)

# --- 6. DIRECT GRIPPER CONTROL PANEL (MANUAL BUTTONS) ---
frame_g_ctrl = tk.Frame(root, bg='#222222', pady=15)
frame_g_ctrl.pack(fill='x', padx=20)

lbl_g_title = ttk.Label(frame_g_ctrl, text="Gripper:", width=10)
lbl_g_title.pack(side='left')

def manual_close_gripper():
    """Manually changes gripper state to closed by sending 0.020 to MuJoCo"""
    global current_gripper_val
    current_gripper_val = 0.020
    val_lbl_g.config(text="Closed")
    send_to_txt()

def manual_open_gripper():
    """Manually changes gripper state to open by sending 0.000 to MuJoCo"""
    global current_gripper_val
    current_gripper_val = 0.000
    val_lbl_g.config(text="Open")
    send_to_txt()

# Quick action manual buttons to open and close
btn_close_g = tk.Button(frame_g_ctrl, text="Close Gripper", width=12, highlightbackground='#222222', command=manual_close_gripper)
btn_close_g.pack(side='left', padx=5, expand=True, fill='x')

btn_open_g = tk.Button(frame_g_ctrl, text="Open Gripper", width=12, highlightbackground='#222222', command=manual_open_gripper)
btn_open_g.pack(side='left', padx=5, expand=True, fill='x')

# Plain text current gripper status indicator (Avoids numerical confusion)
val_lbl_g = ttk.Label(frame_g_ctrl, text="Open", width=15, anchor="center")
val_lbl_g.pack(side='right', padx=5)


# --- 7. AUTOMATIC ROUTINE BUTTON ---
btn_start = tk.Button(root, text="▶ START SMOOTH ROUTINE", font=("Arial", 12, "bold"),
                      bg="#00AA55", fg="white", activebackground="#008844", activeforeground="white",
                      bd=0, padx=10, pady=10, command=comenzar_rutina)
btn_start.pack(pady=20)

def on_close():
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

# Write initial startup values before the main loop
send_to_txt()

root.mainloop()