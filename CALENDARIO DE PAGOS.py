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

# --- 2. FUNCIONES DE EXPORTACIÓN MEJORADAS ---
def create_pdf(titulo, datos_dict, notas, es_comparativa=False):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, txt=titulo, ln=True, align='C')
    pdf.set_font("Arial", '', 9)
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pdf.cell(0, 10, txt=f"Generado el: {ahora}", ln=True, align='R')
    pdf.ln(5)
    
    # Datos Principales
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt="RESUMEN ESTRATEGICO DEL CREDITO:", ln=True)
    pdf.set_draw_color(50, 50, 50)
    pdf.set_font("Arial", '', 10)
    
    for k, v in datos_dict.items():
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(95, 8, txt=f" {k}", border=1, fill=True)
        pdf.cell(95, 8, txt=f" {v}", border=1, ln=True)
    
    # Notas Importantes
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, txt="CLÁUSULAS Y NOTAS DE AUDITORÍA:", ln=True)
    pdf.set_font("Arial", '', 9)
    for nota in notas:
        pdf.multi_cell(0, 6, txt=f"* {nota}")
    
    pdf.ln(5)
    pdf.set_font("Arial", 'I', 8)
    pdf.multi_cell(0, 5, txt="NOTA: Este reporte es estrictamente REFERENCIAL y se basa en las condiciones actuales del mercado financiero. Los montos finales dependen de la evaluacion crediticia y las politicas de cada entidad bancaria.")
    
    # Firma y Redes
    pdf.ln(15)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, txt="Elaborado por: Ing. Jancarlo Mendoza", ln=True, align='C')
    pdf.set_font("Arial", '', 9)
    pdf.cell(0, 5, txt="Asesoria Inmobiliaria Personalizada", ln=True, align='C')
    pdf.cell(0, 5, txt="Siguenos en: @jancarlo.inmobiliario", ln=True, align='C')
    
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

