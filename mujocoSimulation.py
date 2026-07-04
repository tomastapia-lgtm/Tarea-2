import mujoco
import mujoco.viewer
import time
import numpy as np
import os
import xml.etree.ElementTree as ET

# XML modificado para que qpos = 0 coincida con la postura de la foto de referencia
robot_xml = ET.tostring(ET.fromstring(open("niryo.xml").read()), encoding="utf8")

FILENAME = "cmd_joints.txt"

# Forzar la inicialización del archivo en 0 para las articulaciones y ABIERTO (0.020) para la pinza
if not os.path.exists(FILENAME):
    with open(FILENAME, "w") as f:
        f.write("0.0,0.0,0.0,0.0,0.0,0.0,0.020")

model = mujoco.MjModel.from_xml_string(robot_xml)
data = mujoco.MjData(model)

print("-> Iniciando simulación en MuJoCo.")
print("-> Sincronizado con los BOTONES del panel (Abrir = 0.020 / Cerrar = 0.000).")

# Variable para controlar cada cuánto imprimimos el GPS (cada 1 segundo)
ultimo_print = time.time()

with mujoco.viewer.launch_passive(model, data) as viewer:
    viewer.cam.distance = 1.3
    viewer.cam.lookat = [0.2, 0, 0.25]
    viewer.cam.elevation = -20
    viewer.cam.azimuth = 135
    
    while viewer.is_running():
        step_start = time.time()
        
        try:
            with open(FILENAME, "r") as f:
                line = f.read().strip()
                if line:
                    values = [float(x) for x in line.split(",")]
                    if len(values) == 7:
                        # 1. Posicionar las 6 articulaciones del brazo
                        data.qpos[:6] = values[:6]
                        
                        # 2. Controlar la pinza
                        garra_val = values[6]
                        data.qpos[6] = garra_val  # Dedo izquierdo
                        data.qpos[7] = garra_val  # Dedo derecho
        except Exception:
            pass

        mujoco.mj_step(model, data)
        viewer.sync()
        
        # --- NUEVO SISTEMA GPS (CINEMÁTICA DIRECTA) ---
        tiempo_actual = time.time()
        if tiempo_actual - ultimo_print > 1.0:  # Actualiza el mensaje cada 1.0 segundos
            # Identificar el ID del efector final (usualmente el último cuerpo de la cadena)
            id_pinza = model.nbody - 1 
            posicion_metros = data.xpos[id_pinza]
            
            # Convertir de metros (lenguaje MuJoCo) a milímetros (formato del informe PDF)
            x_mm = posicion_metros[0] * 1000
            y_mm = posicion_metros[1] * 1000
            z_mm = posicion_metros[2] * 1000
            
            # Imprimir en la terminal con 1 decimal para que sea fácil de anotar
            print(f"📍 GPS Pinza -> X: {x_mm:.1f} mm | Y: {y_mm:.1f} mm | Z: {z_mm:.1f} mm")
            
            ultimo_print = tiempo_actual
        # ----------------------------------------------

        time_until_next_step = model.opt.timestep - (time.time() - step_start)
        if time_until_next_step > 0:
            time.sleep(time_until_next_step)
        