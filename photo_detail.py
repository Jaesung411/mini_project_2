from flask import *
from DB.imagedb import imageDAO  # imageDAO import 추가
from datetime import datetime

photo_detail_bp = Blueprint('photo_detail', __name__)

@photo_detail_bp.route('/photo/<int:photo_id>', methods=['GET', 'POST'])
def detail(photo_id):
    # 데이터베이스에서 이미지 정보 가져오기
    photo = imageDAO().get_file_by_id(photo_id)
    if not photo:
        flash("사진을 찾을 수 없습니다.")
        return redirect(url_for('gallery.gallery_list'))

    # 날짜 포맷팅
    update_at = photo.get('update_at')
    if update_at:
        try:
            # 저장된 문자열을 datetime 객체로 변환 (예: "20241210_000000" → 2024-12-10)
            parsed_date = datetime.strptime(update_at, '%Y%m%d_%H%M%S')
            date_taken = parsed_date.strftime('%Y년 %m월 %d일')  # 원하는 형식으로 변환
        except ValueError:
            date_taken = "날짜 형식 오류"
    else:
        date_taken = "날짜 정보 없음"

    # 템플릿으로 데이터 전달
    return render_template(
        'photo_detail.html',
        title=photo['file_name'],
        photo_id=photo['file_id'],
        image_url=photo['image_path'],
        video_url=photo['video_path'],
        date_taken=date_taken  # 포맷된 날짜 추가
    )
