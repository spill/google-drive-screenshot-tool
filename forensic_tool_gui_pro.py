#!/usr/bin/env python3
"""
Google Drive File Documentation Tool - Multi-Mode GUI
Supports: Full Mode (API) and Hybrid Mode (UI Scraping)
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import json
import os
from datetime import datetime
from difflib import SequenceMatcher
from drive_forensic_tool import DriveForensicTool
from screenshot_tool import DriveScreenshotTool
from forensic_verifier import ForensicVerifier
from ui_scraper import DriveUIScraper, generate_hash_from_scraped_data


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class MultiModeForensicGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Drive Metadata Capture Tool")
        self.root.geometry("1000x750")
        
        # Tools
        self.api_tool = None
        self.screenshot_tool = None
        self.verifier = ForensicVerifier()
        self.ui_scraper = None
        self.files = []
        self.file_names = []  # For hybrid mode
        self.authenticated = False
        self.baseline_metadata = []
        
        # Session tracking
        self.current_session = None
        self.session_baseline_hash = None
        self.mode = "full"  # full or hybrid
        
        # Create output directories
        self.screenshot_dir = 'GoogleDrive_Screenshots'
        self.export_dir = 'GoogleDrive_Exports'
        os.makedirs(self.screenshot_dir, exist_ok=True)
        os.makedirs(self.export_dir, exist_ok=True)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI with mode selection"""
        
        # Main container
        main = ctk.CTkFrame(self.root)
        main.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        ctk.CTkLabel(
            main,
            text="Google Drive Metadata Capture Tool",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=10)
        
        # MODE SELECTOR
        mode_frame = ctk.CTkFrame(main, fg_color="gray20", corner_radius=10)
        mode_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(
            mode_frame,
            text="Select Mode:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.mode_var = ctk.StringVar(value="full")
        
        ctk.CTkRadioButton(
            mode_frame,
            text="Full Mode (API + Screenshots) - Best quality, requires authentication",
            variable=self.mode_var,
            value="full",
            command=self.on_mode_change,
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=20, pady=3)
        
        ctk.CTkRadioButton(
            mode_frame,
            text="Hybrid Mode (UI Scraping + Screenshots) - No API needed, manual login",
            variable=self.mode_var,
            value="hybrid",
            command=self.on_mode_change,
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=20, pady=(3, 10))
        
        # Two column layout
        content = ctk.CTkFrame(main)
        content.pack(fill="both", expand=True, pady=10)
        
        # Left panel - Controls
        left = ctk.CTkFrame(content, width=400)
        left.pack(side="left", fill="both", padx=(0, 5))
        
        # Right panel - Log
        right = ctk.CTkFrame(content)
        right.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        self.setup_controls(left)
        self.setup_log(right)
        
    def setup_controls(self, parent):
        """Setup control panel"""
        
        scroll = ctk.CTkScrollableFrame(parent)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # FULL MODE SECTION
        self.full_mode_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.full_mode_frame.pack(fill="x")
        
        # Step 1: Authentication
        ctk.CTkLabel(
            self.full_mode_frame,
            text="1. Authentication (Full Mode Only)",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        self.auth_btn = ctk.CTkButton(
            self.full_mode_frame,
            text="Authenticate with Google API",
            command=self.authenticate,
            height=40
        )
        self.auth_btn.pack(fill="x", pady=5)
        
        self.auth_status = ctk.CTkLabel(self.full_mode_frame, text="Not authenticated", text_color="gray")
        self.auth_status.pack(anchor="w", pady=(0, 10))
        
        # Separator
        ctk.CTkFrame(self.full_mode_frame, height=2, fg_color="gray").pack(fill="x", pady=10)
        
        # Step 2: API Search
        ctk.CTkLabel(
            self.full_mode_frame,
            text="2. File Search (API)",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        self.search_type = ctk.StringVar(value="all")
        
        ctk.CTkRadioButton(self.full_mode_frame, text="All files", variable=self.search_type, value="all").pack(anchor="w", pady=2)
        
        max_frame = ctk.CTkFrame(self.full_mode_frame, fg_color="transparent")
        max_frame.pack(fill="x", padx=20, pady=2)
        
        ctk.CTkLabel(max_frame, text="Max results:").pack(side="left", padx=(0, 5))
        self.max_results = ctk.CTkComboBox(
            max_frame,
            values=["10", "20", "50", "100", "500", "1000"],
            width=100
        )
        self.max_results.set("20")
        self.max_results.pack(side="left")
        
        ctk.CTkRadioButton(self.full_mode_frame, text="Date range", variable=self.search_type, value="date").pack(anchor="w", pady=2)
        
        date_frame = ctk.CTkFrame(self.full_mode_frame, fg_color="transparent")
        date_frame.pack(fill="x", padx=20, pady=2)
        
        ctk.CTkLabel(date_frame, text="Start:").pack(side="left")
        self.start_date = ctk.CTkEntry(date_frame, width=100, placeholder_text="2024-01-01")
        self.start_date.pack(side="left", padx=5)
        
        ctk.CTkLabel(date_frame, text="End:").pack(side="left", padx=(10, 0))
        self.end_date = ctk.CTkEntry(date_frame, width=100, placeholder_text="2024-12-31")
        self.end_date.pack(side="left", padx=5)
        
        self.api_search_btn = ctk.CTkButton(
            self.full_mode_frame,
            text="Search Files (API)",
            command=self.search_files_api,
            height=40,
            state="disabled"
        )
        self.api_search_btn.pack(fill="x", pady=10)
        
        # HYBRID MODE SECTION
        self.hybrid_mode_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.hybrid_mode_frame.pack(fill="x")
        self.hybrid_mode_frame.pack_forget()  # Hidden by default
        
        ctk.CTkLabel(
            self.hybrid_mode_frame,
            text="1. File Names (Manual Input)",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        ctk.CTkLabel(
            self.hybrid_mode_frame,
            text="Enter file names (one per line):",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", pady=(0, 5))
        
        self.multi_names = ctk.CTkTextbox(self.hybrid_mode_frame, height=150)
        self.multi_names.pack(fill="x", pady=5)
        
        ctk.CTkButton(
            self.hybrid_mode_frame,
            text="📄 Load from file",
            command=self.load_file_list,
            height=32,
            fg_color="gray"
        ).pack(fill="x", pady=5)
        
        self.hybrid_search_btn = ctk.CTkButton(
            self.hybrid_mode_frame,
            text="Start Hybrid Workflow",
            command=self.start_hybrid_workflow,
            height=40,
            fg_color="purple"
        )
        self.hybrid_search_btn.pack(fill="x", pady=10)
        
        # Separator
        ctk.CTkFrame(scroll, height=2, fg_color="gray").pack(fill="x", pady=10)
        
        # Step 3: Screenshots (common to both modes)
        ctk.CTkLabel(
            scroll,
            text="3. Screenshot Capture",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        self.use_profile = ctk.CTkCheckBox(scroll, text="Use existing Chrome profile")
        self.use_profile.select()
        self.use_profile.pack(anchor="w", pady=5)
        
        self.screenshot_btn = ctk.CTkButton(
            scroll,
            text="Start Screenshot Capture",
            command=self.start_screenshots,
            height=40,
            state="disabled"
        )
        self.screenshot_btn.pack(fill="x", pady=5)
        
        self.progress = ctk.CTkProgressBar(scroll)
        self.progress.pack(fill="x", pady=5)
        self.progress.set(0)
        
        self.progress_label = ctk.CTkLabel(scroll, text="")
        self.progress_label.pack(anchor="w")
        
        # Separator
        ctk.CTkFrame(scroll, height=2, fg_color="gray").pack(fill="x", pady=10)
        
        # Step 4: Verify (only enabled if baseline exists)
        ctk.CTkLabel(
            scroll,
            text="4. Integrity Verification",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        self.verify_btn = ctk.CTkButton(
            scroll,
            text="Verify Data Integrity",
            command=self.verify_data,
            height=40,
            state="disabled",
            fg_color="green"
        )
        self.verify_btn.pack(fill="x", pady=5)
        
    def setup_log(self, parent):
        """Setup log panel"""
        
        ctk.CTkLabel(
            parent,
            text="Activity Log",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.log_text = ctk.CTkTextbox(
            parent,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.log("Ready to begin - Select mode above", "info")
        
    def on_mode_change(self):
        """Handle mode change"""
        self.mode = self.mode_var.get()
        
        if self.mode == "full":
            # Show full mode controls
            self.full_mode_frame.pack(fill="x", before=self.hybrid_mode_frame)
            self.hybrid_mode_frame.pack_forget()
            self.log("Switched to Full Mode (API)", "info")
        else:
            # Show hybrid mode controls
            self.hybrid_mode_frame.pack(fill="x", before=self.full_mode_frame)
            self.full_mode_frame.pack_forget()
            self.log("Switched to Hybrid Mode (UI Scraping)", "info")
            self.log("No API authentication needed!", "success")
    
    def log(self, message, level="info"):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        icons = {"info": "ℹ️", "success": "✓", "warning": "⚠️", "error": "✗"}
        icon = icons.get(level, "ℹ️")
        
        formatted = f"[{timestamp}] {icon} {message}\n"
        self.log_text.insert("end", formatted)
        self.log_text.see("end")
        self.root.update()
    
    def load_file_list(self):
        """Load file names from text file"""
        filename = filedialog.askopenfilename(
            title="Select file list",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.multi_names.delete("1.0", "end")
                self.multi_names.insert("1.0", content)
                self.log(f"Loaded {os.path.basename(filename)}", "success")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load: {e}")
    
    def authenticate(self):
        """Authenticate with Google API (Full Mode only)"""
        self.log("Authenticating with Google API...", "info")
        self.auth_btn.configure(state="disabled")
        
        def auth_thread():
            try:
                self.api_tool = DriveForensicTool()
                if self.api_tool.authenticate():
                    self.authenticated = True
                    self.root.after(0, lambda: self.log("Authenticated successfully", "success"))
                    self.root.after(0, lambda: self.auth_status.configure(text="✓ Authenticated", text_color="green"))
                    self.root.after(0, lambda: self.api_search_btn.configure(state="normal"))
                    
                    if self.api_tool.test_read_only_restriction():
                        self.root.after(0, lambda: self.log("Read-only access confirmed", "success"))
                else:
                    self.root.after(0, lambda: self.log("Authentication failed", "error"))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error: {e}", "error"))
            finally:
                self.root.after(0, lambda: self.auth_btn.configure(state="normal"))
        
        threading.Thread(target=auth_thread, daemon=True).start()
    
    def search_files_api(self):
        """Search files using API (Full Mode)"""
        if not self.authenticated:
            messagebox.showerror("Error", "Authenticate first")
            return
        
        self.log("Searching via API...", "info")
        self.api_search_btn.configure(state="disabled")
        
        def search_thread():
            try:
                search_type = self.search_type.get()
                
                if search_type == "all":
                    max_results = int(self.max_results.get())
                    files = self.api_tool.list_files(max_results=max_results)
                elif search_type == "date":
                    start = self.start_date.get() or "2024-01-01"
                    end = self.end_date.get() or "2024-12-31"
                    files = self.api_tool.find_files_by_date_range(
                        f'{start}T00:00:00',
                        f'{end}T23:59:59'
                    )
                else:
                    files = []
                
                self.files = files
                
                if files:
                    # Create session
                    self.current_session = datetime.now().strftime('%Y%m%d_%H%M%S')
                    self.root.after(0, lambda: self.log(f"Session: {self.current_session}", "info"))
                    
                    # Capture baseline from API
                    self.baseline_metadata = []
                    for file in files:
                        detailed = self.api_tool.service.files().get(
                            fileId=file['id'],
                            fields='id,name,mimeType,createdTime,modifiedTime,viewedByMeTime,size,owners'
                        ).execute()
                        self.baseline_metadata.append(detailed)
                    
                    # Generate hash
                    self.session_baseline_hash = self.verifier.generate_hash(self.baseline_metadata)
                    
                    # Save baseline
                    baseline_path = os.path.join(
                        self.export_dir,
                        f'session_{self.current_session}_BASELINE_BEFORE.json'
                    )
                    with open(baseline_path, 'w', encoding='utf-8') as f:
                        json.dump({
                            'session_id': self.current_session,
                            'mode': 'full_api',
                            'capture_time': datetime.now().isoformat(),
                            'total_files': len(self.baseline_metadata),
                            'baseline_hash_sha256': self.session_baseline_hash,
                            'files': self.baseline_metadata
                        }, f, indent=2)
                    
                    self.root.after(0, lambda: self.log(f"Found {len(files)} files", "success"))
                    self.root.after(0, lambda: self.log(f"Baseline hash: {self.session_baseline_hash}", "info"))
                    
                    # Show files
                    self.root.after(0, lambda: self.log("--- Files Found ---", "info"))
                    for i, f in enumerate(files[:10], 1):
                        file_name = f['name']
                        modified = f.get('modifiedTime', 'N/A')
                        self.root.after(0, lambda i=i, name=file_name, mod=modified:
                            self.log(f"  {i}. {name} (Modified: {mod})", "info"))
                    
                    if len(files) > 10:
                        remaining = len(files) - 10
                        self.root.after(0, lambda r=remaining: self.log(f"  ... and {r} more", "info"))
                    
                    self.root.after(0, lambda: self.log("-------------------", "info"))
                    self.root.after(0, lambda: self.screenshot_btn.configure(state="normal"))
                else:
                    self.root.after(0, lambda: self.log("No files found", "warning"))
                    
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error: {e}", "error"))
            finally:
                self.root.after(0, lambda: self.api_search_btn.configure(state="normal"))
        
        threading.Thread(target=search_thread, daemon=True).start()
    
    def start_hybrid_workflow(self):
        """Start hybrid workflow (UI scraping + screenshots)"""
        names_text = self.multi_names.get("1.0", "end").strip()
        if not names_text:
            messagebox.showerror("Error", "Enter file names")
            return
        
        self.file_names = [n.strip() for n in names_text.split('\n') if n.strip()]
        
        self.log(f"Starting Hybrid Mode for {len(self.file_names)} files", "info")
        self.log("Will scrape metadata from UI (no API)", "info")
        
        # Create session
        self.current_session = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log(f"Session: {self.current_session}", "info")
        
        # Enable screenshot button
        self.screenshot_btn.configure(state="normal")
        
        self.log("Ready to capture screenshots", "success")
        self.log("Click 'Start Screenshot Capture' to begin", "info")
    
    def start_screenshots(self):
        """Start screenshot capture (works for both modes)"""
        use_profile = self.use_profile.get()
        
        if use_profile:
            response = messagebox.askyesno(
                "Chrome Profile",
                "Close ALL Chrome windows now.\n\nClick Yes when ready."
            )
            if not response:
                return
        
        self.log("Starting screenshots...", "info")
        self.screenshot_btn.configure(state="disabled")
        self.progress.set(0)
        
        def screenshot_thread():
            try:
                self.screenshot_tool = DriveScreenshotTool(screenshot_dir=self.screenshot_dir)
                
                if not self.screenshot_tool.setup_browser(headless=False, use_existing_profile=use_profile):
                    self.root.after(0, lambda: self.log("Browser setup failed", "error"))
                    return
                
                self.root.after(0, lambda: self.log("Browser opened...", "info"))
                
                self.screenshot_tool.driver.get('https://drive.google.com/drive/my-drive')
                
                import time
                time.sleep(5)
                
                self.root.after(0, self.show_ready_dialog)
                
                self.user_ready = False
                while not self.user_ready:
                    time.sleep(0.5)
                
                self.root.after(0, lambda: self.log("Starting capture...", "success"))
                
                # HYBRID MODE: Scrape metadata BEFORE screenshots
                if self.mode == "hybrid" and self.file_names:
                    self.root.after(0, lambda: self.log("HYBRID MODE: Scraping metadata from UI...", "info"))
                    
                    self.ui_scraper = DriveUIScraper(self.screenshot_tool.driver)
                    
                    def scrape_callback(progress, file_name):
                        self.root.after(0, lambda p=progress, f=file_name:
                            self.log(f"Scraping {int(p*100)}%: {f}", "info"))
                    
                    self.baseline_metadata = self.ui_scraper.scrape_multiple_files(
                        self.file_names,
                        callback=scrape_callback
                    )
                    
                    # Generate hash from scraped data
                    self.session_baseline_hash = generate_hash_from_scraped_data(self.baseline_metadata)
                    
                    # Save baseline
                    baseline_path = os.path.join(
                        self.export_dir,
                        f'session_{self.current_session}_BASELINE_BEFORE.json'
                    )
                    with open(baseline_path, 'w', encoding='utf-8') as f:
                        json.dump({
                            'session_id': self.current_session,
                            'mode': 'hybrid_ui_scraping',
                            'capture_time': datetime.now().isoformat(),
                            'total_files': len(self.baseline_metadata),
                            'baseline_hash_sha256': self.session_baseline_hash,
                            'files': self.baseline_metadata
                        }, f, indent=2)
                    
                    self.root.after(0, lambda: self.log(f"Scraped {len(self.baseline_metadata)} files", "success"))
                    self.root.after(0, lambda: self.log(f"Baseline hash: {self.session_baseline_hash}", "info"))
                
                # Take screenshots (works for both modes)
                files_to_screenshot = self.files if self.mode == "full" else [{'id': 'unknown', 'name': name} for name in self.file_names]
                
                total = len(files_to_screenshot)
                for i, file in enumerate(files_to_screenshot, 1):
                    progress = i / total
                    self.root.after(0, lambda p=progress: self.progress.set(p))
                    self.root.after(0, lambda i=i, t=total: self.progress_label.configure(text=f"{i}/{t}"))
                    self.root.after(0, lambda f=file: self.log(f"Capturing: {f['name'][:40]}...", "info"))
                    
                    self.screenshot_tool.screenshot_file_details(file.get('id', 'unknown'), file['name'])
                
                self.screenshot_tool.close()
                self.root.after(0, lambda: self.log("Screenshots complete!", "success"))
                self.root.after(0, lambda: self.verify_btn.configure(state="normal"))
                
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error: {e}", "error"))
                import traceback
                traceback.print_exc()
            finally:
                self.root.after(0, lambda: self.screenshot_btn.configure(state="normal"))
                self.root.after(0, lambda: self.progress_label.configure(text=""))
        
        threading.Thread(target=screenshot_thread, daemon=True).start()
    
    def show_ready_dialog(self):
        """Show ready dialog"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Ready?")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        x = (dialog.winfo_screenwidth() // 2) - 200
        y = (dialog.winfo_screenheight() // 2) - 125
        dialog.geometry(f"400x250+{x}+{y}")
        
        ctk.CTkLabel(
            dialog,
            text="Google Drive Loading",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=20)
        
        mode_text = "Log in manually" if self.mode == "hybrid" else "Ensure you're logged in"
        
        ctk.CTkLabel(
            dialog,
            text=f"Please ensure:\n"
                 f"✓ {mode_text}\n"
                 f"✓ Drive has loaded\n"
                 f"✓ You can see your files\n\n"
                 f"Click Ready when done.",
            font=ctk.CTkFont(size=12)
        ).pack(pady=10)
        
        def on_ready():
            self.user_ready = True
            dialog.destroy()
        
        ctk.CTkButton(
            dialog,
            text="I'm Ready",
            command=on_ready,
            height=40
        ).pack(pady=20)
    
    def verify_data(self):
        """Verify integrity (works for both modes)"""
        if not self.current_session:
            messagebox.showerror("Error", "No active session")
            return
        
        self.log(f"Verifying session: {self.current_session}", "info")
        self.verify_btn.configure(state="disabled")
        
        def verify_thread():
            try:
                # Re-capture metadata based on mode
                if self.mode == "full":
                    # API re-capture
                    post_metadata = []
                    for file in self.files:
                        detailed = self.api_tool.service.files().get(
                            fileId=file['id'],
                            fields='id,name,mimeType,createdTime,modifiedTime,viewedByMeTime,size,owners'
                        ).execute()
                        post_metadata.append(detailed)
                    
                    session_post_hash = self.verifier.generate_hash(post_metadata)
                else:
                    # UI scraping re-capture
                    self.root.after(0, lambda: self.log("Re-scraping metadata from UI...", "info"))
                    
                    # Open browser if needed
                    if not self.screenshot_tool or not self.screenshot_tool.driver:
                        self.root.after(0, lambda: self.log("Browser not available for re-scraping", "error"))
                        return
                    
                    self.ui_scraper = DriveUIScraper(self.screenshot_tool.driver)
                    post_metadata = self.ui_scraper.scrape_multiple_files(self.file_names)
                    session_post_hash = generate_hash_from_scraped_data(post_metadata)
                
                # Save post-capture
                post_path = os.path.join(
                    self.export_dir,
                    f'session_{self.current_session}_POST_AFTER.json'
                )
                with open(post_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'session_id': self.current_session,
                        'mode': self.mode,
                        'capture_time': datetime.now().isoformat(),
                        'total_files': len(post_metadata),
                        'post_hash_sha256': session_post_hash,
                        'files': post_metadata
                    }, f, indent=2)
                
                # Verify
                result = self.verifier.verify_no_changes(self.baseline_metadata, post_metadata)
                
                # Save verification
                verification_path = os.path.join(
                    self.export_dir,
                    f'session_{self.current_session}_VERIFICATION.json'
                )
                
                with open(verification_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'session_id': self.current_session,
                        'mode': self.mode,
                        'baseline_hash': self.session_baseline_hash,
                        'post_hash': session_post_hash,
                        'hashes_match': self.session_baseline_hash == session_post_hash,
                        'verification_result': result
                    }, f, indent=2)
                
                # Attestation
                attestation = self.verifier.generate_attestation(result)
                attestation_with_hashes = f"""
SESSION: {self.current_session}
MODE: {self.mode.upper()}

HASH COMPARISON:
  Baseline Hash: {self.session_baseline_hash}
  Post Hash:     {session_post_hash}
  Match:         {self.session_baseline_hash == session_post_hash}

{attestation}
"""
                
                attestation_path = os.path.join(
                    self.export_dir,
                    f'session_{self.current_session}_ATTESTATION.txt'
                )
                with open(attestation_path, 'w', encoding='utf-8') as f:
                    f.write(attestation_with_hashes)
                
                # Results
                self.root.after(0, lambda: self.log(f"Baseline: {self.session_baseline_hash}", "info"))
                self.root.after(0, lambda: self.log(f"Post:     {session_post_hash}", "info"))
                
                if result['match'] and self.session_baseline_hash == session_post_hash:
                    self.root.after(0, lambda: self.log("VERIFICATION PASSED!", "success"))
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Success",
                        f"Integrity verified!\n\n"
                        f"Mode: {self.mode.upper()}\n"
                        f"Files: {len(post_metadata)}\n"
                        f"Hashes match: YES"
                    ))
                else:
                    self.root.after(0, lambda: self.log("VERIFICATION FAILED!", "error"))
                    self.root.after(0, lambda: messagebox.showwarning("Failed", "Hashes don't match!"))
                
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error: {e}", "error"))
                import traceback
                traceback.print_exc()
            finally:
                self.root.after(0, lambda: self.verify_btn.configure(state="normal"))
        
        threading.Thread(target=verify_thread, daemon=True).start()


def main():
    root = ctk.CTk()
    app = MultiModeForensicGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()