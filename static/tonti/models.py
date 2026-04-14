import sqlite3
from datetime import datetime, timedelta
from database import get_db

# ============================================
# CLASSE MEMBRE
# ============================================

class Membre:
    """Classe représentant un membre"""
    def __init__(self, id=None, nom=None, prenom=None, telephone=None, email=None):
        self.id = id
        self.nom = nom
        self.prenom = prenom
        self.telephone = telephone
        self.email = email
    
    @staticmethod
    def get_by_id(membre_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM membres WHERE id = ?", (membre_id,))
        membre = cursor.fetchone()
        conn.close()
        return membre
    
    def get_epargne(self):
        """Récupère le solde d'épargne du membre"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT solde_actuel FROM epargne WHERE membre_id = ?", (self.id,))
        result = cursor.fetchone()
        conn.close()
        return result['solde_actuel'] if result else 0
    
    def get_fonds_caisse(self):
        """Récupère le solde du fonds de caisse"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT solde_actuel FROM fonds_caisse WHERE membre_id = ?", (self.id,))
        result = cursor.fetchone()
        conn.close()
        return result['solde_actuel'] if result else 0
    
    def get_prets_en_cours(self):
        """Récupère la liste des prêts en cours"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM prets 
            WHERE membre_id = ? AND statut = 'en_cours'
            ORDER BY date_octroi DESC
        ''', (self.id,))
        prets = cursor.fetchall()
        conn.close()
        return prets
    
    def get_montant_prets_en_cours(self):
        """Récupère le montant total des prêts en cours"""
        prets = self.get_prets_en_cours()
        return sum(p['montant_restant'] for p in prets)
    
    def get_taux_presence(self):
        """Calcule le taux de présence aux séances"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                COUNT(*) as total_seances,
                SUM(CASE WHEN est_present = 1 THEN 1 ELSE 0 END) as presences
            FROM presences_seance
            WHERE membre_id = ?
        ''', (self.id,))
        result = cursor.fetchone()
        conn.close()
        if result['total_seances'] == 0:
            return 100
        return (result['presences'] / result['total_seances']) * 100
    
    def get_sanctions_recues(self):
        """Récupère le nombre de sanctions reçues"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as nb, SUM(montant_amende) as total
            FROM sanctions 
            WHERE membre_id = ? AND statut = 'appliquee'
        ''', (self.id,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def peut_demander_pret(self, montant_demande):
        """Vérifie si le membre peut demander un prêt"""
        epargne = self.get_epargne()
        
        if montant_demande > epargne * 2:
            return False, f"Le montant demandé ({montant_demande} FCFA) dépasse 2 fois votre épargne ({epargne*2} FCFA)"
        
        prets_en_cours = self.get_montant_prets_en_cours()
        if prets_en_cours > 0:
            return False, f"Vous avez déjà un prêt en cours de {prets_en_cours} FCFA"
        
        taux_presence = self.get_taux_presence()
        if taux_presence < 50:
            return False, f"Votre taux de présence ({taux_presence:.1f}%) est inférieur à 50%"
        
        sanctions = self.get_sanctions_recues()
        if sanctions['nb'] >= 2:
            return False, f"Vous avez reçu {sanctions['nb']} sanctions récemment"
        
        return True, "Conditions remplies"

# ============================================
# CLASSE PRETMANAGER
# ============================================

class PretManager:
    """Gestionnaire professionnel des prêts"""
    
    @staticmethod
    def verifier_conditions(membre_id, montant_demande):
        """Vérifie si un membre peut demander un prêt"""
        conn = get_db()
        cursor = conn.cursor()
        
        conditions = {
            'epargne_suffisante': False,
            'pas_pret_en_cours': False,
            'taux_presence_suffisant': False,
            'sanctions_limite': False,
            'cotisations_a_jour': False,
            'montant_max': 0
        }
        messages = []
        
        try:
            # 1. Vérifier l'épargne
            cursor.execute('SELECT solde_actuel FROM epargne WHERE membre_id = ?', (membre_id,))
            epargne = cursor.fetchone()
            solde_epargne = epargne['solde_actuel'] if epargne else 0
            montant_max = solde_epargne * 2
            conditions['montant_max'] = montant_max
            
            if montant_demande <= montant_max:
                conditions['epargne_suffisante'] = True
            else:
                messages.append(f"❌ Montant demandé > 2× épargne (max {montant_max:,.0f} FCFA)")
            
            # 2. Vérifier les prêts en cours
            cursor.execute('''
                SELECT COUNT(*) as nb FROM prets 
                WHERE membre_id = ? AND statut IN ('en_cours', 'en_retard')
            ''', (membre_id,))
            prets_en_cours = cursor.fetchone()
            if prets_en_cours['nb'] == 0:
                conditions['pas_pret_en_cours'] = True
            else:
                messages.append(f"❌ Vous avez {prets_en_cours['nb']} prêt(s) en cours")
            
            # 3. Vérifier le taux de présence
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN est_present = 1 THEN 1 ELSE 0 END) as presents
                FROM presences_seance
                WHERE membre_id = ?
            ''', (membre_id,))
            presences = cursor.fetchone()
            total_seances = presences['total'] or 0
            if total_seances > 0:
                taux_presence = (presences['presents'] / total_seances) * 100
                if taux_presence >= 50:
                    conditions['taux_presence_suffisant'] = True
                else:
                    messages.append(f"❌ Taux de présence ({taux_presence:.1f}%) < 50%")
            else:
                conditions['taux_presence_suffisant'] = True
            
            # 4. Vérifier les sanctions
            trois_mois = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*) as nb FROM sanctions 
                WHERE membre_id = ? AND date_sanction >= ? AND statut = 'appliquee'
            ''', (membre_id, trois_mois))
            sanctions = cursor.fetchone()
            if sanctions['nb'] <= 2:
                conditions['sanctions_limite'] = True
            else:
                messages.append(f"❌ {sanctions['nb']} sanctions dans les 3 mois (max 2)")
            
            # 5. Vérifier les cotisations
            cursor.execute('''
                SELECT COUNT(*) as nb FROM cotisation_membres 
                WHERE membre_id = ? AND a_cotise = 1
                AND date_ajout >= date('now', '-30 days')
            ''', (membre_id,))
            cotisations_recentes = cursor.fetchone()
            if cotisations_recentes['nb'] >= 1:
                conditions['cotisations_a_jour'] = True
            else:
                messages.append("❌ Aucune cotisation dans les 30 derniers jours")
            
        finally:
            conn.close()
        
        toutes_remplies = all([
            conditions['epargne_suffisante'],
            conditions['pas_pret_en_cours'],
            conditions['taux_presence_suffisant'],
            conditions['sanctions_limite'],
            conditions['cotisations_a_jour']
        ])
        
        if toutes_remplies:
            return True, "✅ Vous remplissez toutes les conditions", conditions
        else:
            return False, "\n".join(messages), conditions
    
    @staticmethod
    def creer_demande(membre_id, montant, duree_mois, motif, seance_id=None):
        """Crée une demande de prêt"""
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM demandes_pret")
            count = cursor.fetchone()[0] + 1
            numero = f"DEM-{datetime.now().strftime('%Y%m')}-{str(count).zfill(4)}"
            
            cursor.execute('''
                INSERT INTO demandes_pret 
                (numero_demande, membre_id, montant_demande, duree_mois, motif, date_demande, seance_id)
                VALUES (?, ?, ?, ?, ?, date('now'), ?)
            ''', (numero, membre_id, montant, duree_mois, motif, seance_id))
            
            demande_id = cursor.lastrowid
            conn.commit()
            
            return True, f"✅ Demande {numero} créée", demande_id
            
        except Exception as e:
            conn.rollback()
            return False, f"❌ Erreur: {str(e)}", None
        finally:
            conn.close()


     
    
    
    
    @staticmethod
    def approuver_demande(demande_id, montant_accorde=None, taux_interet=None, seance_id=None):
        """Approuve une demande et crée le prêt"""
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("BEGIN IMMEDIATE")
            
            cursor.execute('''
                SELECT d.*, e.solde_actuel as epargne
                FROM demandes_pret d
                LEFT JOIN epargne e ON d.membre_id = e.membre_id
                WHERE d.id = ?
            ''', (demande_id,))
            demande = cursor.fetchone()
            
            if not demande or demande['statut'] != 'en_attente':
                return False, "Demande non trouvée ou déjà traitée"
            
            if montant_accorde is None:
                montant_accorde = demande['montant_demande']
            
            epargne = demande['epargne'] or 0
            if montant_accorde > epargne * 2:
                return False, f"Montant accordé > 2× épargne"
            
            if taux_interet is None:
                taux_interet = 5
            
            montant_total = montant_accorde * (1 + taux_interet / 100)
            date_octroi = datetime.now().strftime('%Y-%m-%d')
            date_echeance = (datetime.now() + timedelta(days=demande['duree_mois'] * 30)).strftime('%Y-%m-%d')
            
            cursor.execute("SELECT COUNT(*) FROM prets")
            count = cursor.fetchone()[0] + 1
            numero_pret = f"PRET-{datetime.now().strftime('%Y%m')}-{str(count).zfill(4)}"
            
            cursor.execute('''
                INSERT INTO prets 
                (numero_pret, demande_id, membre_id, montant_principal, taux_interet, 
                 montant_total, montant_restant, date_octroi, date_echeance, duree_mois, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, date('now'))
            ''', (numero_pret, demande_id, demande['membre_id'], montant_accorde, taux_interet,
                  montant_total, montant_total, date_octroi, date_echeance, demande['duree_mois']))
            
            pret_id = cursor.lastrowid
            
            montant_par_echeance = montant_total / demande['duree_mois']
            for i in range(1, demande['duree_mois'] + 1):
                date_echeance_i = (datetime.now() + timedelta(days=i * 30)).strftime('%Y-%m-%d')
                cursor.execute('''
                    INSERT INTO echeances_pret 
                    (pret_id, numero_echeance, montant_echeance, date_echeance, seance_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (pret_id, i, montant_par_echeance, date_echeance_i, seance_id))
            
            cursor.execute('''
                UPDATE demandes_pret 
                SET statut = 'approuve', montant_accorde = ?, taux_interet = ?, 
                    date_decision = date('now')
                WHERE id = ?
            ''', (montant_accorde, taux_interet, demande_id))
            
            conn.commit()
            return True, f"✅ Prêt {numero_pret} accordé"
            
        except Exception as e:
            conn.rollback()
            return False, f"❌ Erreur: {str(e)}"
        finally:
            conn.close()
    
    @staticmethod
    def get_echeances_a_venir(membre_id=None, jours=30):
        """Récupère les échéances à venir"""
        conn = get_db()
        cursor = conn.cursor()
        
        date_limite = (datetime.now() + timedelta(days=jours)).strftime('%Y-%m-%d')
        date_actuelle = datetime.now().strftime('%Y-%m-%d')
        
        query = '''
            SELECT e.*, p.numero_pret, p.montant_principal, p.montant_restant,
                   m.nom, m.prenom, m.telephone
            FROM echeances_pret e
            JOIN prets p ON e.pret_id = p.id
            JOIN membres m ON p.membre_id = m.id
            WHERE e.statut = 'en_attente'
            AND e.date_echeance BETWEEN ? AND ?
        '''
        params = [date_actuelle, date_limite]
        
        if membre_id:
            query += " AND p.membre_id = ?"
            params.append(membre_id)
        
        query += " ORDER BY e.date_echeance"
        
        cursor.execute(query, params)
        echeances = cursor.fetchall()
        conn.close()
        
        return echeances
    
    @staticmethod
    def get_echeances_retard(membre_id=None):
        """Récupère les échéances en retard"""
        conn = get_db()
        cursor = conn.cursor()
        
        date_actuelle = datetime.now().strftime('%Y-%m-%d')
        
        query = '''
            SELECT e.*, p.numero_pret, p.montant_principal, p.montant_restant,
                   m.nom, m.prenom, m.telephone,
                   julianday(?) - julianday(e.date_echeance) as jours_retard
            FROM echeances_pret e
            JOIN prets p ON e.pret_id = p.id
            JOIN membres m ON p.membre_id = m.id
            WHERE e.statut = 'en_attente'
            AND e.date_echeance < ?
        '''
        params = [date_actuelle, date_actuelle]
        
        if membre_id:
            query += " AND p.membre_id = ?"
            params.append(membre_id)
        
        query += " ORDER BY e.date_echeance"
        
        cursor.execute(query, params)
        echeances = cursor.fetchall()
        conn.close()
        
        return echeances
    
    @staticmethod
    def get_statistiques():
        """Retourne les statistiques globales des prêts"""
        conn = get_db()
        cursor = conn.cursor()
        
        stats = {
            'total_prets': 0,
            'prets_en_cours': 0,
            'prets_rembourses': 0,
            'prets_en_retard': 0,
            'montant_total_emprunte': 0,
            'montant_total_avec_interets': 0,
            'montant_rembourse': 0,
            'montant_restant': 0,
            'taux_remboursement': 0
        }
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN statut = 'en_cours' THEN 1 ELSE 0 END) as en_cours,
                SUM(CASE WHEN statut = 'rembourse' THEN 1 ELSE 0 END) as rembourses,
                SUM(montant_principal) as total_principal,
                SUM(montant_total) as total_avec_interets,
                SUM(montant_restant) as total_restant
            FROM prets
        ''')
        result = cursor.fetchone()
        
        if result:
            stats['total_prets'] = result['total'] or 0
            stats['prets_en_cours'] = result['en_cours'] or 0
            stats['prets_rembourses'] = result['rembourses'] or 0
            stats['montant_total_emprunte'] = result['total_principal'] or 0
            stats['montant_total_avec_interets'] = result['total_avec_interets'] or 0
            stats['montant_restant'] = result['total_restant'] or 0
            
            stats['montant_rembourse'] = stats['montant_total_avec_interets'] - stats['montant_restant']
            
            cursor.execute('''
                SELECT COUNT(DISTINCT pret_id) as nb
                FROM echeances_pret
                WHERE statut = 'en_attente' AND date_echeance < date('now')
            ''')
            stats['prets_en_retard'] = cursor.fetchone()['nb'] or 0
            
            if stats['montant_total_avec_interets'] > 0:
                stats['taux_remboursement'] = (stats['montant_rembourse'] / stats['montant_total_avec_interets']) * 100
        
        conn.close()
        return stats

