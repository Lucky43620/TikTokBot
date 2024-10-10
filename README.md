# TikTokBot

## Description
TikTokBot est un script Python qui télécharge des vidéos YouTube, les découpe en segments de 1 minute et 5 secondes, et génère des sous-titres dynamiques à l'aide du modèle Whisper. Le script permet d'intégrer l'audio original de la vidéo tout en affichant les sous-titres pendant la lecture des segments.

## Fonctionnalités
- Téléchargement de vidéos YouTube.
- Découpage des vidéos en segments.
- Transcription audio en texte à l'aide du modèle Whisper.
- Génération de sous-titres dynamiques pour chaque segment.
- Exportation des segments avec sous-titres intégrés et audio original.

## Prérequis
Avant d'exécuter le script, assurez-vous d'avoir installé les dépendances suivantes :

- Python 3.6 ou version ultérieure
- yt-dlp
- moviepy
- whisper
- Pillow
- ImageMagick (pour la manipulation des images et des polices)

Vous pouvez installer les dépendances nécessaires à l'aide de pip :

```bash
pip install yt-dlp moviepy git+https://github.com/openai/whisper.git Pillow
```

Installation d'ImageMagick

ImageMagick est un logiciel de manipulation d'images qui peut être nécessaire pour le bon fonctionnement des sous-titres générés. Vous pouvez télécharger et installer ImageMagick depuis le site officiel.

Assurez-vous que l'installation inclut les bibliothèques de développement et que le chemin d'accès à ImageMagick est ajouté à votre variable d'environnement PATH pour que moviepy puisse l'utiliser.

## Configuration
1. Police de sous-titres
Le script utilise une police de caractères pour les sous-titres. Assurez-vous que le chemin de la police est correct. Par défaut, il utilise Arial.ttf, mais vous pouvez le modifier en fonction de la police de votre choix :

python
Copier le code
font_path="C:/Windows/Fonts/Arial.ttf"
2. Modifier le lien YouTube
Lorsque vous exécutez le script, il vous demande de saisir un lien YouTube. Assurez-vous que le lien est valide et accessible.

## Exécution du script
Pour exécuter le script, utilisez la commande suivante dans votre terminal :

```bash
python TikTokBot.py
```

Suivez les instructions à l'écran pour entrer le lien YouTube souhaité.

## Structure du projet

```bash
TikTokBot/
│
├── TikTokBot.py          # Script principal
└── README.md             # Ce fichier README
```

## Auteurs
Lucas Bruyère

## License
Ce projet est sous licence MIT.
