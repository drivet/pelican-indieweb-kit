import uuid
import os

from PIL import Image
from flask import Response
from flask import request
from flask import Blueprint
from flask import current_app as app
from flask_indieauth import requires_indieauth
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'PNG', 'JPG', 'JPEG', 'GIF'])
IMAGE_SIZE = 1024

media_bp = Blueprint('media_bp', __name__)


@media_bp.route('/', methods=['POST'], strict_slashes=False)
@requires_indieauth
def handle_media():
    # check if the post request has the file part
    if 'file' not in request.files:
        return Response(response='no file part', status=400)
    file = request.files['file']

    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return Response(response='no selected file', status=400)

    if file and allowed_file(file.filename):
        filename = create_filename(secure_filename(file.filename))
        print('saving file: ' + filename)
        abs_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(abs_filename)
        outfile = make_image(app.config['UPLOAD_FOLDER'], filename)
        resp = Response(status=201)
        location = app.config['WEBSITE_URL'] + '/media/' + outfile
        resp.headers['Location'] = location
        return resp


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def create_filename(filename):
    base, ext = os.path.splitext(filename)
    return str(uuid.uuid4()) + ext


def make_image(folder, filename):
    infile = os.path.join(folder, filename)
    outfile = os.path.join(folder, '0_' + filename)
    try:
        im = Image.open(infile)
        im.thumbnail((IMAGE_SIZE, IMAGE_SIZE), Image.ANTIALIAS)
        im.save(outfile, "JPEG")
        return '0_' + filename
    except IOError:
        print("cannot create thumbnail for '%s'" % infile)
