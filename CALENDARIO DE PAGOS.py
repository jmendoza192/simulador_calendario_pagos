import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf # Necesario para la TCEA
import plotly.express as px
from datetime import datetime

# 1. CONFIGURACIÓN E INTERFAZ
st.set_page_config(page_title="Simulador TCEA | Jancarlo Inmobiliario", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetric"] {
        background-color: #1f2630;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
    .tcea-card {
        background: linear-gradient(135deg, #1e3a8a, #1e40af);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #3b82f6;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PANEL LATERAL (INPUTS TÉCNICOS) ---
with st.sidebar:
    st.title("📑 Parámetros del Crédito")
    monto_prestamo = st.number_input("Monto del Préstamo (S/)", value=250000)
    valor_inmueble = st.number_input("Valor del Inmueble (S/)", value=300000)
    tea_input = st.number_input("TEA (%)", value=9.5)
    plazo_anos = st.slider("Plazo (Años)", 5, 30, 20)
    
    st.write("---")
    st.subheader("🛡️ Seguros")
    tasa_desgravamen = st.number_input("Seguro Desgravamen Mensual (%)", value=0.050, format="%.3f") / 100
    tasa_todo_riesgo = st.number_input("Seguro Todo Riesgo Mensual (%)", value=0.025, format="%.3f") / 100
    
    st.write("---")
    st.subheader("🎁 Beneficios")
    cuotas_dobles = st.checkbox("Cuotas Extras (Julio y Diciembre)", value=True)
    fecha_desembolso = st.date_input("Fecha de Desembolso", datetime.now())

# --- 3. LÓGICA FINANCIERA AVANZADA ---
def generar_cronograma_peruano():
    tem = (1 + tea_input/100)**(1/12) - 1
    n_meses = plazo_anos * 12
    seguro_inmueble_fijo = valor_inmueble * tasa_todo_riesgo
    
    # Determinamos los meses de cuota doble
    meses_dobles = []
    if cuotas_dobles:
        for i in range(1, n_meses + 1):
            mes_actual = (fecha_desembolso + pd.DateOffset(months=i)).month
            if mes_actual in [7, 12]:
                meses_dobles.append(i)
    
    # Cálculo de cuota constante (Aproximación para cuotas dobles + desgravamen)
    # Se usa un factor de anualidad ajustado por los meses donde se amortiza el doble
    divisor = 0
    for i in range(1, n_meses + 1):
        peso = 2 if i in meses_dobles else 1
        divisor += peso / (1 + tem + tasa_desgravamen)**i
    
    cuota_base = monto_prestamo / divisor
    
    saldo = monto_prestamo
    data = []
    flujos_tcea = [-monto_prestamo] # Para el cálculo de TIR/TCEA
    
    for i in range(1, n_meses + 1):
        mes_str = (fecha_desembolso + pd.DateOffset(months=i)).strftime('%b-%Y')
        
        interes_mes = saldo * tem
        seg_desgravamen = saldo * tasa_desgravamen
        seg_inmueble = seguro_inmueble_fijo
        
        es_doble = i in meses_dobles
        cuota_total = (cuota_base * 2 if es_doble else cuota_base) + seg_desgravamen + seg_inmueble
        
        amortizacion = (cuota_base * 2 if es_doble else cuota_base) - interes_mes
        saldo -= amortizacion
        
        data.append({
            "N°": i,
            "Mes": mes_str,
            "Saldo Inicial": round(saldo + amortizacion, 2),
            "Cuota Capital+Int": round(cuota_base * (2 if es_doble else 1), 2),
            "Interés": round(interes_mes, 2),
            "Desgravamen": round(seg_desgravamen, 2),
            "Todo Riesgo": round(seg_inmueble, 2),
            "Cuota Total": round(cuota_total, 2),
            "Saldo Final": round(max(0, saldo), 2)
        })
        flujos_tcea.append(cuota_total)

    # Cálculo de TCEA (TIR mensual convertida a anual)
    tir_mensual = npf.irr(flujos_tcea)
    tcea_calculada = ((1 + tir_mensual)**12 - 1) * 100
    
    return pd.DataFrame(data), tcea_calculada

df_cronograma, tcea_final = generar_cronograma_peruano()

# --- 4. DASHBOARD ---
st.title("📅 Cronograma con Seguros y Cuotas Extras")
st.write("---")

# Métricas Principales
col1, col2, col3, col4 = st.columns(4)
with col1:
    cuota_normal = df_cronograma[df_cronograma["N°"] == 1]["Cuota Total"].values[0]
    st.metric("Cuota Ordinaria", f"S/ {cuota_normal:,.2f}")
with col2:
    total_interes = df_cronograma["Interés"].sum()
    st.metric("Total Intereses", f"S/ {total_interes:,.2f}")
with col3:
    total_seguros = df_cronograma["Desgravamen"].sum() + df_cronograma["Todo Riesgo"].sum()
    st.metric("Total Seguros", f"S/ {total_seguros:,.2f}")
with col4:
    st.markdown(f"""<div class="tcea-card">
                <small style="color:#bfdbfe">TCEA ESTIMADA</small><br>
                <b style="font-size:1.8rem; color:white">{tcea_final:.2f}%</b>
                </div>""", unsafe_allow_html=True)

st.write("")

# Gráficos y Tabla
c_graf, c_tab = st.columns([1, 1.5])

with c_graf:
    st.subheader("📉 Evolución de la Deuda")
    fig = px.line(df_cronograma, x="N°", y="Saldo Final", title="Reducción del Principal")
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
    st.plotly_chart(fig, use_container_width=True)
    
    st.info(f"💡 **Nota:** La TCEA de **{tcea_final:.2f}%** es mayor a tu TEA de **{tea_input}%** porque incluye el costo de los seguros y el efecto de las cuotas dobles.")

with c_tab:
    st.subheader("🗓️ Detalle de Pagos")
    df_vis = df_cronograma.copy()
    # Formateo para vista
    cols_money = ["Saldo Inicial", "Interés", "Desgravamen", "Todo Riesgo", "Cuota Total", "Saldo Final"]
    for c in cols_money:
        df_vis[c] = df_vis[c].map("S/ {:,.2f}".format)
    
    st.dataframe(df_vis, height=500, use_container_width=True)

# --- 5. EXPORTACIÓN ---
csv = df_cronograma.to_csv(index=False).encode('utf-8')
st.download_button("📥 Descargar Cronograma Completo (Excel/CSV)", data=csv, file_name=f"Cronograma_TCEA_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
