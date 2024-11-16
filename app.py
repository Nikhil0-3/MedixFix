import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.downloader import download
from nltk.corpus import stopwords
import re
from nltk.stem import PorterStemmer
import streamlit as st
import sqlite3

# Download necessary NLTK data
download('stopwords')
download('punkt')

ps = PorterStemmer()
STOPWORDS = stopwords.words('english')
custom_stopwords = ["having", "feel", "symptoms", "experiencing", "feeling"]
STOPWORDS.extend(custom_stopwords)

# Load dataset
df = pd.read_csv('Medicine_Details.csv', usecols=['Medicine Name', 'Uses', 'Side_effects', 'Excellent Review %', 'Average Review %', 'Poor Review %', 'Image URL'])
df_dict = df.set_index('Medicine Name').T.to_dict('list')

# Database connection
conn = sqlite3.connect('data.db')

# Create the table if it doesn't exist
def create_table():
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users_symptom (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symptoms TEXT,
            recommendations TEXT
        )
    ''')
    conn.commit()

# Call create_table() when the app starts
create_table()

# Streamlit app layout with tabs
tab1, tab2, tab3 = st.tabs(["💊 Medicine Recommender", "☁️ Contact Us", "📊 Metrics"])

with tab1:
    col1, col2 = st.columns([1, 5])

    with col1:
        st.image('logo.png', width=100)

    with col2:
        st.markdown('<span style="font-size: 3.5em; font-weight: bold; vertical-align: middle;">MedixFix 🩺🏥</span>', unsafe_allow_html=True)
    st.header("Interactive Medicine Recommender 💊")
    st.subheader("Please consult your doctor for personalized medical advice.")

    text = st.text_area(
        label="Enter symptoms or diseases separated by commas",
        placeholder="e.g., headache, diabetes, fever",
        height=100
    )

def recommend_medicine(diseases_list):
    recommendations = {}
    for disease in diseases_list:
        disease = disease.lower().strip()
        disease = re.sub(r'[^\w\s]', ' ', disease)
        disease_tokens = [ps.stem(word) for word in word_tokenize(disease) if word not in STOPWORDS]

        medicine_matches = []
        for name, details in df_dict.items():
            uses = details[0].lower()
            uses_tokens = [ps.stem(word) for word in word_tokenize(uses) if word not in STOPWORDS]
            overlap = len(set(disease_tokens) & set(uses_tokens))

            # Ensure the medicine has acceptable review criteria
            excellent_review = float(details[2])  # Excellent Review %
            average_review = float(details[3])    # Average Review %
            poor_review = float(details[4])       # Poor Review %

            if poor_review > 20:  # Skip medicines with poor review > 10%
                continue

            if overlap > 0:  # Only consider medicines with some overlap
                medicine_matches.append({
                    'name': name,
                    'uses': details[0],
                    'side_effects': details[1],
                    'review': f"Excellent: {details[2]}%, Average: {details[3]}%, Poor: {details[4]}%",
                    'image_url': details[5],
                    'score': excellent_review + average_review  # Combined score for sorting
                })

        # Sort matches by combined score and take the top 3
        medicine_matches = sorted(medicine_matches, key=lambda x: x['score'], reverse=True)[:4]
        recommendations[disease] = medicine_matches

    return recommendations

if st.button("🔍 Find Medicines"):
    diseases_list = [d.strip() for d in text.split(',') if d.strip()]
    recommendations = recommend_medicine(diseases_list)

    if not recommendations:
        st.warning("⚠️ No medicines found for the symptoms entered.")
    else:
        st.success("💡 Recommended medicines based on your symptoms:")

        for symptom, medicines in recommendations.items():
            if not medicines:
                st.write(f"⚠️ No medicines found for **{symptom}**.")
                continue

            # Display the best medicine (top 1)
            best_medicine = medicines[0]
            st.write(f"### 💡 Best suggestion for **{symptom.capitalize()}**:")
            st.image(best_medicine['image_url'], width=100)
            st.write(f"**Name:** {best_medicine['name']}")
            st.write(f"**Uses:** {best_medicine['uses']}")
            st.write(f"**Side Effects:** {best_medicine['side_effects']}")
            st.write(f"**Reviews:** {best_medicine['review']}")
            
            # Create an expander for other 3 similar medicines
            with st.expander(f"Similar medicines for **{symptom.capitalize()}**"):
                for med in medicines[1:]:
                    st.image(med['image_url'], width=100)
                    st.write(f"**Name:** {med['name']}")
                    st.write(f"**Uses:** {med['uses']}")
                    st.write(f"**Side Effects:** {med['side_effects']}")
                    st.write(f"**Reviews:** {med['review']}")
                st.markdown("---")  # Divider for better UI

    # Database logging
    result = ", ".join([f"{symptom}: {', '.join([med['name'] for med in meds])}" for symptom, meds in recommendations.items()])
    
    def log_to_database():
        c = conn.cursor()
        c.execute("INSERT INTO users_symptom (symptoms, recommendations) VALUES (?, ?)", (text, result))
        conn.commit()

    log_to_database()

with tab2:
    st.subheader("Name :- Nikhil More")
    st.subheader("Email:- nikhil030304@gmail.com")
    st.image('image.png')

with tab3:
    st.header("User Metrics 📊")
    mdf = pd.read_sql_query('SELECT * FROM users_symptom', conn)
    st.dataframe(mdf)
