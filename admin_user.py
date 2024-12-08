from flask import *
import DB.userdb as userdb
from werkzeug.security import* 

admin_user_bp = Blueprint('admin_user', __name__)

@admin_user_bp.route('/login', methods=['GET','POST'])
def login():

    if request.method == "POST":
        email = request.form['email']
        passwd = request.form['password']
        #이메일에 해당하는 회원 정보
        user_info = userdb.userDAO().authenicate(email)

        if user_info == None or not check_password_hash(user_info[3], passwd):
            # user_logger.info("로그인 실패")
            flash("로그인 실패했습니다.")
            return redirect(url_for('admin_user.login'))
        else:
            flash("로그인 성공했습니다.")
            session['userInfo'] = {
                'userId':user_info[0],
                'name':user_info[1],
                'email':user_info[2],
                'nickname':user_info[4]
            }
            # user_logger.info(f'로그인 성공 user_name : {user_info[4]}')
            return redirect(url_for('gallery.gallery_list'))
    else:
        # user_logger.info('GET /login 진입 로그인 창으로"')
        return render_template('login.html')

@admin_user_bp.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == "GET":
        # user_logger.info("회원가입 시도")
        return render_template('signup.html')
    else:
        name = request.form['name']
        nickname = request.form['nickname']
        email = request.form['email']
        passwd = request.form['password']
        confirm_password = request.form['confirm_password']
        print(passwd)
        if passwd != confirm_password:
            flash("동일한 비밀번호가 아닙니다.")
            return render_template('signup.html')
        #비밀번호 암호화 
        hashed_password = generate_password_hash(passwd)
        print(hashed_password)
        ret = userdb.userDAO().create_user(email,hashed_password,nickname,name)
        if ret[0]:
            # user_logger.info(f'{name} 님 회원가입 성공')
            flash(ret[1])
            return redirect(url_for('admin_user.login'))
        else:
            # user_logger.warning(f'회원가입 실패 원인 {ret[1]}')
            flash(ret[1])
            return render_template('signup.html')

@admin_user_bp.route('/logout')    
def logout():
    # user_logger.info(f'{session["userInfo"]["name"]}님 로그아웃')
    session.pop('userInfo', None)
    return redirect(url_for('admin_user.login'))

        