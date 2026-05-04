# CoComin Diagnose-Assistent

MVP eines textbasierten Diagnose-Assistenten zur Bewertung der Umsetzungsstärke von Organisationen.

## Ziel

Der Assistent führt Nutzer durch eine strukturierte Diagnose entlang von drei Bereichen:

- Strategische Klarheit  
- Fokus und Priorisierung  
- Entscheidungsfähigkeit  

Dabei wird kein klassischer Fragebogen verwendet, sondern ein geführter Dialog, der auf Antworten reagiert.

## Funktionsweise

- Chat-basierte Nutzerführung (Streamlit)
- Zustandsbasierter Dialogfluss
- Bewertung der Mission (Cluster 1) mithilfe von KI
- Regelbasierte Logik für Fokus und Entscheidungen
- Optional: Spracheingabe

## Setup

```bash
pip install -r requirements.txt
streamlit run cocomin_diagnose_assistant_mvp.py
