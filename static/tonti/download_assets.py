import urllib.request
import os
import zipfile
import shutil

def download_file(url, filename):
    """Télécharge un fichier depuis une URL"""
    print(f"📥 Téléchargement de {filename}...")
    try:
        urllib.request.urlretrieve(url, filename)
        print(f"✅ {filename} téléchargé")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def extract_zip(zip_path, extract_to):
    """Extrait un fichier zip"""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def setup_local_assets():
    """Télécharge et installe les assets localement"""
    
    # Créer les dossiers
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static/webfonts', exist_ok=True)
    
    # Télécharger Bootstrap
    bootstrap_url = "https://github.com/twbs/bootstrap/releases/download/v5.1.3/bootstrap-5.1.3-dist.zip"
    bootstrap_zip = "bootstrap.zip"
    
    if download_file(bootstrap_url, bootstrap_zip):
        extract_zip(bootstrap_zip, "static")
        # Déplacer les fichiers
        if os.path.exists("static/bootstrap-5.1.3-dist/css/bootstrap.min.css"):
            shutil.move("static/bootstrap-5.1.3-dist/css/bootstrap.min.css", "static/css/bootstrap.min.css")
        if os.path.exists("static/bootstrap-5.1.3-dist/js/bootstrap.bundle.min.js"):
            shutil.move("static/bootstrap-5.1.3-dist/js/bootstrap.bundle.min.js", "static/js/bootstrap.bundle.min.js")
        # Nettoyer
        shutil.rmtree("static/bootstrap-5.1.3-dist")
        os.remove(bootstrap_zip)
    
    # Télécharger Font Awesome
    fontawesome_url = "https://github.com/FortAwesome/Font-Awesome/releases/download/6.0.0/fontawesome-free-6.0.0-web.zip"
    fontawesome_zip = "fontawesome.zip"
    
    if download_file(fontawesome_url, fontawesome_zip):
        extract_zip(fontawesome_zip, "static")
        # Déplacer les fichiers
        if os.path.exists("static/fontawesome-free-6.0.0-web/css/all.min.css"):
            shutil.move("static/fontawesome-free-6.0.0-web/css/all.min.css", "static/css/all.min.css")
        # Copier les webfonts
        if os.path.exists("static/fontawesome-free-6.0.0-web/webfonts"):
            for file in os.listdir("static/fontawesome-free-6.0.0-web/webfonts"):
                shutil.move(f"static/fontawesome-free-6.0.0-web/webfonts/{file}", f"static/webfonts/{file}")
        # Nettoyer
        shutil.rmtree("static/fontawesome-free-6.0.0-web")
        os.remove(fontawesome_zip)
    
    print("\n✅ Installation des assets locaux terminée !")
    print("Vous pouvez maintenant lancer l'application sans connexion Internet.")

if __name__ == "__main__":
    setup_local_assets()