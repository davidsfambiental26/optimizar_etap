import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from math import floor

st.set_page_config(page_title="SCADA Smart-Plant v5.0", layout="wide")

st.title("⚙️ SCADA Eco-Sim: Monitorización Avanzada ETAP")
st.markdown("---")

# --- SIDEBAR: CONTROL DE SENSORES ---
st.sidebar.header("🕹️ Consola de Sensores")
q_input = st.sidebar.slider("Caudal de Entrada (Q) [m³/h]", 0, 500, 300)
t_input = st.sidebar.slider("Turbidez Detectada (T) [NTU]", 0, 150, 20)

# --- LÓGICA DE CONTROL ---
umbral_turbidez = 80
turbidez_fuera_rango = t_input > umbral_turbidez
estado_valvula = "CERRADA" if turbidez_fuera_rango else "ABIERTA"
dosificacion = 0.0 if turbidez_fuera_rango else (q_input * t_input) / 100

# --- CÁLCULO DE DATOS PARA GRÁFICAS ---
minutos = np.arange(0, 61, 1)

# 1. Simulación de Nivel
def calc_nivel():
    niveles = []
    nivel_act = 55.0
    consumo_red = 2.0
    for t in minutos:
        q_ent = 0 if turbidez_fuera_rango else (q_input / 150)
        if 20 < t < 45 and not turbidez_fuera_rango:
            q_ent *= 0.6 # Caída del 40% (Parte C)
        nivel_act += (q_ent - consumo_red / 10)
        nivel_act = max(min(nivel_act, 100), 0)
        niveles.append(nivel_act)
    return niveles

# 2. Simulación de Consumo Energético (Parte B)
# Convencional: 10.000 kWh/mes -> ~13.8 kWh constante
# Optimizado: 8.500 kWh/mes -> ~11.8 kWh (con fluctuaciones por ahorro)
cons_conv = [13.8] * 61
cons_opt = [11.8 + (np.sin(t/5) * 0.5) for t in minutos]

niveles_plot = calc_nivel()

# --- PANEL DE INDICADORES SUPERIORES ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🌊 Caudal Entrada", f"{q_input} m³/h")
with col2:
    st.metric("🧪 Dosificación", f"{dosificacion:.1f} L/h")
with col3:
    st.metric("🚪 Válvula", estado_valvula, delta="OK" if not turbidez_fuera_rango else "BYPASS", 
              delta_color="normal" if not turbidez_fuera_rango else "inverse")
with col4:
    st.metric("⚡ Ahorro Energía", "15%", "-1.500 kWh/mes")

st.markdown("---")

# --- DISEÑO DE GRÁFICAS (2 COLUMNAS) ---
fila1_col1, fila1_col2 = st.columns(2)

with fila1_col1:
    # GRÁFICA 1: NIVEL DEL TANQUE
    fig_nivel = go.Figure()
    fig_nivel.add_trace(go.Scatter(x=minutos, y=niveles_plot, fill='tozeroy', 
                                   name='Nivel (%)', line=dict(color='#00B4D8', width=3)))
    fig_nivel.update_layout(title="📈 Nivel del Depósito de Agua Tratada", 
                            yaxis=dict(range=[0, 105]), template="plotly_white")
    st.plotly_chart(fig_nivel, use_container_width=True)

with fila1_col2:
    # GRÁFICA 2: CONSUMO ENERGÉTICO (CONVENCIONAL VS OPTIMIZADO)
    fig_ener = go.Figure()
    fig_ener.add_trace(go.Scatter(x=minutos, y=cons_conv, name='ETAP Convencional', 
                                  line=dict(color='grey', dash='dash')))
    fig_ener.add_trace(go.Scatter(x=minutos, y=cons_opt, name='Smart-ETAP (Eco-Sim)', 
                                  line=dict(color='#2ECC71', width=3)))
    fig_ener.update_layout(title="⚡ Comparativa Consumo Energético (kWh)", 
                            template="plotly_white")
    st.plotly_chart(fig_ener, use_container_width=True)

# --- SECCIÓN DE ALERTAS ---
perc_final = floor(niveles_plot[-1])

if turbidez_fuera_rango:
    st.error(f"🛑 VÁLVULA CERRADA: Turbidez crítica ({t_input} NTU).")
else:
    st.success("✅ VÁLVULA ABIERTA: Calidad de agua óptima.")

if perc_final <= 10:
    st.error(f"🚨 RIESGO DE SEQUÍA EXTREMA: El nivel actual es {perc_final}%.")
elif perc_final <= 30:
    st.warning(f"🟡 AVISO: Nivel mínimo en depósito ({perc_final}%).")
else:
    st.info(f"💧 Suministro estable: {perc_final}% de reserva.")

# --- TABLA RESUMEN PARA EL REPOSITORIO ---
with st.expander("Ver tabla de optimización energética (Dato para el Dossier)"):
    df_comparativo = pd.DataFrame({
        "Métrica": ["Consumo Mensual", "Costo Operativo", "Huella CO2"],
        "Antes (Convencional)": ["10.000 kWh", "1.500 €", "2.500 kg"],
        "Después (Eco-Sim)": ["8.500 kWh", "1.275 €", "2.125 kg"],
        "Ahorro": ["15%", "15%", "15%"]
    })
    st.table(df_comparativo)