# ============================================
# CLASSE EPARGNEMANAGER
# ============================================

class EpargneManager:
    """Gestionnaire des opérations d'épargne"""
    
    @staticmethod
    def depot(membre_id, montant, description="", seance_id=None):
        """Effectue un dépôt sur l'épargne"""
        if montant <= 0:
            return False, "Le montant doit être positif"
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("BEGIN IMMEDIATE")
            
            cursor.execute("SELECT * FROM epargne WHERE membre_id = ?", (membre_id,))
            epargne = cursor.fetchone()
            
            if not epargne:
                cursor.execute('''
                    INSERT INTO epargne (membre_id, solde_actuel, depot_total, created_at, updated_at)
                    VALUES (?, ?, ?, date('now'), date('now'))
                ''', (membre_id, montant, montant))
                epargne_id = cursor.lastrowid
                nouveau_solde = montant
            else:
                epargne_id = epargne['id']
                nouveau_solde = epargne['solde_actuel'] + montant
                cursor.execute('''
                    UPDATE epargne 
                    SET solde_actuel = ?, depot_total = depot_total + ?, updated_at = date('now')
                    WHERE id = ?
                ''', (nouveau_solde, montant, epargne_id))
            
            cursor.execute('''
                INSERT INTO operations_epargne 
                (epargne_id, type_operation, montant, date_operation, description, seance_id, solde_apres)
                VALUES (?, 'depot', ?, date('now'), ?, ?, ?)
            ''', (epargne_id, montant, description, seance_id, nouveau_solde))
            
            conn.commit()
            return True, f"Dépôt de {montant:,.0f} FCFA effectué"
            
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()
    
    @staticmethod
    def retrait(membre_id, montant, description="", seance_id=None):
        """Effectue un retrait sur l'épargne"""
        if montant <= 0:
            return False, "Le montant doit être positif"
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("BEGIN IMMEDIATE")
            
            cursor.execute("SELECT * FROM epargne WHERE membre_id = ?", (membre_id,))
            epargne = cursor.fetchone()
            
            if not epargne or epargne['solde_actuel'] < montant:
                return False, "Solde d'épargne insuffisant"
            
            epargne_id = epargne['id']
            nouveau_solde = epargne['solde_actuel'] - montant
            
            cursor.execute('''
                UPDATE epargne 
                SET solde_actuel = ?, retrait_total = retrait_total + ?, updated_at = date('now')
                WHERE id = ?
            ''', (nouveau_solde, montant, epargne_id))
            
            cursor.execute('''
                INSERT INTO operations_epargne 
                (epargne_id, type_operation, montant, date_operation, description, seance_id, solde_apres)
                VALUES (?, 'retrait', ?, date('now'), ?, ?, ?)
            ''', (epargne_id, montant, description, seance_id, nouveau_solde))
            
            conn.commit()
            return True, f"Retrait de {montant:,.0f} FCFA effectué"
            
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()

