from flask import*
import os
import boto3
from datetime import datetime
from DB.imagedb import imageDAO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import cv2
import numpy as np
import time

gallery_bp = Blueprint('gallery', __name__)

# AWS S3 설정
S3_BUCKET = 'mywebimagevideo'
S3_REGION = 'ap-northeast-3'
s3 = boto3.client('s3', region_name=S3_REGION)

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

def upload_to_s3(file_path, s3_key, title=None):
    try:
        s3.upload_file(file_path, S3_BUCKET, s3_key)
        current_app.logger.info(f"Uploaded {file_path} to S3 as {s3_key}")

        # S3 업로드 완료 후 로컬 파일 삭제
        os.remove(file_path)
        current_app.logger.info(f"Deleted local file: {file_path}")

        file_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"

        # RDS에 파일 정보 저장
        current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
        user_id = str(session['userInfo']['userId'])
        return file_url
    except Exception as e:
        current_app.logger.error(f"Failed to upload {file_path} to S3: {e}")
        return None

@gallery_bp.route('/home', methods=['GET', 'POST'])
def gallery_list():
    if request.method == "POST":
        return redirect(url_for('gallery.gallery_list'))
    else:
        # DB에서 사용자의 사진 가져오기
        images = imageDAO().get_files_by_userid(session['userInfo']['userId'])

        # 사진 데이터를 포맷
        photos = []
        for image in images:
            photos.append({
                "id": image['file_id'],
                "title": image['file_name'],
                "image_path": image['image_path'],
                "video_path": image['video_path']
            })

        # 페이지네이션
        page = int(request.args.get('page', 1))
        per_page = 6
        start = (page - 1) * per_page
        end = start + per_page
        total_pages = (len(photos) + per_page - 1) // per_page
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

    # DB에서 사용자 사진 가져오기 (gallery_list와 같은 로직)
    images = imageDAO().get_files_by_userid(session['userInfo']['userId'])

    # DB 데이터를 photos 형태로 변환
    photos = []
    for image in images:
        photos.append({
            "id": image['file_id'],
            "title": image['file_name'],
            "image_path": image['image_path'],
            "video_path": image['video_path']
        })

    # 검색어가 있는 경우에만 필터링 수행
    if query:
        images = imageDAO().search_images_by_query(session['userInfo']['userId'], query)
    else:
        images = imageDAO().get_files_by_userid(session['userInfo']['userId'])

    # 여기서 images를 photos 형태로 변환
    photos = []
    for image in images:
        photos.append({
            "id": image['file_id'],
            "title": image['file_name'],
            "image_path": image['image_path'],
            "video_path": image['video_path']
        })

    # 페이지네이션
    page = request.args.get('page', 1, type=int)
    per_page = 6
    total_pages = (len(photos) - 1) // per_page + 1
    paginated_list = photos[(page - 1) * per_page: page * per_page]
    pages = get_pagination(page, total_pages)

    return render_template('gallery.html', 
                            photos=paginated_list , 
                            page=page, 
                            pages=pages, 
                            total_pages=total_pages,
                            query=query)

@gallery_bp.route("/extract_url", methods=["POST"])
def extract_url_from_qr():
    try:
        image_file = request.files.get("image")
        title = request.form['title']
        if image_file:
            file_bytes = np.frombuffer(image_file.read(), np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

            url = extract_url(image)
            if url:
                return jsonify({"success": True, "url": url, "title": title})
            else:
                return jsonify({"success": False, "message": "QR 코드에서 URL을 추출할 수 없습니다."})
        return jsonify({"success": False, "message": "이미지가 업로드되지 않았습니다."})
    except Exception as e:
        current_app.logger.error(f"Error during extract URL: {e}")
        return jsonify({"success": False, "message": "서버 오류 발생"})

@gallery_bp.route("/download_upload", methods=["POST"])
def download_upload():
    try:
        data = request.get_json()
        url = data.get("url")
        title = data.get("title")
        result = download_from_url(url, title)
        return jsonify({"message": result})
    except Exception as e:
        current_app.logger.error(f"Error during download upload: {e}")
        return jsonify({"message": "서버 오류 발생"})

def click_element_by_text(driver, tag, text):
    try:
        xpath = f"//{tag}[text()='{text}']"
        element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        element.click()
        current_app.logger.info(f"Clicked on element with text: {text}")
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to click on element with text: {text}, {e}")
        return False

def download_from_url(url, title):
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

        # 이미지 업로드 처리
        if image_click:
            time.sleep(5)  # 다운로드 대기
            new_image_name = f"{user_id}_image_{current_datetime}.jpg"
            image_path = rename_downloaded_file(download_dir, "image.jpg", new_image_name)
            if image_path:
                image_s3_key = f"images/{user_id}/{new_image_name}"
                image_s3_url = upload_to_s3(image_path, image_s3_key, title)

        # 비디오 업로드 처리
        if video_click:
            time.sleep(5)  # 다운로드 대기
            new_video_name = f"{user_id}_video_{current_datetime}.mp4"
            video_path = rename_downloaded_file(download_dir, "video.mp4", new_video_name)
            if video_path:
                video_s3_key = f"videos/{user_id}/{new_video_name}"
                video_s3_url = upload_to_s3(video_path, video_s3_key, title)

        # 둘 중 하나라도 업로드 성공했을 경우 DB에 저장
        if image_s3_url or video_s3_url:
            imageDAO().insert_file(
                user_id,
                title,
                url,
                current_datetime,
                image_s3_url,
                video_s3_url
                )
            return "이미지 및 비디오 업로드 완료"

        return "S3 업로드 실패: 이미지와 비디오 모두 업로드되지 않았습니다."

    except Exception as e:
        current_app.logger.error(f"Error during download: {e}")
        return f"오류 발생: {e}"

    finally:
        if driver:
            driver.quit()


def get_pagination(page, total_pages, max_visible=10):
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