# --- 4. INPUTS GLOBALES ---
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
    with col_a2: des_ind = st.number_input("Desgravamen (%)", 0.05, format="%.3f", key="des_ind")
    with col_a3: ries_ind = st.number_input("Riesgo Anual (%)", 0.3, format="%.2f", key="ries_ind")
    
    res = calcular_motor(monto_p, valor_i, tea_ind, des_ind, ries_ind, plazo_p, c_dobles_p, fecha_p)
    df_ind = res["df"]
    
    m1, m2, m3, m4 = st.columns(4)
    c_ord = f"S/ {df_ind[df_ind['Tipo']=='ORDINARIA']['Cuota Total'].iloc[0]:,.0f}"
    m1.metric("Cuota Ordinaria", c_ord)
    m2.metric("Total Intereses", f"S/ {df_ind['Interés'].sum():,.0f}")
    m3.metric("Total Seguros", f"S/ {df_ind['Total Seguros'].sum():,.0f}")
    with m4: st.markdown(f'<div class="tcea-card"><small>TCEA FINAL</small><br><b style="font-size:1.5rem;">{res["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)

    # Gráficos
    cg1, cg2 = st.columns(2)
    with cg1:
        f_area = go.Figure()
        f_area.add_trace(go.Scatter(x=df_ind["N°"], y=df_ind["Interés Acumulado"], name="Interés", stackgroup='one', fillcolor='rgba(239, 68, 68, 0.4)'))
        f_area.add_trace(go.Scatter(x=df_ind["N°"], y=df_ind["Capital Acumulado"], name="Capital", stackgroup='one', fillcolor='rgba(16, 185, 129, 0.4)'))
        f_area.update_layout(title="Acumulado: Interés vs Capital", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(f_area, use_container_width=True)
    with cg2:
        f_line = px.line(df_ind, x="N°", y="Saldo Final", title="Proyección de Deuda")
        f_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(f_line, use_container_width=True)

    # Calendario y Notas
    st.subheader("📋 Calendario de Pagos Detallado")
    st.dataframe(df_ind[["N°", "Mes", "Tipo", "Saldo Inicial", "Cuota Cap+Int", "Interés", "Seg. Desgravamen", "Seg. Todo Riesgo", "Cuota Total", "Saldo Final"]], use_container_width=True)
    
    st.subheader("📝 Notas a Considerar")
    st.markdown("""<div class="nota-box"><ul><li><b>Seguro de Desgravamen:</b> Calculado sobre saldo principal.</li><li><b>Seguro de Todo Riesgo:</b> Calculado sobre el monto asegurado.</li><li><b>Amortizacion:</b> Las primeras cuotas tienen carga mayor de interes.</li></ul></div>""", unsafe_allow_html=True)

    # Exportación PDF 1
    d_pdf1 = {
        "Valor Inmueble": f"S/ {valor_i:,.0f}", "Monto Prestamo": f"S/ {monto_p:,.0f}",
        "TEA": f"{tea_ind}%", "TCEA": f"{res['tcea']:.2f}%", "Cuota Ordinaria": c_ord,
        "Plazo": f"{plazo_p} Anios", "Pago Total Estimado": f"S/ {df_ind['Cuota Total'].sum():,.0f}"
    }
    n_pdf1 = ["El seguro de desgravamen disminuye con el capital.", "El seguro de inmueble es un costo mensual fijo.", "Considerar que Julio y Diciembre tienen impacto doble."]
    pdf1 = create_pdf("AUDITORIA INDIVIDUAL - JANCARLO INMOBILIARIO", d_pdf1, n_pdf1)
    st.markdown(get_binary_link(pdf1, "📄 Generar Reporte Detallado PDF"), unsafe_allow_html=True)

# --- TAB 2: COMPARATIVA ---
with tab2:
    st.subheader("⚔️ Auditoría entre Entidades Financieras")
    cb1, cb2 = st.columns(2)
    with cb1:
        na = st.text_input("Banco A", "BANCO A")
        ta, da, ra = st.number_input("TEA A (%)", 9.5, key="ta"), st.number_input("Desg. A (%)", 0.05, key="da"), st.number_input("Riesgo A (%)", 0.3, key="ra")
        r1 = calcular_motor(monto_p, valor_i, ta, da, ra, plazo_p, c_dobles_p, fecha_p)
    with cb2:
        nb = st.text_input("Banco B", "BANCO B")
        tb, db, rb = st.number_input("TEA B (%)", 9.2, key="tb"), st.number_input("Desg. B (%)", 0.08, key="db"), st.number_input("Riesgo B (%)", 0.28, key="rb")
        r2 = calcular_motor(monto_p, valor_i, tb, db, rb, plazo_p, c_dobles_p, fecha_p)

    # Tarjetas y Recomendación
    ta_tot, tb_tot = r1['df']["Cuota Total"].sum(), r2['df']["Cuota Total"].sum()
    ah_v = ta_tot - tb_tot
    tc1, tc2, tc3 = st.columns(3)
    tc1.markdown(f'<div class="tcea-card"><small>TCEA {na}</small><br><b>{r1["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)
    tc2.markdown(f'<div class="tcea-card"><small>TCEA {nb}</small><br><b>{r2["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)
    tc3.markdown(f'<div class="{"ahorro-card" if ah_v > 0 else "sobrecosto-card"}"><small>{"AHORRO" if ah_v > 0 else "SOBRECOSTO"}</small><br><b>S/ {abs(ah_v):,.0f}</b></div>', unsafe_allow_html=True)

    mj = na if r1['tcea'] < r2['tcea'] else nb
    st.markdown(f'<div style="background-color:{"#1e3a8a" if mj==na else "#065f46"}; padding:20px; border-radius:15px; text-align:center; border:2px solid white;"><h2 style="color:white;margin:0;">✅ RECOMENDACIÓN: {mj}</h2></div>', unsafe_allow_html=True)

    # Resumen Numérico y Gráfico
    st.subheader("📋 Resumen Numérico de Auditoría")
    def gr(r): return [int(r["df"]["Cuota Total"].iloc[0]), int(r["df"]["Interés"].sum()), int(r["df"]["Total Seguros"].sum()), int(r["df"]["Cuota Total"].sum())]
    d_res = pd.DataFrame({"Concepto": ["Cuota Ord.", "Total Intereses", "Total Seguros", "Pago Total"], na: gr(r1), nb: gr(r2)})
    st.table(d_res.set_index("Concepto").applymap(lambda x: f"S/ {x:,.0f}"))
    
    fig_c = go.Figure()
    fig_c.add_trace(go.Bar(name=na, x=d_res["Concepto"][:3], y=d_res[na][:3], marker_color='#1e3a8a'))
    fig_c.add_trace(go.Bar(name=nb, x=d_res["Concepto"][:3], y=d_res[nb][:3], marker_color='#10b981'))
    fig_c.update_layout(title="Diferencia de Costos", barmode='group', paper_bgcolor='rgba(0,0,0,0)', font_color="white")
    st.plotly_chart(fig_c, use_container_width=True)

    # Exportación PDF 2
    d_pdf2 = {
        f"TCEA {na}": f"{r1['tcea']:.2f}%", f"TCEA {nb}": f"{r2['tcea']:.2f}%",
        "Diferencia Patrimonial": f"S/ {abs(ah_v):,.0f}", "Opcion Sugerida": mj,
        f"Costo Total {na}": f"S/ {ta_tot:,.0f}", f"Costo Total {nb}": f"S/ {tb_tot:,.0f}"
    }
    pdf2 = create_pdf("AUDITORIA COMPARATIVA - BANCOS", d_pdf2, [f"Se recomienda elegir {mj} por ahorro proyectado.", "Recuerde negociar el endoso de seguros para mejorar estos numeros."])
    st.markdown(get_binary_link(pdf2, "📄 Generar Comparativa PDF"), unsafe_allow_html=True)
