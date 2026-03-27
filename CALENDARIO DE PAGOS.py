# --- 5. TAB 2: COMPARATIVA (CON RESUMEN EXTENDIDO Y NOTAS) ---
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

    # Cálculos de Totales
    total_a = res1['df']["Cuota Total"].sum()
    total_b = res2['df']["Cuota Total"].sum()
    ahorro = total_a - total_b
    
    # Lógica de Recomendación
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

    # --- TABLA DE RESUMEN NUMÉRICO EXTENDIDA ---
    st.subheader("📋 Resumen Numérico Detallado")
    
    # Preparación de datos para la tabla
    int_a, seg_a = int(res1['df']["Interés"].sum()), int(res1['df']["Seguros"].sum())
    int_b, seg_b = int(res2['df']["Interés"].sum()), int(res2['df']["Seguros"].sum())
    
    gastos_fin_a = int_a + seg_a
    gastos_fin_b = int_b + seg_b
    
    # Definición de Sobrecosto (respecto al mejor banco)
    sobrecosto_a = int(total_a - total_b) if total_a > total_b else 0
    sobrecosto_b = int(total_b - total_a) if total_b > total_a else 0

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
            int_a,
            seg_a,
            gastos_fin_a,
            int(total_a),
            sobrecosto_a
        ],
        nombre_b: [
            int(res2['df'][res2['df']["Tipo"]=="ORDINARIA"]["Cuota Total"].iloc[0]),
            int_b,
            seg_b,
            gastos_fin_b,
            int(total_b),
            sobrecosto_b
        ]
    }
    
    df_resumen = pd.DataFrame(datos_tab)
    
    # Formateo de la tabla
    def format_soles(val):
        if isinstance(val, int): return f"S/ {val:,.0f}"
        return val

    st.table(df_resumen.applymap(format_soles))

    # --- GRÁFICO COMPARATIVO ---
    st.write("")
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(name=nombre_a, x=df_resumen["Concepto"][:4], y=df_resumen[nombre_a][:4], marker_color='#1e3a8a'))
    fig_comp.add_trace(go.Bar(name=nombre_b, x=df_resumen["Concepto"][:4], y=df_resumen[nombre_b][:4], marker_color='#10b981'))
    fig_comp.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
    st.plotly_chart(fig_comp, use_container_width=True)

    # --- NOTAS DE AUDITORÍA Y CÁLCULO ---
    st.write("---")
    st.subheader("📝 Notas de Auditoría de Costos")
    col_n1, col_n2 = st.columns(2)
    
    with col_n1:
        st.markdown(f"""
        <div class="nota-box">
        <h4>💰 ¿Cómo se calcula el Sobrecosto?</h4>
        <p>El sobrecosto no es solo la diferencia de tasas. Se calcula mediante la <b>Suma Total de Flujos (∑)</b>:</p>
        <ul>
            <li>Se suman las {plazo_p*12} cuotas proyectadas de cada banco.</li>
            <li>Se incluye el impacto de las cuotas dobles (Julio/Diciembre).</li>
            <li>El resultado final indica cuánto dinero <b>extra</b> regalarías al banco si eliges la opción menos eficiente.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_n2:
        st.markdown("""
        <div class="nota-box">
        <h4>⚠️ Puntos Clave de la Comparativa</h4>
        <ul>
            <li><b>Gastos Financieros:</b> Es la suma de Intereses + Seguros. Un banco con TEA baja pero seguros altos (Desgravamen/Todo Riesgo) puede ser más caro que uno con TEA alta.</li>
            <li><b>TCEA Real:</b> Es el único indicador que mide el costo real del dinero. Si el sobrecosto es mayor a S/ 5,000, se recomienda renegociar con el banco.</li>
            <li><b>Seguro de Desgravamen:</b> Se calcula sobre el saldo deudor. A medida que amortizas capital, este gasto baja.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
