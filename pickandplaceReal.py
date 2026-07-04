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
    (-50, 50)     # J6
]

initial_pose_deg = list(FALLBACK_POSE_DEG)

if robot_connected:
    try:
        joints_rad = robot.get_joints()
        initial_pose_deg = [int(np.degrees(j)) for j in joints_rad]
        print(f"Synchronizing interface with the real hardware pose: {initial_pose_deg}")
    except Exception as e:
        print(f"Could not read the robot's initial pose, using default values: {e}")

# --- 3. PICK AND PLACE SEQUENCE (Gripper: Open = 0.000 / Closed = 0.020) ---
# Format: [J1, J2, J3, J4, J5, J6, Gripper]
SECUENCIA = [
    {"desc": "1. Inicio / Posicion Inicial", "pose": [0, 0, 0, 0, 0, 0, 0.000]},
    
    # --- Primer cubo ---
    {"desc": "2. Rotar a Objeto (-90°)", "pose": [-90, 0, 0, 0, 0, 0, 0.000]},
    {"desc": "3. Descender a Objeto", "pose": [-90, -35, -33, 0, -7, 0, 0.000]},
    {"desc": "3.1 Descender a Objeto - Cerrar", "pose": [-90, -35, -33, 0, -7, 0, 0.020]},
    {"desc": "4. Cerrar Gripper! (Objeto en Posicion de Picking)", "pose": [-90, 0 , 0, 0, 0, 0, 0.020]},
    {"desc": "5. Levantar Arma con Objeto", "pose": [0, -43, -20, -6, 12, 3, 0.020]},
    {"desc": " 6. Ir al centro", "pose": [0, -43, -20, -6, 12, 3, 0.000]},
    {"desc": " 7. Desciende", "pose": [0, 0, 0, 0, 0, 0, 0.000]},

   # --- Segundo cubo ---
   #{"desc": " 7.1 Abrir Gripper! (Pick)", "pose": [-71, -36, -26, 2, -18, 16, 0.000]},
   {"desc": " 8. Levantar", "pose": [-71, -36, 0, 0, 0, 0, 0]},
   {"desc": "2. Rotar a Objeto (-90°)", "pose": [-71, -36, 0, 2, 0, 0, 0.000]},
   {"desc": "3. Descender a Objeto", "pose": [-71, -36, 0, 2, 0, 16, 0.000]},
   {"desc": "3.1 Descender a Objeto - Cerrar", "pose": [-71, -36, -26, 2, 0, 16, 0.020]},
   {"desc": "4. Cerrar Gripper! (Objeto en Posicion de Picking)", "pose": [-71, -36 , 26.2, 2, -18, 16, 0.020]},
   {"desc": "5. Levantar Arma con Objeto", "pose": [-71, -36 , 26.2, 2, -18, 16, 0.020]},
   {"desc": " 6. Ir al centro", "pose": [0, 0, 0, 0, 0, 0, 0.020]},
   {"desc": " 7. Desciende", "pose": [-8.4, -42.1, -7.9, 39.6, -9, 0, 0.020]},
   {"desc": " 7.1 Abrir Gripper! (Pick)", "pose": [-8.4, -42.1, -7.9, 39.6, -9, 0, 0.000]},
   {"desc": " 8. Levantar", "pose": [0, 30, 0 , 0, 0, 0, 0.000]},
]

# --- 4. GRAPHICAL USER INTERFACE CREATION (Tkinter) ---
root = tk.Tk()
root.title("Unified Control Panel - Niryo Ned2 Real + MuJoCo")
root.geometry("480x640") 
root.configure(bg='#222222')

style = ttk.Style()
style.configure("TLabel", foreground="white", background="#222222", font=("Arial", 11))

title_lbl = ttk.Label(root, text="Niryo Ned2 - Real and Virtual Trajectory", font=("Arial", 14, "bold"))
title_lbl.pack(pady=15)

status_lbl = ttk.Label(root, text="Status: Waiting for command...", font=("Arial", 11, "italic"), foreground="#00FF00")
status_lbl.pack(pady=5)

sliders = []
label_values = []

# Internal state variable to store gripper opening value (Starts open)
current_gripper_val = 0.000

def send_to_txt(*args):
    """Convert slider positions to radians and SWAP J4 and J5 ONLY for MuJoCo (and invert J5)"""
    ui_rad_vals = []
    for i in range(6):
        deg = sliders[i].get()
        label_values[i].config(text=f"{int(deg)}°")
        ui_rad_vals.append(np.radians(deg))
    
    # Inversion of physical J5 for MuJoCo mesh 4
    j5_inverted = -ui_rad_vals[4]
    
    mujoco_joints_rad = [
        ui_rad_vals[0],
        ui_rad_vals[1],
        ui_rad_vals[2],
        ui_rad_vals[3], 
        ui_rad_vals[4],  
        ui_rad_vals[5]
    ]
    
    # Inject current gripper position for the simulator
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
                      troughcolor='#555555', command=send_to_txt, resolution=0.1)
    
    slider.set(initial_pose_deg[i])  
    slider.pack(side='left', fill='x', expand=True, padx=10)
    sliders.append(slider)
    
    val_lbl = ttk.Label(frame, text=f"{initial_pose_deg[i]}°", width=6)
    val_lbl.pack(side='right')
    label_values.append(val_lbl)

# --- 5. DIRECT GRIPPER CONTROL PANEL ---
frame_g_ctrl = tk.Frame(root, bg='#222222', pady=10)
frame_g_ctrl.pack(fill='x', padx=20)

lbl_g_title = ttk.Label(frame_g_ctrl, text="Gripper Control:", width=15)
lbl_g_title.pack(side='left')

