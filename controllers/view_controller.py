from flask import render_template

from models.file_handler import FileHandler


class ViewController:
    """템플릿 렌더링을 담당하는 컨트롤러"""

    def __init__(self, file_handler: FileHandler):
        self.file_handler = file_handler
    
    def index(self):
        """메인 화면 표시"""
        input_files = self.file_handler.get_input_files()
        output_files = self.file_handler.get_output_files()
        return render_template('index.html', input_files=input_files, output_files=output_files)
