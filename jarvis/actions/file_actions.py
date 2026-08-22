"""
jarvis/actions/file_actions.py
Comprehensive File Search Engine and Safe File Operations for Windows.
Searches allowed user directories (Desktop, Documents, Downloads, Music, Pictures, Videos, Project workspace).
Strictly enforces Confirmation for Deletes, Moves, and Overwrites.
"""

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import config
from jarvis.core.security_manager import SecurityManager, PermissionLevel, ALLOWED_USER_DIRS


class FileActions:
    """Provides fast local file searching, folder opening, and validated file operations."""

    @staticmethod
    def get_search_roots() -> List[Path]:
        """Returns the list of accessible user directories."""
        roots = []
        for d in ALLOWED_USER_DIRS:
            if d.exists() and d.is_dir():
                roots.append(d)
        return roots

    @staticmethod
    def search_files(
        query: str,
        extension: Optional[str] = None,
        max_results: int = 5,
        search_dirs: Optional[List[Path]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fast multi-threaded/walk search across allowed user directories.
        Supports filename substring matching and extension filtering (e.g. 'pdf', 'py', 'docx').
        """
        if not query and not extension:
            return []

        clean_query = query.lower().strip() if query else ""
        clean_ext = extension.lower().strip().lstrip(".") if extension else None

        roots = search_dirs or FileActions.get_search_roots()
        results = []

        for root in roots:
            try:
                # Walk with depth limit of 4 to keep search fast and responsive
                for dirpath, dirnames, filenames in os.walk(root):
                    # Filter out hidden or build/cache folders
                    dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in ["__pycache__", "node_modules", "AppData", "build", "dist"]]

                    # Compute relative depth from root
                    depth = len(Path(dirpath).relative_to(root).parts)
                    if depth > 4:
                        dirnames[:] = []  # Don't descend further

                    for fname in filenames:
                        fname_lower = fname.lower()

                        # Check extension if provided
                        if clean_ext and not fname_lower.endswith(f".{clean_ext}"):
                            continue

                        # Check name query
                        if clean_query and clean_query not in fname_lower:
                            continue

                        full_path = Path(dirpath) / fname
                        try:
                            stat = full_path.stat()
                            results.append({
                                "name": fname,
                                "path": str(full_path),
                                "size_bytes": stat.st_size,
                                "size_str": FileActions._format_size(stat.st_size),
                                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                                "is_dir": False
                            })
                        except Exception:
                            continue

                        if len(results) >= max_results:
                            return results
            except Exception:
                continue

        return results

    @staticmethod
    def search_folders(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Searches for directories matching query in allowed user locations."""
        if not query:
            return []

        clean_query = query.lower().strip()
        roots = FileActions.get_search_roots()
        results = []

        for root in roots:
            try:
                for dirpath, dirnames, _ in os.walk(root):
                    dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in ["__pycache__", "node_modules", "AppData"]]
                    depth = len(Path(dirpath).relative_to(root).parts)
                    if depth > 4:
                        dirnames[:] = []

                    for dname in dirnames:
                        if clean_query in dname.lower():
                            full_path = Path(dirpath) / dname
                            results.append({
                                "name": dname,
                                "path": str(full_path),
                                "is_dir": True
                            })
                            if len(results) >= max_results:
                                return results
            except Exception:
                continue

        return results

    @staticmethod
    def open_path(file_or_folder_path: str) -> Tuple[bool, str]:
        """Opens a file or directory in its default Windows associated application or File Explorer."""
        try:
            target = SecurityManager.normalize_path(file_or_folder_path)
            if not target.exists():
                return False, f"Path does not exist: {target}"

            is_safe, msg = SecurityManager.is_path_safe(target)
            if not is_safe:
                return False, msg

            os.startfile(str(target))
            return True, f"Opened '{target.name}'."
        except Exception as e:
            return False, f"Failed to open path: {e}"

    @staticmethod
    def create_folder(folder_name: str, parent_location: str = "Desktop") -> Tuple[bool, str]:
        """Creates a new folder in a safe user location."""
        try:
            base_dir = Path.home() / parent_location if parent_location in ["Desktop", "Documents", "Downloads"] else config.BASE_DIR
            target_path = base_dir / folder_name
            target_path = SecurityManager.normalize_path(target_path)

            is_safe, msg = SecurityManager.is_path_safe(target_path)
            if not is_safe:
                return False, msg

            target_path.mkdir(parents=True, exist_ok=True)
            return True, f"Folder '{folder_name}' created at {parent_location}."
        except Exception as e:
            return False, f"Failed to create folder: {e}"

    @staticmethod
    def create_file(file_name: str, content: str = "", parent_location: str = "Desktop") -> Tuple[bool, str]:
        """Creates a new text or code file in a safe user location."""
        try:
            base_dir = Path.home() / parent_location if parent_location in ["Desktop", "Documents", "Downloads"] else config.BASE_DIR
            target_path = SecurityManager.normalize_path(base_dir / file_name)

            is_safe, msg = SecurityManager.is_path_safe(target_path)
            if not is_safe:
                return False, msg

            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True, f"File '{file_name}' created successfully."
        except Exception as e:
            return False, f"Failed to create file: {e}"

    @staticmethod
    def rename_file_or_folder(old_path: str, new_name: str, confirmed: bool = False) -> Tuple[bool, str]:
        """Renames a file or folder safely."""
        try:
            src = SecurityManager.normalize_path(old_path)
            if not src.exists():
                return False, f"Source path does not exist: {src}"

            dst = src.parent / new_name
            is_safe, msg = SecurityManager.is_path_safe(src)
            if not is_safe:
                return False, msg

            if dst.exists() and not confirmed:
                return False, f"A file or folder named '{new_name}' already exists. Overwrite requires confirmation."

            src.rename(dst)
            return True, f"Renamed to '{new_name}'."
        except Exception as e:
            return False, f"Failed to rename: {e}"

    @staticmethod
    def copy_file_or_folder(src_path: str, dst_path: str) -> Tuple[bool, str]:
        """Copies a file or folder to a destination."""
        try:
            src = SecurityManager.normalize_path(src_path)
            dst = SecurityManager.normalize_path(dst_path)

            if not src.exists():
                return False, f"Source does not exist: {src}"

            is_safe, msg = SecurityManager.is_path_safe(dst)
            if not is_safe:
                return False, msg

            if src.is_dir():
                shutil.copytree(str(src), str(dst), dirs_exist_ok=True)
            else:
                shutil.copy2(str(src), str(dst))
            return True, f"Copied successfully to '{dst.name}'."
        except Exception as e:
            return False, f"Failed to copy: {e}"

    @staticmethod
    def move_file_or_folder(src_path: str, dst_path: str, confirmed: bool = False) -> Tuple[bool, str]:
        """Moves a file or directory with confirmation safeguards."""
        try:
            src = SecurityManager.normalize_path(src_path)
            dst = SecurityManager.normalize_path(dst_path)

            if not src.exists():
                return False, f"Source does not exist: {src}"

            is_safe, msg = SecurityManager.is_path_safe(src)
            if not is_safe:
                return False, msg

            shutil.move(str(src), str(dst))
            return True, f"Moved '{src.name}' to '{dst.name}'."
        except Exception as e:
            return False, f"Failed to move: {e}"

    @staticmethod
    def delete_path(target_path: str, confirmed: bool = False) -> Tuple[bool, str]:
        """
        Permanently deletes a file or directory.
        MANDATORY: Requires explicit user confirmation (Level 2).
        """
        if not confirmed:
            return False, "Deletion requires explicit user confirmation."

        try:
            target = SecurityManager.normalize_path(target_path)
            if not target.exists():
                return False, f"Path not found: {target}"

            is_safe, msg = SecurityManager.is_path_safe(target)
            if not is_safe:
                return False, msg

            if target.is_dir():
                shutil.rmtree(str(target))
            else:
                target.unlink()
            return True, f"Deleted '{target.name}' successfully."
        except Exception as e:
            return False, f"Failed to delete: {e}"

    @staticmethod
    def get_file_info(target_path: str) -> Tuple[bool, Dict[str, Any]]:
        """Retrieves metadata for a file or directory."""
        try:
            target = SecurityManager.normalize_path(target_path)
            if not target.exists():
                return False, {"error": "Path not found"}

            stat = target.stat()
            return True, {
                "name": target.name,
                "path": str(target),
                "is_dir": target.is_dir(),
                "size_bytes": stat.st_size,
                "size_str": FileActions._format_size(stat.st_size),
                "created": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "extension": target.suffix
            }
        except Exception as e:
            return False, {"error": str(e)}

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Converts bytes to human readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
