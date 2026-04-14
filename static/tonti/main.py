# ============================================
# 1. IMPORTS
# ============================================
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, Response, send_file
from database import get_db, init_db
from models import Membre, EpargneManager, FondsManager, PretManager, get_statistiques_globales
from report_generator import ReportGenerator, ExportManager
import os
import json
import csv
from io import StringIO
from datetime import datetime, timedelta
import sqlite3
import random
import uuid

# ============================================
# 2. CRÉATION DE L'APPLICATION (UNE SEULE FOIS)
# ============================================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre_cle_secrete_tontine_2026'

# ============================================
# 3. CONTEXT PROCESSOR (UNE SEULE FOIS)
# ============================================
@app.context_processor
def inject_now():
    return {'now': datetime.now}

# ============================================
# 4. INITIALISATION DE LA BASE (UNE SEULE FOIS)
# ============================================
with app.app_context():
    init_db()

# ============================================
# 5. PAGE D'ACCUEIL
# ============================================
@app.route('/')
def index():
    """Page d'accueil avec les 10 boutons"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Récupérer quelques statistiques
    cursor.execute("SELECT COUNT(*) FROM membres WHERE statut='actif'")
    nb_membres = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM seances WHERE statut IN ('prevue', 'en_cours')")
    nb_seances = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(solde_actuel) FROM fonds_caisse")
    fonds_total = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(solde_actuel) FROM epargne")
    epargne_total = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(montant_paye) FROM cotisation_membres")
    cotisations_total = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(montant_restant) FROM prets WHERE statut = 'en_cours'")
    prets_en_cours = cursor.fetchone()[0] or 0
    
    conn.close()
    
    stats = {
        'membres': nb_membres,
        'seances': nb_seances,
        'fonds': fonds_total,
        'epargne': epargne_total,
        'cotisations': cotisations_total,
        'prets': prets_en_cours,
        'tresorerie': fonds_total + epargne_total + cotisations_total - prets_en_cours
    }
    
    return render_template('index.html', stats=stats)

# ============================================
# 6. ROUTE DE TEST
# ============================================
@app.route('/test')
def test():
    return "Le serveur fonctionne !"

# ============================================
# 7. ROUTE DEBUG
# ============================================
@app.route('/debug-routes')
def debug_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append(f"{rule.endpoint}: {rule}")
    return "<br>".join(sorted(routes))

# ============================================
# 8. ROUTES POUR LES BILANS ET RAPPORTS
# ============================================
@app.route('/bilans/seance/<int:seance_id>')
def bilan_seance(seance_id):
    """Affiche le bilan d'une séance"""
    bilan = ReportGenerator.generer_bilan_seance(seance_id)
    
    if not bilan:
        flash('❌ Séance non trouvée', 'error')
        return redirect(url_for('liste_seances'))
    
    # Sauvegarder le bilan en base de données
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO bilans_seance 
        (seance_id, date_generation, nb_presents, nb_absents, nb_retards, taux_presence,
         total_cotisations, total_prets, total_sanctions, evolution_fonds, commentaires)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        seance_id, bilan['date_generation'],
        bilan['presences']['presents'], bilan['presences']['absents'],
        bilan['presences']['retards'], bilan['taux_presence'],
        bilan['cotisations']['total_cotisations'] or 0,
        bilan['prets']['total_prets'] or 0,
        bilan['sanctions']['total_amendes'] or 0,
        bilan['fonds']['variation'] or 0,
        f"Bilan généré automatiquement - {bilan['date_generation']}"
    ))
    conn.commit()
    conn.close()
    
    return render_template('bilans/bilan_seance.html', bilan=bilan)

@app.route('/bilans/membre/<int:membre_id>')
def bilan_membre(membre_id):
    """Affiche le bilan d'un membre"""
    periode_debut = request.args.get('debut')
    periode_fin = request.args.get('fin')
    
    if periode_debut:
        periode_debut = datetime.strptime(periode_debut, '%Y-%m-%d').strftime('%Y-%m-%d')
    if periode_fin:
        periode_fin = datetime.strptime(periode_fin, '%Y-%m-%d').strftime('%Y-%m-%d')
    
    bilan = ReportGenerator.generer_bilan_membre(membre_id, periode_debut, periode_fin)
    
    if not bilan:
        flash('❌ Membre non trouvé', 'error')
        return redirect(url_for('membres'))
    
    # Sauvegarder le bilan
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO bilans_membre 
        (membre_id, date_generation, periode_debut, periode_fin, total_cotise, total_epargne,
         solde_fonds, solde_epargne, prets_en_cours, montant_prets_en_cours,
         prets_rembourses, montant_prets_rembourses, sanctions_recues, montant_sanctions, taux_presence)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        membre_id, bilan['date_generation'],
        bilan['periode']['debut'], bilan['periode']['fin'],
        bilan['cotisations']['total_cotise'] or 0,
        bilan['epargne']['depots'] or 0,
        bilan['fonds']['solde_actuel'] or 0,
        bilan['epargne']['solde_actuel'] or 0,
        bilan['prets']['nb_prets'] or 0,
        bilan['prets']['total_restant'] or 0,
        bilan['remboursements']['nb_remboursements'] or 0,
        bilan['remboursements']['total_rembourse'] or 0,
        bilan['sanctions']['nb_sanctions'] or 0,
        bilan['sanctions']['total_amendes'] or 0,
        bilan['taux_presence']
    ))
    conn.commit()
    conn.close()
    
    return render_template('bilans/bilan_membre.html', bilan=bilan)

@app.route('/rapports/financier')
def rapport_financier():
    """Affiche le rapport financier global"""
    rapport = ReportGenerator.generer_rapport_financier()
    return render_template('bilans/rapports_financiers.html', rapport=rapport)

@app.route('/rapports/analyse-credit')
def analyse_credit():
    """Affiche l'analyse des crédits"""
    analyse = ReportGenerator.generer_analyse_credit()
    return render_template('bilans/analyse_credit.html', analyse=analyse)

@app.route('/rapports/export')
def export_rapport():
    """Exporte un rapport au format CSV ou JSON"""
    type_rapport = request.args.get('type', 'financier')
    format_export = request.args.get('format', 'csv')
    
    if type_rapport == 'financier':
        rapport = ReportGenerator.generer_rapport_financier()
        filename = f"rapport_financier_{datetime.now().strftime('%Y%m%d')}"
    elif type_rapport == 'credit':
        rapport = ReportGenerator.generer_analyse_credit()
        filename = f"analyse_credit_{datetime.now().strftime('%Y%m%d')}"
    else:
        flash('❌ Type de rapport invalide', 'error')
        return redirect(url_for('dashboard'))
    
    if format_export == 'csv':
        output = StringIO()
        writer = csv.writer(output)
        
        if type_rapport == 'financier':
            writer.writerow(['Rapport Financier', rapport['date_generation']])
            writer.writerow([])
            writer.writerow(['Indicateur', 'Valeur'])
            writer.writerow(['Total cotisations', f"{rapport['stats']['total_cotisations']:,.0f} FCFA"])
            writer.writerow(['Total épargne', f"{rapport['stats']['total_epargne']:,.0f} FCFA"])
            writer.writerow(['Total fonds', f"{rapport['stats']['total_fonds']:,.0f} FCFA"])
            writer.writerow(['Prêts en cours', f"{rapport['stats']['total_prets']:,.0f} FCFA"])
            writer.writerow(['Trésorerie', f"{rapport['stats']['tresorerie']:,.0f} FCFA"])
        
        csv_content = output.getvalue()
        return Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename}.csv"}
        )
    else:
        json_content = ExportManager.exporter_json(rapport)
        return Response(
            json_content,
            mimetype="application/json",
            headers={"Content-disposition": f"attachment; filename={filename}.json"}
        )

@app.route('/bilans/historique')
def historique_bilans():
    """Historique des bilans générés"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT bs.*, s.numero_seance, s.date_seance, s.theme
        FROM bilans_seance bs
        JOIN seances s ON bs.seance_id = s.id
        ORDER BY bs.date_generation DESC
        LIMIT 20
    ''')
    bilans_seance = cursor.fetchall()
    
    cursor.execute('''
        SELECT bm.*, m.nom, m.prenom
        FROM bilans_membre bm
        JOIN membres m ON bm.membre_id = m.id
        ORDER BY bm.date_generation DESC
        LIMIT 20
    ''')
    bilans_membre = cursor.fetchall()
    
    conn.close()
    
    return render_template('bilans/historique.html',
                         bilans_seance=bilans_seance,
                         bilans_membre=bilans_membre)

# ============================================
# 9. ROUTES POUR LES MEMBRES
# ============================================
@app.route('/membres')
def membres():
    """Page de gestion des membres"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM membres ORDER BY date_adhesion DESC")
    membres = cursor.fetchall()
    conn.close()
    return render_template('membres.html', membres=membres)

