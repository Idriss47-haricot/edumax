from django.shortcuts import redirect
from django.urls import reverse, resolve, Resolver404

URLS_LIBRES = {
    'accueil', 'connexion', 'inscription', 'deconnexion',
    'mot_de_passe_oublie', 'reinitialisation_mot_de_passe',
    'choix_abonnement', 'initier_paiement', 'confirmer_paiement',
    'paiement_callback', 'demarrer_essai', 'verifier_abonnement',
    'abandonner_inscription',
    # Pages publiques
    'ecoles_liste', 'ecole_detail',
    'formations_liste', 'formation_detail',
    'epreuves_accueil', 'epreuves_rubrique', 'epreuves_recherche',
    'epreuves_categorie_ajax',
}

class AbonnementMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Chemins statiques/media/admin : toujours libres
        if request.path_info.startswith(('/static/', '/media/', '/admin/')):
            return self.get_response(request)

        # Utilisateur non connecté : libre sur les pages publiques,
        # redirigé vers connexion sur les pages privées
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Super admin et admin école : accès total
        if request.user.role in ('super_admin', 'admin_ecole'):
            return self.get_response(request)

        # Paiement désactivé manuellement par le super admin
        if getattr(request.user, 'paiement_desactive', False):
            return self.get_response(request)

        # Résoudre le nom de l'URL
        try:
            url_name = resolve(request.path_info).url_name
        except Resolver404:
            return self.get_response(request)

        if url_name in URLS_LIBRES:
            return self.get_response(request)

        # Vérifier l'abonnement
        from .models import AbonnementUtilisateur
        from django.utils import timezone

        abonnement = AbonnementUtilisateur.objects.filter(
            utilisateur=request.user
        ).first()

        if abonnement:
            # Paiement désactivé sur l'abonnement
            if abonnement.paiement_oblige is False:
                return self.get_response(request)
            # Essai actif
            if (abonnement.statut == 'essai'
                    and abonnement.date_fin_essai
                    and abonnement.date_fin_essai > timezone.now()):
                return self.get_response(request)
            # Abonnement payant actif
            if (abonnement.statut == 'actif'
                    and abonnement.date_fin
                    and abonnement.date_fin > timezone.now()):
                return self.get_response(request)

        # Aucun abonnement valide → page de choix
        return redirect(reverse('choix_abonnement'))