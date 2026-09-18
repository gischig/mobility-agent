import streamlit as st
from google import genai
from google.genai import types
import uuid
from datetime import datetime
import requests

# 1. API-Schlüssel (Hier wieder deinen Schlüssel einfügen!)
API_KEY = st.secrets["GEMINI_API_KEY"]

# 2. System-Prompt (unser bewährter Text)
system_anweisung = """
Deine Rolle:
Du bist ein empathischer, professioneller und zielorientierter Verhaltenscoach für Mobilität. Du führst ein Gespräch mit einer arbeitenden oder studierenden Person (Alter 20-65). Dein Ziel ist es, die Person dazu zu bringen, ihr aktuelles Mobilitätsverhalten zu reflektieren und sich am Ende des Gesprächs auf eine konkrete, nachhaltigere Verhaltensänderung für die kommenden Wochen festzulegen.

Deine Grundregeln:
* Eine Frage pro Antwort: Stelle immer nur eine präzise Frage am Ende deiner Nachricht.
* Wertfrei bleiben: Verurteile niemals das Fahren mit dem Auto.
* Kurz und gesprächig: Antworte natürlich und auf Augenhöhe. Formuliere prägnant.

Gesprächsphasen:
1. Die Ist-Analyse: Finde heraus, wie die Person zur Arbeit/Uni kommt (Distanz, Gründe).
2. Werte und Barrieren: Finde heraus, was der Person wichtig ist (Stress, Zeit, Geld, Umwelt).
3. Der Pivot: Schlage 1-2 sehr konkrete, auf die Person zugeschnittene Alternativen vor.
4. Das Commitment: Lass den Nutzer nicht mit einem vagen "Ich versuche es mal" entkommen. Dränge auf einen konkreten Wenn-Dann-Plan (Wann, Wo, Wie).
5. Verabschiedung: Lobe den Entschluss und beende das Gespräch positiv.
"""

# 3. Streamlit Seiten-Konfiguration (Titel der Webseite)
st.set_page_config(page_title="Mobilitäts-Coach", page_icon="🚲")
st.title("🌱 Dein persönlicher Mobilitäts-Coach")
st.write("Willkommen zum Experiment! Lass uns über deine täglichen Wege sprechen.")

# # 4. Das "Gedächtnis" der App einrichten (Session State)
if "chat_session" not in st.session_state:
    # WICHTIG: Wir speichern jetzt auch den Client im Gedächtnis (st.session_state.client)
    st.session_state.client = genai.Client(api_key=API_KEY)
    
    st.session_state.chat_session = st.session_state.client.chats.create(
        model="gemini-3.6-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_anweisung,
        )
    )
    # Startnachricht in den Verlauf legen
    st.session_state.messages = [
        {"role": "assistant", "content": "Hallo! Lass uns kurz über deinen alltäglichen Weg zur Arbeit oder zur Uni sprechen. Wie bist du da meistens unterwegs?"}
    ]

# 5. Bisherigen Chatverlauf auf dem Bildschirm anzeigen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. Eingabefeld für den Nutzer
if user_input := st.chat_input("Schreibe hier deine Antwort..."):
    
    # Nutzer-Nachricht anzeigen und speichern
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Lade-Animation ("Coach tippt...")
    with st.chat_message("assistant"):
        with st.spinner("Coach überlegt..."):
            # Antwort von Gemini holen
            response = st.session_state.chat_session.send_message(user_input)
            st.markdown(response.text)
            
    # Antwort des Coaches speichern
    st.session_state.messages.append({"role": "assistant", "content": response.text})
# 7. NEU: Daten an Google senden ---
st.write("---")
st.write("Bist du am Ende des Gesprächs angekommen?")

# Wenn der Button geklickt wird:
if st.button("🏁 Gespräch beenden & Daten speichern"):
    
    # 1. Erzeuge ID und Uhrzeit
    probanden_id = str(uuid.uuid4())[:8]
    zeitstempel = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    
    # 2. Sammle den Chat-Text
    chat_protokoll = ""
    for message in st.session_state.messages:
        sprecher = "Coach" if message["role"] == "assistant" else "Proband"
        chat_protokoll += f"{sprecher}: {message['content']}\n\n"
        
    # 3. Daten heimlich an Google Forms senden
    url = "https://docs.google.com/forms/d/e/1FAIpQLSe5-C410ty1tl2HHZwgKo0EdpomfC0rzmQE827pMsCSOx7NfA/formResponse"
    form_data = {
        "entry.1637973582": probanden_id,
        "entry.1151736903": zeitstempel,
        "entry.1769684280": chat_protokoll
    }
    
    try:
        requests.post(url, data=form_data)
        st.success(f"Vielen Dank für deine Teilnahme! Deine Daten wurden anonymisiert und sicher gespeichert (Deine ID: {probanden_id}). Du kannst das Fenster nun schließen.")
    except Exception as e:
        st.error("Es gab ein Problem bei der Datenübertragung. Bitte überprüfe deine Internetverbindung.")
