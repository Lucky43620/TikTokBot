import yt_dlp as youtube_dl
import moviepy.editor as mp
import whisper
from moviepy.editor import TextClip, CompositeVideoClip
from PIL import ImageFont
import math
import os

def download_and_split_video(youtube_link, output_dir):
    print(f"Téléchargement de la vidéo à partir du lien : {youtube_link}")
    
    # Spécifier les options de téléchargement
    ydl_opts = {
        'format': 'bestvideo+bestaudio',
        'outtmpl': os.path.join(output_dir, 'video.mp4'),
        'merge_output_format': 'mp4'  # Fusionner les formats en MP4
    }
    
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_link])
    
    # Charger la vidéo téléchargée
    clip = mp.VideoFileClip(os.path.join(output_dir, 'video.mp4'))

    duration = clip.duration
    segments = []

    # Découper en segments de 1min et 5 sec
    start = 0
    segment_duration = 65  # 1min et 5sec
    while start < duration:
        end = min(start + segment_duration, duration)
        
        # Mettre au format TikTok (9:16)
        segment = clip.subclip(start, end)
        width, height = segment.size
        new_height = width * 16 / 9  # Calculer la nouvelle hauteur pour un format 9:16
        if new_height > height:
            # Si la nouvelle hauteur dépasse l'original, on ajuste
            new_height = height
            new_width = height * 9 / 16
            x_center = (width - new_width) / 2  # Centre horizontal
            segment = segment.crop(x1=x_center, x2=x_center + new_width, y1=0, y2=new_height)
        else:
            segment = segment.resize(newsize=(width, int(new_height)))

        segments.append(segment)
        start = end

    return clip, segments  # Retourner aussi le clip original

def calculate_font_size(text, max_width, base_size=50):
    # Calculer une taille de police basée sur la longueur du texte
    font = ImageFont.truetype("C:/Windows/Fonts/comic.ttf", base_size)
    text_bbox = font.getbbox(text)  # Utiliser getbbox pour obtenir les dimensions

    text_width = text_bbox[2] - text_bbox[0]  # largeur du texte

    # Réduire la taille de la police si le texte déborde
    while text_width > max_width and base_size > 10:
        base_size -= 2
        font = ImageFont.truetype("C:/Windows/Fonts/comic.ttf", base_size)
        text_bbox = font.getbbox(text)
        text_width = text_bbox[2] - text_bbox[0]

    return base_size

def generate_dynamic_subtitles(segment, transcript, font_path="C:/Windows/Fonts/comic.ttf"):
    clips = []
    
    # Taille de police de base
    base_font_size = 50  # Taille de police initiale
    color = 'yellow'  # Couleur plus lisible
    border_color = 'black'  # Couleur de la bordure

    segment_duration = segment.duration
    
    if 'segments' not in transcript or not transcript['segments']:
        print("Aucun segment de transcription trouvé.")
        return segment  # Retourner le segment d'origine s'il n'y a pas de transcription

    last_end_time = 0

    for segment_text in transcript['segments']:
        start_time = segment_text['start']
        end_time = segment_text['end']

        # Vérifier que le texte est dans la plage de temps du segment
        if start_time >= segment_duration:
            break

        if end_time > segment_duration:
            end_time = segment_duration

        if start_time < last_end_time:
            start_time = last_end_time

        words = segment_text['text'].split()
        chunk_size = 3  # Nombre de mots par clip
        
        for j in range(0, len(words), chunk_size):
            chunk = ' '.join(words[j:j + chunk_size])
            word_start_time = start_time + (j // chunk_size) * ((end_time - start_time) / math.ceil(len(words) / chunk_size))
            word_end_time = word_start_time + ((end_time - start_time) / math.ceil(len(words) / chunk_size))

            if word_end_time <= segment_duration:
                # Calculer la taille de la police en fonction du texte
                font_size = calculate_font_size(chunk, segment.size[0] * 0.9, base_size=base_font_size)
                
                # Créer un TextClip avec un contour
                text_clip = (TextClip(chunk, fontsize=font_size, font="Comic-Sans-MS", color=color, stroke_color=border_color, stroke_width=2)
                             .set_position(("center", "bottom"))  # Placer le texte en bas de l'écran
                             .set_start(word_start_time)
                             .set_end(word_end_time))
                clips.append(text_clip)

        last_end_time = word_end_time

    if not clips:
        text_clip = TextClip("Aucun sous-titre disponible", fontsize=base_font_size, font="Comic-Sans-MS", color=color)
        text_clip = text_clip.set_position(("center", "bottom")).set_duration(segment_duration)
        clips.append(text_clip)

    # Combiner les clips de sous-titres avec la vidéo
    final_clip = CompositeVideoClip([segment] + clips)
    return final_clip

def main():
    youtube_link = input("Entrez le lien YouTube: ")
    print(f"Lien YouTube reçu : {youtube_link}")

    # Créer un dossier pour les résultats
    output_dir = youtube_link.split('=')[-1]  # Utiliser l'ID vidéo comme nom de dossier
    os.makedirs(output_dir, exist_ok=True)
    final_dir = os.path.join(output_dir, 'results')
    os.makedirs(final_dir, exist_ok=True)

    # Télécharger et découper la vidéo
    original_clip, segments = download_and_split_video(youtube_link, output_dir)
    
    # Charger le modèle Whisper
    print("Chargement du modèle Whisper...")
    model = whisper.load_model("base")
    print("Modèle Whisper chargé.")
    
    for i, segment in enumerate(segments):
        print(f"Traitement du segment {i+1}...")

        # Exporter l'audio du segment vers un fichier temporaire
        audio_temp_path = os.path.join(output_dir, f"temp_audio_{i}.wav")
        segment.audio.write_audiofile(audio_temp_path, codec='pcm_s16le')  # Exporter en WAV

        # Transcrire tout l'audio du segment sans découpage
        result = model.transcribe(audio_temp_path, language="fr", fp16=False)  # Utiliser une transcription complète

        # Générer des sous-titres dynamiques
        final_clip = generate_dynamic_subtitles(segment, result)

        # Réintégrer l'audio du segment d'origine
        final_clip = final_clip.set_audio(segment.audio)

        # Exporter le segment avec sous-titres et audio
        final_clip.write_videofile(os.path.join(final_dir, f"segment_{i}_with_subtitles.mp4"), fps=24, audio_codec='aac')

        # Supprimer le fichier audio temporaire après traitement
        os.remove(audio_temp_path)

    print("Traitement terminé.")

if __name__ == "__main__":
    main()
