import tensorflow as tf
from tflearn import DNN
import time
import numpy as np
import dlib
import cv2
import os
from skimage.feature import hog
from website.CNNmodel.parameters import DATASET, TRAINING, NETWORK, VIDEO_PREDICTOR
from website.CNNmodel.model import build_model
from website.modules.add_emoji import AddEmoji


class EmotionPrediction:

    window_size = 24
    window_step = 6

    def load_model(self):
        model = None
        with tf.Graph().as_default():
            print( "loading pretrained model...")
            network = build_model()
            model = DNN(network)
            if os.path.isfile(TRAINING.save_model_path):
                model.load(TRAINING.save_model_path)
            else:
                print( "Error: file '{}' not found".format(TRAINING.save_model_path))
        return model

    def get_landmarks(self, image, rects, predictor):
        # this function have been copied from http://bit.ly/2cj7Fpq
        if len(rects) > 1:
            raise "TooManyFaces"
        if len(rects) == 0:
            raise "NoFaces"
        return np.matrix([[p.x, p.y] for p in predictor(image, rects[0]).parts()])

    def sliding_hog_windows(self, image):
        hog_windows = []
        for y in range(0, NETWORK.input_size, self.window_step):
            for x in range(0, NETWORK.input_size, self.window_step):
                window = image[y:y+self.window_size, x:x+self.window_size]
                hog_windows.extend(hog(window, orientations=8, pixels_per_cell=(8, 8),
                                                cells_per_block=(1, 1), visualize=False))
        return hog_windows

    def predict(self, image, model, shape_predictor=None):
        # get landmarks
        if NETWORK.use_landmarks or NETWORK.use_hog_and_landmarks or NETWORK.use_hog_sliding_window_and_landmarks:
            face_rects = [dlib.rectangle(left=0, top=0, right=NETWORK.input_size, bottom=NETWORK.input_size)]
            face_landmarks = np.array([self.get_landmarks(image, face_rects, shape_predictor)])
            features = face_landmarks
            if NETWORK.use_hog_sliding_window_and_landmarks:
                hog_features = self.sliding_hog_windows(image)
                hog_features = np.asarray(hog_features)
                face_landmarks = face_landmarks.flatten()
                features = np.concatenate((face_landmarks, hog_features))
            else:
                hog_features, _ = hog(image, orientations=8, pixels_per_cell=(16, 16),
                                        cells_per_block=(1, 1), visualize=True)
                hog_features = np.asarray(hog_features)
                face_landmarks = face_landmarks.flatten()
                features = np.concatenate((face_landmarks, hog_features))
            tensor_image = image.reshape([-1, NETWORK.input_size, NETWORK.input_size, 1])
            predicted_label = model.predict([tensor_image, features.reshape((1, -1))])
            return self.get_emotion(predicted_label[0])
        else:
            tensor_image = image.reshape([-1, NETWORK.input_size, NETWORK.input_size, 1])
            predicted_label = model.predict(tensor_image)
            return self.get_emotion(predicted_label[0])
        return None

    def get_emotion(self, label):
        if VIDEO_PREDICTOR.print_emotions:
            print( "- Angry: {0:.1f}%\n- Happy: {1:.1f}%\n- Sad: {2:.1f}%\n- Surprise: {3:.1f}%\n- Neutral: {4:.1f}%".format(
                    label[0]*100, label[1]*100, label[2]*100, label[3]*100, label[4]*100))
        label = label.tolist()
        return VIDEO_PREDICTOR.emotions[label.index(max(label))], max(label)


    def classify(self, img_name, username, model, shape_predictor, conn):
        image = cv2.imread('CNNmodel/detectedFaces/' + username + "/" + img_name, 0)
        start_time = time.time()
        emotion, confidence = self.predict(image, model, shape_predictor)
        total_time = time.time() - start_time
        print( "Prediction: {0} (confidence: {1:.1f}%)".format(emotion, confidence*100))
        print( "time: {0:.1f} sec".format(total_time))
        AddEmoji.emoji_to_image(img_name, username, emotion, conn)
        return emotion


    def init_model(self):
        model = self.load_model()
        shape_predictor = dlib.shape_predictor(DATASET.shape_predictor_path)
        return model, shape_predictor


    def classifyArray(self, images, model, shape_predictor, conn, username, filename):
        emotions = []
        for i in range(len(images)):
            image = cv2.imread(images[i], 0)
            emotion, confidence = self.predict(image, model, shape_predictor)
            emotions.append(emotion)
        chosen_emotion = self.find_emotion(emotions)
        AddEmoji.emoji_to_video(filename, username, chosen_emotion, conn)
        return chosen_emotion


    def find_emotion(self, emotions):
        emotion_dict = {
            "Angry": 0,
            "Disgust": 0,
            "Fear": 0,
            "Happy": 0,
            "Sad": 0,
            "Surprise": 0,
            "Neutral": 0
        }
        for emotion in emotions:
            emotion_dict[emotion] += 1
        print(emotion_dict)
        return max(emotion_dict, key=emotion_dict.get)
