import os
from typing import List, Dict, Any, Optional


class FileHandler:
    """파일 처리를 담당하는 클래스"""
    
    def __init__(self, input_folder: str, output_folder: str, allowed_extensions: set):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.allowed_extensions = allowed_extensions
        
        # 필요한 폴더 생성
        os.makedirs(self.input_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)
    
    def allowed_file(self, filename: str) -> bool:
        """허용된 파일 확장자인지 확인하는 함수"""
        if '.' not in filename:
            print(f"확장자가 없는 파일: {filename}")
            return False
            
        ext = filename.rsplit('.', 1)[1].lower()
        is_allowed = ext in self.allowed_extensions
        if not is_allowed:
            print(f"파일 확장자 {ext}는 허용 목록({self.allowed_extensions})에 없습니다.")
        return is_allowed
    
    def safe_filename(self, filename: str) -> str:
        """한글 파일명 처리를 위한 함수"""
        # 위험한 문자는 제거하되 한글, 특수 문자, 로마 숫자 등은 보존
        # '/'와 '\' 및 시스템에서 허용되지 않는 문자만 변환
        unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        safe_name = filename
        for char in unsafe_chars:
            safe_name = safe_name.replace(char, '_')
        return safe_name
    
    def get_input_files(self) -> List[str]:
        """입력 폴더에 있는 모든 파일 목록을 반환하는 함수"""
        files = []
        for filename in os.listdir(self.input_folder):
            if self.allowed_file(filename):
                files.append(filename)
        return files
    
    def get_output_files(self) -> List[str]:
        """출력 폴더에 있는 모든 마크다운 파일 목록을 반환하는 함수"""
        files = []
        for filename in os.listdir(self.output_folder):
            if filename.endswith('.md'):
                files.append(filename)
        return files
    
    def save_uploaded_file(self, file) -> str:
        """업로드된 파일을 저장하고 저장된 경로를 반환"""
        original_filename = file.filename
        filename = self.safe_filename(original_filename)
        file_path = os.path.join(self.input_folder, filename)
        print(f"파일 업로드 중: {original_filename} -> {file_path}")
        
        # 입력 폴더가 존재하는지 확인하고 없으면 생성
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        file.save(file_path)
        print(f"파일 업로드 완료: {file_path} (크기: {os.path.getsize(file_path)} 바이트)")
        return file_path
    
    def save_markdown_content(self, original_filename: str, markdown_content: str) -> str:
        """마크다운 내용을 파일로 저장하고 저장 경로 반환"""
        base_filename = os.path.basename(original_filename)
        output_filename = os.path.splitext(base_filename)[0] + '.md'
        output_path = os.path.join(self.output_folder, output_filename)
        
        print(f"마크다운 저장 시작: {original_filename} -> {output_path}")
        if not markdown_content:
            print("마크다운 내용이 비어 있습니다.")
            return ""
            
        try:
            with open(output_path, 'wb') as f:
                encoded_content = markdown_content.encode('utf-8', errors='ignore')
                f.write(encoded_content)
                print(f"마크다운 파일 저장 완료: {output_path} (크기: {len(encoded_content)} 바이트)")
        except Exception as e:
            print(f"마크다운 파일 저장 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return ""
            
        return output_path
