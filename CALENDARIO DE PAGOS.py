import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from fpdf import FPDF
import base64

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
        padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #3b82f6; color: white;
    }
    .ahorro-card {
        background: linear-gradient(135deg, #064e3b, #065f46);
        padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #10b981; color: white;
    }
    .sobrecosto-card {
        background: linear-gradient(135deg, #7f1d1d, #b91c1c);
        padding: 20px; border-radius: 12px; text-align: center; border: 1px solid #ef4444; color: white;
    }
    .nota-box {
        background-color: #161b22; padding: 15px; border-left: 5px solid #d1a435; border-radius: 5px; margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCIONES DE EXPORTACIÓN (ESTILO TECHO DE INVERSIÓN) ---
def create_pdf(titulo, datos_dict, notas):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=titulo, ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Resumen de Auditoria:", ln=True)
    pdf.set_font("Arial", '', 10)
    
    for k, v in datos_dict.items():
        pdf.cell(100, 8, txt=f"{k}:", border=1)
        pdf.cell(90, 8, txt=f"{v}", border=1, ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Notas del Asesor:", ln=True)
    pdf.set_font("Arial", '', 10)
    for nota in notas:
        pdf.multi_cell(0, 8, txt=f"- {nota}")
    
    return pdf.output(dest="S").encode("latin-1")

def get_binary_link(bin_file, file_label="Archivo"):
    b64 = base64.b64encode(bin_file).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{file_label}.pdf" style="text-decoration:none;"><button style="width:100%; padding:10px; background-color:#3b82f6; color:white; border:none; border-radius:5px; cursor:pointer;">{file_label}</button></a>'

# --- 3. MOTOR DE CÁLCULO ---
def calcular_motor(monto, valor_inm, tea, t_des, t_riesgo, plazo, c_dobles, fecha_d):
    tem = (1 + tea/100)**(1/12) - 1
    n_meses = plazo * 12
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
            "Saldo Inicial": int(saldo + amort), "Cuota Cap+Int": int(c_cap_int),
            "Interés": int(int_m), "Seg. Desgravamen": int(seg_desg), 
            "Seg. Todo Riesgo": int(seg_todo_riesgo_mensual), "Cuota Total": int(c_total),
            "Saldo Final": int(max(0, saldo)), "Interés Acumulado": int(int_ac), 
            "Capital Acumulado": int(cap_ac), "Total Seguros": int(seg_desg + seg_todo_riesgo_mensual)
        })
        flujos.append(c_total)
    
    tcea = ((1 + npf.irr(flujos))**12 - 1) * 100
    return {"df": pd.DataFrame(data), "tcea": tcea}

# --- 4. INPUTS GLOBALES (SIDEBAR) ---
with st.sidebar:
    st.title("🏦 Panel de Auditoría")
    monto_p = st.number_input("Monto Préstamo (S/)", value=250000)
    valor_i = st.number_input("Valor Inmueble (S/)", value=300000)
    plazo_p = st.slider("Plazo (Años)", 5, 30, 20)
    c_dobles_p = st.checkbox("Cuotas Julio/Dic", value=True)
    fecha_p = st.date_input("Fecha Desembolso", datetime.now())

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
    c_ord = f"S/ {df_ind[df_ind['Tipo']=='ORDINARIA']['Cuota Total'].iloc[0]:,.0f}"
    m1.metric("Cuota Ordinaria", c_ord)
    m2.metric("Total Intereses", f"S/ {df_ind['Interés'].sum():,.0f}")
    m3.metric("Total Seguros", f"S/ {df_ind['Total Seguros'].sum():,.0f}")
    with m4: st.markdown(f'<div class="tcea-card"><small>TCEA FINAL</small><br><b style="font-size:1.5rem;">{res["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig_area = go.Figure()
        fig_area.add_trace(go.Scatter(x=df_ind["N°"], y=df_ind["Interés Acumulado"], name="Interés", stackgroup='one', fillcolor='rgba(239, 68, 68, 0.5)', line=dict(color='#ef4444')))
        fig_area.add_trace(go.Scatter(x=df_ind["N°"], y=df_ind["Capital Acumulado"], name="Capital", stackgroup='one', fillcolor='rgba(16, 185, 129, 0.5)', line=dict(color='#10b981')))
        fig_area.update_layout(title="Interés vs Capital", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig_area, use_container_width=True)
    with col_g2:
        fig_line = px.line(df_ind, x="N°", y="Saldo Final", title="Saldo del Préstamo")
        fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig_line, use_container_width=True)

    st.subheader("📝 Notas a Considerar")
    st.markdown("""<div class="nota-box"><ul><li><b>Seguro de Desgravamen:</b> Sobre saldo principal.</li><li><b>Seguro Todo Riesgo:</b> Sobre monto asegurado.</li></ul></div>""", unsafe_allow_html=True)
    
    # Exportación Pestaña 1
    datos_pdf1 = {
        "Monto Prestamo": f"S/ {monto_p:,.0f}", "TEA": f"{tea_ind}%", 
        "Cuota Ordinaria": c_ord, "TCEA": f"{res['tcea']:.2f}%"
    }
    pdf1 = create_pdf("REPORTE INDIVIDUAL - AUDITORIA INMOBILIARIA", datos_pdf1, ["El seguro de desgravamen baja cada mes.", "El seguro de inmueble es costo fijo."])
    st.markdown(get_binary_link(pdf1, "📄 Descargar Reporte Individual"), unsafe_allow_html=True)

# --- TAB 2: COMPARATIVA ---
with tab2:
    st.subheader("⚔️ Auditoría entre Entidades Financieras")
    c_b1, c_b2 = st.columns(2)
    with c_b1:
        n_a = st.text_input("Nombre Banco A", value="BANCO A")
        res1 = calcular_motor(monto_p, valor_i, st.number_input("TEA A (%)", value=9.5, key="t1"), st.number_input("Desgravamen A (%)", 0.05, key="d1"), st.number_input("Riesgo A (%)", 0.3, key="r1"), plazo_p, c_dobles_p, fecha_p)
    with c_b2:
        n_b = st.text_input("Nombre Banco B", value="BANCO B")
        res2 = calcular_motor(monto_p, valor_i, st.number_input("TEA B (%)", value=9.2, key="t2"), st.number_input("Desgravamen B (%)", 0.08, key="d2"), st.number_input("Riesgo B (%)", 0.28, key="r2"), plazo_p, c_dobles_p, fecha_p)

    total_a, total_b = res1['df']["Cuota Total"].sum(), res2['df']["Cuota Total"].sum()
    ahorro_val = total_a - total_b
    
    tc1, tc2, tc3 = st.columns(3)
    with tc1: st.markdown(f'<div class="tcea-card"><small>TCEA {n_a}</small><br><b style="font-size:1.8rem;">{res1["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)
    with tc2: st.markdown(f'<div class="tcea-card"><small>TCEA {n_b}</small><br><b style="font-size:1.8rem;">{res2["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)
    with tc3: st.markdown(f'<div class="{"ahorro-card" if ahorro_val > 0 else "sobrecosto-card"}"><small>{"AHORRO" if ahorro_val > 0 else "SOBRECOSTO"}</small><br><b style="font-size:1.8rem;">S/ {abs(ahorro_val):,.0f}</b></div>', unsafe_allow_html=True)

    mejor = n_a if res1['tcea'] < res2['tcea'] else n_b
    st.markdown(f'<div style="background-color: {"#1e3a8a" if mejor == n_a else "#065f46"}; padding: 20px; border-radius: 15px; text-align: center; margin: 25px 0; border: 2px solid white;"><h2 style="color: white; margin: 0;">✅ RECOMENDACIÓN: {mejor}</h2></div>', unsafe_allow_html=True)

    # Tabla Resumen
    def g_r(r): return [int(r["df"]["Cuota Total"].sum()), f"{r['tcea']:.2f}%"]
    df_res = pd.DataFrame({"Concepto": ["Pago Total", "TCEA"], n_a: g_r(res1), n_b: g_r(res2)})
    st.table(df_res.set_index("Concepto"))

    # Exportación Pestaña 2
    datos_pdf2 = {
        f"TCEA {n_a}": f"{res1['tcea']:.2f}%", f"TCEA {n_b}": f"{res2['tcea']:.2f}%",
        "Recomendacion": mejor, "Impacto Economico": f"S/ {abs(ahorro_val):,.0f}"
    }
    pdf2 = create_pdf("AUDITORIA COMPARATIVA DE BANCOS", datos_pdf2, [f"La mejor opcion es {mejor}.", "Se recomienda negociar endoso de seguros."])
    st.markdown(get_binary_link(pdf2, "📄 Descargar Comparativa PDF"), unsafe_allow_html=True)
