# website/admin_accueil.py
from django.contrib import admin
from .models import ConfigurationPlateforme, DiapositiveHero, Temoignage, Partenaire, BannierePromo

@admin.register(ConfigurationPlateforme)
class ConfigurationPlateformeAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Statistiques', {
            'fields': (
                'stat1_valeur_auto', 'stat1_valeur_fixe', 'stat1_label',
                'stat2_valeur_auto', 'stat2_valeur_fixe', 'stat2_label',
                'stat3_valeur_auto', 'stat3_valeur_fixe', 'stat3_label',
                'stat4_valeur_auto', 'stat4_valeur_fixe', 'stat4_label',
            )
        }),
        ('Paramètres', {
            'fields': ('formations_tri', 'nb_formations_accueil', 'nb_epreuves_accueil', 'nb_ecoles_accueil')
        }),
    )
    def has_add_permission(self, request):
        return not ConfigurationPlateforme.objects.exists()
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(DiapositiveHero)
class DiapositiveHeroAdmin(admin.ModelAdmin):
    list_display = ['titre', 'ordre', 'actif', 'date_creation']
    list_editable = ['ordre', 'actif']
    list_filter = ['actif']
    search_fields = ['titre']

@admin.register(Temoignage)
class TemoignageAdmin(admin.ModelAdmin):
    list_display = ['nom', 'note', 'ordre', 'actif']
    list_editable = ['ordre', 'actif']
    list_filter = ['actif', 'note']

@admin.register(Partenaire)
class PartenaireAdmin(admin.ModelAdmin):
    list_display = ['nom', 'ordre', 'actif']
    list_editable = ['ordre', 'actif']

@admin.register(BannierePromo)
class BannierePromoAdmin(admin.ModelAdmin):
    list_display = ['texte', 'actif', 'date_debut', 'date_fin']
    list_editable = ['actif']