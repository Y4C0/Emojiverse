# app.py
import os
from flask import Flask, request, session, redirect, url_for, render_template, flash, send_from_directory
from flask import Response
import psycopg2  # pip install psycopg2
import psycopg2.extras
import re
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pandas as pd
from website.modules.forms import ContactForm
from website.CNNmodel.DetectFace import DetectFace
from website.CNNmodel.predict import EmotionPrediction
from website.modules.add_audio_to_image import audio_to_image
from website.modules.resize_img import resize_image
from website.modules.video_detection import Video_detect
from website.modules.add_audio_to_video import audio_to_video
from website.modules.add_emoji import AddEmoji
from flask import send_file
import uuid  # for unique filenames

UPLOAD_FOLDER = 'CNNmodel/images/'
def create_app():
    app = Flask(__name__)
    app.secret_key = 'cairocoders-ednalan'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    DB_HOST = "localhost"
    DB_NAME = "postgres"
    DB_USER = "postgres"
    DB_PASS = "123456"

conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'mp4'])
predict = EmotionPrediction()
model, shape_predictor = predict.init_model()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Check if user is loggedin
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM gallery WHERE username = %s', [session['username']])
        data = cursor.fetchone()
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'], images=data[1], videos=data[2], total=data[3])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/login/', methods=['GET', 'POST'])
def login():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        # Fetch one record and return result
        account = cursor.fetchone()
        if account:
            password_rs = account['password']
            # If account exists in users table in out database
            if check_password_hash(password_rs, password):
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                # Redirect to home page
                return redirect(url_for('home'))
            else:
                # Account doesnt exist or username/password incorrect
                flash('Incorrect username/password')
        else:
            # Account doesnt exist or username/password incorrect
            flash('Incorrect username/password')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        fullname = request.form['fullname']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        _hashed_password = generate_password_hash(password)

        # Check if account exists using MySQL
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            flash('Account already exists!')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address!')
        elif not re.match(r'[A-Za-z0-9]+', username):
            flash('Username must contain only characters and numbers!')
        elif not username or not password or not email:
            flash('Please fill out the form!')
        else:
            # Account doesnt exists and the form data is valid, now insert new account into users table
            cursor.execute("INSERT INTO users (fullname, username, password, email) VALUES (%s,%s,%s,%s)",
                           (fullname, username, _hashed_password, email))
            cursor.execute("INSERT INTO gallery (username, numofimages, numofvideos, totalobjects) VALUES (%s,%s,%s,%s)",
                           (username, 0, 0, 0))
            conn.commit()
            os.mkdir("CNNmodel/images/" + username)
            os.mkdir("CNNmodel/images/" + username + "/temp")
            os.mkdir("CNNmodel/detectedFaces/" + username)
            flash('You have successfully registered!')
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        flash('Please fill out the form!')
    # Show registration form with message (if any)
    return render_template('register.html')


@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    # Redirect to login page
    return redirect(url_for('login'))


@app.route('/profile')
def profile():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Check if user is loggedin
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM users WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        cursor.execute('SELECT * FROM gallery WHERE username = %s', [session['username']])
        data = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account, images=data[1], videos=data[2])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/upload', methods=['POST', 'GET'])
def upload():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM users WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        pattern = re.compile(r"[A-Za-z0-9]+")
        if 'file' not in request.files:
            return render_template('upload.html')
        file = request.files['file']
        if file.filename == '':
            flash('No image selected for uploading')
            return render_template('upload.html')
        if file and allowed_file(file.filename):
            ext = '.' + file.filename.split('.')[1]
            name = request.form.get('file_name')
            # Creates a random filename: str(uuid.uuid4())
            filename = str(uuid.uuid4()) + ext if name == '' or not re.fullmatch(pattern, name) else name + ext
            file.save(os.path.join(app.config['UPLOAD_FOLDER'] + account['username'] + "/temp", filename))
            if ext == '.mp4':
                emotion = Video_detect.extractImages(account['username'], filename, model, shape_predictor, conn)
                direct = 'CNNmodel/detectedFaces/' + account['username']
                for f in os.listdir(direct):
                    os.remove(os.path.join(direct, f))
                session['filename'] = filename
                if emotion == "noface":
                    flash('No face detected')
                    return render_template('upload.html')
                else:
                    cursor.execute(
                        'UPDATE gallery SET numofvideos=numofvideos+1, totalobjects=totalobjects+1 WHERE username=%s',
                        [session['username']])
                    conn.commit()
                    return redirect(url_for('detected_mood', emotion=emotion, type='video'))
            else:
                emotion = DetectFace.detect(filename, account['username'], model, shape_predictor, conn)
                if emotion != "noface":
                    username = account['username']
                    session['filename'] = filename
                    cursor.execute('UPDATE gallery SET numofimages=numofimages+1, totalobjects=totalobjects+1 WHERE username=%s', [session['username']])
                    conn.commit()
                    return redirect(url_for('detected_mood', emotion=emotion, type='image'))
                else:
                    flash('No face detected')
                    return render_template('upload.html')
        else:
            flash('Allowed image types are - png, jpg, jpeg, gif')
            flash('Allowed video types are - mp4')
            return render_template('upload.html')
    return redirect(url_for('login'))


