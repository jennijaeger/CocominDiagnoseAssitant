import os
import json
import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="CoComin Diagnose-Assistent",
    layout="centered",
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

INTRO = """
Dieser Diagnose-Assistent gibt Ihnen eine strukturierte Einschätzung, 
wie wirksam Ihre Organisation Strategie in Umsetzung übersetzt.

Wir betrachten drei zentrale Hebel:

- Strategische Klarheit
- Fokus und Priorisierung
- Entscheidungsfähigkeit

Ich führe Sie Schritt für Schritt durch.
"""

MISSION_QUESTION = (
    "Wenn Sie die strategische Stoßrichtung oder Mission Ihres Unternehmens, Ihrer Abteilung "
    "oder Ihres Teams für die nächsten 12 Monate in einem Satz formulieren: Wie würde dieser Satz lauten?"
)

CLUSTER_1_SCORE_QUESTION = (
    "Wie klar ist Ihre strategische Richtung aktuell formuliert – und wie stark gibt sie im Alltag "
    "tatsächlich Orientierung für Entscheidungen? Bitte bewerten Sie von 1 bis 5."
)

CLUSTER_2_INTRO = (
    "Viele Organisationen verlieren Wirkung nicht durch falsche Ziele, "
    "sondern dadurch, dass zu viele Dinge gleichzeitig verfolgt werden."
)

CLUSTER_2_QUESTION = (
    "Wenn Sie auf Ihre aktuellen Initiativen schauen: Arbeiten Sie auf wenige klare Prioritäten hin – "
    "oder eher parallel an mehreren Themen?"
)

CLUSTER_2_DEEPENING_QUESTION = (
    "Wenn Sie auf die letzten Monate schauen: Wie viele neue Initiativen sind dazugekommen – "
    "und in welchem Umfang wurden gleichzeitig Themen bewusst beendet?"
)

CLUSTER_2_SCORE_QUESTION = (
    "Wie konsequent gelingt es Ihnen aktuell, Fokus herzustellen – also Prioritäten zu setzen "
    "und gleichzeitig bewusst auf anderes zu verzichten? Bitte bewerten Sie von 1 bis 5."
)

CLUSTER_3_INTRO = (
    "Wenn Richtung und Fokus stehen, wird entscheidend, "
    "wie schnell und konsequent Entscheidungen getroffen und umgesetzt werden."
)

CLUSTER_3_QUESTION = (
    "Werden wichtige Entscheidungen bei Ihnen eher zügig getroffen – "
    "oder eher weiter analysiert, mehrfach abgestimmt oder hinausgeschoben?"
)

CLUSTER_3_SCORE_QUESTION = (
    "Wie wirksam ist Ihre Organisation darin, rechtzeitig zu entscheiden "
    "und Entscheidungen anschließend konsequent umzusetzen? Bitte bewerten Sie von 1 bis 5."
)

MISSION_PROMPT = """
Du bist ein professioneller Diagnose-Assistent für Führungskräfte.

Bewerte die formulierte strategische Stoßrichtung / Mission anhand dieser Kriterien:
- Klarheit
- konkreter Kundennutzen
- wirtschaftliche Tragfähigkeit
- Operationalisierbarkeit
- Orientierung für Entscheidungen im Alltag
- keine reine Ziel- oder Marketingfloskel

Wichtig:
- Antworte wertschätzend, aber klar.
- Keine lange Analyse.
- Keine Aufzählung der Kriterien.
- Stelle genau eine passende Vertiefungsfrage.
- Schreibe auf Deutsch.
- Gib ausschließlich valides JSON zurück.

Format:
{
  "feedback": "...",
  "question": "..."
}
"""


def init_state():
    defaults = {
        "messages": [],
        "step": "intro",
        "mission": None,
        "cluster_1_score": None,
        "cluster_2_score": None,
        "cluster_3_score": None,
        "last_audio_id": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def add_message(role, text):
    st.session_state.messages.append({"role": role, "text": text})


def render_messages():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["text"])


