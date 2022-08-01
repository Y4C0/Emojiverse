import os
import cv2
from website.CNNmodel.predict import EmotionPrediction


class DetectFace:
    @staticmethod
    def detect(img_name, username, model, shape_predictor, conn):
        # Read the input image
        img = cv2.imread('CNNmodel/images/' + username + "/temp/" + img_name)
        # Convert into grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Load the cascade
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        if len(faces) == 0:
            os.remove('CNNmodel/images/' + username + "/temp/" + img_name)
            return "noface"
        # Draw rectangle around the faces and crop the faces
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
            faces = img[y:y + h, x:x + w]
            res = cv2.resize(faces, dsize=(48, 48), interpolation=cv2.INTER_CUBIC)
            cv2.imwrite('CNNmodel/detectedFaces/' + username + "/" + img_name, res)
            pred = EmotionPrediction()
            return pred.classify(img_name, username, model, shape_predictor, conn)


    @staticmethod
    def detectFromArray(frames, model, shape_predictor, conn, username, filename):
        images = []
        for i in range(len(frames)):
            # Read the input image
            img = cv2.imread(frames[i])
            # Convert into grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Load the cascade
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

            # Detect faces
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            # Draw rectangle around the faces and crop the faces
            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
                faces = img[y:y + h, x:x + w]
                res = cv2.resize(faces, dsize=(48, 48), interpolation=cv2.INTER_CUBIC)
                name = 'CNNmodel/detectedFaces/' + username + '/' + str(i) + '.jpg'
                cv2.imwrite(name, res)
                images.append(name)
        if len(images) == 0:
            # os.remove('CNNmodel/images/' + username + "/" + img_name)
            return "noface"
        pred = EmotionPrediction()
        return pred.classifyArray(images, model, shape_predictor, conn, username, filename)
