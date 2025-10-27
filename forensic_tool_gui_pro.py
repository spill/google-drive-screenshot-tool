#!/usr/bin/env python3
"""
Google Drive File Documentation Tool - Clean GUI
Simple, functional interface with all the features
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


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ForensicToolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Drive File Documentation Tool")
        self.root.geometry("1000x700")
        
        # Tools
        self.api_tool = None
        self.screenshot_tool = None
        self.verifier = ForensicVerifier()
        self.files = []
        self.authenticated = False
        self.baseline_metadata = []
        
        # Session tracking
        self.current_session = None
        self.session_baseline_hash = None
        
        # Create output directories
        self.screenshot_dir = 'GoogleDrive_Screenshots'
        self.export_dir = 'GoogleDrive_Exports'
        os.makedirs(self.screenshot_dir, exist_ok=True)
        os.makedirs(self.export_dir, exist_ok=True)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup simple, clean UI"""
        
        # Main container
        main = ctk.CTkFrame(self.root)
        main.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        ctk.CTkLabel(
            main,
            text="Google Drive File Documentation Tool",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=10)
        
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
        
        # Step 1: Authentication
        ctk.CTkLabel(
            scroll,
            text="1. Authentication",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        self.auth_btn = ctk.CTkButton(
            scroll,
            text="Authenticate with Google",
            command=self.authenticate,
            height=40
        )
        self.auth_btn.pack(fill="x", pady=5)
        
        self.auth_status = ctk.CTkLabel(scroll, text="Not authenticated", text_color="gray")
        self.auth_status.pack(anchor="w", pady=(0, 10))
        
        # Separator
        ctk.CTkFrame(scroll, height=2, fg_color="gray").pack(fill="x", pady=10)
        
        # Step 2: Search
        ctk.CTkLabel(
            scroll,
            text="2. File Search",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        self.search_type = ctk.StringVar(value="all")
        
        ctk.CTkRadioButton(scroll, text="All files", variable=self.search_type, value="all").pack(anchor="w", pady=2)
        
        # Max results for "All files"
        max_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        max_frame.pack(fill="x", padx=20, pady=2)
        
        ctk.CTkLabel(max_frame, text="Max results:").pack(side="left", padx=(0, 5))
        self.max_results = ctk.CTkComboBox(
            max_frame,
            values=["10", "20", "50", "100", "500", "1000"],
            width=100
        )
        self.max_results.set("20")
        self.max_results.pack(side="left")
        
        ctk.CTkRadioButton(scroll, text="Date range", variable=self.search_type, value="date").pack(anchor="w", pady=2)
        
        date_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        date_frame.pack(fill="x", padx=20, pady=2)
        
        ctk.CTkLabel(date_frame, text="Start:").pack(side="left")
        self.start_date = ctk.CTkEntry(date_frame, width=100, placeholder_text="2024-01-01")
        self.start_date.pack(side="left", padx=5)
        
        ctk.CTkLabel(date_frame, text="End:").pack(side="left", padx=(10, 0))
        self.end_date = ctk.CTkEntry(date_frame, width=100, placeholder_text="2024-12-31")
        self.end_date.pack(side="left", padx=5)
        
        ctk.CTkRadioButton(scroll, text="Search by name", variable=self.search_type, value="name").pack(anchor="w", pady=2)
        
        self.search_name = ctk.CTkEntry(scroll, placeholder_text="Enter file name")
        self.search_name.pack(fill="x", padx=20, pady=2)
        
        ctk.CTkRadioButton(scroll, text="Multiple files (fuzzy match)", variable=self.search_type, value="multi").pack(anchor="w", pady=2)
        
        self.multi_names = ctk.CTkTextbox(scroll, height=100)
        self.multi_names.pack(fill="x", padx=20, pady=2)
        
        ctk.CTkButton(
            scroll,
            text="Load from file",
            command=self.load_file_list,
            height=28,
            fg_color="gray"
        ).pack(fill="x", padx=20, pady=2)
        
        self.search_btn = ctk.CTkButton(
            scroll,
            text="Search Files",
            command=self.search_files,
            height=40,
            state="disabled"
        )
        self.search_btn.pack(fill="x", pady=10)
        
        # Separator
        ctk.CTkFrame(scroll, height=2, fg_color="gray").pack(fill="x", pady=10)
        
        # Step 3: Screenshots
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
        
        # Step 4: Verify
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
        
        self.log("Ready to begin", "info")
        
    def log(self, message, level="info"):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        icons = {"info": "ℹ️", "success": "✓", "warning": "⚠️", "error": "✗"}
        icon = icons.get(level, "ℹ️")
        
        formatted = f"[{timestamp}] {icon} {message}\n"
        self.log_text.insert("end", formatted)
        self.log_text.see("end")
        self.root.update()
    
    def fuzzy_match(self, search_name, file_name, threshold=0.6):
        """Fuzzy match file names"""
        search_lower = search_name.lower().strip()
        file_lower = file_name.lower().strip()
        
        if search_lower == file_lower:
            return 1.0
        if search_lower in file_lower:
            return 0.9
        return SequenceMatcher(None, search_lower, file_lower).ratio()
    
    def search_multi_files(self, search_names):
        """Search for multiple files with fuzzy matching"""
        self.log(f"Searching for {len(search_names)} files...")
        
        all_files = self.api_tool.list_files(max_results=1000)
        matched_files = []
        
        for search_name in search_names:
            best_match = None
            best_score = 0
            
            for file in all_files:
                score = self.fuzzy_match(search_name, file['name'])
                if score > best_score:
                    best_score = score
                    best_match = file
            
            if best_match and best_score >= 0.6:
                matched_files.append(best_match)
                
                if best_score == 1.0:
                    self.log(f"  Exact: '{search_name}' -> {best_match['name']}", "success")
                elif best_score >= 0.9:
                    self.log(f"  Strong: '{search_name}' -> {best_match['name']}", "success")
                else:
                    self.log(f"  Fuzzy ({int(best_score*100)}%): '{search_name}' -> {best_match['name']}", "warning")
            else:
                self.log(f"  Not found: '{search_name}'", "error")
        
        return matched_files
    
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
        """Authenticate with Google"""
        self.log("Authenticating...")
        self.auth_btn.configure(state="disabled")
        
        def auth_thread():
            try:
                self.api_tool = DriveForensicTool()
                if self.api_tool.authenticate():
                    self.authenticated = True
                    self.root.after(0, lambda: self.log("Authenticated successfully", "success"))
                    self.root.after(0, lambda: self.auth_status.configure(text="✓ Authenticated", text_color="green"))
                    self.root.after(0, lambda: self.search_btn.configure(state="normal"))
                    
                    if self.api_tool.test_read_only_restriction():
                        self.root.after(0, lambda: self.log("Read-only access confirmed", "success"))
                else:
                    self.root.after(0, lambda: self.log("Authentication failed", "error"))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error: {e}", "error"))
            finally:
                self.root.after(0, lambda: self.auth_btn.configure(state="normal"))
        
        threading.Thread(target=auth_thread, daemon=True).start()
    
    def search_files(self):
        """Search for files"""
        if not self.authenticated:
            messagebox.showerror("Error", "Authenticate first")
            return
        
        self.log("Searching...")
        self.search_btn.configure(state="disabled")
        
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
                    
                elif search_type == "name":
                    name = self.search_name.get()
                    if not name:
                        self.root.after(0, lambda: messagebox.showerror("Error", "Enter a file name"))
                        return
                    query = f"name contains '{name}'"
                    files = self.api_tool.list_files(query=query)
                    
                elif search_type == "multi":
                    names_text = self.multi_names.get("1.0", "end").strip()
                    if not names_text:
                        self.root.after(0, lambda: messagebox.showerror("Error", "Enter file names"))
                        return
                    
                    search_names = [n.strip() for n in names_text.split('\n') if n.strip()]
                    files = self.search_multi_files(search_names)
                else:
                    files = []
                
                self.files = files
                
                if files:
                    # Create new session ID
                    self.current_session = datetime.now().strftime('%Y%m%d_%H%M%S')
                    
                    self.log(f"Session ID: {self.current_session}", "info")
                    
                    # Capture baseline
                    self.baseline_metadata = []
                    for file in files:
                        detailed = self.api_tool.service.files().get(
                            fileId=file['id'],
                            fields='id,name,mimeType,createdTime,modifiedTime,viewedByMeTime,size,owners'
                        ).execute()
                        self.baseline_metadata.append(detailed)
                    
                    # Generate hash BEFORE saving
                    self.session_baseline_hash = self.verifier.generate_hash(self.baseline_metadata)
                    
                    # Save with session ID and hash
                    baseline_path = os.path.join(
                        self.export_dir, 
                        f'session_{self.current_session}_BASELINE_BEFORE.json'
                    )
                    with open(baseline_path, 'w', encoding='utf-8') as f:
                        json.dump({
                            'session_id': self.current_session,
                            'capture_time': datetime.now().isoformat(),
                            'total_files': len(self.baseline_metadata),
                            'baseline_hash_sha256': self.session_baseline_hash,
                            'search_type': search_type,
                            'files': self.baseline_metadata
                        }, f, indent=2)
                    
                    self.root.after(0, lambda: self.log(f"Found {len(files)} files", "success"))
                    self.root.after(0, lambda: self.log(f"Baseline hash: {self.session_baseline_hash}", "info"))
                    self.root.after(0, lambda: self.log(f"Saved: session_{self.current_session}_BASELINE_BEFORE.json", "success"))
                    
                    # Display found files
                    self.root.after(0, lambda: self.log("--- Files Found ---", "info"))
                    for i, f in enumerate(files[:10], 1):  # Show first 10
                        file_name = f['name']
                        modified = f.get('modifiedTime', 'N/A')
                        self.root.after(0, lambda i=i, name=file_name, mod=modified: 
                            self.log(f"  {i}. {name} (Modified: {mod})", "info"))
                    
                    if len(files) > 10:
                        remaining = len(files) - 10
                        self.root.after(0, lambda r=remaining: self.log(f"  ... and {r} more files", "info"))
                    
                    self.root.after(0, lambda: self.log("-------------------", "info"))
                    self.root.after(0, lambda: self.screenshot_btn.configure(state="normal"))
                else:
                    self.root.after(0, lambda: self.log("No files found", "warning"))
                    
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error: {e}", "error"))
            finally:
                self.root.after(0, lambda: self.search_btn.configure(state="normal"))
        
        threading.Thread(target=search_thread, daemon=True).start()
    
    def start_screenshots(self):
        """Start screenshot capture"""
        if not self.files:
            messagebox.showerror("Error", "No files to capture")
            return
        
        use_profile = self.use_profile.get()
        
        if use_profile:
            response = messagebox.askyesno(
                "Chrome Profile",
                "Close ALL Chrome windows now.\n\nClick Yes when ready."
            )
            if not response:
                return
        
        self.log("Starting screenshots...")
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
                
                total = len(self.files)
                for i, file in enumerate(self.files, 1):
                    progress = i / total
                    self.root.after(0, lambda p=progress: self.progress.set(p))
                    self.root.after(0, lambda i=i, t=total: self.progress_label.configure(text=f"{i}/{t}"))
                    self.root.after(0, lambda f=file: self.log(f"Capturing: {f['name'][:40]}...", "info"))
                    
                    self.screenshot_tool.screenshot_file_details(file['id'], file['name'])
                
                self.screenshot_tool.close()
                self.root.after(0, lambda: self.log("Screenshots complete!", "success"))
                self.root.after(0, lambda: self.verify_btn.configure(state="normal"))
                
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error: {e}", "error"))
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
        
        ctk.CTkLabel(
            dialog,
            text="Please ensure:\n"
                 "✓ Logged in to Google\n"
                 "✓ Drive has loaded\n"
                 "✓ You can see your files\n\n"
                 "Click Ready when done.",
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
        """Verify integrity"""
        
        if not self.current_session:
            messagebox.showerror("Error", "No active session to verify")
            return
        
        self.log("Verifying...", "info")
        self.log(f"Verifying session: {self.current_session}", "info")
        self.verify_btn.configure(state="disabled")
        
        def verify_thread():
            try:
                # Re-capture metadata
                post_metadata = []
                for file in self.files:
                    detailed = self.api_tool.service.files().get(
                        fileId=file['id'],
                        fields='id,name,mimeType,createdTime,modifiedTime,viewedByMeTime,size,owners'
                    ).execute()
                    post_metadata.append(detailed)
                
                # Generate post-capture hash
                session_post_hash = self.verifier.generate_hash(post_metadata)
                
                # Save post-capture with session ID and hash
                post_path = os.path.join(
                    self.export_dir, 
                    f'session_{self.current_session}_POST_AFTER.json'
                )
                with open(post_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'session_id': self.current_session,
                        'capture_time': datetime.now().isoformat(),
                        'total_files': len(post_metadata),
                        'post_hash_sha256': session_post_hash,
                        'files': post_metadata
                    }, f, indent=2)
                
                # Verify hashes
                result = self.verifier.verify_no_changes(self.baseline_metadata, post_metadata)
                
                # Save verification report with session ID
                verification_path = os.path.join(
                    self.export_dir, 
                    f'session_{self.current_session}_VERIFICATION.json'
                )
                
                # Add hash comparison to verification report
                verification_report = {
                    'session_id': self.current_session,
                    'verification_time': datetime.now().isoformat(),
                    'baseline_hash': self.session_baseline_hash,
                    'post_hash': session_post_hash,
                    'hashes_match': self.session_baseline_hash == session_post_hash,
                    'total_files': len(self.files),
                    'verification_result': result
                }
                
                with open(verification_path, 'w', encoding='utf-8') as f:
                    json.dump(verification_report, f, indent=2)
                
                # Generate attestation
                attestation = self.verifier.generate_attestation(result)
                
                # Add hash info to attestation
                attestation_with_hashes = f"""
SESSION: {self.current_session}

HASH COMPARISON:
  Baseline Hash (BEFORE): {self.session_baseline_hash}
  Post Hash (AFTER):      {session_post_hash}
  Hashes Match:           {self.session_baseline_hash == session_post_hash}

{attestation}
"""
                
                attestation_path = os.path.join(
                    self.export_dir, 
                    f'session_{self.current_session}_ATTESTATION.txt'
                )
                with open(attestation_path, 'w', encoding='utf-8') as f:
                    f.write(attestation_with_hashes)
                
                # Log results
                self.root.after(0, lambda: self.log(f"Baseline hash: {self.session_baseline_hash}", "info"))
                self.root.after(0, lambda: self.log(f"Post hash:     {session_post_hash}", "info"))
                
                if result['match'] and self.session_baseline_hash == session_post_hash:
                    self.root.after(0, lambda: self.log("VERIFICATION PASSED - Hashes match!", "success"))
                    self.root.after(0, lambda: self.log(f"Saved: session_{self.current_session}_VERIFICATION.json", "success"))
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Success",
                        f"Data integrity verified!\n\n"
                        f"Session: {self.current_session}\n"
                        f"Files: {len(self.files)}\n"
                        f"Hash verification: PASSED\n\n"
                        f"Baseline hash matches post-capture hash."
                    ))
                else:
                    self.root.after(0, lambda: self.log("VERIFICATION FAILED - Hashes DO NOT match!", "error"))
                    self.root.after(0, lambda: messagebox.showwarning(
                        "Failed",
                        f"Hash verification FAILED\n\n"
                        f"Session: {self.current_session}\n"
                        f"See verification report for details."
                    ))
                
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error: {e}", "error"))
            finally:
                self.root.after(0, lambda: self.verify_btn.configure(state="normal"))
        
        threading.Thread(target=verify_thread, daemon=True).start()


def main():
    root = ctk.CTk()
    app = ForensicToolGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()