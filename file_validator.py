"""
File validation utilities for the Legal Contract AI Auditor
"""

import os
import re

SUPPORTED_EXTENSIONS = {
    'txt': 'Text Files',
    'md': 'Markdown',
    'py': 'Python Code',
    'js': 'JavaScript',
    'html': 'HTML',
    'css': 'CSS',
    'json': 'JSON Data',
    'xml': 'XML Data',
    'csv': 'CSV Data',
    'log': 'Log Files',
    'docx': 'Word Documents',
    'pdf': 'PDF Documents',
    'rtf': 'Rich Text Format',
    'odt': 'OpenDocument Text',
    'eml': 'Email Files',
    'msg': 'Outlook Email',
    'htm': 'HTML Pages',
    'xlsx': 'Excel Spreadsheets',
    'xls': 'Excel Spreadsheets',
    'pptx': 'PowerPoint Presentations',
    'jpg': 'Images',
    'jpeg': 'Images',
    'png': 'Images',
    'bmp': 'Images',
    'tiff': 'Images',
    'tif': 'Images'
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_file(uploaded_file):
    """Validates uploaded file type and size"""
    file_size = uploaded_file.size
    if file_size > MAX_FILE_SIZE:
        return False, f"File too large: {file_size/1024/1024:.2f}MB. Maximum is 10MB."
    
    file_name = uploaded_file.name
    ext = get_file_extension(file_name)
    
    if ext not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported file type: .{ext}. Supported formats: {', '.join(SUPPORTED_EXTENSIONS.keys())}"
    
    try:
        uploaded_file.seek(0)
        header = uploaded_file.read(1024)
        uploaded_file.seek(0)
        
        if ext == 'pdf':
            if not header.startswith(b'%PDF'):
                return False, "Invalid PDF file."
        elif ext == 'docx' or ext == 'pptx' or ext == 'xlsx':
            if not header.startswith(b'PK'):
                return False, f"Invalid {ext.upper()} file."
        elif ext in ['jpg', 'jpeg']:
            if not header.startswith(b'\xff\xd8'):
                return False, "Invalid JPEG file."
        elif ext == 'png':
            if not header.startswith(b'\x89PNG'):
                return False, "Invalid PNG file."
    except Exception as e:
        return False, f"Error validating file: {str(e)}"
    
    return True, "File is valid"

def get_file_extension(filename):
    filename = os.path.basename(filename)
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''

def get_file_type(filename):
    ext = get_file_extension(filename)
    return SUPPORTED_EXTENSIONS.get(ext, 'Unknown')

def get_file_info(uploaded_file):
    file_name = uploaded_file.name
    file_size = uploaded_file.size
    ext = get_file_extension(file_name)
    file_type = get_file_type(ext)
    
    if file_size < 1024:
        size_display = f"{file_size} B"
    elif file_size < 1024 * 1024:
        size_display = f"{file_size/1024:.2f} KB"
    else:
        size_display = f"{file_size/1024/1024:.2f} MB"
    
    return {
        'name': file_name,
        'extension': ext,
        'size_bytes': file_size,
        'size_display': size_display,
        'type': file_type,
        'is_text': ext in ['txt', 'md', 'py', 'js', 'html', 'css', 'json', 'xml', 'csv', 'log', 'htm'],
        'is_valid': True
    }

def check_file_safety(uploaded_file):
    warnings = []
    file_name = uploaded_file.name
    ext = get_file_extension(file_name)
    
    dangerous_extensions = ['exe', 'bat', 'cmd', 'com', 'scr', 'vbs']
    if ext in dangerous_extensions:
        warnings.append(f"File type .{ext} may contain executable code. Exercise caution.")
    
    suspicious_patterns = [r'\.\./', r'\\\.\.', r'%[0-9a-fA-F]{2}']
    for pattern in suspicious_patterns:
        if re.search(pattern, file_name):
            warnings.append("Suspicious filename pattern detected.")
            break
    
    if file_name.count('.') > 1:
        warnings.append("Multiple file extensions detected. File may be disguised.")
    
    return warnings