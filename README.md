# AURA Lite — Intelligent Agriculture Assistant

AURA Lite is an AI-powered agriculture assistant that helps farmers and agronomists 
with crop disease prediction, real-time weather insights, and natural language 
database queries — powered by Google Gemini AI and deployed on Google Cloud.

## Live Demo
https://aura-lite-109229828744.asia-south1.run.app

## Features
- Gemini AI with multi-key rotation and automatic model fallback
- Real-time weather and live data integration via MCP
- Natural language to SQL query engine
- Glassmorphism UI with cinematic design
- Fully deployed on Google Cloud Run with Cloud SQL (PostgreSQL)

## Tech Stack
| Layer | Technology |
|---|---|
| Backend | FastAPI, Python 3.11 |
| AI | Google Gemini 2.5 Flash |
| Database | PostgreSQL (Cloud SQL) |
| Deployment | Google Cloud Run |
| Frontend | HTML, CSS, JavaScript |

## Setup
Clone the repo, copy `.env.example` to `.env`, fill in your API keys and run:

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080

## Author
Varshith Kumar — Submitted for Google Cloud Cohort 1, 2026
