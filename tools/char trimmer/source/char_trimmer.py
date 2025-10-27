import os
from tkinter import Tk, filedialog

def nettoyer_noms_fichiers(dossier):
    """Parcourt récursivement un dossier et nettoie les noms des fichiers."""
    for racine, _, fichiers in os.walk(dossier):
        for fichier in fichiers:
            ancien_chemin = os.path.join(racine, fichier)
            nouveau_nom = fichier.replace("'", "").replace('"', "")
            nouveau_chemin = os.path.join(racine, nouveau_nom)
            
            if nouveau_nom != fichier:
                try:
                    os.rename(ancien_chemin, nouveau_chemin)
                    print(f"Renommé : {fichier} → {nouveau_nom}")
                except Exception as e:
                    print(f"❌ Erreur lors du renommage de {fichier}: {e}")
    print("\n✅ Nettoyage terminé.")

def choisir_dossier():
    """Ouvre une boîte de dialogue pour choisir un dossier."""
    Tk().withdraw()  # Masque la fenêtre principale de Tkinter
    dossier = filedialog.askdirectory(title="Choisissez le dossier à analyser")
    return dossier

if __name__ == "__main__":
    dossier_choisi = choisir_dossier()
    if dossier_choisi:
        print(f"Dossier choisi : {dossier_choisi}\n")
        nettoyer_noms_fichiers(dossier_choisi)
    else:
        print("Aucun dossier sélectionné.")
