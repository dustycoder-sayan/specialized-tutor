from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/conversations/", views.conversation_list, name="conversation-list"),
    path("api/conversations/<uuid:conversation_id>/", views.conversation_detail, name="conversation-detail"),
    path("api/chat/", views.chat, name="chat"),
]
