"""Document Extractors for Text Extraction"""
from typing import Dict, Any
from abc import ABC, abstractmethod
import re


class BaseExtractor(ABC):
    """Base class for document extractors"""
    
    @abstractmethod
    async def extract_text(self, file_path: str) -> str:
        """Extract text from document"""
    
    @abstractmethod
    async def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from document"""


class PDFExtractor(BaseExtractor):
    """PDF text extractor"""
    
    async def extract_text(self, file_path: str) -> str:
        """Extract text from PDF"""
        # Placeholder for PDF extraction
        # In production, use PyPDF2 or pdfplumber
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            # Fallback to simple text extraction
            return f"PDF text extraction not implemented for {file_path}"
    
    async def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                metadata = reader.metadata
                return {
                    "title": metadata.get("/Title", ""),
                    "author": metadata.get("/Author", ""),
                    "subject": metadata.get("/Subject", ""),
                    "creator": metadata.get("/Creator", ""),
                    "producer": metadata.get("/Producer", ""),
                    "page_count": len(reader.pages)
                }
        except ImportError:
            return {}


class WordExtractor(BaseExtractor):
    """Word document text extractor"""
    
    async def extract_text(self, file_path: str) -> str:
        """Extract text from Word document"""
        # Placeholder for Word extraction
        # In production, use python-docx
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except ImportError:
            return f"Word text extraction not implemented for {file_path}"
    
    async def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from Word document"""
        try:
            from docx import Document
            doc = Document(file_path)
            return {
                "title": doc.core_properties.title or "",
                "author": doc.core_properties.author or "",
                "subject": doc.core_properties.subject or "",
                "created": doc.core_properties.created.isoformat() if doc.core_properties.created else "",
                "modified": doc.core_properties.modified.isoformat() if doc.core_properties.modified else "",
                "paragraph_count": len(doc.paragraphs)
            }
        except ImportError:
            return {}


class ExcelExtractor(BaseExtractor):
    """Excel text extractor"""
    
    async def extract_text(self, file_path: str) -> str:
        """Extract text from Excel file"""
        # Placeholder for Excel extraction
        # In production, use openpyxl or pandas
        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_path, read_only=True)
            text = ""
            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                text += f"Sheet: {sheet_name}\n"
                for row in sheet.iter_rows(values_only=True):
                    row_text = " ".join(str(cell) if cell is not None else "" for cell in row)
                    if row_text.strip():
                        text += row_text + "\n"
            return text
        except ImportError:
            return f"Excel text extraction not implemented for {file_path}"
    
    async def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from Excel file"""
        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_path, read_only=True)
            return {
                "sheet_count": len(wb.sheetnames),
                "sheet_names": wb.sheetnames,
                "active_sheet": wb.active.title if wb.active else ""
            }
        except ImportError:
            return {}


class MarkdownExtractor(BaseExtractor):
    """Markdown text extractor"""
    
    async def extract_text(self, file_path: str) -> str:
        """Extract text from Markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            return f"Error reading Markdown file: {str(e)}"
    
    async def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from Markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Extract title from first heading
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else ""
            
            # Count headings
            heading_count = len(re.findall(r'^#{1,6}\s+', content, re.MULTILINE))
            
            # Count code blocks
            code_block_count = len(re.findall(r'```', content))
            
            return {
                "title": title,
                "heading_count": heading_count,
                "code_block_count": code_block_count // 2,
                "character_count": len(content)
            }
        except Exception:
            return {}


class TextChunker:
    """Text chunking utility for splitting text into manageable pieces"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_by_paragraph(self, text: str) -> list[str]:
        """Chunk text by paragraphs"""
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def chunk_by_token(self, text: str, token_limit: int = 500) -> list[str]:
        """Chunk text by approximate token count (roughly 4 chars per token)"""
        char_limit = token_limit * 4
        chunks = []
        
        for i in range(0, len(text), char_limit - self.chunk_overlap):
            chunk = text[i:i + char_limit]
            if chunk.strip():
                chunks.append(chunk.strip())
        
        return chunks
    
    def chunk_by_semantic(self, text: str) -> list[str]:
        """Chunk text by semantic boundaries (sentences)"""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def chunk(self, text: str, method: str = "paragraph") -> list[str]:
        """Chunk text using specified method"""
        if method == "paragraph":
            return self.chunk_by_paragraph(text)
        elif method == "token":
            return self.chunk_by_token(text)
        elif method == "semantic":
            return self.chunk_by_semantic(text)
        else:
            return self.chunk_by_paragraph(text)


# Factory function to get appropriate extractor
def get_extractor(file_type: str) -> BaseExtractor:
    """Get extractor for file type"""
    from app.ml.models import FileType
    
    if file_type == FileType.PDF.value:
        return PDFExtractor()
    elif file_type == FileType.WORD.value:
        return WordExtractor()
    elif file_type == FileType.EXCEL.value:
        return ExcelExtractor()
    elif file_type == FileType.MARKDOWN.value:
        return MarkdownExtractor()
    elif file_type == FileType.TXT.value:
        return MarkdownExtractor()  # Reuse for plain text
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
