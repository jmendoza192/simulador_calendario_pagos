# --- TAB 2: COMPARATIVA BANCARIA (ACTUALIZADA CON NOTAS) ---
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
    pago_total_a = res1['df']["Cuota Total"].sum()
    pago_total_b = res2['df']["Cuota Total"].sum()
    ahorro = pago_total_a - pago_total_b
    
    st.write("---")
    cm1, cm2, cm3 = st.columns(3)
    cm1.markdown(f'<div class="tcea-card">TCEA BANCO A<br><b style="font-size:1.8rem;">{res1["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)
    cm2.markdown(f'<div class="tcea-card">TCEA BANCO B<br><b style="font-size:1.8rem;">{res2["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)
    with cm3:
        color_ah = "#10b981" if ahorro > 0 else "#ef4444"
        etiqueta = "AHORRO PROYECTADO" if ahorro > 0 else "SOBRECOSTO ESTIMADO"
        st.markdown(f'<div class="ahorro-card" style="background:{color_ah}">{etiqueta}<br><b style="font-size:1.8rem;">S/ {abs(ahorro):,.0f}</b></div>', unsafe_allow_html=True)

    # GRÁFICO COMPARATIVO
    st.write("")
    comp_df = pd.DataFrame({
        "Concepto": ["Cuota Ordinaria", "Total Intereses", "Total Seguros"],
        "Banco A": [res1['df'][res1['df']["Tipo"]=="ORDINARIA"]["Cuota Total"].iloc[0], res1['df']["Interés"].sum(), res1['df']["df"]["Seguros"].sum() if 'df' in res1 else res1['df']['Seguros'].sum()],
        "Banco B": [res2['df'][res2['df']["Tipo"]=="ORDINARIA"]["Cuota Total"].iloc[0], res2['df']["Interés"].sum(), res2['df']["df"]["Seguros"].sum() if 'df' in res2 else res2['df']['Seguros'].sum()]
    })
    # Ajuste rápido para asegurar que lea bien la columna Seguros
    comp_df = pd.DataFrame({
        "Concepto": ["Cuota Ord.", "Total Interés", "Total Seguros"],
        "Banco A": [res1['df'][res1['df']["Tipo"]=="ORDINARIA"]["Cuota Total"].iloc[0], res1['df']["Interés"].sum(), res1['df']["df"]["Seguros"].sum()],
        "Banco B": [res2['df'][res2['df']["Tipo"]=="ORDINARIA"]["Cuota Total"].iloc[0], res2['df']["Interés"].sum(), res2['df']["df"]["Seguros"].sum()]
    })
    
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(name='Banco A', x=comp_df["Concepto"], y=comp_df["Banco A"], marker_color='#1e3a8a'))
    fig_comp.add_trace(go.Bar(name='Banco B', x=comp_df["Concepto"], y=comp_df["Banco B"], marker_color='#10b981'))
    fig_comp.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
    fig_comp.update_yaxes(tickprefix="S/ ", tickformat=",.0f")
    st.plotly_chart(fig_comp, use_container_width=True)

    # --- NOTAS DE CÁLCULO Y AUDITORÍA ---
    st.write("---")
    st.subheader("📝 Notas de Auditoría Comparativa")
    n_col1, n_col2 = st.columns(2)
    
    with n_col1:
        st.markdown(f"""
        <div class="nota-box">
        <h4>🔍 ¿Cómo se calculó el ahorro/sobrecosto?</h4>
        <ul>
            <li><b>Suma de Flujos:</b> El monto total es la suma de las {plazo_p*12} cuotas proyectadas. El ahorro de <b>S/ {abs(ahorro):,.0f}</b> representa dinero que se queda en tu bolsillo al finalizar el préstamo.</li>
            <li><b>Trampa de la Tasa Nominal:</b> Nota que aunque un banco tenga menor TEA, si su seguro de desgravamen es más alto, el costo final sube. La <b>TCEA</b> es tu único indicador real de comparación.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with n_col2:
        st.markdown("""
        <div class="nota-box">
        <h4>🚩 Puntos Críticos a Considerar</h4>
        <ul>
            <li><b>Seguro de Desgravamen Mancomunado:</b> Si compras con pareja, la tasa de desgravamen suele duplicarse. Asegúrate de que el banco esté aplicando la tasa correcta en su oferta oficial.</li>
            <li><b>Endoso de Seguros:</b> Si cuentas con un seguro de vida externo, podrías <b>endosarlo</b> al banco para eliminar el costo del seguro de desgravamen mensual, bajando tu TCEA drásticamente.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
