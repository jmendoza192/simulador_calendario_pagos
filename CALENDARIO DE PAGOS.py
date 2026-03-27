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

# --- 2. MOTOR DE CÁLCULO ACTUALIZADO ---
def calcular_motor(monto, valor_inm, tea, t_des, t_riesgo, plazo, c_dobles, fecha_d):
    tem = (1 + tea/100)**(1/12) - 1
    n_meses = plazo * 12
    # El Seguro Todo Riesgo suele ser una tasa anual dividida entre 12 aplicada al valor de edificación/inmueble
    seg_todo_riesgo_mensual = valor_inm * (t_riesgo/100) / 12
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
        seg_desg = saldo * t_des_m
        es_d = i in meses_d
        c_cap_int = cuota_base * (2 if es_d else 1)
        amort = c_cap_int - int_m
        c_total = c_cap_int + seg_desg + seg_todo_riesgo_mensual
        saldo -= amort
        int_ac += int_m; cap_ac += amort
        
        data.append({
            "N°": i, "Mes": (fecha_d + pd.DateOffset(months=i)).strftime('%b-%Y'),
            "Tipo": "DOBLE" if es_d else "ORDINARIA",
            "Saldo Inicial": int(saldo + amort), 
            "Cuota Cap+Int": int(c_cap_int),
            "Interés": int(int_m), 
            "Seg. Desgravamen": int(seg_desg), 
            "Seg. Todo Riesgo": int(seg_todo_riesgo_mensual), 
            "Cuota Total": int(c_total),
            "Saldo Final": int(max(0, saldo)), 
            "Interés Acumulado": int(int_ac), 
            "Capital Acumulado": int(cap_ac), 
            "Total Seguros": int(seg_desg + seg_todo_riesgo_mensual)
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

# --- 4. DEFINICIÓN DE PESTAÑAS ---
tab1, tab2 = st.tabs(["📊 Simulador Individual", "⚔️ Comparativa de Bancos"])

# --- TAB 1: INDIVIDUAL ---
with tab1:
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1: tea_ind = st.number_input("TEA Banco (%)", value=9.50, key="tea_ind")
    with col_a2: des_ind = st.number_input("Desgravamen (%)", value=0.050, format="%.3f", key="des_ind")
    with col_a3: ries_ind = st.number_input("Todo Riesgo Anual (%)", value=0.30, format="%.2f", key="ries_ind")
    
    res = calcular_motor(monto_p, valor_i, tea_ind, des_ind, ries_ind, plazo_p, c_dobles_p, fecha_p)
    df_ind = res["df"]
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Cuota Ordinaria", f"S/ {df_ind[df_ind['Tipo']=='ORDINARIA']['Cuota Total'].iloc[0]:,.0f}")
    m2.metric("Total Intereses", f"S/ {df_ind['Interés'].sum():,.0f}")
    m3.metric("Total Seguros", f"S/ {df_ind['Total Seguros'].sum():,.0f}")
    with m4: st.markdown(f'<div class="tcea-card"><small>TCEA FINAL</small><br><b style="font-size:1.5rem;">{res["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)

    st.subheader("📋 Calendario de Pagos Detallado")
    st.dataframe(df_ind[["N°", "Mes", "Tipo", "Saldo Inicial", "Cuota Cap+Int", "Interés", "Seg. Desgravamen", "Seg. Todo Riesgo", "Cuota Total", "Saldo Final"]], use_container_width=True)

# --- TAB 2: COMPARATIVA ---
with tab2:
    st.subheader("⚔️ Auditoría entre Entidades Financieras")
    c_b1, c_b2 = st.columns(2)
    with c_b1:
        st.info("🏦 OPCIÓN A")
        n_a = st.text_input("Banco A", value="BANCO A")
        t1 = st.number_input("TEA A (%)", value=9.5, key="t1")
        d1 = st.number_input("Desgravamen A (%)", value=0.050, format="%.3f", key="d1")
        r1 = st.number_input("Todo Riesgo A (%)", value=0.30, key="r1")
        res1 = calcular_motor(monto_p, valor_i, t1, d1, r1, plazo_p, c_dobles_p, fecha_p)
    with c_b2:
        st.success("🏦 OPCIÓN B")
        n_b = st.text_input("Banco B", value="BANCO B")
        t2 = st.number_input("TEA B (%)", value=9.2, key="t2")
        d2 = st.number_input("Desgravamen B (%)", value=0.080, format="%.3f", key="d2")
        r2 = st.number_input("Todo Riesgo B (%)", value=0.28, key="r2")
        res2 = calcular_motor(monto_p, valor_i, t2, d2, r2, plazo_p, c_dobles_p, fecha_p)

    # Lógica de Recomendación
    total_a = res1['df']["Cuota Total"].sum()
    total_b = res2['df']["Cuota Total"].sum()
    mejor = n_a if res1['tcea'] < res2['tcea'] else n_b
    color_rec = "#1e3a8a" if mejor == n_a else "#10b981"
    
    st.write("---")
    st.markdown(f"""
        <div style="background-color: {color_rec}; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 25px; border: 2px solid #ffffff33;">
            <h2 style="color: white; margin: 0;">✅ RECOMENDACIÓN: {mejor}</h2>
            <p style="color: #e0e0e0; font-size: 1.1rem; margin-top: 10px;">
                El <b>{mejor}</b> es la opción ganadora tras auditar Intereses, Desgravamen y Seguro de Inmueble.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # --- RESUMEN NUMÉRICO EXTENDIDO ---
    st.subheader("📋 Resumen Numérico de Auditoría")
    
    def get_row(res_b):
        df = res_b["df"]
        return [
            int(df[df["Tipo"]=="ORDINARIA"]["Cuota Total"].iloc[0]),
            int(df["Interés"].sum()),
            int(df["Seg. Desgravamen"].sum()),
            int(df["Seg. Todo Riesgo"].sum()),
            int(df["Total Seguros"].sum()),
            int(df["Interés"].sum() + df["Total Seguros"].sum()),
            int(df["Cuota Total"].sum())
        ]

    datos_tab = {
        "Concepto": ["Cuota Ord.", "Total Intereses", "Total Desgravamen", "Total Todo Riesgo", "TOTAL SEGUROS", "GASTOS FINANCIEROS", "PAGO TOTAL"],
        n_a: get_row(res1),
        n_b: get_row(res2)
    }
    
    df_res = pd.DataFrame(datos_tab)
    # Cálculo de sobrecosto
    sobrecosto_a = int(max(0, total_a - total_b))
    sobrecosto_b = int(max(0, total_b - total_a))
    
    new_row = {"Concepto": "SOBRECOSTO BANCARIO", n_a: sobrecosto_a, n_b: sobrecosto_b}
    df_res = pd.concat([df_res, pd.DataFrame([new_row])], ignore_index=True)

    st.table(df_res.set_index("Concepto").applymap(lambda x: f"S/ {x:,.0f}"))

    # --- GRÁFICO COMPARATIVO ---
    st.write("")
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(name=n_a, x=df_res["Concepto"][:4], y=df_res[n_a][:4], marker_color='#1e3a8a'))
    fig_comp.add_trace(go.Bar(name=n_b, x=df_res["Concepto"][:4], y=df_res[n_b][:4], marker_color='#10b981'))
    fig_comp.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
    st.plotly_chart(fig_comp, use_container_width=True)

    # --- NOTAS TÉCNICAS ---
    st.write("---")
    st.subheader("📝 Notas de Auditoría")
    n1, n2 = st.columns(2)
    with n1:
        st.markdown(f"""
        <div class="nota-box">
        <h4>💰 Cálculo del Sobrecosto</h4>
        <p>Se obtiene comparando el <b>Pago Total</b> proyectado. El sobrecosto es dinero que el cliente "pierde" al no elegir la opción con TCEA más baja.</p>
        <ul>
            <li><b>Seguro Todo Riesgo:</b> Es un costo fijo basado en el valor del inmueble. No reduce con el saldo.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    with n2:
        st.markdown("""
        <div class="nota-box">
        <h4>⚠️ Puntos Clave</h4>
        <ul>
            <li><b>Gastos Financieros:</b> Suma de Intereses + Seguros (Desgravamen + Todo Riesgo).</li>
            <li><b>Endoso:</b> Puedes endosar tu seguro de vida (elimina Desgravamen) y tu seguro domiciliario (elimina Todo Riesgo) para bajar la cuota.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
