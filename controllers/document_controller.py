from flask import request, flash, redirect, url_for, jsonify, make_response
from typing import List
import os
import re
import tempfile 

from models.file_handler import FileHandler
from services.converter_service import ConverterService
from services.search_service import SearchService


class DocumentController:
    """문서 변환 및 검색 처리를 담당하는 컨트롤러"""
    
    def __init__(self, file_handler: FileHandler, converter_service: ConverterService, search_service: SearchService):
        self.file_handler = file_handler
        self.converter_service = converter_service
        self.search_service = search_service
    
    def upload_file(self):
        """파일 업로드 처리"""
        if 'file' not in request.files:
            flash('No file part')
            return redirect(url_for('index'))
        
        files = request.files.getlist('file')
        
        if not files or files[0].filename == '':
            flash('No selected file')
            return redirect(url_for('index'))
        
        for file in files:
            if file and self.file_handler.allowed_file(file.filename):
                self.file_handler.save_uploaded_file(file)
        
        flash('Files successfully uploaded')
        return redirect(url_for('index'))
    
    def convert_documents(self):
        """선택된 문서 변환 처리"""
        selected_files = request.form.getlist('files')
        
        if not selected_files:
            flash('No files selected')
            return redirect(url_for('index'))
        
        self._process_files_conversion(selected_files)
        return redirect(url_for('index'))
    
    def convert_all_documents(self):
        """모든 문서 변환 처리"""
        input_files = self.file_handler.get_input_files()
        
        if not input_files:
            flash('No files in input folder')
            return redirect(url_for('index'))
        
        self._process_files_conversion(input_files)
        return redirect(url_for('index'))
    
    def search(self):
        """키워드 검색 처리"""
        keyword = request.form.get('keyword', '')
        # 정규식 이스케이프는 search_service에서 처리
        result = self.search_service.search_keyword(keyword)
        return jsonify(result)
    
    def _process_files_conversion(self, filenames: List[str]):
        """파일 변환 처리 공통 로직"""
        for filename in filenames:
            if not self.file_handler.allowed_file(filename):
                flash(f'File {filename} is not allowed')
                continue
            
            input_path = os.path.join(self.file_handler.input_folder, filename)
            
            # 파일이 존재하는지 확인
            if not os.path.exists(input_path):
                flash(f'File {filename} not found')
                continue
            
            # 문서 변환
            markdown_content = self.converter_service.convert_document_to_markdown(input_path)
            
            if markdown_content:
                # 마크다운 파일 저장
                self.file_handler.save_markdown_content(filename, markdown_content)
                flash(f'Successfully converted {filename} to markdown')
            else:
                flash(f'Failed to convert {filename}')
