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
                key_index = (key_index + 1) % len(API_KEYS)
                continue
        except requests.RequestException:
            continue
    
    return set()

# Fonction pour comparer les URLs et créer des clusters
def compare_keywords(df):
    clusters = {}
    keywords = df['keyword'].tolist()
    
    for i in range(len(keywords)):
        for j in range(i+1, len(keywords)):
            common_urls = df.loc[i, 'urls'].intersection(df.loc[j, 'urls'])
            similarity = len(common_urls) / 20.0
            if similarity >= 0.4:
                if keywords[i] not in clusters:
                    clusters[keywords[i]] = [keywords[j]]
                else:
                    clusters[keywords[i]].append(keywords[j])
                
    return clusters

# Interface Streamlit
uploaded_file = st.file_uploader("📤 Choisissez un fichier CSV contenant vos mots-clés", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    if 'volume' in df.columns:
        df = df.sort_values(by="volume", ascending=False)
    
    if 'keyword' in df.columns:
        st.subheader("Récupération des URLs en cours...")
        df['urls'] = df['keyword'].apply(fetch_urls)

        st.subheader("Création des clusters en cours...")
        clusters = compare_keywords(df)

        st.subheader("Clusters trouvés :")
        
        keywords_in_clusters = set()

        for main_keyword, similar_keywords in clusters.items():
            cluster_keywords = [main_keyword] + similar_keywords
            keywords_cluster = df[df['keyword'].isin(cluster_keywords)].sort_values(by="volume", ascending=False).reset_index(drop=True)
            
            data = {
                "Type de mot-clé": ["Mot-clé principal"] + ["Mot-clé secondaire"] * (len(keywords_cluster) - 1),
                "Mot-clé": keywords_cluster["keyword"].tolist(),
                "Volume": keywords_cluster["volume"].tolist()
            }
            
            cluster_df = pd.DataFrame(data)
            st.table(cluster_df)

            keywords_in_clusters.update(cluster_keywords)

        # Preparing CSV structure
        csv_data = {
            "keyword": [],
            "volume": [],
            "cluster": []
        }
        
        for main_keyword, similar_keywords in clusters.items():
            for keyword in [main_keyword] + similar_keywords:
                csv_data["keyword"].append(keyword)
                csv_data["volume"].append(df[df["keyword"] == keyword]["volume"].values[0])
                csv_data["cluster"].append(main_keyword)

        # Adding keywords not in clusters
        for keyword in set(df["keyword"]) - keywords_in_clusters:
            csv_data["keyword"].append(keyword)
            csv_data["volume"].append(df[df["keyword"] == keyword]["volume"].values[0])
            csv_data["cluster"].append("keyword unique")

        csv_df = pd.DataFrame(csv_data)
        csv_download = csv_df.to_csv(index=False).encode()
        st.download_button("Télécharger le CSV avec les clusters", csv_download, "updated_keywords.csv")
    else:
        st.error("❌ Le fichier CSV doit avoir une colonne 'keyword'")