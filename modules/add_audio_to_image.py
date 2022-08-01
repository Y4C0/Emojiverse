from moviepy.editor import AudioFileClip, ImageClip


class audio_to_image:
    @staticmethod
    def add_audio_to_static_image(image_path, audio_path, output_path):
        """Create and save a video file to `output_path` after
        combining a static image that is located in `image_path`
        with an audio file in `audio_path`"""
        codec = "libx264"
        format = 'yuv420p'
        ffmpeg_params = []
        ffmpeg_params.extend(['-pixel_format', str(format)])

        # create the audio clip object
        audio_clip = AudioFileClip(audio_path)
        # create the image clip object
        image_clip = ImageClip(image_path)
        # use set_audio method from image clip to combine the audio with the image
        video_clip = image_clip.set_audio(audio_clip)
        # specify the duration of the new clip to be the duration of the audio clip
        video_clip.duration = audio_clip.duration
        # set the FPS to 1
        video_clip.fps = 1
        # write the resuling video clip
        video_clip.write_videofile(output_path, codec=codec, ffmpeg_params=ffmpeg_params)

# audio2image = add_audio_to_image()
# audio2image.add_static_image_to_audio(r"C:\Users\Yarden\Desktop\images\surprised.jpg", r"C:\Users\Yarden\Desktop\samurai_jack.mp3", "output.mp4")