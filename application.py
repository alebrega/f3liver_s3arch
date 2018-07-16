from flask import Flask
from models import db, Customer, Product, ScriptTag
from flask import flash,render_template,request,redirect,session, render_template_string, url_for
from  pickle import dumps
import requests, uuid, os,json, shopify,urllib
from pprint import pprint
import libraries
from tasks import make_celery
from celery import chain
from werkzeug.utils import secure_filename
from PIL import Image
from datetime import datetime
import numpy as np
from feature_extractor import FeatureExtractor
import os
import glob
import pickle
from functools import reduce




#CONSTANTS
api_key = "d44aecebcdbbc97c095a6123b6f2efca"
api_secret_key = "dd00f2f32e7c4a93d415c187f1092d6a"
scopes = "read_content,read_themes, write_themes,read_products,read_script_tags, write_script_tags"

os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

application = Flask(__name__)
# load config from the config file we created earlier
application.config.from_object('config')

db.init_app(application)
db.create_all(app=application)

celery = make_celery(application)

FEATURE_IMAGES_FOLDER = 'static/feliver_feature_images/'
PRODUCT_IMAGES_FOLDER = 'static/feliver_product_images/'
USER_IMAGES_FOLDER = 'static/feliver_user_images/'

fe = FeatureExtractor()
features = []
img_paths = []
for feature_path in glob.glob(FEATURE_IMAGES_FOLDER+"*"):
    features.append(pickle.load(open(feature_path, 'rb')))
    img_paths.append(PRODUCT_IMAGES_FOLDER + os.path.splitext(os.path.basename(feature_path))[0] + '.jpg')


@application.errorhandler(404)
def error_404(e):
    # note that we set the 404 status explicitly
    return render_template('errors/404.html'), 404

@application.errorhandler(500)
def error_500(e):
    # note that we set the 404 status explicitly
    return render_template('errors/500.html'), 500

application.register_error_handler(404, error_404)
application.register_error_handler(500, error_500)

@application.route('/index')
@application.route('/')
def index():
    today = datetime.now()
    year = today.year
    link_install=application.config['INSTALL_LINK']
    return render_template('index.html',year=year, link_install=link_install)

@application.route('/app', methods=['GET', 'POST'])
def app():
    shop = request.args.get("shop")
    customer = Customer.query.filter_by(shop=shop).first()

    if customer is None:
        return redirect('/app/install', code=302)
    else:
        images_indexed = Product.query.filter(Product.shop == shop).filter(Product.download == '1').all()
        if images_indexed is not None:
            return render_template('admin/index.html')
        else:
            return render_template('admin/indexing_images.html')


@application.route('/app/install', methods=['GET', 'POST'])
def install():
    shop = request.args.get("shop")
    if shop is not None:
        libraries.delete(shop)
        nonce =uuid.uuid4().hex + uuid.uuid1().hex
        session['nonce'] = nonce
        url="https://"+shop+"/admin/oauth/authorize?client_id="+api_key+"&amp;scope="+scopes+"&amp;redirect_uri="+application.config['REDIRECT_URI']+"&amp;state="+nonce+"&amp;grant_options[]="
        return redirect(url, code=302)
    else:
        link_install=application.config['INSTALL_LINK']
        return render_template('admin/error.html',link_install=link_install)
@application.route('/app/install_ok', methods=['GET', 'POST'])
def install_ok():
    #validate nonce
    if session.get("nonce") == request.args.get("state"):
        code = request.args.get("code")
        hmac = request.args.get("hmac")
        shop = request.args.get("shop")
        PARAMS = {'client_id': api_key,'client_secret':api_secret_key,'code':code}
        url_access_token= 'https://'+shop+'/admin/oauth/access_token'
        c = Customer.query.filter_by(shop=shop).first()
        if c is None:
            r = requests.post(url_access_token,PARAMS).json()
            c = Customer(r['access_token'],hmac,shop)
            db.session.add(c)
            db.session.commit()
            action=application.config['HTTPS']+application.config['HOST']+"/search"
            content=render_template('modals/browse.html',action=action,shop=shop)
            css_content=render_template('modals/modal.html')
            result = chain(get_images(shop),download_images(shop),modify_search_box(shop),add_code_shopify(shop,'body',content),add_code_shopify(shop,'head',css_content),add_webhooks(shop))
            if result:
                return render_template('admin/index.html')
            else:
                if result.parent:
                    return render_template('admin/indexing_images.html')
                else:
                    return render_template('admin/indexing_products.html')
    return render_template('admin/index.html')

@celery.task(name='application.add_webhooks')
def add_webhooks(shop):
    customer = Customer.query.filter_by(shop=shop).first()
    shopify.Session.setup(api_key=api_key, secret=api_secret_key)
    session = shopify.Session(customer.shop, customer.code)
    shopify.ShopifyResource.activate_session(session)

    action=application.config['HTTPS']+application.config['HOST']+"/webhook/product/create"
    sw = shopify.Webhook()
    sw.topic='products/create'
    sw.address: action
    sw.format= "json"
    sw.save()

    s = ScriptTag(sw.id,'webhook-product-create',shop)
    db.session.add(s)
    db.session.commit()

    action=application.config['HTTPS']+application.config['HOST']+"/webhook/product/delete"
    sw = shopify.Webhook()
    sw.topic='products/delete'
    sw.address: action
    sw.format= "json"
    sw.save()

    s = ScriptTag(sw.id,'webhook-product-delete',shop)
    db.session.add(s)
    db.session.commit()

    action=application.config['HTTPS']+application.config['HOST']+"/webhook/product/update"
    sw = shopify.Webhook()
    sw.topic='products/update'
    sw.address: action
    sw.format= "json"
    sw.save()

    s = ScriptTag(sw.id,'webhook-product-update',shop)
    db.session.add(s)
    db.session.commit()

    return True

