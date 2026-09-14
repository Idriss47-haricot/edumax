import hashlib
import requests
import time
from django.conf import settings

# Configuration par défaut (à mettre dans settings.py)
BBB_URL = getattr(settings, 'BBB_URL', 'https://test.bigbluebutton.org/bigbluebutton/')
BBB_SECRET = getattr(settings, 'BBB_SECRET', '8cd8ef52e8e101574e400365b55e11a6')


def create_bbb_meeting(meeting_id, meeting_name, duration=120):
    """
    Crée une réunion BigBlueButton et retourne les liens enseignant et étudiant
    
    Args:
        meeting_id: identifiant unique de la réunion
        meeting_name: nom de la réunion
        duration: durée en minutes
    
    Returns:
        tuple: (lien_enseignant, lien_etudiant)
    """
    
    # Paramètres de création
    params = {
        'meetingID': meeting_id,
        'name': meeting_name[:80],
        'attendeePW': 'etudiant123',
        'moderatorPW': 'enseignant123',
        'record': 'true',
        'autoStartRecording': 'true',
        'allowStartStopRecording': 'false',
        'duration': duration,
    }
    
    # Générer la checksum
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    checksum = hashlib.sha1(f"create{query_string}{BBB_SECRET}".encode()).hexdigest()
    
    # Appel API
    url = f"{BBB_URL}api/create?{query_string}&checksum={checksum}"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200 and 'returncode="SUCCESS"' in response.text:
            
            # Lien pour l'enseignant (modérateur)
            join_params_mod = {
                'meetingID': meeting_id,
                'password': 'enseignant123',
                'fullName': 'Enseignant',
                'role': 'MODERATOR'
            }
            join_query_mod = '&'.join([f"{k}={v}" for k, v in join_params_mod.items()])
            join_checksum_mod = hashlib.sha1(f"join{join_query_mod}{BBB_SECRET}".encode()).hexdigest()
            lien_enseignant = f"{BBB_URL}api/join?{join_query_mod}&checksum={join_checksum_mod}"
            
            # Lien pour l'étudiant (participant)
            join_params_etud = {
                'meetingID': meeting_id,
                'password': 'etudiant123',
                'fullName': 'Étudiant',
                'role': 'VIEWER'
            }
            join_query_etud = '&'.join([f"{k}={v}" for k, v in join_params_etud.items()])
            join_checksum_etud = hashlib.sha1(f"join{join_query_etud}{BBB_SECRET}".encode()).hexdigest()
            lien_etudiant = f"{BBB_URL}api/join?{join_query_etud}&checksum={join_checksum_etud}"
            
            return lien_enseignant, lien_etudiant
        
        else:
            # Fallback: générer des liens mock pour le développement
            return f"/visio/mock/enseignant/{meeting_id}", f"/visio/mock/etudiant/{meeting_id}"
            
    except Exception as e:
        print(f"Erreur BBB: {e}")
        # Fallback
        return f"/visio/mock/enseignant/{meeting_id}", f"/visio/mock/etudiant/{meeting_id}"


def get_bbb_recordings(meeting_id):
    """Récupère les enregistrements d'une réunion"""
    
    params = {
        'meetingID': meeting_id,
    }
    
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    checksum = hashlib.sha1(f"getRecordings{query_string}{BBB_SECRET}".encode()).hexdigest()
    
    url = f"{BBB_URL}api/getRecordings?{query_string}&checksum={checksum}"
    
    try:
        response = requests.get(url, timeout=10)
        # Traiter la réponse XML pour extraire les URLs
        # (Simplifié pour l'exemple)
        return []
    except:
        return []