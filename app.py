import streamlit as st
import pandas as pd
from io import BytesIO
import os
from datetime import date

st.set_page_config(page_title="Listino Prezzi", layout="wide")
st.title("🧾 Listino Prezzi Web App")

def safe_float(val):
    try:
        return float(val)
    except:
        return None

# 📁 Cartella per salvare i file
SAVE_FOLDER = "listini_salvati"
os.makedirs(SAVE_FOLDER, exist_ok=True)

# ✅ Inizializza lo stato del dettaglio
if "dettaglio_aperto" not in st.session_state:
    st.session_state["dettaglio_aperto"] = None

# 📂 Caricamento file
uploaded_file = st.file_uploader("Carica nuovo file Excel", type=["xlsx", "xls"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    sheet = st.selectbox("Seleziona foglio", xls.sheet_names)
    df = xls.parse(sheet)

    # 💾 Salva il file con data
    today = date.today().isoformat()
    save_path = os.path.join(SAVE_FOLDER, f"listino_{today}.xlsx")
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"✅ File salvato come: {save_path}")

else:
    # 📁 Caricamento automatico dell’ultimo file salvato
    files = sorted(os.listdir(SAVE_FOLDER), reverse=True)
    if files:
        latest_file = os.path.join(SAVE_FOLDER, files[0])
        xls = pd.ExcelFile(latest_file)
        sheet = st.selectbox("Seleziona foglio", xls.sheet_names)
        df = xls.parse(sheet)
        st.info(f"📄 File aperto automaticamente: {latest_file}")
    else:
        st.warning("⚠️ Nessun file salvato trovato.")
        df = None

if df is not None:
    for col in ["Prodotto", "Maglia", "Piatto"]:
        if col in df.columns:
            df[col] = df[col].astype(str).fillna("")

    st.markdown("### 🔍 Ricerca e Filtri")

    col1, col2, col3 = st.columns(3)
    with col1:
        prodotto = st.text_input("Cerca prodotto")
    with col2:
        maglia = st.selectbox("Filtra Maglia", [""] + sorted(df["Maglia"].dropna().unique()) if "Maglia" in df.columns else [""])
    with col3:
        piatto = st.selectbox("Filtra Piatto", [""] + sorted(df["Piatto"].dropna().unique()) if "Piatto" in df.columns else [""])

    df_filtrato = df.copy()

    if prodotto:
        df_filtrato = df_filtrato[df_filtrato["Prodotto"].str.contains(prodotto, case=False, na=False)]
    if maglia:
        df_filtrato = df_filtrato[df_filtrato["Maglia"] == maglia]
    if piatto:
        df_filtrato = df_filtrato[df_filtrato["Piatto"] == piatto]

    st.markdown("### 🧮 Sconti globali")

    s1, s2, s3 = st.columns(3)
    with s1:
        sconto1 = st.number_input("Sconto1 (%)", value=0.0)
    with s2:
        sconto2 = st.number_input("Sconto2 (%)", value=0.0)
    with s3:
        sconto3 = st.number_input("Sconto3 (%)", value=0.0)

    sconto_totale = sconto1 + sconto2 + sconto3

    if "Grezzo Mq" in df_filtrato.columns:
        df_filtrato["Prezzo Scontato Mq Grezzo"] = df_filtrato["Grezzo Mq"].apply(
            lambda x: round(safe_float(x) * (1 - sconto_totale / 100), 2) if safe_float(x) is not None else x
        )

    if "Zincato Mq" in df_filtrato.columns:
        df_filtrato["Prezzo Scontato Mq Zincato"] = df_filtrato["Zincato Mq"].apply(
            lambda x: round(safe_float(x) * (1 - sconto_totale / 100), 2) if safe_float(x) is not None else x
        )

    st.markdown("### 📋 Prodotti (prime 50 righe)")
    for i, row in df_filtrato.head(50).iterrows():
        cols = st.columns([7, 1])
        with cols[0]:
            st.write(f"**{row['Prodotto']}** | Maglia: {row.get('Maglia', '')} | Piatto: {row.get('Piatto', '')} | Dim: {row.get('Dimensione', '')} | GR: {row.get('Kg/Mq GR.', '')} | ZN: {row.get('Kg/Mq ZN.', '')} | Grezzo: {row.get('Grezzo Mq', '')} | Zincato: {row.get('Zincato Mq', '')}")
        with cols[1]:
            if st.button("🔍 Dettaglio", key=f"modifica_{i}"):
                if st.session_state["dettaglio_aperto"] == i:
                    st.session_state["dettaglio_aperto"] = None
                else:
                    st.session_state["dettaglio_aperto"] = i

        if st.session_state["dettaglio_aperto"] == i:
            st.markdown(f"#### 📄 Dettaglio: {row['Prodotto']}")

            st.write(f"**Maglia:** {row.get('Maglia', '')}")
            st.write(f"**Piatto:** {row.get('Piatto', '')}")
            st.write(f"**Dimensione:** {row.get('Dimensione', '')}")
            st.write(f"**Kg/Mq GR.:** {row.get('Kg/Mq GR.', '')}")
            st.write(f"**Kg/Mq ZN.:** {row.get('Kg/Mq ZN.', '')}")
            st.write(f"**Grezzo Mq:** {row.get('Grezzo Mq', '')}")
            st.write(f"**Zincato Mq:** {row.get('Zincato Mq', '')}")
            

            col1, col2, col3 = st.columns(3)
            with col1:
                s1_val = st.number_input("Sconto1 (prodotto)", value=safe_float(row.get("Sconto1", 0)), key=f"s1_{i}")
            with col2:
                s2_val = st.number_input("Sconto2 (prodotto)", value=safe_float(row.get("Sconto2", 0)), key=f"s2_{i}")
            with col3:
                s3_val = st.number_input("Sconto3 (prodotto)", value=safe_float(row.get("Sconto3", 0)), key=f"s3_{i}")

            sconto_riga = s1_val + s2_val + s3_val

            grezzo_val = safe_float(row.get("Grezzo Mq", 0))
            zincato_val = safe_float(row.get("Zincato Mq", 0))

            prezzo_grezzo = round(grezzo_val * (1 - sconto_riga / 100), 2) if grezzo_val is not None else "-"
            prezzo_zincato = round(zincato_val * (1 - sconto_riga / 100), 2) if zincato_val is not None else "-"

            st.success(f"💰 Prezzo Scontato Mq Grezzo: **{prezzo_grezzo}**")
            st.success(f"💰 Prezzo Scontato Mq Zincato: **{prezzo_zincato}**")

    st.markdown("### 💾 Esporta file aggiornato")
    buffer = BytesIO()
    df_filtrato.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)

    st.download_button(
        label="📥 Scarica Excel",
        data=buffer,
        file_name="listino_aggiornato.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
