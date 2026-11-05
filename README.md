# AI Tutor

Single-page Django chat app (ChatGPT/Claude-style layout) backed by the OpenAI client library, with streaming responses, persisted history and input guardrails.

## Run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add your OPENAI_API_KEY
python manage.py migrate
python manage.py runserver
```
Open http://127.0.0.1:8000. Run tests with `python manage.py test`.

## Architecture
| Layer | File | Pattern |
|---|---|---|
| Views (HTTP only) | `chat/views.py` | Thin controllers |
| Orchestration | `chat/services/tutor.py` | Service layer |
| LLM access | `chat/services/llm.py` | Strategy / Adapter (swap OpenAI for another provider) |
| Input safety | `chat/services/guardrails.py` | Chain of Responsibility |
| Persistence | `chat/repositories.py`, `chat/models.py` | Repository |
| Wiring | `chat/services/__init__.py` | Composition root / dependency injection |

Conversations are scoped to the anonymous browser session; add `django.contrib.auth` and a user FK to support accounts.
