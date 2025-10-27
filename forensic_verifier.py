#!/usr/bin/env python3
"""
Forensic Verification Module
Generates cryptographic hashes to prove no metadata modifications occurred
"""

import json
import hashlib
from datetime import datetime


class ForensicVerifier:
    """
    Cryptographic verification of metadata integrity
    Proves that screenshot process did not modify file timestamps
    """
    
    def __init__(self):
        self.verification_log = []
    
    def generate_hash(self, metadata):
        """
        Generate SHA-256 hash of metadata
        
        Args:
            metadata: Dictionary or list of file metadata
            
        Returns:
            str: SHA-256 hex digest
        """
        # Convert to JSON string (sorted keys for consistency)
        json_str = json.dumps(metadata, sort_keys=True)
        
        # Generate SHA-256 hash
        hash_obj = hashlib.sha256(json_str.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def generate_file_hash(self, file_metadata):
        """
        Generate hash of critical timestamps for a single file
        
        Critical fields:
        - createdTime
        - modifiedTime  
        - viewedByMeTime (Last Opened)
        """
        critical_data = {
            'id': file_metadata.get('id'),
            'name': file_metadata.get('name'),
            'createdTime': file_metadata.get('createdTime'),
            'modifiedTime': file_metadata.get('modifiedTime'),
            'viewedByMeTime': file_metadata.get('viewedByMeTime')
        }
        
        return self.generate_hash(critical_data)
    
    def verify_no_changes(self, before_metadata, after_metadata):
        """
        Compare before and after metadata
        
        Returns:
            dict: Verification result with details
        """
        before_hash = self.generate_hash(before_metadata)
        after_hash = self.generate_hash(after_metadata)
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'before_hash': before_hash,
            'after_hash': after_hash,
            'match': before_hash == after_hash,
            'total_files': len(before_metadata) if isinstance(before_metadata, list) else 1
        }
        
        # Detailed comparison for each file
        if isinstance(before_metadata, list) and isinstance(after_metadata, list):
            result['file_details'] = []
            
            for before_file, after_file in zip(before_metadata, after_metadata):
                file_result = self.verify_file(before_file, after_file)
                result['file_details'].append(file_result)
                
                if not file_result['timestamps_match']:
                    result['violations'] = result.get('violations', [])
                    result['violations'].append(file_result)
        
        self.verification_log.append(result)
        return result
    
    def verify_file(self, before_file, after_file):
        """
        Verify a single file's metadata hasn't changed
        
        Returns:
            dict: File-specific verification
        """
        file_id = before_file.get('id')
        file_name = before_file.get('name')
        
        # Critical timestamps
        before_timestamps = {
            'created': before_file.get('createdTime'),
            'modified': before_file.get('modifiedTime'),
            'viewed': before_file.get('viewedByMeTime')
        }
        
        after_timestamps = {
            'created': after_file.get('createdTime'),
            'modified': after_file.get('modifiedTime'),
            'viewed': after_file.get('viewedByMeTime')
        }
        
        # Check for changes
        changes = {}
        for key in before_timestamps:
            if before_timestamps[key] != after_timestamps[key]:
                changes[key] = {
                    'before': before_timestamps[key],
                    'after': after_timestamps[key]
                }
        
        return {
            'file_id': file_id,
            'file_name': file_name,
            'before_hash': self.generate_file_hash(before_file),
            'after_hash': self.generate_file_hash(after_file),
            'timestamps_match': len(changes) == 0,
            'changes': changes if changes else None
        }
    
    def export_verification_report(self, filename='forensic_verification.json'):
        """
        Export complete verification report
        
        This serves as cryptographic proof that no modifications occurred
        """
        report = {
            'verification_timestamp': datetime.now().isoformat(),
            'verifier_version': '1.0',
            'hash_algorithm': 'SHA-256',
            'verification_count': len(self.verification_log),
            'verifications': self.verification_log
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        return filename
    
    def generate_attestation(self, verification_result):
        """
        Generate a formal attestation statement
        
        Returns:
            str: Formatted attestation for legal use
        """
        if verification_result['match']:
            attestation = f"""
FORENSIC INTEGRITY ATTESTATION
{'='*70}

Verification Timestamp: {verification_result['timestamp']}
Total Files Examined: {verification_result['total_files']}

METADATA HASH VERIFICATION:
  Before Hash (SHA-256): {verification_result['before_hash']}
  After Hash (SHA-256):  {verification_result['after_hash']}
  
RESULT: [PASS] HASHES MATCH

ATTESTATION:
I hereby attest that cryptographic hash verification confirms no 
modifications were made to file metadata during the screenshot capture 
process. The SHA-256 hashes of all file metadata remained identical 
before and after the documentation process.

This verification proves that critical forensic timestamps including:
- Created Time
- Modified Time  
- Viewed By Me Time (Last Opened)

remained unaltered during evidence collection.

{'='*70}
"""
        else:
            violations = verification_result.get('violations', [])
            violation_details = "\n".join([
                f"  - {v['file_name']}: {v['changes']}"
                for v in violations
            ])
            
            attestation = f"""
FORENSIC INTEGRITY VIOLATION
{'='*70}

Verification Timestamp: {verification_result['timestamp']}
Total Files Examined: {verification_result['total_files']}

METADATA HASH VERIFICATION:
  Before Hash (SHA-256): {verification_result['before_hash']}
  After Hash (SHA-256):  {verification_result['after_hash']}
  
RESULT: [FAIL] HASHES DO NOT MATCH

WARNING: TIMESTAMP MODIFICATIONS DETECTED

The following files had timestamp changes:
{violation_details}

This indicates that the documentation process may have altered 
forensic evidence. Manual review and remediation required.

{'='*70}
"""
        
        return attestation


def print_verification_summary(result):
    """
    Print human-readable verification summary
    """
    print("\n" + "="*70)
    print("FORENSIC VERIFICATION RESULTS")
    print("="*70)
    
    print(f"\nVerification Time: {result['timestamp']}")
    print(f"Total Files: {result['total_files']}")
    print(f"\nBefore Hash: {result['before_hash']}")
    print(f"After Hash:  {result['after_hash']}")
    
    if result['match']:
        print("\n✓✓✓ VERIFICATION PASSED ✓✓✓")
        print("\nHashes match - No modifications detected")
        print("All timestamps remained unchanged during screenshot process")
        print("\nForensic integrity: CONFIRMED")
    else:
        print("\n✗✗✗ VERIFICATION FAILED ✗✗✗")
        print("\nHashes do NOT match - Modifications detected!")
        
        if 'violations' in result:
            print(f"\n⚠️ {len(result['violations'])} file(s) had timestamp changes:")
            for v in result['violations']:
                print(f"\n  File: {v['file_name']}")
                for change_type, change_data in v['changes'].items():
                    print(f"    {change_type}:")
                    print(f"      Before: {change_data['before']}")
                    print(f"      After:  {change_data['after']}")
        
        print("\nForensic integrity: COMPROMISED")
        print("Manual review required")
    
    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    # Example usage
    print("Forensic Verification Module")
    print("This module provides cryptographic proof of metadata integrity")
    print("\nImport this in forensic_workflow.py for verification")