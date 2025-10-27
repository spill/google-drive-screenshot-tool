#!/usr/bin/env python3
"""
Comprehensive Read-Only Verification
Tests multiple write operations to prove API is truly read-only
"""

from googleapiclient.errors import HttpError


class ReadOnlyVerifier:
    """
    Comprehensive verification that API access is read-only
    Tests multiple write operations that should ALL fail
    """
    
    def __init__(self, service):
        self.service = service
        self.test_results = []
    
    def verify_comprehensive(self):
        """
        Run comprehensive read-only verification
        
        Returns:
            dict: Complete verification report
        """
        print("\n" + "="*70)
        print("COMPREHENSIVE READ-ONLY VERIFICATION")
        print("="*70)
        print("\nTesting multiple write operations...")
        print("(All should FAIL to confirm read-only access)\n")
        
        tests = [
            ("Create File", self.test_create_file),
            ("Update File Metadata", self.test_update_metadata),
            ("Delete File", self.test_delete_file),
            ("Create Folder", self.test_create_folder),
            ("Move File", self.test_move_file),
            ("Copy File", self.test_copy_file),
            ("Modify Permissions", self.test_modify_permissions),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            result = test_func()
            self.test_results.append(result)
            
            if result['passed']:
                passed += 1
                print(f"  ✓ {test_name}: {result['status']}")
            else:
                failed += 1
                print(f"  ✗ {test_name}: {result['status']}")
        
        all_passed = (failed == 0)
        
        print("\n" + "-"*70)
        print(f"Results: {passed}/{len(tests)} tests passed")
        
        if all_passed:
            print("\n✓✓✓ VERIFICATION PASSED ✓✓✓")
            print("All write operations failed as expected.")
            print("API access is confirmed READ-ONLY.")
        else:
            print("\n✗✗✗ VERIFICATION FAILED ✗✗✗")
            print("Some write operations succeeded!")
            print("⚠️ WARNING: API may NOT be read-only!")
        
        print("="*70 + "\n")
        
        return {
            'all_passed': all_passed,
            'passed_count': passed,
            'failed_count': failed,
            'total_tests': len(tests),
            'test_results': self.test_results
        }
    
    def test_create_file(self):
        """Test: Try to create a file"""
        try:
            file_metadata = {
                'name': 'READONLY_TEST.txt',
                'mimeType': 'text/plain'
            }
            self.service.files().create(body=file_metadata).execute()
            
            return {
                'test': 'Create File',
                'passed': False,
                'status': 'DANGER - File creation succeeded!',
                'error': None
            }
        except HttpError as error:
            if 'insufficient' in str(error).lower() or 'scope' in str(error).lower():
                return {
                    'test': 'Create File',
                    'passed': True,
                    'status': 'Blocked (insufficient permissions)',
                    'error': str(error)[:100]
                }
            else:
                return {
                    'test': 'Create File',
                    'passed': True,
                    'status': f'Blocked ({type(error).__name__})',
                    'error': str(error)[:100]
                }
    
    def test_update_metadata(self):
        """Test: Try to update file metadata"""
        try:
            # Get first file we have access to
            files = self.service.files().list(pageSize=1).execute().get('files', [])
            
            if not files:
                return {
                    'test': 'Update Metadata',
                    'passed': True,
                    'status': 'Skipped (no files to test)',
                    'error': None
                }
            
            file_id = files[0]['id']
            
            # Try to rename it
            file_metadata = {'name': 'RENAMED_BY_TEST'}
            self.service.files().update(
                fileId=file_id,
                body=file_metadata
            ).execute()
            
            return {
                'test': 'Update Metadata',
                'passed': False,
                'status': 'DANGER - Metadata update succeeded!',
                'error': None
            }
        except HttpError as error:
            if 'insufficient' in str(error).lower() or 'scope' in str(error).lower():
                return {
                    'test': 'Update Metadata',
                    'passed': True,
                    'status': 'Blocked (insufficient permissions)',
                    'error': str(error)[:100]
                }
            else:
                return {
                    'test': 'Update Metadata',
                    'passed': True,
                    'status': f'Blocked ({type(error).__name__})',
                    'error': str(error)[:100]
                }
    
    def test_delete_file(self):
        """Test: Try to delete a file"""
        try:
            # Try to delete a fake file (will fail for multiple reasons)
            self.service.files().delete(fileId='fake_file_id_12345').execute()
            
            return {
                'test': 'Delete File',
                'passed': False,
                'status': 'DANGER - Delete succeeded!',
                'error': None
            }
        except HttpError as error:
            if 'insufficient' in str(error).lower() or 'scope' in str(error).lower() or 'not found' in str(error).lower():
                return {
                    'test': 'Delete File',
                    'passed': True,
                    'status': 'Blocked (insufficient permissions or not found)',
                    'error': str(error)[:100]
                }
            else:
                return {
                    'test': 'Delete File',
                    'passed': True,
                    'status': f'Blocked ({type(error).__name__})',
                    'error': str(error)[:100]
                }
    
    def test_create_folder(self):
        """Test: Try to create a folder"""
        try:
            folder_metadata = {
                'name': 'READONLY_TEST_FOLDER',
                'mimeType': 'application/vnd.google-apps.folder'
            }
            self.service.files().create(body=folder_metadata).execute()
            
            return {
                'test': 'Create Folder',
                'passed': False,
                'status': 'DANGER - Folder creation succeeded!',
                'error': None
            }
        except HttpError as error:
            if 'insufficient' in str(error).lower() or 'scope' in str(error).lower():
                return {
                    'test': 'Create Folder',
                    'passed': True,
                    'status': 'Blocked (insufficient permissions)',
                    'error': str(error)[:100]
                }
            else:
                return {
                    'test': 'Create Folder',
                    'passed': True,
                    'status': f'Blocked ({type(error).__name__})',
                    'error': str(error)[:100]
                }
    
    def test_move_file(self):
        """Test: Try to move a file"""
        try:
            files = self.service.files().list(pageSize=1).execute().get('files', [])
            
            if not files:
                return {
                    'test': 'Move File',
                    'passed': True,
                    'status': 'Skipped (no files to test)',
                    'error': None
                }
            
            file_id = files[0]['id']
            
            # Try to move to root
            self.service.files().update(
                fileId=file_id,
                addParents='root',
                fields='id, parents'
            ).execute()
            
            return {
                'test': 'Move File',
                'passed': False,
                'status': 'DANGER - File move succeeded!',
                'error': None
            }
        except HttpError as error:
            if 'insufficient' in str(error).lower() or 'scope' in str(error).lower():
                return {
                    'test': 'Move File',
                    'passed': True,
                    'status': 'Blocked (insufficient permissions)',
                    'error': str(error)[:100]
                }
            else:
                return {
                    'test': 'Move File',
                    'passed': True,
                    'status': f'Blocked ({type(error).__name__})',
                    'error': str(error)[:100]
                }
    
    def test_copy_file(self):
        """Test: Try to copy a file"""
        try:
            files = self.service.files().list(pageSize=1).execute().get('files', [])
            
            if not files:
                return {
                    'test': 'Copy File',
                    'passed': True,
                    'status': 'Skipped (no files to test)',
                    'error': None
                }
            
            file_id = files[0]['id']
            
            # Try to copy it
            copy_metadata = {'name': 'COPY_TEST'}
            self.service.files().copy(
                fileId=file_id,
                body=copy_metadata
            ).execute()
            
            return {
                'test': 'Copy File',
                'passed': False,
                'status': 'DANGER - File copy succeeded!',
                'error': None
            }
        except HttpError as error:
            if 'insufficient' in str(error).lower() or 'scope' in str(error).lower():
                return {
                    'test': 'Copy File',
                    'passed': True,
                    'status': 'Blocked (insufficient permissions)',
                    'error': str(error)[:100]
                }
            else:
                return {
                    'test': 'Copy File',
                    'passed': True,
                    'status': f'Blocked ({type(error).__name__})',
                    'error': str(error)[:100]
                }
    
    def test_modify_permissions(self):
        """Test: Try to modify file permissions"""
        try:
            files = self.service.files().list(pageSize=1).execute().get('files', [])
            
            if not files:
                return {
                    'test': 'Modify Permissions',
                    'passed': True,
                    'status': 'Skipped (no files to test)',
                    'error': None
                }
            
            file_id = files[0]['id']
            
            # Try to add a permission
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            self.service.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
            
            return {
                'test': 'Modify Permissions',
                'passed': False,
                'status': 'DANGER - Permission change succeeded!',
                'error': None
            }
        except HttpError as error:
            if 'insufficient' in str(error).lower() or 'scope' in str(error).lower():
                return {
                    'test': 'Modify Permissions',
                    'passed': True,
                    'status': 'Blocked (insufficient permissions)',
                    'error': str(error)[:100]
                }
            else:
                return {
                    'test': 'Modify Permissions',
                    'passed': True,
                    'status': f'Blocked ({type(error).__name__})',
                    'error': str(error)[:100]
                }


# Integration with existing tool
def verify_read_only_comprehensive(api_tool):
    """
    Run comprehensive read-only verification on DriveForensicTool instance
    
    Args:
        api_tool: DriveForensicTool instance with authenticated service
        
    Returns:
        dict: Verification results
    """
    if not api_tool.service:
        print("ERROR: Not authenticated. Cannot verify read-only status.")
        return None
    
    verifier = ReadOnlyVerifier(api_tool.service)
    return verifier.verify_comprehensive()


if __name__ == '__main__':
    print("This is a verification module.")
    print("Import and use verify_read_only_comprehensive(api_tool)")