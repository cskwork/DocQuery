import os
import re
from typing import Dict, List, Any, Optional


class SearchService:
    """마크다운 파일 검색 기능을 담당하는 클래스"""
    
    def __init__(self, output_folder: str):
        self.output_folder = output_folder
    
    def search_keyword(self, keyword: str) -> Dict[str, Dict[str, Any]]:
        """키워드 검색 함수 - 완전/부분 일치 구분 및 스니펫 제공"""
        result = {}
        output_files = self._get_markdown_files()
        
        if not keyword.strip():
            return result
        
        # 정규식 패턴, 대소문자 구분 없이 키워드 전체 단어 검색을 위해 양쪽에  추가 고려
        # 하지만 부분 일치도 찾아야 하므로, 우선 기존 패턴을 사용하고, 이후 로직에서 완전 일치 여부 판단
        pattern = re.compile(re.escape(keyword), re.IGNORECASE) # re.escape 추가
        
        for filename in output_files:
            file_path = os.path.join(self.output_folder, filename)
            try:
                snippets = []
                count = 0
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        for match in pattern.finditer(line):
                            count += 1
                            start, end = match.span()
                            
                            # 완전 일치 여부 판단
                            # match_type: 'complete' 또는 'partial'
                            match_type = 'partial' # 기본값은 부분 일치
                            
                            # 매치 앞부분이 라인의 시작이거나, 앞 글자가 알파벳/숫자가 아닌 경우
                            is_prefix_boundary = (start == 0) or (not line[start-1].isalnum())
                            # 매치 뒷부분이 라인의 끝이거나, 뒷 글자가 알파벳/숫자가 아닌 경우
                            is_suffix_boundary = (end == len(line)) or (not line[end].isalnum())
                            
                            if is_prefix_boundary and is_suffix_boundary:
                                match_type = 'complete'
                                
                            context_start = max(0, start - 50)
                            context_end = min(len(line), end + 50)
                            
                            # 이전 줄 가져오기
                            prev_line = lines[i-1] + '\n' if i > 0 else ""
                            # 다음 줄 가져오기
                            next_line = '\n' + lines[i+1] if i < len(lines)-1 else ""
                            
                            # 이전 줄을 before에 포함, 다음 줄을 after에 포함
                            before = prev_line + line[context_start:start]
                            matched_text = line[start:end]
                            after = line[end:context_end] + next_line
                            
                            snippet = {
                                'line_number': i + 1,
                                'before': before,
                                'matched': matched_text, # 필드명 'matched' 유지
                                'after': after,
                                'match_type': match_type # 완전/부분 일치 정보 추가
                            }
                            snippets.append(snippet)
                
                if count > 0:
                    result[filename] = {
                        'count': count,
                        'snippets': snippets[:10]
                    }
            except Exception as e:
                print(f"Error searching in {file_path}: {str(e)}")
        
        return result
    
    def _get_markdown_files(self) -> List[str]:
        """출력 폴더에 있는 모든 마크다운 파일 목록을 반환하는 함수"""
        files = []
        for filename in os.listdir(self.output_folder):
            if filename.endswith('.md'):
                files.append(filename)
        return files
