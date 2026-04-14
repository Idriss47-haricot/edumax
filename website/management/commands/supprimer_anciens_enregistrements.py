from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from website.models import SeanceProgrammee

class Command(BaseCommand):
    help = 'Supprime les enregistrements de visio de plus de 15 jours'

    def handle(self, *args, **options):
        date_limite = timezone.now() - timedelta(days=15)
        
        anciennes_visios = SeanceProgrammee.objects.filter(
            type_seance='visio',
            enregistrement_disponible_jusqua__lt=date_limite,
            enregistrement_url__isnull=False
        )
        
        count = 0
        for visio in anciennes_visios:
            # Ici, appeler l'API BBB pour supprimer l'enregistrement
            visio.enregistrement_url = None
            visio.enregistrement_id = None
            visio.enregistrement_disponible_jusqua = None
            visio.save()
            count += 1
            self.stdout.write(f"Enregistrement supprimé pour la séance {visio.id}")
        
        self.stdout.write(f"Terminé. {count} enregistrement(s) supprimé(s).")