@app.route('/membres/ajouter', methods=['POST'])
def ajouter_membre():
    """Ajouter un nouveau membre avec création automatique du compte épargne"""
    nom = request.form['nom']
    prenom = request.form['prenom']
    telephone = request.form['telephone']
    email = request.form['email']
    date_adhesion = datetime.now().strftime('%Y-%m-%d')
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("BEGIN IMMEDIATE")
        
        # Insérer le membre
        cursor.execute(
            "INSERT INTO membres (nom, prenom, telephone, email, date_adhesion) VALUES (?, ?, ?, ?, ?)",
            (nom, prenom, telephone, email, date_adhesion)
        )
        membre_id = cursor.lastrowid
        
        # Créer automatiquement le compte épargne
        cursor.execute('''
            INSERT INTO epargne (membre_id, solde_actuel, depot_total, retrait_total, created_at, updated_at)
            VALUES (?, 0, 0, 0, date('now'), date('now'))
        ''', (membre_id,))
        
        # Créer automatiquement le fonds de caisse (si nécessaire)
        cursor.execute('''
            INSERT INTO fonds_caisse (membre_id, montant_base, solde_actuel, date_creation, date_derniere_mise_a_jour)
            VALUES (?, 100000, 100000, date('now'), date('now'))
        ''', (membre_id,))
        
        conn.commit()
        flash(f'✅ Membre {prenom} {nom} ajouté avec succès. Compte épargne créé automatiquement.', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'❌ Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('membres'))

@app.route('/membres/modifier/<int:id>', methods=['GET', 'POST'])
def modifier_membre(id):
    """Modifier un membre existant"""
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        telephone = request.form['telephone']
        email = request.form['email']
        statut = request.form['statut']
        
        cursor.execute('''
            UPDATE membres 
            SET nom=?, prenom=?, telephone=?, email=?, statut=?
            WHERE id=?
        ''', (nom, prenom, telephone, email, statut, id))
        conn.commit()
        conn.close()
        
        return redirect(url_for('membres'))
    else:
        cursor.execute("SELECT * FROM membres WHERE id=?", (id,))
        membre = cursor.fetchone()
        conn.close()
        
        if membre is None:
            return redirect(url_for('membres'))
        return render_template('modifier_membre.html', membre=membre)

@app.route('/membres/supprimer/<int:id>', methods=['GET', 'POST'])
def supprimer_membre(id):
    """Supprimer un membre"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT nom, prenom FROM membres WHERE id=?", (id,))
        membre = cursor.fetchone()
        
        if membre:
            nom_complet = f"{membre['prenom']} {membre['nom']}"
            cursor.execute("DELETE FROM membres WHERE id=?", (id,))
            conn.commit()
            flash(f'✅ {nom_complet} a été supprimé avec succès', 'success')
        else:
            flash('❌ Membre non trouvé', 'error')
    except Exception as e:
        flash(f'❌ Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('membres'))

@app.route('/membres/statut/<int:id>', methods=['POST'])
def changer_statut(id):
    """Changer le statut d'un membre"""
    try:
        data = request.get_json()
        nouveau_statut = data.get('statut')
        
        conn = get_db()
        cursor = conn.cursor()
        
        if nouveau_statut in ['actif', 'inactif']:
            cursor.execute("UPDATE membres SET statut=? WHERE id=?", (nouveau_statut, id))
            conn.commit()
            cursor.execute("SELECT nom, prenom FROM membres WHERE id=?", (id,))
            membre = cursor.fetchone()
            nom_complet = f"{membre['prenom']} {membre['nom']}"
            conn.close()
            
            return jsonify({
                'success': True, 
                'message': f"Statut de {nom_complet} changé avec succès"
            })
        else:
            return jsonify({'success': False, 'message': "Statut invalide"})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============================================
# 10. ROUTES POUR LES SÉANCES
# ============================================
def generer_numero_seance():
    """Génère un numéro de séance unique"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM seances")
    count = cursor.fetchone()[0] + 1
    conn.close()
    annee = datetime.now().strftime('%Y')
    mois = datetime.now().strftime('%m')
    return f"SE-{annee}{mois}-{str(count).zfill(3)}"

@app.route('/seances')
def liste_seances():
    """Liste de toutes les séances"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            s.*,
            (SELECT COUNT(*) FROM presences_seance WHERE seance_id = s.id AND est_present = 1) as presents,
            (SELECT COUNT(*) FROM presences_seance WHERE seance_id = s.id) as total_membres
        FROM seances s
        ORDER BY 
            CASE s.statut
                WHEN 'en_cours' THEN 1
                WHEN 'prevue' THEN 2
                WHEN 'terminee' THEN 3
                ELSE 4
            END,
            s.date_seance DESC
    ''')
    seances = cursor.fetchall()
    conn.close()
    
    return render_template('seances/liste_seances.html', seances=seances)

@app.route('/seances/ajouter', methods=['GET', 'POST'])
def ajouter_seance():
    """Ajouter une nouvelle séance"""
    if request.method == 'POST':
        conn = None
        try:
            date_seance = request.form['date_seance']
            heure_debut = request.form['heure_debut']
            theme = request.form['theme']
            lieu = request.form['lieu']
            ordre_du_jour = request.form['ordre_du_jour']
            
            numero_seance = generer_numero_seance()
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE")
            
            cursor.execute('''
                INSERT INTO seances 
                (numero_seance, date_seance, heure_debut, theme, lieu, ordre_du_jour, statut)
                VALUES (?, ?, ?, ?, ?, ?, 'prevue')
            ''', (numero_seance, date_seance, heure_debut, theme, lieu, ordre_du_jour))
            
            seance_id = cursor.lastrowid
            
            cursor.execute("SELECT id FROM membres WHERE statut = 'actif'")
            membres = cursor.fetchall()
            
            for membre in membres:
                cursor.execute('''
                    INSERT INTO presences_seance (seance_id, membre_id, est_present)
                    VALUES (?, ?, 0)
                ''', (seance_id, membre['id']))
            
            conn.commit()
            flash(f'✅ Séance {numero_seance} créée avec succès', 'success')
            return redirect(url_for('detail_seance', id=seance_id))
            
        except Exception as e:
            if conn:
                conn.rollback()
            flash(f'❌ Erreur: {str(e)}', 'error')
            return redirect(url_for('ajouter_seance'))
        finally:
            if conn:
                conn.close()
    
    return render_template('seances/ajouter_seance.html', now=datetime.now)

@app.route('/seances/<int:id>')
def detail_seance(id):
    """Détails d'une séance"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM seances WHERE id = ?', (id,))
    seance = cursor.fetchone()
    
    if not seance:
        flash('❌ Séance non trouvée', 'error')
        return redirect(url_for('liste_seances'))
    
    cursor.execute('''
        SELECT p.*, m.nom, m.prenom, m.telephone
        FROM presences_seance p
        JOIN membres m ON p.membre_id = m.id
        WHERE p.seance_id = ?
        ORDER BY m.nom, m.prenom
    ''', (id,))
    presences = cursor.fetchall()
    
    conn.close()
    
    return render_template('seances/detail_seance.html',
                         seance=seance,
                         presences=presences)

@app.route('/seances/<int:id>/cloturer', methods=['GET', 'POST'])
def cloturer_seance(id):
    """Clôturer une séance"""
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        compte_rendu = request.form['compte_rendu']
        heure_fin = request.form['heure_fin']
        
        cursor.execute('''
            UPDATE seances 
            SET statut = 'terminee', compte_rendu = ?, heure_fin = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (compte_rendu, heure_fin, id))
        
        conn.commit()
        conn.close()
        
        flash('✅ Séance clôturée avec succès', 'success')
        return redirect(url_for('detail_seance', id=id))
    
    cursor.execute('SELECT * FROM seances WHERE id = ?', (id,))
    seance = cursor.fetchone()
    conn.close()
    
    return render_template('seances/cloture_seance.html', seance=seance)

@app.route('/seances/<int:id>/presence', methods=['POST'])
def update_presence(id):
    """Mettre à jour la présence d'un membre"""
    membre_id = request.form['membre_id']
    est_present = request.form.get('est_present') == 'on'
    retard = request.form.get('retard') == 'on'
    heure_arrivee = request.form.get('heure_arrivee', '')
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE presences_seance 
        SET est_present = ?, retard = ?, heure_arrivee = ?
        WHERE seance_id = ? AND membre_id = ?
    ''', (est_present, retard, heure_arrivee, id, membre_id))
    
    conn.commit()
    conn.close()
    
    flash('✅ Présence mise à jour', 'success')
    return redirect(url_for('detail_seance', id=id))

# ============================================
# 11. ROUTES POUR LES COTISATIONS
# ============================================
@app.route('/cotisations')
def liste_cotisations():
    """Affiche la liste de toutes les cotisations"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Récupérer toutes les cotisations
    cursor.execute('''
        SELECT 
            c.*,
            COUNT(cm.membre_id) as nb_membres,
            SUM(CASE WHEN cm.a_cotise = 1 THEN 1 ELSE 0 END) as nb_cotise,
            COALESCE(SUM(cm.montant_paye), 0) as total_collecte
        FROM cotisations c
        LEFT JOIN cotisation_membres cm ON c.id = cm.cotisation_id
        GROUP BY c.id
        ORDER BY c.date_creation DESC
    ''')
    cotisations = cursor.fetchall()
    
    # Convertir en liste de dictionnaires et ajouter le taux de participation
    cotisations_list = []
    for c in cotisations:
        cotisation_dict = dict(c)
        nb_membres = cotisation_dict.get('nb_membres', 0) or 0
        nb_cotise = cotisation_dict.get('nb_cotise', 0) or 0
        if nb_membres > 0:
            cotisation_dict['taux_participation'] = round((nb_cotise / nb_membres) * 100, 2)
        else:
            cotisation_dict['taux_participation'] = 0
        cotisations_list.append(cotisation_dict)
    
    # Statistiques globales
    total_cotisations = len(cotisations_list)
    montant_total_global = sum(c.get('montant_total', 0) for c in cotisations_list)
    total_collecte_global = sum(c.get('total_collecte', 0) for c in cotisations_list)
    
    # Taux moyen
    if total_cotisations > 0:
        taux_moyen = round(sum(c.get('taux_participation', 0) for c in cotisations_list) / total_cotisations, 2)
    else:
        taux_moyen = 0
    
    stats_globales = {
        'total_cotisations': total_cotisations,
        'montant_total_global': montant_total_global,
        'total_collecte_global': total_collecte_global,
        'taux_moyen': taux_moyen
    }
    
    conn.close()
    
    return render_template('cotisations/liste_cotisations.html', 
                         cotisations=cotisations_list,
                         stats_globales=stats_globales)

@app.route('/seances/<int:seance_id>/cotisation/<int:cotisation_id>/membre/<int:membre_id>/toggle', methods=['POST'])
def toggle_cotisation_membre_seance(seance_id, cotisation_id, membre_id):
    """Marquer qu'un membre a cotisé ou non pendant la séance"""
    data = request.get_json()
    a_cotise = data.get('a_cotise', False)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("BEGIN IMMEDIATE")
        
        # Récupérer le montant de la cotisation
        cursor.execute('SELECT montant_total FROM cotisations WHERE id = ?', (cotisation_id,))
        cotisation = cursor.fetchone()
        
        # Calculer le montant par membre (montant total / nombre de membres)
        cursor.execute("SELECT COUNT(*) FROM membres WHERE statut = 'actif'")
        nb_membres = cursor.fetchone()[0]
        montant_par_membre = cotisation['montant_total'] / nb_membres if nb_membres > 0 else 0
        
        # Mettre à jour la cotisation du membre
        cursor.execute('''
            UPDATE cotisation_membres 
            SET a_cotise = ?, montant_paye = ?
            WHERE cotisation_id = ? AND membre_id = ? AND seance_id = ?
        ''', (a_cotise, montant_par_membre if a_cotise else 0, cotisation_id, membre_id, seance_id))
        
        if cursor.rowcount == 0:
            # Si la ligne n'existe pas, l'insérer
            cursor.execute('''
                INSERT INTO cotisation_membres (cotisation_id, membre_id, date_ajout, a_cotise, montant_paye, seance_id)
                VALUES (?, ?, date('now'), ?, ?, ?)
            ''', (cotisation_id, membre_id, a_cotise, montant_par_membre if a_cotise else 0, seance_id))
        
        # Si le membre a cotisé, mettre à jour son fonds de caisse (optionnel)
        if a_cotise:
            cursor.execute('SELECT * FROM fonds_individuels WHERE membre_id = ?', (membre_id,))
            fonds = cursor.fetchone()
            
            if fonds:
                nouveau_solde = fonds['solde_actuel'] - montant_par_membre
                cursor.execute('''
                    UPDATE fonds_individuels 
                    SET solde_actuel = ?, date_derniere_mise_a_jour = date('now')
                    WHERE membre_id = ?
                ''', (nouveau_solde, membre_id))
                
                cursor.execute('''
                    INSERT INTO operations_fonds 
                    (fonds_id, type_operation, montant, date_operation, description, seance_id, solde_apres)
                    VALUES ((SELECT id FROM fonds_individuels WHERE membre_id = ?), 'cotisation', ?, date('now'), ?, ?, ?)
                ''', (membre_id, montant_par_membre, f"Cotisation séance {seance_id}", seance_id, nouveau_solde))
        
        conn.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()


@app.route('/cotisations/<int:id>')
def detail_cotisation(id):
    """Affiche les détails d'une cotisation"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Récupérer la cotisation
    cursor.execute('SELECT * FROM cotisations WHERE id = ?', (id,))
    cotisation = cursor.fetchone()
    
    if not cotisation:
        flash('❌ Cotisation non trouvée', 'error')
        return redirect(url_for('liste_cotisations'))
    
    # Récupérer les membres DEJA dans cette cotisation
    cursor.execute('''
        SELECT m.*, cm.date_ajout, cm.a_cotise, cm.montant_paye
        FROM membres m
        INNER JOIN cotisation_membres cm ON m.id = cm.membre_id
        WHERE cm.cotisation_id = ?
        ORDER BY m.nom, m.prenom
    ''', (id,))
    membres = cursor.fetchall()
    
    # Récupérer les membres DISPONIBLES (pas encore dans la cotisation)
    cursor.execute('''
        SELECT m.*, COALESCE(fi.solde_actuel, 0) as solde_fonds
        FROM membres m
        LEFT JOIN fonds_individuels fi ON m.id = fi.membre_id
        WHERE m.statut = 'actif'
        AND m.id NOT IN (
            SELECT membre_id FROM cotisation_membres WHERE cotisation_id = ?
        )
        ORDER BY m.nom, m.prenom
    ''', (id,))
    membres_disponibles = cursor.fetchall()
    
    # Calculer les statistiques
    cursor.execute('''
        SELECT 
            COUNT(*) as total_membres,
            SUM(CASE WHEN a_cotise = 1 THEN 1 ELSE 0 END) as nb_cotise,
            SUM(montant_paye) as total_paye
        FROM cotisation_membres
        WHERE cotisation_id = ?
    ''', (id,))
    stats = cursor.fetchone()
    
    conn.close()
    
    return render_template('cotisations/detail_cotisation.html', 
                         cotisation=cotisation, 
                         membres=membres,
                         membres_disponibles=membres_disponibles,
                         stats=stats)

@app.route('/cotisations/<int:id>/membres/ajouter', methods=['POST'])
def ajouter_membres_cotisation(id):
    """Ajoute des membres à une cotisation"""
    membres_ids = request.form.getlist('membres_ids')
    date_ajout = datetime.now().strftime('%Y-%m-%d')
    
    if not membres_ids:
        flash('❌ Veuillez sélectionner au moins un membre', 'warning')
        return redirect(url_for('detail_cotisation', id=id))
    
    conn = get_db()
    cursor = conn.cursor()
    
    for membre_id in membres_ids:
        cursor.execute('''
            INSERT OR IGNORE INTO cotisation_membres (cotisation_id, membre_id, date_ajout, a_cotise, montant_paye)
            VALUES (?, ?, ?, 0, 0)
        ''', (id, membre_id, date_ajout))
    
    conn.commit()
    conn.close()
    
    flash(f'✅ {len(membres_ids)} membre(s) ajouté(s) avec succès', 'success')
    return redirect(url_for('detail_cotisation', id=id))

@app.route('/cotisations/<int:id>/membres/supprimer', methods=['POST'])
def supprimer_membres_cotisation(id):
    """Supprime des membres d'une cotisation"""
    membres_ids = request.form.getlist('membres_ids')
    
    if not membres_ids:
        flash('❌ Veuillez sélectionner au moins un membre', 'warning')
        return redirect(url_for('detail_cotisation', id=id))
    
    conn = get_db()
    cursor = conn.cursor()
    
    placeholders = ','.join(['?' for _ in membres_ids])
    query = f'''
        DELETE FROM cotisation_membres 
        WHERE cotisation_id = ? AND membre_id IN ({placeholders})
    '''
    cursor.execute(query, [id] + membres_ids)
    nb_supprime = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    flash(f'✅ {nb_supprime} membre(s) retiré(s) avec succès', 'success')
    return redirect(url_for('detail_cotisation', id=id))

@app.route('/cotisations/<int:id>/membres/toggle/<int:membre_id>', methods=['POST'])
def toggle_cotisation_membre(id, membre_id):
    """Marque qu'un membre a cotisé ou non"""
    data = request.get_json()
    a_cotise = data.get('a_cotise', False)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE cotisation_membres 
        SET a_cotise = ?
        WHERE cotisation_id = ? AND membre_id = ?
    ''', (a_cotise, id, membre_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/cotisations/<int:id>/modifier', methods=['GET', 'POST'])
def modifier_cotisation(id):
    """Modifie une cotisation"""
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        nom = request.form['nom_cotisation']
        montant = float(request.form['montant_total'])
        
        cursor.execute('''
            UPDATE cotisations 
            SET nom_cotisation = ?, montant_total = ?
            WHERE id = ?
        ''', (nom, montant, id))
        
        conn.commit()
        conn.close()
        
        flash('✅ Cotisation modifiée avec succès', 'success')
        return redirect(url_for('detail_cotisation', id=id))
    
    cursor.execute('SELECT * FROM cotisations WHERE id = ?', (id,))
    cotisation = cursor.fetchone()
    conn.close()
    
    return render_template('cotisations/modifier_cotisation.html', cotisation=cotisation)

@app.route('/cotisations/<int:id>/supprimer')
def supprimer_cotisation(id):
    """Supprime une cotisation"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT nom_cotisation FROM cotisations WHERE id = ?', (id,))
    cotisation = cursor.fetchone()
    nom = cotisation['nom_cotisation'] if cotisation else 'Cotisation'
    
    cursor.execute('DELETE FROM cotisations WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash(f'✅ {nom} supprimée avec succès', 'success')
    return redirect(url_for('liste_cotisations'))

# ============================================
# 12. ROUTES POUR LES SANCTIONS
# ============================================
def generer_numero_sanction():
    """Génère un numéro de sanction unique"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sanctions")
    count = cursor.fetchone()[0] + 1
    conn.close()
    annee = datetime.now().strftime('%Y')
    mois = datetime.now().strftime('%m')
    return f"SAN-{annee}{mois}-{str(count).zfill(4)}"