def manual_close_gripper():
    global current_gripper_val
    if robot_connected:
        try:
            robot.grasp_with_tool()
            print("Real Gripper: Closed!")
        except Exception as e:
            print(f"Error closing real gripper: {e}")
            
    current_gripper_val = 0.020
    val_lbl_g.config(text="Closed")
    send_to_txt()

def manual_open_gripper():
    global current_gripper_val
    if robot_connected:
        try:
            robot.release_with_tool()
            print("Real Gripper: Open!")
        except Exception as e:
            print(f"Error opening real gripper: {e}")
            
    current_gripper_val = 0.000
    val_lbl_g.config(text="Open")
    send_to_txt()

btn_close_g = tk.Button(frame_g_ctrl, text="Close Gripper", width=12, highlightbackground='#222222', command=manual_close_gripper)
btn_close_g.pack(side='left', padx=5, expand=True, fill='x')

btn_open_g = tk.Button(frame_g_ctrl, text="Open Gripper", width=12, highlightbackground='#222222', command=manual_open_gripper)
btn_open_g.pack(side='left', padx=5, expand=True, fill='x')

val_lbl_g = ttk.Label(frame_g_ctrl, text="Open", width=15, anchor="center")
val_lbl_g.pack(side='right', padx=5)


# --- 6. SMOOTH MOTION INTERPOLATION ENGINE (Hardware Synchronized) ---
paso_secuencia_actual = 0
sub_paso_actual = 0
total_sub_pasos = 60  
pose_inicial_tramo = []

def interpolar_movimiento():
    global sub_paso_actual, paso_secuencia_actual, pose_inicial_tramo, current_gripper_val
    
    if paso_secuencia_actual >= len(SECUENCIA):
        status_lbl.config(text="Status: Pick & Place Routine Successfully Completed!", foreground="#00FF00")
        btn_start.config(state="normal")
        btn_close_g.config(state="normal")
        btn_open_g.config(state="normal")
        btn_move_manual.config(state="normal")
        return

    pose_objetivo = SECUENCIA[paso_secuencia_actual]["pose"]
    
    if sub_paso_actual == 0:
        pose_inicial_tramo = [sliders[i].get() for i in range(6)] + [current_gripper_val]
        status_lbl.config(text=f"Executing: {SECUENCIA[paso_secuencia_actual]['desc']}", foreground="#FFCC00")

    t = sub_paso_actual / total_sub_pasos
    
    # Progressive update on Sliders and txt file to refresh MuJoCo smoothly
    for i in range(6):
        val_interpolado = pose_inicial_tramo[i] + (pose_objetivo[i] - pose_inicial_tramo[i]) * t
        sliders[i].set(val_interpolado)
        
    current_gripper_val = pose_inicial_tramo[6] + (pose_objetivo[6] - pose_inicial_tramo[6]) * t
    
    if current_gripper_val >= 0.015:
        val_lbl_g.config(text="Closed")
    else:
        val_lbl_g.config(text="Open")
        
    send_to_txt()
    sub_paso_actual += 1
    
    if sub_paso_actual <= total_sub_pasos:
        root.after(20, interpolar_movimiento)
    else:
        # --- THE VISUAL SMOOTH TRANSIT REACHED DESTINATION -> EXECUTE ON REAL ROBOT ---
        if robot_connected:
            try:
                # Real robot receives joint angles in their direct native order
                joints_real_rad = [np.radians(pose_objetivo[i]) for i in range(6)]
                robot.move_joints(joints_real_rad)
                
                # Physical tool control matching the current sequence step
                if pose_objetivo[6] >= 0.015:
                    robot.grasp_with_tool()
                else:
                    robot.release_with_tool()
            except Exception as e:
                print(f"Hardware execution error in segment {paso_secuencia_actual}: {e}")
                
        sub_paso_actual = 0
        paso_secuencia_actual += 1
        # 500ms static rest to absorb physical inertia before the next command
        root.after(500, interpolar_movimiento)

def comenzar_rutina():
    global paso_secuencia_actual, sub_paso_actual
    btn_start.config(state="disabled")
    btn_close_g.config(state="disabled")
    btn_open_g.config(state="disabled")
    btn_move_manual.config(state="disabled")
    
    paso_secuencia_actual = 0
    sub_paso_actual = 0
    interpolar_movimiento()

# --- 7. COMPLEMENTARY ACTION BUTTONS ---
frame_buttons = tk.Frame(root, bg='#222222', pady=10)
frame_buttons.pack()

def move_robot_manual():
    """Takes the current configuration from UI sliders and commands the real arm natively"""
    if robot_connected:
        try:
            joints_rad = [np.radians(slider.get()) for slider in sliders]
            robot.move_joints(joints_rad)
            print("Hardware: Arm manually moved to UI pose configuration.")
        except Exception as e:
            print(f"Error in manual joint command transmission: {e}")
    send_to_txt()

btn_move_manual = tk.Button(frame_buttons, text="Send Sliders to Real Arm", width=25, highlightbackground='#222222', command=move_robot_manual)
btn_move_manual.pack(pady=4)

btn_start = tk.Button(frame_buttons, text="▶ START SMOOTH ROUTINE", font=("Arial", 11, "bold"),
                      bg="#00AA55", fg="white", activebackground="#008844", activeforeground="white",
                      bd=0, padx=10, pady=8, command=comenzar_rutina)
btn_start.pack(pady=10)

# --- 8. SAFE SHUTDOWN MANAGEMENT ---
def on_close():
    if robot_connected:
        robot.close_connection()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

# Force initialization write
send_to_txt()

root.mainloop()