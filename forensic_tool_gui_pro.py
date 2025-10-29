#!/usr/bin/env python3
"""
Google Drive Comprehensive Metadata Extraction Tool - Enhanced GUI
Focus on complete API data extraction with optional screenshot support
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import json
import os
from datetime import datetime
from drive_forensic_tool import DriveForensicTool
from forensic_verifier import ForensicVerifier

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class EnhancedForensicGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Drive Comprehensive Metadata Extraction Tool")
        self.root.geometry("1400x900")
        
        # Tools
        self.api_tool = None
        self.verifier = ForensicVerifier()
        self.authenticated = False
        self.current_session = None
        self.baseline_metadata = []
        self.session_baseline_hash = None
        self.all_files_data = []
        
        # Create output directory
        self.export_dir = 'GoogleDrive_Exports'
        os.makedirs(self.export_dir, exist_ok=True)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup enhanced UI with focus on API"""
        
        # Main container
        main = ctk.CTkFrame(self.root)
        main.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_frame = ctk.CTkFrame(main, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            title_frame,
            text="Google Drive Comprehensive Metadata Extraction",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(side="left", padx=10)
        
        ctk.CTkLabel(
            title_frame,
            text="Focus: Complete API Data Extraction",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(side="left", padx=10)
        
        # Two column layout
        content = ctk.CTkFrame(main)
        content.pack(fill="both", expand=True, pady=10)
        
        # Left panel - Controls (narrower)
        left = ctk.CTkFrame(content, width=450)
        left.pack(side="left", fill="both", padx=(0, 5))
        
        # Right panel - Log (wider)
        right = ctk.CTkFrame(content)
        right.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        self.setup_controls(left)
        self.setup_log(right)
        
    def setup_controls(self, parent):
        """Setup control panel with API focus"""
        
        scroll = ctk.CTkScrollableFrame(parent)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ============================================================
        # STEP 1: AUTHENTICATION
        # ============================================================
        ctk.CTkLabel(
            scroll,
            text="Step 1: Google API Authentication",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        ctk.CTkLabel(
            scroll,
            text="Read-only access to your Google Drive",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w", pady=(0, 10))
        
        self.auth_btn = ctk.CTkButton(
            scroll,
            text="🔐 Authenticate with Google Drive API",
            command=self.authenticate,
            height=45,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.auth_btn.pack(fill="x", pady=5)
        
        self.auth_status = ctk.CTkLabel(
            scroll,
            text="⚪ Not authenticated",
            text_color="gray",
            font=ctk.CTkFont(size=12)
        )
        self.auth_status.pack(anchor="w", pady=(5, 0))
        
        # ============================================================
        # STEP 2: ACCOUNT & DRIVE INFORMATION
        # ============================================================
        ctk.CTkLabel(
            scroll,
            text="Step 2: Account & Drive Information",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        ctk.CTkLabel(
            scroll,
            text="Get complete account and shared drive details",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w", pady=(0, 10))
        
        info_btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        info_btn_frame.pack(fill="x", pady=5)
        
        self.account_btn = ctk.CTkButton(
            info_btn_frame,
            text="📊 Get Account Info",
            command=self.get_account_info,
            height=35,
            state="disabled"
        )
        self.account_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.drives_btn = ctk.CTkButton(
            info_btn_frame,
            text="💼 Get Shared Drives",
            command=self.get_shared_drives,
            height=35,
            state="disabled"
        )
        self.drives_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        # Separator
        ctk.CTkFrame(scroll, height=2, fg_color="gray30").pack(fill="x", pady=15)
        ctk.CTkLabel(
            scroll,
            text="Step 2: File Metadata Extraction",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        ctk.CTkLabel(
            scroll,
            text="Extract complete metadata for all files",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w", pady=(0, 10))
        
        # Search type
        self.search_type = ctk.StringVar(value="all")
        
        search_frame = ctk.CTkFrame(scroll, fg_color="gray20")
        search_frame.pack(fill="x", pady=5)
        
        ctk.CTkRadioButton(
            search_frame,
            text="All files",
            variable=self.search_type,
            value="all",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=10, pady=5)
        
        limit_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        limit_frame.pack(fill="x", padx=30, pady=(0, 5))
        
        ctk.CTkLabel(limit_frame, text="Limit:", font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 5))
        self.max_results = ctk.CTkComboBox(
            limit_frame,
            values=["10", "20", "50", "100", "500", "1000"],
            width=100,
            font=ctk.CTkFont(size=11)
        )
        self.max_results.set("20")
        self.max_results.pack(side="left")
        
        ctk.CTkRadioButton(
            search_frame,
            text="Date range",
            variable=self.search_type,
            value="date",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=10, pady=5)
        
        date_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        date_frame.pack(fill="x", padx=30, pady=(0, 5))
        
        ctk.CTkLabel(date_frame, text="From:", font=ctk.CTkFont(size=11)).pack(anchor="w")
        self.start_date = ctk.CTkEntry(date_frame, placeholder_text="2024-01-01", font=ctk.CTkFont(size=11))
        self.start_date.pack(fill="x", pady=2)
        
        ctk.CTkLabel(date_frame, text="To:", font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(5, 0))
        self.end_date = ctk.CTkEntry(date_frame, placeholder_text="2024-12-31", font=ctk.CTkFont(size=11))
        self.end_date.pack(fill="x", pady=2)
        
        ctk.CTkRadioButton(
            search_frame,
            text="Specific file",
            variable=self.search_type,
            value="specific",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=10, pady=5)
        
        specific_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        specific_frame.pack(fill="x", padx=30, pady=(0, 10))
        
        ctk.CTkLabel(specific_frame, text="File ID:", font=ctk.CTkFont(size=11)).pack(anchor="w")
        self.file_id_entry = ctk.CTkEntry(specific_frame, placeholder_text="Enter file ID", font=ctk.CTkFont(size=11))
        self.file_id_entry.pack(fill="x", pady=2)
        
        # Extract button
        self.extract_btn = ctk.CTkButton(
            scroll,
            text="🔍 Extract Complete Metadata",
            command=self.extract_metadata,
            height=45,
            state="disabled",
            fg_color="green",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.extract_btn.pack(fill="x", pady=10)
        
        # Progress
        self.progress = ctk.CTkProgressBar(scroll)
        self.progress.pack(fill="x", pady=5)
        self.progress.set(0)
        
        self.progress_label = ctk.CTkLabel(scroll, text="", font=ctk.CTkFont(size=11))
        self.progress_label.pack(anchor="w")
        
        # Separator
        ctk.CTkFrame(scroll, height=2, fg_color="gray30").pack(fill="x", pady=15)
        
        # ============================================================
        # STEP 3: VERIFICATION
        # ============================================================
        ctk.CTkLabel(
            scroll,
            text="Step 3: Data Integrity Verification",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        ctk.CTkLabel(
            scroll,
            text="Verify no changes during extraction",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w", pady=(0, 10))
        
        self.verify_btn = ctk.CTkButton(
            scroll,
            text="✓ Verify Data Integrity",
            command=self.verify_data,
            height=40,
            state="disabled",
            fg_color="orange"
        )
        self.verify_btn.pack(fill="x", pady=5)
        
        # Separator
        ctk.CTkFrame(scroll, height=2, fg_color="gray30").pack(fill="x", pady=15)
        
        # ============================================================
        # STEP 4: EXPORT
        # ============================================================
        ctk.CTkLabel(
            scroll,
            text="Step 4: Export Options",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        export_frame = ctk.CTkFrame(scroll, fg_color="gray20")
        export_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(
            export_frame,
            text="📁 Open Export Folder",
            command=self.open_export_folder,
            height=35
        ).pack(fill="x", padx=10, pady=10)
        
    def setup_log(self, parent):
        """Setup enhanced log panel"""
        
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(
            header,
            text="Activity Log",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        ctk.CTkButton(
            header,
            text="Clear Log",
            command=self.clear_log,
            width=100,
            height=28,
            fg_color="gray30"
        ).pack(side="right")
        
        # Enhanced log with better formatting
        self.log_text = ctk.CTkTextbox(
            parent,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.log("=" * 80, "info")
        self.log("Google Drive Comprehensive Metadata Extraction Tool", "info")
        self.log("=" * 80, "info")
        self.log("", "info")
        self.log("This tool extracts COMPLETE metadata from Google Drive API", "info")
        self.log("All operations are READ-ONLY - your files will not be modified", "success")
        self.log("", "info")
        self.log("Ready to begin. Please authenticate to start.", "info")
        
    def log(self, message, level="info"):
        """Enhanced logging with better formatting"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        icons = {
            "info": "ℹ️",
            "success": "✓",
            "warning": "⚠️",
            "error": "✗"
        }
        icon = icons.get(level, "ℹ️")
        
        # Don't add timestamp to separator lines
        if message.startswith("=") or message.startswith("-") or message == "":
            formatted = f"{message}\n"
        else:
            formatted = f"[{timestamp}] {icon} {message}\n"
        
        self.log_text.insert("end", formatted)
        self.log_text.see("end")
        self.root.update()
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.delete("1.0", "end")
        self.log("Log cleared", "info")
    
    def authenticate(self):
        """Authenticate with Google API"""
        self.log("=" * 80, "info")
        self.log("Starting authentication process...", "info")
        self.log("=" * 80, "info")
        
        self.auth_btn.configure(state="disabled")
        
        def auth_thread():
            try:
                self.api_tool = DriveForensicTool()
                
                self.root.after(0, lambda: self.log("Checking for credentials...", "info"))
                
                if self.api_tool.authenticate():
                    self.authenticated = True
                    self.root.after(0, lambda: self.auth_status.configure(
                        text="🟢 Authenticated Successfully",
                        text_color="green"
                    ))
                    self.root.after(0, lambda: self.account_btn.configure(state="normal"))
                    self.root.after(0, lambda: self.drives_btn.configure(state="normal"))
                    self.root.after(0, lambda: self.extract_btn.configure(state="normal"))
                    
                    self.root.after(0, lambda: self.log("✓ Successfully authenticated with READ-ONLY access", "success"))
                    
                    # Test read-only
                    self.root.after(0, lambda: self.log("Testing read-only restriction...", "info"))
                    if self.api_tool.test_read_only_restriction():
                        self.root.after(0, lambda: self.log("✓ GOOD: Cannot create files (read-only confirmed)", "success"))
                    
                    self.root.after(0, lambda: self.log("=" * 80, "success"))
                    self.root.after(0, lambda: self.log("Authentication complete! You can now extract metadata.", "success"))
                    self.root.after(0, lambda: self.log("=" * 80, "success"))
                else:
                    self.root.after(0, lambda: self.log("Authentication failed", "error"))
                    self.root.after(0, lambda: self.auth_status.configure(
                        text="🔴 Authentication Failed",
                        text_color="red"
                    ))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error: {e}", "error"))
                import traceback
                traceback.print_exc()
            finally:
                self.root.after(0, lambda: self.auth_btn.configure(state="normal"))
        
        threading.Thread(target=auth_thread, daemon=True).start()
    
    def get_account_info(self):
        """Get comprehensive Drive account information"""
        if not self.authenticated:
            messagebox.showerror("Error", "Please authenticate first")
            return
        
        self.log("=" * 80, "info")
        self.log("Fetching comprehensive account information...", "info")
        self.log("=" * 80, "info")
        
        self.account_btn.configure(state="disabled")
        
        def account_thread():
            try:
                about = self.api_tool.get_about_info()
                
                if about:
                    # Save to file
                    account_file = os.path.join(self.export_dir, 'account_info.json')
                    with open(account_file, 'w', encoding='utf-8') as f:
                        json.dump(about, f, indent=2, default=str)
                    
                    self.root.after(0, lambda: self.log("", "info"))
                    self.root.after(0, lambda: self.log(f"✓ Account info saved to: {account_file}", "success"))
                else:
                    self.root.after(0, lambda: self.log("Failed to fetch account info", "error"))
                    
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error: {e}", "error"))
            finally:
                self.root.after(0, lambda: self.account_btn.configure(state="normal"))
        
        threading.Thread(target=account_thread, daemon=True).start()
    
    def get_shared_drives(self):
        """Get list of all shared drives"""
        if not self.authenticated:
            messagebox.showerror("Error", "Please authenticate first")
            return
        
        self.log("=" * 80, "info")
        self.log("Fetching shared drives (Team Drives)...", "info")
        self.log("=" * 80, "info")
        
        self.drives_btn.configure(state="disabled")
        
        def drives_thread():
            try:
                drives = self.api_tool.get_drives_list()
                
                if drives:
                    # Save to file
                    drives_file = os.path.join(self.export_dir, 'shared_drives.json')
                    with open(drives_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            'timestamp': datetime.now().isoformat(),
                            'drive_count': len(drives),
                            'drives': drives
                        }, f, indent=2, default=str)
                    
                    self.root.after(0, lambda: self.log("", "info"))
                    self.root.after(0, lambda: self.log(f"✓ Found {len(drives)} shared drives", "success"))
                    
                    for i, drive in enumerate(drives[:10], 1):
                        drive_name = drive.get('name', 'Unknown')
                        self.root.after(0, lambda i=i, n=drive_name:
                            self.log(f"  {i}. {n}", "info"))
                    
                    if len(drives) > 10:
                        self.root.after(0, lambda: self.log(f"  ... and {len(drives)-10} more", "info"))
                    
                    self.root.after(0, lambda: self.log(f"✓ Saved to: {drives_file}", "success"))
                else:
                    self.root.after(0, lambda: self.log("No shared drives found or not accessible", "info"))
                    
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error: {e}", "error"))
            finally:
                self.root.after(0, lambda: self.drives_btn.configure(state="normal"))
        
        threading.Thread(target=drives_thread, daemon=True).start()
    
    def extract_metadata(self):
        """Extract comprehensive metadata including revisions and comments"""
        if not self.authenticated:
            messagebox.showerror("Error", "Please authenticate first")
            return
        
        self.log("=" * 80, "info")
        self.log("Starting comprehensive metadata extraction...", "info")
        self.log("=" * 80, "info")
        
        self.extract_btn.configure(state="disabled")
        self.progress.set(0)
        
        def extract_thread():
            try:
                search_type = self.search_type.get()
                files = []
                
                if search_type == "all":
                    max_results = int(self.max_results.get())
                    self.root.after(0, lambda: self.log(f"Searching for up to {max_results} files...", "info"))
                    files = self.api_tool.list_files(max_results=max_results)
                    
                elif search_type == "date":
                    start = self.start_date.get() or "2024-01-01"
                    end = self.end_date.get() or "2024-12-31"
                    self.root.after(0, lambda: self.log(f"Searching for files modified between {start} and {end}...", "info"))
                    files = self.api_tool.find_files_by_date_range(
                        f'{start}T00:00:00',
                        f'{end}T23:59:59'
                    )
                    
                elif search_type == "specific":
                    file_id = self.file_id_entry.get().strip()
                    if not file_id:
                        self.root.after(0, lambda: messagebox.showerror("Error", "Enter a file ID"))
                        return
                    
                    self.root.after(0, lambda: self.log(f"Fetching specific file: {file_id}", "info"))
                    metadata = self.api_tool.get_file_metadata(file_id)
                    if metadata:
                        files = [metadata]
                
                if not files:
                    self.root.after(0, lambda: self.log("No files found", "warning"))
                    return
                
                self.root.after(0, lambda: self.log(f"✓ Found {len(files)} files", "success"))
                
                # Show sample of files
                self.root.after(0, lambda: self.log("--- Files Found ---", "info"))
                for i, f in enumerate(files[:10], 1):
                    file_name = f.get('name', 'Unknown')
                    modified = f.get('modifiedTime', 'N/A')
                    self.root.after(0, lambda i=i, name=file_name, mod=modified:
                        self.log(f"  {i}. {name} (Modified: {mod})", "info"))
                
                if len(files) > 10:
                    remaining = len(files) - 10
                    self.root.after(0, lambda r=remaining: self.log(f"  ... and {r} more", "info"))
                
                self.root.after(0, lambda: self.log("-------------------", "info"))
                
                # Create session
                self.current_session = datetime.now().strftime('%Y%m%d_%H%M%S')
                self.root.after(0, lambda: self.log(f"Session ID: {self.current_session}", "info"))
                
                # Get COMPREHENSIVE data for each file (metadata + revisions + comments)
                self.root.after(0, lambda: self.log("", "info"))
                self.root.after(0, lambda: self.log("=" * 80, "info"))
                self.root.after(0, lambda: self.log("Extracting COMPREHENSIVE data (metadata + activity log + comments)...", "info"))
                self.root.after(0, lambda: self.log("=" * 80, "info"))
                
                comprehensive_data = []
                total = len(files)
                
                for i, file in enumerate(files, 1):
                    progress = i / total
                    self.root.after(0, lambda p=progress: self.progress.set(p))
                    self.root.after(0, lambda i=i, t=total: self.progress_label.configure(text=f"Processing {i}/{t}"))
                    
                    file_id = file.get('id')
                    file_name = file.get('name', 'Unknown')
                    
                    self.root.after(0, lambda n=file_name, i=i, t=total: self.log(f"[{i}/{t}] {n}", "info"))
                    
                    # Get EVERYTHING: metadata + revisions + comments + permissions + labels
                    comp_data = self.api_tool.get_comprehensive_file_data(file_id)
                    comprehensive_data.append(comp_data)
                    
                    # Log what we got
                    rev_count = comp_data.get('revision_count', 0)
                    comment_count = comp_data.get('comment_count', 0)
                    perm_count = comp_data.get('permission_count', 0)
                    has_labels = bool(comp_data.get('labels', {}))
                    
                    self.root.after(0, lambda rc=rev_count, cc=comment_count, pc=perm_count, hl=has_labels: 
                        self.log(f"  → {rc} revisions, {cc} comments, {pc} permissions" + 
                                 (" + labels" if hl else ""), "info"))
                
                self.baseline_metadata = comprehensive_data
                self.all_files_data = comprehensive_data
                
                # Generate hash
                self.session_baseline_hash = self.verifier.generate_hash(comprehensive_data)
                
                # Save baseline
                baseline_path = os.path.join(
                    self.export_dir,
                    f'session_{self.current_session}_BASELINE.json'
                )
                
                with open(baseline_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'session_id': self.current_session,
                        'capture_time': datetime.now().isoformat(),
                        'total_files': len(comprehensive_data),
                        'baseline_hash_sha256': self.session_baseline_hash,
                        'files': comprehensive_data
                    }, f, indent=2, default=str)
                
                self.root.after(0, lambda: self.log("", "info"))
                self.root.after(0, lambda: self.log("=" * 80, "success"))
                self.root.after(0, lambda: self.log(f"Extraction complete! Processed {len(comprehensive_data)} files", "success"))
                
                # Summary stats
                total_revisions = sum(f.get('revision_count', 0) for f in comprehensive_data)
                total_comments = sum(f.get('comment_count', 0) for f in comprehensive_data)
                total_permissions = sum(f.get('permission_count', 0) for f in comprehensive_data)
                self.root.after(0, lambda tr=total_revisions, tc=total_comments, tp=total_permissions: 
                    self.log(f"Total: {tr} revisions, {tc} comments, {tp} permissions extracted", "success"))
                
                self.root.after(0, lambda: self.log(f"Baseline hash: {self.session_baseline_hash}", "info"))
                self.root.after(0, lambda: self.log(f"Saved to: {baseline_path}", "info"))
                self.root.after(0, lambda: self.log("=" * 80, "success"))
                
                self.root.after(0, lambda: self.verify_btn.configure(state="normal"))
                
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error: {e}", "error"))
                import traceback
                traceback.print_exc()
            finally:
                self.root.after(0, lambda: self.extract_btn.configure(state="normal"))
                self.root.after(0, lambda: self.progress.set(0))
                self.root.after(0, lambda: self.progress_label.configure(text=""))
        
        threading.Thread(target=extract_thread, daemon=True).start()
    
    def verify_data(self):
        """Verify data integrity including revisions"""
        if not self.current_session:
            messagebox.showerror("Error", "No active session to verify")
            return
        
        self.log("=" * 80, "info")
        self.log("Verifying data integrity (including activity log)...", "info")
        self.log("=" * 80, "info")
        
        self.verify_btn.configure(state="disabled")
        
        def verify_thread():
            try:
                # Re-capture comprehensive data
                self.root.after(0, lambda: self.log("Re-capturing comprehensive metadata for verification...", "info"))
                
                post_data = []
                total = len(self.baseline_metadata)
                
                for i, baseline_item in enumerate(self.baseline_metadata, 1):
                    progress = i / total
                    self.root.after(0, lambda p=progress: self.progress.set(p))
                    self.root.after(0, lambda i=i, t=total: self.progress_label.configure(text=f"Re-capturing {i}/{t}"))
                    
                    file_id = baseline_item.get('file_id') or baseline_item.get('metadata', {}).get('id')
                    
                    # Re-fetch everything
                    comp_data = self.api_tool.get_comprehensive_file_data(file_id)
                    post_data.append(comp_data)
                
                # Generate new hash
                post_hash = self.verifier.generate_hash(post_data)
                
                # Save post-capture
                post_path = os.path.join(
                    self.export_dir,
                    f'session_{self.current_session}_POST.json'
                )
                
                with open(post_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'session_id': self.current_session,
                        'capture_time': datetime.now().isoformat(),
                        'total_files': len(post_data),
                        'post_hash_sha256': post_hash,
                        'files': post_data
                    }, f, indent=2, default=str)
                
                # Compare
                result = self.verifier.verify_no_changes(self.baseline_metadata, post_data)
                
                # Save verification
                verification_path = os.path.join(
                    self.export_dir,
                    f'session_{self.current_session}_VERIFICATION.json'
                )
                
                with open(verification_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'session_id': self.current_session,
                        'baseline_hash': self.session_baseline_hash,
                        'post_hash': post_hash,
                        'hashes_match': self.session_baseline_hash == post_hash,
                        'verification_result': result
                    }, f, indent=2, default=str)
                
                # Attestation
                attestation = self.verifier.generate_attestation(result)
                attestation_with_hashes = f"""
SESSION: {self.current_session}

HASH COMPARISON:
  Baseline Hash: {self.session_baseline_hash}
  Post Hash:     {post_hash}
  Match:         {self.session_baseline_hash == post_hash}

{attestation}
"""
                
                attestation_path = os.path.join(
                    self.export_dir,
                    f'session_{self.current_session}_ATTESTATION.txt'
                )
                with open(attestation_path, 'w', encoding='utf-8') as f:
                    f.write(attestation_with_hashes)
                
                # Results
                self.root.after(0, lambda: self.log("", "info"))
                self.root.after(0, lambda: self.log("=" * 80, "info"))
                self.root.after(0, lambda: self.log("VERIFICATION RESULTS:", "info"))
                self.root.after(0, lambda: self.log("=" * 80, "info"))
                self.root.after(0, lambda: self.log(f"Baseline Hash: {self.session_baseline_hash}", "info"))
                self.root.after(0, lambda: self.log(f"Post Hash:     {post_hash}", "info"))
                
                if self.session_baseline_hash == post_hash:
                    self.root.after(0, lambda: self.log("", "info"))
                    self.root.after(0, lambda: self.log("✓✓✓ VERIFICATION PASSED ✓✓✓", "success"))
                    self.root.after(0, lambda: self.log("No changes detected - data integrity confirmed", "success"))
                    self.root.after(0, lambda: self.log("All metadata, revisions, and comments are identical", "success"))
                    self.root.after(0, lambda: self.log("=" * 80, "success"))
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Success",
                        f"Integrity verified!\n\nFiles: {len(post_data)}\nHashes match: YES\nAll activity logs preserved"
                    ))
                else:
                    self.root.after(0, lambda: self.log("", "info"))
                    self.root.after(0, lambda: self.log("✗✗✗ VERIFICATION FAILED ✗✗✗", "error"))
                    self.root.after(0, lambda: self.log("Changes detected! Review verification report.", "error"))
                    self.root.after(0, lambda: self.log("=" * 80, "error"))
                    self.root.after(0, lambda: messagebox.showwarning("Failed", "Hashes don't match!"))
                
                self.root.after(0, lambda: self.log(f"Verification saved to: {verification_path}", "info"))
                self.root.after(0, lambda: self.log(f"Attestation saved to: {attestation_path}", "info"))
                
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error: {e}", "error"))
                import traceback
                traceback.print_exc()
            finally:
                self.root.after(0, lambda: self.verify_btn.configure(state="normal"))
                self.root.after(0, lambda: self.progress.set(0))
                self.root.after(0, lambda: self.progress_label.configure(text=""))
        
        threading.Thread(target=verify_thread, daemon=True).start()
    
    def open_export_folder(self):
        """Open the export folder"""
        import subprocess
        import platform
        
        try:
            if platform.system() == "Windows":
                os.startfile(self.export_dir)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", self.export_dir])
            else:
                subprocess.Popen(["xdg-open", self.export_dir])
            
            self.log(f"Opened folder: {self.export_dir}", "info")
        except Exception as e:
            self.log(f"Could not open folder: {e}", "error")


def main():
    root = ctk.CTk()
    app = EnhancedForensicGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()