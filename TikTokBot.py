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
        segment = clip.subclip(start, end)
        segments.append(segment)
        start = end

    return clip, segments  # Retourner aussi le clip original

def generate_dynamic_subtitles(segment, transcript, font_path="C:/Windows/Fonts/Arial.ttf"):
    clips = []
    font = ImageFont.truetype(font_path, 50)

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

        # Ajuster les timings pour qu'ils soient relatifs au segment
        if end_time > segment_duration:
            end_time = segment_duration

        # S'assurer qu'il n'y a pas de superposition
        if start_time < last_end_time:
            start_time = last_end_time  # Déplacer le start_time si superposition

        # Créer le texte avec un effet d'apparition progressive
        words = segment_text['text'].split()
        chunk_size = 3  # Nombre de mots par clip
        
        for j in range(0, len(words), chunk_size):
            chunk = ' '.join(words[j:j + chunk_size])
            word_start_time = start_time + (j // chunk_size) * ((end_time - start_time) / math.ceil(len(words) / chunk_size))
            word_end_time = word_start_time + ((end_time - start_time) / math.ceil(len(words) / chunk_size))

            # Ne pas créer un clip si les timings sont en dehors du segment
            if word_end_time <= segment_duration:
                text_clip = TextClip(chunk, fontsize=50, font="Arial", color='white')
                text_clip = text_clip.set_position(("center", 50)).set_start(word_start_time).set_end(word_end_time)
                clips.append(text_clip)

        last_end_time = word_end_time  # Mettre à jour le dernier end_time

    # Si des sous-titres n'ont pas été créés, afficher un sous-titre par défaut
    if not clips:
        text_clip = TextClip("Aucun sous-titre disponible", fontsize=50, font="Arial", color='white')
        text_clip = text_clip.set_position(("center", 50)).set_duration(segment_duration)
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
