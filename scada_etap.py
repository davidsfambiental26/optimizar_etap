import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="SCADA Eco-Sim v3.0", layout="wide")

# Título y encabezado profesional
st.title("🛡️ SCADA Eco-Sim: Control Inteligente de ETAP")
st.markdown("---")

# --- SIDEBAR: CONTROL DE SENSORES EN TIEMPO REAL ---
st.sidebar.header("🕹️ Simulación de Sensores")
q_input = st.sidebar.slider("Caudal de Entrada (Q) [m³/h]", 0, 500, 300)
t_input = st.sidebar.slider("Turbidez Detectada (T) [NTU]", 0, 150, 20)

# --- LÓGICA DE PROCESAMIENTO (REGLAS DE INGENIERÍA) ---
umbral_critico = 80
es_emergencia = t_input > umbral_critico

# Regla A: Dosificación proporcional (Q * T) / 100
# Si hay emergencia, la dosificación se detiene por seguridad
dosificacion = 0.0 if es_emergencia else (q_input * t_input) / 100

# Regla B: Consumo proyectado (Eficiencia Energética)
# El consumo es constante pero se muestra el ahorro del 15% aplicado
consumo_base = 250.0 
consumo_proyectado = consumo_base * 0.85 # Aplicando el ahorro del 15% solicitado

# --- GENERACIÓN DE LA CURVA DE RESILIENCIA ---
def generar_curva(caudal_act, emergencia):
    minutos = np.arange(0, 61, 1)
    niveles = []
    nivel_actual = 65.0
    
    for t in minutos:
        # Simulación de caída del 40% a mitad del tiempo
        caudal_t = caudal_act
        if 15 < t < 40:
            caudal_t = caudal_act * 0.6
        
        # Si hay emergencia por turbidez, la entrada al tanque es 0 (Bypass activo)
        entrada = 0 if emergencia else (caudal_t / 15)
        salida = consumo_proyectado / 150
        
        nivel_actual += (entrada - salida)
        nivel_actual = max(min(nivel_actual, 100), 0)
        niveles.append(nivel_actual)
    return minutos, niveles

minutos, niveles = generar_curva(q_input, es_emergencia)

# --- VISUALIZACIÓN DE PARÁMETROS (KPIs) ---
# Estos son los parámetros que solicitaste que aparecieran junto a la gráfica
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🌊 Caudal Entrada", f"{q_input} m³/h")
with col2:
    color_t = "normal" if not es_emergencia else "inverse"
    st.metric("👁️ Turbidez Detectada", f"{t_input} NTU", delta="CRÍTICO" if es_emergencia else None, delta_color=color_t)
with col3:
    st.metric("🧪 Dosif. Químicos", f"{dosificacion:.2f} L/h")
with col4:
    st.metric("⚡ Consumo Proyectado", f"{consumo_proyectado:.1f} kWh", delta="-15% Ahorro")

# --- GRÁFICA DE CONTROL DE NIVEL ---
fig = go.Figure()

# Sombreado de zonas críticas
fig.add_hrect(y0=0, y1=10, fillcolor="red", opacity=0.1, annotation_text="SEQUÍA EXTREMA")
fig.add_hrect(y0=10, y1=30, fillcolor="orange", opacity=0.1, annotation_text="NIVEL MÍNIMO")

fig.add_trace(go.Scatter(
    x=minutos, 
    y=niveles, 
    mode='lines',
    name='Nivel Tanque Tratada',
    line=dict(color='#0072B2', width=4),
    fill='tozeroy'
))

fig.update_layout(
    title="Análisis de Resiliencia: Curva de Nivel vs Eventos de Caudal",
    xaxis_title="Tiempo de Operación (minutos)",
    yaxis_title="Nivel del Depósito (%)",
    yaxis=dict(range=[0, 105]),
    template="plotly_white",
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# --- ALERTAS DEL SISTEMA ---
if es_emergencia:
    st.error(f"🚨 ALERTA DE CALIDAD: Turbidez ({t_input} NTU) por encima del umbral. Válvula de entrada CERRADA. Bypass a Tanque de Seguridad activo.")
elif niveles[-1] < 10:
    st.warning("🚨 ALERTA DE SUMINISTRO: Nivel de depósito por debajo del 10%. Riesgo de desabastecimiento urbano.")
else:
    st.success("✅ Sistema operando dentro de los parámetros nominales.")

# --- EXPORTACIÓN PARA DOSSIER ---
if st.button("Generar Resumen para Informe Ejecutivo"):
    st.write("### Resumen de Reglas Aplicadas")
    st.table(pd.DataFrame({
        "Parámetro": ["Ahorro Energético", "Lógica Dosificación", "Seguridad por Turbidez"],
        "Estado": ["Activo (8.500 kWh/mes)", f"Dinámica ({dosificacion:.2f} L/h)", "Bypass Automático"],
        "Resultado": ["15% reducción", "Optimización Químicos", "Protección de Filtros"]
    }))
