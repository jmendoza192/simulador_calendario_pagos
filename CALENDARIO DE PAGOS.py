# --- 5. TAB 2: COMPARATIVA (ACTUALIZADA CON TARJETA DE RECOMENDACIÓN) ---
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

    ahorro = res1['df']["Cuota Total"].sum() - res2['df']["Cuota Total"].sum()
    
    st.write("---")
    
    # --- NUEVA TARJETA DE RECOMENDACIÓN INTELIGENTE ---
    mejor_banco = "BANCO A" if res1['tcea'] < res2['tcea'] else "BANCO B"
    color_rec = "#1e3a8a" if mejor_banco == "BANCO A" else "#10b981"
    
    st.markdown(f"""
        <div style="background-color: {color_rec}; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 25px; border: 2px solid #ffffff33;">
            <h2 style="color: white; margin: 0;">✅ RECOMENDACIÓN: {mejor_banco}</h2>
            <p style="color: #e0e0e0; font-size: 1.1rem; margin-top: 10px;">
                Tras auditar los costos financieros y seguros, el <b>{mejor_banco}</b> ofrece la TCEA más eficiente para tu perfil.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Métricas de Resumen
    cm1, cm2, cm3 = st.columns(3)
    cm1.markdown(f'<div class="tcea-card">TCEA BANCO A<br><b style="font-size:1.8rem;">{res1["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)
    cm2.markdown(f'<div class="tcea-card">TCEA BANCO B<br><b style="font-size:1.8rem;">{res2["tcea"]:.2f}%</b></div>', unsafe_allow_html=True)
    with cm3:
        color_ah = "#10b981" if ahorro > 0 else "#ef4444"
        st.markdown(f'<div class="ahorro-card" style="background:{color_ah}">{"AHORRO" if ahorro > 0 else "SOBRECOSTO"}<br><b style="font-size:1.8rem;">S/ {abs(ahorro):,.0f}</b></div>', unsafe_allow_html=True)

    # Gráfico de Barras
    st.write("")
    st.subheader("📊 Comparación de Costos Lado a Lado")
    
    comp_df = pd.DataFrame({
        "Concepto": ["Cuota Ord.", "Total Interés", "Total Seguros"],
        "Banco A": [int(res1['df'][res1['df']["Tipo"]=="ORDINARIA"]["Cuota Total"].iloc[0]), int(res1['df']["Interés"].sum()), int(res1['df']["Seguros"].sum())],
        "Banco B": [int(res2['df'][res2['df']["Tipo"]=="ORDINARIA"]["Cuota Total"].iloc[0]), int(res2['df']["Interés"].sum()), int(res2['df']["Seguros"].sum())]
    })
    
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(name='Banco A', x=comp_df["Concepto"], y=comp_df["Banco A"], marker_color='#1e3a8a'))
    fig_comp.add_trace(go.Bar(name='Banco B', x=comp_df["Concepto"], y=comp_df["Banco B"], marker_color='#10b981'))
    fig_comp.update_layout(barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"))
    fig_comp.update_yaxes(tickprefix="S/ ", tickformat=",.0f")
    st.plotly_chart(fig_comp, use_container_width=True)

    # Tabla Comparativa de Datos
    st.subheader("📋 Resumen Numérico")
    tabla_comp = comp_df.copy()
    tabla_comp["Banco A"] = tabla_comp["Banco A"].map("S/ {:,.0f}".format)
    tabla_comp["Banco B"] = tabla_comp["Banco B"].map("S/ {:,.0f}".format)
    st.table(tabla_comp)
