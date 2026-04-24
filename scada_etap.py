import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="SCADA Eco-Sim v11.0 - Seguridad Crítica", layout="wide")

st.title("🛡️ SCADA Eco-Sim: Gestión de Resiliencia y Niveles Críticos")
st.markdown("---")

# --- SIDEBAR: SENSORES ---
st.sidebar.header("🕹️ Consola de Sensores")
q_input = st.sidebar.slider("Caudal de Entrada (Q) [m³/h]", 0, 500, 260)
t_input = st.sidebar.slider("Turbidez Detectada (T) [NTU]", 0, 150, 25)

st.sidebar.markdown("---")
st.sidebar.header("🔋 Gestión Energética")
horario = st.sidebar.select_slider("Franja Horaria", options=["Diurno (Punta)", "Nocturno (Valle)"])
presion_filtro = st.sidebar.slider("Presión Diferencial Filtro [bar]", 0.0, 3.0, 1.2, step=0.1)

# --- LÓGICA DE CONTROL ---
umbral_turbidez = 80
valvula_est = "ABIERTA" if t_input <= umbral_turbidez else "CERRADA"
lavado_req = presion_filtro > 1.5

# --- SIMULACIÓN MATEMÁTICA ---
minutos = np.arange(0, 61, 1)

def simular_proceso():
    niveles = []
    energia = []
    nivel_act = 45.0 # Nivel inicial
    demanda_ciudad = 3.4 # Salida de agua potable constante
    
    for t in minutos:
        # Entrada de agua
        if valvula_est == "CERRADA":
            q_in = 0
        else:
            # Simulación de caída del 40% (Parte C de la guía)
            factor_q = 0.6 if t > 15 else 1.0
            q_in = (q_input * factor_q) / 60
            
        # Balance Hídrico
        nivel_act += (q_in - demanda_ciudad)
        nivel_act = max(min(nivel_act, 100), 0)
        niveles.append(nivel_act)
        
        # Energía
        base_e = 13.0 + (q_input / 100)
        ahorro = 0
        if horario == "Nocturno (Valle)": ahorro += 2.0
        if presion_filtro <= 1.5: ahorro += 1.5
        if lavado_req: ahorro += (base_e * 0.06)
        
        consumo_inst = base_e - ahorro
        energia.append(round(consumo_inst + np.random.uniform(-0.05, 0.05), 2))
        
    return niveles, energia

niveles, energia = simular_proceso()
nivel_f = int(niveles[-1])
cons_actual = energia[-1]

# --- 1. KPIs SUPERIORES ---
st.subheader("📊 Panel de Instrumentación")
k1, k2, k3, k4, k5 = st.columns(5)
with k1: st.metric("🌊 Caudal", f"{q_input} m³/h")
with k2: st.metric("👁️ Turbidez", f"{t_input} NTU")
with k3: st.metric("🚪 Válvula", valvula_est)
with k4: st.metric("⚡ Energía", f"{cons_actual:.2f} kWh/h")
with k5: st.metric("🚿 Filtro", f"{presion_filtro} bar")

st.markdown("---")

# --- 2. GRÁFICAS ---
col_g1, col_g2 = st.columns(2)

with col_g1:
    fig_n = go.Figure()
    # Zonas de seguridad sombreadas
    fig_n.add_hrect(y0=0, y1=10, fillcolor="red", opacity=0.3, annotation_text="SEQUÍA EXTREMA")
    fig_n.add_hrect(y0=10, y1=30, fillcolor="orange", opacity=0.2, annotation_text="RIESGO: NIVEL BAJO")
    
    fig_n.add_trace(go.Scatter(x=minutos, y=niveles, fill='tozeroy', name='Nivel (%)', line=dict(color='#0077B6', width=4)))
    fig_n.update_layout(title="📈 Curva de Nivel y Resiliencia", yaxis=dict(range=[0, 105]), template="plotly_white")
    st.plotly_chart(fig_n, use_container_width=True)

with col_g2:
    fig_e = go.Figure()
    fig_e.add_trace(go.Scatter(x=minutos, y=energia, name='Smart-Plant', line=dict(color='#2ECC71', width=3)))
    fig_e.add_trace(go.Scatter(x=minutos, y=[14.5]*61, name='Base Convencional', line=dict(color='grey', dash='dot')))
    fig_e.update_layout(title="⚡ Detalle de Eficiencia Energética", template="plotly_white")
    st.plotly_chart(fig_e, use_container_width=True)

# --- 3. ALERTAS DE SISTEMA (Lógica Corregida) ---
st.subheader("📢 Notificaciones de Control")

# Lógica estricta de niveles
if nivel_f <= 10:
    st.error(f"🚨 RIESGO DE SEQUÍA EXTREMA: Depósito crítico al {nivel_f}%. Suministro en peligro.")
elif 10 < nivel_f <= 30:
    st.warning(f"⚠️ AVISO: RIESGO DE NIVEL BAJO DE DEPÓSITO. Nivel actual: {nivel_f}%. Incrementar caudal de entrada.")
elif t_input > umbral_turbidez:
    st.error(f"🛑 CALIDAD: Válvula CERRADA. Turbidez fuera de rango ({t_input} NTU).")
else:
    st.success(
