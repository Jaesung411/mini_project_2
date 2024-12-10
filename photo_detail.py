from flask import *

photo_detail_bp = Blueprint('photo_detail', __name__)

# 사진 상세 페이지
@photo_detail_bp.route('/photo/<int:photo_id>',methods=['GET','POST'])
def detail(photo_id):
    # URL 쿼리 파라미터 가져오기
    title = request.args.get('title')  # None을 반환할 수 있음
    image_url = request.args.get('image_url')  # None을 반환할 수 있음
    video_url = request.args.get('video_url')

    # 템플릿으로 데이터 전달
    return render_template(
        'photo_detail.html',
        title=title,
        photo_id=photo_id,
        image_url=image_url,
        video_url=video_url
    )