from flask import *
import os
import boto3
from datetime import datetime
from DB.imagedb import *
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import cv2
import numpy as np
import time

gallery_bp = Blueprint('gallery', __name__)

# 샘플 사진 데이터
photos = [{"id": i, "title": f"사진 {i}", "description": "이 사진은 샘플 사진입니다."} for i in range(100)]
s3 = boto3.client('s3')
S3_BUCKET = 'mywebimagevideo'
S3_REGION = "ap-northeast-3"

# AWS S3 설정 변경필요!
s3 = boto3.client('s3', region_name='ap-northeast-2')
S3_BUCKET = 'testbucketa0'
S3_REGION = 'ap-northeast-2'

# ChromeDriver 설정
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# QR 코드에서 URL 추출
def extract_url(image):
    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(image)
    return data if bbox is not None else None

def rename_downloaded_file(download_dir, original_name, new_name):
    original_path = os.path.join(download_dir, original_name)
    new_path = os.path.join(download_dir, new_name)
    if os.path.exists(original_path):
        os.rename(original_path, new_path)
        return new_path
    return None

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
            photos.gallery_bpend(element)
       
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

def upload_to_s3(file_path, s3_key, image_name=None, video_name=None, title=None, current_datetime=None):
    try:
        s3.upload_file(file_path, S3_BUCKET, s3_key)
        gallery_bp.logger.info(f"Uploaded {file_path} to S3 as {s3_key}")

        # S3 업로드 완료 후 로컬 파일 삭제
        os.remove(file_path)
        gallery_bp.logger.info(f"Deleted local file: {file_path}")

        file_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"

        # RDS에 파일 정보 저장
        if image_name and video_name:
            image_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/images/{str(session['userInfo']['userId'])}/{current_datetime}_{image_name}"
            video_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/videos/{str(session['userInfo']['userId'])}/{current_datetime}_{video_name}"
            imageDAO().insert_file(session['userInfo']['userId'], title, current_datetime, current_datetime, image_url, video_url)

        return file_url
    except Exception as e:
        gallery_bp.logger.error(f"Failed to upload {file_path} to S3: {e}")
        return None

