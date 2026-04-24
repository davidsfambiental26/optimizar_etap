import streamlit as st
import pandas as pd
import numpy as np
import datetime

# Configuración de página para que se adapte a cualquier pantalla
st.set_page_config(
    page_title="SCADA Eco-Sim | ETAP Smart",
    page_icon="💧",
    layout="wide"
)

# Estilos CSS para simular una estética industrial
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🌊 SCADA Eco-Sim: Smart-Plant ETAP")
st.info("Sistema de Control y Adquisición de Datos - Oficina Técnica de Ingeniería")

# --- SIDEBAR: CONTROLES ---
st.sidebar.header("🕹️ Panel de Simulación")
caudal = st.sidebar.slider("Caudal de Entrada (Q) [m3/h]", 0, 500, 250)
turbidez = st.sidebar.slider("Turbidez (T) [NTU]", 0, 150, 20)
tarifa_valle = st.sidebar.toggle("Horario Valle (Bajo Consumo)", value=True)

# --- LÓGICA DE CONTROL (Basada en la Guía E3) ---
umbral_critico = 80
estado_valvula = "ABIERTA"
alerta = False

if turbidez > umbral_critico:
    estado_valvula = "CERRADA (Desvío a Tanque Seguridad)"
    alerta = True
    dosificacion = 0
else:
    # Lógica proporcional: Q x T
    dosificacion = (caudal * turbidez) / 100

# Cálculo de Eficiencia Energética (Parte B)
consumo_base = 10000 
consumo_actual = 8200 if tarifa_valle else 10000

# --- DASHBOARD PRINCIPAL ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Caudal de Entrada", f"{caudal} m³/h")
    st.write(f"**Válvula:** `{estado_valvula}`")
    if alerta:
        st.error("🚨 CRÍTICO: Turbidez fuera de rango")

with col2:
    st.metric("Turbidez detectada", f"{turbidez} NTU")
    # Barra visual de nivel de suciedad
    st.progress(min(turbidez / 150, 1.0))

with col3:
    st.metric("Dosificación Químicos", f"{dosificacion:.2f} L/h")
    st.metric("Consumo Proyectado", f"{consumo_actual} kWh/mes", 
              delta=f"-{consumo_base - consumo_actual} kWh" if tarifa_valle else None)

# --- GRÁFICO DE RESILIENCIA (Parte C) ---
st.divider()
st.subheader("📊 Monitoreo de Resiliencia (Simulación de Sequía)")
data = pd.DataFrame({
    'Minutos': np.arange(60),
    'Nivel Tanque (%)': np.random.uniform(85, 95, 60)
})
# Simular caída si el caudal es bajo
if caudal < 150:
    data['Nivel Tanque (%)'] = data['Nivel Tanque (%)'] - 20
    st.warning("⚠️ Detectada baja presión por sequía. Ajustando Variadores de Frecuencia.")

st.line_chart(data, x='Minutos', y='Nivel Tanque (%)')

# --- REPORTE DE SOSTENIBILIDAD (Parte D) ---
with st.expander("🍀 Ver Informe de Impacto Ambiental"):
    ahorro = consumo_base - consumo_actual
    co2 = ahorro * 0.25
    st.write(f"**Reducción de Huella de Carbono:** {co2} kg de CO2/mes")
    st.write("**Economía Circular:** Optimización de lodos mediante dosificación precisa.")