# ============================================
# CLASSE FONDSMANAGER
# ============================================

class FondsManager:
    """Gestionnaire des opérations de fonds de caisse"""
    
    MONTANT_BASE = 100000
    
    @staticmethod
    def get_solde(membre_id):
        """Récupère le solde du fonds de caisse"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT solde_actuel FROM fonds_caisse WHERE membre_id = ?", (membre_id,))
        result = cursor.fetchone()
        conn.close()
        return result['solde_actuel'] if result else 0
    
    @staticmethod
    def debiter(membre_id, montant, description="", evenement_id=None, seance_id=None):
        """Débite le fonds de caisse"""
        if montant <= 0:
            return False, "Le montant doit être positif"
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("BEGIN IMMEDIATE")
            
            cursor.execute("SELECT * FROM fonds_caisse WHERE membre_id = ?", (membre_id,))
            fonds = cursor.fetchone()
            
            if not fonds or fonds['solde_actuel'] < montant:
                return False, "Solde du fonds de caisse insuffisant"
            
            nouveau_solde = fonds['solde_actuel'] - montant
            
            cursor.execute('''
                UPDATE fonds_caisse 
                SET solde_actuel = ?, date_derniere_mise_a_jour = date('now')
                WHERE id = ?
            ''', (nouveau_solde, fonds['id']))
            
            cursor.execute('''
                INSERT INTO operations_fonds_caisse 
                (fonds_id, type_operation, montant, date_operation, description, evenement_id, seance_id, solde_apres)
                VALUES (?, 'debit', ?, date('now'), ?, ?, ?, ?)
            ''', (fonds['id'], montant, description, evenement_id, seance_id, nouveau_solde))
            
            conn.commit()
            return True, f"Débit de {montant:,.0f} FCFA effectué"
            
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()
    
    @staticmethod
    def crediter(membre_id, montant, description="", evenement_id=None, seance_id=None):
        """Crédite le fonds de caisse"""
        if montant <= 0:
            return False, "Le montant doit être positif"
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("BEGIN IMMEDIATE")
            
            cursor.execute("SELECT * FROM fonds_caisse WHERE membre_id = ?", (membre_id,))
            fonds = cursor.fetchone()
            
            if not fonds:
                cursor.execute('''
                    INSERT INTO fonds_caisse (membre_id, montant_base, solde_actuel, date_creation, date_derniere_mise_a_jour)
                    VALUES (?, ?, ?, date('now'), date('now'))
                ''', (membre_id, FondsManager.MONTANT_BASE, FondsManager.MONTANT_BASE))
                nouveau_solde = FondsManager.MONTANT_BASE + montant
                fonds_id = cursor.lastrowid
                cursor.execute('''
                    UPDATE fonds_caisse SET solde_actuel = ? WHERE id = ?
                ''', (nouveau_solde, fonds_id))
            else:
                nouveau_solde = fonds['solde_actuel'] + montant
                cursor.execute('''
                    UPDATE fonds_caisse 
                    SET solde_actuel = ?, date_derniere_mise_a_jour = date('now')
                    WHERE id = ?
                ''', (nouveau_solde, fonds['id']))
                fonds_id = fonds['id']
            
            cursor.execute('''
                INSERT INTO operations_fonds_caisse 
                (fonds_id, type_operation, montant, date_operation, description, evenement_id, seance_id, solde_apres)
                VALUES (?, 'credit', ?, date('now'), ?, ?, ?, ?)
            ''', (fonds_id, montant, description, evenement_id, seance_id, nouveau_solde))
            
            conn.commit()
            return True, f"Crédit de {montant:,.0f} FCFA effectué"
            
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()

# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def get_statistiques_globales():
    """Récupère les statistiques globales de l'application"""
    conn = get_db()
    cursor = conn.cursor()
    
    stats = {
        'total_membres': 0,
        'total_epargne': 0,
        'total_fonds': 0,
        'total_prets': 0,
        'total_cotisations': 0,
        'total_amendes': 0,
        'tresorerie': 0
    }
    
    try:
        cursor.execute("SELECT COUNT(*) FROM membres WHERE statut='actif'")
        stats['total_membres'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(solde_actuel), 0) FROM epargne")
        stats['total_epargne'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(solde_actuel), 0) FROM fonds_caisse")
        stats['total_fonds'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(montant_restant), 0) FROM prets WHERE statut='en_cours'")
        stats['total_prets'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(montant_paye), 0) FROM cotisation_membres")
        stats['total_cotisations'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(montant_amende), 0) FROM sanctions WHERE statut='appliquee'")
        stats['total_amendes'] = cursor.fetchone()[0]
        
        stats['tresorerie'] = (stats['total_fonds'] + stats['total_epargne'] + 
                               stats['total_cotisations'] + stats['total_amendes'] - 
                               stats['total_prets'])
        
    except Exception as e:
        print(f"Erreur dans get_statistiques_globales: {e}")
    
    finally:
        conn.close()
    
    return stats

    def a_compte_epargne(self):
        """Vérifie si le membre a un compte épargne"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM epargne WHERE membre_id = ?", (self.id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def creer_compte_epargne(self):
        """Crée un compte épargne pour le membre"""
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO epargne (membre_id, solde_actuel, depot_total, retrait_total, created_at, updated_at)
                VALUES (?, 0, 0, 0, date('now'), date('now'))
            ''', (self.id,))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()


# ============================================
# CLASSE PRETMANAGER AVEC NOUVELLES FONCTIONS
# ============================================

class PretManager:
    
    @staticmethod
    def verifier_conditions_approfondies(membre_id, montant_demande):
        """
        Vérifie toutes les conditions pour l'octroi d'un prêt
        Retourne (bool, message, conditions_detaillees)
        """
        conn = get_db()
        cursor = conn.cursor()
        
        conditions = {
            'epargne_suffisante': False,
            'montant_max': 0,
            'epargne_actuelle': 0,
            'cotisations_a_jour': False,
            'dernier_paiement': None,
            'prets_en_cours': 0,
            'sanctions_recentes': 0
        }
        messages = []
        
        try:
            # 1. Vérifier l'épargne
            cursor.execute('SELECT solde_actuel FROM epargne WHERE membre_id = ?', (membre_id,))
            epargne = cursor.fetchone()
            epargne_actuelle = epargne['solde_actuel'] if epargne else 0
            montant_max = epargne_actuelle * 2
            conditions['epargne_actuelle'] = epargne_actuelle
            conditions['montant_max'] = montant_max
            
            if montant_demande <= montant_max:
                conditions['epargne_suffisante'] = True
                messages.append(f"✅ Montant demandé ≤ 2× épargne ({montant_max:,.0f} FCFA)")
            else:
                messages.append(f"❌ Montant demandé > 2× épargne (max {montant_max:,.0f} FCFA)")
            
            # 2. Vérifier les cotisations à jour (dernier paiement < 30 jours)
            cursor.execute('''
                SELECT date_ajout, montant_paye 
                FROM cotisation_membres 
                WHERE membre_id = ? AND a_cotise = 1
                ORDER BY date_ajout DESC
                LIMIT 1
            ''', (membre_id,))
            dernier_paiement = cursor.fetchone()
            
            if dernier_paiement:
                date_dernier = datetime.strptime(dernier_paiement['date_ajout'], '%Y-%m-%d')
                jours_ecoules = (datetime.now() - date_dernier).days
                conditions['dernier_paiement'] = jours_ecoules
                
                if jours_ecoules <= 30:
                    conditions['cotisations_a_jour'] = True
                    messages.append(f"✅ Cotisations à jour (dernier paiement il y a {jours_ecoules} jours)")
                else:
                    messages.append(f"❌ Cotisations en retard ({jours_ecoules} jours sans paiement)")
            else:
                messages.append("❌ Aucune cotisation enregistrée")
            
            # 3. Vérifier les prêts en cours
            cursor.execute('''
                SELECT COUNT(*) as nb, SUM(montant_restant) as total
                FROM prets 
                WHERE membre_id = ? AND statut IN ('en_cours', 'en_retard')
            ''', (membre_id,))
            prets = cursor.fetchone()
            conditions['prets_en_cours'] = prets['nb'] if prets else 0
            
            if conditions['prets_en_cours'] == 0:
                messages.append("✅ Aucun prêt en cours")
            else:
                messages.append(f"❌ Vous avez {prets['nb']} prêt(s) en cours (total restant: {prets['total']:,.0f} FCFA)")
            
            # 4. Vérifier les sanctions récentes (3 derniers mois)
            trois_mois = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*) as nb 
                FROM sanctions 
                WHERE membre_id = ? AND date_sanction >= ? AND statut = 'appliquee'
            ''', (membre_id, trois_mois))
            sanctions = cursor.fetchone()
            conditions['sanctions_recentes'] = sanctions['nb'] if sanctions else 0
            
            if conditions['sanctions_recentes'] <= 2:
                messages.append(f"✅ {conditions['sanctions_recentes']} sanction(s) récente(s)")
            else:
                messages.append(f"❌ Trop de sanctions récentes ({conditions['sanctions_recentes']})")
            
        finally:
            conn.close()
        
        # Vérifier si toutes les conditions sont remplies
        toutes_remplies = all([
            conditions['epargne_suffisante'],
            conditions['cotisations_a_jour'],
            conditions['prets_en_cours'] == 0,
            conditions['sanctions_recentes'] <= 2
        ])
        
        if toutes_remplies:
            return True, "✅ Vous remplissez toutes les conditions pour un prêt", conditions
        else:
            return False, "\n".join(messages), conditions
    
    @staticmethod
    def demander_pret(membre_id, montant, duree_mois, motif, seance_id=None):
        """
        Demande de prêt avec vérification automatique et prélèvement
        """
        # Vérifier les conditions
        peut, message, conditions = PretManager.verifier_conditions_approfondies(membre_id, montant)
        
        if not peut:
            return False, message, None
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("BEGIN IMMEDIATE")
            
            # Générer un numéro de demande unique
            cursor.execute("SELECT COUNT(*) FROM demandes_pret")
            count = cursor.fetchone()[0] + 1
            numero_demande = f"DEM-{datetime.now().strftime('%Y%m')}-{str(count).zfill(4)}"
            
            # Créer la demande
            cursor.execute('''
                INSERT INTO demandes_pret 
                (numero_demande, membre_id, montant_demande, duree_mois, motif, date_demande, seance_id, statut)
                VALUES (?, ?, ?, ?, ?, date('now'), ?, 'en_attente')
            ''', (numero_demande, membre_id, montant, duree_mois, motif, seance_id))
            
            demande_id = cursor.lastrowid
            conn.commit()
            
            # Créer une alerte pour l'administrateur
            cursor.execute('''
                INSERT INTO alertes (type_alerte, message, date_alerte, lien_action, statut)
                VALUES ('demande_pret', ?, date('now'), ?, 'non_lu')
            ''', (f"Nouvelle demande de prêt de {montant:,.0f} FCFA de {membre_id}", f"/prets/validation/{demande_id}"))
            
            conn.commit()
            
            return True, f"✅ Demande {numero_demande} créée avec succès. En attente de validation.", demande_id
            
        except Exception as e:
            conn.rollback()
            return False, f"❌ Erreur: {str(e)}", None
        finally:
            conn.close()
    
    @staticmethod
    def approuver_pret(demande_id, montant_accorde=None, taux_interet=5, seance_id=None):
        """
        Approuve une demande et crée le prêt avec prélèvement dans la trésorerie
        """
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("BEGIN IMMEDIATE")
            
            # Récupérer la demande
            cursor.execute('''
                SELECT d.*, m.nom, m.prenom, e.solde_actuel as epargne
                FROM demandes_pret d
                JOIN membres m ON d.membre_id = m.id
                LEFT JOIN epargne e ON m.id = e.membre_id
                WHERE d.id = ?
            ''', (demande_id,))
            demande = cursor.fetchone()
            
            if not demande or demande['statut'] != 'en_attente':
                return False, "Demande non trouvée ou déjà traitée"
            
            # Déterminer le montant accordé
            if montant_accorde is None:
                montant_accorde = demande['montant_demande']
            
            # Vérifier à nouveau les conditions
            peut, message, conditions = PretManager.verifier_conditions_approfondies(
                demande['membre_id'], montant_accorde
            )
            
            if not peut:
                return False, f"Conditions non remplies: {message}"
            
            # Calculer le montant total avec intérêts
            montant_total = montant_accorde * (1 + taux_interet / 100)
            date_octroi = datetime.now().strftime('%Y-%m-%d')
            date_echeance = (datetime.now() + timedelta(days=demande['duree_mois'] * 30)).strftime('%Y-%m-%d')
            
            # Générer numéro de prêt
            cursor.execute("SELECT COUNT(*) FROM prets")
            count = cursor.fetchone()[0] + 1
            numero_pret = f"PRET-{datetime.now().strftime('%Y%m')}-{str(count).zfill(4)}"
            
            # Créer le prêt
            cursor.execute('''
                INSERT INTO prets 
                (numero_pret, demande_id, membre_id, montant_principal, taux_interet, 
                 montant_total, montant_restant, date_octroi, date_echeance, duree_mois, 
                 type_pret, description, statut, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'standard', ?, 'en_cours', date('now'))
            ''', (numero_pret, demande_id, demande['membre_id'], montant_accorde, taux_interet,
                  montant_total, montant_total, date_octroi, date_echeance, demande['duree_mois'],
                  demande['motif']))
            
            pret_id = cursor.lastrowid
            
            # ========== PRÉLÈVEMENT DANS LA TRÉSORERIE ==========
            # Créer une opération de prélèvement dans le fonds de caisse du membre
            cursor.execute('SELECT * FROM fonds_caisse WHERE membre_id = ?', (demande['membre_id'],))
            fonds_caisse = cursor.fetchone()
            
            if fonds_caisse:
                nouveau_solde = fonds_caisse['solde_actuel'] + montant_accorde
                cursor.execute('''
                    UPDATE fonds_caisse 
                    SET solde_actuel = ?, date_derniere_mise_a_jour = date('now')
                    WHERE membre_id = ?
                ''', (nouveau_solde, demande['membre_id']))
                
                # Enregistrer l'opération
                cursor.execute('''
                    INSERT INTO operations_fonds_caisse 
                    (fonds_id, type_operation, montant, date_operation, description, pret_id, seance_id, solde_apres)
                    VALUES ((SELECT id FROM fonds_caisse WHERE membre_id = ?), 'pret_recu', ?, date('now'), ?, ?, ?, ?)
                ''', (demande['membre_id'], montant_accorde, f"Réception prêt {numero_pret}", pret_id, seance_id, nouveau_solde))
            else:
                # Créer un fonds de caisse si inexistant
                cursor.execute('''
                    INSERT INTO fonds_caisse (membre_id, montant_base, solde_actuel, date_creation, date_derniere_mise_a_jour)
                    VALUES (?, 100000, ?, date('now'), date('now'))
                ''', (demande['membre_id'], montant_accorde))
            
            # Créer les échéances
            montant_par_echeance = montant_total / demande['duree_mois']
            for i in range(1, demande['duree_mois'] + 1):
                date_echeance_i = (datetime.now() + timedelta(days=i * 30)).strftime('%Y-%m-%d')
                cursor.execute('''
                    INSERT INTO echeances_pret 
                    (pret_id, numero_echeance, montant_echeance, date_echeance, seance_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (pret_id, i, montant_par_echeance, date_echeance_i, seance_id))
            
            # Mettre à jour la demande
            cursor.execute('''
                UPDATE demandes_pret 
                SET statut = 'approuve', montant_accorde = ?, taux_interet = ?, 
                    date_decision = date('now')
                WHERE id = ?
            ''', (montant_accorde, taux_interet, demande_id))
            
            # Créer une alerte pour le membre
            cursor.execute('''
                INSERT INTO alertes (membre_id, type_alerte, message, date_alerte, lien_action, statut)
                VALUES (?, 'pret_approuve', ?, date('now'), ?, 'non_lu')
            ''', (demande['membre_id'], f"✅ Votre prêt {numero_pret} a été approuvé !", f"/prets/{pret_id}"))
            
            conn.commit()
            return True, f"✅ Prêt {numero_pret} accordé avec succès", pret_id
            
        except Exception as e:
            conn.rollback()
            return False, f"❌ Erreur: {str(e)}", None
        finally:
            conn.close()


    @staticmethod
    def get_statistiques():
        """Retourne les statistiques globales des prêts"""
        conn = get_db()
        cursor = conn.cursor()
        
        stats = {
            'total_prets': 0,
            'prets_en_cours': 0,
            'prets_rembourses': 0,
            'prets_en_retard': 0,
            'montant_total_emprunte': 0,
            'montant_total_avec_interets': 0,
            'montant_rembourse': 0,
            'montant_restant': 0,
            'taux_remboursement': 0
        }
        
        # Récupérer les statistiques des prêts
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN statut = 'en_cours' THEN 1 ELSE 0 END) as en_cours,
                SUM(CASE WHEN statut = 'rembourse' THEN 1 ELSE 0 END) as rembourses,
                SUM(montant_principal) as total_principal,
                SUM(montant_total) as total_avec_interets,
                SUM(montant_restant) as total_restant
            FROM prets
        ''')
        result = cursor.fetchone()
        
        if result:
            stats['total_prets'] = result['total'] or 0
            stats['prets_en_cours'] = result['en_cours'] or 0
            stats['prets_rembourses'] = result['rembourses'] or 0
            stats['montant_total_emprunte'] = result['total_principal'] or 0
            stats['montant_total_avec_interets'] = result['total_avec_interets'] or 0
            stats['montant_restant'] = result['total_restant'] or 0
            
            # Calcul du montant déjà remboursé
            stats['montant_rembourse'] = stats['montant_total_avec_interets'] - stats['montant_restant']
            
            # Calculer les prêts en retard
            cursor.execute('''
                SELECT COUNT(DISTINCT pret_id) as nb
                FROM echeances_pret
                WHERE statut = 'en_attente' AND date_echeance < date('now')
            ''')
            stats['prets_en_retard'] = cursor.fetchone()['nb'] or 0
            
            # Taux de remboursement
            if stats['montant_total_avec_interets'] > 0:
                stats['taux_remboursement'] = (stats['montant_rembourse'] / stats['montant_total_avec_interets']) * 100
        
        conn.close()
        return stats      