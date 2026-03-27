import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
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
    .nota-box {
        background-color: #161b22;
        padding: 15px;
        border-left: 5px solid #d1a435;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. PANEL LATERAL ---
with st.sidebar:
    st.title("📑 Parámetros del Crédito")
    monto_prestamo = st.number_input("Monto del Préstamo (S/)", value=250000)
    valor_inmueble = st.number_input("Valor del Inmueble (S/)", value=300000)
    tea_input = st.number_input("TEA (%)", value=9.5)
    plazo_anos = st.slider("Plazo (Años)", 5, 30, 20)
    
    st.write("---")
    st.subheader("🛡️ Seguros Mensuales")
    tasa_desgravamen = st.number_input("Seguro Desgravamen (%)", value=0.050, format="%.3f") / 100
    tasa_todo_riesgo = st.number_input("Seguro Todo Riesgo (%)", value=0.025, format="%.3f") / 100
    
    st.write("---")
    st.subheader("🎁 Estructura de Pagos")
    cuotas_dobles = st.checkbox("Cuotas Extras (Julio y Diciembre)", value=True)
    fecha_desembolso = st.date_input("Fecha de Desembolso", datetime.now())

# --- 3. LÓGICA DE CÁLCULO ---
def generar_cronograma():
    tem = (1 + tea_input/100)**(1/12) - 1
    n_meses = plazo_anos * 12
    seg_inmueble_fijo = valor_inmueble * tasa_todo_riesgo
    
    meses_dobles = []
    if cuotas_dobles:
        for i in range(1, n_meses + 1):
            mes_actual = (fecha_desembolso + pd.DateOffset(months=i)).month
            if mes_actual in [7, 12]: meses_dobles.append(i)
    
    # Factor para cuota constante con cuotas dobles
    divisor = sum((2 if i in meses_dobles else 1) / (1 + tem + tasa_desgravamen)**i for i in range(1, n_meses + 1))
    cuota_base = monto_prestamo / divisor
    
    saldo = monto_prestamo
    data = []
    flujos = [-monto_prestamo]
    
    for i in range(1, n_meses + 1):
        f_actual = fecha_desembolso + pd.DateOffset(months=i)
        interes_mes = saldo * tem
        seg_des = saldo * tasa_desgravamen
        es_doble = i in meses_dobles
        
        c_cap_int = cuota_base * (2 if es_doble else 1)
        amortizacion = c_cap_int - interes_mes
        cuota_total = c_cap_int + seg_des + seg_inmueble_fijo
        
        saldo -= amortizacion
        
        data.append({
            "N°": i,
            "Mes": f_actual.strftime('%b-%Y'),
            "Tipo": "DOBLE" if es_doble else "ORDINARIA",
            "Saldo Inicial": round(saldo + amortizacion, 2),
            "Cuota Cap+Int": round(c_cap_int, 2),
            "Interés": round(interes_mes, 2),
            "Seg. Desgravamen": round(seg_des, 2),
            "Seg. Todo Riesgo": round(seg_inmueble_fijo, 2),
            "Cuota Total": round(cuota_total, 2),
            "Saldo Final": round(max(0, saldo), 2)
        })
        flujos.append(cuota_total)

    tcea = ((1 + npf.irr(flujos))**12 - 1) * 100
    return pd.DataFrame(data), tcea

df_cronograma, tcea_final = generar_cronograma()

# --- 4. DASHBOARD ---
st.title("📅 Simulador de Cronograma Inmobiliario")
st.write("---")

c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Cuota Ordinaria", f"S/ {df_cronograma[df_cronograma['Tipo']=='ORDINARIA']['Cuota Total'].iloc[0]:,.2f}")
with c2: st.metric("Total Intereses", f"S/ {df_cronograma['Interés'].sum():,.2f}")
with c3: st.metric("Total Seguros", f"S/ {(df_cronograma['Seg. Desgravamen'].sum() + df_cronograma['Seg. Todo Riesgo'].sum()):,.2f}")
with c4: st.markdown(f'<div class="tcea-card"><small>TCEA (Costo Real)</small><br><b style="font-size:1.8rem;">{tcea_final:.2f}%</b></div>', unsafe_allow_html=True)

st.write("")

# TABLA RESALTADA
st.subheader("🗓️ Detalle del Calendario de Pagos")

def resaltar_dobles(s):
    return ['background-color: #0e2647; font-weight: bold' if s.Tipo == 'DOBLE' else '' for _ in s]

df_vis = df_cronograma.copy()
cols_format = ["Saldo Inicial", "Cuota Cap+Int", "Interés", "Seg. Desgravamen", "Seg. Todo Riesgo", "Cuota Total", "Saldo Final"]
for c in cols_format: df_vis[c] = df_vis[c].map("S/ {:,.2f}".format)

st.dataframe(df_vis.style.apply(resaltar_dobles, axis=1), height=450, use_container_width=True)

# --- 5. NOTAS TÉCNICAS (SOLICITADAS) ---
st.write("---")
col_n1, col_n2 = st.columns(2)

with col_n1:
    st.markdown("""
    <div class="nota-box">
    <h4>📌 Notas Importantes</h4>
    <ul>
        <li><b>Seguro de Desgravamen:</b> Se calcula sobre el <b>saldo del principal</b> pendiente. A medida que amortizas capital, este seguro disminuye.</li>
        <li><b>Seguro de Todo Riesgo:</b> Se calcula sobre el <b>monto asegurado</b> (valor del inmueble excluyendo el terreno). Es un monto fijo mensual.</li>
        <li><b>TCEA:</b> La Tasa Costo Efectiva Anual incluye la TEA, seguros y comisiones. Es el indicador real de cuánto te cuesta el préstamo.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

with col_n2:
    st.markdown("""
    <div class="nota-box">
    <h4>💡 Recomendación del Asesor</h4>
    <ul>
        <li><b>Cuotas Extras:</b> Al pagar cuotas dobles en Julio y Diciembre, reduces el capital más rápido, lo que genera un ahorro masivo de intereses a largo plazo.</li>
        <li><b>Pre-pagos:</b> Siempre que tengas un excedente, solicita <b>"Amortización de Capital con reducción de plazo"</b> para maximizar tu ahorro.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

# EXPORTACIÓN
csv = df_cronograma.to_csv(index=False).encode('utf-8')
st.download_button("📥 Descargar Cronograma para el Cliente", data=csv, file_name=f"Cronograma_Jancarlo_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
