# 🌍 Multilingual Language Learning App
An intelligent language learning application with AI-powered Anki algorithm for personalized vocabulary training.

## 📖 About the Project
This app enables users to input sentences in their native language, categorize them by themes (e.g., "Arbeit", "Essen"), and have them translated into target languages using AI. An intelligent spaced repetition algorithm ensures optimal learning success through personalized review scheduling.


# 🧠 N-Languages AI — Intelligent Language Learning App

An intelligent, LLM-powered **language learning platform** designed to evaluate user translations, provide feedback, and track progress using an **Anki-style review algorithm**.
Built with **Flask**, **SQLAlchemy**, and **OpenAI-compatible LLM adapters**, the app offers a scalable backend for personalized multilingual training.

---

## 🚀 Features & Functionality

- 🌐 **Multi-language support** — users can define one *native language* and multiple *target languages*.
- 🧩 **Smart evaluation** — translations are evaluated by an LLM (via `llm_adapter.py`) for accuracy and fluency.
- 📊 **Score tracking** — each sentence is scored from `0–100` and stored in the database.
- 🕒 **Anki-style scheduling** — spaced repetition logic determines when a sentence should next be reviewed.
- 💬 **Interactive API** — fully documented Swagger UI for testing endpoints.
- 🧱 **Modular architecture** — clear separation between API, data layer, and LLM logic.

---

## ⚙️ Workflow Overview

1. **User registration**
   A user is created with a `username` and a `native_language`.

2. **Target language setup**
   The user defines one or more target languages via `/user_languages`.

3. **Sentence creation**
   Sentences in the native language are stored in the `sentences` table.

4. **Translation submission**
   The user submits translations for all target languages to `/evaluate_sentence`.

5. **Evaluation & Scoring**
   The LLM adapter (`llm_adapter.py`) evaluates the translations, returning:
   - a per-language score (0–100)
   - an overall score
   - explanations and feedback
---
## 🧪 Example API Interaction (Swagger)
### POST /evaluate_sentence
```text
{
  "native_language": "pl",
  "sentence_id": 7,
  "translations": {
    "translations": [
      {
        "nl": "School is saai"
      },
      {
        "fr": "L'école est ennuyeuse"
      }
    ]
  },
  "user_id": 7
}
```
### Response:
```text
{
  "explanations": {
    "fr": "Diese Übersetzung hat bedeutende Fehler, insbesondere im Wort 'fourure', das nicht korrekt ist. Das richtige Wort 'pelage' sollte verwendet werden, und 'Ma' sollte 'Mon' sein, weil es sich auf das maskuline Wort für Fell bezieht.",
    "it": "Diese Übersetzung ist grammatikalisch korrekt und versteht die Hauptbedeutung, könnte aber stilistisch etwas verbessert werden."
  },
  "language_scores": {
    "fr": 40,
    "it": 80
  },
  "message": "Evaluation completed and score updated.",
  "overall_score": 74,
  "sentence": {
    "id": 10,
    "next_review": "2025-10-12T10:26:35.889797",
    "review_count": 2,
    "score": 74
  },
  "success": true
}
```

## 🗄️ Database Schema (ERD)

```text
┌───────────────────────────┐
│          USERS            │
├───────────────────────────┤
│ id (PK)                   │
│ username                  │
│ native_language           │
│ created_at                │
└────────────┬──────────────┘
             │ 1
             │
             │ N
┌────────────▼──────────────┐
│      USER_LANGUAGES       │
├───────────────────────────┤
│ id (PK)                   │
│ user_id (FK → users.id)   │
│ language_code             │
│ created_at                │
└────────────┬──────────────┘
             │ 1
             │
             │ N
┌────────────▼──────────────┐
│        SENTENCES          │
├───────────────────────────┤
│ id (PK)                   │
│ user_id (FK → users.id)   │
│ original_text             │
│ language_code             │
│ category                  │
│ score                     │
│ last_review               │
│ next_review               │
│ review_count              │
│ created_at                │
└───────────────────────────┘

```

## 🔍 Structure
```text
app.py
│
└── src/server/
    ├── main.py               → Flask initialization, app setup
    ├── extensions.py          → DB, Swagger, CORS setup
    ├── routes_web.py          → Web routes (UI)
    │
    ├── api/
    │   ├── routes.py          → REST API endpoints (Swagger-documented)
    │   ├── llm_adapter.py     → LLM scoring logic (translation evaluation)
    │
    ├── models/
    │   ├── data_models.py     → SQLAlchemy models (User, Sentence, etc.)
    │   └── api.py             → Pydantic schemas for API validation
    │
    ├── data_manager.py        → Business logic, DB operations, score updates
    │
    └── ...
.env                          → Environment variables
README.md                     → Project documentation
```

## 🧠 Technical Highlights
```text
| Component         | Technology                           |
| ----------------- | ------------------------------------ |
| Backend Framework | Flask                                |
| Database ORM      | SQLAlchemy                           |
| Data Validation   | Pydantic                             |
| LLM Interface     | OpenAI-compatible adapter            |
| API Docs          | Swagger / Flasgger                   |
| Storage           | SQLite (dev), scalable to PostgreSQL |
```
🧩 Design Patterns Used

Service Layer Pattern — business logic encapsulated in data_manager.py

MVC/Blueprint Architecture — API (Controller), Models (Model), Web Routes (View)

Separation of Concerns — independent layers for API, DB, and LLM logic

Dependency Injection via extensions.py

### AI-Powered Features
- **Dynamic Translation Quality**: Confidence scoring for translation accuracy.
- **Personalized Learning**: AI adapts review intervals based on individual performance.
- **Intelligent Feedback**: Context-aware error analysis and improvement suggestions.

### System Architecture
- **Scalable Database Design**: Normalized schema supporting unlimited languages and categories.
- **RESTful API Design**: Clean separation of concerns with proper HTTP methods.
- **Modular AI Integration**: Pluggable AI services with structured JSON communication.

### Performance Considerations
- **Optimized Queries**: Indexed database fields for fast retrieval, including category-based queries.
- **Efficient Data Structure**: Minimal redundancy with proper foreign key relationships.
- **Caching Strategy**: Ready for Redis integration for frequently accessed translations.

## 🔬 Technical Challenges Solved
1. **Multi-language Scalability**: Database design supports adding new languages without schema changes.
2. **Category-Based Filtering**: Efficient querying for thematic learning (e.g., "Arbeit").
3. **AI Integration Reliability**: Robust error handling and fallback strategies for API calls.
4. **Spaced Repetition Logic**: Complex algorithm implementation with AI-enhanced decision making.
5. **Performance Optimization**: Efficient query patterns for review scheduling and progress tracking.
