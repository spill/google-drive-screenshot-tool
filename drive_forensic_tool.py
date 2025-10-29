#!/usr/bin/env python3
"""
Google Drive Forensic Screenshot Tool - Enhanced Version
Read-only access with comprehensive metadata extraction
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
        
        print("Checking for saved credentials...")
        
        # Check if we have a saved token
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
            print("✓ Found saved token")
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing expired token...")
                creds.refresh(Request())
                print("✓ Token refreshed")
            else:
                if not os.path.exists(self.credentials_file):
                    print(f"ERROR: {self.credentials_file} not found!")
                    print("\nYou need to:")
                    print("1. Go to Google Cloud Console")
                    print("2. Create OAuth 2.0 credentials")
                    print("3. Download as 'credentials.json'")
                    return False
                
                print("Starting OAuth flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
                print("✓ OAuth completed")
            
            # Save credentials for future use
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
            print("✓ Credentials saved")
        
        try:
            self.service = build('drive', 'v3', credentials=creds)
            print("✓ Successfully authenticated with READ-ONLY access")
            return True
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    def get_about_info(self):
        """Get COMPLETE information about the Drive account"""
        if not self.service:
            print("Not authenticated. Run authenticate() first.")
            return None
        
        try:
            print("Fetching COMPLETE Drive account information...")
            
            # Request ALL about fields
            about = self.service.about().get(fields='*').execute()
            
            user_info = about.get('user', {})
            storage = about.get('storageQuota', {})
            
            print(f"✓ User: {user_info.get('emailAddress', 'Unknown')}")
            print(f"✓ Display Name: {user_info.get('displayName', 'Unknown')}")
            
            if storage:
                limit = int(storage.get('limit', 0))
                usage = int(storage.get('usage', 0))
                usage_in_drive = int(storage.get('usageInDrive', 0))
                usage_in_drive_trash = int(storage.get('usageInDriveTrash', 0))
                
                if limit > 0:
                    pct = (usage / limit) * 100
                    print(f"✓ Storage: {self._format_bytes(usage)} / {self._format_bytes(limit)} ({pct:.1f}%)")
                else:
                    print(f"✓ Storage Used: {self._format_bytes(usage)}")
                
                print(f"✓ Drive Storage: {self._format_bytes(usage_in_drive)}")
                print(f"✓ Trash Storage: {self._format_bytes(usage_in_drive_trash)}")
            
            # Additional info
            if 'maxUploadSize' in about:
                print(f"✓ Max Upload Size: {self._format_bytes(int(about['maxUploadSize']))}")
            
            if 'importFormats' in about:
                print(f"✓ Import Formats: {len(about['importFormats'])} types")
            
            if 'exportFormats' in about:
                print(f"✓ Export Formats: {len(about['exportFormats'])} types")
            
            return about
        except HttpError as error:
            print(f"Error fetching about info: {error}")
            return None
    
    def _format_bytes(self, bytes_val):
        """Format bytes to human readable"""
        bytes_val = float(bytes_val)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} PB"
    
    def get_drives_list(self):
        """Get list of all shared drives (Team Drives) user has access to"""
        if not self.service:
            print("Not authenticated. Run authenticate() first.")
            return []
        
        try:
            print("Fetching shared drives...")
            
            drives = self.service.drives().list(
                pageSize=100,
                fields='*'
            ).execute()
            
            drive_list = drives.get('drives', [])
            print(f"✓ Found {len(drive_list)} shared drives")
            
            return drive_list
            
        except HttpError as error:
            print(f"⚠️ Could not fetch shared drives: {error}")
            return []
    
    def list_files(self, query=None, max_results=100):
        """List files with ALL available fields"""
        if not self.service:
            print("Not authenticated. Run authenticate() first.")
            return []
        
        try:
            # Request ALL available fields for comprehensive metadata
            fields = (
                "files(id, name, mimeType, description, starred, trashed, "
                "explicitlyTrashed, parents, properties, appProperties, "
                "spaces, version, webContentLink, webViewLink, iconLink, "
                "hasThumbnail, thumbnailLink, thumbnailVersion, "
                "viewedByMe, viewedByMeTime, createdTime, modifiedTime, "
                "modifiedByMeTime, modifiedByMe, sharedWithMeTime, "
                "sharingUser, owners, teamDriveId, driveId, "
                "lastModifyingUser, shared, ownedByMe, capabilities, "
                "viewersCanCopyContent, copyRequiresWriterPermission, "
                "writersCanShare, permissions, permissionIds, "
                "hasAugmentedPermissions, folderColorRgb, originalFilename, "
                "fullFileExtension, fileExtension, md5Checksum, sha1Checksum, "
                "sha256Checksum, size, quotaBytesUsed, headRevisionId, "
                "contentHints, imageMediaMetadata, videoMediaMetadata, "
                "isAppAuthorized, exportLinks, shortcutDetails, "
                "contentRestrictions, resourceKey, linkShareMetadata, "
                "labelInfo)"
            )
            
            print(f"Querying Drive API (max {max_results} results)...")
            if query:
                print(f"Query: {query}")
            
            results = self.service.files().list(
                q=query,
                pageSize=max_results,
                fields=fields,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            
            files = results.get('files', [])
            print(f"✓ Retrieved {len(files)} files")
            return files
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
    
    def get_file_metadata(self, file_id):
        """Get detailed metadata for a specific file with ALL fields"""
        if not self.service:
            print("Not authenticated. Run authenticate() first.")
            return None
        
        try:
            print(f"Fetching detailed metadata for file {file_id}...")
            
            # Request ALL available fields
            fields = (
                "id, name, mimeType, description, starred, trashed, "
                "explicitlyTrashed, parents, properties, appProperties, "
                "spaces, version, webContentLink, webViewLink, iconLink, "
                "hasThumbnail, thumbnailLink, thumbnailVersion, "
                "viewedByMe, viewedByMeTime, createdTime, modifiedTime, "
                "modifiedByMeTime, modifiedByMe, sharedWithMeTime, "
                "sharingUser, owners, teamDriveId, driveId, "
                "lastModifyingUser, shared, ownedByMe, capabilities, "
                "viewersCanCopyContent, copyRequiresWriterPermission, "
                "writersCanShare, permissions, permissionIds, "
                "hasAugmentedPermissions, folderColorRgb, originalFilename, "
                "fullFileExtension, fileExtension, md5Checksum, sha1Checksum, "
                "sha256Checksum, size, quotaBytesUsed, headRevisionId, "
                "contentHints, imageMediaMetadata, videoMediaMetadata, "
                "isAppAuthorized, exportLinks, shortcutDetails, "
                "contentRestrictions, resourceKey, linkShareMetadata, "
                "labelInfo"
            )
            
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields=fields,
                supportsAllDrives=True
            ).execute()
            
            print(f"✓ Retrieved metadata for: {file_metadata.get('name', 'Unknown')}")
            return file_metadata
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
    
    def get_file_revisions(self, file_id):
        """Get ALL revision history for a file (activity log)"""
        if not self.service:
            print("Not authenticated. Run authenticate() first.")
            return []
        
        try:
            print(f"  Fetching revision history...")
            
            # Request ALL revision fields
            revisions = self.service.revisions().list(
                fileId=file_id,
                fields='*',
                pageSize=1000
            ).execute()
            
            revision_list = revisions.get('revisions', [])
            print(f"  ✓ Found {len(revision_list)} revisions")
            
            return revision_list
            
        except HttpError as error:
            print(f"  ⚠️ Could not fetch revisions: {error}")
            return []
    
    def get_file_comments(self, file_id):
        """Get ALL comments on a file"""
        if not self.service:
            print("Not authenticated. Run authenticate() first.")
            return []
        
        try:
            print(f"  Fetching comments...")
            
            comments = self.service.comments().list(
                fileId=file_id,
                fields='*',
                pageSize=100,
                includeDeleted=False
            ).execute()
            
            comment_list = comments.get('comments', [])
            print(f"  ✓ Found {len(comment_list)} comments")
            
            return comment_list
            
        except HttpError as error:
            print(f"  ⚠️ Could not fetch comments: {error}")
            return []
    
    def get_comprehensive_file_data(self, file_id):
        """
        Get EVERYTHING about a file:
        - Metadata (all fields)
        - Revision history (activity log)
        - Comments (with replies)
        - Permissions (detailed sharing info)
        - Capabilities
        - Labels
        - Properties
        """
        print(f"Getting MAXIMUM comprehensive data for file...")
        
        data = {
            'file_id': file_id,
            'fetch_time': datetime.now().isoformat(),
        }
        
        # Get metadata with EVERY field
        metadata = self.get_file_metadata(file_id)
        if metadata:
            data['metadata'] = metadata
            print(f"  File: {metadata.get('name', 'Unknown')}")
        
        # Get revisions (ACTIVITY LOG)
        revisions = self.get_file_revisions(file_id)
        if revisions:
            data['revisions'] = revisions
            data['revision_count'] = len(revisions)
        
        # Get comments WITH REPLIES
        comments = self.get_file_comments(file_id)
        if comments:
            data['comments'] = comments
            data['comment_count'] = len(comments)
        
        # Get detailed permissions
        permissions = self.get_file_permissions(file_id)
        if permissions:
            data['permissions'] = permissions
            data['permission_count'] = len(permissions)
        
        # Get labels (if any)
        labels = self.get_file_labels(file_id)
        if labels:
            data['labels'] = labels
        
        print(f"✓ MAXIMUM comprehensive data collected")
        return data
    
    def get_file_permissions(self, file_id):
        """Get detailed permissions (who has access and what they can do)"""
        if not self.service:
            print("Not authenticated. Run authenticate() first.")
            return []
        
        try:
            print(f"  Fetching detailed permissions...")
            
            # Request ALL permission fields
            permissions = self.service.permissions().list(
                fileId=file_id,
                fields='*',
                pageSize=100,
                supportsAllDrives=True
            ).execute()
            
            permission_list = permissions.get('permissions', [])
            print(f"  ✓ Found {len(permission_list)} permissions")
            
            return permission_list
            
        except HttpError as error:
            print(f"  ⚠️ Could not fetch permissions: {error}")
            return []
    
    def get_file_labels(self, file_id):
        """Get labels applied to file"""
        if not self.service:
            print("Not authenticated. Run authenticate() first.")
            return {}
        
        try:
            print(f"  Fetching labels...")
            
            # Labels are part of metadata, but let's be explicit
            file_info = self.service.files().get(
                fileId=file_id,
                fields='labelInfo,labels',
                supportsAllDrives=True
            ).execute()
            
            label_info = file_info.get('labelInfo', {})
            labels = file_info.get('labels', {})
            
            if label_info or labels:
                print(f"  ✓ Found label information")
                return {'labelInfo': label_info, 'labels': labels}
            
            return {}
            
        except HttpError as error:
            print(f"  ⚠️ Could not fetch labels: {error}")
            return {}
    
    def find_files_by_date_range(self, start_date, end_date, date_field='modifiedTime'):
        """
        Find files modified/created within a date range
        date_field: 'modifiedTime', 'createdTime', or 'viewedByMeTime'
        """
        query = f"{date_field} >= '{start_date}' and {date_field} <= '{end_date}'"
        print(f"Searching with query: {query}")
        return self.list_files(query=query, max_results=1000)
    
    def export_metadata_report(self, files, output_file='forensic_report.json'):
        """Export file metadata to JSON for documentation"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'tool': 'Drive Forensic Tool (Read-Only)',
            'file_count': len(files),
            'files': files
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
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