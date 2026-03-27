import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURACIÓN E INTERFAZ
st.set_page_config(page_title="Auditoría Bancaria | Jancarlo Inmobiliario", layout="wide")

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

# --- 2. MOTOR DE CÁLCULO REUTILIZABLE ---
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

tab1, tab2 = st.tabs(["📊 Simulador Individual", "⚔️ Comparativa de Bancos"])

# --- TAB 1: SIMULADOR INDIVIDUAL (CON GRÁFICOS) ---
with tab1:
    col_a1, col_a2 = st.columns(2)
    with col_a1: tea_a = st.number_input("TEA Banco (%)", value=9.50, key="tea_ind")
    with col_a2: des_a = st.number_input("Seg. Desgravamen Mensual (%)", value=0.050, format="%.3f", key="des_ind")
    riesgo_a = st.number_input("Seg. Todo Riesgo Mensual (%)", value=0.025, format="%.3f", key="ries_ind")
    
    res = calcular_motor(monto_p, valor_i, tea_a, des_a, riesgo_a, plazo_p, c_dobles_p, fecha_p)
    df_ind = res["df"]
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Cuota Ordinaria", f"S/ {df_ind[df_ind['Tipo']=='ORDINARIA']['Cuota Total'].iloc[0]:,.0f}")
    m2.metric("Total Intereses", f"S/ {df_ind['Interés'].sum():,.0f}")
    m3.metric("Total Seguros", f"S/ {df_ind['Seguros'].sum():,.0f}")
    with m4: st.markdown(f'<div class="tcea-card"><small>TCEA FINAL</small><br><b style="font-size:1.5rem;">{res["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)

    # REINTEGRACIÓN DE GRÁFICOS
    st.write("")
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

    # TABLA DETALLADA
    st.subheader("🗓️ Detalle del Calendario")
    df_vis = df_ind.drop(columns=["Interés Acumulado", "Capital Acumulado", "Seguros"])
    cols_f = ["Saldo Inicial", "Cuota Cap+Int", "Interés", "Seg. Desgravamen", "Seg. Todo Riesgo", "Cuota Total", "Saldo Final"]
    for c in cols_f: df_vis[c] = df_vis[c].map("S/ {:,.0f}".format)
    st.dataframe(df_vis.style.apply(lambda s: ['background-color: #0e2647' if s.Tipo == 'DOBLE' else '' for _ in s], axis=1), height=400, use_container_width=True)

# --- TAB 2: COMPARATIVA BANCARIA ---
with tab2:
    st.subheader("⚔️ Auditoría entre Entidades Financieras")
    c_b1, c_b2 = st.columns(2)
    with c_b1:
        st.info("🏦 BANCO A")
        t1 = st.number_input("TEA A (%)", value=9.5, key="t1")
        d1 = st.number_input("Desgravamen A (%)", value=0.050, format="%.3f", key="d1")
        r1 = st.number_input("Todo Riesgo A (%)", value=0.025, format="%.3f", key="r1")
        res1 = calcular_motor(monto_p, valor_i, t1, d1, r1, plazo_p, c_dobles_p, fecha_p)
    with c_b2:
        st.success("🏦 BANCO B")
        t2 = st.number_input("TEA B (%)", value=9.2, key="t2")
        d2 = st.number_input("Desgravamen B (%)", value=0.080, format="%.3f", key="d2")
        r2 = st.number_input("Todo Riesgo B (%)", value=0.025, format="%.3f", key="r2")
        res2 = calcular_motor(monto_p, valor_i, t2, d2, r2, plazo_p, c_dobles_p, fecha_p)

    # MÉTRICAS COMPARATIVAS
    ahorro = res1['df']["Cuota Total"].sum() - res2['df']["Cuota Total"].sum()
    st.write("---")
    cm1, cm2, cm3 = st.columns(3)
    cm1.markdown(f'<div class="tcea-card">TCEA BANCO A<br><b style="font-size:1.8rem;">{res1["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)
    cm2.markdown(f'<div class="tcea-card">TCEA BANCO B<br><b style="font-size:1.8rem;">{res2["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)
    with cm3:
        color_ah = "#10b981" if ahorro > 0 else "#ef4444"
        st.markdown(f'<div class="ahorro-card" style="background:{color_ah}">{"AHORRO TOTAL" if ahorro > 0 else "SOBRECOSTO"}<br><b style="font-size:1.8rem;">S/ {abs(ahorro):,.0f}</b></div>', unsafe_allow_html=True)

    # GRÁFICO COMPARATIVO
    comp_df = pd.DataFrame({
        "Concepto": ["Cuota Ord.", "Total Interés", "Total Seguros"],
        "Banco A": [res1['df'][res1['df']["Tipo"]=="ORDINARIA"]["Cuota Total"].iloc[0], res1['df']["Interés"].sum(), res1['df']["Seguros"].sum()],
        "Banco B": [res2['df'][res2['df']["Tipo"]=="ORDINARIA"]["Cuota Total"].iloc[0], res2['df']["Interés"].sum(), res2['df']["Seguros"].sum()]
    })
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(name='Banco A', x=comp_df["Concepto"], y=comp_df["Banco A"], marker_color='#1e3a8a'))
    fig_comp.add_trace(go.Bar(name='Banco B', x=comp_df["Concepto"], y=comp_df["Banco B"], marker_color='#10b981'))
    fig_comp.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
    fig_comp.update_yaxes(tickprefix="S/ ", tickformat=",.0f")
    st.plotly_chart(fig_comp, use_container_width=True)
