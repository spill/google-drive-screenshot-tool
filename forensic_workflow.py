#!/usr/bin/env python3
"""
Google Drive Comprehensive Forensic Workflow - Enhanced Version
Command-line interface for extracting ALL metadata from Google Drive API
"""

import sys
import json
from datetime import datetime
from drive_forensic_tool_enhanced import DriveForensicToolEnhanced
from forensic_verifier import ForensicVerifier


def forensic_workflow_enhanced():
    """
    Complete forensic workflow with comprehensive API data extraction:
    1. Authenticate (read-only)
    2. Get account information
    3. Search for files
    4. Extract ALL metadata (files + revisions + comments)
    5. Verify integrity
    """
    print("=" * 70)
    print("GOOGLE DRIVE COMPREHENSIVE FORENSIC WORKFLOW")
    print("Extracts ALL metadata via API (read-only)")
    print("=" * 70)
    
    # Initialize tools
    api_tool = DriveForensicToolEnhanced()
    verifier = ForensicVerifier()
    
    # ========================================
    # PHASE 1: AUTHENTICATION
    # ========================================
    print("\n" + "=" * 70)
    print("PHASE 1: Authentication (Read-Only API)")
    print("=" * 70)
    
    if not api_tool.authenticate():
        print("❌ Authentication failed. Exiting.")
        return
    
    api_tool.test_read_only_restriction()
    
    # ========================================
    # PHASE 2: ACCOUNT INFORMATION
    # ========================================
    print("\n" + "=" * 70)
    print("PHASE 2: Account Information")
    print("=" * 70)
    
    about = api_tool.get_about_info()
    if about:
        with open('account_info.json', 'w', encoding='utf-8') as f:
            json.dump(about, f, indent=2, default=str)
        print("✓ Account info saved to: account_info.json")
    
    # ========================================
    # PHASE 3: FILE SEARCH
    # ========================================
    print("\n" + "=" * 70)
    print("PHASE 3: File Discovery")
    print("=" * 70)
    
    print("\nSearch options:")
    print("1. All files (limited)")
    print("2. All files (unlimited - may take time)")
    print("3. Files modified in date range")
    print("4. Specific file IDs")
    
    choice = input("\nChoice (1-4): ").strip()
    
    files = []
    if choice == '1':
        max_results = input("Max results (default 100): ").strip() or "100"
        result = api_tool.list_files(max_results=int(max_results))
        files = result['files']
    elif choice == '2':
        print("\n⚠️  This will fetch ALL files and may take a long time!")
        proceed = input("Continue? (y/n): ").strip().lower()
        if proceed == 'y':
            files = api_tool.get_all_files()
    elif choice == '3':
        start = input("Start date (YYYY-MM-DD): ").strip()
        end = input("End date (YYYY-MM-DD): ").strip()
        files = api_tool.find_files_by_date_range(
            f'{start}T00:00:00',
            f'{end}T23:59:59'
        )
    elif choice == '4':
        print("Enter file IDs (one per line, empty line to finish):")
        file_ids = []
        while True:
            fid = input().strip()
            if not fid:
                break
            file_ids.append(fid)
        
        for fid in file_ids:
            metadata = api_tool.get_file_metadata(fid)
            if metadata:
                files.append(metadata)
    
    if not files:
        print("\n❌ No files found. Exiting.")
        return
    
    print(f"\n✓ Found {len(files)} files")
    print("-" * 70)
    for i, f in enumerate(files[:10], 1):
        print(f"{i}. {f['name']}")
        print(f"   Modified: {f.get('modifiedTime', 'N/A')}")
    if len(files) > 10:
        print(f"... and {len(files) - 10} more")
    print("-" * 70)
    
    # ========================================
    # PHASE 4: COMPREHENSIVE DATA EXTRACTION
    # ========================================
    print("\n" + "=" * 70)
    print("PHASE 4: Comprehensive Metadata Extraction")
    print("=" * 70)
    
    print("\nThis will extract:")
    print("  • File metadata (ALL fields)")
    print("  • Revision history")
    print("  • Comments")
    print("  • Permissions")
    
    proceed = input("\nProceed? (y/n): ").strip().lower()
    if proceed != 'y':
        print("❌ Extraction cancelled.")
        return
    
    # Create session
    session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    print(f"\nSession ID: {session_id}")
    
    # Extract comprehensive data
    print(f"\n📊 Extracting comprehensive data for {len(files)} files...")
    comprehensive_data = []
    
    for i, file in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] Processing: {file['name']}")
        file_id = file.get('id')
        
        comp_data = api_tool.get_comprehensive_file_data(file_id)
        comprehensive_data.append(comp_data)
    
    # Generate baseline hash
    baseline_hash = verifier.generate_hash(comprehensive_data)
    
    # Save baseline
    baseline_file = f'session_{session_id}_BASELINE.json'
    with open(baseline_file, 'w', encoding='utf-8') as f:
        json.dump({
            'session_id': session_id,
            'capture_time': datetime.now().isoformat(),
            'total_files': len(comprehensive_data),
            'baseline_hash_sha256': baseline_hash,
            'files': comprehensive_data
        }, f, indent=2, default=str)
    
    print(f"\n✓ Baseline saved: {baseline_file}")
    print(f"✓ Baseline hash: {baseline_hash}")
    
    # ========================================
    # PHASE 5: VERIFICATION
    # ========================================
    print("\n" + "=" * 70)
    print("PHASE 5: Integrity Verification")
    print("=" * 70)
    
    verify = input("\nRe-capture metadata to verify integrity? (y/n): ").strip().lower()
    
    if verify == 'y':
        print("\n📊 Re-capturing metadata...")
        
        post_data = []
        for i, baseline_item in enumerate(comprehensive_data, 1):
            print(f"[{i}/{len(comprehensive_data)}] Re-capturing...")
            file_id = baseline_item.get('file_id')
            comp_data = api_tool.get_comprehensive_file_data(file_id)
            post_data.append(comp_data)
        
        # Generate post hash
        post_hash = verifier.generate_hash(post_data)
        
        # Save post-capture
        post_file = f'session_{session_id}_POST.json'
        with open(post_file, 'w', encoding='utf-8') as f:
            json.dump({
                'session_id': session_id,
                'capture_time': datetime.now().isoformat(),
                'total_files': len(post_data),
                'post_hash_sha256': post_hash,
                'files': post_data
            }, f, indent=2, default=str)
        
        print(f"\n✓ Post-capture saved: {post_file}")
        print(f"✓ Post hash: {post_hash}")
        
        # Compare
        result = verifier.verify_no_changes(comprehensive_data, post_data)
        
        # Save verification
        verification_file = f'session_{session_id}_VERIFICATION.json'
        with open(verification_file, 'w', encoding='utf-8') as f:
            json.dump({
                'session_id': session_id,
                'baseline_hash': baseline_hash,
                'post_hash': post_hash,
                'hashes_match': baseline_hash == post_hash,
                'verification_result': result
            }, f, indent=2, default=str)
        
        # Generate attestation
        attestation = verifier.generate_attestation(result)
        attestation_with_hashes = f"""
SESSION: {session_id}

HASH COMPARISON:
  Baseline Hash: {baseline_hash}
  Post Hash:     {post_hash}
  Match:         {baseline_hash == post_hash}

{attestation}
"""
        
        attestation_file = f'session_{session_id}_ATTESTATION.txt'
        with open(attestation_file, 'w', encoding='utf-8') as f:
            f.write(attestation_with_hashes)
        
        # Results
        print("\n" + "=" * 70)
        print("VERIFICATION RESULTS")
        print("=" * 70)
        print(f"\nBaseline Hash: {baseline_hash}")
        print(f"Post Hash:     {post_hash}")
        
        if baseline_hash == post_hash:
            print("\n✓✓✓ VERIFICATION PASSED ✓✓✓")
            print("No changes detected - data integrity confirmed")
        else:
            print("\n✗✗✗ VERIFICATION FAILED ✗✗✗")
            print("Changes detected - review verification report")
        
        print(f"\n✓ Verification saved: {verification_file}")
        print(f"✓ Attestation saved: {attestation_file}")
    
    # ========================================
    # FINAL SUMMARY
    # ========================================
    print("\n" + "=" * 70)
    print("WORKFLOW COMPLETE")
    print("=" * 70)
    
    print("\n📁 Generated Files:")
    print(f"  • {baseline_file}")
    if verify == 'y':
        print(f"  • {post_file}")
        print(f"  • {verification_file}")
        print(f"  • {attestation_file}")
    
    print(f"\n✅ Successfully extracted comprehensive metadata for {len(comprehensive_data)} files")
    print("=" * 70)


if __name__ == '__main__':
    try:
        forensic_workflow_enhanced()
    except KeyboardInterrupt:
        print("\n\n❌ Workflow interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)