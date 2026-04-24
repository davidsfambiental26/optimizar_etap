import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="SCADA Eco-Sim v8.0 - Full Integration", layout="wide")

st.title("🛡️ SCADA Eco-Sim: Control de Resiliencia y Eficiencia Energética")
st.markdown("---")

# --- SIDEBAR: SENSORES ---
st.sidebar.header("🕹️ Consola de Sensores")
q_input = st.sidebar.slider("Caudal de Entrada (Q) [m³/h]", 0, 500, 250)
t_input = st.sidebar.slider("Turbidez Detectada (T) [NTU]", 0, 150, 20)

st.sidebar.markdown("---")
st.sidebar.header("🔋 Parámetros de Eficiencia")
horario = st.sidebar.select_slider("Franja Horaria", options=["Diurno (Punta)", "Nocturno (Valle)"])
presion_filtro = st.sidebar.slider("Presión Diferencial Filtro [bar]", 0.0, 3.0, 1.0, step=0.1)

# --- LÓGICA DE CONTROL ---
umbral_turbidez = 80
valvula_abierta = t_input <= umbral_turbidez
lavado_activo = presion_filtro > 1.5

# --- SIMULACIÓN MATEMÁTICA ---
minutos = np.arange(0, 61, 1)

def ejecutar_simulacion():
    niveles = []
    energia = []
    nivel_act = 40.0 # Nivel inicial
    
    # Consumo de la ciudad (fijado alto para permitir el vaciado)
    demanda_ciudad = 3.5 
    
    for t in minutos:
        # 1. Lógica de Entrada (Llenado)
        if not valvula_abierta:
            caudal_neto_in = 0  # Bypass por turbidez
        else:
            # Caída del 40% de caudal a partir del min 10 (Escenario Parte C)
            factor_resiliencia = 0.6 if t > 10 else 1.0
            caudal_neto_in = (q_input * factor_resiliencia) / 60 
        
        # 2. Actualización de Nivel (Entrada - Salida)
        nivel_act += (caudal_neto_in - demanda_ciudad)
        nivel_act = max(min(nivel_act, 100), 0)
        niveles.append(nivel_act)
        
        # 3. Lógica Energética DINÁMICA (kWh/h)
        # Base según caudal (a más caudal, más bombeo)
        base_e = 10.0 + (q_input / 100)
        
        # Aplicación de reglas de ahorro (E3)
        ahorro = 0
        if horario == "Nocturno (Valle)": ahorro += 2.0  # Regla 800kWh/mes
        if presion_filtro <= 1.5: ahorro += 1.5         # Regla 700kWh/mes
        if lavado_activo: ahorro += (base_e * 0.05)     # Regla 5% extra
        
        consumo_inst = base_e - ahorro
        energia.append(consumo_inst + np.random.uniform(-0.1, 0.1))
        
    return niveles, energia

niveles_plot, energia_plot = ejecutar_simulacion()
nivel_final = int(niveles_plot[-1])

# --- PANEL DE MÉTRICAS ---
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("🌊 Caudal", f"{q_input} m³/h", delta="-40% (Active)" if q_input > 0 else "OFF")
with c2:
    st.metric("🚪 Válvula", "ABIERTA" if valvula_abierta else "CERRADA", 
              delta_color="normal" if valvula_abierta else "inverse")
with c3:
    st.metric("🧼 Filtro", f"{presion_filtro} bar", delta="LAVANDO" if lavado_activo else "OK")
with c4:
    cons_mes = 10000 - (1500 if (horario == "Nocturno (Valle)" and not lavado_activo) else 0)
    st.metric("⚡ Consumo Est.", f"{energia_plot[-1]:.2f} kWh/h")

# --- GRÁFICAS ---
g1, g2 = st.columns(2)

with g1:
    fig_n = go.Figure()
    # Zona de peligro
    fig_n.add_hrect(y0=0, y1=10, fillcolor="red", opacity=0.3, annotation_text="SEQUÍA EXTREMA")
    fig_n.add_trace(go.Scatter(x=minutos, y=niveles_plot, fill='tozeroy', name='Nivel (%)', line=dict(color='#0077B6', width=4)))
    fig_n.update_layout(title="📈 Nivel del Depósito (Vaciado vs Llenado)", yaxis=dict(range=[0, 105]), template="plotly_white")
    st.plotly_chart(fig_n, use_container_width=True)

with g2:
    fig_e = go.Figure()
    fig_e.add_trace(go.Scatter(x=minutos, y=[13.8]*61, name='Consumo Convencional', line=dict(color='grey', dash='dash')))
    fig_e.add_trace(go.Scatter(x=minutos, y=energia_plot, name='Consumo Smart-Plant', line=dict(color='#2ECC71', width=3)))
    fig_e.update_layout(title="⚡ Consumo Energético en Tiempo Real", template="plotly_white")
    st.plotly_chart(fig_e, use_container_width=True)

# --- SISTEMA DE ALERTAS PRIORIZADAS ---
st.subheader("📢 Estado del Sistema SCADA")

# 1. Alerta de Nivel (Prioridad Máxima)
if nivel_final <= 10:
    st.error(f"🚨 RIESGO DE SEQUÍA EXTREMA: El nivel ({nivel_final}%) es crítico. La demanda urbana supera al llenado.")
elif nivel_final <= 30:
    st.warning(f"🟡 AVISO: Reserva en nivel mínimo ({nivel_final}%).")
else:
    st.success(f"💧 Suministro normal: Nivel al {nivel_final}%.")

# 2. Alerta de Operación
if not valvula_abierta:
    st.error("🛑 CALIDAD: Válvula CERRADA por turbidez alta. Entrada de agua interrumpida.")
if lavado_activo:
    st.info("🧼 MANTENIMIENTO: Lavado de filtros activo por alta presión diferencial.")
