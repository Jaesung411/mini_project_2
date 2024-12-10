FROM python:3.8-slim
WORKDIR /app
# 필수 패키지 설치
RUN apt-get update && \
    apt-get install -y wget curl unzip libnss3 libx11-6 libgdk-pixbuf2.0-0 fonts-liberation libappindicator3-1 xdg-utils && \
    apt-get clean
# 최신 Chrome 설치 (dpkg 사용)
RUN wget -O /tmp/google-chrome-stable_current_amd64.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i /tmp/google-chrome-stable_current_amd64.deb || apt-get -f install -y && \
    rm /tmp/google-chrome-stable_current_amd64.deb
# Python 패키지 설치
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 80
ENV FLASK_APP=app.py
COPY . .
CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]

