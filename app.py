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

# Ajout des widgets pour le choix du domaine, du pays, de la langue, du dispositif et de l'appareil
domains = ["google.com", "google.de", "google.es", "google.fr", "google.it"]
selected_domain = st.sidebar.selectbox("Domaine de Google", sorted(domains), index=3)

countries = {
    "USA": "us",
    "Espagne": "es",
    "Allemagne": "de",
    "Angleterre": "uk",
    "France": "fr",
    "Italie": "it"
}
selected_country = st.sidebar.selectbox("Pays (gl)", sorted(countries.keys()), index=4)
gl_value = countries[selected_country]

languages = {
    "Anglais": "en",
    "Français": "fr",
    "Italien": "it",
    "Allemand": "de"
}
selected_language = st.sidebar.selectbox("Langue (hl)", sorted(languages.keys()), index=1)
hl_value = languages[selected_language]

devices = ["mobile", "desktop", "tablet"]
selected_device = st.sidebar.selectbox("Appareil", devices, index=0)

# Ajout d'un widget pour choisir le pourcentage de similarité
similarity_threshold = st.sidebar.slider("Pourcentage de similarité", min_value=0.0, max_value=1.0, value=0.4, step=0.05)
st.sidebar.text(f"Seuil de similarité choisi: {similarity_threshold*100}%")

# Ajout d'un widget pour choisir le nombre de résultats
num_results_options = [3, 5, 10, 15, 20]
num_results = st.sidebar.selectbox("Nombre de résultats à considérer", num_results_options)
st.sidebar.text(f"Nombre de résultats choisis: {num_results}")

# Fonction pour récupérer les URLs
def fetch_urls(keyword):
    global key_index
    MAX_RETRIES = 3
    
    for _ in range(MAX_RETRIES):
        api_key = API_KEYS[key_index]
        url = f"https://api.spaceserp.com/google/search?apiKey={api_key}&q={keyword}&domain={selected_domain}&gl={gl_value}&hl={hl_value}&device={selected_device}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if 'organic_results' in data:
                    urls = [entry.get('link', '') for entry in data['organic_results'] if 'link' in entry][:num_results]
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
            similarity = len(common_urls) / float(num_results)
            if similarity >= similarity_threshold:
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

        # Preparing CSV structure
        csv_data = {
            "keyword": [],
            "volume": [],
            "cluster": []
        }
        
        keywords_in_clusters = set()
        for main_keyword, similar_keywords in clusters.items():
            for keyword in [main_keyword] + similar_keywords:
                keywords_in_clusters.add(keyword)
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
        st.download_button("Télécharger le CSV avec les clusters", csv_download, "clusters_keywords.csv")
    else:
        st.error("❌ Le fichier CSV doit avoir une colonne 'keyword'")
