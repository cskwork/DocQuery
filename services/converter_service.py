import os
import logging
import asyncio
import threading
import time
from typing import Optional, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor

from io import BytesIO
from docling.datamodel.base_models import DocumentStream
from docling.document_converter import DocumentConverter # 사용자의 기존 DocumentConverter 경로
from services.hwp_converter_service import get_hwp_text # Python 기반 HWP 프로세서

logger = logging.getLogger(__name__) # 이 모듈의 로거 ('converter_service')

# 기본 로깅 설정 
if not logger.handlers: 
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


class ConverterService:
    """문서 변환을 담당하는 서비스 클래스"""

    def __init__(self):
        """ConverterService 초기화"""
        self.converter = DocumentConverter()
        self.executor = ThreadPoolExecutor(max_workers=3)  # 동시에 처리할 수 있는 비동기 작업 수 제한
        self.conversion_tasks: Dict[str, Dict[str, Any]] = {}  # 작업 상태 추적을 위한 딕셔너리
        self.lock = threading.Lock()  # 스레드 안전성을 위한 락
        
        logger.info("ConverterService initialized. HWP conversion will use Python-based get_hwp_text.")

    def convert_document_to_markdown(self, file_path: str) -> Optional[str]:
        """단일 문서를 마크다운으로 변환하는 함수"""
        logger.info(f"문서 변환 요청: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"변환할 파일을 찾을 수 없습니다: {file_path}")
            return None
            
        file_ext = os.path.splitext(file_path)[1].lower()

        # PDF 파일 처리 (비동기 방식)
        if file_ext == '.pdf':
            logger.debug(f"PDF 파일 감지, 비동기 방식으로 처리합니다: {file_path}")
            task_id = self._start_async_conversion(file_path)
            return f"# PDF 변환 진행 중\n\nPDF 파일({os.path.basename(file_path)})이 백그라운드에서 변환 중입니다.\n\n작업 ID: {task_id}\n\n변환이 완료되면 결과를 확인할 수 있습니다."

        # HWP 파일 처리 (Python 기반)
        if file_ext == '.hwp':
            logger.debug("HWP 파일 감지, Python 기반 hwp_converter_service.py로 처리합니다.")
            
            try:
                markdown_content = get_hwp_text(file_path)
                if markdown_content:
                    logger.info(f"HWP 파일 변환 성공: {file_path}")
                else:
                    logger.warning(f"HWP 파일 변환 실패 또는 내용 없음: {file_path}")
                return markdown_content
            except ValueError as ve: 
                logger.error(f"HWP 파일 변환 중 오류 발생 (ValueError) ({file_path}): {str(ve)}", exc_info=True) 
                return f"# HWP 변환 오류\n\nHWP 파일({os.path.basename(file_path)}) 변환 중 오류가 발생했습니다: {str(ve)}"
            except Exception as e: 
                logger.error(f"HWP 파일 변환 중 예외 발생 ({file_path}): {str(e)}", exc_info=True) 
                return None
        
        # TXT 파일 처리: 직접 파일 내용을 읽음
        if file_ext == '.txt':
            logger.debug(f"TXT 파일 감지, 직접 파일 내용을 읽습니다: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.info(f"TXT 파일 읽기 성공: {file_path}")
                return content
            except Exception as e:
                logger.error(f"TXT 파일 읽기 중 오류 발생 ({file_path}): {str(e)}", exc_info=True)
                return None

        # 그 외 다른 문서 형식 처리 (기존 방식 사용)
        try:
            logger.debug(f"기본 변환기({type(self.converter).__name__})를 사용하여 {file_ext} 파일 변환 시도: {file_path}")
            
            # PDF 파일은 스트리밍 방식으로 처리
            if file_ext == '.pdf':
                logger.debug(f"PDF 파일 스트리밍 방식으로 변환 시도: {file_path}")
                with open(file_path, 'rb') as f:
                    buf = BytesIO(f.read())
                    source = DocumentStream(name=os.path.basename(file_path), stream=buf)
                    result = self.converter.convert(source)
            else:
                # 다른 파일 형식은 기존 방식 사용
                result = self.converter.convert(file_path, max_num_pages=100, max_file_size=20971520)

            if hasattr(result, 'document') and hasattr(result.document, 'export_to_markdown'):
                markdown = result.document.export_to_markdown()
                logger.info(f"기본 변환기를 통한 문서 변환 완료: {file_path}, 결과 크기: {len(markdown)} 바이트")
                return markdown
            elif isinstance(result, str): # convert 메서드가 바로 마크다운 문자열을 반환하는 경우
                logger.info(f"기본 변환기를 통한 문서 변환 완료 (직접 문자열 반환): {file_path}, 결과 크기: {len(result)} 바이트")
                return result
            else:
                logger.error(f"기본 변환기의 결과 형식이 예상과 다릅니다 ({type(result)}): {file_path}")
                return None
                
        except Exception as e:
            logger.error(f"기본 변환기 사용 중 문서 변환 오류 발생 ({file_path}): {str(e)}", exc_info=True)
            return None

    def _start_async_conversion(self, file_path: str) -> str:
        """비동기 변환 작업을 시작하는 함수"""
        task_id = f"task_{int(time.time())}_{os.path.basename(file_path)}"
        
        with self.lock:
            self.conversion_tasks[task_id] = {
                'file_path': file_path,
                'status': 'pending',
                'result': None,
                'error': None,
                'start_time': time.time()
            }
        
        # 비동기 작업 시작
        self.executor.submit(self._process_pdf_in_background, task_id, file_path)
        logger.info(f"비동기 PDF 변환 작업 시작: {task_id} - {file_path}")
        
        return task_id
    
    def _process_pdf_in_background(self, task_id: str, file_path: str) -> None:
        """백그라운드에서 PDF 파일을 처리하는 함수"""
        try:
            logger.debug(f"백그라운드 PDF 처리 시작: {task_id} - {file_path}")
            
            # 상태 업데이트
            with self.lock:
                self.conversion_tasks[task_id]['status'] = 'processing'
                self.conversion_tasks[task_id]['progress_log_time'] = time.time()
                self.conversion_tasks[task_id]['progress_count'] = 0
            
            # 로깅 스레드 시작
            stop_logging = threading.Event()
            logging_thread = threading.Thread(
                target=self._log_conversion_progress, 
                args=(task_id, stop_logging)
            )
            logging_thread.daemon = True
            logging_thread.start()
            
            try:
                # PDF 변환 작업 수행
                logger.info(f"PDF 변환 시작 ({task_id}): {file_path}, 최대 100페이지, 최대 20MB")
                with open(file_path, 'rb') as f:
                    buf = BytesIO(f.read())
                    source = DocumentStream(name=os.path.basename(file_path), stream=buf)
                    result = self.converter.convert(source)
                
                if hasattr(result, 'document') and hasattr(result.document, 'export_to_markdown'):
                    markdown = result.document.export_to_markdown()
                    logger.info(f"백그라운드 PDF 변환 완료: {task_id}, 결과 크기: {len(markdown)} 바이트")
                    
                    # 파일 저장 로직 추가
                    try:
                        # 현재 파일(converter_service.py)의 디렉토리 (services)
                        current_file_dir = os.path.dirname(os.path.abspath(__file__))
                        # 프로젝트 루트 디렉토리 (services 폴더의 부모)
                        project_root_dir = os.path.dirname(current_file_dir)
                        output_dir_name = "output"
                        output_dir = os.path.join(project_root_dir, output_dir_name)

                        if not os.path.exists(output_dir):
                            os.makedirs(output_dir)
                        
                        base_name = os.path.basename(file_path)
                        file_name_without_ext, _ = os.path.splitext(base_name)
                        output_file_name = f"{file_name_without_ext}.md"
                        output_file_path = os.path.join(output_dir, output_file_name)
                        
                        with open(output_file_path, 'w', encoding='utf-8') as f_out:
                            f_out.write(markdown) # 'markdown' 변수 사용
                        logger.info(f"변환된 마크다운 파일 저장 완료: {output_file_path}")
                        
                    except Exception as e_save:
                        logger.error(f"백그라운드 PDF 변환 후 파일 저장 중 오류 발생 ({task_id}): {str(e_save)}", exc_info=True)
                        with self.lock:
                            _current_error = self.conversion_tasks[task_id].get('error', '')
                            _save_error_msg = f"File save error: {str(e_save)}"
                            self.conversion_tasks[task_id]['error'] = f"{_current_error}; {_save_error_msg}".strip('; ') if _current_error else _save_error_msg

                    # 결과 저장 (메모리 내)
                    with self.lock:
                        self.conversion_tasks[task_id]['status'] = 'completed'
                        self.conversion_tasks[task_id]['result'] = markdown
                        self.conversion_tasks[task_id]['end_time'] = time.time()
                        
                elif isinstance(result, str):
                    logger.info(f"백그라운드 PDF 변환 완료 (직접 문자열 반환): {task_id}, 결과 크기: {len(result)} 바이트")
                    
                    # 파일 저장 로직 추가
                    try:
                        # 현재 파일(converter_service.py)의 디렉토리 (services)
                        current_file_dir = os.path.dirname(os.path.abspath(__file__))
                        # 프로젝트 루트 디렉토리 (services 폴더의 부모)
                        project_root_dir = os.path.dirname(current_file_dir)
                        output_dir_name = "output"
                        output_dir = os.path.join(project_root_dir, output_dir_name)

                        if not os.path.exists(output_dir):
                            os.makedirs(output_dir)
                        
                        base_name = os.path.basename(file_path)
                        file_name_without_ext, _ = os.path.splitext(base_name)
                        output_file_name = f"{file_name_without_ext}.md"
                        output_file_path = os.path.join(output_dir, output_file_name)
                        
                        with open(output_file_path, 'w', encoding='utf-8') as f_out:
                            f_out.write(result) # 'result' 변수 사용 (직접 문자열인 경우)
                        logger.info(f"변환된 마크다운 파일 저장 완료: {output_file_path}")
                        
                    except Exception as e_save:
                        logger.error(f"백그라운드 PDF 변환 후 파일 저장 중 오류 발생 ({task_id}): {str(e_save)}", exc_info=True)
                        with self.lock:
                            _current_error = self.conversion_tasks[task_id].get('error', '')
                            _save_error_msg = f"File save error: {str(e_save)}"
                            self.conversion_tasks[task_id]['error'] = f"{_current_error}; {_save_error_msg}".strip('; ') if _current_error else _save_error_msg

                    # 결과 저장 (메모리 내)
                    with self.lock:
                        self.conversion_tasks[task_id]['status'] = 'completed'
                        self.conversion_tasks[task_id]['result'] = result
                        self.conversion_tasks[task_id]['end_time'] = time.time()
                else:
                    logger.error(f"백그라운드 PDF 변환 결과 형식이 예상과 다릅니다 ({type(result)}): {task_id}")
                    
                    # 오류 저장
                    with self.lock:
                        self.conversion_tasks[task_id]['status'] = 'failed'
                        self.conversion_tasks[task_id]['error'] = f"결과 형식이 예상과 다릅니다: {type(result)}"
                        self.conversion_tasks[task_id]['end_time'] = time.time()
            finally:
                # 로깅 스레드 종료 신호
                stop_logging.set()
                logging_thread.join(timeout=1.0)  # 최대 1초 대기
                
        except Exception as e:
            logger.error(f"백그라운드 PDF 변환 중 오류 발생 ({task_id}): {str(e)}", exc_info=True)
            
            # 오류 저장
            with self.lock:
                self.conversion_tasks[task_id]['status'] = 'failed'
                self.conversion_tasks[task_id]['error'] = str(e)
                self.conversion_tasks[task_id]['end_time'] = time.time()
    
    def _log_conversion_progress(self, task_id: str, stop_event: threading.Event) -> None:
        """PDF 변환 진행 상황을 주기적으로 로깅하는 함수"""
        while not stop_event.is_set():
            # 10초마다 로깅
            time.sleep(15)
            
            if stop_event.is_set():
                break
                
            with self.lock:
                if task_id not in self.conversion_tasks:
                    break
                    
                task = self.conversion_tasks[task_id]
                if task['status'] not in ['pending', 'processing']:
                    break
                    
                # 진행 카운트 증가
                task['progress_count'] += 1
                elapsed_time = time.time() - task['start_time']
                
                # 상태 로깅
                logger.info(f"PDF 변환 진행 중 ({task_id}): {task['progress_count'] * 10}초 경과, 상태: {task['status']}")
                
                # 메모리 사용량 로깅 (옵션)
                try:
                    import psutil
                    process = psutil.Process()
                    memory_info = process.memory_info()
                    logger.debug(f"메모리 사용량: {memory_info.rss / (1024 * 1024):.2f} MB")
                except ImportError:
                    pass  # psutil이 설치되지 않은 경우 무시
    
    def get_conversion_status(self, task_id: str) -> Dict[str, Any]:
        """변환 작업의 상태를 확인하는 함수"""
        with self.lock:
            if task_id in self.conversion_tasks:
                return self.conversion_tasks[task_id].copy()
            else:
                return {'status': 'not_found', 'error': f"작업 ID를 찾을 수 없습니다: {task_id}"}
    
    def get_conversion_result(self, task_id: str) -> Tuple[bool, Optional[str]]:
        """변환 작업의 결과를 가져오는 함수"""
        with self.lock:
            if task_id not in self.conversion_tasks:
                return False, f"작업 ID를 찾을 수 없습니다: {task_id}"
            
            task = self.conversion_tasks[task_id]
            
            if task['status'] == 'completed':
                return True, task['result']
            elif task['status'] == 'failed':
                return False, f"변환 작업 실패: {task['error']}"
            else:
                return False, f"변환 작업이 아직 완료되지 않았습니다. 현재 상태: {task['status']}"
    
    def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """오래된 작업 정보를 정리하는 함수"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        removed_count = 0
        
        with self.lock:
            task_ids = list(self.conversion_tasks.keys())
            
            for task_id in task_ids:
                task = self.conversion_tasks[task_id]
                
                # 완료되었거나 실패한 작업 중 오래된 것 제거
                if task['status'] in ['completed', 'failed']:
                    if 'end_time' in task and (current_time - task['end_time']) > max_age_seconds:
                        del self.conversion_tasks[task_id]
                        removed_count += 1
                        
                # 시작된 지 너무 오래된 작업(처리 중이지만 멈춘 것으로 추정) 제거
                elif (current_time - task['start_time']) > max_age_seconds * 2:  # 더 긴 시간 허용
                    del self.conversion_tasks[task_id]
                    removed_count += 1
        
        return removed_count


# 사용 예시 (테스트용)
if __name__ == '__main__': # pragma: no cover
    # 로깅 기본 설정 (이 파일이 직접 실행될 때)
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("ConverterService 테스트 시작")
    service = ConverterService()

    # PDF 테스트 (비동기)
    test_pdf = "./test.pdf"
    if os.path.exists(test_pdf):
        task_id = service._start_async_conversion(test_pdf)
        logger.info(f"PDF 변환 작업 시작: {task_id}")
        
        # 상태 확인 (실제로는 API 엔드포인트를 통해 확인)
        time.sleep(2)  # 잠시 대기
        status = service.get_conversion_status(task_id)
        logger.info(f"변환 상태: {status['status']}")
        
        # 결과 확인 (완료되었을 경우)
        if status['status'] == 'completed':
            success, result = service.get_conversion_result(task_id)
            if success:
                logger.info(f"변환 결과 크기: {len(result)} 바이트")
    
    logger.info("ConverterService 테스트 완료.")