@app.route('/sanctions')
def liste_sanctions():
    """Liste de toutes les sanctions"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            s.*,
            m.nom, m.prenom
        FROM sanctions s
        JOIN membres m ON s.membre_id = m.id
        ORDER BY s.date_sanction DESC
    ''')
    sanctions = cursor.fetchall()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN statut = 'appliquee' THEN 1 ELSE 0 END) as appliquees,
            SUM(montant_amende) as total_amendes
        FROM sanctions
    ''')
    stats = cursor.fetchone()
    
    conn.close()
    
    return render_template('sanctions/liste_sanctions.html', 
                         sanctions=sanctions, 
                         stats=stats)

@app.route('/sanctions/ajouter', methods=['GET', 'POST'])
def ajouter_sanction():
    """Ajouter une nouvelle sanction"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, nom, prenom FROM membres WHERE statut = "actif" ORDER BY nom, prenom')
    membres = cursor.fetchall()
    
    if request.method == 'POST':
        membre_id = request.form['membre_id']
        type_sanction = request.form['type_sanction']
        motif = request.form['motif']
        montant_amende = float(request.form.get('montant_amende', 0))
        
        numero_sanction = generer_numero_sanction()
        date_sanction = datetime.now().strftime('%Y-%m-%d')
        
        try:
            cursor.execute('''
                INSERT INTO sanctions 
                (numero_sanction, membre_id, type_sanction, motif, montant_amende, 
                 date_sanction, statut)
                VALUES (?, ?, ?, ?, ?, ?, 'appliquee')
            ''', (numero_sanction, membre_id, type_sanction, motif, montant_amende,
                  date_sanction))
            
            sanction_id = cursor.lastrowid
            conn.commit()
            flash(f'✅ Sanction {numero_sanction} ajoutée avec succès', 'success')
            return redirect(url_for('detail_sanction', id=sanction_id))
        except Exception as e:
            flash(f'❌ Erreur: {str(e)}', 'error')
        finally:
            conn.close()
    
    conn.close()
    return render_template('sanctions/ajouter_sanction.html', membres=membres)

@app.route('/sanctions/<int:id>')
def detail_sanction(id):
    """Détails d'une sanction"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.*, m.nom, m.prenom
        FROM sanctions s
        JOIN membres m ON s.membre_id = m.id
        WHERE s.id = ?
    ''', (id,))
    sanction = cursor.fetchone()
    conn.close()
    
    return render_template('sanctions/detail_sanction.html', sanction=sanction)

@app.route('/sanctions/<int:id>/modifier', methods=['GET', 'POST'])
def modifier_sanction(id):
    """Modifier une sanction"""
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        type_sanction = request.form['type_sanction']
        motif = request.form['motif']
        montant_amende = float(request.form.get('montant_amende', 0))
        statut = request.form['statut']
        
        try:
            cursor.execute('''
                UPDATE sanctions 
                SET type_sanction = ?, motif = ?, montant_amende = ?, statut = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (type_sanction, motif, montant_amende, statut, id))
            conn.commit()
            flash('✅ Sanction modifiée avec succès', 'success')
            return redirect(url_for('detail_sanction', id=id))
        except Exception as e:
            flash(f'❌ Erreur: {str(e)}', 'error')
        finally:
            conn.close()
    
    cursor.execute('SELECT * FROM sanctions WHERE id = ?', (id,))
    sanction = cursor.fetchone()
    conn.close()
    
    return render_template('sanctions/modifier_sanction.html', sanction=sanction)

@app.route('/sanctions/<int:id>/supprimer', methods=['POST'])
def supprimer_sanction(id):
    """Supprimer une sanction"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT numero_sanction FROM sanctions WHERE id = ?', (id,))
        sanction = cursor.fetchone()
        
        if sanction:
            cursor.execute('DELETE FROM sanctions WHERE id = ?', (id,))
            conn.commit()
            flash(f'✅ Sanction {sanction["numero_sanction"]} supprimée', 'success')
        else:
            flash('❌ Sanction non trouvée', 'error')
    except Exception as e:
        flash(f'❌ Erreur: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('liste_sanctions'))

@app.route('/sanctions/etat')
def etat_sanctions():
    """État récapitulatif des sanctions"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total_sanctions,
            SUM(CASE WHEN statut = 'appliquee' THEN 1 ELSE 0 END) as appliquees,
            SUM(montant_amende) as total_amendes
        FROM sanctions
    ''')
    stats = cursor.fetchone()
    
    cursor.execute('''
        SELECT type_sanction, COUNT(*) as nombre, SUM(montant_amende) as total
        FROM sanctions
        GROUP BY type_sanction
        ORDER BY nombre DESC
    ''')
    sanctions_par_type = cursor.fetchall()
    
    conn.close()
    
    return render_template('sanctions/etat_sanctions.html',
                         stats=stats,
                         sanctions_par_type=sanctions_par_type)

@app.route('/sanctions/exporter/csv')
def exporter_sanctions_csv():
    """Exporter les sanctions au format CSV"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            s.numero_sanction,
            m.nom || ' ' || m.prenom as membre,
            s.type_sanction,
            s.motif,
            s.montant_amende,
            s.date_sanction,
            s.statut
        FROM sanctions s
        JOIN membres m ON s.membre_id = m.id
        ORDER BY s.date_sanction DESC
    ''')
    sanctions = cursor.fetchall()
    conn.close()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Numéro', 'Membre', 'Type', 'Motif', 'Montant', 'Date', 'Statut'])
    
    for s in sanctions:
        writer.writerow([
            s[0], s[1], s[2], s[3], 
            f"{s[4]:,.0f} FCFA", s[5][:10], s[6]
        ])
    
    csv_content = output.getvalue()
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=sanctions.csv"}
    )

# ============================================
# 13. ROUTES POUR LES ÉVÉNEMENTS
# ============================================
@app.route('/evenements')
def liste_evenements():
    """Liste de tous les événements"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT e.*, COUNT(p.id) as nb_participants,
               COALESCE(SUM(p.montant_paye), 0) as total_collecte,
               (SELECT COUNT(*) FROM membres WHERE statut = 'actif') as total_membres
        FROM evenements e
        LEFT JOIN participations_evenement p ON e.id = p.evenement_id
        GROUP BY e.id
        ORDER BY e.date_evenement DESC
    ''')
    evenements = cursor.fetchall()
    conn.close()
    
    return render_template('evenements/liste_evenements.html', evenements=evenements)

