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
    .ahorro-card {
        background: linear-gradient(135deg, #064e3b, #065f46); padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #10b981; color: white;
    }
    .sobrecosto-card {
        background: linear-gradient(135deg, #451a1a, #7f1d1d); padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #ef4444; color: white;
    }
    .nota-box {
        background-color: #161b22; padding: 15px; border-left: 5px solid #d1a435; border-radius: 5px; margin: 10px 0; color: #e0e0e0;
    }
    .rec-box {
        background-color: #1e3a8a; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid white; margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCIONES DE EXPORTACIÓN (CONTENIDO AMPLIADO) ---
def create_pdf(titulo, datos_dict, notas_pro, glosario=None, asunciones=None):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado Profesional
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 10, txt=titulo, ln=True, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 8)
    pdf.cell(0, 8, txt=f"Documento Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True, align='R')
    pdf.ln(5)
    
    # Aviso Legal (Referencial)
    pdf.set_fill_color(255, 235, 204)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(0, 6, txt="AVISO IMPORTANTE: Este informe es estrictamente REFERENCIAL.", ln=True, fill=True, align='C')
    pdf.set_font("Arial", '', 7)
    pdf.multi_cell(0, 4, txt="Los valores presentados son proyecciones basadas en modelos matematicos estandar. Las condiciones finales dependen exclusivamente de la evaluacion crediticia y las politicas vigentes de la entidad financiera al momento del desembolso.")
    pdf.ln(5)

    # Datos del Crédito
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, txt="1. RESUMEN DE CONDICIONES DETALLADAS:", ln=True)
    pdf.set_font("Arial", '', 9)
    for k, v in datos_dict.items():
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(95, 7, txt=f" {k}", border=1, fill=True)
        pdf.cell(95, 7, txt=f" {v}", border=1, ln=True)
    
    # Asunciones y Consideraciones del Modelo
    if asunciones:
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 8, txt="2. CONSIDERACIONES DEL MODELO FINANCIERO:", ln=True)
        pdf.set_font("Arial", '', 8)
        for asun in asunciones:
            pdf.multi_cell(0, 5, txt=f"- {asun}")

    # Glosario y Recomendaciones
    if glosario:
        pdf.ln(5); pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, txt="3. ANALISIS TECNICO Y CONCEPTOS:", ln=True)
        for g_k, g_v in glosario.items():
            pdf.set_font("Arial", 'B', 8); pdf.write(5, f"{g_k}: "); pdf.set_font("Arial", '', 8); pdf.write(5, f"{g_v}\n"); pdf.ln(2)

    pdf.ln(5); pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, txt="4. RECOMENDACIONES ESTRATEGICAS FINANCIERAS:", ln=True)
    pdf.set_font("Arial", '', 9)
    for nota in notas_pro:
        pdf.multi_cell(0, 6, txt=f"[*] {nota}")
    
    # Firma de Marca
    pdf.ln(10); pdf.set_draw_color(200, 200, 200); pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5); pdf.set_font("Arial", 'B', 10); pdf.cell(0, 5, txt="Ing. Jancarlo Mendoza", ln=True, align='C')
    pdf.set_font("Arial", '', 8); pdf.cell(0, 5, txt="Consultoria Inmobiliaria y Analisis de Riesgo | Lima, Peru", ln=True, align='C')
    
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
    int_ac, cap_ac = 0, 0
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
    return {"df": pd.DataFrame(data), "tcea": ((1 + npf.irr(flujos))**12 - 1) * 100}

# --- 4. PANEL LATERAL ---
with st.sidebar:
    st.title("🏦 Panel de Auditoría")
    m_p = st.number_input("Monto Préstamo (S/)", value=250000)
    v_i = st.number_input("Valor Inmueble (S/)", value=300000)
    plazo_p = st.slider("Plazo (Años)", 5, 30, 20)
    c_dobles_p = st.checkbox("Cuotas Julio/Dic", value=True)
    fecha_p = st.date_input("Fecha Desembolso", datetime.now())

tab1, tab2 = st.tabs(["📊 Simulador Individual", "⚔️ Comparativa de Bancos"])

