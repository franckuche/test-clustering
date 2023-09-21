import streamlit as st
import pandas as pd
import requests
from urllib.parse import urlparse
import time

st.set_page_config(page_title="Extracteur de Liens", layout="wide")

st.title("Extracteur de liens à partir des résultats de recherche")
st.write("Cette application permet d'extraire les liens des 20 premiers résultats de recherche de Google pour chaque mot-clé fourni.")

API_KEYS = [
    "8e87e954-6b75-4888-bd6c-86868540beeb",  # Votre première clé
    "b0b85ece-cff0-4943-a341-ca654c6fa3ce"   # Votre deuxième clé (remplacez par la valeur réelle)
]
key_index = 0  # Utilisé pour suivre la clé actuellement utilisée

def fetch_links(keyword):
    global key_index
    MAX_RETRIES = 3
    
    for _ in range(MAX_RETRIES):
        # Sélectionnez la clé API à utiliser
        api_key = API_KEYS[key_index]
        
        url = f"https://api.spaceserp.com/google/search?apiKey={api_key}&q={keyword}&domain=google.fr&gl=cn&hl=nl&device=mobile"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if 'organic_results' in data:
                    urls = [entry.get('link', '') for entry in data['organic_results'] if 'link' in entry][:20]
                    if urls:
                        return ", ".join(urls)
                else:
                    return "Pas de résultats"
            else:
                # Si la clé API actuelle renvoie une erreur, passez à la clé suivante
                key_index = (key_index + 1) % len(API_KEYS)
                time.sleep(2)
                continue
        except requests.RequestException:
            time.sleep(2)
            continue
            
    return "Pas de résultats"

uploaded_file = st.file_uploader("📤 Choisissez un fichier CSV contenant vos mots-clés", type="csv")

if uploaded_file is not None:
    st.subheader("Aperçu du fichier CSV téléchargé")
    df = pd.read_csv(uploaded_file)
    st.write(df.head())

    if 'keyword' in df.columns:
        st.subheader("Extraction en cours...")
        df['cluster'] = df['keyword'].apply(fetch_links)

        st.subheader("Résultats avec les liens extraits")
        st.write(df)
        
        csv_download = df.to_csv(index=False).encode()
        st.download_button("Télécharger le CSV avec les liens", csv_download, "updated_keywords.csv")
    else:
        st.error("❌ Le fichier CSV doit avoir une colonne 'keyword'")