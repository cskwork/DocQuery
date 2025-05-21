# -*- coding: utf-8 -*-
import olefile
import zlib
import struct
import re
from typing import List

# 원본 hwp_text_converter.py에서 가져온 함수들

def get_hwp_text(filename: str) -> str:
    """HWP 파일에서 텍스트를 추출하여 Markdown 형식으로 반환하는 함수."""
    with olefile.OleFileIO(filename) as f:
        if not f.exists('FileHeader') or not f.exists('\x05HwpSummaryInformation'):
            raise ValueError(f"유효하지 않은 HWP 파일: {filename}")

        header = f.openstream('FileHeader').read()
        is_compressed = (header[36] & 1) == 1

        sections = []
        for entry in f.listdir():
            if entry[0] == 'BodyText' and entry[1].startswith('Section'):
                idx = int(entry[1][len('Section'):])
                sections.append((idx, f"BodyText/Section{idx}"))
        sections.sort()

        md_lines: List[str] = []
        for _, stream in sections:
            raw = f.openstream(stream).read()
            data = zlib.decompress(raw, -15) if is_compressed else raw
            i, size = 0, len(data)
            while i < size:
                header = struct.unpack_from('<I', data, i)[0]
                rec_type = header & 0x3ff
                rec_len = (header >> 20) & 0xfff
                if rec_type == 67:
                    rec_data = data[i+4:i+4+rec_len]
                    try:
                        text = rec_data.decode('utf-16-le')
                    except UnicodeDecodeError:
                        text = rec_data.decode('utf-16', errors='ignore')
                    # 제어문자 제거
                    text = re.sub(r"[\x00-\x1F]+", '', text)
                    for line in text.splitlines():
                        md_lines.append(line.rstrip())
                i += 4 + rec_len

        # 중복 빈 줄 축소
        cleaned, prev_blank = [], False
        for line in md_lines:
            if not line.strip():
                if not prev_blank:
                    cleaned.append('')
                prev_blank = True
            else:
                cleaned.append(line)
                prev_blank = False
        markdown = '\n'.join(cleaned).strip() + '\n'
        # 표 변환 적용
        return convert_tables(markdown)

def convert_tables(md: str) -> str:
    """탭 구분 또는 공백 구분된 블록을 Markdown 테이블로 변환"""
    """탭 구분 또는 공백 구분된 블록을 Markdown 테이블로 변환"""
    lines = md.splitlines()
    out_lines: List[str] = []
    i = 0
    while i < len(lines):
        # 연속된 표 블록 감지 (탭 또는 2개 이상의 연속된 스페이스)
        if '\t' in lines[i] or re.search(r' {2,}', lines[i]):
            # 블록 수집
            block = []
            while i < len(lines) and ('\t' in lines[i] or re.search(r' {2,}', lines[i])):
                # 셀 구분: 우선 탭 스플릿, 없으면 두 칸 이상 스페이스
                if '\t' in lines[i]:
                    cells = [c.strip() for c in lines[i].split('\t')]
                else:
                    cells = [c.strip() for c in re.split(r' {2,}', lines[i])]
                block.append(cells)
                i += 1
            # 최대 컬럼 수
            max_cols = max(len(row) for row in block)
            # 패딩
            for row in block:
                row += [''] * (max_cols - len(row))
            # Markdown 테이블 생성
            # 헤더로 첫 행 사용
            header = block[0]
            out_lines.append('| ' + ' | '.join(header) + ' |')
            out_lines.append('| ' + ' | '.join(['---'] * max_cols) + ' |')
            for row in block[1:]:
                out_lines.append('| ' + ' | '.join(row) + ' |')
            out_lines.append('')
        else:
            out_lines.append(lines[i])
            i += 1
    return '\n'.join(out_lines) + '\n'