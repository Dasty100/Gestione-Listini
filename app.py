import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Gestione Listini", layout="centered")
st.title("📋 Gestione Listini")

def calcola_prezzo_scontato(prezzo, s1, s2, s3):
    try:
        prezzo = float(prezzo)
        return round(prezzo * (1 - s1 / 100) * (1 - s2 / 100) * (1 - s3 / 100), 2)
    except Exception:
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

    ricerca = st.text_input("🔍 Cerca prodotto o maglia", key=f"search_{nome_tab}")

    nuova_df = df.copy()
    nuova_df["Prezzo Scontato Mq Grezzo"] = nuova_df["Grezzo Mq"].apply(lambda x: calcola_prezzo_scontato(x, s1, s2, s3))
    nuova_df["Prezzo Scontato Mq Zincato"] = nuova_df["Zincato Mq"].apply(lambda x: calcola_prezzo_scontato(x, s1, s2, s3))

    if ricerca:
        nuova_df = nuova_df[nuova_df.apply(lambda row: ricerca.lower() in str(row["Prodotto"]).lower() or ricerca.lower() in str(row["Maglia"]).lower(), axis=1)]

    for idx, row in nuova_df.iterrows():
        with st.expander(f'📌 {row["Prodotto"]} - {row["Maglia"]}'):
            col1, col2, col3 = st.columns(3)
            with col1:
                s1p = st.number_input("Sconto 1 (%)", value=float(row["Sconto1"]), key=f"s1_{idx}")
            with col2:
                s2p = st.number_input("Sconto 2 (%)", value=float(row["Sconto2"]), key=f"s2_{idx}")
            with col3:
                s3p = st.number_input("Sconto 3 (%)", value=float(row["Sconto3"]), key=f"s3_{idx}")

            nuova_df.at[idx, "Sconto1"] = s1p
            nuova_df.at[idx, "Sconto2"] = s2p
            nuova_df.at[idx, "Sconto3"] = s3p

            nuova_df.at[idx, "Prezzo Scontato Mq Grezzo"] = calcola_prezzo_scontato(row["Grezzo Mq"], s1p, s2p, s3p)
            nuova_df.at[idx, "Prezzo Scontato Mq Zincato"] = calcola_prezzo_scontato(row["Zincato Mq"], s1p, s2p, s3p)

            st.success(f'💰 Prezzo Grezzo: {nuova_df.at[idx, "Prezzo Scontato Mq Grezzo"]} €/Mq')
            st.success(f'💰 Prezzo Zincato: {nuova_df.at[idx, "Prezzo Scontato Mq Zincato"]} €/Mq')

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
