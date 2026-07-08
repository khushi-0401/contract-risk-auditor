"""
Universal Document Parser for Legal Contract AI Auditor
"""

import docx
import PyPDF2
import io
import re
import os
from pathlib import Path

def extract_text_from_file(uploaded_file):
    """Universal document parser - handles ANY document type"""
    
    file_name = uploaded_file.name.lower()
    file_ext = get_file_extension(file_name)
    
    # ============================================
    # 1. TEXT FILES
    # ============================================
    if file_ext in ['txt', 'md', 'py', 'js', 'html', 'css', 'json', 'xml', 'csv', 'log', 'sh', 'bat']:
        return extract_text_from_text_file(uploaded_file)
    
    # ============================================
    # 2. WORD DOCUMENTS
    # ============================================
    elif file_ext == 'docx':
        return extract_text_from_docx(uploaded_file)
    
    # ============================================
    # 3. PDF FILES
    # ============================================
    elif file_ext == 'pdf':
        return extract_text_from_pdf(uploaded_file)
    
    # ============================================
    # 4. RICH TEXT FORMAT
    # ============================================
    elif file_ext == 'rtf':
        return extract_text_from_rtf(uploaded_file)
    
    # ============================================
    # 5. OPEN DOCUMENT TEXT
    # ============================================
    elif file_ext == 'odt':
        return extract_text_from_odt(uploaded_file)
    
    # ============================================
    # 6. EMAIL FILES
    # ============================================
    elif file_ext in ['eml', 'msg']:
        return extract_text_from_email(uploaded_file)
    
    # ============================================
    # 7. HTML FILES
    # ============================================
    elif file_ext in ['htm', 'html']:
        return extract_text_from_html(uploaded_file)
    
    # ============================================
    # 8. EXCEL FILES
    # ============================================
    elif file_ext in ['xlsx', 'xls']:
        return extract_text_from_excel(uploaded_file)
    
    # ============================================
    # 9. POWERPOINT FILES
    # ============================================
    elif file_ext == 'pptx':
        return extract_text_from_pptx(uploaded_file)
    
    # ============================================
    # 10. IMAGE FILES (OCR)
    # ============================================
    elif file_ext in ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'gif']:
        return extract_text_from_image(uploaded_file)
    
    # ============================================
    # 11. UNKNOWN FORMAT
    # ============================================
    else:
        try:
            content = uploaded_file.read()
            uploaded_file.seek(0)
            try:
                text = content.decode('utf-8')
                if text.strip():
                    return text
            except:
                pass
            text = content.decode('utf-8', errors='ignore')
            if text.strip():
                return text
            raise ValueError(f"Unsupported file format: .{file_ext}")
        except Exception as e:
            raise ValueError(f"Unsupported file format: .{file_ext}")

def get_file_extension(filename):
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''

def extract_text_from_text_file(uploaded_file):
    try:
        content = uploaded_file.read()
        uploaded_file.seek(0)
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    return content.decode(encoding)
                except:
                    continue
        return content.decode('utf-8', errors='ignore')
    except Exception as e:
        raise Exception(f"Error reading text file: {str(e)}")

def extract_text_from_docx(uploaded_file):
    try:
        doc = docx.Document(uploaded_file)
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)
        for table in doc.tables:
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    if cell.text.strip():
                        row_text.append(cell.text.strip())
                if row_text:
                    full_text.append(' | '.join(row_text))
        text = '\n'.join(full_text)
        if not text.strip():
            raise Exception("No text extracted from Word document")
        return text
    except Exception as e:
        raise Exception(f"Error reading Word document: {str(e)}")

def extract_text_from_pdf(uploaded_file):
    try:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        if pdf_reader.is_encrypted:
            try:
                pdf_reader.decrypt('')
            except:
                raise Exception("PDF is encrypted")
        full_text = []
        for page_num, page in enumerate(pdf_reader.pages, 1):
            try:
                text = page.extract_text()
                if text.strip():
                    full_text.append(f"[Page {page_num}]")
                    full_text.append(text)
            except:
                continue
        if not full_text:
            raise Exception("No text extracted from PDF")
        return '\n'.join(full_text)
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")

def extract_text_from_rtf(uploaded_file):
    try:
        content = uploaded_file.read()
        uploaded_file.seek(0)
        try:
            text = content.decode('utf-8', errors='ignore')
        except:
            text = content.decode('latin-1', errors='ignore')
        text = re.sub(r'\\[a-z]+', ' ', text)
        text = re.sub(r'\{.*?\}', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'{\\rtf[^}]*}', '', text)
        text = text.strip()
        if not text:
            raise Exception("No text extracted from RTF file")
        return text
    except Exception as e:
        raise Exception(f"Error reading RTF file: {str(e)}")

