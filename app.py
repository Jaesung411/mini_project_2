from flask import Flask, render_template, request, jsonify, session, logging
import os
import boto3
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

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# AWS S3 설정
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

def upload_to_s3(file_path, s3_key):
    try:
        s3.upload_file(file_path, S3_BUCKET, s3_key)
        app.logger.info(f"Uploaded {file_path} to S3 as {s3_key}")
        
        # S3 업로드 완료 후 로컬 파일 삭제
        os.remove(file_path)
        app.logger.info(f"Deleted local file: {file_path}")
        
        return f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
    except Exception as e:
        app.logger.error(f"Failed to upload {file_path} to S3: {e}")
        return None

@app.route("/", methods=["GET"])
def index():
    session['userInfo'] = {'userId': 'testuser01'}  # 임시로 세션에 userId 설정
    return render_template("add_photo.html")

@app.route("/extract_url", methods=["POST"])
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

@app.route("/download_upload", methods=["POST"])
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
        app.logger.info(f"Clicked on element with text: {text}")
        return True
    except Exception as e:
        app.logger.error(f"Failed to click on element with text: {text}, {e}")
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
                app.logger.info(f"Image downloaded and renamed to {image_path}")
                image_s3_key = f"images/{user_id}/{new_image_name}"
                image_s3_url = upload_to_s3(image_path, image_s3_key)
                if image_s3_url is None:
                    return "Failed to upload image to S3."
            else:
                app.logger.error("Failed to rename downloaded image.")
                return "Failed to rename image."

        # 동영상 다운로드 및 파일명 변경
        if video_click:
            time.sleep(5)  # 다운로드가 완료되기를 기다림
            new_video_name = f"{user_id}_video_{current_datetime}.mp4"
            video_path = rename_downloaded_file(download_dir, "video.mp4", new_video_name)
            if video_path:
                app.logger.info(f"Video downloaded and renamed to {video_path}")
                video_s3_key = f"videos/{user_id}/{new_video_name}"
                video_s3_url = upload_to_s3(video_path, video_s3_key)
                if video_s3_url is None:
                    return "Failed to upload video to S3."
            else:
                app.logger.error("Failed to rename downloaded video.")
                return "Failed to rename video."

        if not image_s3_url and not video_s3_url:
            return "No files uploaded to S3."

        return f"이미지 및 비디오 다운로드 및 S3 업로드가 완료되었습니다. 이미지 URL: {image_s3_url}, 비디오 URL: {video_s3_url}"
    except Exception as e:
        app.logger.error(f"Error during download: {e}")
        return f"오류 발생: {e}"
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