# --- PESTAÑA 1 ---
with tab1:
    col1, col2, col3 = st.columns(3)
    tea1 = col1.number_input("TEA Banco (%)", 9.5, key="tea1")
    des1 = col2.number_input("Desgravamen (%)", 0.05, format="%.3f", key="des1")
    rie1 = col3.number_input("Riesgo Anual (%)", 0.3, format="%.2f", key="rie1")
    
    res = calcular_motor(m_p, v_i, tea1, des1, rie1, plazo_p, c_dobles_p, fecha_p)
    df = res["df"]
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Cuota Ordinaria", f"S/ {df[df['Tipo']=='ORDINARIA']['Cuota Total'].iloc[0]:,.0f}")
    m2.metric("Total Intereses", f"S/ {df['Interés'].sum():,.0f}")
    m3.metric("Total Seguros", f"S/ {df['Total Seguros'].sum():,.0f}")
    m4.metric("TCEA", f"{res['tcea']:.2f} %") # MISMO FORMATO QUE LAS OTRAS METRICAS

    g1, g2 = st.columns(2)
    with g1:
        f1 = go.Figure()
        f1.add_trace(go.Scatter(x=df["N°"], y=df["Interés Acumulado"], name="Interés", stackgroup='one', fillcolor='rgba(239, 68, 68, 0.4)'))
        f1.add_trace(go.Scatter(x=df["N°"], y=df["Capital Acumulado"], name="Capital", stackgroup='one', fillcolor='rgba(16, 185, 129, 0.4)'))
        f1.update_layout(title="Interés vs Capital Acumulado", paper_bgcolor='rgba(0,0,0,0)', font_color="white", plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(f1, use_container_width=True)
    with g2:
        f2 = px.line(df, x="N°", y="Saldo Final", title="Proyección de Saldo Deudor")
        f2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(f2, use_container_width=True)

    st.subheader("📋 Calendario de Pagos")
    st.dataframe(df[["N°", "Mes", "Tipo", "Saldo Inicial", "Cuota Cap+Int", "Interés", "Seg. Desgravamen", "Seg. Todo Riesgo", "Cuota Total", "Saldo Final"]], use_container_width=True)
    
    # PDF 1 AMPLIADO
    d_pdf1 = {
        "Monto del Credito": f"S/ {m_p:,.0f}", "Tasa TEA": f"{tea1}%", "Tasa TCEA": f"{res['tcea']:.2f}%",
        "Plazo": f"{plazo_p} Anios", "Pago Total Estimado": f"S/ {df['Cuota Total'].sum():,.0f}",
        "Costo Total de Seguros": f"S/ {df['Total Seguros'].sum():,.0f}",
        "Intereses Totales": f"S/ {df['Interés'].sum():,.0f}"
    }
    a_pdf1 = [
        "Modelo Frances: Amortizacion constante de capital + interes sobre el saldo pendiente.",
        "Metodo de Intereses: Calculado mensualmente sobre el capital que aun se adeuda.",
        "Seguro Desgravamen: Al ser sobre saldo deudor, el costo disminuye conforme usted paga su deuda.",
        "Periodicidad: Se consideran 12 cuotas ordinarias y 2 cuotas dobles (Julio/Diciembre) segun seleccion."
    ]
    g_pdf1 = {
        "TCEA (Costo Real)": "Es el indicador real para comparar. Incluye la TEA mas todos los seguros y cargos adicionales.",
        "Desgravamen": "Seguro que cancela la deuda en caso de fallecimiento, protegiendo el patrimonio familiar.",
        "Modelo Frances": "Sistema donde las cuotas suelen ser iguales, pero la proporcion de interes baja con el tiempo."
    }
    n_pdf1 = [
        "REFERENCIAL: Este documento no constituye una oferta vinculante.",
        "Estrategia: Los prepagos en los primeros 36 meses tienen un impacto desproporcionadamente positivo en el ahorro de intereses.",
        "Seguros: Usted tiene derecho a endosar polizas externas si cumplen los requisitos de la SBS.",
        "Inflacion: Evalue su capacidad de pago considerando que la cuota hipotecaria suele ser fija frente a una inflacion variable."
    ]
    pdf1 = create_pdf("AUDITORÍA FINANCIERA INDIVIDUAL", d_pdf1, n_pdf1, glosario=g_pdf1, asunciones=a_pdf1)
    st.markdown(get_binary_link(pdf1, "📄 Descargar Reporte de Auditoría Individual PDF"), unsafe_allow_html=True)

# --- PESTAÑA 2 ---
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

    st.write("")
    tc1, tc2, tc3 = st.columns(3)
    tc1.metric(f"TCEA {na}", f"{r1['tcea']:.2f} %")
    tc2.metric(f"TCEA {nb}", f"{r2['tcea']:.2f} %")
    ah_v = r1['df']["Cuota Total"].sum() - r2['df']["Cuota Total"].sum()
    with tc3:
        st.markdown(f'<div class="{"ahorro-card" if ah_v > 0 else "sobrecosto-card"}"><small>{"AHORRO" if ah_v > 0 else "SOBRECOSTO"}</small><br><b style="font-size:1.5rem;">S/ {abs(ah_v):,.0f}</b></div>', unsafe_allow_html=True)

    mj = na if r1['tcea'] < r2['tcea'] else nb
    st.markdown(f'<div class="rec-box"><h2 style="color:white;margin:0;">✅ RECOMENDACIÓN: {mj}</h2></div>', unsafe_allow_html=True)

    d_res = pd.DataFrame({"Concepto": ["TEA", "Seg. Desgravamen", "Seg. Todo Riesgo", "TCEA", "Cuota Ord.", "Total Intereses", "Total Seguros", "Pago Total"], 
                         na: [f"{ta}%", f"{da}%", f"{ra}%", f"{r1['tcea']:.2f}%", f"S/ {int(r1['df']['Cuota Total'].iloc[0]):,}", f"S/ {int(r1['df']['Interés'].sum()):,}", f"S/ {int(r1['df']['Total Seguros'].sum()):,}", f"S/ {int(r1['df']['Cuota Total'].sum()):,}"],
                         nb: [f"{tb}%", f"{db}%", f"{rb}%", f"{r2['tcea']:.2f}%", f"S/ {int(r2['df']['Cuota Total'].iloc[0]):,}", f"S/ {int(r2['df']['Interés'].sum()):,}", f"S/ {int(r2['df']['Total Seguros'].sum()):,}", f"S/ {int(r2['df']['Cuota Total'].sum()):,}"]})
    st.table(d_res.set_index("Concepto"))
    
    # PDF 2 AMPLIADO
    d_pdf2 = {f"TCEA {na}": f"{r1['tcea']:.2f}%", f"TCEA {nb}": f"{r2['tcea']:.2f}%", "Impacto Financiero": f"S/ {abs(ah_v):,.0f}", "Entidad Recomendada": mj}
    a_pdf2 = [
        "El estudio compara dos escenarios financieros bajo el mismo capital y tiempo.",
        "Se prioriza la TCEA como indicador de eficiencia financiera sobre la tasa nominal (TEA).",
        "Los seguros han sido proyectados segun las tasas ingresadas; cambios en estas alteran el resultado final."
    ]
    n_pdf2 = [
        "DOCUMENTO REFERENCIAL: Las tasas varian diariamente segun el perfil de riesgo del cliente.",
        f"Conclusión: Optar por {mj} representa una optimización de su patrimonio de S/ {abs(ah_v):,.0f}.",
        "Negociación: Use este cuadro comparativo para solicitar una mejora de condiciones en la entidad de su preferencia.",
        "Recomendacion: Revise los beneficios adicionales (cuenta sueldo, seguros de salud asociados) que no forman parte de este analisis cuantitativo."
    ]
    pdf2 = create_pdf("AUDITORÍA COMPARATIVA ESTRATÉGICA", d_pdf2, n_pdf2, asunciones=a_pdf2)
    st.markdown(get_binary_link(pdf2, "📄 Descargar Comparativa Estratégica PDF"), unsafe_allow_html=True)
