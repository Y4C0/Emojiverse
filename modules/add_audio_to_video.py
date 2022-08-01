# from moviepy.editor import *
import moviepy.editor as mpe
import os


class audio_to_video:
    @staticmethod
    def add_audio_to_video(video_path, song_path, username, filename):
        audio = mpe.AudioFileClip(song_path)
        video1 = mpe.VideoFileClip(video_path)
        audio.duration = video1.duration
        final = video1.set_audio(audio)
        final.write_videofile('CNNmodel/images/' + username + '/videos/1' + filename)
        video1.close()
        final.close()
        os.remove(video_path)
