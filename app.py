from flask import *
from admin_user import admin_user_bp
from gallery import gallery_bp
from photo_detail import photo_detail_bp

app = Flask(__name__)
app.secret_key='1234'

app.register_blueprint(admin_user_bp)
app.register_blueprint(gallery_bp)
app.register_blueprint(photo_detail_bp)

@app.route('/')
def welcome():
    return render_template('login.html')

@app.route('/health')
def health_check():
    return "Healthy", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)