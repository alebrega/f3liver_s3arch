import mimetypes
import requests

class ImageHelper:
    def exists(self,path):
        r = requests.head(path)
        return r.status_code == requests.codes.ok
