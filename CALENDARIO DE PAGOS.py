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
    .tcea-card-neutral {
        background-color: #262730;
        padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #464855; color: #e0e0e0;
        margin-bottom: 10px;
    }
    .ahorro-card {
        background: linear-gradient(135deg, #064e3b, #065f46);
        padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #10b981; color: white;
    }
    .sobrecosto-card {
        background: linear-gradient(135deg, #451a1a, #7f1d1d);
        padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #ef4444; color: white;
    }
    .nota-box {
        background-color: #161b22; padding: 15px; border-left: 5px solid #d1a435; border-radius: 5px; margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCIONES DE EXPORTACIÓN ROBUSTECIDAS ---
def create_pdf(titulo, datos_dict, notas_pro, glosario=None):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, txt=titulo, ln=True, align='C')
    pdf.set_font("Arial", '', 8)
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pdf.cell(0, 10, txt=f"Fecha de emision: {ahora}", ln=True, align='R')
    pdf.ln(5)
    
    # Tabla de Datos
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, txt="1. RESUMEN DE CONDICIONES FINANCIERAS:", ln=True)
    pdf.set_font("Arial", '', 9)
    for k, v in datos_dict.items():
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(95, 7, txt=f" {k}", border=1, fill=True)
        pdf.cell(95, 7, txt=f" {v}", border=1, ln=True)
    
    # Glosario Técnico (Solo PDF 1)
    if glosario:
        pdf.ln(8)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 8, txt="2. CONCEPTOS CLAVE A CONSIDERAR:", ln=True)
        pdf.set_font("Arial", '', 8)
        for g_k, g_v in glosario.items():
            pdf.set_font("Arial", 'B', 8)
            pdf.write(5, f"{g_k}: ")
            pdf.set_font("Arial", '', 8)
            pdf.write(5, f"{g_v}\n")
            pdf.ln(2)

    # Recomendaciones / Notas
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, txt="3. RECOMENDACIONES DEL ASESOR:", ln=True)
    pdf.set_font("Arial", '', 9)
    for nota in notas_pro:
        pdf.multi_cell(0, 6, txt=f"> {nota}")
    
    # Footer de Marca
    pdf.ln(10)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, txt="Elaborado por: Ing. Jancarlo Mendoza", ln=True, align='C')
    pdf.set_font("Arial", '', 8)
    pdf.cell(0, 5, txt="Asesoria Especializada en Credito Hipotecario e Inversion Inmobiliaria", ln=True, align='C')
    pdf.cell(0, 5, txt="Contacto y Redes: @jancarlo.inmobiliario", ln=True, align='C')
    
    return pdf.output(dest="S").encode("latin-1")

def get_binary_link(bin_file, file_label="Archivo"):
    b64 = base64.b64encode(bin_file).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{file_label}.pdf" style="text-decoration:none;"><button style="width:100%; padding:12px; background-color:#d1a435; color:black; font-weight:bold; border:none; border-radius:5px; cursor:pointer;">{file_label}</button></a>'

# --- 3. MOTOR DE CÁLCULO ---
def calcular_motor(monto, valor_inm, tea, t_des, t_riesgo, plazo, c_dobles, fecha_d):
    tem = (1 + tea/100)**(1/12) - 1
    n_meses = plazo * 12
    seg_todo_riesgo_m = valor_inm * (t_riesgo/100) / 12
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
        c_total = c_cap_int + seg_desg + seg_todo_riesgo_m
        saldo -= amort
        int_ac += int_m; cap_ac += amort
        data.append({
            "N°": i, "Mes": (fecha_d + pd.DateOffset(months=i)).strftime('%b-%Y'),
            "Tipo": "DOBLE" if es_d else "ORDINARIA",
            "Saldo Inicial": int(saldo + amort), "Cuota Cap+Int": int(c_cap_int),
            "Interés": int(int_m), "Seg. Desgravamen": int(seg_desg), 
            "Seg. Todo Riesgo": int(seg_todo_riesgo_m), "Cuota Total": int(c_total),
            "Saldo Final": int(max(0, saldo)), "Interés Acumulado": int(int_ac), 
            "Capital Acumulado": int(cap_ac), "Total Seguros": int(seg_desg + seg_todo_riesgo_m)
        })
        flujos.append(c_total)
    tcea = ((1 + npf.irr(flujos))**12 - 1) * 100
    return {"df": pd.DataFrame(data), "tcea": tcea}

# --- 4. PANEL DE CONTROL ---
with st.sidebar:
    st.title("🏦 Panel de Auditoría")
    m_p = st.number_input("Monto Préstamo (S/)", value=250000)
    v_i = st.number_input("Valor Inmueble (S/)", value=300000)
    plazo_p = st.slider("Plazo (Años)", 5, 30, 20)
    c_dobles_p = st.checkbox("Cuotas Julio/Dic", value=True)
    fecha_p = st.date_input("Fecha Desembolso", datetime.now())

tab1, tab2 = st.tabs(["📊 Simulador Individual", "⚔️ Comparativa de Bancos"])

