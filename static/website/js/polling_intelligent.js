// Polling intelligent pour la messagerie
class MessageriePolling {
    constructor() {
        this.timeoutId = null;
        this.pollingActif = false;
        this.intervalleActuel = 30;
        this.adaptationAuto = true;
        this.intervalleMin = 10;
        this.intervalleMax = 90;
        this.pauseNocturne = false;
        this.heureDebut = 22;
        this.heureFin = 6;
        this.pauseOngletInactif = true;
        this.enPause = false;
        this.lastCheck = 0;
        
        this.init();
    }
    
    init() {
        // Récupérer la configuration depuis le DOM
        const config = document.getElementById('messagerie-config');
        if (config) {
            this.pollingActif = config.dataset.pollingActif === 'true';
            this.intervalleActuel = parseInt(config.dataset.intervalle) || 30;
            this.pauseOngletInactif = config.dataset.pauseOnglet === 'true';
            this.pauseNocturne = config.dataset.pauseNocturne === 'true';
            this.heureDebut = parseInt(config.dataset.heureDebut) || 22;
            this.heureFin = parseInt(config.dataset.heureFin) || 6;
            this.adaptationAuto = config.dataset.adaptationAuto === 'true';
            this.intervalleMin = parseInt(config.dataset.intervalleMin) || 10;
            this.intervalleMax = parseInt(config.dataset.intervalleMax) || 90;
        }
        
        // Démarrer le polling
        this.demarrer();
        
        // Écouter la visibilité de l'onglet
        if (this.pauseOngletInactif) {
            document.addEventListener('visibilitychange', () => this.onVisibilityChange());
        }
        
        // Écouter la connexion réseau
        window.addEventListener('online', () => this.onOnline());
        window.addEventListener('offline', () => this.onOffline());
    }
    
    estHeureNocturne() {
        if (!this.pauseNocturne) return false;
        const heure = new Date().getHours();
        if (this.heureDebut > this.heureFin) {
            return heure >= this.heureDebut || heure < this.heureFin;
        }
        return heure >= this.heureDebut && heure < this.heureFin;
    }
    
    doitFairePause() {
        // Pause si onglet inactif ou heure nocturne
        if (this.pauseOngletInactif && document.hidden) return true;
        if (this.estHeureNocturne()) return true;
        return false;
    }
    
    async verifierMessages() {
        if (!this.pollingActif) {
            this.afficherMessagePollingDesactive();
            return;
        }
        
        if (this.doitFairePause()) {
            if (!this.enPause) {
                this.enPause = true;
                console.log('Polling en pause');
            }
            // Reprogrammer pour plus tard
            this.timeoutId = setTimeout(() => this.verifierMessages(), 60000);
            return;
        }
        
        this.enPause = false;
        
        try {
            const response = await fetch('/api/messages/non-lus/', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            const data = await response.json();
            
            if (data.nouveaux_messages > 0) {
                this.mettreAJourBadge(data.nouveaux_messages);
                this.afficherNotification(data.nouveaux_messages);
            }
            
            // Adapter l'intervalle si nécessaire
            this.ajusterIntervalle(data);
            
        } catch (error) {
            console.error('Erreur polling:', error);
        }
        
        // Programmer le prochain check
        this.timeoutId = setTimeout(() => this.verifierMessages(), this.intervalleActuel * 1000);
    }
    
    ajusterIntervalle(data) {
        if (!this.adaptationAuto) return;
        
        let nouvelIntervalle = this.intervalleActuel;
        
        if (data.charge_serveur) {
            const charge = data.charge_serveur;
            if (charge > 0.8) {
                nouvelIntervalle = Math.min(this.intervalleMax, this.intervalleActuel + 10);
            } else if (charge < 0.3) {
                nouvelIntervalle = Math.max(this.intervalleMin, this.intervalleActuel - 5);
            }
        }
        
        if (data.utilisateurs_actifs > 10000) {
            nouvelIntervalle = Math.min(this.intervalleMax, 60);
        } else if (data.utilisateurs_actifs > 5000) {
            nouvelIntervalle = Math.min(this.intervalleMax, 45);
        }
        
        if (nouvelIntervalle !== this.intervalleActuel) {
            this.intervalleActuel = nouvelIntervalle;
            console.log(`Intervalle polling ajusté à ${this.intervalleActuel}s`);
            
            // Redémarrer le timer
            clearTimeout(this.timeoutId);
            this.timeoutId = setTimeout(() => this.verifierMessages(), this.intervalleActuel * 1000);
        }
    }
    
    mettreAJourBadge(nombre) {
        const badge = document.querySelector('.badge-messages');
        if (badge) {
            if (nombre > 0) {
                badge.textContent = nombre > 99 ? '99+' : nombre;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }
    }
    
    afficherNotification(nombre) {
        if (Notification.permission === 'granted' && document.hidden) {
            new Notification('Nouveaux messages', {
                body: `Vous avez ${nombre} nouveau${nombre > 1 ? 'x' : ''} message${nombre > 1 ? 's' : ''}`,
                icon: '/static/website/img/logo.png'
            });
        }
    }
    
    afficherMessagePollingDesactive() {
        const container = document.querySelector('.messagerie-container');
        if (container && !container.querySelector('.alert-polling-desactive')) {
            const configDiv = document.getElementById('messagerie-config');
            const message = configDiv?.dataset.messagePollingDesactive || 
                "La messagerie est en mode manuel. Cliquez ci-dessous pour actualiser.";
            
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-warning alert-polling-desactive';
            alertDiv.innerHTML = `
                <i class="fas fa-clock me-2"></i>
                ${message}
                <button onclick="location.reload()" class="btn btn-sm btn-primary ms-3">
                    <i class="fas fa-sync-alt me-1"></i>Actualiser
                </button>
            `;
            container.prepend(alertDiv);
        }
    }
    
    onVisibilityChange() {
        if (!document.hidden) {
            // L'utilisateur revient sur l'onglet → vérifier immédiatement
            clearTimeout(this.timeoutId);
            this.verifierMessages();
        }
    }
    
    onOnline() {
        console.log('Connexion rétablie');
        clearTimeout(this.timeoutId);
        this.verifierMessages();
    }
    
    onOffline() {
        console.log('Pas de connexion');
    }
    
    demarrer() {
        this.verifierMessages();
        
        // Demander la permission pour les notifications
        if (Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }
    
    arreter() {
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
        }
    }
}

// Initialiser au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    window.messageriePolling = new MessageriePolling();
});