@app.route('/evenements/ajouter', methods=['GET', 'POST'])
def ajouter_evenement():
    """Ajouter un nouvel événement"""
    if request.method == 'POST':
        nom = request.form['nom_evenement']
        type_evenement = request.form['type_evenement']
        montant = float(request.form['montant_fixe'])
        date_evenement = request.form['date_evenement']
        description = request.form.get('description', '')
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO evenements 
            (nom_evenement, type_evenement, montant_fixe, date_evenement, description, statut, created_at)
            VALUES (?, ?, ?, ?, ?, 'prevue', date('now'))
        ''', (nom, type_evenement, montant, date_evenement, description))
        
        evenement_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        flash(f'✅ Événement "{nom}" créé avec succès', 'success')
        return redirect(url_for('detail_evenement', id=evenement_id))
    
    return render_template('evenements/ajouter_evenement.html')

@app.route('/evenements/<int:id>')
def detail_evenement(id):
    """Détails d'un événement"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM evenements WHERE id = ?', (id,))
    evenement = cursor.fetchone()
    
    if not evenement:
        flash('❌ Événement non trouvé', 'error')
        return redirect(url_for('liste_evenements'))
    
    conn.close()
    
    return render_template('evenements/detail_evenement.html', evenement=evenement)

@app.route('/evenements/<int:id>/participer', methods=['POST'])
def participer_evenement(id):
    """Ajouter des participants à un événement"""
    membres_ids = request.form.getlist('membres_ids')
    mode = request.form.get('mode_participation', 'cotisation_directe')
    
    if not membres_ids:
        flash('❌ Veuillez sélectionner au moins un membre', 'warning')
        return redirect(url_for('detail_evenement', id=id))
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT montant_fixe FROM evenements WHERE id = ?', (id,))
    evenement = cursor.fetchone()
    montant = evenement['montant_fixe']
    
    date_actuelle = datetime.now().strftime('%Y-%m-%d')
    succes = 0
    
    for membre_id in membres_ids:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO participations_evenement 
                (evenement_id, membre_id, mode_participation, montant_paye, date_participation, a_participe)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (id, membre_id, mode, montant, date_actuelle))
            
            if cursor.rowcount > 0:
                succes += 1
        except:
            pass
    
    conn.commit()
    conn.close()
    
    if succes > 0:
        flash(f'✅ {succes} membre(s) ajouté(s) avec succès', 'success')
    
    return redirect(url_for('detail_evenement', id=id))

@app.route('/evenements/<int:id>/retirer-participants', methods=['POST'])
def retirer_participants_evenement(id):
    """Retirer des participants d'un événement"""
    membres_ids = request.form.getlist('membres_ids')
    
    if not membres_ids:
        flash('❌ Veuillez sélectionner au moins un membre', 'warning')
        return redirect(url_for('detail_evenement', id=id))
    
    conn = get_db()
    cursor = conn.cursor()
    
    placeholders = ','.join(['?' for _ in membres_ids])
    query = f'''
        DELETE FROM participations_evenement 
        WHERE evenement_id = ? AND membre_id IN ({placeholders})
    '''
    cursor.execute(query, [id] + membres_ids)
    nb_supprime = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    flash(f'✅ {nb_supprime} participant(s) retiré(s) avec succès', 'success')
    return redirect(url_for('detail_evenement', id=id))

# ============================================
# 14. ROUTES POUR LES PRÊTS
# ============================================
def generer_numero_pret():
    """Génère un numéro de prêt unique"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM prets")
    count = cursor.fetchone()[0] + 1
    conn.close()
    return f"PRET-{datetime.now().strftime('%Y%m')}-{str(count).zfill(4)}"



@app.route('/prets/<int:id>')
def detail_pret(id):
    """Détails d'un prêt"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            p.*,
            preteur.nom as nom_preteur, preteur.prenom as prenom_preteur,
            emprunteur.nom as nom_emprunteur, emprunteur.prenom as prenom_emprunteur
        FROM prets p
        JOIN membres preteur ON p.preteur_id = preteur.id
        JOIN membres emprunteur ON p.emprunteur_id = emprunteur.id
        WHERE p.id = ?
    ''', (id,))
    pret = cursor.fetchone()
    
    if not pret:
        flash('❌ Prêt non trouvé', 'error')
        return redirect(url_for('liste_prets'))
    
    cursor.execute('''
        SELECT * FROM echeances_pret 
        WHERE pret_id = ? 
        ORDER BY numero_echeance
    ''', (id,))
    echeances = cursor.fetchall()
    
    cursor.execute('''
        SELECT * FROM remboursements_pret 
        WHERE pret_id = ? 
        ORDER BY date_remboursement DESC
    ''', (id,))
    remboursements = cursor.fetchall()
    
    conn.close()
    
    return render_template('prets/detail_pret.html',
                         pret=pret,
                         echeances=echeances,
                         remboursements=remboursements)

# ============================================
# 15. ROUTES POUR L'ÉPARGNE
# ============================================
@app.route('/epargne')
def epargne_tableau_bord():
    """Tableau de bord de l'épargne"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Vérifier les membres sans compte épargne
    cursor.execute('''
        SELECT m.id, m.nom, m.prenom
        FROM membres m
        WHERE m.statut = 'actif'
        AND NOT EXISTS (SELECT 1 FROM epargne e WHERE e.membre_id = m.id)
    ''')
    membres_sans_compte = cursor.fetchall()
    
    if membres_sans_compte:
        flash(f'⚠️ Attention : {len(membres_sans_compte)} membre(s) n\'ont pas de compte épargne. Ils seront créés automatiquement.', 'warning')
        
        # Créer les comptes manquants
        for m in membres_sans_compte:
            cursor.execute('''
                INSERT INTO epargne (membre_id, solde_actuel, depot_total, retrait_total, created_at, updated_at)
                VALUES (?, 0, 0, 0, date('now'), date('now'))
            ''', (m['id'],))
        conn.commit()
        flash('✅ Tous les comptes épargne ont été créés automatiquement.', 'success')
    
    # Récupérer tous les comptes
    cursor.execute('''
        SELECT 
            e.*,
            m.nom, m.prenom, m.telephone,
            (SELECT COUNT(*) FROM operations_epargne WHERE epargne_id = e.id) as nb_operations
        FROM epargne e
        JOIN membres m ON e.membre_id = m.id
        WHERE m.statut = 'actif'
        ORDER BY e.solde_actuel DESC
    ''')
    comptes = cursor.fetchall()
    
    # Statistiques
    cursor.execute('''
        SELECT 
            SUM(solde_actuel) as total_epargne,
            AVG(solde_actuel) as moyenne_epargne,
            MAX(solde_actuel) as max_epargne,
            COUNT(*) as nb_comptes
        FROM epargne
    ''')
    stats = cursor.fetchone()
    
    conn.close()
    
    return render_template('epargne/tableau_bord.html', 
                         comptes=comptes, 
                         stats=stats,
                         total_membres=len(comptes))

@app.route('/epargne/depot/<int:membre_id>', methods=['GET', 'POST'])
def epargne_depot(membre_id):
    """Dépôt sur compte d'épargne"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM membres WHERE id = ?', (membre_id,))
    membre = cursor.fetchone()
    
    if not membre:
        flash('❌ Membre non trouvé', 'error')
        return redirect(url_for('epargne_tableau_bord'))
    
    if request.method == 'POST':
        montant = float(request.form['montant'])
        description = request.form.get('description', '')
        
        success, message = EpargneManager.depot(membre_id, montant, description)
        
        if success:
            flash(f'✅ {message}', 'success')
        else:
            flash(f'❌ {message}', 'error')
        
        return redirect(url_for('epargne_historique', membre_id=membre_id))
    
    return render_template('epargne/depot.html', membre=membre)

@app.route('/epargne/retrait/<int:membre_id>', methods=['GET', 'POST'])
def epargne_retrait(membre_id):
    """Retrait sur compte d'épargne"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM membres WHERE id = ?', (membre_id,))
    membre = cursor.fetchone()
    
    if not membre:
        flash('❌ Membre non trouvé', 'error')
        return redirect(url_for('epargne_tableau_bord'))
    
    cursor.execute('SELECT solde_actuel FROM epargne WHERE membre_id = ?', (membre_id,))
    epargne = cursor.fetchone()
    solde_epargne = epargne['solde_actuel'] if epargne else 0
    
    if request.method == 'POST':
        montant = float(request.form['montant'])
        description = request.form.get('description', '')
        
        if montant > solde_epargne:
            flash(f'❌ Solde d\'épargne insuffisant ({solde_epargne:,.0f} FCFA)', 'error')
            return redirect(url_for('epargne_retrait', membre_id=membre_id))
        
        success, message = EpargneManager.retrait(membre_id, montant, description)
        
        if success:
            flash(f'✅ {message}', 'success')
        else:
            flash(f'❌ {message}', 'error')
        
        return redirect(url_for('epargne_historique', membre_id=membre_id))
    
    return render_template('epargne/retrait.html', 
                         membre=membre, 
                         solde_epargne=solde_epargne)

@app.route('/epargne/historique/<int:membre_id>')
def epargne_historique(membre_id):
    """Historique des opérations d'épargne"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM membres WHERE id = ?', (membre_id,))
    membre = cursor.fetchone()
    
    cursor.execute('''
        SELECT o.*
        FROM operations_epargne o
        JOIN epargne e ON o.epargne_id = e.id
        WHERE e.membre_id = ?
        ORDER BY o.date_operation DESC
        LIMIT 50
    ''', (membre_id,))
    operations = cursor.fetchall()
    
    cursor.execute('SELECT solde_actuel FROM epargne WHERE membre_id = ?', (membre_id,))
    solde = cursor.fetchone()
    
    conn.close()
    
    return render_template('epargne/historique.html', 
                         membre=membre, 
                         operations=operations,
                         solde=solde['solde_actuel'] if solde else 0)

# ============================================
# ROUTES POUR LES FONDS GÉNÉRAUX
# ============================================