@gallery_bp.route("/extract_url", methods=["POST"])
def extract_url_from_qr():
    image_file = request.files.get("image")
    if image_file:
        file_bytes = np.frombuffer(image_file.read(), np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        url = extract_url(image)
        if url:
            return jsonify({"success": True, "url": url})
        else:
            return jsonify({"success": False, "message": "QR 코드에서 URL을 추출할 수 없습니다."})

    return jsonify({"success": False, "message": "이미지가 업로드되지 않았습니다."})

@gallery_bp.route("/download_upload", methods=["POST"])
def download_upload():
    data = request.get_json()
    url = data.get("url")
    result = download_from_url(url)
    return jsonify({"message": result})

# 요소 존재 여부 확인 및 클릭
def click_element_by_text(driver, tag, text):
    try:
        xpath = f"//{tag}[text()='{text}']"
        element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        element.click()
        gallery_bp.logger.info(f"Clicked on element with text: {text}")
        return True
    except Exception as e:
        gallery_bp.logger.error(f"Failed to click on element with text: {text}, {e}")
        return False

# QR 코드에서 URL을 통해 이미지와 비디오 다운로드
def download_from_url(url):
    driver = None
    try:
        driver = setup_driver()
        driver.get(url)

        current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
        download_dir = os.path.join(os.path.expanduser("~"), "Downloads")

        # 요소 클릭 및 다운로드
        image_click = click_element_by_text(driver, "p", "Image")
        video_click = click_element_by_text(driver, "p", "Video")
        
        image_path, video_path = None, None
        image_s3_url, video_s3_url = None, None
        user_id = str(session['userInfo']['userId'])

        # 이미지 다운로드 및 파일명 변경
        if image_click:
            time.sleep(5)  # 다운로드가 완료되기를 기다림
            new_image_name = f"{user_id}_image_{current_datetime}.jpg"
            image_path = rename_downloaded_file(download_dir, "image.jpg", new_image_name)
            if image_path:
                gallery_bp.logger.info(f"Image downloaded and renamed to {image_path}")
                image_s3_key = f"images/{user_id}/{new_image_name}"
                image_s3_url = upload_to_s3(image_path, image_s3_key)
                if image_s3_url is None:
                    return "Failed to upload image to S3."
            else:
                gallery_bp.logger.error("Failed to rename downloaded image.")
                return "Failed to rename image."

        # 동영상 다운로드 및 파일명 변경
        if video_click:
            time.sleep(5)  # 다운로드가 완료되기를 기다림
            new_video_name = f"{user_id}_video_{current_datetime}.mp4"
            video_path = rename_downloaded_file(download_dir, "video.mp4", new_video_name)
            if video_path:
                gallery_bp.logger.info(f"Video downloaded and renamed to {video_path}")
                video_s3_key = f"videos/{user_id}/{new_video_name}"
                video_s3_url = upload_to_s3(video_path, video_s3_key)
                if video_s3_url is None:
                    return "Failed to upload video to S3."
            else:
                gallery_bp.logger.error("Failed to rename downloaded video.")
                return "Failed to rename video."

        if not image_s3_url and not video_s3_url:
            return "No files uploaded to S3."

        return f"이미지 및 비디오 다운로드 및 S3 업로드가 완료되었습니다. 이미지 URL: {image_s3_url}, 비디오 URL: {video_s3_url}"
    except Exception as e:
        gallery_bp.logger.error(f"Error during download: {e}")
        return f"오류 발생: {e}"
    finally:
        if driver:
            driver.quit()
    
def get_pagination(page, total_pages, max_visible=10):
    """
    Pagination logic to handle truncation.
    """
    if total_pages <= max_visible:
        return list(range(1, total_pages + 1))

    visible_pages = []
    visible_pages.gallery_bpend(1)
    if page > 3:
        visible_pages.gallery_bpend('...')

    start = max(2, page - 1)
    end = min(total_pages - 1, page + 1)
    visible_pages.extend(range(start, end + 1))

    if page < total_pages - 2:
        visible_pages.gallery_bpend('...')
        visible_pages.gallery_bpend(total_pages)

    return visible_pages

# @gallery_bp.route('/add_image', methods=['GET','POST'])
# def add_image():
#     # 폼 데이터와 파일 가져오기
#     title = request.form['title']
#     image = request.files['image']
#     video = request.files['video']
#     current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
#     # HTML 폼에서 파일 가져오기
#     # if 'file' not in request.files:
#     #     return "No file uploaded", 400

#     # file = request.files['file']
#     # if file.filename == '':
#     #     return "No selected file", 400

#     # S3로 파일 업로드
#     try:
#         # S3에 이미지 업로드
#         s3.upload_fileobj(
#             image,
#             S3_BUCKET,
#             f"images/{str(session['userInfo']['userId'])}/{current_datetime}_{image.filename}",  # S3 내 경로
#             # ExtraArgs={'ACL': 'public-read'}
#         )

#         # S3에 동영상 업로드
#         s3.upload_fileobj(
#             video,
#             S3_BUCKET,
#             f"videos/{str(session['userInfo']['userId'])}/{current_datetime}_{video.filename}",  # S3 내 경로
#             # ExtraArgs={'ACL': 'public-read'}
#         )

#         image_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/images/{str(session['userInfo']['userId'])}/{current_datetime}_{image.filename}"
#         video_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/videos/{str(session['userInfo']['userId'])}/{current_datetime}_{video.filename}"
#         imageDAO().insert_file(session['userInfo']['userId'], title, current_datetime, current_datetime, image_url, video_url)
#         flash("업로드 성공")
#         return redirect(url_for('gallery.gallery_list'))
#     except Exception as e:
#         print(e)
#         flash("업로드 실패")
#         return redirect(url_for('gallery.gallery_list'))

