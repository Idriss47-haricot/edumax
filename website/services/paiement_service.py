# services/paiement_service.py
from abc import ABC, abstractmethod
import uuid

class PaiementService(ABC):
    @abstractmethod
    def initier_paiement(self, montant, reference, telephone):
        pass
    
    @abstractmethod
    def verifier_paiement(self, reference):
        pass


class OrangeMoneyService(PaiementService):
    def initier_paiement(self, montant, reference, telephone):
        # TODO: Implémenter l'appel API Orange Money
        return {
            'success': True,
            'message': 'Paiement initié (simulation)',
            'data': {'reference': reference, 'montant': float(montant), 'telephone': telephone}
        }
    
    def verifier_paiement(self, reference):
        return {'success': True, 'statut': 'confirmé'}


class MTNMoneyService(PaiementService):
    def initier_paiement(self, montant, reference, telephone):
        return {
            'success': True,
            'message': 'Paiement initié (simulation)',
            'data': {'reference': reference, 'montant': float(montant), 'telephone': telephone}
        }
    
    def verifier_paiement(self, reference):
        return {'success': True, 'statut': 'confirmé'}


def get_paiement_service(type_paiement):
    if type_paiement == 'orange':
        return OrangeMoneyService()
    elif type_paiement == 'mtn':
        return MTNMoneyService()
    else:
        return None

# Ajoutez cette fonction au début du fichier, après les imports

def calculer_commission(prix, condition):
    """
    Calcule la commission plateforme et revenu créateur
    
    Args:
        prix (float): Prix de la formation
        condition (ConditionVente): Objet contenant le pourcentage
    
    Returns:
        tuple: (commission, revenu_createur)
    """
    commission = (prix * condition.commission_pourcentage) / 100
    revenu_createur = prix - commission
    return round(commission, 2), round(revenu_createur, 2)