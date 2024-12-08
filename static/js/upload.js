let checkStatusInterval;

function uploadImage() {
    const input = document.getElementById('file-input');
    const file = input.files[0];
    const messageElement = document.getElementById('message');

    if (!file) {
        messageElement.textContent = 'QR코드가 포함된 이미지 파일을 업로드해 주세요!';
        return;
    }

    const formData = new FormData();
    formData.append('image', file);

    messageElement.textContent = 'QR 코드 인식 중...';

    // 이미지 업로드 요청
    fetch('/upload/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            messageElement.textContent = data.error;
        } else {
            messageElement.textContent = data.message;
            checkStatus(data.qr_data);
        }
    })
    .catch(error => {
        console.error('오류:', error);
        messageElement.textContent = '이미지 업로드에 실패했습니다. 다시 시도해 주세요.';
    });
}

function checkStatus(qr_data) {
    if (checkStatusInterval) {
        clearInterval(checkStatusInterval);
    }

    checkStatusInterval = setInterval(function() {
        fetch(`/upload/status?qr_data=${qr_data}`)
            .then(response => response.json())
            .then(data => {
                const status = data.status;
                if (status === 'completed' || status === 'error') {
                    clearInterval(checkStatusInterval);
                }
                updateStatusUI(status);
            });
    }, 2000);
}

function updateStatusUI(status) {
    const statusElement = document.getElementById('status');
    if (status === 'in_progress') {
        statusElement.textContent = "작업 중...";
    } else if (status === 'completed') {
        statusElement.textContent = "작업 완료!";
    } else if (status === 'error') {
        statusElement.textContent = "오류 발생. 다시 시도해 주세요.";
    } else {
        statusElement.textContent = "작업을 찾을 수 없습니다.";
    }
}
