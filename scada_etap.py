import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="SCADA Eco-Sim v9.0 - Informe Pro", layout="wide")

st.title("🛡️ SCADA Eco-Sim: Control Total e Informe de Eficiencia")
st.markdown("---")

# --- SIDEBAR: SENSORES ---
st.sidebar.header("🕹️ Consola de Sensores")
q_input = st.sidebar.slider("Caudal de Entrada (Q) [m³/h]", 0, 500, 280)
t_input = st.sidebar.slider("Turbidez Detectada (T) [NTU]", 0, 150, 22)

st.sidebar.markdown("---")
st.sidebar.header("🔋 Gestión Energética")
horario = st.sidebar.select_slider("Franja Horaria", options=["Diurno (Punta)", "Nocturno (Valle)"])
presion_filtro = st.sidebar.slider("Presión Diferencial Filtro [bar]", 0.0, 3.0, 1.2, step=0.1)

# --- LÓGICA DE CONTROL ---
umbral_turbidez = 80
valvula_est = "ABIERTA" if t_input <= umbral_turbidez else "CERRADA"
lavado_req = presion_filtro > 1.5

# --- SIMULACIÓN ---
minutos = np.arange(0, 61, 1)

def simular_todo():
    niveles = []
    energia = []
    nivel_act = 45.0
    demanda_ciudad = 3.2 # Consumo de la red
    
    for t in minutos:
        # Lógica de entrada
        if valvula_est == "CERRADA":
            q_in = 0
        else:
            factor_q = 0.6 if t > 15 else 1.0 # Caída por resiliencia
            q_in = (q_input * factor_q) / 65
            
        nivel_act += (q_in - demanda_ciudad)
        nivel_act = max(min(nivel_act, 100), 0)
        niveles.append(nivel_act)
        
        # Energía con detalle (kWh/h)
        base_e = 12.0 + (q_input / 80)
        ahorro = 0
        if horario == "Nocturno (Valle)": ahorro += 2.5
        if presion_filtro <= 1.5: ahorro += 1.2
        if lavado_req: ahorro += (base_e * 0.07) # 7% ahorro por limpieza
        
        energia.append(round(base_e - ahorro + np.random.uniform(-0.05, 0.05), 2))
        
    return niveles, energia

niveles, energia = simular_todo()
nivel_f = int(niveles[-1])
cons_act = energia[-1]

# --- GRÁFICAS DETALLADAS ---
col_g1, col_g2 = st.columns(2)

with col_g1:
    fig_n = go.Figure()
    fig_n.add_hrect(y0=0, y1=10, fillcolor="red", opacity=0.3, annotation_text="SEQUÍA EXTREMA")
    fig_n.add_trace(go.Scatter(x=minutos, y=niveles, fill='tozeroy', name='Nivel (%)', line=dict(color='#0077B6', width=4)))
    fig_n.update_layout(title="📈 Nivel del Depósito (Simulación 60 min)", yaxis=dict(range=[0, 105]), template="plotly_white")
    st.plotly_chart(fig_n, use_container_width=True)

with col_g2:
    fig_e = go.Figure()
    fig_e.add_trace(go.Scatter(x=minutos, y=energia, name='Consumo Smart-Plant', line=dict(color='#2ECC71', width=3)))
    fig_e.add_trace(go.Scatter(x=minutos, y=[14.5]*61, name='Línea Base Convencional', line=dict(color='grey', dash='dot')))
    fig_e.update_layout(title="⚡ Detalle Consumo Energético (kWh/h)", yaxis=dict(range=[min(energia)-1, 16]), template="plotly_white")
    st.plotly_chart(fig_e, use_container_width=True)

# --- INFORME FINAL Y RECOMENDACIONES ---
st.markdown("---")
st.header("📋 Informe Ejecutivo de Operación y Sostenibilidad")

inf1, inf2, inf3 = st.columns(3)

with inf1:
    st.subheader("🛠️ Estado de Activos")
    st.write(f"**Válvula de Entrada:** {valvula_est}")
    st.write(f"**Tanque de Seguridad:** {'ACTIVO (Recibiendo agua)' if valvula_est == 'CERRADA' else 'STANDBY'}")
    st.write(f"**Sistema de Lavado:** {'INICIADO' if lavado_req else 'DESACTIVADO'}")

with inf2:
    st.subheader("💧 Situación del Suministro")
    if nivel_f <= 10:
        st.error(f"ESTADO: SEQUÍA EXTREMA ({nivel_f}%)")
        st.write("⚠️ **Acción:** Realizar cortes programados en red urbana.")
    elif nivel_f <= 30:
        st.warning(f"ESTADO: NIVEL MÍNIMO ({nivel_f}%)")
        st.write("⚠️ **Acción:** Aumentar caudal de captación inmediatamente.")
    else:
        st.success(f"ESTADO: SUMINISTRO NORMAL ({nivel_f}%)")
        st.write("✅ **Acción:** Mantener régimen de bombeo actual.")

with inf3:
    st.subheader("🌱 Auditoría Energética")
    ahorro_est = 14.5 - cons_act
    porcentaje = (ahorro_est / 14.5) * 100
    st.write(f"**Ahorro Actual:** {ahorro_est:.2f} kWh/h")
    st.write(f"**Eficiencia:** {porcentaje:.1f}% de reducción")
    if porcentaje >= 15:
        st.success("🎯 Objetivo de la Guía Eco-Sim cumplido.")
    else:
        st.info("📉 Objetivo del 15% aún no alcanzado.")

st.info("💡 **Recomendación IA:** " + 
        ("Active el modo nocturno para maximizar el ahorro económico." if horario == "Diurno (Punta)" else "Régimen de ahorro nocturno óptimo.") + 
        (" El filtro requiere limpieza para mejorar el flujo." if presion_filtro > 1.5 else " Presión de filtrado excelente."))
