import os
import uuid
from flask import Flask, jsonify, send_file, Response, request

from models.file_handler import FileHandler
from services.converter_service import ConverterService
from services.search_service import SearchService
from services.hwp_converter_service import get_hwp_text
import logging # 로깅 모듈
from logging.handlers import TimedRotatingFileHandler # 일자별 로깅 핸들러
from controllers.document_controller import DocumentController
from controllers.view_controller import ViewController


def create_app():
    """애플리케이션 팩토리 패턴을 사용하여 Flask 애플리케이션 생성"""
    app = Flask(__name__, 
                static_folder='templates',  # templates 폴더를 static 폴더로도 사용
                static_url_path='')
    
    # 설정
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_' + str(uuid.uuid4()))
    app.config['INPUT_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'input')
    app.config['OUTPUT_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    app.config['LOGS_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs') # 로그 폴더 설정
    app.config['ALLOWED_EXTENSIONS'] = {'txt','pdf', 'docx', 'xlsx', 'html', 'htm', 'png', 'jpg', 'jpeg', 'hwp'}

    # 로거 설정
    log_directory = app.config['LOGS_FOLDER']
    # 로그 디렉토리 생성은 아래 '필요한 폴더 생성' 부분에서 처리됩니다.

    log_file_basename = "app.log" # TimedRotatingFileHandler가 여기에 날짜를 붙입니다.
    log_file_path = os.path.join(log_directory, log_file_basename)

    # 로그 포맷터 생성: 시간 - 로거 이름 - 로그 레벨 - 메시지 [경로:라인번호]
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s [in %(pathname)s:%(lineno)d]'
    )

    # 시간 기반 파일 로테이션 핸들러 생성
    # when='D': 매일 자정 기준으로 로그 파일 교체 (Day)
    # interval=1: 1일 간격
    # backupCount=30: 최대 30개의 백업 파일 유지
    # encoding='utf-8': 로그 파일 인코딩
    # delay=False: 앱 시작 시 즉시 로그 파일 생성 또는 열기 시도
    daily_file_handler = TimedRotatingFileHandler(
        log_file_path,
        when='D',
        interval=1,
        backupCount=30,
        encoding='utf-8',
        delay=False
    )
    daily_file_handler.setFormatter(formatter)

    # Flask 앱 로거에 핸들러 추가
    # 기존 핸들러를 제거하고 싶다면 다음 주석을 해제 (중복 로깅 방지):
    # for handler in list(app.logger.handlers):
    #     app.logger.removeHandler(handler)
    # 루트 로거에 핸들러 및 레벨 설정
    root_logger = logging.getLogger() # 최상위 로거
    
    # 핸들러 중복 추가 방지: 동일한 파일로 출력하는 TimedRotatingFileHandler가 이미 있는지 확인
    handler_exists = False
    for handler in root_logger.handlers:
        if isinstance(handler, TimedRotatingFileHandler):
            # TimedRotatingFileHandler의 baseFilename 속성을 통해 비교
            if hasattr(handler, 'baseFilename') and handler.baseFilename == daily_file_handler.baseFilename:
                handler_exists = True
                break
    
    if not handler_exists:
        root_logger.addHandler(daily_file_handler)

    if not app.debug:
        root_logger.setLevel(logging.WARNING) # 프로덕션 레벨
    else:
        root_logger.setLevel(logging.DEBUG) # 개발 레벨
        # 루트 로거가 DEBUG 레벨일 때 초기화 메시지를 남김
        root_logger.debug("Root logger configured with TimedRotatingFileHandler for daily rotation in DEBUG mode.")

    # Flask 앱 자체의 로거(app.logger) 레벨도 루트 로거와 동기화하거나 애플리케이션 필요에 맞게 설정합니다.
    # app.logger의 메시지도 루트 로거로 전파되어 파일에 기록됩니다.
    app.logger.setLevel(logging.DEBUG if app.debug else logging.WARNING)

    # 초기화 완료 로그 (app.logger 또는 root_logger 중 하나로 기록)
    # 이 메시지는 app.logger를 통해 발생하고, 설정된 레벨에 따라 루트 로거로 전파되어 파일에 기록됨.
    app.logger.info(f"Application logging initialized. Log files will be stored in: {log_directory}")
    
    # 의존성 주입을 통한 컴포넌트 초기화
    file_handler = FileHandler(
        app.config['INPUT_FOLDER'],
        app.config['OUTPUT_FOLDER'],
        app.config['ALLOWED_EXTENSIONS']
    )
    converter_service = ConverterService()
    search_service = SearchService(app.config['OUTPUT_FOLDER'])
    
    # 컨트롤러 초기화
    document_controller = DocumentController(file_handler, converter_service, search_service)
    view_controller = ViewController(file_handler)
    
    # 라우트 등록
    @app.route('/')
    def index():
        return view_controller.index()
    
    @app.route('/upload', methods=['POST'])
    def upload_file():
        return document_controller.upload_file()
    
    @app.route('/convert', methods=['POST'])
    def convert():
        return document_controller.convert_documents()
    
    @app.route('/convert-all', methods=['POST'])
    def convert_all():
        return document_controller.convert_all_documents()
    
    @app.route('/search', methods=['POST'])
    def search():
        return document_controller.search()
    
    @app.route('/api/hwp-to-markdown/<filename>')
    def convert_hwp_to_markdown(filename):
        """HWP 파일을 마크다운으로 변환하는 API"""
        file_path = os.path.join(app.config['INPUT_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "파일을 찾을 수 없습니다"}), 404
        
        try:
            # HWP 파일을 마크다운으로 변환 (새로운 서비스 사용)
            markdown_content = get_hwp_text(file_path)
            if markdown_content is None: # get_hwp_text가 None을 반환하는 경우는 거의 없지만, 오류 문자열을 반환할 수 있음
                return jsonify({"error": "변환 실패 또는 파일 내용 없음"}), 500
            # get_hwp_text가 오류 메시지를 직접 반환하는 경우도 처리
            if markdown_content.startswith("OLE 파일 처리 오류:") or markdown_content.startswith("HWP 텍스트 추출 중 알 수 없는 오류:"):
                 return jsonify({"error": markdown_content}), 500
            return Response(markdown_content, mimetype='text/plain')
        except Exception as e:
            app.logger.error(f"Error converting HWP to Markdown for {filename}: {e}")
            return jsonify({"error": f"변환 중 오류 발생: {str(e)}"}), 500

    @app.route('/api/convert-hwp-to-markdown', methods=['POST'])
    def convert_uploaded_hwp_to_markdown():
        """HWP 파일 업로드 받아서 마크다운으로 변환하는 API"""
        if 'file' not in request.files:
            return jsonify({"error": "파일이 업로드되지 않았습니다"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "파일이 선택되지 않았습니다"}), 400
            
        if not file.filename.lower().endswith('.hwp'):
            return jsonify({"error": "HWP 파일만 지원됩니다"}), 400
        
        # 임시 파일로 저장
        temp_filename = f"temp_{uuid.uuid4().hex}.hwp"
        temp_path = os.path.join(app.config['INPUT_FOLDER'], temp_filename)
        
        try:
            file.save(temp_path)
            
            # HWP 파일을 마크다운으로 변환 (새로운 서비스 사용)
            markdown_content = get_hwp_text(temp_path)
            if markdown_content is None: # 위와 동일한 로직
                return jsonify({"error": "변환 실패 또는 파일 내용 없음"}), 500
            if markdown_content.startswith("OLE 파일 처리 오류:") or markdown_content.startswith("HWP 텍스트 추출 중 알 수 없는 오류:"):
                return jsonify({"error": markdown_content}), 500
                
            return Response(markdown_content, mimetype='text/plain')
        except Exception as e:
            app.logger.error(f"Error converting uploaded HWP to Markdown: {e}")
            return jsonify({"error": f"오류 발생: {str(e)}"}), 500
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
    
    # 필요한 폴더 생성
    os.makedirs(app.config['INPUT_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    os.makedirs(app.config['LOGS_FOLDER'], exist_ok=True) # 로그 폴더 생성
    
    # node_modules 폴더를 정적 파일로 제공하는 라우트 추가
    @app.route('/node_modules/<path:filename>')
    def serve_node_modules(filename):
        node_modules_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'node_modules')
        return send_file(os.path.join(node_modules_path, filename))
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
