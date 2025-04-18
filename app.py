import os
import streamlit as st
import whisper
from gtts import gTTS
from textblob import TextBlob

UPLOAD_FOLDER = "uploads"
FEEDBACK_AUDIO_FOLDER = "feedback_audio"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FEEDBACK_AUDIO_FOLDER, exist_ok=True)

model = whisper.load_model("base")

intent_keywords = {
    "refund": ["refund", "money back", "return"],
    "cancellation": ["cancel", "terminate", "end service"],
    "onboarding": ["start", "setup", "onboarding"],
    "support": ["help", "support", "issue", "problem", "trouble"],
    "billing": ["charge", "billing", "invoice", "payment"],
}

def evaluate_call(transcription):
    score = 0
    feedback = []
    transcription_lower = transcription.lower()
    found_intents = []

    greetings = ["hello", "good morning", "good afternoon", "good evening", "hi", "namaste"]
    if any(transcription_lower.startswith(greet) for greet in greetings):
        score += 20
        feedback.append("The call started with a proper greeting, which sets a positive tone.")
    else:
        feedback.append("The call did not start with a recognizable greeting. Consider starting with a professional greeting like 'Good morning' or 'Hello'.")

    for intent, keywords in intent_keywords.items():
        if any(keyword in transcription_lower for keyword in keywords):
            found_intents.append(intent)

    if found_intents:
        score += 20
        feedback.append(f"The intent of the customer was successfully identified as related to: {', '.join(found_intents)}.")
    else:
        feedback.append("The call did not clearly identify the customer's intent. Listening carefully and confirming their need would help.")

    positives = ["thank you", "sure", "absolutely", "happy to help", "zarur", "dhanyavaad"]
    if any(word in transcription_lower for word in positives):
        score += 20
        feedback.append("The use of positive and affirming language contributes to a better customer experience.")
    else:
        feedback.append("There was a lack of positive phrases. Using reassuring language helps build rapport.")

    if any(closing in transcription_lower for closing in ["thank you", "bye", "have a nice day", "shukriya", "alvida"]):
        score += 20
        feedback.append("The call ended with a proper closing, which leaves a good final impression.")
    else:
        feedback.append("A closing statement was missing. Always end calls with a polite and clear farewell.")

    try:
        sentiment = TextBlob(transcription).sentiment.polarity
        if sentiment > 0:
            score += 20
            feedback.append("Overall tone of the conversation was positive, which is appreciated in customer interactions.")
        elif sentiment < 0:
            feedback.append("The tone seemed negative at times. Try to stay calm and constructive even in tough conversations.")
        else:
            feedback.append("The tone was neutral. Consider adding more warmth and engagement.")
    except:
        feedback.append("Sentiment analysis could not be performed on this transcription.")

    return min(score, 100), "\n\n".join(feedback)

st.title("📞 Call Evaluation Tool")

uploaded_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a"])

if uploaded_file:
    temp_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)

    with open(temp_path, "wb") as f:
        f.write(uploaded_file.read())
    st.success("File uploaded successfully.")

    if st.button("Evaluate Call"):
        with st.spinner("Transcribing and analyzing..."):
            result = model.transcribe(temp_path)
            transcription = result["text"]
            score, feedback_text = evaluate_call(transcription)

            audio_filename = f"{uploaded_file.name}_feedback.mp3"
            audio_path = os.path.join(FEEDBACK_AUDIO_FOLDER, audio_filename)
            tts = gTTS(text=feedback_text, lang='en')
            tts.save(audio_path)

        st.subheader(f"Score: {score}/100")
        st.write(feedback_text)
        st.audio(audio_path)

