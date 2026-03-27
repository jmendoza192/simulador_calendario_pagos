import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURACIÓN E INTERFAZ
st.set_page_config(page_title="Auditoría Inmobiliaria | Jancarlo", layout="wide")

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

# --- 2. MOTOR DE CÁLCULO ---
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
    int_ac = 0; cap_ac = 0
    
    for i in range(1, n_meses + 1):
        int_m = saldo * tem
        seg_d = saldo * t_des_m
        es_d = i in meses_d
        c_cap_int = cuota_base * (2 if es_d else 1)
        amort = c_cap_int - int_m
        c_total = c_cap_int + seg_d + seg_fijo
        saldo -= amort
        int_ac += int_m; cap_ac += amort
        
        data.append({
            "N°": i, "Mes": (fecha_d + pd.DateOffset(months=i)).strftime('%b-%Y'),
            "Tipo": "DOBLE" if es_d else "ORDINARIA",
            "Saldo Inicial": int(saldo + amort), "Cuota Cap+Int": int(c_cap_int),
            "Interés": int(int_m), "Seg. Desgravamen": int(seg_d), 
            "Seg. Todo Riesgo": int(seg_fijo), "Cuota Total": int(c_total),
            "Saldo Final": int(max(0, saldo)), "Interés Acumulado": int(int_ac), 
            "Capital Acumulado": int(cap_ac), "Seguros": int(seg_d + seg_fijo)
        })
        flujos.append(c_total)
    
    tcea = ((1 + npf.irr(flujos))**12 - 1) * 100
    return {"df": pd.DataFrame(data), "tcea": tcea}

# --- 3. INPUTS GLOBALES (SIDEBAR) ---
with st.sidebar:
    st.title("🏦 Panel de Auditoría")
    monto_p = st.number_input("Monto Préstamo (S/)", value=250000)
    valor_i = st.number_input("Valor Inmueble (S/)", value=300000)
    plazo_p = st.slider("Plazo (Años)", 5, 30, 20)
    c_dobles_p = st.checkbox("Cuotas Julio/Dic", value=True)
    fecha_p = st.date_input("Fecha Desembolso", datetime.now())

# IMPORTANTE: Definir las pestañas AQUÍ antes de usarlas
tab1, tab2 = st.tabs(["📊 Simulador Individual", "⚔️ Comparativa de Bancos"])

# --- 4. TAB 1: INDIVIDUAL ---
with tab1:
    col_a1, col_a2 = st.columns(2)
    with col_a1: tea_ind = st.number_input("TEA Banco (%)", value=9.50, key="tea_ind")
    with col_a2: des_ind = st.number_input("Seg. Desgravamen Mensual (%)", value=0.050, format="%.3f", key="des_ind")
    
    res = calcular_motor(monto_p, valor_i, tea_ind, des_ind, 0.025, plazo_p, c_dobles_p, fecha_p)
    df_ind = res["df"]
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Cuota Ordinaria", f"S/ {df_ind[df_ind['Tipo']=='ORDINARIA']['Cuota Total'].iloc[0]:,.0f}")
    m2.metric("Total Intereses", f"S/ {df_ind['Interés'].sum():,.0f}")
    m3.metric("Total Seguros", f"S/ {df_ind['Seguros'].sum():,.0f}")
    with m4: st.markdown(f'<div class="tcea-card"><small>TCEA FINAL</small><br><b style="font-size:1.5rem;">{res["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("📊 Interés vs Capital (Acumulado)")
        fig_area = go.Figure()
        fig_area.add_trace(go.Scatter(x=df_ind["N°"], y=df_ind["Interés Acumulado"], name="Interés", stackgroup='one', fillcolor='rgba(239, 68, 68, 0.5)', line=dict(color='#ef4444')))
        fig_area.add_trace(go.Scatter(x=df_ind["N°"], y=df_ind["Capital Acumulado"], name="Capital", stackgroup='one', fillcolor='rgba(16, 185, 129, 0.5)', line=dict(color='#10b981')))
        fig_area.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", hovermode='x unified')
        fig_area.update_yaxes(tickprefix="S/ ", tickformat=",.0f")
        st.plotly_chart(fig_area, use_container_width=True)
    with col_g2:
        st.subheader("📉 Saldo del Préstamo")
        fig_line = px.line(df_ind, x="N°", y="Saldo Final")
        fig_line.update_traces(line_color='#3b82f6', line_width=3, hovertemplate="Cuota: %{x}<br>Saldo: S/ %{y:,.0f}")
        fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        fig_line.update_yaxes(tickprefix="S/ ", tickformat=",.0f")
        st.plotly_chart(fig_line, use_container_width=True)

# --- 5. TAB 2: COMPARATIVA ---
with tab2:
    st.subheader("⚔️ Auditoría entre Entidades Financieras")
    c_b1, c_b2 = st.columns(2)
    with c_b1:
        st.info("🏦 BANCO A")
        t1 = st.number_input("TEA A (%)", value=9.5, key="t1")
        d1 = st.number_input("Desgravamen A (%)", value=0.050, format="%.3f", key="d1")
        res1 = calcular_motor(monto_p, valor_i, t1, d1, 0.025, plazo_p, c_dobles_p, fecha_p)
    with c_b2:
        st.success("🏦 BANCO B")
        t2 = st.number_input("TEA B (%)", value=9.2, key="t2")
        d2 = st.number_input("Desgravamen B (%)", value=0.080, format="%.3f", key="d2")
        res2 = calcular_motor(monto_p, valor_i, t2, d2, 0.025, plazo_p, c_dobles_p, fecha_p)

    pago_total_a = res1['df']["Cuota Total"].sum()
    pago_total_b = res2['df']["Cuota Total"].sum()
    ahorro = pago_total_a - pago_total_b
    
    st.write("---")
    cm1, cm2, cm3 = st.columns(3)
    cm1.markdown(f'<div class="tcea-card">TCEA BANCO A<br><b style="font-size:1.8rem;">{res1["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)
    cm2.markdown(f'<div class="tcea-card">TCEA BANCO B<br><b style="font-size:1.8rem;">{res2["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)
    with cm3:
        color_ah = "#10b981" if ahorro > 0 else "#ef4444"
        st.markdown(f'<div class="ahorro-card" style="background:{color_ah}">{"AHORRO" if ahorro > 0 else "SOBRECOSTO"}<br><b style="font-size:1.8rem;">S/ {abs(ahorro):,.0f}</b></div>', unsafe_allow_html=True)

    st.write("---")
    st.subheader("📝 Notas de Auditoría")
    n_col1, n_col2 = st.columns(2)
    with n_col1:
        st.markdown(f"""
        <div class="nota-box">
        <h4>🔍 Cálculo del Sobrecosto</h4>
        <ul>
            <li><b>Diferencia de Flujos:</b> Se calcula restando el pago total proyectado de ambos bancos. El monto de <b>S/ {abs(ahorro):,.0f}</b> es el impacto real en tu patrimonio.</li>
            <li><b>Efecto TCEA:</b> Nota que el banco con menor TEA no siempre es el más barato si sus seguros son elevados.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    with n_col2:
        st.markdown("""
        <div class="nota-box">
        <h4>🚩 Consideraciones</h4>
        <ul>
            <li><b>Seguros:</b> El desgravamen se calcula sobre saldo. Si es muy alto, anula el beneficio de una tasa baja.</li>
            <li><b>Recomendación:</b> Evalúa el endoso de un seguro de vida externo para reducir costos bancarios.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
