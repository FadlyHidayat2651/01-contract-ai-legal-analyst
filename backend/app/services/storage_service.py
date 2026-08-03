import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
import hashlib

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing local file storage"""
    
    def __init__(self):
        """Initialize storage service and ensure upload directory exists"""
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"StorageService initialized with upload directory: {self.upload_dir}")
    
    def save_file(self, file_content: bytes, original_filename: str) -> Tuple[str, str, int]:
        """
        Save uploaded file to local storage
        
        Args:
            file_content: File content as bytes
            original_filename: Original name of the uploaded file
            
        Returns:
            Tuple of (file_path, file_name, file_size)
        """
        try:
            # Generate unique filename to avoid collisions
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_hash = hashlib.md5(file_content[:1024]).hexdigest()[:8]
            
            # Preserve original extension
            file_ext = Path(original_filename).suffix
            unique_filename = f"{timestamp}_{file_hash}_{original_filename}"
            
            # Create full file path
            file_path = self.upload_dir / unique_filename
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            file_size = len(file_content)
            
            logger.info(f"File saved successfully: {file_path} ({file_size} bytes)")
            
            return str(file_path), unique_filename, file_size
            
        except Exception as e:
            logger.error(f"Error saving file {original_filename}: {str(e)}")
            raise
    
    def save_uploaded_file(self, file_obj, original_filename: str) -> Tuple[str, str, int]:
        """
        Save uploaded file object to local storage
        
        Args:
            file_obj: File object from FastAPI UploadFile
            original_filename: Original name of the uploaded file
            
        Returns:
            Tuple of (file_path, file_name, file_size)
        """
        try:
            # Read file content
            file_content = file_obj.read()
            
            # Reset file pointer if needed for further processing
            file_obj.seek(0)
            
            return self.save_file(file_content, original_filename)
            
        except Exception as e:
            logger.error(f"Error saving uploaded file {original_filename}: {str(e)}")
            raise
    
    def get_file_path(self, filename: str) -> Optional[Path]:
        """
        Get full path for a stored file
        
        Args:
            filename: Name of the file
            
        Returns:
            Path object if file exists, None otherwise
        """
        file_path = self.upload_dir / filename
        
        if file_path.exists():
            return file_path
        
        logger.warning(f"File not found: {filename}")
        return None
    
    def delete_file(self, filename: str) -> bool:
        """
        Delete a file from storage
        
        Args:
            filename: Name of the file to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            file_path = self.upload_dir / filename
            
            if file_path.exists():
                file_path.unlink()
                logger.info(f"File deleted successfully: {filename}")
                return True
            else:
                logger.warning(f"File not found for deletion: {filename}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting file {filename}: {str(e)}")
            return False
    
    def get_file_info(self, filename: str) -> Optional[dict]:
        """
        Get information about a stored file
        
        Args:
            filename: Name of the file
            
        Returns:
            Dictionary with file information or None if not found
        """
        file_path = self.get_file_path(filename)
        
        if not file_path:
            return None
        
        try:
            stat = file_path.stat()
            
            return {
                "filename": filename,
                "path": str(file_path),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime),
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "extension": file_path.suffix,
            }
            
        except Exception as e:
            logger.error(f"Error getting file info for {filename}: {str(e)}")
            return None
    
    def list_files(self, pattern: str = "*") -> list:
        """
        List files in upload directory
        
        Args:
            pattern: Glob pattern for filtering files (default: all files)
            
        Returns:
            List of file paths
        """
        try:
            files = list(self.upload_dir.glob(pattern))
            return [str(f) for f in files if f.is_file()]
            
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return []
    
    def get_storage_stats(self) -> dict:
        """
        Get storage statistics
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            files = list(self.upload_dir.glob("*"))
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            file_count = len([f for f in files if f.is_file()])
            
            return {
                "total_files": file_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "upload_directory": str(self.upload_dir),
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {str(e)}")
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "upload_directory": str(self.upload_dir),
            }

# Made with Bob
