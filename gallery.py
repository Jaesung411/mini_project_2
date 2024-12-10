from flask import *
import os
import boto3
from datetime import datetime
from DB.imagedb import *

gallery_bp = Blueprint('gallery', __name__)

# 샘플 사진 데이터
photos = [{"id": i, "title": f"사진 {i}", "description": "이 사진은 샘플 사진입니다."} for i in range(100)]
s3 = boto3.client('s3')
S3_BUCKET = 'mywebimagevideo'
S3_REGION = "ap-northeast-3"

@gallery_bp.route('/home', methods=['GET','POST'])
def gallery_list():
    if request.method == "POST":
        return redirect(url_for('gallery.gallery_list'))
    else:
        # DB에서 사용자의 사진 가져오기
        images = imageDAO().get_files_by_userid(session['userInfo']['userId'])
        
        # photos 리스트 초기화
        photos = []
        for image in images:
            element = {"id": image['file_id'], "title": image['file_name'], "image_path": image['image_path'], "video_path": image['video_path']}
            photos.append(element)
       
        # 현재 페이지 번호 가져오기 (기본값은 1)
        page = int(request.args.get('page', 1))
        per_page = 6  # 한 페이지에 보여줄 사진 개수
        start = (page - 1) * per_page
        end = start + per_page

        total_pages = (len(photos) + per_page - 1) // per_page  # 총 페이지 수

        # 현재 페이지의 사진 데이터 슬라이싱
        current_photos = photos[start:end]
        pages = get_pagination(page, total_pages)

        return render_template('gallery.html', 
                               photos=current_photos, 
                               page=page, 
                               pages=pages, 
                               total_pages=total_pages)

@gallery_bp.route('/search')    
def search():
    query = request.args.get('query', '')

    if query:
        # 데이터베이스나 데이터 리스트에서 검색어가 포함된 가게를 필터링합니다.
        filtered_list = [photo for photo in photos if query.lower() in photo['title'].lower()]
    else:
        filtered_list = photos  # 검색어가 없을 경우 전체 목록 반환

    # 페이지네이션 처리가 필요할 경우 추가
    page = request.args.get('page', 1, type=int)
    per_page = 6
    total_pages = (len(filtered_list) - 1) // per_page + 1
    paginated_list = filtered_list[(page - 1) * per_page: page * per_page]
    pages = get_pagination(page, total_pages)

    return render_template('gallery.html', 
                            photos=paginated_list , 
                            page=page, 
                            pages=pages, 
                            total_pages=total_pages,
                            query=query)

# def get_images_by_query(query):
#     # 데이터베이스에서 쿼리를 사용해 이미지 목록을 검색하는 예시 함수
#     # 이 부분은 실제 구현에 맞게 수정 필요
#     return images
    
def get_pagination(page, total_pages, max_visible=10):
    """
    Pagination logic to handle truncation.
    """
    if total_pages <= max_visible:
        return list(range(1, total_pages + 1))

    visible_pages = []
    visible_pages.append(1)
    if page > 3:
        visible_pages.append('...')

    start = max(2, page - 1)
    end = min(total_pages - 1, page + 1)
    visible_pages.extend(range(start, end + 1))

    if page < total_pages - 2:
        visible_pages.append('...')
        visible_pages.append(total_pages)

    return visible_pages

@gallery_bp.route('/add_image', methods=['GET','POST'])
def add_image():
    # 폼 데이터와 파일 가져오기
    title = request.form['title']
    image = request.files['image']
    video = request.files['video']
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    # HTML 폼에서 파일 가져오기
    # if 'file' not in request.files:
    #     return "No file uploaded", 400

    # file = request.files['file']
    # if file.filename == '':
    #     return "No selected file", 400

    # S3로 파일 업로드
    try:
        # S3에 이미지 업로드
        s3.upload_fileobj(
            image,
            S3_BUCKET,
            f"images/{str(session['userInfo']['userId'])}/{current_datetime}_{image.filename}",  # S3 내 경로
            # ExtraArgs={'ACL': 'public-read'}
        )

        # S3에 동영상 업로드
        s3.upload_fileobj(
            video,
            S3_BUCKET,
            f"videos/{str(session['userInfo']['userId'])}/{current_datetime}_{video.filename}",  # S3 내 경로
            # ExtraArgs={'ACL': 'public-read'}
        )

        image_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/images/{str(session['userInfo']['userId'])}/{current_datetime}_{image.filename}"
        video_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/videos/{str(session['userInfo']['userId'])}/{current_datetime}_{video.filename}"
        imageDAO().insert_file(session['userInfo']['userId'], title, current_datetime, current_datetime, image_url, video_url)
        flash("업로드 성공")
        return redirect(url_for('gallery.gallery_list'))
    except Exception as e:
        print(e)
        flash("업로드 실패")
        return redirect(url_for('gallery.gallery_list'))
    
@gallery_bp.route('/delete_image/<int:image_id>', methods=['POST'])
def delete_image(image_id):
    try:
        # DB에서 이미지 경로 가져오기
        image = imageDAO().get_file_by_id(image_id)
        if not image:
            flash("사진을 찾을 수 없습니다.")
            return redirect(url_for('gallery.gallery_list'))

        image_path = image['image_path']
        video_path = image['video_path']

        # S3에서 이미지 파일 삭제
        image_key = image_path.replace(f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/", "")
        print(f"Deleting image from S3 with Key: {image_key}")
        s3.delete_object(
            Bucket=S3_BUCKET,
            Key=image_key
        )

        # S3에서 비디오 파일 삭제
        video_key = video_path.replace(f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/", "")
        print(f"Deleting video from S3 with Key: {video_key}")
        s3.delete_object(
            Bucket=S3_BUCKET,
            Key=video_key
        )

        # DB에서 이미지 정보 삭제
        imageDAO().delete_file(image_id)

        flash("사진과 동영상이 성공적으로 삭제되었습니다.")
        return redirect(url_for('gallery.gallery_list'))

    except Exception as e:
        print(f"Error: {e}")  # 에러 메시지 출력
        flash("삭제 실패")
        return redirect(url_for('gallery.gallery_list'))

