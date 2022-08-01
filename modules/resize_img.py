from PIL import Image


class resize_image():
    @staticmethod
    def resize(path):
        basewidth = 70
        img = Image.open(path)
        wpercent = (basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((basewidth, hsize), Image.ANTIALIAS)
        img.save(path)
