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

# --- 4. DEFINICIÓN DE PESTAÑAS (CRÍTICO: Declarar antes de usar) ---
tab1, tab2 = st.tabs(["📊 Simulador Individual", "⚔️ Comparativa de Bancos"])

# --- CONTENIDO TAB 1: INDIVIDUAL ---
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
        fig_line.update_traces(line_color='#3b82f6', line_width=3, hovertemplate="Mes: %{x}<br>Saldo: S/ %{y:,.0f}")
        fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        fig_line.update_yaxes(tickprefix="S/ ", tickformat=",.0f")
        st.plotly_chart(fig_line, use_container_width=True)

# --- CONTENIDO TAB 2: COMPARATIVA ---
with tab2:
    st.subheader("⚔️ Auditoría entre Entidades Financieras")
    c_b1, c_b2 = st.columns(2)
    with c_b1:
        st.info("🏦 BANCO A")
        nombre_a = st.text_input("Nombre Banco A", value="BANCO A")
        t1 = st.number_input("TEA A (%)", value=9.5, key="t1")
        d1 = st.number_input("Desgravamen A (%)", value=0.050, format="%.3f", key="d1")
        res1 = calcular_motor(monto_p, valor_i, t1, d1, 0.025, plazo_p, c_dobles_p, fecha_p)
    with c_b2:
        st.success("🏦 BANCO B")
        nombre_b = st.text_input("Nombre Banco B", value="BANCO B")
        t2 = st.number_input("TEA B (%)", value=9.2, key="t2")
        d2 = st.number_input("Desgravamen B (%)", value=0.080, format="%.3f", key="d2")
        res2 = calcular_motor(monto_p, valor_i, t2, d2, 0.025, plazo_p, c_dobles_p, fecha_p)

    # Lógica de Recomendación y Sobrecostos
    total_a = res1['df']["Cuota Total"].sum()
    total_b = res2['df']["Cuota Total"].sum()
    mejor_banco = nombre_a if res1['tcea'] < res2['tcea'] else nombre_b
    color_rec = "#1e3a8a" if mejor_banco == nombre_a else "#10b981"
    
    st.write("---")
    st.markdown(f"""
        <div style="background-color: {color_rec}; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 25px; border: 2px solid #ffffff33;">
            <h2 style="color: white; margin: 0;">✅ RECOMENDACIÓN: {mejor_banco}</h2>
            <p style="color: #e0e0e0; font-size: 1.1rem; margin-top: 10px;">
                Tras analizar la TCEA, el <b>{mejor_banco}</b> minimiza tus gastos financieros totales.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Métricas de Resumen
    cm1, cm2, cm3 = st.columns(3)
    cm1.markdown(f'<div class="tcea-card">TCEA {nombre_a}<br><b style="font-size:1.8rem;">{res1["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)
    cm2.markdown(f'<div class="tcea-card">TCEA {nombre_b}<br><b style="font-size:1.8rem;">{res2["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)
    with cm3:
        ahorro_val = total_a - total_b
        color_ah = "#10b981" if ahorro_val > 0 else "#ef4444"
        st.markdown(f'<div class="ahorro-card" style="background:{color_ah}">{"AHORRO" if ahorro_val > 0 else "SOBRECOSTO"}<br><b style="font-size:1.8rem;">S/ {abs(ahorro_val):,.0f}</b></div>', unsafe_allow_html=True)

    # --- RESUMEN NUMÉRICO EXTENDIDO ---
    st.subheader("📋 Resumen Numérico Detallado")
    int_a, seg_a = int(res1['df']["Interés"].sum()), int(res1['df']["Seguros"].sum())
    int_b, seg_b = int(res2['df']["Interés"].sum()), int(res2['df']["Seguros"].sum())
    
    datos_tab = {
        "Concepto": [
            "Cuota Ordinaria", 
            "Total Intereses", 
            "Total Seguros", 
            "GASTOS FINANCIEROS (Int+Seg)", 
            "PAGO TOTAL PROYECTADO",
            "SOBRECOSTO BANCARIO"
        ],
        nombre_a: [
            int(res1['df'][res1['df']["Tipo"]=="ORDINARIA"]["Cuota Total"].iloc[0]),
            int_a, seg_a, int_a + seg_a, int(total_a), int(max(0, total_a - total_b))
        ],
        nombre_b: [
            int(res2['df'][res2['df']["Tipo"]=="ORDINARIA"]["Cuota Total"].iloc[0]),
            int_b, seg_b, int_b + seg_b, int(total_b), int(max(0, total_b - total_a))
        ]
    }
    df_res = pd.DataFrame(datos_tab)
    st.table(df_res.set_index("Concepto").applymap(lambda x: f"S/ {x:,.0f}"))

    # --- GRÁFICO COMPARATIVO ---
    st.write("")
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(name=nombre_a, x=df_res["Concepto"][:4], y=df_res[nombre_a][:4], marker_color='#1e3a8a'))
    fig_comp.add_trace(go.Bar(name=nombre_b, x=df_res["Concepto"][:4], y=df_res[nombre_b][:4], marker_color='#10b981'))
    fig_comp.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
    st.plotly_chart(fig_comp, use_container_width=True)

    # --- NOTAS TÉCNICAS Y ENDOSOS ---
    st.write("---")
    st.subheader("📝 Notas de Auditoría de Costos")
    n1, n2 = st.columns(2)
    with n1:
        st.markdown(f"""
        <div class="nota-box">
        <h4>💰 ¿Cómo se calcula el Sobrecosto?</h4>
        <p>El sobrecosto no es solo una diferencia de tasas nominales. Es el impacto patrimonial calculado mediante la <b>Suma Total de Flujos (∑)</b>:</p>
        <ul>
            <li>Comparamos el pago total final de cada banco.</li>
            <li>Si eliges la opción NO recomendada, estarías pagando un excedente innecesario al banco.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    with n2:
        st.markdown("""
        <div class="nota-box">
        <h4>⚠️ Puntos Clave</h4>
        <ul>
            <li><b>Gastos Financieros:</b> Es el "alquiler" real que pagas por el dinero. Incluye intereses y seguros.</li>
            <li><b>Efecto Seguros:</b> Un banco con TEA baja pero seguros agresivos puede ser más caro que uno con TEA alta.</li>
            <li><b>Endoso de Seguros:</b> Tienes el derecho de <b>endosar una póliza de vida externa</b> para eliminar el cobro mensual del Seguro de Desgravamen bancario, reduciendo significativamente tu pago total.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
