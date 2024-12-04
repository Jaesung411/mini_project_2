from flask import *

admin_user_bp = Blueprint('admin_user', __name__)

# app.register_blueprint(admin_user_bp)

@admin_user_bp.route('/login', methods=['GET','POST'])
def login():
    return redirect(url_for('home'))