from flask import *
import cv2
import numpy as np
import threading
from download import download_files
import logging
import os

# 로그 설정
logging.basicConfig(level=logging.DEBUG)

# Blueprint 설정
upload_bp = Blueprint('upload', __name__, template_folder='templates')

# 작업 상태를 저장할 로컬 메모리 딕셔너리
task_status = {}

@upload_bp.route('/')
def upload_form():
    return render_template('add_photo.html')

@upload_bp.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        logging.error('이미지가 선택되지 않았습니다.')
        return jsonify({'error': '이미지를 선택하세요!'}), 400

    file = request.files['image']
    try:
        logging.debug('이미지 파일을 읽는 중입니다...')
        np_img = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(np_img, cv2.IMREAD_GRAYSCALE)

        # 디버깅용 이미지 저장
        save_debug_image(img, "uploaded_image.jpg")

        logging.debug(f'디코딩된 이미지 크기: {img.shape}')

        # QR 코드 디코딩
        qr = cv2.QRCodeDetector()
        data, points, _ = qr.detectAndDecode(img)

        if points is not None:
            logging.debug(f'QR 코드 영역 좌표: {points}')
        else:
            logging.warning('QR 코드 영역을 감지하지 못했습니다.')

        logging.debug(f'QR 코드 데이터: {data}')

        if not data:
            return jsonify({'error': 'QR 코드를 찾을 수 없습니다. 다시 업로드해주세요.'}), 400

        # 작업 상태 초기화
        user_id = 'testuser01'  # 테스트용 사용자 ID
        task_status[data] = 'in_progress'  # 작업 상태 저장

        # 다운로드 및 S3 업로드 비동기 처리
        thread = threading.Thread(target=process_download, args=(data, user_id))
        thread.start()

        return jsonify({'message': '다운로드 중입니다...', 'qr_data': data})
    except Exception as e:
        logging.exception('QR 코드 업로드 처리 중 오류:')
        return jsonify({'error': str(e)}), 500

def process_download(qr_data, user_id):
    try:
        logging.debug(f'QR 데이터: {qr_data}, 사용자 ID: {user_id}')
        download_files(qr_data, user_id)  # 다운로드 및 S3 업로드 처리
        task_status[qr_data] = 'completed'  # 작업 상태를 완료로 설정
    except Exception as e:
        task_status[qr_data] = 'error'  # 오류 상태 설정
        logging.exception(f'Download error for {qr_data}:')

@upload_bp.route('/status', methods=['GET'])
def status():
    qr_data = request.args.get('qr_data')
    status = task_status.get(qr_data, 'not_found')  # 작업 상태 조회
    return jsonify({'status': status})

def save_debug_image(img, filename):
    try:
        debug_dir = "debug_images"
        os.makedirs(debug_dir, exist_ok=True)
        filepath = os.path.join(debug_dir, filename)
        cv2.imwrite(filepath, img)
        logging.debug(f'이미지를 "{filepath}"로 저장했습니다.')
    except Exception as e:
        logging.warning(f'이미지 저장 중 오류 발생: {e}')