@app.route('/upload/<username>/<filename>')
def send_image(filename, username):
    return send_from_directory("CNNmodel/images/" + username + "/", filename)


@app.route('/gallery')
def get_gallery():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM users WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        username = account['username']
        path = 'CNNmodel/images/' + username + "/"
        image_names = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        if os.path.exists(path + "videos"):
            video_names = os.listdir(path + "videos")
        else:
            video_names = []
        return render_template("gallery.html", image_names=image_names, video_names=video_names, username=username)
    return redirect(url_for('login'))


@app.route('/contactus', methods=["GET","POST"])
def get_contact():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM users WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        name = account['fullname']
        email = account['email']
        form = ContactForm()
        # here, if the request type is a POST we get the data on contat
        #forms and save them else we return the contact forms html page
        if request.method == 'POST':
            subject = request.form["subject"]
            message = request.form["message"]
            if subject == '' or message == '':
                flash("You must fill all the fields")
                return render_template('contactus.html', form=form, name=name, email=email)
            else:
                res = pd.DataFrame({'name':name, 'email':email, 'subject':subject ,'message':message}, index=[0])
                res.to_csv('./contactusMessage.csv', mode='a', header=not os.path.exists('./contactusMessage.csv'))
                flash("The message is sent!")
                return render_template('contactus.html', form=form, name=name, email=email)
        else:
            return render_template('contactus.html', form=form, name=name, email=email)
    return redirect(url_for('login'))


@app.route('/detected_mood/<emotion>/<type>', methods=['GET', 'POST'])
def detected_mood(emotion, type):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM users WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        username = account['username']
        if request.method == 'GET':
            return render_template('detectedmood.html', filename=session['filename'], emotion=emotion, username=username, type=type)
        if request.method == 'POST':
            change_emotion = request.form.get("emotion")
            if change_emotion == 'Choose emotion':
                flash('You did not specify emotion.')
                return render_template('detectedmood.html', filename=session['filename'], emotion=emotion,
                                       username=username, type=type)
            else:
                if type == 'image':
                    AddEmoji.emoji_to_image(session['filename'], username, change_emotion, conn)
                else:
                    AddEmoji.emoji_to_video(session['filename'], username, change_emotion, conn)
            return redirect(url_for('detected_mood', emotion=change_emotion, type=type))
    return redirect(url_for('login'))


@app.route('/upload/<emotion>')
def send_emoji(emotion):
    return send_from_directory("CNNmodel/emojis/", emotion + ".png")


@app.route('/chooseasong/<emotion>/<type>', methods=['GET', 'POST'])
def chooseasong(emotion, type):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM users WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        username = account['username']
        if request.method == 'GET':
            directory = app.config['UPLOAD_FOLDER'] + account['username'] + "/temp"
            # remove all temporary files from user's temp folder
            for f in os.listdir(directory):
                os.remove(os.path.join(directory, f))
            songs = os.listdir('songs/' + emotion + '/')
            song_names = [i.split('_')[0] for i in songs]
            artists = [j.split('.')[0] for j in [i.split('_')[1] for i in songs]]
            cursor.execute('SELECT * FROM song WHERE username=%s and emotion=%s', [username, emotion])
            song_list = cursor.fetchall()
            return render_template('chooseasong.html', songs=zip(song_names, artists, songs), song_list=song_list, emotion=emotion, username=username)
        if request.method == 'POST':
            session['choice'] = request.form.get("options")
            return redirect(url_for('song_to_image', emotion=emotion, type=type))
    return redirect(url_for('login'))


@app.route('/<emotion>/<song>')
def song_mp3(emotion, song):
    return send_file('songs/' + emotion + '/' + song, attachment_filename=song)


