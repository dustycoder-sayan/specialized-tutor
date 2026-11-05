"""Thin views: parse request, delegate to services/repositories, shape response."""
import json

from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .repositories import ConversationRepository
from .services import get_tutor_service

repo = ConversationRepository()


def _session_key(request) -> str:
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def _serialize(c):
    return {"id": str(c.id), "title": c.title}


@ensure_csrf_cookie
def index(request):
    _session_key(request)
    return render(request, "chat/index.html")


@require_GET
def conversation_list(request):
    items = repo.list_for_session(_session_key(request))
    return JsonResponse({"conversations": [_serialize(c) for c in items]})


@require_http_methods(["GET", "DELETE"])
def conversation_detail(request, conversation_id):
    conversation = repo.get(_session_key(request), conversation_id)
    if conversation is None:
        return JsonResponse({"error": "Not found"}, status=404)
    if request.method == "DELETE":
        repo.delete(conversation)
        return JsonResponse({"ok": True})
    messages = [{"role": m.role, "content": m.content} for m in conversation.messages.all()]
    return JsonResponse({**_serialize(conversation), "messages": messages})


@require_POST
def chat(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    events = get_tutor_service().stream_reply(
        _session_key(request), body.get("conversation_id"), str(body.get("message", ""))
    )
    stream = (json.dumps(e) + "\n" for e in events)
    response = StreamingHttpResponse(stream, content_type="application/x-ndjson")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
