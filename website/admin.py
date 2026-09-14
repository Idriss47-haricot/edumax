from django.contrib import admin
from .models import (
    RubriqueEpreuve, 
    CategorieEpreuve, 
    Epreuve, 
    AchatEpreuve,
    PanierEpreuve,
    TelechargementEpreuve,
)


# Garder les autres
@admin.register(RubriqueEpreuve)
class RubriqueEpreuveAdmin(admin.ModelAdmin):
    list_display = ['nom', 'slug', 'ordre', 'actif']
    prepopulated_fields = {'slug': ('nom',)}
    list_editable = ['ordre', 'actif']

@admin.register(CategorieEpreuve)
class CategorieEpreuveAdmin(admin.ModelAdmin):
    list_display = ['nom', 'rubrique', 'ordre', 'actif']
    list_filter = ['rubrique', 'actif']
    prepopulated_fields = {'slug': ('nom',)}
    list_editable = ['ordre', 'actif']

@admin.register(Epreuve)
class EpreuveAdmin(admin.ModelAdmin):
    list_display = ['titre', 'categorie', 'annee', 'serie', 'prix', 'nb_ventes', 'statut']
    list_filter = ['categorie', 'statut', 'annee', 'serie']
    search_fields = ['titre', 'description']
    list_editable = ['prix', 'statut']

@admin.register(AchatEpreuve)
class AchatEpreuveAdmin(admin.ModelAdmin):
    list_display = ['acheteur', 'prix_total', 'statut', 'date_achat']
    list_filter = ['statut', 'date_achat']
    search_fields = ['acheteur__username', 'reference_paiement']

@admin.register(PanierEpreuve)
class PanierEpreuveAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'date_modification']

@admin.register(TelechargementEpreuve)
class TelechargementEpreuveAdmin(admin.ModelAdmin):
    list_display = ['epreuve', 'date_telechargement', 'ip_adresse']
    list_filter = ['date_telechargement']

 
ADMIN_REGISTRATIONS = """
from django.contrib import admin
from .models import (
    Formation, FichierFormation, ModuleFormation,
    WishlistFormation, ProgressionFormation,
    CertificatFormation, ValidationAutomatiqueLog,
    Avis, AchatFormation, Coupon, ConditionVente,
    SignalementFormation, RegleVente, CentreInteret,
)
 
 
@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display  = ('titre', 'createur', 'statut', 'prix', 'note_moyenne',
                     'nb_ventes', 'certifiee', 'mise_en_avant', 'date_creation')
    list_filter   = ('statut', 'certifiee', 'mise_en_avant', 'niveau', 'langue')
    search_fields = ('titre', 'createur__username', 'createur__email')
    prepopulated_fields = {'slug': ('titre',)}
    readonly_fields = ('nb_ventes', 'nb_avis', 'note_moyenne', 'revenu_total',
                       'nb_vues', 'date_creation', 'date_publication')
    filter_horizontal = ('centres_interet', 'cours')
    actions   = ['publier', 'suspendre', 'mettre_en_avant']
    list_per_page = 25
 
    def publier(self, request, queryset):
        from django.utils import timezone
        queryset.update(statut='publie', date_publication=timezone.now())
    publier.short_description = "Publier les formations sélectionnées"
 
    def suspendre(self, request, queryset):
        queryset.update(statut='suspendu')
    suspendre.short_description = "Suspendre les formations sélectionnées"
 
    def mettre_en_avant(self, request, queryset):
        queryset.update(mise_en_avant=True)
    mettre_en_avant.short_description = "Mettre en avant"
 
 
@admin.register(FichierFormation)
class FichierFormationAdmin(admin.ModelAdmin):
    list_display  = ('titre', 'formation', 'type_fichier', 'est_apercu', 'ordre')
    list_filter   = ('type_fichier', 'est_apercu')
    search_fields = ('titre', 'formation__titre')
 
 
@admin.register(ModuleFormation)
class ModuleFormationAdmin(admin.ModelAdmin):
    list_display = ('titre', 'formation', 'ordre')
 
 
@admin.register(WishlistFormation)
class WishlistFormationAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'formation', 'date_ajout')
 
 
@admin.register(ProgressionFormation)
class ProgressionFormationAdmin(admin.ModelAdmin):
    list_display  = ('apprenant', 'formation', 'terminee', 'date_debut')
    list_filter   = ('terminee',)
    readonly_fields = ('date_debut', 'date_derniere_activite')
 
 
@admin.register(CertificatFormation)
class CertificatFormationAdmin(admin.ModelAdmin):
    list_display  = ('apprenant', 'formation', 'code_unique', 'date_obtenu')
    readonly_fields = ('code_unique', 'date_obtenu')
    search_fields = ('code_unique', 'apprenant__username', 'formation__titre')
 
 
@admin.register(Avis)
class AvisAdmin(admin.ModelAdmin):
    list_display  = ('formation', 'utilisateur', 'note', 'date_creation')
    list_filter   = ('note',)
 
 
@admin.register(AchatFormation)
class AchatFormationAdmin(admin.ModelAdmin):
    list_display  = ('formation', 'acheteur', 'prix_net', 'statut',
                     'type_paiement', 'date_achat')
    list_filter   = ('statut', 'type_paiement')
    search_fields = ('reference_paiement', 'acheteur__username', 'formation__titre')
    readonly_fields = ('date_achat', 'date_confirmation', 'reference_paiement')
 
 
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display  = ('code', 'reduction_pourcentage', 'reduction_fixe',
                     'utilisations_count', 'utilisations_max', 'actif', 'validite_fin')
    list_filter   = ('actif',)
 
 
@admin.register(SignalementFormation)
class SignalementFormationAdmin(admin.ModelAdmin):
    list_display = ('formation', 'utilisateur', 'motif', 'traite', 'date_creation')
    list_filter  = ('motif', 'traite')
    actions      = ['marquer_traite']
 
    def marquer_traite(self, request, queryset):
        queryset.update(traite=True)
    marquer_traite.short_description = "Marquer comme traité"
 
 
@admin.register(CentreInteret)
class CentreInteretAdmin(admin.ModelAdmin):
    list_display      = ('nom', 'slug', 'actif', 'ordre')
    prepopulated_fields = {'slug': ('nom',)}
 
 
@admin.register(ConditionVente)
class ConditionVenteAdmin(admin.ModelAdmin):
    list_display = ('commission_pourcentage', 'actif', 'date_modification')
 
 
@admin.register(RegleVente)
class RegleVenteAdmin(admin.ModelAdmin):
    list_display = ('rubrique', 'titre', 'ordre', 'actif')
    list_filter  = ('rubrique', 'actif')
"""
 