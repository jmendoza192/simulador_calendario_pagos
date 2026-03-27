import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Simulador de Pagos | Jancarlo Inmobiliario", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stTable { background-color: #1f2630; border-radius: 10px; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.8rem !important; }
    div[data-testid="stMetric"] {
        background-color: #1f2630;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LÓGICA DE AMORTIZACIÓN ---
def calcular_cronograma(monto, tea, plazo_anos, fecha_inicio):
    tem = (1 + tea/100)**(1/12) - 1
    n_cuotas = plazo_anos * 12
    cuota_base = monto * (tem * (1 + tem)**n_cuotas) / ((1 + tem)**n_cuotas - 1)
    
    saldo = monto
    cronograma = []
    
    for i in range(1, n_cuotas + 1):
        interes = saldo * tem
        principal = cuota_base - interes
        saldo -= principal
        
        # Ajuste por redondeo en la última cuota
        if i == n_cuotas:
            principal += saldo
            saldo = 0
            
        cronograma.append({
            "N° Cuota": i,
            "Mes": (fecha_inicio + pd.DateOffset(months=i-1)).strftime('%b-%Y'),
            "Saldo Inicial": round(saldo + principal, 2),
            "Cuota": round(cuota_base, 2),
            "Interés": round(interes, 2),
            "Amortización": round(principal, 2),
            "Saldo Final": round(max(0, saldo), 2)
        })
    return pd.DataFrame(cronograma)

# --- 3. PANEL LATERAL ---
with st.sidebar:
    st.title("📑 Parámetros del Crédito")
    monto_prestamo = st.number_input("Monto del Préstamo (S/)", min_value=1000, value=250000, step=5000)
    tea_input = st.number_input("TEA (%)", min_value=1.0, value=9.5, step=0.1)
    plazo_input = st.slider("Plazo (Años)", 5, 30, 20)
    fecha_desembolso = st.date_input("Fecha de Desembolso", datetime.now())

# --- 4. CÁLCULOS Y DASHBOARD ---
df_cronograma = calcular_cronograma(monto_prestamo, tea_input, plazo_input, fecha_desembolso)
total_pagado = df_cronograma["Cuota"].sum()
total_interes = df_cronograma["Interés"].sum()
cuota_mensual = df_cronograma["Cuota"].iloc[0]

st.title("📅 Simulación de Calendario de Pagos")
st.write("---")

# Métricas Principales
m1, m2, m3 = st.columns(3)
m1.metric("Cuota Mensual Estimada", f"S/ {cuota_mensual:,.2f}")
m2.metric("Total Intereses", f"S/ {total_interes:,.2f}")
m3.metric("Total a Pagar", f"S/ {total_pagado:,.2f}")

st.write("")

# Gráfico de Composición de la Cuota
col_chart, col_table = st.columns([1, 1.5])

with col_chart:
    st.subheader("📊 Evolución del Saldo")
    fig = px.area(df_cronograma, x="N° Cuota", y="Saldo Final", 
                  title="Reducción de la Deuda en el Tiempo",
                  color_discrete_sequence=['#3b82f6'])
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
    st.plotly_chart(fig, use_container_width=True)
    
    # Donut Chart: Capital vs Interés
    data_pie = pd.DataFrame({
        "Concepto": ["Capital", "Intereses"],
        "Monto": [monto_prestamo, total_interes]
    })
    fig_pie = px.pie(data_pie, values="Monto", names="Concepto", hole=0.5,
                     color_discrete_sequence=['#10b981', '#ef4444'],
                     title="Composición Total del Pago")
    fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white")
    st.plotly_chart(fig_pie, use_container_width=True)

with col_table:
    st.subheader("🗓️ Tabla de Amortización")
    # Formatear la tabla para visualización
    df_mostrar = df_cronograma.copy()
    for col in ["Saldo Inicial", "Cuota", "Interés", "Amortización", "Saldo Final"]:
        df_mostrar[col] = df_mostrar[col].map("S/ {:,.2f}".format)
    
    st.dataframe(df_mostrar, height=600, use_container_width=True)

# --- 5. EXPORTACIÓN ---
st.write("---")
if st.button("📥 Generar Reporte de Cronograma"):
    st.success("Cronograma listo para exportar (Simulación completa)")
    csv = df_cronograma.to_csv(index=False).encode('utf-8')
    st.download_button("Descargar Excel (CSV)", data=csv, file_name="cronograma_pagos.csv", mime="text/csv")