@app.route('/song_to_image/<emotion>/<type>')
def song_to_image(emotion, type):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM users WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        username = account['username']
        filename = session['filename'].split('.')[0]
        # execute module song_with_image
        # args: image_path, audio_path, output_path
        if (os.path.exists("songs/" + emotion + "/" + session['choice'])):
            song_path = "songs/" + emotion + "/" + session['choice']
        else:
            song_path = "CNNmodel/userfiles/" + session['choice']
        if type == 'image':
            output_path = createFolderIfNotExist(username, filename)
            image_path = "CNNmodel/images/" + username + "/" + session['filename']
            audio_to_image.add_audio_to_static_image(image_path, song_path, output_path)
            os.remove(image_path)
            vidname = filename + ".mp4"
            cursor.execute('UPDATE gallery SET numofimages=numofimages-1, numofvideos=numofvideos+1 WHERE username=%s',
                           [session['username']])
            conn.commit()
        else:
            video_path = "CNNmodel/images/" + username + "/videos/" + session['filename']
            audio_to_video.add_audio_to_video(video_path, song_path, username, session['filename'])
            vidname = '1' + session['filename']
        return render_template('songwithimage.html', file=vidname, username=username)
    return redirect(url_for('login'))


@app.route('/display/<username>/<filename>')
def display_video(filename, username):
    return send_file('CNNmodel/images/' + username + '/videos/' + filename, attachment_filename=filename)


def createFolderIfNotExist(username, filename):
    path = "CNNmodel/images/" + username + "/videos"
    # Check whether the specified path exists or not
    isExist = os.path.exists(path)
    if not isExist:
        # Create a new directory because it does not exist
        os.makedirs(path)
    return path + "/" + filename + ".mp4"


@app.route('/<filetype>/<username>/<filename>')
def delete_file(username, filename, filetype):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if filetype == 'image':
        path = "CNNmodel/images/" + username + "/" + filename
        cursor.execute('UPDATE gallery SET numofimages=numofimages-1, totalobjects=totalobjects-1 WHERE username=%s',[session['username']])
    else:
        path = "CNNmodel/images/" + username + "/videos/" + filename
        cursor.execute('UPDATE gallery SET numofvideos=numofvideos-1, totalobjects=totalobjects-1 WHERE username=%s',[session['username']])
    conn.commit()
    os.remove(path)
    return ('', 204)


@app.route('/support')
def support():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Check if user is loggedin
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM users WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('support.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/download/<filetype>/<username>/<filename>')
def downloadFile(username, filename, filetype):
    path = "CNNmodel/images/" + username + "/" + filename if filetype == 'image' \
        else "CNNmodel/images/" + username + "/videos/" + filename
    return send_file(path, as_attachment=True)


@app.route("/emojis", methods=["GET", "POST"])
def emojis():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM users WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        username = account['username']
        cursor.execute('SELECT * FROM emoji WHERE username = %s', [account['username']])
        emoji_names = [i[2] for i in cursor.fetchall()]
        emotion_list = ["Happy", "Sad", "Angry", "Fear", "Surprise", "Disgust", "Neutral"]
        default_list = []
        categories = {"Happy": None, "Sad": None, "Angry": None, "Fear": None, "Surprise": None, "Disgust": None, "Neutral": None}
        for emo in emotion_list:
            cursor.execute('SELECT filename FROM emoji WHERE username=%s and emotion=%s and isdefault=%s',
                           [username, emo, "true"])
            file_emoji = cursor.fetchone()
            if file_emoji:
                default_list.append(file_emoji[0])
            else:
                default_list.append("null")
            cursor.execute('SELECT filename FROM emoji WHERE username=%s and emotion=%s and isdefault=%s',
                           [username, emo, "false"])
            categories[emo] = [item for sublist in cursor.fetchall() for item in sublist]
        happy = categories["Happy"]
        sad = categories["Sad"]
        angry = categories["Angry"]
        fear = categories["Fear"]
        surprise = categories["Surprise"]
        disgust = categories["Disgust"]
        neutral = categories["Neutral"]
        if 'file' not in request.files:
            return render_template('emojis.html', happy=happy, sad=sad, angry=angry, fear=fear, surprise=surprise,
                                   disgust=disgust, neutral=neutral, categories=categories, default_list=default_list,
                                   emoji_names=emoji_names, username=username)
        file = request.files['file']
        if file.filename == '':
            flash('No image selected for uploading')
            return render_template('emojis.html', happy=happy, sad=sad, angry=angry, fear=fear, surprise=surprise,
                                   disgust=disgust, neutral=neutral, categories=categories, default_list=default_list,
                                   emoji_names=emoji_names, username=username)
        if file and allowed_file(file.filename):
            ext = '.' + file.filename.split('.')[1]
            # Creates a random filename
            filename = str(uuid.uuid4()) + ext
            file.save(os.path.join("CNNmodel/userfiles/", filename))
            resize_image.resize(os.path.join("CNNmodel/userfiles/", filename))
            emotion = request.form.get('emotion')
            if emotion == 'Emotion':
                flash('You must choose emotion category')
                return render_template('emojis.html', happy=happy, sad=sad, angry=angry, fear=fear, surprise=surprise,
                                       disgust=disgust, neutral=neutral, categories=categories,
                                       default_list=default_list,
                                       emoji_names=emoji_names, username=username)
            else:
                flag = "true" if request.form.get("toggle") is not None else "false"
                if flag:
                    cursor.execute(
                        'UPDATE emoji SET isdefault=%s WHERE username=%s and emotion=%s',
                        ["false", username, emotion])
                cursor.execute(
                    'INSERT INTO emoji (username, emotion, filename, isdefault) VALUES (%s, %s, %s, %s)',
                    [username, emotion, filename, flag])
                conn.commit()
                flash('Emoji successfully uploaded!')
                return redirect(url_for('emojis'))
        else:
            flash('Allowed image types are - png, jpg, jpeg, gif')
            return render_template('emojis.html', happy=happy, sad=sad, angry=angry, fear=fear, surprise=surprise,
                                   disgust=disgust, neutral=neutral, categories=categories, default_list=default_list,
                                   emoji_names=emoji_names, username=username)
    return redirect(url_for('login'))


