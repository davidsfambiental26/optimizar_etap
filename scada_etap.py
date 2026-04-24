import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time

st.set_page_config(page_title="SCADA Eco-Sim Smart-Plant", layout="wide")

st.title("🚀 SCADA Eco-Sim: Simulación de Resiliencia")
st.markdown("""
Esta simulación muestra la **Parte C** de la guía: la respuesta del sistema ante una 
**caída del 40% del caudal** (escenario de sequía o fallo de captación).
""")

# --- SIDEBAR: SENSORES ---
st.sidebar.header("Panel de Sensores")
caudal_nominal = st.sidebar.slider("Caudal Nominal (m³/h)", 100, 500, 300)
turbidez = st.sidebar.slider("Turbidez (NTU)", 0, 150, 20)

# --- LÓGICA DE SIMULACIÓN DE NIVEL ---
def simular_caida_caudal(caudal_base):
    minutos = np.arange(0, 61, 1)
    nivel = []
    caudal_real = []
    actual_nivel = 70.0 # Nivel inicial 70%
    consumo_ciudad = caudal_base / 2 # La ciudad consume la mitad del nominal
    
    for t in minutos:
        # A los 10 minutos cae el caudal un 40%
        if t < 10:
            q_t = caudal_base
        elif t < 30:
            q_t = caudal_base * 0.6 # Caída del 40%
        else:
            # Recuperación parcial o estabilización mediante VFD
            q_t = caudal_base * 0.85 
        
        # El nivel cambia: (Entrada - Salida) / Factor de capacidad
        cambio = (q_t - consumo_ciudad) / 20
        actual_nivel += cambio
        actual_nivel = max(min(actual_nivel, 100), 0)
        
        nivel.append(actual_nivel)
        caudal_real.append(q_t)
        
    return minutos, nivel, caudal_real

minutos, niveles, caudales = simular_caida_caudal(caudal_nominal)

# --- VISUALIZACIÓN: GRÁFICO DE RESILIENCIA ---
fig = go.Figure()

# Línea de Nivel
fig.add_trace(go.Scatter(x=minutos, y=niveles, name="Nivel del Tanque (%)",
                         line=dict(color='royalblue', width=4)))

# Línea de Caudal (Eje secundario opcional, aquí lo ponemos en el mismo para ver la relación)
fig.add_trace(go.Scatter(x=minutos, y=[(c/caudal_nominal)*100 for c in caudales], 
                         name="Caudal Entrada (% del nominal)",
                         line=dict(color='firebrick', width=2, dash='dot')))

fig.update_layout(
    title="Curva de Resiliencia: Estabilización tras Caída de Caudal (40%)",
    xaxis_title="Tiempo (minutos)",
    yaxis_title="Porcentaje (%)",
    template="plotly_white",
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

# --- INDICADORES KPI ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Estado del Sistema", "RESILIENTE" if niveles[-1] > 20 else "CRÍTICO", delta=None)
with col2:
    st.metric("Nivel Final Tanque", f"{round(niveles[-1], 1)} %")
with col3:
    st.metric("Ahorro Energético (Regla B)", "15%", "-1.500 kWh")

# --- TABLA DE DATOS PARA EL DOSSIER ---
if st.checkbox("Mostrar datos de la simulación para el reporte"):
    df_sim = pd.DataFrame({"Minuto": minutos, "Nivel (%)": niveles, "Caudal (m3/h)": caudales})
    st.dataframe(df_sim)