# --- TAB 1: INDIVIDUAL ---
with tab1:
    c1, c2, c3 = st.columns(3)
    tea1 = c1.number_input("TEA Banco (%)", 9.5, key="tea1")
    des1 = c2.number_input("Desgravamen (%)", 0.05, format="%.3f", key="des1")
    rie1 = c3.number_input("Riesgo Anual (%)", 0.3, format="%.2f", key="rie1")
    
    res = calcular_motor(m_p, v_i, tea1, des1, rie1, plazo_p, c_dobles_p, fecha_p)
    df = res["df"]
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Cuota Ordinaria", f"S/ {df[df['Tipo']=='ORDINARIA']['Cuota Total'].iloc[0]:,.0f}")
    m2.metric("Total Intereses", f"S/ {df['Interés'].sum():,.0f}")
    m3.metric("Total Seguros", f"S/ {df['Total Seguros'].sum():,.0f}")
    with m4: st.markdown(f'<div class="tcea-card-neutral"><small>TCEA</small><br><b>{res["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)

    # Gráficos y Tabla (UI)
    st.subheader("📋 Calendario de Pagos Detallado")
    st.dataframe(df[["N°", "Mes", "Tipo", "Saldo Inicial", "Cuota Cap+Int", "Interés", "Seg. Desgravamen", "Seg. Todo Riesgo", "Cuota Total", "Saldo Final"]], use_container_width=True)
    
    # PDF Pestaña 1
    d_pdf1 = {
        "Valor Inmueble": f"S/ {v_i:,.0f}", "Monto Prestamo": f"S/ {m_p:,.0f}",
        "TEA (Tasa Efectiva Anual)": f"{tea1}%", "TCEA (Costo Efectivo)": f"{res['tcea']:.2f}%",
        "Plazo": f"{plazo_p} Anios", "Cuota Ordinaria Estimada": f"S/ {df['Cuota Total'].iloc[0]:,.0f}",
        "Total Intereses a Pagar": f"S/ {df['Interés'].sum():,.0f}",
        "Total Seguros a Pagar": f"S/ {df['Total Seguros'].sum():,.0f}"
    }
    g_pdf1 = {
        "Sistema de Amortizacion": "Modelo Frances (Cuotas Constantes). Es el mas usado en el sistema peruano, donde el interes se calcula sobre el saldo deudor.",
        "TEA": "Es la tasa que el banco cobra por el dinero prestado.",
        "Seguro Desgravamen": "Protege a tus herederos cancelando la deuda en caso de fallecimiento. Se calcula sobre el saldo principal, por lo que baja cada mes.",
        "Seguro Todo Riesgo": "Protege el inmueble contra siniestros. Se calcula sobre el valor del inmueble y suele ser un costo fijo.",
        "TCEA": "Es el costo real. Incluye TEA + Seguros + Comisiones. Es el indicador real para comparar bancos."
    }
    n_pdf1 = ["Recuerda que puedes realizar prepagos para reducir el interes total.", "El seguro de desgravamen puede ser endosado si ya cuentas con un seguro de vida con cobertura suficiente."]
    
    pdf1 = create_pdf("ANÁLISIS DE CRÉDITO HIPOTECARIO", d_pdf1, n_pdf1, glosario=g_pdf1)
    st.markdown(get_binary_link(pdf1, "📄 Descargar Analisis Profesional PDF"), unsafe_allow_html=True)

# --- TAB 2: COMPARATIVA ---
with tab2:
    cb1, cb2 = st.columns(2)
    with cb1:
        na = st.text_input("Banco A", "BANCO A")
        ta, da, ra = st.number_input("TEA A", 9.5, key="ta"), st.number_input("Desg. A", 0.05, key="da"), st.number_input("Rie. A", 0.3, key="ra")
        r1 = calcular_motor(m_p, v_i, ta, da, ra, plazo_p, c_dobles_p, fecha_p)
    with cb2:
        nb = st.text_input("Banco B", "BANCO B")
        tb, db, rb = st.number_input("TEA B", 9.2, key="tb"), st.number_input("Desg. B", 0.08, key="db"), st.number_input("Rie. B", 0.28, key="rb")
        r2 = calcular_motor(m_p, v_i, tb, db, rb, plazo_p, c_dobles_p, fecha_p)

    ah_v = r1['df']["Cuota Total"].sum() - r2['df']["Cuota Total"].sum()
    mj = na if r1['tcea'] < r2['tcea'] else nb
    
    # PDF Pestaña 2
    d_pdf2 = {
        f"TEA {na}": f"{ta}%", f"TEA {nb}": f"{tb}%",
        f"Seg. Desgravamen {na}": f"{da}%", f"Seg. Desgravamen {nb}": f"{db}%",
        f"Seg. Todo Riesgo {na}": f"{ra}%", f"Seg. Todo Riesgo {nb}": f"{rb}%",
        f"TCEA {na}": f"{r1['tcea']:.2f}%", f"TCEA {nb}": f"{r2['tcea']:.2f}%",
        "DIFERENCIA TOTAL (SOBRECOSTO)": f"S/ {abs(ah_v):,.0f}",
        "RECOMENDACION ESTRATEGICA": mj
    }
    n_pdf2 = [
        f"La mejor opcion financiera es {mj} debido a su menor TCEA.",
        "Considere el endoso del seguro de desgravamen para eliminar este costo mensual si tiene un seguro de vida externo.",
        "Negocie el Seguro Todo Riesgo; el banco esta obligado a aceptar polizas endosadas si cumplen los requisitos.",
        "Incluso una diferencia de 0.20% en la TCEA puede representar miles de soles de ahorro a largo plazo."
    ]
    pdf2 = create_pdf("AUDITORÍA COMPARATIVA BANCARIA", d_pdf2, n_pdf2)
    
    st.markdown(get_binary_link(pdf2, "📄 Descargar Auditoria Comparativa PDF"), unsafe_allow_html=True)
