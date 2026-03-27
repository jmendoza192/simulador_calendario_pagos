import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import plotly.express as px
import plotly.graph_objects as go
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
    
    divisor = sum((2 if i in meses_dobles else 1) / (1 + tem + tasa_desgravamen)**i for i in range(1, n_meses + 1))
    cuota_base = monto_prestamo / divisor
    
    saldo = monto_prestamo
    data = []
    flujos = [-monto_prestamo]
    int_ac = 0; cap_ac = 0
    
    for i in range(1, n_meses + 1):
        f_act = fecha_desembolso + pd.DateOffset(months=i)
        int_m = saldo * tem
        seg_d = saldo * tasa_desgravamen
        es_d = i in meses_dobles
        c_cap_int = cuota_base * (2 if es_d else 1)
        amort = c_cap_int - int_m
        c_total = c_cap_int + seg_d + seg_inmueble_fijo
        
        saldo -= amort
        int_ac += int_m; cap_ac += amort
        
        data.append({
            "N°": i, "Mes": f_act.strftime('%b-%Y'), "Tipo": "DOBLE" if es_d else "ORDINARIA",
            "Saldo Inicial": int(saldo + amort), "Cuota Cap+Int": int(c_cap_int), "Interés": int(int_m),
            "Seg. Desgravamen": int(seg_d), "Seg. Todo Riesgo": int(seg_inmueble_fijo),
            "Cuota Total": int(c_total), "Saldo Final": int(max(0, saldo)),
            "Interés Acumulado": int(int_ac), "Capital Acumulado": int(cap_ac)
        })
        flujos.append(c_total)

    tcea = ((1 + npf.irr(flujos))**12 - 1) * 100
    return pd.DataFrame(data), tcea

df_cronograma, tcea_final = generar_cronograma()

# --- 4. DASHBOARD ---
st.title("📅 Simulador de Cronograma Inmobiliario")
st.write("---")

c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Cuota Ordinaria", f"S/ {df_cronograma[df_cronograma['Tipo']=='ORDINARIA']['Cuota Total'].iloc[0]:,.0f}")
with c2: st.metric("Total Intereses", f"S/ {df_cronograma['Interés'].sum():,.0f}")
with c3: st.metric("Total Seguros", f"S/ {(df_cronograma['Seg. Desgravamen'].sum() + df_cronograma['Seg. Todo Riesgo'].sum()):,.0f}")
with c4: st.markdown(f'<div class="tcea-card"><small>TCEA (Costo Real)</small><br><b style="font-size:1.8rem;">{tcea_final:.2f}%</b></div>', unsafe_allow_html=True)

st.write("")

# --- 5. GRÁFICAS CON FORMATO S/ ---
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("📊 Interés vs Capital (Acumulado)")
    fig_area = go.Figure()
    fig_area.add_trace(go.Scatter(x=df_cronograma["N°"], y=df_cronograma["Interés Acumulado"], name="Interés Pagado", stackgroup='one', fillcolor='rgba(239, 68, 68, 0.5)', line=dict(color='#ef4444')))
    fig_area.add_trace(go.Scatter(x=df_cronograma["N°"], y=df_cronograma["Capital Acumulado"], name="Capital Pagado", stackgroup='one', fillcolor='rgba(16, 185, 129, 0.5)', line=dict(color='#10b981')))
    fig_area.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", hovermode='x unified')
    fig_area.update_yaxes(tickprefix="S/ ", tickformat=",.0f")
    st.plotly_chart(fig_area, use_container_width=True)

with col_g2:
    st.subheader("📉 Saldo del Préstamo")
    fig_line = px.line(df_cronograma, x="N°", y="Saldo Final")
    fig_line.update_traces(line_color='#3b82f6', line_width=3, hovertemplate="Cuota: %{x}<br>Saldo: S/ %{y:,.0f}")
    fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
    fig_line.update_yaxes(tickprefix="S/ ", tickformat=",.0f")
    st.plotly_chart(fig_line, use_container_width=True)

# --- 6. TABLA RESALTADA SIN DECIMALES ---
st.subheader("🗓️ Detalle del Calendario de Pagos")

def resaltar_dobles(s):
    return ['background-color: #0e2647; font-weight: bold; color: #ffffff' if s.Tipo == 'DOBLE' else '' for _ in s]

df_vis = df_cronograma.copy()
cols_cliente = ["N°", "Mes", "Tipo", "Saldo Inicial", "Cuota Cap+Int", "Interés", "Seg. Desgravamen", "Seg. Todo Riesgo", "Cuota Total", "Saldo Final"]
df_vis = df_vis[cols_cliente]

cols_format = ["Saldo Inicial", "Cuota Cap+Int", "Interés", "Seg. Desgravamen", "Seg. Todo Riesgo", "Cuota Total", "Saldo Final"]
for c in cols_format: df_vis[c] = df_vis[c].map("S/ {:,.0f}".format)

st.dataframe(df_vis.style.apply(resaltar_dobles, axis=1), height=450, use_container_width=True)

# --- 7. NOTAS TÉCNICAS ---
st.write("---")
col_n1, col_n2 = st.columns(2)

with col_n1:
    st.markdown("""
    <div class="nota-box">
    <h4>📌 Notas Técnicas</h4>
    <ul>
        <li><b>Seguro de Desgravamen:</b> Calculado sobre el <b>saldo del principal</b>. Baja cada mes conforme pagas tu deuda.</li>
        <li><b>Seguro de Todo Riesgo:</b> Calculado sobre el <b>monto asegurado</b> (valor del inmueble). Es un monto fijo.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

with col_n2:
    st.markdown("""
    <div class="nota-box">
    <h4>💡 Estrategia de Ahorro</h4>
    <ul>
        <li><b>Cuotas Dobles:</b> Al pagar el doble en Julio y Diciembre, ahorras una cantidad masiva de intereses al reducir el capital más rápido.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

# EXPORTACIÓN
csv = df_cronograma[cols_cliente].to_csv(index=False).encode('utf-8')
st.download_button("📥 Descargar Reporte (Excel/CSV)", data=csv, file_name=f"Cronograma_Inmobiliario_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
