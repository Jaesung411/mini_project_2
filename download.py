import time, logging, requests, boto3
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


# 파일명: {user_id}_image_{current_datetime}.jpg
# 경로: images/{user_id}/{user_id}_image_{current_datetime}.jpg


# 파일명: {user_id}_video_{current_datetime}.mp4
# 경로: videos/{user_id}/{user_id}_video_{current_datetime}.mp4

# AWS S3 설정
s3 = boto3.client('s3')
bucket_name = 'testbucketa0'

def setup_driver(headless=True):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service("/usr/local/bin/chromedriver")
    return webdriver.Chrome(service=service, options=chrome_options)

def click_element_by_text(driver, tag, text):
    try:
        xpath = f"//{tag}[contains(text(), '{text}')]"
        element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(1)
        element.click()
        logging.info(f"Clicked element with text: '{text}'")
        return True
    except Exception as e:
        logging.error(f"Failed to click element with text '{text}': {e}")
        return False

def download_file(driver, xpath, file_name, file_extension):
    try:
        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
        url = element.get_attribute('src')
        response = requests.get(url)
        file_path = f'{file_name}.{file_extension}'
        
        with open(file_path, 'wb') as file:
            file.write(response.content)
        
        logging.info(f"Downloaded file to {file_path}")
        return file_path
    except Exception as e:
        logging.error(f"Error downloading file: {e}")
        return None

def upload_to_s3(file_path, s3_key):
    try:
        with open(file_path, 'rb') as file:
            s3.upload_fileobj(file, bucket_name, s3_key)
        logging.info(f"Uploaded {file_path} to S3 at {s3_key}")
    except Exception as e:
        logging.error(f"Error uploading {file_path} to S3: {e}")

def download_files(url, user_id, headless=True):
    driver = None
    try:
        driver = setup_driver(headless)
        driver.get(url)
        current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 이미지 다운로드 및 S3 업로드
        if click_element_by_text(driver, "p", "Image"):
            image_path = download_file(driver, '//*[@id="image"]', f'{user_id}_image_{current_datetime}', 'jpg')
            if image_path:
                s3_key = f'images/{user_id}/{user_id}_image_{current_datetime}.jpg'
                upload_to_s3(image_path, s3_key)

        # 비디오 다운로드 및 S3 업로드
        if click_element_by_text(driver, "p", "Video"):
            video_path = download_file(driver, '//*[@id="video"]', f'{user_id}_video_{current_datetime}', 'mp4')
            if video_path:
                s3_key = f'videos/{user_id}/{user_id}_video_{current_datetime}.mp4'
                upload_to_s3(video_path, s3_key)

    except Exception as e:
        logging.error(f"Error during download or upload process: {e}")
        raise
    finally:
        if driver:
            driver.quit()
