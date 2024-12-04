from flask import *

photo_detail_bp = Blueprint('photo_detail', __name__)

# 사진 상세 페이지
@photo_detail_bp.route('/photo/<int:photo_id>',methods=['GET','POST'])
def detail(photo_id):
    return render_template('photo_detail.html', photo_id=photo_id)