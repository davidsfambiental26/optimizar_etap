import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from math import floor

st.set_page_config(page_title="SCADA Eco-Sim v6.0 - Eficiencia Energética", layout="wide")

st.title("⚡ SCADA Eco-Sim: Gestión Energética e Inteligencia Operacional")
st.markdown("---")

# --- SIDEBAR: PANEL DE CONTROL DE SENSORES ---
st.sidebar.header("🕹️ Consola de Sensores")
q_input = st.sidebar.slider("Caudal de Entrada (Q) [m³/h]", 0, 500, 300)
t_input = st.sidebar.slider("Turbidez Detectada (T) [NTU]", 0, 150, 20)

st.sidebar.markdown("---")
st.sidebar.header("🔋 Eficiencia Energética")
horario = st.sidebar.select_slider("Franja Horaria", options=["Diurno (Punta)", "Nocturno (Valle)"])
presion_filtro = st.sidebar.slider("Presión Diferencial Filtro [bar]", 0.0, 3.0, 1.0, step=0.1)

# --- LÓGICA DE CONTROL INTELIGENTE ---
umbral_turbidez = 80
turbidez_fuera_rango = t_input > umbral_turbidez
estado_valvula = "CERRADA" if turbidez_fuera_rango else "ABIERTA"

# Regla de Motores: Apagar si el tanque está lleno (>90%) y hay poco caudal
motores_activos = True
# Nivel estimado para la lógica (basado en el último punto de la simulación previa o inicial)
# Para la lógica de control inmediata usamos una aproximación
if q_input < 100: # Simulación de demanda baja
    motores_activos = False

# --- CÁLCULO DE AHORRO ENERGÉTICO (Actividad E3) ---
consumo_base = 10000  # kWh base mensual
ahorro_total = 0

# 1. Ahorro por bombeo nocturno (800 kWh)
if horario == "Nocturno (Valle)":
    ahorro_total += 800

# 2. Ahorro por lavado de filtros (700 kWh)
# Se asume que el sistema "sabe" optimizar si la presión es controlada
if presion_filtro <= 1.5:
    ahorro_total += 700

# 3. Ahorro adicional del 5% por lavar a tiempo
if presion_filtro > 1.5:
    lavado_activo = True
    ahorro_total += (consumo_base * 0.05)
else:
    lavado_activo = False

consumo_final = consumo_base - ahorro_total

# --- SIMULACIÓN DE DATOS PARA GRÁFICAS ---
minutos = np.arange(0, 61, 1)

def simular_proceso():
    niveles = []
    nivel_act = 60.0
    cons_instantaneo = []
    
    for t in minutos:
        # Entrada de agua
        if turbidez_fuera_rango or (nivel_act > 95 and not motores_activos):
            q_ent = 0
        else:
            q_ent = q_input / 150
            
        # Salida (Demanda ciudad)
        consumo_ciudad = 1.8 
        
        nivel_act += (q_ent - consumo_ciudad / 10)
        nivel_act = max(min(nivel_act, 100), 0)
        niveles.append(nivel_act)
        
        # Consumo instantáneo simulado
        base_inst = 13.8 # (10000 / 720 horas al mes)
        reduccion = (ahorro_total / 720)
        cons_instantaneo.append(base_inst - reduccion + np.random.uniform(-0.2, 0.2))
        
    return niveles, cons_instantaneo

niveles_plot, energia_plot = simular_proceso()

# --- PANEL DE MÉTRICAS ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("💧 Estado Motores", "ACTIVOS" if motores_activos else "OFF (Ahorro)", 
              delta="Manual" if motores_activos else "IA Optimized")
with col2:
    st.metric("🚿 Lavado Filtro", "EJECUTANDO" if lavado_activo else "STANDBY", 
              delta=f"{presion_filtro} bar")
with col3:
    st.metric("🕒 Tarifa Actual", horario)
with col4:
    st.metric("📉 Consumo Mes", f"{int(consumo_final)} kWh", delta=f"-{int(ahorro_total)} kWh")

st.markdown("---")

# --- GRÁFICAS ---
f1_c1, f1_c2 = st.columns(2)

with f1_c1:
    fig_n = go.Figure()
    fig_n.add_trace(go.Scatter(x=minutos, y=niveles_plot, fill='tozeroy', name='Nivel %', line=dict(color='#0077B6')))
    fig_n.update_layout(title="📈 Nivel del Tanque (Control IA)", yaxis=dict(range=[0, 105]), template="plotly_white")
    st.plotly_chart(fig_n, use_container_width=True)

with f1_c2:
    fig_e = go.Figure()
    fig_e.add_trace(go.Scatter(x=minutos, y=[13.8]*61, name='Línea Base (Sin IA)', line=dict(color='grey', dash='dash')))
    fig_e.add_trace(go.Scatter(x=minutos, y=energia_plot, name='Consumo Smart-Plant', line=dict(color='#2ECC71', width=3)))
    fig_e.update_layout(title="⚡ Eficiencia Energética en Tiempo Real (kWh/h)", template="plotly_white")
    st.plotly_chart(fig_e, use_container_width=True)

# --- ALERTAS OPERATIVAS ---
st.subheader("📢 Centro de Notificaciones Inteligentes")
col_a, col_b = st.columns(2)

with col_a:
    if lavado_activo:
        st.warning(f"⚠️ Presión en filtro: {presion_filtro} bar. Iniciando lavado automático para ahorrar 5% energía.")
    else:
        st.success("✅ Presión de filtrado nominal. Lavado no requerido.")

with col_b:
    if niveles_plot[-1] > 90 and not motores_activos:
        st.error("🤖 IA: Tanque lleno y demanda baja. Motores APAGADOS para evitar rebose.")
    elif turbidez_fuera_rango:
        st.error("🛑 VÁLVULA CERRADA: Turbidez alta detectada.")
    else:
        st.info("💧 Suministro y caudal en rangos normales.")

# --- DATOS PARA EL REPORTE ---
with st.expander("📝 Desglose de Reglas de Eficiencia Aplicadas"):
    st.write(f"""
    - **Regla 1 (Horaria):** Ahorro de 800 kWh al detectar franja {horario}.
    - **Regla 2 (Mantenimiento):** Lavado optimizado de filtros ahorra 700 kWh.
    - **Regla 3 (Predictiva):** Lavado por presión diferencial (>1.5 bar) añade 5% de ahorro.
    - **Regla 4 (Anti-Rebose):** Gestión de motores activa según nivel de depósito.
    """)