@application.route('/webhook/product/<action>')
def listen_product_webhook(action):
    if action=='update' or action=='create':
        libraries.indexImages(request.headers.get('X-Shopify-Shop-Domain'))

def get_all_resources(resource, **kwargs):
    resource_count = resource.count(**kwargs)
    resources = []
    if resource_count > 0:
        for page in range(1, ((resource_count-1) // 250) + 2):
            kwargs.update({"limit" : 250, "page" : page})
            resources.extend(resource.find(**kwargs))
    return resources

@application.route('/upload', methods=['GET'])
def upload_form():
    action=application.config['HTTPS']+application.config['HOST']+"/search"
    return render_template('modals/browse.html',action=action)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in application.config['ALLOWED_EXTENSIONS']

@application.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        file = request.files['image_feliver']

        img = Image.open(file.stream)  # PIL image
        uploaded_img_path = USER_IMAGES_FOLDER + datetime.now().isoformat() + str(uuid.uuid4())+ "_" + file.filename
        img.save(uploaded_img_path)
        query = fe.extract(img)
        dists = np.linalg.norm(features - query, axis=1)  # Do search
        ids = np.argsort(dists)[:1000] # Top 30 results
        scores = [(dists[id], img_paths[id]) for id in ids]
        average=0
        for score in scores:
            average=score[0]+average
        average=float(average/len(scores))
        scores = [item for item in scores if item[0] < average]
        return render_template('result_search.html',
                               query_path=uploaded_img_path,
                               scores=scores)
    else:
        return render_template('result_search.html')

@application.route('/app/install_ok', methods=['GET', 'POST'])
def get_images(shop):
    customer = Customer.query.filter_by(shop=shop).first()
    product_images=None
    if customer is not None:
        shopify.Session.setup(api_key=api_key, secret=api_secret_key)
        session = shopify.Session(customer.shop, customer.code)
        shopify.ShopifyResource.activate_session(session)
        products = get_all_resources(shopify.Product)
        product_images = []
        for product in products:
            product_images.extend(shopify.Image.find(product_id=product.id))
            for image in product_images:
                imageHelper = libraries.ImageHelper()
                if imageHelper.exists(image.src):
                    p = Product.query.filter_by(image_src=image.src).first()
                    if p is None:
                        p = Product(product.id,image.src,shop)
                        db.session.add(p)
                        db.session.commit()
    else:
        return False
    return True

@celery.task(name='application.modify_search_box')
#@application.route('/modify_search_box')
def modify_search_box(shop):
    customer = Customer.query.filter_by(shop=shop).first()
    if customer is not None:
        shopify.Session.setup(api_key=api_key, secret=api_secret_key)
        session = shopify.Session(customer.shop, customer.code)
        shopify.ShopifyResource.activate_session(session)
        sp = shopify.ScriptTag()
        sp.event = "onload"
        sp.src="https://"+application.config['HOST']+"/js/search_box.js"
        success = sp.save()
        if sp.errors:
            return str(sp.errors.full_messages())
        else:
            s = ScriptTag(sp.id,sp.display_scope,shop)
            db.session.add(s)
            db.session.commit()
            return True
    return False

@celery.task(name='application.add_code_shopify')
def add_code_shopify(shop,tag,content):
    customer = Customer.query.filter_by(shop=shop).first()
    if customer is not None:
        shopify.Session.setup(api_key=api_key, secret=api_secret_key)
        session = shopify.Session(customer.shop, customer.code)
        shopify.ShopifyResource.activate_session(session)
        theme = shopify.Asset.find('layout/theme.liquid')

        theme.value= theme.value.replace('</'+tag+'>', content+' </'+tag+'>')
        success = theme.save()
        if theme.errors:
            return str(theme.errors.full_messages())
        else:
            s = ScriptTag(theme.theme_id,'content_to_tag-theme_id',shop)
            db.session.add(s)
            db.session.commit()
            return True
    return False



@application.route('/js/<js_file>')
def js(js_file):
    return render_template('assets/'+js_file)

@celery.task(name='application.download_images')
def download_images(shop):
    images=Product.query.filter(Product.shop==shop).filter(Product.download=='0').all()
    if len(images):
        if not os.path.exists(PRODUCT_IMAGES_FOLDER+'/'):
            try:
                os.makedirs(PRODUCT_IMAGES_FOLDER+'/')
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
        for image in images:
            path_file=PRODUCT_IMAGES_FOLDER+'/'+str(image.id)+'.jpg'
            if not os.path.exists(path_file):
                urllib.request.urlretrieve(image.image_src,path_file)
            image.download=True
            db.session.commit()
        indexImages(shop)
    else:
        return False
    return True



def indexImages(shop):
    images=Product.query.filter(Product.shop==shop).filter(Product.indexed=='0').all()
    for image in images:
        img_path=PRODUCT_IMAGES_FOLDER+str(image.id)+".jpg"
        img = Image.open(img_path)  # PIL image
        feature = fe.extract(img)
        feature_path = 'static/feliver_feature_images/' + os.path.splitext(os.path.basename(img_path))[0] + '.pkl'
        pickle.dump(feature, open(feature_path, 'wb'))
        image.indexed=True
        db.session.commit()
    return True
@application.route('/admin/error.html')
def error():
    link_install=application.config['INSTALL_LINK']
    return render_template('admin/error.html',link_install=link_install)

@application.route('/admin/indexing_images.html')
def indexing_images():
    return render_template('admin/indexing_images.html')

@application.route('/admin/indexing_products.html')
def indexing_products():
    return render_template('admin/indexing_products.html')

# run the app.
if __name__ == "__main__":
    application.run()
