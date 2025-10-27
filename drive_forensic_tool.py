#!/usr/bin/env python3
"""
Google Drive Forensic Screenshot Tool
Read-only access to prevent accidental metadata modification
"""

import os
import json
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle

# READ-ONLY scope - prevents any modifications
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class DriveForensicTool:
    def __init__(self, credentials_file='credentials.json'):
        """Initialize the forensic tool with read-only credentials"""
        self.credentials_file = credentials_file
        self.token_file = 'token.pickle'
        self.service = None
        
    def authenticate(self):
        """Authenticate with Google Drive using read-only scope"""
        creds = None
        
        # Check if we have a saved token
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    print(f"ERROR: {self.credentials_file} not found!")
                    print("\nYou need to:")
                    print("1. Go to Google Cloud Console")
                    print("2. Create OAuth 2.0 credentials")
                    print("3. Download as 'credentials.json'")
                    return False
                    
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        try:
            self.service = build('drive', 'v3', credentials=creds)
            print("✓ Successfully authenticated with READ-ONLY access")
            return True
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    def list_files(self, query=None, max_results=100):
        """List files with optional query filter"""
        if not self.service:
            print("Not authenticated. Run authenticate() first.")
            return []
        
        try:
            results = self.service.files().list(
                q=query,
                pageSize=max_results,
                fields="files(id, name, mimeType, createdTime, modifiedTime, viewedByMeTime, owners, size)"
            ).execute()
            
            files = results.get('files', [])
            return files
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
    
    def get_file_metadata(self, file_id):
        """Get detailed metadata for a specific file"""
        if not self.service:
            print("Not authenticated. Run authenticate() first.")
            return None
        
        try:
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, createdTime, modifiedTime, viewedByMeTime, "
                       "lastModifyingUser, owners, size, webViewLink, webContentLink, "
                       "permissions, parents, shared"
            ).execute()
            
            return file_metadata
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
    
    def find_files_by_date_range(self, start_date, end_date, date_field='modifiedTime'):
        """
        Find files modified/created within a date range
        date_field: 'modifiedTime', 'createdTime', or 'viewedByMeTime'
        """
        query = f"{date_field} >= '{start_date}' and {date_field} <= '{end_date}'"
        print(f"Searching with query: {query}")
        return self.list_files(query=query)
    
    def export_metadata_report(self, files, output_file='forensic_report.json'):
        """Export file metadata to JSON for documentation"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'tool': 'Drive Forensic Tool (Read-Only)',
            'file_count': len(files),
            'files': files
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"✓ Exported metadata report to {output_file}")
        return output_file
    
    def test_read_only_restriction(self):
        """Test that we cannot modify files (should fail)"""
        print("\n=== Testing Read-Only Restriction ===")
        print("Attempting to create a file (this should FAIL)...")
        
        try:
            file_metadata = {'name': 'test_file.txt', 'mimeType': 'text/plain'}
            self.service.files().create(body=file_metadata).execute()
            print("❌ WARNING: File creation succeeded! Scope may not be read-only!")
            return False
        except HttpError as error:
            if 'insufficient authentication scopes' in str(error).lower():
                print("✓ GOOD: Cannot create files (read-only confirmed)")
                return True
            else:
                print(f"Unexpected error: {error}")
                return False


def main():
    """Main function to demonstrate the tool"""
    print("=" * 60)
    print("Google Drive Forensic Tool - Read Only Mode")
    print("=" * 60)
    
    tool = DriveForensicTool()
    
    # Authenticate
    print("\n[1] Authenticating...")
    if not tool.authenticate():
        return
    
    # Test read-only restriction
    tool.test_read_only_restriction()
    
    # List recent files
    print("\n[2] Listing recent files...")
    files = tool.list_files(max_results=10)
    
    if not files:
        print("No files found or no access to any files.")
    else:
        print(f"\nFound {len(files)} files:")
        print("-" * 60)
        for i, file in enumerate(files, 1):
            print(f"{i}. {file['name']}")
            print(f"   ID: {file['id']}")
            print(f"   Modified: {file.get('modifiedTime', 'N/A')}")
            print(f"   Created: {file.get('createdTime', 'N/A')}")
            print()
        
        # Export metadata
        print("\n[3] Exporting metadata report...")
        tool.export_metadata_report(files)
    
    # Example: Search by date range
    print("\n[4] Example: Searching files modified in 2024...")
    files_2024 = tool.find_files_by_date_range('2024-01-01T00:00:00', '2024-12-31T23:59:59')
    print(f"Found {len(files_2024)} files modified in 2024")
    
    print("\n" + "=" * 60)
    print("✓ Forensic scan complete - No modifications made to Drive")
    print("=" * 60)


if __name__ == '__main__':
    main()