@app.route('/fonds_generaux')
def fonds_generaux():
    """Tableau de bord des fonds généraux de la réunion"""
    conn = get_db()
    cursor = conn.cursor()
    
    # ========== STATISTIQUES GLOBALES ==========
    
    # 1. Total des cotisations collectées
    cursor.execute("SELECT COALESCE(SUM(montant_paye), 0) FROM cotisation_membres")
    total_cotisations = cursor.fetchone()[0]
    
    # 2. Total du fonds de caisse (argent disponible des membres)
    cursor.execute("SELECT COALESCE(SUM(solde_actuel), 0) FROM fonds_caisse")
    total_fonds_caisse = cursor.fetchone()[0]
    
    # 3. Total de l'épargne
    cursor.execute("SELECT COALESCE(SUM(solde_actuel), 0) FROM epargne")
    total_epargne = cursor.fetchone()[0]
    
    # 4. Total des prêts en cours
    cursor.execute("SELECT COALESCE(SUM(montant_restant), 0) FROM prets WHERE statut = 'en_cours'")
    total_prets = cursor.fetchone()[0]
    
    # 5. Total des amendes collectées
    cursor.execute("SELECT COALESCE(SUM(montant_amende), 0) FROM sanctions WHERE statut = 'appliquee'")
    total_amendes = cursor.fetchone()[0]
    
    # 6. Trésorerie globale
    tresorerie_globale = total_fonds_caisse + total_epargne + total_cotisations + total_amendes - total_prets
    
    # 7. Évolution des cotisations par mois (12 derniers mois) - CONVERTIR EN DICT
    cursor.execute('''
        SELECT 
            strftime('%Y-%m', date_ajout) as mois,
            SUM(montant_paye) as total
        FROM cotisation_membres
        WHERE date_ajout >= date('now', '-12 months')
        GROUP BY mois
        ORDER BY mois
    ''')
    evolution_cotisations_raw = cursor.fetchall()
    evolution_cotisations = [{'mois': row['mois'], 'total': row['total']} for row in evolution_cotisations_raw]
    
    # 8. Évolution de l'épargne par mois - CONVERTIR EN DICT
    cursor.execute('''
        SELECT 
            strftime('%Y-%m', date_operation) as mois,
            SUM(CASE WHEN type_operation = 'depot' THEN montant ELSE -montant END) as variation
        FROM operations_epargne
        WHERE date_operation >= date('now', '-12 months')
        GROUP BY mois
        ORDER BY mois
    ''')
    evolution_epargne_raw = cursor.fetchall()
    evolution_epargne = [{'mois': row['mois'], 'variation': row['variation']} for row in evolution_epargne_raw]
    
    # 9. Répartition des fonds
    repartition = {
        'cotisations': total_cotisations,
        'fonds_caisse': total_fonds_caisse,
        'epargne': total_epargne,
        'amendes': total_amendes,
        'prets': total_prets
    }
    
    # 10. Top contributeurs (cotisations) - CONVERTIR EN DICT
    cursor.execute('''
        SELECT m.nom, m.prenom, SUM(cm.montant_paye) as total
        FROM cotisation_membres cm
        JOIN membres m ON cm.membre_id = m.id
        GROUP BY m.id
        ORDER BY total DESC
        LIMIT 5
    ''')
    top_contributeurs_raw = cursor.fetchall()
    top_contributeurs = [{'nom': row['nom'], 'prenom': row['prenom'], 'total': row['total']} for row in top_contributeurs_raw]
    
    # 11. Top épargnants - CONVERTIR EN DICT
    cursor.execute('''
        SELECT m.nom, m.prenom, e.solde_actuel as total
        FROM epargne e
        JOIN membres m ON e.membre_id = m.id
        ORDER BY e.solde_actuel DESC
        LIMIT 5
    ''')
    top_epargnants_raw = cursor.fetchall()
    top_epargnants = [{'nom': row['nom'], 'prenom': row['prenom'], 'total': row['total']} for row in top_epargnants_raw]
    
    # 12. Historique des transactions récentes - CONVERTIR EN DICT
    cursor.execute('''
        SELECT 'Cotisation' as type, date_ajout as date, montant_paye as montant, 
               m.nom, m.prenom, NULL as description
        FROM cotisation_membres cm
        JOIN membres m ON cm.membre_id = m.id
        UNION ALL
        SELECT 'Épargne' as type, date_operation as date, montant as montant,
               m.nom, m.prenom, description
        FROM operations_epargne oe
        JOIN epargne e ON oe.epargne_id = e.id
        JOIN membres m ON e.membre_id = m.id
        UNION ALL
        SELECT 'Prêt' as type, date_octroi as date, montant_principal as montant,
               m.nom, m.prenom, description
        FROM prets p
        JOIN membres m ON p.membre_id = m.id
        UNION ALL
        SELECT 'Sanction' as type, date_sanction as date, montant_amende as montant,
               m.nom, m.prenom, motif as description
        FROM sanctions s
        JOIN membres m ON s.membre_id = m.id
        ORDER BY date DESC
        LIMIT 20
    ''')
    transactions_recentes_raw = cursor.fetchall()
    transactions_recentes = [dict(row) for row in transactions_recentes_raw]
    
    conn.close()
    
    # Calculer les pourcentages
    total_general = total_cotisations + total_fonds_caisse + total_epargne + total_amendes
    if total_general > 0:
        pourcentages = {
            'cotisations': (total_cotisations / total_general) * 100,
            'fonds_caisse': (total_fonds_caisse / total_general) * 100,
            'epargne': (total_epargne / total_general) * 100,
            'amendes': (total_amendes / total_general) * 100
        }
    else:
        pourcentages = {'cotisations': 0, 'fonds_caisse': 0, 'epargne': 0, 'amendes': 0}
    
    stats = {
        'total_cotisations': total_cotisations,
        'total_fonds_caisse': total_fonds_caisse,
        'total_epargne': total_epargne,
        'total_prets': total_prets,
        'total_amendes': total_amendes,
        'tresorerie_globale': tresorerie_globale,
        'pourcentages': pourcentages,
        'evolution_cotisations': evolution_cotisations,
        'evolution_epargne': evolution_epargne,
        'repartition': repartition,
        'top_contributeurs': top_contributeurs,
        'top_epargnants': top_epargnants,
        'transactions_recentes': transactions_recentes,
        'date_generation': datetime.now().strftime('%d/%m/%Y %H:%M')
    }
    
    return render_template('fonds_generaux/tableau_bord.html', stats=stats)


@app.route('/fonds_generaux/evolution')
def fonds_generaux_evolution():
    """Page d'évolution détaillée des fonds"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Évolution sur 12 mois
    cursor.execute('''
        SELECT 
            strftime('%Y-%m', date_ajout) as mois,
            SUM(montant_paye) as cotisations,
            0 as epargne
        FROM cotisation_membres
        WHERE date_ajout >= date('now', '-12 months')
        GROUP BY mois
    ''')
    data = cursor.fetchall()
    
    # Transformer en format pour graphique
    evolution_data = []
    for row in data:
        evolution_data.append({
            'mois': row['mois'],
            'cotisations': row['cotisations'],
            'epargne': 0
        })
    
    conn.close()
    
    return render_template('fonds_generaux/evolution.html', evolution_data=evolution_data)


@app.route('/fonds_generaux/export/csv')
def fonds_generaux_export_csv():
    """Export des données financières au format CSV"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Récupérer toutes les transactions
    cursor.execute('''
        SELECT 'Cotisation' as type, date_ajout as date, montant_paye as montant, 
               m.nom, m.prenom
        FROM cotisation_membres cm
        JOIN membres m ON cm.membre_id = m.id
        UNION ALL
        SELECT 'Épargne' as type, date_operation as date, montant as montant,
               m.nom, m.prenom
        FROM operations_epargne oe
        JOIN epargne e ON oe.epargne_id = e.id
        JOIN membres m ON e.membre_id = m.id
        UNION ALL
        SELECT 'Prêt' as type, date_octroi as date, montant_principal as montant,
               m.nom, m.prenom
        FROM prets p
        JOIN membres m ON p.membre_id = m.id
        ORDER BY date DESC
    ''')
    transactions = cursor.fetchall()
    conn.close()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Type', 'Date', 'Montant (FCFA)', 'Membre'])
    
    for t in transactions:
        writer.writerow([t[0], t[1][:10], f"{t[2]:,.0f}", f"{t[4]} {t[3]}"])
    
    csv_content = output.getvalue()
    filename = f"rapport_financier_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )



# ============================================
# 16. ROUTES POUR LES FONDS DE CAISSE
# ============================================
@app.route('/fonds')
def tableau_bord_fonds():
    """Tableau de bord des fonds de caisse"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Récupérer la liste des membres avec leurs fonds (utilise fonds_caisse)
    cursor.execute('''
        SELECT 
            m.id, m.nom, m.prenom, m.telephone,
            COALESCE(fc.solde_actuel, 0) as solde,
            COALESCE(fc.statut, 'actif') as statut_fonds
        FROM membres m
        LEFT JOIN fonds_caisse fc ON m.id = fc.membre_id
        WHERE m.statut = 'actif'
        ORDER BY solde DESC
    ''')
    membres_fonds = cursor.fetchall()
    
    # Calculer les statistiques globales
    cursor.execute('''
        SELECT 
            COUNT(*) as nb_membres_avec_fonds,
            COALESCE(SUM(solde_actuel), 0) as total_fonds,
            COALESCE(AVG(solde_actuel), 0) as moyenne_fonds,
            COALESCE(MAX(solde_actuel), 0) as max_fonds,
            COALESCE(MIN(solde_actuel), 0) as min_fonds
        FROM fonds_caisse
        WHERE statut = 'actif'
    ''')
    result = cursor.fetchone()
    
    stats_globales = {
        'nb_membres_avec_fonds': result[0] if result else 0,
        'total_fonds': result[1] if result else 0,
        'moyenne_fonds': result[2] if result else 0,
        'max_fonds': result[3] if result else 0,
        'min_fonds': result[4] if result else 0
    }
    
    conn.close()
    
    return render_template('fonds/tableau_bord.html', 
                         stats_globales=stats_globales,
                         membres_fonds=membres_fonds)
@app.route('/prets/transfert-cotisation', methods=['GET', 'POST'])
def transfert_cotisation():
    """Transférer une cotisation d'un membre à un autre (sous forme de prêt)"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Récupérer les cotisations actives
    cursor.execute('''
        SELECT c.*, 
               COUNT(cm.membre_id) as nb_membres,
               SUM(CASE WHEN cm.a_cotise = 1 THEN 1 ELSE 0 END) as nb_cotise
        FROM cotisations c
        LEFT JOIN cotisation_membres cm ON c.id = cm.cotisation_id
        WHERE c.statut = 'active'
        GROUP BY c.id
    ''')
    cotisations = cursor.fetchall()
    
    # Récupérer les membres actifs
    cursor.execute("SELECT id, nom, prenom FROM membres WHERE statut = 'actif' ORDER BY nom, prenom")
    membres = cursor.fetchall()
    
    if request.method == 'POST':
        cotisation_id = request.form['cotisation_id']
        donneur_id = request.form['donneur_id']
        receveur_id = request.form['receveur_id']
        montant = float(request.form['montant'])
        taux = float(request.form.get('taux_interet', 0))
        description = request.form.get('description', '')
        
        if donneur_id == receveur_id:
            flash('❌ Le donneur et le receveur doivent être différents', 'error')
            return redirect(url_for('transfert_cotisation'))
        
        try:
            cursor.execute("BEGIN IMMEDIATE")
            
            # Vérifier que le donneur a bien cotisé
            cursor.execute('''
                SELECT * FROM cotisation_membres 
                WHERE cotisation_id = ? AND membre_id = ? AND a_cotise = 1
            ''', (cotisation_id, donneur_id))
            cotisation_donneur = cursor.fetchone()
            
            if not cotisation_donneur:
                flash('❌ Ce membre n\'a pas cotisé à cette cotisation', 'error')
                return redirect(url_for('transfert_cotisation'))
            
            # Vérifier que le receveur n'a pas déjà cotisé
            cursor.execute('''
                SELECT * FROM cotisation_membres 
                WHERE cotisation_id = ? AND membre_id = ?
            ''', (cotisation_id, receveur_id))
            cotisation_receveur = cursor.fetchone()
            
            if cotisation_receveur:
                flash('❌ Ce membre a déjà une participation à cette cotisation', 'error')
                return redirect(url_for('transfert_cotisation'))
            
            # Créer un prêt entre le donneur et le receveur
            numero_pret = generer_numero_pret()
            montant_total = montant * (1 + taux / 100)
            date_octroi = datetime.now().strftime('%Y-%m-%d')
            date_echeance = datetime.now().replace(month=datetime.now().month + 3).strftime('%Y-%m-%d')
            
            # Créer le prêt
            cursor.execute('''
                INSERT INTO prets 
                (numero_pret, preteur_id, emprunteur_id, montant_principal, taux_interet, 
                 montant_total, montant_restant, date_octroi, date_echeance, type_pret, 
                 description, source_fonds, cotisation_source_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'transfert_cotisation', ?, 'cotisation', ?, date('now'))
            ''', (numero_pret, donneur_id, receveur_id, montant, taux, 
                  montant_total, montant_total, date_octroi, date_echeance, 
                  description, cotisation_id))
            
            pret_id = cursor.lastrowid
            
            # Créer une échéance
            cursor.execute('''
                INSERT INTO echeances_pret (pret_id, numero_echeance, montant_echeance, date_echeance)
                VALUES (?, 1, ?, ?)
            ''', (pret_id, montant_total, date_echeance))
            
            # Ajouter le receveur à la cotisation
            cursor.execute('''
                INSERT INTO cotisation_membres (cotisation_id, membre_id, date_ajout, a_cotise, montant_paye)
                VALUES (?, ?, date('now'), 1, ?)
            ''', (cotisation_id, receveur_id, montant))
            
            # Enregistrer le transfert
            cursor.execute('''
                INSERT INTO transferts_cotisation 
                (cotisation_id, donneur_id, receveur_id, montant, date_transfert, description, pret_genere_id)
                VALUES (?, ?, ?, ?, date('now'), ?, ?)
            ''', (cotisation_id, donneur_id, receveur_id, montant, description, pret_id))
            
            conn.commit()
            flash(f'✅ Transfert de cotisation effectué avec succès. Prêt {numero_pret} créé.', 'success')
            return redirect(url_for('detail_pret', id=pret_id))
            
        except Exception as e:
            conn.rollback()
            flash(f'❌ Erreur lors du transfert: {str(e)}', 'error')
        finally:
            conn.close()
    
    conn.close()
    return render_template('prets/transfert_cotisation.html', 
                         cotisations=cotisations,
                         membres=membres)






