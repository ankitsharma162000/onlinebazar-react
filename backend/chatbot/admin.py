from django.contrib import admin
from .models import ChatKnowledge, ChatSession, ChatMessage, PendingQuestion

@admin.register(ChatKnowledge)
class ChatKnowledgeAdmin(admin.ModelAdmin):
    list_display = ['question', 'hits', 'created_at']
    search_fields = ['question', 'keywords', 'answer']

@admin.register(PendingQuestion)
class PendingQuestionAdmin(admin.ModelAdmin):
    list_display = ['question', 'status', 'created_at']
    list_filter = ['status']
