import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Gestione Listini", layout="centered")
st.title("📋 Gestione Listini")


def calcola_prezzo_scontato(prezzo, s1, s2, s3):
    try:
        prezzo = float(prezzo)
        return round(prezzo * (1 - s1 / 100) * (1 - s2 / 100) * (1 - s3 / 100), 2)
    except Exception as e:
        return 0.0


def to_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()


def mostra_tabella(nome_tab, df):
    st.subheader(f"📄 {nome_tab}")

    if "sconti_generali" not in st.session_state:
        st.session_state.sconti_generali = {}
    if nome_tab not in st.session_state.sconti_generali:
        st.session_state.sconti_generali[nome_tab] = {"Sconto1": 0, "Sconto2": 0, "Sconto3": 0}

    sconti = st.session_state.sconti_generali[nome_tab]
    col1, col2, col3 = st.columns(3)
    with col1:
        s1 = st.number_input("Sconto Generale 1 (%)", value=sconti["Sconto1"], key=f"sg1_{nome_tab}")
    with col2:
        s2 = st.number_input("Sconto Generale 2 (%)", value=sconti["Sconto2"], key=f"sg2_{nome_tab}")
    with col3:
        s3 = st.number_input("Sconto Generale 3 (%)", value=sconti["Sconto3"], key=f"sg3_{nome_tab}")

    st.session_state.sconti_generali[nome_tab] = {"Sconto1": s1, "Sconto2": s2, "Sconto3": s3}

    filtro_prodotto = st.selectbox(
        "🔍 Seleziona Prodotto",
        [""] + df["Prodotto"].dropna().astype(str).unique().tolist(),
        key=f"prod_{nome_tab}"
    )

    nuova_df = df.copy()

    nuova_df["Prezzo Scontato Mq Grezzo"] = nuova_df["Grezzo Mq"].apply(lambda x: calcola_prezzo_scontato(x, s1, s2, s3))
    nuova_df["Prezzo Scontato Mq Zincato"] = nuova_df["Zincato Mq"].apply(lambda x: calcola_prezzo_scontato(x, s1, s2, s3))

    if filtro_prodotto:
        prodotto_sel = nuova_df[nuova_df["Prodotto"] == filtro_prodotto]
        if not prodotto_sel.empty:
            idx = prodotto_sel.index[0]
            row = nuova_df.loc[idx]

            st.markdown("### ✏️ Dettaglio Prodotto")
            c1, c2, c3 = st.columns(3)
            with c1:
                ps1 = st.number_input("Sconto 1 (%)", value=float(row["Sconto1"]), key=f"sp1_{nome_tab}")
            with c2:
                ps2 = st.number_input("Sconto 2 (%)", value=float(row["Sconto2"]), key=f"sp2_{nome_tab}")
            with c3:
                ps3 = st.number_input("Sconto 3 (%)", value=float(row["Sconto3"]), key=f"sp3_{nome_tab}")

            ps_g = calcola_prezzo_scontato(row.get("Grezzo Mq", 0), ps1, ps2, ps3)
            ps_z = calcola_prezzo_scontato(row.get("Zincato Mq", 0), ps1, ps2, ps3)

            nuova_df.at[idx, "Sconto1"] = ps1
            nuova_df.at[idx, "Sconto2"] = ps2
            nuova_df.at[idx, "Sconto3"] = ps3
            nuova_df.at[idx, "Prezzo Scontato Mq Grezzo"] = ps_g
            nuova_df.at[idx, "Prezzo Scontato Mq Zincato"] = ps_z

            st.success(f"💰 Prezzo Scontato Grezzo: {ps_g:.2f} €/Mq")
            st.success(f"💰 Prezzo Scontato Zincato: {ps_z:.2f} €/Mq")

    st.dataframe(nuova_df, use_container_width=True)

    st.download_button("⬇️ Esporta in Excel", to_excel_bytes(nuova_df), file_name=f"{nome_tab}.xlsx")

    if st.button("➕ Aggiungi Nuovo Prodotto", key=f"add_{nome_tab}"):
        nuova_riga = {col: "" for col in df.columns}
        nuova_df = pd.concat([nuova_df, pd.DataFrame([nuova_riga])], ignore_index=True)
        st.session_state.dati[nome_tab] = nuova_df
        st.experimental_rerun()

    if st.button("💾 Salva File", key=f"save_{nome_tab}"):
        st.session_state.dati[nome_tab] = nuova_df
        st.success("✅ File aggiornato correttamente!")


uploaded = st.file_uploader("📄 Carica un file Excel con fogli separati", type=["xlsx"])
if uploaded:
    try:
        xls = pd.read_excel(uploaded, sheet_name=None)
        st.session_state.dati = xls
        tabs = st.tabs(list(xls.keys()))
        for i, nome_tab in enumerate(xls):
            with tabs[i]:
                mostra_tabella(nome_tab, st.session_state.dati[nome_tab])
    except Exception as e:
        st.error(f"❌ Errore caricamento file: {e}")