# ============================================
# ROUTES POUR LES PRÊTS (VERSION COMPLÈTE)
# ============================================


@app.route('/prets')
def liste_prets():
    """Liste de tous les prêts"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            p.*,
            preteur.nom as nom_preteur, preteur.prenom as prenom_preteur,
            emprunteur.nom as nom_emprunteur, emprunteur.prenom as prenom_emprunteur,
            (SELECT COUNT(*) FROM echeances_pret WHERE pret_id = p.id AND statut = 'en_attente') as echeances_restantes,
            COALESCE((SELECT SUM(montant) FROM remboursements_pret WHERE pret_id = p.id), 0) as total_rembourse
        FROM prets p
        JOIN membres preteur ON p.preteur_id = preteur.id
        JOIN membres emprunteur ON p.emprunteur_id = emprunteur.id
        ORDER BY p.date_octroi DESC
    ''')
    prets = cursor.fetchall()
    
    stats = PretManager.get_statistiques()
    
    conn.close()
    
    return render_template('prets/liste_prets.html', prets=prets, stats=stats)

@app.route('/prets/demander', methods=['GET', 'POST'])
def pret_demander():
    """Formulaire de demande de prêt avec vérification en temps réel"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Récupérer les membres actifs
    cursor.execute("SELECT id, nom, prenom FROM membres WHERE statut = 'actif'")
    membres = cursor.fetchall()
    conn.close()
    
    if request.method == 'POST':
        membre_id = int(request.form['membre_id'])
        montant = float(request.form['montant'])
        duree_mois = int(request.form['duree_mois'])
        motif = request.form['motif']
        
        # Vérifier les conditions
        peut, message, conditions = PretManager.verifier_conditions_approfondies(membre_id, montant)
        
        if not peut:
            flash(f'❌ {message}', 'error')
            return redirect(url_for('pret_demander'))
        
        # Créer la demande
        success, message, demande_id = PretManager.demander_pret(
    membre_id, montant, duree_mois, motif
)
        if success:
            flash(f'✅ {message}', 'success')
            return redirect(url_for('prets_mes_demandes'))
        else:
            flash(f'❌ {message}', 'error')
            return redirect(url_for('pret_demander'))
    
    return render_template('prets/demander_pret.html', membres=membres)


@app.route('/prets/demandes')
def prets_mes_demandes():
    """Liste des demandes de prêt"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT d.*, m.nom, m.prenom, e.solde_actuel as epargne
        FROM demandes_pret d
        JOIN membres m ON d.membre_id = m.id
        LEFT JOIN epargne e ON m.id = e.membre_id
        ORDER BY d.date_demande DESC
    ''')
    demandes = cursor.fetchall()
    conn.close()
    
    # Convertir les données pour éviter les None
    demandes_list = []
    for d in demandes:
        demande_dict = dict(d)
        if demande_dict.get('date_decision') is None:
            demande_dict['date_decision'] = None
        demandes_list.append(demande_dict)
    
    return render_template('prets/validation_pret.html', demandes=demandes_list)   

@app.route('/prets/validation/<int:demande_id>', methods=['GET', 'POST'])
def pret_valider(demande_id):
    """Validation d'une demande de prêt"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT d.*, m.nom, m.prenom, e.solde_actuel as epargne
        FROM demandes_pret d
        JOIN membres m ON d.membre_id = m.id
        LEFT JOIN epargne e ON m.id = e.membre_id
        WHERE d.id = ?
    ''', (demande_id,))
    demande = cursor.fetchone()
    conn.close()
    
    if not demande:
        flash('❌ Demande non trouvée', 'error')
        return redirect(url_for('prets_mes_demandes'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'approuver':
            montant_accorde = float(request.form.get('montant_accorde', demande['montant_demande']))
            taux_interet = float(request.form.get('taux_interet', 5))
            
            # Utiliser la bonne méthode : approuver_pret (pas approuver_demande)
            success, message, pret_id = PretManager.approuver_pret(demande_id, montant_accorde, taux_interet)
            
            if success:
                flash(f'✅ {message}', 'success')
            else:
                flash(f'❌ {message}', 'error')
                
        elif action == 'refuser':
            motif = request.form.get('motif_refus', '')
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE demandes_pret 
                SET statut = 'refuse', motif_refus = ?, date_decision = date('now')
                WHERE id = ?
            ''', (motif, demande_id))
            conn.commit()
            conn.close()
            flash('✅ Demande refusée', 'warning')
        
        return redirect(url_for('prets_mes_demandes'))
    
    # Pour les requêtes GET, afficher la page de validation
    # Calculer la simulation
    montant = demande['montant_demande']
    duree = demande['duree_mois']
    simulation = {
        'total': montant * 1.05,
        'mensualite': (montant * 1.05) / duree
    }
    
    return render_template('prets/validation_pret.html', demande=demande, simulation=simulation)

@app.route('/prets/<int:pret_id>')
def pret_detail(pret_id):
    """Détails d'un prêt"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.*, 
               preteur.nom as nom_preteur, preteur.prenom as prenom_preteur, preteur.telephone as tel_preteur,
               emprunteur.nom as nom_emprunteur, emprunteur.prenom as prenom_emprunteur, emprunteur.telephone as tel_emprunteur
        FROM prets p
        JOIN membres preteur ON p.preteur_id = preteur.id
        JOIN membres emprunteur ON p.emprunteur_id = emprunteur.id
        WHERE p.id = ?
    ''', (pret_id,))
    pret = cursor.fetchone()
    
    if not pret:
        flash('❌ Prêt non trouvé', 'error')
        return redirect(url_for('liste_prets'))
    
    # Échéances
    cursor.execute('''
        SELECT * FROM echeances_pret 
        WHERE pret_id = ? 
        ORDER BY numero_echeance
    ''', (pret_id,))
    echeances = cursor.fetchall()
    
    # Remboursements
    cursor.execute('''
        SELECT r.*, e.numero_echeance
        FROM remboursements_pret r
        LEFT JOIN echeances_pret e ON r.echeance_id = e.id
        WHERE r.pret_id = ?
        ORDER BY r.date_remboursement DESC
    ''', (pret_id,))
    remboursements = cursor.fetchall()
    
    # Solde fonds de l'emprunteur
    cursor.execute('SELECT solde_actuel FROM fonds_individuels WHERE membre_id = ?', (pret['emprunteur_id'],))
    fonds_emprunteur = cursor.fetchone()
    
    conn.close()
    
    return render_template('prets/detail_pret.html',
                         pret=pret,
                         echeances=echeances,
                         remboursements=remboursements,
                         fonds_emprunteur=fonds_emprunteur)

@app.route('/prets/<int:pret_id>/rembourser', methods=['GET', 'POST'])
def rembourser_pret(pret_id):
    """Rembourser un prêt"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.*, 
               emprunteur.nom as nom_emprunteur, emprunteur.prenom as prenom_emprunteur
        FROM prets p
        JOIN membres emprunteur ON p.emprunteur_id = emprunteur.id
        WHERE p.id = ?
    ''', (pret_id,))
    pret = cursor.fetchone()
    
    if not pret or pret['statut'] != 'en_cours':
        flash('❌ Prêt non remboursable', 'error')
        return redirect(url_for('liste_prets'))
    
    cursor.execute('''
        SELECT * FROM echeances_pret 
        WHERE pret_id = ? AND statut = 'en_attente'
        ORDER BY numero_echeance
    ''', (pret_id,))
    echeances = cursor.fetchall()
    
    cursor.execute('SELECT * FROM fonds_individuels WHERE membre_id = ?', (pret['emprunteur_id'],))
    fonds_emprunteur = cursor.fetchone()
    
    if request.method == 'POST':
        echeance_id = request.form.get('echeance_id')
        montant = float(request.form['montant'])
        mode = request.form['mode_remboursement']
        description = request.form.get('description', '')
        
        if montant <= 0 or montant > pret['montant_restant']:
            flash('❌ Montant invalide', 'error')
            return redirect(url_for('rembourser_pret', pret_id=pret_id))
        
        try:
            cursor.execute("BEGIN IMMEDIATE")
            date_actuelle = datetime.now().strftime('%Y-%m-%d')
            
            if mode == 'fonds' and fonds_emprunteur:
                if fonds_emprunteur['solde_actuel'] < montant:
                    flash('❌ Solde insuffisant dans votre fonds', 'error')
                    return redirect(url_for('rembourser_pret', pret_id=pret_id))
                
                nouveau_solde = fonds_emprunteur['solde_actuel'] - montant
                cursor.execute('''
                    UPDATE fonds_individuels 
                    SET solde_actuel = ?, date_derniere_mise_a_jour = ?
                    WHERE membre_id = ?
                ''', (nouveau_solde, date_actuelle, pret['emprunteur_id']))
            
            # Enregistrer le remboursement
            cursor.execute('''
                INSERT INTO remboursements_pret 
                (pret_id, echeance_id, montant, date_remboursement, mode_remboursement, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (pret_id, echeance_id if echeance_id else None, montant, date_actuelle, mode, description))
            
            # Mettre à jour le prêt
            nouveau_restant = pret['montant_restant'] - montant
            nouveau_statut = 'rembourse' if nouveau_restant <= 0 else 'en_cours'
            cursor.execute('''
                UPDATE prets 
                SET montant_restant = ?, statut = ?, updated_at = ?
                WHERE id = ?
            ''', (max(nouveau_restant, 0), nouveau_statut, date_actuelle, pret_id))
            
            # Mettre à jour l'échéance
            if echeance_id:
                cursor.execute('''
                    UPDATE echeances_pret 
                    SET statut = 'paye', date_paiement = ?, montant_paye = ?
                    WHERE id = ?
                ''', (date_actuelle, montant, echeance_id))
            
            conn.commit()
            flash(f'✅ Remboursement de {montant:,.0f} FCFA effectué', 'success')
            
        except Exception as e:
            conn.rollback()
            flash(f'❌ Erreur: {str(e)}', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('pret_detail', pret_id=pret_id))
    
    conn.close()
    return render_template('prets/remboursement_pret.html',
                         pret=pret,
                         echeances=echeances,
                         fonds_emprunteur=fonds_emprunteur)

