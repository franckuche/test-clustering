import streamlit as st
import pandas as pd
import requests
from urllib.parse import urlparse
import time

st.set_page_config(page_title="Clusters de similarité", layout="wide")

st.title("Clusters de similarité basés sur les URLs de recherche")
st.write("Cette application regroupe les mots-clés basés sur la similarité des URLs des résultats de recherche.")

API_KEYS = [
    "8e87e954-6b75-4888-bd6c-86868540beeb",  # Première clé
    "b0b85ece-cff0-4943-a341-ca654c6fa3ce"   # Deuxième clé
]
key_index = 0  # Utilisé pour suivre la clé actuellement utilisée

# Fonction pour récupérer les URLs
def fetch_urls(keyword):
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
                    return set(urls)
            else:
                # Si la clé API actuelle renvoie une erreur, passez à la clé suivante
                key_index = (key_index + 1) % len(API_KEYS)
                continue
        except requests.RequestException:
            continue
    
    return set()

# Fonction pour comparer les URLs et créer des clusters
def compare_keywords(df):
    clusters = []
    keywords = df['keyword'].tolist()
    
    for i in range(len(keywords)):
        for j in range(i+1, len(keywords)):
            common_urls = df.loc[i, 'urls'].intersection(df.loc[j, 'urls'])
            similarity = len(common_urls) / 20.0
            if similarity >= 0.4:
                clusters.append((keywords[i], keywords[j], similarity))
                
    return clusters

# Interface Streamlit
uploaded_file = st.file_uploader("📤 Choisissez un fichier CSV contenant vos mots-clés", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df = df.sort_values(by="volume", ascending=False)  # Tri par volume
    if 'keyword' in df.columns:
        st.subheader("Récupération des URLs en cours...")
        df['urls'] = df['keyword'].apply(fetch_urls)

        st.subheader("Création des clusters en cours...")
        clusters = compare_keywords(df)

        st.subheader("Clusters trouvés :")
        for cluster in clusters:
            # Trouver les mots-clés du cluster triés par volume
            keywords_cluster = df[df['keyword'].isin(cluster[:2])].sort_values(by="volume", ascending=False)
            st.table(keywords_cluster[["keyword", "volume"]])

        csv_download = df.to_csv(index=False).encode()
        st.download_button("Télécharger le CSV avec les liens", csv_download, "updated_keywords.csv")
    else:
        st.error("❌ Le fichier CSV doit avoir une colonne 'keyword'")
