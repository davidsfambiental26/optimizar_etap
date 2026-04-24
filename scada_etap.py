import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="SCADA Eco-Sim v12.0 - Control Total", layout="wide")

st.title("🛡️ SCADA Eco-Sim: Monitorización de Procesos y Eficiencia")
st.markdown("---")

# --- SIDEBAR: SENSORES ---
st.sidebar.header("🕹️ Consola de Sensores")
q_input = st.sidebar.slider("Caudal de Entrada (Q) [m³/h]", 0, 500, 280)
t_input = st.sidebar.slider("Turbidez Detectada (T) [NTU]", 0, 150, 25)

st.sidebar.markdown("---")
st.sidebar.header("🔋 Gestión Energética")
horario = st.sidebar.select_slider("Franja Horaria", options=["Diurno (Punta)", "Nocturno (Valle)"])
presion_filtro = st.sidebar.slider("Presión Diferencial Filtro [bar]", 0.0, 3.0, 1.2, step=0.1)

# --- LÓGICA DE CONTROL ---
umbral_turbidez = 80
valvula_est = "ABIERTA" if t_input <= umbral_turbidez else "CERRADA"
# REGLA: Si P > 1.5 bar, se activa el lavado automático
filtrado_estado = "LAVANDO..." if presion_filtro > 1.5 else "FILTRANDO"

# --- SIMULACIÓN MATEMÁTICA ---
minutos = np.arange(0, 61, 1)

def simular_proceso():
    niveles = []
    energia = []
    nivel_act = 50.0 
    demanda_ciudad = 3.3 
    
    for t in minutos:
        # Entrada
        if valvula_est == "CERRADA":
            q_in = 0
        else:
            factor_q = 0.6 if t > 15 else 1.0
            q_in = (q_input * factor_q) / 60
            
        nivel_act += (q_in - demanda_ciudad)
        nivel_act = max(min(nivel_act, 100), 0)
        niveles.append(nivel_act)
        
        # Energía
        base_e = 13.0 + (q_input / 100)
        ahorro = 0
        if horario == "Nocturno (Valle)": ahorro += 2.0
        if presion_filtro <= 1.5: ahorro += 1.5
        if filtrado_estado == "LAVANDO...": ahorro += (base_e * 0.05)
        
        consumo_inst = base_e - ahorro
        energia.append(round(consumo_inst + np.random.uniform(-0.05, 0.05), 2))
        
    return niveles, energia

niveles, energia = simular_proceso()
nivel_f = int(niveles[-1])
cons_actual = energia[-1]

# --- 1. PANEL DE INSTRUMENTACIÓN (Métricas actualizadas) ---
st.subheader("📊 Panel de Instrumentación en Tiempo Real")
k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.metric("🌊 Caudal", f"{q_input} m³/h")
with k2:
    st.metric("👁️ Turbidez", f"{t_input} NTU")
with k3:
    st.metric("🚪 Válvula", valvula_est, delta="Normal" if valvula_est == "ABIERTA" else "Bypass")
with k4:
    st.metric("🚿 Estado Filtro", filtrado_estado, 
              delta=f"{presion_filtro} bar", 
              delta_color="normal" if filtrado_estado == "FILTRANDO" else "inverse")
with k5:
    st.metric("⚡ Consumo", f"{cons_actual:.2f} kWh/h", delta=f"{round(((cons_actual/14.5)-1)*100,1)}%")

st.markdown("---")

# --- 2. GRÁFICAS ---
col_g1, col_g2 = st.columns(2)

with col_g1:
    fig_n = go.Figure()
    fig_n.add_hrect(y0=0, y1=10, fillcolor="red", opacity=0.3, annotation_text="SEQUÍA EXTREMA")
    fig_n.add_hrect(y0=10, y1=30, fillcolor="orange", opacity=0.2, annotation_text="AVISO: NIVEL BAJO")
    fig_n.add_trace(go.Scatter(x=minutos, y=niveles, fill='tozeroy', name='Nivel (%)', line=dict(color='#0077B6', width=4)))
    fig_n.update_layout(title="📈 Curva de Nivel y Resiliencia", yaxis=dict(range=[0, 105]), template="plotly_white")
    st.plotly_chart(fig_n, use_container_width=True)

with col_g2:
    fig_e = go.Figure()
    fig_e.add_trace(go.Scatter(x=minutos, y=energia, name='Smart-ETAP', line=dict(color='#2ECC71', width=3)))
    fig_e.add_trace(go.Scatter(x=minutos, y=[14.5]*61, name='Línea Base', line=dict(color='grey', dash='dot')))
    fig_e.update_layout(title="⚡ Detalle de Eficiencia Energética (kWh/h)", template="plotly_white")
    st.plotly_chart(fig_e, use_container_width=True)

# --- 3. ALERTAS DE SISTEMA ---
st.subheader("📢 Notificaciones de Control")

# Prioridad 1: Nivel Crítico
if nivel_f <= 10:
    st.error(f"🚨 RIESGO DE SEQUÍA EXTREMA: Depósito al {nivel_f}%. Suministro insuficiente.")
# Prioridad 2: Nivel Bajo
elif 10 < nivel_f <= 30:
    st.warning(f"⚠️ AVISO: RIESGO DE NIVEL BAJO. Nivel actual: {nivel_f}%. Incrementar entrada.")
# Prioridad 3: Calidad
elif valvula_est == "CERRADA":
    st.error(f"🛑 CALIDAD: Válvula CERRADA por turbidez alta ({t_input} NTU).")
# Prioridad 4: Mantenimiento
if filtrado_estado == "LAVANDO...":
    st.info(f"🧼 MANTENIMIENTO: Presión en {presion_filtro} bar. Lavado de filtros activado automáticamente.")
elif nivel_f > 30 and valvula_est == "ABIERTA":
    st.success("✅ OPERACIÓN NORMAL: Sistema estable y bajo control.")

# --- 4. INFORME FINAL ---
st.markdown("---")
st.header("📋 Informe Ejecutivo de Operación")
inf1, inf2, inf3 = st.columns(3)

with inf1:
    st.write("**Resumen de Activos**")
    st.write(f"- Válvula de Entrada: {valvula_est}")
    st.write(f"- Ciclo de Filtrado: {filtrado_estado}")
    st.write(f"- Presión Diferencial: {presion_filtro} bar")

with inf2:
    st.write("**Análisis de Suministro**")
    st.write(f"- Nivel Final Depósito: {nivel_f}%")
    st.write(f"- Seguridad Hídrica: {'CRÍTICA' if nivel_f <= 30 else 'ÓPTIMA'}")

with inf3:
    st.write("**Auditoría de Eficiencia**")
    ahorro = 14.5 - cons_actual
    st.write(f"- Ahorro por Gestión: {ahorro:.2f} kWh/h")
    st.write(f"- Objetivo 15% Alcaidado: {'SÍ' if (ahorro/14.5) >= 0.15 else 'NO'}")