@app.route('/prets/echeances')
def prets_echeances():
    """Liste des échéances à venir et en retard"""
    echeances = PretManager.get_echeances_a_venir(jours=30)
    echeances_retard = PretManager.get_echeances_retard()
    
    return render_template('prets/echeances.html', 
                         echeances=echeances,
                         echeances_retard=echeances_retard)

@app.route('/prets/simulation')
def pret_simulation():
    """Page de simulation de prêt"""
    return render_template('prets/simulation_pret.html')

@app.route('/prets/conditions')
def pret_conditions():
    """Affiche les conditions d'obtention d'un prêt"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM conditions_pret')
    conditions = cursor.fetchone()
    conn.close()
    
    return render_template('prets/conditions.html', conditions=conditions)


@app.route('/api/verifier-conditions/<int:membre_id>')
def api_verifier_conditions(membre_id):
    """API pour vérifier les conditions de prêt en temps réel"""
    montant = request.args.get('montant', type=float, default=0)
    
    # Utiliser la bonne méthode
    peut, message, conditions = PretManager.verifier_conditions_approfondies(membre_id, montant)
    
    return jsonify({
        'eligible': peut,
        'message': message,
        'conditions': {
            'epargne_suffisante': conditions.get('epargne_suffisante', False),
            'montant_max': conditions.get('montant_max', 0),
            'epargne_actuelle': conditions.get('epargne_actuelle', 0),
            'cotisations_a_jour': conditions.get('cotisations_a_jour', False),
            'dernier_paiement': conditions.get('dernier_paiement', None),
            'prets_en_cours': conditions.get('prets_en_cours', 0),
            'sanctions_recentes': conditions.get('sanctions_recentes', 0)
        }
    })

@app.route('/fonds/membre/<int:membre_id>/operation', methods=['POST'])
def ajouter_operation_fonds(membre_id):
    """Ajouter une opération sur le fonds d'un membre"""
    type_operation = request.form['type_operation']
    montant = float(request.form['montant'])
    description = request.form.get('description', '')
    
    if montant <= 0:
        flash('❌ Le montant doit être positif', 'error')
        return redirect(url_for('details_fonds_membre', membre_id=membre_id))
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Récupérer le fonds
    cursor.execute('SELECT * FROM fonds_caisse WHERE membre_id = ?', (membre_id,))
    fonds = cursor.fetchone()
    
    if not fonds:
        # Créer un fonds automatiquement
        cursor.execute('''
            INSERT INTO fonds_caisse (membre_id, montant_base, solde_actuel, date_creation, date_derniere_mise_a_jour)
            VALUES (?, 100000, 100000, date('now'), date('now'))
        ''', (membre_id,))
        conn.commit()
        cursor.execute('SELECT * FROM fonds_caisse WHERE membre_id = ?', (membre_id,))
        fonds = cursor.fetchone()
    
    # Calculer le nouveau solde
    nouveau_solde = fonds['solde_actuel']
    if type_operation == 'depot':
        nouveau_solde += montant
    elif type_operation == 'retrait':
        if fonds['solde_actuel'] < montant:
            flash('❌ Solde insuffisant pour ce retrait', 'error')
            conn.close()
            return redirect(url_for('details_fonds_membre', membre_id=membre_id))
        nouveau_solde -= montant
    else:
        flash('❌ Type d\'opération invalide', 'error')
        conn.close()
        return redirect(url_for('details_fonds_membre', membre_id=membre_id))
    
    # Mettre à jour le fonds
    cursor.execute('''
        UPDATE fonds_caisse 
        SET solde_actuel = ?, date_derniere_mise_a_jour = date('now')
        WHERE id = ?
    ''', (nouveau_solde, fonds['id']))
    
    # Enregistrer l'opération
    cursor.execute('''
        INSERT INTO operations_fonds_caisse 
        (fonds_id, type_operation, montant, date_operation, description, solde_apres)
        VALUES (?, ?, ?, date('now'), ?, ?)
    ''', (fonds['id'], type_operation, montant, description, nouveau_solde))
    
    conn.commit()
    conn.close()
    
    flash(f'✅ {type_operation.capitalize()} de {montant:,.0f} FCFA effectué avec succès', 'success')
    return redirect(url_for('details_fonds_membre', membre_id=membre_id))




