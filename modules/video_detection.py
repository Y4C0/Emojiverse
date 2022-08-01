import cv2
import os
from website.CNNmodel.DetectFace import DetectFace

class Video_detect():

    @staticmethod
    def extractImages(username, filename, model, shape_predictor, conn):
        count = 0
        vidcap = cv2.VideoCapture('CNNmodel/images/' + username + "/temp/" + filename)
        # success, image = vidcap.read()
        success = True
        frames = []
        while success:
            vidcap.set(cv2.CAP_PROP_POS_MSEC, (count*1000))    # extract frame every one second
            success, image = vidcap.read()
            if success:
                name = 'CNNmodel/detectedFaces/' + username + '/' + "frame%d.jpg" % count
                cv2.imwrite(name, image)     # save frame as JPEG file
                frames.append(name)
                count = count + 1
        return DetectFace.detectFromArray(frames, model, shape_predictor, conn, username, filename)
