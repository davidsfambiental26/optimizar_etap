import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from math import floor

st.set_page_config(page_title="SCADA Eco-Sim v7.0 - Control Total", layout="wide")

st.title("⚙️ SCADA Eco-Sim: Control de Resiliencia y Eficiencia")
st.markdown("---")

# --- SIDEBAR: PANEL DE CONTROL ---
st.sidebar.header("🕹️ Consola de Sensores")
q_input = st.sidebar.slider("Caudal de Entrada (Q) [m³/h]", 0, 500, 300)
t_input = st.sidebar.slider("Turbidez Detectada (T) [NTU]", 0, 150, 20)

st.sidebar.markdown("---")
st.sidebar.header("🔋 Parámetros de Eficiencia")
horario = st.sidebar.select_slider("Franja Horaria", options=["Diurno (Punta)", "Nocturno (Valle)"])
presion_filtro = st.sidebar.slider("Presión Diferencial Filtro [bar]", 0.0, 3.0, 1.0, step=0.1)

# --- LÓGICA DE CONTROL ---
umbral_turbidez = 80
turbidez_fuera_rango = t_input > umbral_turbidez
estado_valvula = "CERRADA" if turbidez_fuera_rango else "ABIERTA"

# --- SIMULACIÓN DINÁMICA (Cálculo de niveles y energía) ---
minutos = np.arange(0, 61, 1)

def simular_sistema():
    niveles = []
    cons_inst = []
    nivel_act = 50.0  # Nivel inicial
    consumo_ciudad = 2.2 # Demanda constante de la red urbana
    
    # Cálculo de ahorro mensual para KPI
    ahorro_fijo = 0
    if horario == "Nocturno (Valle)": ahorro_fijo += 800
    if presion_filtro <= 1.5: ahorro_fijo += 700
    
    for t in minutos:
        # Lógica de Entrada de Agua (Bypass o Apagado Inteligente)
        if turbidez_fuera_rango:
            q_ent = 0 # Válvula cerrada por calidad
        elif nivel_act > 95 and q_input < 100:
            q_ent = 0 # IA apaga motores por tanque lleno y baja demanda
        else:
            # Simulación de caída de caudal al minuto 20 (Parte C)
            factor_caudal = 0.6 if (20 < t < 50) else 1.0
            q_ent = (q_input * factor_caudal) / 120 
            
        # El tanque SIEMPRE se vacía si hay demanda urbana
        nivel_act += (q_ent - (consumo_ciudad / 10))
        nivel_act = max(min(nivel_act, 100), 0)
        niveles.append(nivel_act)
        
        # Energía
        base_inst = 13.8 
        ahorro_variable = 0.7 if presion_filtro > 1.5 else 0 # 5% extra
        cons_inst.append(base_inst - (ahorro_fijo/720) - ahorro_variable)
        
    return niveles, cons_inst, ahorro_fijo

niveles_plot, energia_plot, ahorro_mensual = simular_sistema()
perc_final = int(niveles_plot[-1])

# --- PANEL DE MÉTRICAS (KPIs) ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🌊 Caudal Real", f"{q_input} m³/h", delta="-40%" if q_input > 0 else "CORTE")
with col2:
    st.metric("🚪 Válvula Entrada", estado_valvula, delta="Bypass" if turbidez_fuera_rango else "Normal", delta_color="inverse" if turbidez_fuera_rango else "normal")
with col3:
    st.metric("🚿 Filtros", f"{presion_filtro} bar", delta="LAVADO" if presion_filtro > 1.5 else "OK")
with col4:
    total_kwh = 10000 - ahorro_mensual - (500 if presion_filtro > 1.5 else 0)
    st.metric("⚡ Consumo Proyectado", f"{int(total_kwh)} kWh", delta=f"-{10000-int(total_kwh)} kWh")

st.markdown("---")

# --- GRÁFICAS ---
c1, c2 = st.columns(2)

with c1:
    fig_n = go.Figure()
    # Zona roja de sequía extrema
    fig_n.add_hrect(y0=0, y1=10, fillcolor="red", opacity=0.2)
    fig_n.add_trace(go.Scatter(x=minutos, y=niveles_plot, fill='tozeroy', name='Nivel %', line=dict(color='#0077B6', width=4)))
    fig_n.update_layout(title="📈 Monitorización de Nivel (Control de Sequía)", yaxis=dict(range=[0, 105]), template="plotly_white")
    st.plotly_chart(fig_n, use_container_width=True)

with c2:
    fig_e = go.Figure()
    fig_e.add_trace(go.Scatter(x=minutos, y=energia_plot, name='Consumo Optimizado', line=dict(color='#2ECC71', width=3)))
    fig_e.add_trace(go.Scatter(x=minutos, y=[13.8]*61, name='Consumo Base', line=dict(color='grey', dash='dash')))
    fig_e.update_layout(title="⚡ Eficiencia Energética (kWh/h)", template="plotly_white")
    st.plotly_chart(fig_e, use_container_width=True)

# --- SISTEMA DE ALERTAS CRÍTICAS ---
st.markdown("### 📢 Notificaciones del Sistema")

# Alerta de Calidad
if turbidez_fuera_rango:
    st.error(f"🛑 VÁLVULA CERRADA: Turbidez crítica ({t_input} NTU). Bypass activado.")

# Alerta de Nivel (Prioridad Sequía)
if perc_final <= 10:
    st.error(f"🚨 RIESGO DE SEQUÍA EXTREMA: Depósito al {perc_final}%. ¡SUMINISTRO CRÍTICO!")
elif perc_final <= 30:
    st.warning(f"🟡 AVISO: Nivel mínimo alcanzado ({perc_final}%).")
else:
    st.success(f"💧 Nivel de depósito estable ({perc_final}%).")

# Alerta de Eficiencia
if presion_filtro > 1.5:
    st.info(f"🧼 Sistema: Presión en {presion_filtro} bar. Lavado automático activado (+5% ahorro).")