@app.route('/fonds/membre/<int:membre_id>')
def details_fonds_membre(membre_id):
    """Détails du fonds d'un membre spécifique"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Informations du membre
    cursor.execute('SELECT * FROM membres WHERE id = ?', (membre_id,))
    membre = cursor.fetchone()
    
    if not membre:
        flash('❌ Membre non trouvé', 'error')
        return redirect(url_for('tableau_bord_fonds'))
    
    # Récupérer le fonds du membre (utilise fonds_caisse)
    cursor.execute('SELECT * FROM fonds_caisse WHERE membre_id = ?', (membre_id,))
    fonds = cursor.fetchone()
    
    if not fonds:
        # Créer un fonds automatiquement si inexistant
        cursor.execute('''
            INSERT INTO fonds_caisse (membre_id, montant_base, solde_actuel, date_creation, date_derniere_mise_a_jour)
            VALUES (?, 100000, 100000, date('now'), date('now'))
        ''', (membre_id,))
        conn.commit()
        cursor.execute('SELECT * FROM fonds_caisse WHERE membre_id = ?', (membre_id,))
        fonds = cursor.fetchone()
    
    # Historique des opérations (si la table existe)
    try:
        cursor.execute('''
            SELECT * FROM operations_fonds_caisse 
            WHERE fonds_id = ?
            ORDER BY date_operation DESC
            LIMIT 20
        ''', (fonds['id'],))
        operations = cursor.fetchall()
    except:
        operations = []
    
    # Statistiques simples
    stats = {
        'total_operations': len(operations),
        'total_depots': sum(o['montant'] for o in operations if o['type_operation'] == 'credit') if operations else 0,
        'total_retraits': sum(o['montant'] for o in operations if o['type_operation'] == 'debit') if operations else 0,
        'total_cotisations_evenements': 0
    }
    
    conn.close()
    
    return render_template('fonds/details_membre.html',
                         membre=membre,
                         fonds=fonds,
                         operations=operations,
                         stats=stats)
    
    # Récupérer ou créer le fonds du membre
    cursor.execute('SELECT * FROM fonds_individuels WHERE membre_id = ?', (membre_id,))
    fonds = cursor.fetchone()
    
    if not fonds:
        # Créer un fonds automatiquement si inexistant
        cursor.execute('''
            INSERT INTO fonds_individuels (membre_id, solde_actuel, date_creation, date_derniere_mise_a_jour)
            VALUES (?, 100000, date('now'), date('now'))
        ''', (membre_id,))
        conn.commit()
        
        cursor.execute('SELECT * FROM fonds_individuels WHERE membre_id = ?', (membre_id,))
        fonds = cursor.fetchone()
    
    # Historique des opérations
    cursor.execute('''
        SELECT 
            op.*,
            e.nom_evenement,
            e.type_evenement
        FROM operations_fonds op
        LEFT JOIN evenements e ON op.evenement_id = e.id
        WHERE op.fonds_id = ?
        ORDER BY op.date_operation DESC
        LIMIT 50
    ''', (fonds['id'],))
    operations = cursor.fetchall()
    
    # Statistiques du membre
    cursor.execute('''
        SELECT 
            COUNT(*) as total_operations,
            COALESCE(SUM(CASE WHEN type_operation = 'depot' THEN montant ELSE 0 END), 0) as total_depots,
            COALESCE(SUM(CASE WHEN type_operation = 'retrait' THEN montant ELSE 0 END), 0) as total_retraits,
            COALESCE(SUM(CASE WHEN type_operation = 'cotisation_evenement' THEN montant ELSE 0 END), 0) as total_cotisations_evenements
        FROM operations_fonds
        WHERE fonds_id = ?
    ''', (fonds['id'],))
    result = cursor.fetchone()
    
    # Créer le dictionnaire stats
    stats = {
        'total_operations': result[0] if result else 0,
        'total_depots': result[1] if result else 0,
        'total_retraits': result[2] if result else 0,
        'total_cotisations_evenements': result[3] if result else 0
    }
    
    # Événements à venir pour lesquels le membre n'a pas encore participé
    cursor.execute('''
        SELECT e.*
        FROM evenements e
        WHERE e.statut IN ('prevue', 'en_cours')
        AND e.id NOT IN (
            SELECT evenement_id FROM participations_evenement 
            WHERE membre_id = ?
        )
        ORDER BY e.date_evenement
        LIMIT 5
    ''', (membre_id,))
    evenements_disponibles = cursor.fetchall()
    
    conn.close()
    
    return render_template('fonds/details_membre.html',
                         membre=membre,
                         fonds=fonds,
                         operations=operations,
                         stats=stats,
                         evenements_disponibles=evenements_disponibles)

# ============================================
# 17. ROUTES POUR LE DASHBOARD
# ============================================
@app.route('/dashboard')
def dashboard():
    """Tableau de bord global"""
    conn = get_db()
    cursor = conn.cursor()
    
    stats = {
        'total_membres': 0,
        'total_epargne': 0,
        'total_fonds': 0,
        'total_prets': 0
    }
    
    cursor.execute("SELECT COUNT(*) FROM membres WHERE statut='actif'")
    stats['total_membres'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(solde_actuel) FROM epargne")
    stats['total_epargne'] = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(solde_actuel) FROM fonds_caisse")
    stats['total_fonds'] = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(montant_restant) FROM prets WHERE statut='en_cours'")
    stats['total_prets'] = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return render_template('dashboard.html', stats=stats)

# ============================================
# 18. ROUTES POUR LES RAPPORTS ET RÈGLEMENTS
# ============================================
@app.route('/rapports')
def rapports():
    """Page des rapports"""
    return render_template('rapports.html')

@app.route('/reglements')
def reglements():
    """Page de gestion des règlements"""
    flash('⚠️ Module en cours de développement', 'info')
    return redirect(url_for('index'))

# ============================================
# 19. ROUTE POUR LES STATISTIQUES API
# ============================================
@app.route('/api/stats/evolution')
def api_evolution_stats():
    """API pour les graphiques d'évolution"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            strftime('%Y-%m', date_operation) as mois,
            SUM(CASE WHEN type_operation = 'depot' THEN montant ELSE 0 END) as depots,
            SUM(CASE WHEN type_operation = 'retrait' THEN montant ELSE 0 END) as retraits
        FROM operations_epargne
        WHERE date_operation >= date('now', '-12 months')
        GROUP BY mois
        ORDER BY mois
    ''')
    epargne_evolution = cursor.fetchall()
    
    cursor.execute('''
        SELECT 
            strftime('%Y-%m', date_ajout) as mois,
            SUM(montant_paye) as total
        FROM cotisation_membres
        WHERE date_ajout >= date('now', '-12 months')
        GROUP BY mois
        ORDER BY mois
    ''')
    cotisations_evolution = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        'epargne': [dict(row) for row in epargne_evolution],
        'cotisations': [dict(row) for row in cotisations_evolution]
    })


# ============================================
# ROUTES POUR LES COTISATIONS (VERSION COMPLÈTE)
# ============================================



@app.route('/cotisations/ajouter', methods=['GET', 'POST'])
def ajouter_cotisation():
    """Ajouter une nouvelle cotisation avec validation"""
    if request.method == 'POST':
        nom = request.form.get('nom_cotisation', '').strip()
        montant = request.form.get('montant_total', '')
        
        # Validation
        if not nom:
            flash('❌ Le nom de la cotisation est obligatoire', 'error')
            return redirect(url_for('ajouter_cotisation'))
        
        try:
            montant = float(montant)
            if montant <= 0:
                flash('❌ Le montant doit être supérieur à 0', 'error')
                return redirect(url_for('ajouter_cotisation'))
        except ValueError:
            flash('❌ Le montant doit être un nombre valide', 'error')
            return redirect(url_for('ajouter_cotisation'))
        
        date_creation = datetime.now().strftime('%Y-%m-%d')
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("BEGIN IMMEDIATE")
            
            cursor.execute('''
                INSERT INTO cotisations (nom_cotisation, montant_total, date_creation, statut)
                VALUES (?, ?, ?, 'active')
            ''', (nom, montant, date_creation))
            
            cotisation_id = cursor.lastrowid
            conn.commit()
            
            flash(f'✅ Cotisation "{nom}" créée avec succès', 'success')
            return redirect(url_for('detail_cotisation', id=cotisation_id))
            
        except Exception as e:
            conn.rollback()
            flash(f'❌ Erreur lors de la création: {str(e)}', 'error')
            return redirect(url_for('ajouter_cotisation'))
        finally:
            conn.close()
    
    return render_template('cotisations/ajouter_cotisation.html')


    
    # Récupérer tous les membres avec leur statut de cotisation
    cursor.execute('''
        SELECT 
            m.id, m.nom, m.prenom, m.telephone, m.email,
            COALESCE(cm.a_cotise, 0) as a_cotise,
            COALESCE(cm.montant_paye, 0) as montant_paye,
            COALESCE(cm.date_ajout, '') as date_cotisation,
            COALESCE(fi.solde_actuel, 0) as solde_fonds
        FROM membres m
        LEFT JOIN cotisation_membres cm ON m.id = cm.membre_id AND cm.cotisation_id = ?
        LEFT JOIN fonds_individuels fi ON m.id = fi.membre_id
        WHERE m.statut = 'actif'
        ORDER BY m.nom, m.prenom
    ''', (id,))
    membres = cursor.fetchall()
    
    conn.close()
    
    # Calculer les statistiques
    stats = {
        'total_membres': len(membres),
        'nb_cotise': sum(1 for m in membres if m['a_cotise']),
        'total_paye': sum(m['montant_paye'] for m in membres),
        'taux_participation': round(sum(1 for m in membres if m['a_cotise']) / len(membres) * 100, 2) if membres else 0
    }
    
    return render_template('cotisations/detail_cotisation.html', 
                         cotisation=cotisation, 
                         membres=membres,
                         stats=stats)



@app.route('/cotisations/<int:id>/exporter/csv')
def exporter_cotisation_csv(id):
    """Exporter les détails d'une cotisation au format CSV"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Récupérer la cotisation
    cursor.execute('SELECT * FROM cotisations WHERE id = ?', (id,))
    cotisation = cursor.fetchone()
    
    if not cotisation:
        flash('❌ Cotisation non trouvée', 'error')
        return redirect(url_for('liste_cotisations'))
    
    # Récupérer les membres avec leur statut
    cursor.execute('''
        SELECT 
            m.nom, m.prenom, m.telephone, m.email,
            CASE WHEN cm.a_cotise = 1 THEN 'Oui' ELSE 'Non' END as a_cotise,
            cm.montant_paye,
            cm.date_ajout
        FROM membres m
        LEFT JOIN cotisation_membres cm ON m.id = cm.membre_id AND cm.cotisation_id = ?
        WHERE m.statut = 'actif'
        ORDER BY m.nom, m.prenom
    ''', (id,))
    membres = cursor.fetchall()
    
    conn.close()
    
    # Créer le CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # En-tête
    writer.writerow([f'Cotisation: {cotisation["nom_cotisation"]}'])
    writer.writerow([f'Date de création: {cotisation["date_creation"][:10]}'])
    writer.writerow([f'Montant total: {cotisation["montant_total"]:,.0f} FCFA'])
    writer.writerow([])
    writer.writerow(['Nom', 'Prénom', 'Téléphone', 'Email', 'A cotisé', 'Montant payé', 'Date de cotisation'])
    
    # Données
    for m in membres:
        writer.writerow([
            m['nom'], m['prenom'], m['telephone'], m['email'],
            m['a_cotise'], f"{m['montant_paye']:,.0f} FCFA" if m['montant_paye'] else '0 FCFA',
            m['date_ajout'][:10] if m['date_ajout'] else ''
        ])
    
    csv_content = output.getvalue()
    filename = f"cotisation_{cotisation['nom_cotisation'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )


# ============================================
# EXPORT PDF MEMBRES
# ============================================

import pdfkit
import os
from datetime import datetime

# Configuration de wkhtmltopdf (à adapter selon votre installation)
# Chemin local dans le projet
WKHTMLTOPDF_PATH = os.path.join(os.path.dirname(__file__), 'wkhtmltopdf', 'bin', 'wkhtmltopdf.exe')
config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

def generer_pdf(html_content, filename):
    """Génère un PDF à partir du contenu HTML"""
    try:
        pdf = pdfkit.from_string(html_content, False, configuration=config, options={
            'encoding': 'UTF-8',
            'enable-local-file-access': None,
            'margin-top': '1.5cm',
            'margin-bottom': '1.5cm',
            'margin-left': '1.5cm',
            'margin-right': '1.5cm'
        })
        return pdf
    except Exception as e:
        print(f"Erreur PDF: {e}")
        return None

@app.route('/membres/export-pdf/<int:id>')
def export_pdf_membre(id):
    """Exporte la fiche d'un membre au format PDF"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Informations du membre
    cursor.execute('SELECT * FROM membres WHERE id = ?', (id,))
    membre = cursor.fetchone()
    
    if not membre:
        flash('❌ Membre non trouvé', 'error')
        return redirect(url_for('membres'))
    
    # Récupérer l'épargne
    cursor.execute('SELECT COALESCE(solde_actuel, 0) FROM epargne WHERE membre_id = ?', (id,))
    epargne = cursor.fetchone()
    solde_epargne = epargne[0] if epargne else 0
    
    # Récupérer le fonds de caisse
    cursor.execute('SELECT COALESCE(solde_actuel, 0) FROM fonds_caisse WHERE membre_id = ?', (id,))
    fonds = cursor.fetchone()
    fonds_caisse = fonds[0] if fonds else 0
    
    # Récupérer les cotisations
    cursor.execute('''
        SELECT cm.*, c.nom_cotisation
        FROM cotisation_membres cm
        JOIN cotisations c ON cm.cotisation_id = c.id
        WHERE cm.membre_id = ?
        ORDER BY cm.date_ajout DESC
        LIMIT 20
    ''', (id,))
    cotisations = cursor.fetchall()
    
    # Récupérer les prêts
    cursor.execute('''
        SELECT * FROM prets 
        WHERE membre_id = ?
        ORDER BY date_octroi DESC
    ''', (id,))
    prets = cursor.fetchall()
    
    # Récupérer les sanctions
    cursor.execute('''
        SELECT * FROM sanctions 
        WHERE membre_id = ?
        ORDER BY date_sanction DESC
    ''', (id,))
    sanctions = cursor.fetchall()
    
    # Récupérer les présences - CORRIGÉ
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN est_present = 1 THEN 1 ELSE 0 END) as presents,
            SUM(CASE WHEN retard = 1 THEN 1 ELSE 0 END) as retards
        FROM presences_seance
        WHERE membre_id = ?
    ''', (id,))
    presences_data = cursor.fetchone()
    
    # Gestion des valeurs None
    total_seances = presences_data['total'] if presences_data and presences_data['total'] else 0
    presences = presences_data['presents'] if presences_data and presences_data['presents'] else 0
    retards = presences_data['retards'] if presences_data and presences_data['retards'] else 0
    absences = total_seances - presences
    taux_presence = (presences / total_seances * 100) if total_seances > 0 else 0
    
    # Calculs totaux
    total_cotise = sum(c['montant_paye'] for c in cotisations) if cotisations else 0
    prets_en_cours = sum(p['montant_restant'] for p in prets if p['statut'] == 'en_cours') if prets else 0
    total_amendes = sum(s['montant_amende'] for s in sanctions if s['statut'] == 'appliquee') if sanctions else 0
    
    conn.close()
    
    # Rendre le template
    html = render_template('membres/pdf/etat_individuel.html',
                         membre=membre,
                         epargne=solde_epargne,
                         fonds_caisse=fonds_caisse,
                         cotisations=cotisations,
                         prets=prets,
                         sanctions=sanctions,
                         total_cotise=total_cotise,
                         prets_en_cours=prets_en_cours,
                         total_amendes=total_amendes,
                         total_seances=total_seances,
                         presences=presences,
                         absences=absences,
                         retards=retards,
                         taux_presence=taux_presence,
                         date_generation=datetime.now().strftime('%d/%m/%Y à %H:%M'))
    
    # Générer le PDF
    pdf_content = generer_pdf(html, f"membre_{id}.pdf")
    
    if pdf_content:
        return Response(pdf_content,
                        mimetype='application/pdf',
                        headers={'Content-Disposition': f'attachment; filename=membre_{membre["prenom"]}_{membre["nom"]}_{datetime.now().strftime("%Y%m%d")}.pdf'})
    else:
        flash('❌ Erreur lors de la génération du PDF', 'error')
        return redirect(url_for('membres'))

@app.route('/membres/export-pdf/tous')
def export_pdf_tous():
    """Exporte la liste de tous les membres au format PDF"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Récupérer tous les membres
    cursor.execute('SELECT * FROM membres ORDER BY nom, prenom')
    membres = cursor.fetchall()
    
    # Ajouter l'épargne et les fonds pour chaque membre
    membres_list = []
    for m in membres:
        cursor.execute('SELECT solde_actuel FROM epargne WHERE membre_id = ?', (m['id'],))
        epargne = cursor.fetchone()
        cursor.execute('SELECT solde_actuel FROM fonds_caisse WHERE membre_id = ?', (m['id'],))
        fonds = cursor.fetchone()
        
        membre_dict = dict(m)
        membre_dict['epargne'] = epargne['solde_actuel'] if epargne else 0
        membre_dict['fonds'] = fonds['solde_actuel'] if fonds else 0
        membres_list.append(membre_dict)
    
    # Statistiques
    total_membres = len(membres_list)
    membres_actifs = sum(1 for m in membres_list if m['statut'] == 'actif')
    membres_inactifs = total_membres - membres_actifs
    total_epargne = sum(m['epargne'] for m in membres_list)
    
    conn.close()
    
    # Rendre le template
    html = render_template('membres/pdf/etat_collectif.html',
                         membres=membres_list,
                         total_membres=total_membres,
                         membres_actifs=membres_actifs,
                         membres_inactifs=membres_inactifs,
                         total_epargne=total_epargne,
                         date_generation=datetime.now().strftime('%d/%m/%Y à %H:%M'))
    
    # Générer le PDF
    pdf_content = generer_pdf(html, "tous_membres.pdf")
    
    if pdf_content:
        return Response(pdf_content,
                        mimetype='application/pdf',
                        headers={'Content-Disposition': f'attachment; filename=liste_membres_{datetime.now().strftime("%Y%m%d")}.pdf'})
    else:
        flash('❌ Erreur lors de la génération du PDF', 'error')
        return redirect(url_for('membres'))
    

# ============================================
# 20. LANCEMENT DE L'APPLICATION
# ============================================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)