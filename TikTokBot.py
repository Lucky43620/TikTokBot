import yt_dlp as youtube_dl
import moviepy.editor as mp
import whisper
from moviepy.editor import TextClip, CompositeVideoClip
from PIL import ImageFont
import math
import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading
import time

class TikTokBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TikTok Video Generator")
        self.root.geometry("600x500")
        self.root.config(bg="#2c2c2e")
        self.root.resizable(False, False)

        self.video_info = {}
        self.output_dir = ""
        self.progress = tk.DoubleVar()

        self.create_widgets()

    def create_widgets(self):
        title_label = tk.Label(self.root, text="TikTok Video Generator", font=("Arial", 24), bg="#2c2c2e", fg="white")
        title_label.pack(pady=(20, 10))

        self.link_entry = tk.Entry(self.root, width=50)
        self.link_entry.pack(pady=10)

        self.search_button = tk.Button(self.root, text="Rechercher", command=self.search_video_info, bg="#007aff", fg="white", padx=10)
        self.search_button.pack(pady=10)

        self.video_details_frame = tk.Frame(self.root, bg="#2c2c2e")
        self.video_details_frame.pack(pady=10)

        self.title_label = tk.Label(self.video_details_frame, text="", font=("Arial", 12), bg="#2c2c2e", fg="white")
        self.title_label.pack()

        self.author_label = tk.Label(self.video_details_frame, text="", font=("Arial", 12), bg="#2c2c2e", fg="white")
        self.author_label.pack()

        self.duration_label = tk.Label(self.video_details_frame, text="", font=("Arial", 12), bg="#2c2c2e", fg="white")
        self.duration_label.pack()

        self.estimate_label = tk.Label(self.video_details_frame, text="", font=("Arial", 12), bg="#2c2c2e", fg="white")
        self.estimate_label.pack()

        self.start_button = tk.Button(self.root, text="Démarrer", command=self.start_processing, bg="#28a745", fg="white", padx=10, state=tk.DISABLED)
        self.start_button.pack(pady=20)

        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress, maximum=100)
        self.progress_bar.pack(pady=10, fill=tk.X)

        self.result_button = tk.Button(self.root, text="Ouvrir dossier résultats", command=self.open_results_folder, bg="#007aff", fg="white", padx=10, state=tk.DISABLED)
        self.result_button.pack(pady=(10, 5))

        # Nouveau bouton pour réinitialiser
        self.new_project_button = tk.Button(self.root, text="Nouveau projet", command=self.reset_project, bg="#ff9500", fg="white", padx=10, state=tk.DISABLED)
        self.new_project_button.pack(pady=(5, 20))

    def search_video_info(self):
        youtube_link = self.link_entry.get()
        if not youtube_link:
            messagebox.showwarning("Avertissement", "Veuillez entrer un lien YouTube.")
            return

        try:
            with youtube_dl.YoutubeDL() as ydl:
                info_dict = ydl.extract_info(youtube_link, download=False)
                self.video_info = {
                    "title": info_dict.get('title', 'N/A'),
                    "author": info_dict.get('uploader', 'N/A'),
                    "duration": info_dict.get('duration', 0),
                    "webpage_url": info_dict.get('webpage_url', ''),
                }
                self.display_video_info()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la récupération des informations de la vidéo: {str(e)}")

    def display_video_info(self):
        self.title_label.config(text=f"Titre : {self.video_info['title']}")
        self.author_label.config(text=f"Auteur : {self.video_info['author']}")
        duration = self.video_info['duration']
        self.duration_label.config(text=f"Durée : {duration // 60}min {duration % 60}s")

        estimated_time = duration * 2 / 60  # en minutes
        self.estimate_label.config(text=f"Temps estimé : {int(estimated_time)} minutes")

        self.start_button.config(state=tk.NORMAL)

    def start_processing(self):
        self.start_button.config(state=tk.DISABLED)
        self.search_button.config(state=tk.DISABLED)
        self.new_project_button.config(state=tk.NORMAL)  # Activer le bouton Nouveau projet
        self.progress.set(0)

        self.output_dir = self.video_info['title']
        os.makedirs(self.output_dir, exist_ok=True)

        threading.Thread(target=self.process_video).start()

    def process_video(self):
        youtube_link = self.video_info.get('webpage_url')
        if not youtube_link:
            messagebox.showerror("Erreur", "Lien vidéo manquant.")
            return
        
        try:
            original_clip, segments = self.download_and_split_video(youtube_link, self.output_dir)

            model = whisper.load_model("base")

            total_segments = len(segments)
            for i, segment in enumerate(segments):
                audio_temp_path = os.path.join(self.output_dir, f"temp_audio_{i}.wav")
                segment.audio.write_audiofile(audio_temp_path, codec='pcm_s16le')
                
                result = model.transcribe(audio_temp_path, language="fr", fp16=False)

                final_clip = self.generate_dynamic_subtitles(segment, result)
                final_clip = final_clip.set_audio(segment.audio)

                final_clip.write_videofile(os.path.join(self.output_dir, f"segment_{i}_with_subtitles.mp4"), fps=24, audio_codec='aac')

                os.remove(audio_temp_path)

                self.progress.set(((i+1) / total_segments) * 100)
                self.root.update_idletasks()

            self.progress.set(100)
            self.result_button.config(state=tk.NORMAL)

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur pendant le téléchargement ou le traitement: {str(e)}")

    def download_and_split_video(self, youtube_link, output_dir):
        ydl_opts = {
            'format': 'bestvideo+bestaudio',
            'outtmpl': os.path.join(output_dir, 'video.mp4'),
            'merge_output_format': 'mp4'
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_link])

        clip = mp.VideoFileClip(os.path.join(output_dir, 'video.mp4'))
        duration = clip.duration
        segments = []
        start = 0
        segment_duration = 65

        while start < duration:
            end = min(start + segment_duration, duration)
            segment = clip.subclip(start, end)
            width, height = segment.size
            new_height = width * 16 / 9
            if new_height > height:
                new_width = height * 9 / 16
                x_center = (width - new_width) / 2
                segment = segment.crop(x1=x_center, x2=x_center + new_width, y1=0, y2=height)
            else:
                segment = segment.resize(newsize=(width, int(new_height)))
            segments.append(segment)
            start = end

        return clip, segments

    def generate_dynamic_subtitles(self, segment, transcript):
        clips = []
        base_font_size = 50
        color = 'yellow'
        border_color = 'black'
        segment_duration = segment.duration
        last_end_time = 0

        for segment_text in transcript['segments']:
            start_time = segment_text['start']
            end_time = segment_text['end']
            if start_time >= segment_duration:
                break
            if end_time > segment_duration:
                end_time = segment_duration
            if start_time < last_end_time:
                start_time = last_end_time

            words = segment_text['text'].split()
            chunk_size = 3
            for j in range(0, len(words), chunk_size):
                chunk = ' '.join(words[j:j + chunk_size])
                word_start_time = start_time + (j // chunk_size) * ((end_time - start_time) / math.ceil(len(words) / chunk_size))
                word_end_time = word_start_time + ((end_time - start_time) / math.ceil(len(words) / chunk_size))
                if word_end_time <= segment_duration:
                    font_size = self.calculate_font_size(chunk, segment.size[0] * 0.9, base_size=base_font_size)
                    text_clip = (TextClip(chunk, fontsize=font_size, font="Comic-Sans-MS", color=color, stroke_color=border_color, stroke_width=2)
                                 .set_position(("center", "bottom"))
                                 .set_start(word_start_time)
                                 .set_end(word_end_time))
                    clips.append(text_clip)
            last_end_time = word_end_time

        final_clip = CompositeVideoClip([segment] + clips)
        return final_clip

    def calculate_font_size(self, text, max_width, base_size=50):
        font = ImageFont.truetype("arial.ttf", base_size)
        width, _ = font.getsize(text)

        while width > max_width and base_size > 10:  # Limite à une taille minimale de 10
            base_size -= 1
            font = ImageFont.truetype("arial.ttf", base_size)
            width, _ = font.getsize(text)

        return base_size

    def open_results_folder(self):
        os.startfile(self.output_dir)

    def reset_project(self):
        # Réinitialiser les champs de l'interface
        self.link_entry.delete(0, tk.END)
        self.title_label.config(text="")
        self.author_label.config(text="")
        self.duration_label.config(text="")
        self.estimate_label.config(text="")
        self.start_button.config(state=tk.DISABLED)
        self.search_button.config(state=tk.NORMAL)
        self.result_button.config(state=tk.DISABLED)
        self.new_project_button.config(state=tk.DISABLED)
        self.progress.set(0)
        self.video_info = {}
        self.output_dir = ""

if __name__ == "__main__":
    root = tk.Tk()
    app = TikTokBotApp(root)
    root.mainloop()