def fallback_evaluate_mission(text):
    text_lower = text.lower()

    if "marktführer" in text_lower or len(text.split()) < 6:
        return (
            "Die Aussage ist nachvollziehbar, bleibt aber noch sehr allgemein und bietet wenig Orientierung für konkrete Entscheidungen im Alltag.",
            "Woran würden Sie konkret erkennen, dass diese Richtung erreicht ist?",
        )

    return (
        "Die Richtung ist erkennbar, könnte aber noch stärker konkretisiert werden.",
        "Welche konkrete Entscheidung würde sich durch diese Mission im Alltag verändern?",
    )


def evaluate_mission(text):
    if not OPENAI_API_KEY:
        return fallback_evaluate_mission(text)

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": MISSION_PROMPT},
                {"role": "user", "content": f"Mission: {text}"},
            ],
            temperature=0.3,
        )

        result = json.loads(response.choices[0].message.content)
        return result["feedback"], result["question"]

    except Exception:
        return fallback_evaluate_mission(text)


def transcribe_audio(audio_file):
    if not OPENAI_API_KEY:
        return None

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="de",
        )

        return transcript.text

    except Exception:
        return None


def parse_score(text):
    try:
        score = int(text.strip())
        if 1 <= score <= 5:
            return score
    except ValueError:
        return None
    return None


def sounds_unfocused(text):
    indicators = ["viele", "parallel", "gleichzeitig", "zu viel", "alles", "ständig"]
    return any(word in text.lower() for word in indicators)


def sounds_slow(text):
    indicators = ["langsam", "verzögert", "abgestimmt", "analysiert", "hinausgeschoben", "diskutiert"]
    return any(word in text.lower() for word in indicators)


def final_summary():
    c1 = st.session_state.cluster_1_score
    c2 = st.session_state.cluster_2_score
    c3 = st.session_state.cluster_3_score
    avg = round((c1 + c2 + c3) / 3, 1)

    scores = {
        "Strategische Klarheit": c1,
        "Fokus und Priorisierung": c2,
        "Entscheidungen": c3,
    }

    weakest_area = min(scores, key=scores.get)

    return f"""
### Gesamtdiagnose

**Strategische Klarheit:** {c1}/5  
**Fokus und Priorisierung:** {c2}/5  
**Entscheidungen:** {c3}/5  
**Durchschnitt:** {avg}/5  

---

**Einordnung**

Der aktuell kritischste Hebel liegt im Bereich: **{weakest_area}**.

Die Umsetzungsstärke Ihrer Organisation hängt vor allem davon ab, ob strategische Richtung, klare Prioritäten und konsequente Entscheidungen im Alltag zusammenwirken.

**Nächster sinnvoller Schritt**

Prüfen Sie, welche konkrete Entscheidung oder Priorität in den nächsten zwei Wochen sichtbar anders gehandhabt werden müsste, damit Umsetzungskraft entsteht.
"""


def start():
    add_message("assistant", INTRO)
    add_message("assistant", "**Cluster 1 – Strategische Klarheit**")
    add_message("assistant", MISSION_QUESTION)
    st.session_state.step = "mission"


