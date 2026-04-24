import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="SCADA Eco-Sim v10.0 - Control Integrado", layout="wide")

st.title("🛡️ SCADA Eco-Sim: Monitorización de Calidad, Resiliencia y Energía")
st.markdown("---")

# --- SIDEBAR: SENSORES ---
st.sidebar.header("🕹️ Consola de Sensores")
q_input = st.sidebar.slider("Caudal de Entrada (Q) [m³/h]", 0, 500, 300)
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
    nivel_act = 55.0
    demanda_ciudad = 3.6 # Consumo elevado para permitir vaciado si Q es bajo
    
    for t in minutos:
        # Lógica de entrada de agua
        if valvula_est == "CERRADA":
            q_in = 0
        else:
            # Caída del 40% por resiliencia a partir del min 15
            factor_q = 0.6 if t > 15 else 1.0
            q_in = (q_input * factor_q) / 60
            
        # Balance Hídrico
        nivel_act += (q_in - demanda_ciudad)
        nivel_act = max(min(nivel_act, 100), 0)
        niveles.append(nivel_act)
        
        # Consumo Eléctrico Dinámico (kWh/h)
        base_e = 13.0 + (q_input / 100)
        ahorro = 0
        if horario == "Nocturno (Valle)": ahorro += 2.0
        if presion_filtro <= 1.5: ahorro += 1.5
        if lavado_req: ahorro += (base_e * 0.06) # 6% ahorro extra por eficiencia
        
        consumo_inst = base_e - ahorro
        energia.append(round(consumo_inst + np.random.uniform(-0.05, 0.05), 2))
        
    return niveles, energia

niveles, energia = simular_proceso()
nivel_f = int(niveles[-1])
cons_actual = energia[-1]

# --- 1. FILA DE AVISOS Y KPIs (RESTAURADA) ---
st.subheader("📊 Indicadores de Sensores en Tiempo Real")
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.metric("🌊 Caudal", f"{q_input} m³/h")
with kpi2:
    st.metric("👁️ Turbidez", f"{t_input} NTU", 
              delta="ALTA" if t_input > umbral_turbidez else "OK", 
              delta_color="inverse" if t_input > umbral_turbidez else "normal")
with kpi3:
    st.metric("🚪 Válvula", valvula_est)
with kpi4:
    st.metric("⚡ Energía", f"{cons_actual:.2f} kWh/h", 
              delta=f"-{round(14.5-cons_actual,1)} kWh")
with kpi5:
    st.metric("🚿 Filtro", f"{presion_filtro} bar", 
              delta="LAVAR" if lavado_req else "OK", 
              delta_color="inverse" if lavado_req else "normal")

st.markdown("---")

# --- 2. GRÁFICAS ---
col_g1, col_g2 = st.columns(2)

with col_g1:
    fig_n = go.Figure()
    fig_n.add_hrect(y0=0, y1=10, fillcolor="red", opacity=0.3, annotation_text="SEQUÍA EXTREMA")
    fig_n.add_trace(go.Scatter(x=minutos, y=niveles, fill='tozeroy', name='Nivel (%)', line=dict(color='#0077B6', width=4)))
    fig_n.update_layout(title="📈 Nivel del Depósito (Vaciado vs Llenado)", yaxis=dict(range=[0, 105]), template="plotly_white")
    st.plotly_chart(fig_n, use_container_width=True)

with col_g2:
    fig_e = go.Figure()
    fig_e.add_trace(go.Scatter(x=minutos, y=energia, name='Smart-ETAP (Optimizado)', line=dict(color='#2ECC71', width=3)))
    fig_e.add_trace(go.Scatter(x=minutos, y=[14.5]*61, name='Consumo Convencional', line=dict(color='grey', dash='dot')))
    fig_e.update_layout(title="⚡ Detalle de Consumo Energético", yaxis=dict(range=[min(energia)-1, 16]), template="plotly_white")
    st.plotly_chart(fig_e, use_container_width=True)

# --- 3. ALERTAS DE SISTEMA (NOTIFICACIONES) ---
if nivel_f <= 10:
    st.error(f"🚨 RIESGO DE SEQUÍA EXTREMA: Depósito al {nivel_f}%. La salida supera a la entrada.")
elif t_input > umbral_turbidez:
    st.error(f"🛑 CALIDAD CRÍTICA: Válvula CERRADA por Turbidez ({t_input} NTU).")
elif lavado_req:
    st.warning(f"🧼 MANTENIMIENTO: Iniciando lavado de filtros por alta presión ({presion_filtro} bar).")
else:
    st.success("✅ OPERACIÓN NORMAL: Todos los parámetros están dentro del rango.")

# --- 4. INFORME EJECUTIVO FINAL ---
st.markdown("---")
st.header("📋 Informe de Auditoría y Sostenibilidad")

inf1, inf2, inf3 = st.columns(3)

with inf1:
    st.write("**Resumen de Suministro**")
    st.write(f"- Estado Tanque Tratada: {nivel_f}%")
    st.write(f"- Estado Válvula Entrada: {valvula_est}")
    st.write(f"- Balance Hídrico: {'Déficit' if niveles[0] > niveles[-1] else 'Superávit'}")

with inf2:
    st.write("**Eficiencia Energética**")
    ahorro_real = 14.5 - cons_actual
    eficiencia = (ahorro_real / 14.5) * 100
    st.write(f"- Ahorro Estimado: {ahorro_real:.2f} kWh/h")
    st.write(f"- Mejora de Eficiencia: {eficiencia:.1f}%")

with inf3:
    st.write("**Recomendaciones Operativas**")
    if nivel_f < 30: st.write("👉 Aumentar captación de agua bruta.")
    if horario == "Diurno (Punta)": st.write("👉 Desplazar cargas pesadas a la noche.")
    if t_input > 40: st.write("👉 Vigilar sedimentación en decantadores.")

# Expander con los datos crudos para el dossier
with st.expander("Ver tabla de datos detallada"):
    df_final = pd.DataFrame({"Minuto": minutos, "Nivel (%)": niveles, "Energía (kWh/h)": energia})
    st.dataframe(df_final)
