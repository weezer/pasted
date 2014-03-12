import os

import flask

from pasteraw import app
from pasteraw import backend
from pasteraw import decorators
from pasteraw import forms


class BadRequest(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        return rv


@app.route('/', methods=['POST', 'GET'])
@decorators.templated()
def index():
    form = forms.PasteForm()
    if form.validate_on_submit():
        paste_id = backend.save(flask.request.form['content'])
        return flask.redirect(flask.url_for('show_paste', paste_id=paste_id))
    return dict(form=form)


@app.route('/api/v1/pastes', methods=['POST'])
def create_paste():
    form = forms.PasteForm(csrf_enabled=False)
    if form.validate_on_submit():
        paste_id = backend.save(flask.request.form['content'])
        return flask.redirect(flask.url_for('show_paste', paste_id=paste_id))
    raise BadRequest('missing paste content')


@app.route('/<paste_id>')
def show_paste(paste_id):
    content = backend.load(paste_id)
    if content is None:
        flask.abort(404)
    return content, 200, {'Content-Type': 'text/plain'}


@app.errorhandler(404)
def handle_not_found(error):
    return flask.render_template('not_found.html'), 404


@app.errorhandler(BadRequest)
def handle_bad_request(error):
    response = flask.jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route('/favicon.ico')
def favicon():
    return flask.send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/x-icon')