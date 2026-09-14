from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import ParametresMessagerie, MessagePrive, Conversation

def nettoyer_anciens_messages():
    """Supprime les anciens messages selon configuration"""
    config = ParametresMessagerie.get_config()
    
    date_limite = timezone.now() - timedelta(days=config.supprimer_messages_apres_jours)
    anciens_messages = MessagePrive.objects.filter(date_envoi__lt=date_limite)
    count = anciens_messages.count()
    anciens_messages.delete()
    
    # Supprimer les conversations vides
    date_limite_conv = timezone.now() - timedelta(days=config.supprimer_conversations_vides_apres_jours)
    conversations_vides = Conversation.objects.filter(
        messages__isnull=True,
        date_modification__lt=date_limite_conv
    )
    count_conv = conversations_vides.count()
    conversations_vides.delete()
    
    return count, count_conv

# Appeler ceci via une tâche cron ou Celery