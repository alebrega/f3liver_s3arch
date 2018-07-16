import glob,os, pickle, shopify, requests, mimetypes
from PIL import Image
from feature_extractor import FeatureExtractor
from models import db, Customer, Product


PRODUCT_IMAGES_FOLDER = 'static/feliver_product_images/'
FEATURE_IMAGES_FOLDER = 'static/feliver_feature_images/'


def remove_code_shopify(shop,content,layout):
    customer = Customer.query.filter_by(shop=shop).first()
    if customer is not None:
        shopify.Session.setup(api_key=api_key, secret=api_secret_key)
        session = shopify.Session(customer.shop, customer.code)
        shopify.ShopifyResource.activate_session(session)
        theme = shopify.Asset.find(layout)
        theme.value= theme.value.replace(content, '')
        success = theme.save()
        if theme.errors:
            return str(theme.errors.full_messages())
        else:
            s = ScriptTag(theme.theme_id,'remove_code_shopify-theme_id',shop)
            db.session.add(s)
            db.session.commit()
            return True
    return False

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
