import glob
import os
import pickle
from PIL import Image
from feature_extractor import FeatureExtractor

import mimetypes
import requests
from models import db, Customer, Product


PRODUCT_IMAGES_FOLDER = 'static/feliver_product_images/'
FEATURE_IMAGES_FOLDER = 'static/feliver_feature_images/'



def delete(shop):
    customer = Customer.query.filter_by(shop=shop).first()
    if customer is not None:
        db.session.delete(customer)
        db.session.commit()
        products = Product.query.filter_by(shop=shop).all()
        for product in products:
            db.session.delete(product)
            db.session.commit()
            if os.path.exists(PRODUCT_IMAGES_FOLDER+'/'+product.id+'.jpg'):
                os.remove(PRODUCT_IMAGES_FOLDER+'/'+product.id+'.jpg')
            if os.path.exists(FEATURE_IMAGES_FOLDER+product.id+'.pkl'):
                os.remove(FEATURE_IMAGES_FOLDER+product.id+'.pkl')

class ImageHelper:
    def exists(self,path):
        r = requests.head(path)
        return r.status_code == requests.codes.ok
