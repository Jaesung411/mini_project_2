from flask import *
import os

gallery_bp = Blueprint('gallery', __name__)

# 샘플 사진 데이터
photos = [{"id": i, "title": f"사진 {i}", "description": "이 사진은 샘플 사진입니다."} for i in range(100)]

@gallery_bp.route('/home', methods=['GET','POST'])
def gallery_list():
    if request.method == "POST":
        print("!!!!")
        return redirect(url_for('gallery.gallery_list'))
    else:
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

@gallery_bp.route('/add_image', methods=['POST'])
def add_image():
    # 폼 데이터와 파일 가져오기
    title = request.form['title']
    file = request.files['image']
    
    if file and file.filename != '':
        # 파일 저장
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        # 여기에서 저장된 이미지를 데이터베이스나 리스트에 추가 가능
        return redirect(url_for('home'))
    return "이미지 업로드 실패", 400

