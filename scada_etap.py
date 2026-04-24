import streamlit as st
import pandas as pd
import numpy as np
import time

# Configuración de la página
st.set_page_config(page_title="SCADA Eco-Sim: Smart-Plant ETAP", layout="wide")

st.title("🌊 SCADA Eco-Sim: Optimización Inteligente ETAP")
st.subheader("Panel de Control de Oficina Técnica de Ingeniería")

# --- SIDEBAR: CONTROLES DE SIMULACIÓN ---
st.sidebar.header("Configuración de Sensores")
caudal = st.sidebar.slider("Caudal de Entrada (Q) [m3/h]", 0, 500, 250)
turbidez = st.sidebar.slider("Turbidez (T) [NTU]", 0, 150, 20)
tarifa_valle = st.sidebar.checkbox("Activar Horario Valle (Tarifa Económica)", value=True)

# --- LÓGICA DEL ALGORITMO (Parte A y B) ---
umbral_critico = 80
dosificacion = (caudal * turbidez) / 100  # Lógica proporcional
estado_valvula = "ABIERTA"
alerta_seguridad = False

if turbidez > umbral_critico:
    estado_valvula = "CERRADA (Desvío a Tanque Seguridad)"
    alerta_seguridad = True
    dosificacion = 0

# Ahorro energético (Parte B)
objetivo_ahorro = 8500  # kWh/mes
consumo_actual = 10000 if not tarifa_valle else 8200

# --- INTERFAZ PRINCIPAL ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Caudal Actual", f"{caudal} m3/h")
    st.write(f"**Estado Válvula Entrada:** {estado_valvula}")
    if alerta_seguridad:
        st.error("⚠️ ALERTA: Turbidez crítica detectada")

with col2:
    st.metric("Turbidez", f"{turbidez} NTU", delta=f"{turbidez-umbral_critico}" if turbidez > umbral_critico else None, delta_color="inverse")
    st.progress(min(turbidez / 150, 1.0))

with col3:
    st.metric("Dosificación Coagulante", f"{dosificacion:.2f} L/h")
    st.info(f"Consumo Energético Est.: {consumo_actual} kWh/mes")

# --- GRÁFICO DE RESILIENCIA (Parte C) ---
st.divider()
st.subheader("📈 Simulación de Resiliencia y Niveles")

# Simulación de datos históricos
chart_data = pd.DataFrame(
    np.random.randn(20, 2) / 10 + [caudal, 85],
    columns=['Caudal Real-time', 'Nivel Tanque (%)']
)

st.line_chart(chart_data)

# --- REPORTE DE SOSTENIBILIDAD (Parte D) ---
st.divider()
st.subheader("🍃 ROI Ambiental y Economía Circular")
ahorro_kwh = 10000 - consumo_actual
co2_evitado = ahorro_kwh * 0.25

c_eco1, c_eco2 = st.columns(2)
with c_eco1:
    st.success(f"CO2 evitado este mes: {co2_evitado} kg")
with c_eco2:
    st.write("**Estatus de Filtros:**")
    st.write("Presión Diferencial: 1.2 bar (Estado Óptimo)")
