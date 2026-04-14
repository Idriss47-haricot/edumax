"""Générateur de rapports professionnels pour l'application Tontine"""
import json
from datetime import datetime, timedelta
import sqlite3
from database import get_db

class ReportGenerator:
    """Classe pour générer des rapports et bilans professionnels"""
    
    @staticmethod
    def generer_bilan_seance(seance_id):
        """Génère un bilan complet d'une séance"""
        conn = get_db()
        cursor = conn.cursor()
        
        # Informations de la séance
        cursor.execute('''
            SELECT * FROM seances WHERE id = ?
        ''', (seance_id,))
        seance = cursor.fetchone()
        
        if not seance:
            return None
        
        # Présences
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN est_present = 1 THEN 1 ELSE 0 END) as presents,
                SUM(CASE WHEN retard = 1 THEN 1 ELSE 0 END) as retards,
                SUM(CASE WHEN est_present = 0 THEN 1 ELSE 0 END) as absents
            FROM presences_seance
            WHERE seance_id = ?
        ''', (seance_id,))
        presences = cursor.fetchone()
        
        # Cotisations collectées pendant la séance
        cursor.execute('''
            SELECT 
                COUNT(*) as nb_cotisations,
                SUM(cm.montant_paye) as total_cotisations,
                GROUP_CONCAT(DISTINCT c.nom_cotisation) as cotisations_liste
            FROM cotisation_membres cm
            JOIN cotisations c ON cm.cotisation_id = c.id
            WHERE cm.seance_id = ?
        ''', (seance_id,))
        cotisations = cursor.fetchone()
        
        # Prêts accordés pendant la séance
        cursor.execute('''
            SELECT 
                COUNT(*) as nb_prets,
                SUM(p.montant_principal) as total_prets,
                GROUP_CONCAT(p.numero_pret) as prets_liste
            FROM seance_prets sp
            JOIN prets p ON sp.pret_id = p.id
            WHERE sp.seance_id = ?
        ''', (seance_id,))
        prets = cursor.fetchone()
        
        # Sanctions appliquées pendant la séance
        cursor.execute('''
            SELECT 
                COUNT(*) as nb_sanctions,
                SUM(s.montant_amende) as total_amendes,
                GROUP_CONCAT(s.type_sanction) as sanctions_liste
            FROM seance_sanctions ss
            JOIN sanctions s ON ss.sanction_id = s.id
            WHERE ss.seance_id = ?
        ''', (seance_id,))
        sanctions = cursor.fetchone()
        
        # Événements discutés
        cursor.execute('''
            SELECT 
                COUNT(*) as nb_evenements,
                GROUP_CONCAT(e.nom_evenement) as evenements_liste
            FROM seance_evenements se
            JOIN evenements e ON se.evenement_id = e.id
            WHERE se.seance_id = ?
        ''', (seance_id,))
        evenements = cursor.fetchone()
        
        # Évolution des fonds
        cursor.execute('''
            SELECT 
                SUM(solde_avant) as total_avant,
                SUM(solde_apres) as total_apres,
                SUM(solde_apres - solde_avant) as variation
            FROM seance_fonds
            WHERE seance_id = ?
        ''', (seance_id,))
        fonds = cursor.fetchone()
        
        # Évolution de l'épargne
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN type_operation = 'depot' THEN montant ELSE 0 END) as depots,
                SUM(CASE WHEN type_operation = 'retrait' THEN montant ELSE 0 END) as retraits
            FROM operations_epargne
            WHERE seance_id = ?
        ''', (seance_id,))
        epargne = cursor.fetchone()
        
        conn.close()
        
        bilan = {
            'seance': dict(seance),
            'presences': dict(presences),
            'cotisations': dict(cotisations),
            'prets': dict(prets),
            'sanctions': dict(sanctions),
            'evenements': dict(evenements),
            'fonds': dict(fonds),
            'epargne': dict(epargne),
            'taux_presence': (presences['presents'] / presences['total'] * 100) if presences['total'] > 0 else 0,
            'date_generation': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return bilan
    
    @staticmethod
    def generer_bilan_membre(membre_id, periode_debut=None, periode_fin=None):
        """Génère un bilan complet pour un membre sur une période"""
        conn = get_db()
        cursor = conn.cursor()
        
        if not periode_debut:
            periode_debut = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not periode_fin:
            periode_fin = datetime.now().strftime('%Y-%m-%d')
        
        # Informations du membre
        cursor.execute('SELECT * FROM membres WHERE id = ?', (membre_id,))
        membre = cursor.fetchone()
        
        if not membre:
            return None
        
        # Statistiques des cotisations
        cursor.execute('''
            SELECT 
                COUNT(*) as nb_cotisations,
                SUM(montant_paye) as total_cotise,
                AVG(montant_paye) as moyenne_cotisation,
                MAX(montant_paye) as max_cotisation,
                MIN(montant_paye) as min_cotisation
            FROM cotisation_membres
            WHERE membre_id = ? AND date_ajout BETWEEN ? AND ?
        ''', (membre_id, periode_debut, periode_fin))
        cotisations = cursor.fetchone()
        
        # Évolution de l'épargne sur la période
        cursor.execute('''
            SELECT 
                COALESCE(SUM(CASE WHEN type_operation = 'depot' THEN montant ELSE 0 END), 0) as depots,
                COALESCE(SUM(CASE WHEN type_operation = 'retrait' THEN montant ELSE 0 END), 0) as retraits,
                (SELECT solde_actuel FROM epargne WHERE membre_id = ?) as solde_actuel
            FROM operations_epargne o
            JOIN epargne e ON o.epargne_id = e.id
            WHERE e.membre_id = ? AND o.date_operation BETWEEN ? AND ?
        ''', (membre_id, membre_id, periode_debut, periode_fin))
        epargne = cursor.fetchone()
        
        # Prêts
        cursor.execute('''
            SELECT 
                COUNT(*) as nb_prets,
                SUM(montant_principal) as total_emprunte,
                SUM(montant_restant) as total_restant,
                AVG(taux_interet) as taux_moyen
            FROM prets
            WHERE membre_id = ? AND date_octroi BETWEEN ? AND ?
        ''', (membre_id, periode_debut, periode_fin))
        prets = cursor.fetchone()
        
        # Remboursements
        cursor.execute('''
            SELECT 
                COUNT(*) as nb_remboursements,
                SUM(r.montant) as total_rembourse
            FROM remboursements_pret r
            JOIN prets p ON r.pret_id = p.id
            WHERE p.membre_id = ? AND r.date_remboursement BETWEEN ? AND ?
        ''', (membre_id, periode_debut, periode_fin))
        remboursements = cursor.fetchone()
        
        # Sanctions
        cursor.execute('''
            SELECT 
                COUNT(*) as nb_sanctions,
                SUM(montant_amende) as total_amendes,
                GROUP_CONCAT(type_sanction) as types_sanctions
            FROM sanctions
            WHERE membre_id = ? AND date_sanction BETWEEN ? AND ?
        ''', (membre_id, periode_debut, periode_fin))
        sanctions = cursor.fetchone()
        
        # Présences aux séances
        cursor.execute('''
            SELECT 
                COUNT(*) as total_seances,
                SUM(CASE WHEN est_present = 1 THEN 1 ELSE 0 END) as presences,
                SUM(CASE WHEN retard = 1 THEN 1 ELSE 0 END) as retards
            FROM presences_seance ps
            JOIN seances s ON ps.seance_id = s.id
            WHERE ps.membre_id = ? AND s.date_seance BETWEEN ? AND ?
        ''', (membre_id, periode_debut, periode_fin))
        presences = cursor.fetchone()
        
        # Solde fonds de caisse
        cursor.execute('SELECT solde_actuel FROM fonds_caisse WHERE membre_id = ?', (membre_id,))
        fonds = cursor.fetchone()
        
        conn.close()
        
        bilan = {
            'membre': dict(membre),
            'periode': {
                'debut': periode_debut,
                'fin': periode_fin
            },
            'cotisations': dict(cotisations),
            'epargne': dict(epargne),
            'prets': dict(prets),
            'remboursements': dict(remboursements),
            'sanctions': dict(sanctions),
            'presences': dict(presences),
            'fonds': dict(fonds) if fonds else {'solde_actuel': 0},
            'taux_presence': (presences['presences'] / presences['total_seances'] * 100) if presences['total_seances'] > 0 else 0,
            'solde_net': (epargne['solde_actuel'] if epargne['solde_actuel'] else 0) + 
                         (fonds['solde_actuel'] if fonds else 0),
            'date_generation': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return bilan
    
    @staticmethod
    def generer_rapport_financier():
        """Génère un rapport financier complet"""
        conn = get_db()
        cursor = conn.cursor()
        
        # Situation actuelle
        stats = {
            'total_cotisations': 0,
            'total_epargne': 0,
            'total_fonds': 0,
            'total_prets': 0,
            'total_amendes': 0,
            'tresorerie': 0
        }
        
        cursor.execute("SELECT SUM(montant_paye) FROM cotisation_membres")
        stats['total_cotisations'] = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(solde_actuel) FROM epargne")
        stats['total_epargne'] = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(solde_actuel) FROM fonds_caisse")
        stats['total_fonds'] = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(montant_restant) FROM prets WHERE statut = 'en_cours'")
        stats['total_prets'] = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(montant_amende) FROM sanctions WHERE statut = 'appliquee'")
        stats['total_amendes'] = cursor.fetchone()[0] or 0
        
        stats['tresorerie'] = stats['total_fonds'] + stats['total_epargne'] + stats['total_cotisations'] - stats['total_prets']
        
        # Évolution mensuelle sur 12 mois
        cursor.execute('''
            SELECT 
                strftime('%Y-%m', date_operation) as mois,
                SUM(CASE WHEN type_operation = 'depot' THEN montant ELSE -montant END) as evolution_epargne
            FROM operations_epargne
            WHERE date_operation >= date('now', '-12 months')
            GROUP BY mois
            ORDER BY mois
        ''')
        evolution_epargne = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute('''
            SELECT 
                strftime('%Y-%m', date_ajout) as mois,
                SUM(montant_paye) as total
            FROM cotisation_membres
            WHERE date_ajout >= date('now', '-12 months')
            GROUP BY mois
            ORDER BY mois
        ''')
        evolution_cotisations = [dict(row) for row in cursor.fetchall()]
        
        # Top contributeurs
        cursor.execute('''
            SELECT m.nom, m.prenom, SUM(cm.montant_paye) as total_cotise
            FROM cotisation_membres cm
            JOIN membres m ON cm.membre_id = m.id
            GROUP BY m.id
            ORDER BY total_cotise DESC
            LIMIT 5
        ''')
        top_cotiseurs = [dict(row) for row in cursor.fetchall()]
        
        # Top épargnants
        cursor.execute('''
            SELECT m.nom, m.prenom, e.solde_actuel as epargne
            FROM epargne e
            JOIN membres m ON e.membre_id = m.id
            ORDER BY e.solde_actuel DESC
            LIMIT 5
        ''')
        top_epargnants = [dict(row) for row in cursor.fetchall()]
        
        # Prêts en cours
        cursor.execute('''
            SELECT 
                COUNT(*) as nb_prets,
                SUM(montant_restant) as total_restant,
                AVG(taux_interet) as taux_moyen
            FROM prets
            WHERE statut = 'en_cours'
        ''')
        prets_en_cours = cursor.fetchone()
        
        # Sanctions par type
        cursor.execute('''
            SELECT 
                type_sanction,
                COUNT(*) as nombre,
                SUM(montant_amende) as total
            FROM sanctions
            WHERE statut = 'appliquee'
            GROUP BY type_sanction
            ORDER BY nombre DESC
        ''')
        sanctions_par_type = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'stats': stats,
            'evolution_epargne': evolution_epargne,
            'evolution_cotisations': evolution_cotisations,
            'top_cotiseurs': top_cotiseurs,
            'top_epargnants': top_epargnants,
            'prets_en_cours': dict(prets_en_cours) if prets_en_cours else {'nb_prets': 0, 'total_restant': 0, 'taux_moyen': 0},
            'sanctions_par_type': sanctions_par_type,
            'date_generation': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @staticmethod
    def generer_analyse_credit():
        """Analyse avancée des crédits et risques"""
        conn = get_db()
        cursor = conn.cursor()
        
        # Taux de remboursement global
        cursor.execute('''
            SELECT 
                COUNT(*) as total_prets,
                SUM(CASE WHEN statut = 'rembourse' THEN 1 ELSE 0 END) as rembourses,
                SUM(CASE WHEN statut = 'en_cours' THEN 1 ELSE 0 END) as en_cours,
                SUM(CASE WHEN statut = 'en_retard' THEN 1 ELSE 0 END) as en_retard
            FROM prets
        ''')
        stats_prets = cursor.fetchone()
        
        # Délais moyens de remboursement
        cursor.execute('''
            SELECT 
                AVG(julianday(date_remboursement) - julianday(date_octroi)) as delai_moyen
            FROM prets p
            JOIN remboursements_pret r ON p.id = r.pret_id
            WHERE p.statut = 'rembourse'
        ''')
        delai_moyen = cursor.fetchone()
        
        # Membres à risque (plus de 2 retards ou prêt en retard)
        cursor.execute('''
            SELECT 
                m.id, m.nom, m.prenom,
                COUNT(CASE WHEN p.statut = 'en_retard' THEN 1 END) as prets_retard,
                COUNT(CASE WHEN e.statut = 'en_attente' AND e.date_echeance < date('now') THEN 1 END) as echeances_retard
            FROM membres m
            LEFT JOIN prets p ON m.id = p.membre_id
            LEFT JOIN echeances_pret e ON p.id = e.pret_id
            GROUP BY m.id
            HAVING prets_retard > 0 OR echeances_retard > 0
            ORDER BY echeances_retard DESC
        ''')
        membres_risque = [dict(row) for row in cursor.fetchall()]
        
        # Capacité d'emprunt des membres
        cursor.execute('''
            SELECT 
                m.id, m.nom, m.prenom,
                COALESCE(e.solde_actuel, 0) as epargne,
                COALESCE((SELECT SUM(montant_restant) FROM prets WHERE membre_id = m.id AND statut = 'en_cours'), 0) as prets_en_cours,
                COALESCE(e.solde_actuel * 2, 0) as capacite_max,
                COALESCE(e.solde_actuel * 2 - 
                    (SELECT COALESCE(SUM(montant_restant), 0) FROM prets WHERE membre_id = m.id AND statut = 'en_cours'), 
                    e.solde_actuel * 2) as capacite_restante
            FROM membres m
            LEFT JOIN epargne e ON m.id = e.membre_id
            WHERE m.statut = 'actif'
            ORDER BY capacite_restante DESC
        ''')
        capacite_emprunt = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'stats_prets': dict(stats_prets),
            'delai_moyen': delai_moyen[0] if delai_moyen else 0,
            'membres_risque': membres_risque,
            'capacite_emprunt': capacite_emprunt,
            'taux_remboursement': (stats_prets[1] / stats_prets[0] * 100) if stats_prets[0] > 0 else 0,
            'taux_retard': (stats_prets[3] / stats_prets[0] * 100) if stats_prets[0] > 0 else 0
        }

class ExportManager:
    """Gestionnaire des exports de rapports"""
    
    @staticmethod
    def exporter_csv(bilan, filename):
        """Exporte un bilan au format CSV"""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        if 'membre' in bilan:
            # Bilan membre
            writer.writerow(['Bilan Membre', bilan['membre']['prenom'], bilan['membre']['nom']])
            writer.writerow(['Période', bilan['periode']['debut'], bilan['periode']['fin']])
            writer.writerow([])
            writer.writerow(['Catégorie', 'Valeur'])
            writer.writerow(['Cotisations totales', f"{bilan['cotisations']['total_cotise']:,.0f} FCFA"])
            writer.writerow(['Nombre de cotisations', bilan['cotisations']['nb_cotisations']])
            writer.writerow(['Épargne actuelle', f"{bilan['epargne']['solde_actuel']:,.0f} FCFA"])
            writer.writerow(['Prêts empruntés', f"{bilan['prets']['total_emprunte']:,.0f} FCFA"])
            writer.writerow(['Remboursements effectués', f"{bilan['remboursements']['total_rembourse']:,.0f} FCFA"])
            writer.writerow(['Sanctions', f"{bilan['sanctions']['total_amendes']:,.0f} FCFA"])
            writer.writerow(['Taux de présence', f"{bilan['taux_presence']:.1f}%"])
            writer.writerow(['Solde net', f"{bilan['solde_net']:,.0f} FCFA"])
        
        return output.getvalue()
    
    @staticmethod
    def exporter_json(bilan):
        """Exporte un bilan au format JSON"""
        return json.dumps(bilan, indent=2, default=str, ensure_ascii=False)