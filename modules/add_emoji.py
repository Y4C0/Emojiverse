from PIL import Image, ImageDraw, ImageFilter
import psycopg2  # pip install psycopg2
import psycopg2.extras
import moviepy.editor as mp


class AddEmoji:
    @staticmethod
    def emoji_to_image(filename, username, emotion, conn):
        emoji = AddEmoji.get_default_emoji(emotion, username, conn)
        im1 = Image.open('CNNmodel/images/' + username + "/temp/" + filename)
        im2 = Image.open(emoji)
        # Convert image to RGBA
        im2 = im2.convert("RGBA")
        # Convert image to RGBA
        im1 = im1.convert("RGBA")
        # Calculate width to be at the center
        width = (im1.width - im2.width) // 2
        # Calculate height to be at the center
        height = (im1.height - im2.height) // 2
        # Paste the frontImage at (width, height)
        im1.paste(im2, (10, 10), im2)
        # Save this image
        im1.save('CNNmodel/images/' + username + "/" + filename, format="png")

    @staticmethod
    def emoji_to_video(filename, username, emotion, conn):
        emoji = AddEmoji.get_default_emoji(emotion, username, conn)
        video = mp.VideoFileClip('CNNmodel/images/' + username + '/temp/' + filename)
        logo = (mp.ImageClip(emoji)
                .set_duration(video.duration)
                .resize(height=70)  # if you need to resize...
                .margin(right=8, top=8, opacity=0)  # (optional) logo-border padding
                .set_pos(("right", "top")))
        final = mp.CompositeVideoClip([video, logo])
        final.write_videofile('CNNmodel/images/' + username + '/videos/' + filename)
        final.close()


    @staticmethod
    def get_default_emoji(emotion, username, conn):
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT filename FROM emoji WHERE isdefault=%s and emotion=%s and username=%s', ["true", emotion, username])
        filename = cursor.fetchone()
        if filename is not None:
            emoji = 'CNNmodel/userfiles/' + filename[0]
        else:
            emoji = 'CNNmodel/emojis/' + emotion + '.png'
        return emoji