@app.route('/emojis/<filename>')
def send_user_emoji(filename):
    return send_from_directory("CNNmodel/userfiles/", filename)


@app.route('/<filename>')
def delete_emoji(filename):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    path = "CNNmodel/userfiles/" + filename
    cursor.execute('DELETE FROM emoji WHERE filename=%s', [filename])
    conn.commit()
    os.remove(path)
    return ('', 204)


@app.route('/download/<filename>')
def download_emoji(filename):
    path = "CNNmodel/userfiles/" + filename
    return send_file(path, as_attachment=True)


@app.route("/songs", methods=["GET", "POST"])
def songs():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM users WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        username = account['username']
        cursor.execute('SELECT * FROM song WHERE username = %s', [username])
        song_list = cursor.fetchall()
        if 'file' not in request.files:
            return render_template('songs.html', songs=song_list, username=username)
        file = request.files['file']
        if file.filename == '':
            flash('No song selected for uploading')
            return render_template('songs.html', songs=song_list, username=username)
        if file and file.filename.split('.')[1] == "mp3":
            ext = '.' + file.filename.split('.')[1]
            # Creates a random filename
            filename = str(uuid.uuid4()) + ext
            file.save(os.path.join("CNNmodel/userfiles/", filename))
            song_name = request.form.get('song_name')
            artist_name = request.form.get('artist_name')
            emotion = request.form.get('emotion')
            if emotion == 'Emotion' or song_name == '' or artist_name == '':
                flash('You must fill all the fields.')
                return render_template('songs.html', songs=song_list, username=username)
            else:
                cursor.execute(
                    'INSERT INTO song (username, song_name, artist_name, filename, emotion) VALUES (%s, %s, %s, %s, %s)',
                    [username, song_name, artist_name, filename, emotion])
                conn.commit()
                flash('Song successfully uploaded!')
                return redirect(url_for('songs'))
        else:
            flash('Allowed song types are - mp3')
            return render_template('songs.html', songs=song_list, username=username)
    return redirect(url_for('login'))


@app.route('/usergallery/<filename>')
def user_song(filename):
    return send_file("CNNmodel/userfiles/" + filename, attachment_filename=filename)


@app.route('/delete/<filename>')
def delete_song(filename):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    path = "CNNmodel/userfiles/" + filename
    os.remove(path)
    cursor.execute('DELETE FROM song WHERE filename=%s', [filename])
    conn.commit()
    return ('', 204)


@app.route('/default/<emotion>/<filename>')
def set_default_emoji(emotion, filename):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('UPDATE emoji set isdefault=%s WHERE username=%s and isdefault=%s and emotion=%s', ["false", session['username'], "true", emotion])
    cursor.execute('UPDATE emoji set isdefault=%s WHERE filename=%s', ["true", filename])
    conn.commit()
    return ('', 204)


@app.route('/default/<emotion>')
def restore_default(emotion):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('UPDATE emoji set isdefault=%s WHERE username=%s and isdefault=%s and emotion=%s', ["false", session['username'], "true", emotion])
    conn.commit()
    return ('', 204)


if __name__ == "__main__":
    app.run(debug=True)