def extract_text_from_odt(uploaded_file):
    try:
        import zipfile
        from xml.etree import ElementTree as ET
        with zipfile.ZipFile(io.BytesIO(uploaded_file.read())) as odt_zip:
            content = odt_zip.read('content.xml')
            root = ET.fromstring(content)
            paragraphs = root.findall('.//text:p', {'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'})
            text = '\n'.join([p.text or '' for p in paragraphs if p.text])
            if not text.strip():
                raise Exception("No text extracted from ODT file")
            return text
    except Exception as e:
        raise Exception(f"Error reading ODT file: {str(e)}")

def extract_text_from_email(uploaded_file):
    try:
        content = uploaded_file.read()
        uploaded_file.seek(0)
        try:
            text = content.decode('utf-8', errors='ignore')
        except:
            text = content.decode('latin-1', errors='ignore')
        subject_match = re.search(r'Subject:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        subject = subject_match.group(1) if subject_match else "No Subject"
        body_match = re.search(r'\n\n(.*?)(?:\n\n|\Z)', text, re.DOTALL)
        body = body_match.group(1) if body_match else text
        body = re.sub(r'^[A-Za-z-]+:\s*.+$\n?', '', body, flags=re.MULTILINE)
        body = body.strip()
        if not body:
            raise Exception("No text extracted from email file")
        return f"Subject: {subject}\n\n{body}"
    except Exception as e:
        raise Exception(f"Error reading email file: {str(e)}")

def extract_text_from_html(uploaded_file):
    try:
        content = uploaded_file.read()
        uploaded_file.seek(0)
        try:
            text = content.decode('utf-8', errors='ignore')
        except:
            text = content.decode('latin-1', errors='ignore')
        text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style.*?>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        if not text:
            raise Exception("No text extracted from HTML file")
        return text
    except Exception as e:
        raise Exception(f"Error reading HTML file: {str(e)}")

def extract_text_from_excel(uploaded_file):
    try:
        import pandas as pd
        excel_file = pd.ExcelFile(uploaded_file)
        all_text = []
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=None)
            all_text.append(f"\n--- Sheet: {sheet_name} ---")
            for row in df.values:
                row_text = []
                for cell in row:
                    if pd.notna(cell) and str(cell).strip():
                        row_text.append(str(cell).strip())
                if row_text:
                    all_text.append(' | '.join(row_text))
        text = '\n'.join(all_text)
        if not text.strip():
            raise Exception("No text extracted from Excel file")
        return text
    except ImportError:
        raise Exception("pandas not installed. Run: pip install pandas openpyxl")
    except Exception as e:
        raise Exception(f"Error reading Excel file: {str(e)}")

def extract_text_from_pptx(uploaded_file):
    try:
        from pptx import Presentation
        prs = Presentation(uploaded_file)
        text_runs = []
        for slide_num, slide in enumerate(prs.slides, 1):
            slide_text = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text.append(shape.text.strip())
            if slide_text:
                text_runs.append(f"[Slide {slide_num}]")
                text_runs.extend(slide_text)
        text = '\n'.join(text_runs)
        if not text.strip():
            raise Exception("No text extracted from PowerPoint")
        return text
    except ImportError:
        raise Exception("python-pptx not installed. Run: pip install python-pptx")
    except Exception as e:
        raise Exception(f"Error reading PowerPoint file: {str(e)}")

def extract_text_from_image(uploaded_file):
    try:
        from PIL import Image
        import pytesseract
        image = Image.open(io.BytesIO(uploaded_file.read()))
        if image.mode != 'L':
            image = image.convert('L')
        try:
            text = pytesseract.image_to_string(image, lang='eng')
        except:
            text = pytesseract.image_to_string(image)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        if not text:
            raise Exception("No text found in image")
        return text
    except ImportError as e:
        if 'PIL' in str(e):
            raise Exception("Pillow not installed. Run: pip install pillow")
        elif 'pytesseract' in str(e):
            raise Exception("pytesseract not installed. Run: pip install pytesseract")
        else:
            raise Exception(f"OCR libraries not installed: {str(e)}")
    except Exception as e:
        raise Exception(f"Error reading image: {str(e)}")