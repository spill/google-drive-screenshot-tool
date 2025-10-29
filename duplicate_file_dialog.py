#!/usr/bin/env python3
"""
Duplicate File Selection Dialog
Shows when multiple files match and lets user pick the right one
"""

import customtkinter as ctk
from typing import List, Tuple, Optional, Callable


class DuplicateFileDialog(ctk.CTkToplevel):
    """
    Dialog for selecting from multiple matching files
    """
    
    def __init__(self, parent, search_term: str, matches: List[Tuple[str, float]], 
                 metadata: Optional[List[dict]] = None):
        """
        Args:
            parent: Parent window
            search_term: What user searched for
            matches: List of (filename, score) tuples
            metadata: Optional metadata for each file (modifiedTime, size, etc.)
        """
        super().__init__(parent)
        
        self.search_term = search_term
        self.matches = matches
        self.metadata = metadata or [{}] * len(matches)
        self.selected_index = None
        
        self.title("Multiple Files Found")
        self.geometry("700x500")
        
        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 350
        y = (self.winfo_screenheight() // 2) - 250
        self.geometry(f"700x500+{x}+{y}")
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            header,
            text="⚠️  Multiple Files Found",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header,
            text=f"Searching for: '{self.search_term}'",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(anchor="w", pady=(5, 0))
        
        ctk.CTkLabel(
            header,
            text=f"Found {len(self.matches)} similar files. Please select one:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", pady=(5, 0))
        
        # Scrollable list
        list_frame = ctk.CTkScrollableFrame(self)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Radio button variable
        self.selection_var = ctk.IntVar(value=0)
        
        # Create radio buttons for each match
        for i, (filename, score) in enumerate(self.matches):
            file_meta = self.metadata[i] if i < len(self.metadata) else {}
            
            # Container for this file
            file_container = ctk.CTkFrame(list_frame, fg_color="gray25", corner_radius=8)
            file_container.pack(fill="x", pady=5)
            
            # Radio button with file info
            radio_container = ctk.CTkFrame(file_container, fg_color="transparent")
            radio_container.pack(fill="x", padx=10, pady=10)
            
            # Radio button
            radio = ctk.CTkRadioButton(
                radio_container,
                text="",
                variable=self.selection_var,
                value=i,
                font=ctk.CTkFont(size=12)
            )
            radio.pack(side="left", padx=(0, 10))
            
            # File info
            info_container = ctk.CTkFrame(radio_container, fg_color="transparent")
            info_container.pack(side="left", fill="x", expand=True)
            
            # Filename
            ctk.CTkLabel(
                info_container,
                text=f"{filename}",
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w"
            ).pack(anchor="w")
            
            # Similarity score
            ctk.CTkLabel(
                info_container,
                text=f"Similarity: {score:.1%}",
                font=ctk.CTkFont(size=11),
                text_color="lightblue",
                anchor="w"
            ).pack(anchor="w")
            
            # Additional metadata
            meta_parts = []
            
            if 'modifiedTime' in file_meta:
                modified = file_meta['modifiedTime']
                if 'T' in modified:
                    modified = modified.split('T')[0]  # Just date
                meta_parts.append(f"Modified: {modified}")
            
            if 'size' in file_meta:
                size = int(file_meta.get('size', 0))
                if size > 1024*1024:
                    size_str = f"{size/(1024*1024):.1f} MB"
                elif size > 1024:
                    size_str = f"{size/1024:.1f} KB"
                else:
                    size_str = f"{size} B"
                meta_parts.append(f"Size: {size_str}")
            
            if 'location' in file_meta and file_meta['location']:
                meta_parts.append(f"Location: {file_meta['location']}")
            
            if meta_parts:
                meta_text = " • ".join(meta_parts)
                ctk.CTkLabel(
                    info_container,
                    text=meta_text,
                    font=ctk.CTkFont(size=10),
                    text_color="gray",
                    anchor="w"
                ).pack(anchor="w")
        
        # Help text
        help_frame = ctk.CTkFrame(self, fg_color="gray20")
        help_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(
            help_frame,
            text="💡 Tip: Use index notation to avoid this dialog next time\n"
                 "Example: 'Untitled Document [2]' or 'Untitled Document #3'",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            justify="left"
        ).pack(padx=10, pady=8)
        
        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.on_cancel,
            fg_color="gray",
            hover_color="darkgray",
            width=100
        ).pack(side="right", padx=(10, 0))
        
        ctk.CTkButton(
            button_frame,
            text="Select",
            command=self.on_select,
            width=100
        ).pack(side="right")
    
    def on_select(self):
        """User clicked Select"""
        self.selected_index = self.selection_var.get()
        self.destroy()
    
    def on_cancel(self):
        """User clicked Cancel"""
        self.selected_index = None
        self.destroy()
    
    def get_selection(self) -> Optional[Tuple[str, float]]:
        """
        Get the user's selection
        
        Returns:
            (filename, score) tuple or None if cancelled
        """
        if self.selected_index is not None and 0 <= self.selected_index < len(self.matches):
            return self.matches[self.selected_index]
        return None


def show_duplicate_dialog(parent, search_term: str, matches: List[Tuple[str, float]], 
                         metadata: Optional[List[dict]] = None) -> Optional[int]:
    """
    Show duplicate file selection dialog
    
    Args:
        parent: Parent window
        search_term: What user searched for
        matches: List of (filename, score) tuples
        metadata: Optional metadata for each file
    
    Returns:
        Selected index (0-based) or None if cancelled
    """
    dialog = DuplicateFileDialog(parent, search_term, matches, metadata)
    parent.wait_window(dialog)
    
    selection = dialog.get_selection()
    if selection:
        filename, score = selection
        # Find the index
        for i, (f, s) in enumerate(matches):
            if f == filename and abs(s - score) < 0.001:
                return i
    return None


# Standalone test
if __name__ == '__main__':
    # Test the dialog
    root = ctk.CTk()
    root.geometry("400x300")
    
    test_matches = [
        ("Untitled Document", 1.0),
        ("Untitled Document", 1.0),
        ("Untitled Document", 1.0),
        ("Untitled Document (1)", 0.95),
        ("Untitled document", 0.98)
    ]
    
    test_metadata = [
        {'modifiedTime': '2024-10-27T10:00:00', 'size': 1024, 'location': 'My Drive'},
        {'modifiedTime': '2024-10-26T10:00:00', 'size': 2048, 'location': 'My Drive'},
        {'modifiedTime': '2024-10-28T10:00:00', 'size': 512, 'location': 'Shared/Projects'},
        {'modifiedTime': '2024-10-25T10:00:00', 'size': 4096, 'location': 'My Drive'},
        {'modifiedTime': '2024-10-24T10:00:00', 'size': 256, 'location': 'Archive'}
    ]
    
    def test_dialog():
        result = show_duplicate_dialog(root, "Untitled Document", test_matches, test_metadata)
        if result is not None:
            filename, score = test_matches[result]
            print(f"Selected: {filename} (index {result})")
        else:
            print("Cancelled")
    
    ctk.CTkButton(root, text="Show Duplicate Dialog", command=test_dialog).pack(pady=20)
    
    root.mainloop()