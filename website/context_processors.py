from .models import ParametresMessagerie, MessagePrive

def messagerie_config(request):
    """Injecte la configuration de la messagerie dans tous les templates"""
    config = ParametresMessagerie.get_config()
    
    # Compter les messages non lus
    messages_non_lus = 0
    if request.user.is_authenticated:
        messages_non_lus = MessagePrive.objects.filter(
            conversation__participants=request.user,
            lu=False
        ).exclude(expediteur=request.user).count()
    
    return {
        'messagerie_config': {
            'polling_actif': config.polling_actif,
            'intervalle_polling': config.intervalle_polling,
            'pause_onglet_actif': config.pause_polling_onglet_inactif,
            'pause_nocturne_active': config.pause_polling_apres_heure,
            'heure_debut_pause': config.heure_debut_pause.strftime('%H:%M') if config.heure_debut_pause else '22:00',
            'heure_fin_pause': config.heure_fin_pause.strftime('%H:%M') if config.heure_fin_pause else '06:00',
            'adaptation_auto': config.adaptation_auto_intervalle,
            'intervalle_min': config.min_intervalle_polling,
            'intervalle_max': config.max_intervalle_polling,
            'message_polling_desactive': config.message_polling_desactive,
            'messages_non_lus': messages_non_lus,
        }
    }