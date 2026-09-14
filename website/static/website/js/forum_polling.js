// forum_polling.js - Spécifique pour les forums
class ForumPolling {
    constructor(forumId) {
        this.forumId = forumId;
        this.dernierMessageId = parseInt(document.getElementById('dernier-message-id')?.value || 0);
        this.pollingActif = false;
        this.intervalleActuel = 15;
        this.timeoutId = null;
        this.enPause = false;
        
        this.init();
    }
    
    init() {
        const config = document.getElementById('forum-config');
        if (config) {
            this.pollingActif = config.dataset.pollingActif === 'true';
            this.intervalleActuel = parseInt(config.dataset.intervalle) || 15;
        }
        
        if (this.pollingActif) {
            this.demarrer();
        }
    }
    
    async verifierNouveauxMessages() {
        if (!this.pollingActif || this.enPause) return;
        
        try {
            const response = await fetch(`/forum/${this.forumId}/messages/nouveaux/?dernier_id=${this.dernierMessageId}`);
            const data = await response.json();
            
            if (data.messages && data.messages.length > 0) {
                this.afficherNouveauxMessages(data.messages);
                this.dernierMessageId = data.dernier_id;
            }
        } catch (error) {
            console.error('Erreur polling forum:', error);
        }
        
        this.timeoutId = setTimeout(() => this.verifierNouveauxMessages(), this.intervalleActuel * 1000);
    }
    
    afficherNouveauxMessages(messages) {
        const container = document.getElementById('forum-messages');
        if (!container) return;
        
        for (const msg of messages) {
            const messageHtml = this.genererMessageHtml(msg);
            container.insertAdjacentHTML('beforeend', messageHtml);
        }
        
        // Scroll en bas
        container.scrollTop = container.scrollHeight;
        
        // Mettre à jour le badge
        this.mettreAJourBadge(messages.length);
    }
    
    genererMessageHtml(msg) {
        return `
            <div class="forum-message" data-message-id="${msg.id}">
                <div class="message-avatar">
                    <i class="fas fa-user-circle"></i>
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <strong>${msg.auteur.prenom || msg.auteur.username}</strong>
                        <span class="message-date">${msg.date_creation}</span>
                        <button class="btn-signaler" data-message-id="${msg.id}" title="Signaler">
                            <i class="fas fa-flag"></i>
                        </button>
                    </div>
                    <div class="message-body">
                        ${this.escapeHtml(msg.contenu)}
                    </div>
                </div>
            </div>
        `;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    mettreAJourBadge(nb) {
        // Mettre à jour un éventuel badge
    }
    
    demarrer() {
        this.verifierNouveauxMessages();
    }
    
    arreter() {
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
        }
    }
}

// Initialiser au chargement
document.addEventListener('DOMContentLoaded', () => {
    const forumContainer = document.getElementById('forum-container');
    if (forumContainer) {
        const forumId = forumContainer.dataset.forumId;
        window.forumPolling = new ForumPolling(forumId);
    }
});