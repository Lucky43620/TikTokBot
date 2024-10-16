import os
import subprocess
import yt_dlp
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.fx.all import resize, crop
from threading import Thread

# Télécharger la vidéo YouTube
def download_youtube_video(link, output_path='video.mp4'):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}],
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([link])

    return output_path

# Convertir en 120fps
def convert_to_120fps(input_video, output_video):
    command = ['ffmpeg', '-i', input_video, '-filter:v', 'fps=fps=120', '-c:a', 'copy', output_video]
    subprocess.run(command, check=True)

# Améliorer les couleurs
def enhance_colors(input_video, output_video):
    command = ['ffmpeg', '-i', input_video, '-vf', 'eq=saturation=2:brightness=0.05:contrast=1.4:gamma=1.2', '-c:a', 'copy', output_video]
    subprocess.run(command, check=True)

# Découper et adapter au format TikTok
def split_and_format(input_video_path, output_folder, segment_duration=65):
    clip = VideoFileClip(input_video_path)
    total_duration = clip.duration
    num_segments = int(total_duration // segment_duration) + (1 if total_duration % segment_duration != 0 else 0)

    for i in range(num_segments):
        start_time = i * segment_duration
        end_time = min((i + 1) * segment_duration, total_duration)
        segment = clip.subclip(start_time, end_time)
        width, height = segment.size
        if width > height:
            new_width = int(height * (9 / 16))
            cropped_segment = crop(segment, width=new_width, height=height, x_center=width/2, y_center=height/2)
        else:
            cropped_segment = resize(segment, height=1920)
            cropped_segment = crop(cropped_segment, width=1080, height=1920, x_center=cropped_segment.w/2, y_center=cropped_segment.h/2)

        output_path = os.path.join(output_folder, f"segment_{i+1}.mp4")
        cropped_segment.write_videofile(output_path, codec="libx264", bitrate="5000k", audio_codec="aac", audio_bitrate="192k", preset="slow", threads=4)

    clip.close()

# Processus complet avec barre de progression
def process_video(youtube_link):
    try:
        video_title = youtube_link.split('v=')[-1][:11]  # Exemple de récupération du titre
        output_folder = os.path.join("output_videos", video_title)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Étape 1 : Téléchargement
        progress_var.set(0)
        progress_label.config(text="Téléchargement...")
        root.update_idletasks()
        video_path = download_youtube_video(youtube_link, os.path.join(output_folder, 'video_4k_or_best.mp4'))
        
        # Étape 2 : Conversion en 120 FPS
        progress_var.set(33)
        progress_label.config(text="Conversion en 120 FPS...")
        root.update_idletasks()
        video_120fps = os.path.join(output_folder, 'video_120fps.mp4')
        convert_to_120fps(video_path, video_120fps)
        
        # Étape 3 : Amélioration des couleurs
        progress_var.set(66)
        progress_label.config(text="Amélioration des couleurs...")
        root.update_idletasks()
        enhanced_video = os.path.join(output_folder, 'video_120fps_enhanced.mp4')
        enhance_colors(video_120fps, enhanced_video)
        
        # Étape 4 : Découpage et format TikTok
        progress_var.set(100)
        progress_label.config(text="Découpage et conversion au format TikTok...")
        root.update_idletasks()
        split_and_format(enhanced_video, output_folder)

        progress_label.config(text="Processus terminé !")
    except Exception as e:
        messagebox.showerror("Erreur", f"Une erreur s'est produite : {e}")
    finally:
        start_button.config(state=tk.NORMAL)

# Lancer le processus en thread séparé pour ne pas bloquer l'interface
def start_processing():
    youtube_link = url_entry.get()
    if not youtube_link:
        messagebox.showerror("Erreur", "Veuillez entrer un lien YouTube.")
        return
    
    start_button.config(state=tk.DISABLED)
    progress_label.config(text="Démarrage...")
    thread = Thread(target=process_video, args=(youtube_link,))
    thread.start()

# Interface graphique
root = tk.Tk()
root.title("TikTok Video Generator")
root.geometry("500x300")
root.config(bg="#2e2e2e")

# URL de la vidéo YouTube
url_label = tk.Label(root, text="Lien YouTube :", bg="#2e2e2e", fg="white", font=("Arial", 12))
url_label.pack(pady=10)
url_entry = tk.Entry(root, width=50)
url_entry.pack(pady=5)

# Bouton pour démarrer
start_button = tk.Button(root, text="Démarrer", command=start_processing, bg="#1DB954", fg="white", font=("Arial", 12))
start_button.pack(pady=20)

# Barre de progression
progress_var = tk.DoubleVar()
progress_bar = Progressbar(root, variable=progress_var, maximum=100, length=400)
progress_bar.pack(pady=10)

# Texte de progression
progress_label = tk.Label(root, text="En attente...", bg="#2e2e2e", fg="white", font=("Arial", 12))
progress_label.pack(pady=10)

root.mainloop()
