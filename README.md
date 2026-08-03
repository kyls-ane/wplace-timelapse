# 🎞️ wplace.live — Bot Timelapse

Bot qui capture automatiquement l'évolution d'une zone de 6 tuiles sur
[wplace.live](https://wplace.live) pour créer un timelapse.

---

## 📁 Structure du projet

| Fichier | Rôle |
|---|---|
| `timelapse.py` | Script principal : télécharge 6 tuiles, les assemble en grille 2×3 (2000×3000 px), compare avec la référence, et sauvegarde une frame horodatée si un changement est détecté. |
| `requirements.txt` | Dépendances Python (`requests`, `Pillow`, `numpy`). |
| `.github/workflows/timelapse.yml` | Workflow GitHub Actions : cron toutes les 5 min, uploade les frames comme artifacts, committe la référence. |
| `reference.png` | Dernière image assemblée (auto-générée, committée par le bot). |

---

## 🖼️ Grille d'assemblage

Les 6 tuiles sont assemblées comme ceci (2000×3000 px) :

```
┌──────────────┬──────────────┐
│  1053/735    │  1054/735    │
│  (1000×1000) │  (1000×1000) │
├──────────────┼──────────────┤
│  1053/736    │  1054/736    │
│  (1000×1000) │  (1000×1000) │
├──────────────┼──────────────┤
│  1053/737    │  1054/737    │
│  (1000×1000) │  (1000×1000) │
└──────────────┴──────────────┘
```

---

## 🚀 Installation

### 1. Créer le repo GitHub

1. Va sur [github.com/new](https://github.com/new)
2. Nom : `wplace-timelapse`
3. Visibilité : **Public** (minutes GitHub Actions illimitées)
4. Ne coche rien, clique **Create repository**

### 2. Pousser les fichiers

```bash
cd wplace-timelapse
git init
git add .
git commit -m "🚀 Premier commit — timelapse wplace.live"
git branch -M main
git remote add origin https://github.com/TON_PSEUDO/wplace-timelapse.git
git push -u origin main
```

### 3. (Optionnel) Configurer la tolérance

Dans **Settings → Secrets and variables → Actions → Variables** :

| Variable | Défaut | Description |
|---|---|---|
| `TL_COLOR_TOLERANCE` | `5` | Tolérance couleur (0-255). Plus bas = plus sensible. |

### 4. Activer et tester

1. Onglet **Actions** → activer les workflows
2. Cliquer **"Run workflow"** pour un test manuel
3. Le bot se lancera ensuite tout seul toutes les ~5 min

---

## 📥 Récupérer les frames du timelapse

Les frames sont stockées comme **GitHub Actions Artifacts** :

1. Va dans l'onglet **Actions** de ton repo
2. Clique sur un run qui a le label vert ✅
3. En bas de la page, section **Artifacts**, télécharge le zip `timelapse-frame-XXXX`
4. Chaque zip contient les frames PNG horodatées de ce run

### Assembler le timelapse (avec ffmpeg)

Une fois toutes les frames téléchargées et extraites dans un dossier :

```bash
ffmpeg -framerate 10 -pattern_type glob -i "frame_*.png" -c:v libx264 -pix_fmt yuv420p timelapse.mp4
```

---

## ⚠️ Limites

- **Stockage artifacts** : 500 Mo sur le plan gratuit. Chaque frame ≈ 2-5 Mo. Pense à télécharger et supprimer les anciens artifacts régulièrement.
- **Rétention** : Les artifacts sont conservés 90 jours par défaut.
- **Délai cron** : GitHub peut ajouter 1 à 15 min de délai sur le cron.