def handle(user_input):
    add_message("user", user_input)

    step = st.session_state.step

    if step == "mission":
        st.session_state.mission = user_input
        feedback, question = evaluate_mission(user_input)

        add_message("assistant", feedback)
        add_message("assistant", question)
        st.session_state.step = "mission_deepening"

    elif step == "mission_deepening":
        add_message(
            "assistant",
            "Danke. Das macht deutlicher, ob die Richtung im Alltag tatsächlich entscheidungsleitend ist.",
        )
        add_message("assistant", CLUSTER_1_SCORE_QUESTION)
        st.session_state.step = "cluster_1_score"

    elif step == "cluster_1_score":
        score = parse_score(user_input)

        if score is None:
            add_message("assistant", "Bitte geben Sie eine Zahl zwischen 1 und 5 ein.")
            return

        st.session_state.cluster_1_score = score

        add_message("assistant", f"**Zwischenfazit – Strategische Klarheit**\n\nIhre Bewertung: **{score}/5**")
        add_message("assistant", "**Cluster 2 – Fokus und Priorisierung**")
        add_message("assistant", CLUSTER_2_INTRO)
        add_message("assistant", CLUSTER_2_QUESTION)

        st.session_state.step = "cluster_2_answer"

    elif step == "cluster_2_answer":
        if sounds_unfocused(user_input):
            add_message(
                "assistant",
                "Das klingt danach, dass mehrere Themen parallel Aufmerksamkeit binden. Genau hier entsteht häufig Umsetzungsverlust.",
            )
        else:
            add_message(
                "assistant",
                "Das klingt nach vorhandener Priorisierung. Entscheidend ist, ob diese Prioritäten auch gegen neue Themen geschützt werden.",
            )

        add_message("assistant", CLUSTER_2_DEEPENING_QUESTION)
        st.session_state.step = "cluster_2_deepening"

    elif step == "cluster_2_deepening":
        add_message(
            "assistant",
            "Danke. Das zeigt, ob Fokus nur formuliert ist oder ob tatsächlich bewusst entschieden wird, was nicht mehr verfolgt wird.",
        )
        add_message("assistant", CLUSTER_2_SCORE_QUESTION)
        st.session_state.step = "cluster_2_score"

    elif step == "cluster_2_score":
        score = parse_score(user_input)

        if score is None:
            add_message("assistant", "Bitte geben Sie eine Zahl zwischen 1 und 5 ein.")
            return

        st.session_state.cluster_2_score = score

        add_message("assistant", f"**Zwischenfazit – Fokus und Priorisierung**\n\nIhre Bewertung: **{score}/5**")
        add_message("assistant", "**Cluster 3 – Entscheidungen**")
        add_message("assistant", CLUSTER_3_INTRO)
        add_message("assistant", CLUSTER_3_QUESTION)

        st.session_state.step = "cluster_3_answer"

    elif step == "cluster_3_answer":
        if sounds_slow(user_input):
            add_message(
                "assistant",
                "Das deutet darauf hin, dass Entscheidungen möglicherweise zu lange im System bleiben und dadurch Geschwindigkeit verloren geht.",
            )
        else:
            add_message(
                "assistant",
                "Das klingt nach grundsätzlich funktionierenden Entscheidungsprozessen. Entscheidend ist, ob Entscheidungen anschließend konsequent umgesetzt werden.",
            )

        add_message("assistant", CLUSTER_3_SCORE_QUESTION)
        st.session_state.step = "cluster_3_score"

    elif step == "cluster_3_score":
        score = parse_score(user_input)

        if score is None:
            add_message("assistant", "Bitte geben Sie eine Zahl zwischen 1 und 5 ein.")
            return

        st.session_state.cluster_3_score = score

        add_message("assistant", f"**Zwischenfazit – Entscheidungen**\n\nIhre Bewertung: **{score}/5**")
        add_message("assistant", final_summary())

        st.session_state.step = "done"

    elif step == "done":
        add_message("assistant", "Die Diagnose ist abgeschlossen. Sie können über „Neu starten“ einen neuen Durchlauf beginnen.")


init_state()

st.title("CoComin Diagnose-Assistent")
st.caption("MVP – Strategische Klarheit, Fokus und Entscheidungen")

with st.sidebar:
    st.header("Status")
    st.write(f"Aktueller Schritt: `{st.session_state.step}`")

    if st.button("Neu starten"):
        st.session_state.clear()
        st.rerun()

if st.session_state.step == "intro" and not st.session_state.messages:
    start()

render_messages()

if prompt := st.chat_input("Ihre Antwort ..."):
    handle(prompt)
    st.rerun()

audio = st.audio_input("Antwort per Sprache aufnehmen")

if audio is not None:
    audio_id = f"{audio.name}-{audio.size}"

    if st.session_state.last_audio_id != audio_id:
        st.session_state.last_audio_id = audio_id

        transcript = transcribe_audio(audio)

        if transcript:
            st.info(f"Erkannter Text: {transcript}")
            handle(transcript)
            st.rerun()
        else:
            st.warning("Audio konnte nicht transkribiert werden. Bitte nutzen Sie die Texteingabe.")