import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURACIÓN E INTERFAZ
st.set_page_config(page_title="Comparador Bancario | Jancarlo Inmobiliario", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetric"] {
        background-color: #1f2630; padding: 15px; border-radius: 10px; border: 1px solid #30363d;
    }
    .tcea-card {
        background: linear-gradient(135deg, #1e3a8a, #1e40af);
        padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #3b82f6;
    }
    .ahorro-card {
        background: linear-gradient(135deg, #064e3b, #065f46);
        padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #10b981;
    }
    .nota-box {
        background-color: #161b22; padding: 15px; border-left: 5px solid #d1a435; border-radius: 5px; margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LÓGICA DE CÁLCULO CORE ---
def calcular_motor(monto, valor_inm, tea, t_des, t_riesgo, plazo, c_dobles, fecha_d):
    tem = (1 + tea/100)**(1/12) - 1
    n_meses = plazo * 12
    seg_fijo = valor_inm * (t_riesgo/100)
    t_des_m = t_des/100
    
    meses_d = []
    if c_dobles:
        for i in range(1, n_meses + 1):
            if (fecha_d + pd.DateOffset(months=i)).month in [7, 12]: meses_d.append(i)
    
    divisor = sum((2 if i in meses_d else 1) / (1 + tem + t_des_m)**i for i in range(1, n_meses + 1))
    cuota_base = monto / divisor
    
    saldo = monto; data = []; flujos = [-monto]
    
    for i in range(1, n_meses + 1):
        int_m = saldo * tem
        seg_d = saldo * t_des_m
        es_d = i in meses_d
        c_cap_int = cuota_base * (2 if es_d else 1)
        amort = c_cap_int - int_m
        c_total = c_cap_int + seg_d + seg_fijo
        saldo -= amort
        data.append({"N°": i, "Tipo": "DOBLE" if es_d else "ORDINARIA", "Interés": int_m, "Cuota Total": c_total, "Seguros": seg_d + seg_fijo})
        flujos.append(c_total)
    
    tcea = ((1 + npf.irr(flujos))**12 - 1) * 100
    df = pd.DataFrame(data)
    return {"df": df, "tcea": tcea, "total_pago": df["Cuota Total"].sum(), "interes_total": df["Interés"].sum(), "cuota_ord": df[df["Tipo"]=="ORDINARIA"]["Cuota Total"].iloc[0]}

# --- 3. UI - SIDEBAR COMPARTIDA ---
with st.sidebar:
    st.title("🏦 Panel de Auditoría")
    monto_p = st.number_input("Monto Préstamo (S/)", value=250000)
    valor_i = st.number_input("Valor Inmueble (S/)", value=300000)
    plazo_p = st.slider("Plazo (Años)", 5, 30, 20)
    c_dobles_p = st.checkbox("Cuotas Julio/Dic", value=True)
    fecha_p = st.date_input("Fecha Desembolso", datetime.now())

tab1, tab2 = st.tabs(["📊 Simulador Individual", "⚔️ Comparativa de Bancos"])

# --- TAB 1: INDIVIDUAL (EL QUE YA TENÍAS) ---
with tab1:
    col_a1, col_a2 = st.columns(2)
    with col_a1: tea_a = st.number_input("TEA Banco (%)", value=9.50, key="tea_a")
    with col_a2: des_a = st.number_input("Seg. Desgravamen Mensual (%)", value=0.050, format="%.3f", key="des_a")
    riesgo_a = st.number_input("Seg. Todo Riesgo Mensual (%)", value=0.025, format="%.3f", key="ries_a")
    
    res = calcular_motor(monto_p, valor_i, tea_a, des_a, riesgo_a, plazo_p, c_dobles_p, fecha_p)
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Cuota Ordinaria", f"S/ {res['cuota_ord']:,.0f}")
    m2.metric("Total Intereses", f"S/ {res['interes_total']:,.0f}")
    m3.metric("Total a Pagar", f"S/ {res['total_pago']:,.0f}")
    with m4: st.markdown(f'<div class="tcea-card"><small>TCEA FINAL</small><br><b style="font-size:1.5rem;">{res["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)

# --- TAB 2: COMPARATIVA (NUEVA FUNCIÓN) ---
with tab2:
    st.subheader("⚔️ Auditoría entre Entidades Financieras")
    
    c_b1, c_b2 = st.columns(2)
    with c_b1:
        st.info("🏦 BANCO A (Referencia)")
        t1 = st.number_input("TEA A (%)", value=9.5, key="t1")
        d1 = st.number_input("Desgravamen A (%)", value=0.050, format="%.3f", key="d1")
        r1 = st.number_input("Todo Riesgo A (%)", value=0.025, format="%.3f", key="r1")
        res1 = calcular_motor(monto_p, valor_i, t1, d1, r1, plazo_p, c_dobles_p, fecha_p)
        
    with c_b2:
        st.success("🏦 BANCO B (Propuesta)")
        t2 = st.number_input("TEA B (%)", value=9.2, key="t2")
        d2 = st.number_input("Desgravamen B (%)", value=0.080, format="%.3f", key="d2")
        r2 = st.number_input("Todo Riesgo B (%)", value=0.025, format="%.3f", key="r2")
        res2 = calcular_motor(monto_p, valor_i, t2, d2, r2, plazo_p, c_dobles_p, fecha_p)

    st.write("---")
    # MÉTRICAS DE COMPARACIÓN
    ahorro_total = res1['total_pago'] - res2['total_pago']
    col_comp1, col_comp2, col_comp3 = st.columns(3)
    
    with col_comp1:
        st.markdown(f'<div class="tcea-card">TCEA BANCO A<br><b style="font-size:1.8rem;">{res1["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)
    with col_comp2:
        st.markdown(f'<div class="tcea-card">TCEA BANCO B<br><b style="font-size:1.8rem;">{res2["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)
    with col_comp3:
        color_ahorro = "#10b981" if ahorro_total > 0 else "#ef4444"
        texto_ahorro = "AHORRO TOTAL" if ahorro_total > 0 else "SOBRECOSTO"
        st.markdown(f'<div class="ahorro-card" style="background:{color_ahorro}">{texto_ahorro}<br><b style="font-size:1.8rem;">S/ {abs(ahorro_total):,.0f}</b></div>', unsafe_allow_html=True)

    # GRÁFICO COMPARATIVO
    st.write("")
    st.subheader("📊 Comparación de Cuotas y Costos")
    
    comp_data = pd.DataFrame({
        "Concepto": ["Cuota Ordinaria", "Total Intereses", "Total Seguros"],
        "Banco A": [res1['cuota_ord'], res1['interes_total'], res1['df']['Seguros'].sum()],
        "Banco B": [res2['cuota_ord'], res2['interes_total'], res2['df']['Seguros'].sum()]
    })
    
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(name='Banco A', x=comp_data["Concepto"], y=comp_data["Banco A"], marker_color='#1e3a8a'))
    fig_comp.add_trace(go.Bar(name='Banco B', x=comp_data["Concepto"], y=comp_data["Banco B"], marker_color='#10b981'))
    fig_comp.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
    fig_comp.update_yaxes(tickprefix="S/ ", tickformat=",.0f")
    st.plotly_chart(fig_comp, use_container_width=True)

    st.markdown(f"""
    <div class="nota-box">
    <b>💡 Conclusión de Auditoría:</b><br>
    Aunque el Banco B tiene una TEA de {t2}%, su TCEA real es de {res2['tcea']:.2f}%. 
    {"Esto lo hace la opción más eficiente." if res2['tcea'] < res1['tcea'] else "A pesar de la tasa nominal, los seguros encarecen el crédito por encima de la opción A."}
    </div>
    """, unsafe_allow_html=True)
