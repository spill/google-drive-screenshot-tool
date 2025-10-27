#!/usr/bin/env python3
"""
Google Drive Forensic Workflow with Hash Verification
Ensures 100% proof that no metadata was modified during screenshot capture
"""

import sys
import json
from datetime import datetime
from drive_forensic_tool import DriveForensicTool
from screenshot_tool import DriveScreenshotTool
from forensic_verifier import ForensicVerifier, print_verification_summary


def forensic_workflow_with_verification():
    """
    Complete forensic workflow with cryptographic verification:
    1. Capture metadata BEFORE (with hash)
    2. Take screenshots
    3. Capture metadata AFTER (with hash)
    4. Compare hashes to prove no modifications
    """
    print("=" * 70)
    print("GOOGLE DRIVE FORENSIC WORKFLOW WITH HASH VERIFICATION")
    print("Cryptographic proof of evidence integrity")
    print("=" * 70)
    
    # Initialize tools
    api_tool = DriveForensicTool()
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
    
    print("✓ Authenticated with READ-ONLY access")
    api_tool.test_read_only_restriction()
    
    # ========================================
    # PHASE 2: FILE SEARCH
    # ========================================
    print("\n" + "=" * 70)
    print("PHASE 2: File Discovery")
    print("=" * 70)
    
    print("\nSearch options:")
    print("1. All files (up to 20)")
    print("2. Files modified in date range")
    print("3. Files with specific name")
    
    choice = input("\nChoice (1-3): ").strip()
    
    files = []
    if choice == '1':
        files = api_tool.list_files(max_results=20)
    elif choice == '2':
        start = input("Start date (YYYY-MM-DD): ").strip()
        end = input("End date (YYYY-MM-DD): ").strip()
        files = api_tool.find_files_by_date_range(
            f'{start}T00:00:00',
            f'{end}T23:59:59'
        )
    elif choice == '3':
        name = input("File name (partial match): ").strip()
        query = f"name contains '{name}'"
        files = api_tool.list_files(query=query)
    
    if not files:
        print("\n❌ No files found. Exiting.")
        return
    
    print(f"\n✓ Found {len(files)} files")
    print("-" * 70)
    for i, f in enumerate(files, 1):
        print(f"{i}. {f['name']}")
        print(f"   Modified: {f.get('modifiedTime', 'N/A')}")
        print(f"   Opened: {f.get('viewedByMeTime', 'N/A')}")
    print("-" * 70)
    
    # ========================================
    # PHASE 3: BASELINE METADATA CAPTURE
    # ========================================
    print("\n" + "=" * 70)
    print("PHASE 3: BASELINE Metadata Capture (BEFORE Screenshots)")
    print("=" * 70)
    
    print("\n📊 Capturing baseline metadata with timestamps...")
    
    # Get detailed metadata for each file
    baseline_metadata = []
    for file in files:
        detailed = api_tool.service.files().get(
            fileId=file['id'],
            fields='id,name,mimeType,createdTime,modifiedTime,viewedByMeTime,size,owners'
        ).execute()
        baseline_metadata.append(detailed)
    
    # Export baseline
    baseline_file = 'forensic_baseline_BEFORE.json'
    with open(baseline_file, 'w', encoding='utf-8') as f:
        json.dump({
            'capture_time': datetime.now().isoformat(),
            'total_files': len(baseline_metadata),
            'purpose': 'BASELINE BEFORE screenshot capture',
            'files': baseline_metadata
        }, f, indent=2)
    
    # Generate baseline hash
    baseline_hash = verifier.generate_hash(baseline_metadata)
    
    print(f"✓ Baseline metadata saved: {baseline_file}")
    print(f"✓ Baseline hash (SHA-256): {baseline_hash}")
    print(f"✓ Total files: {len(baseline_metadata)}")
    
    # ========================================
    # PHASE 4: SCREENSHOT CAPTURE
    # ========================================
    print("\n" + "=" * 70)
    print("PHASE 4: Screenshot Capture")
    print("=" * 70)
    
    proceed = input("\n⚠️  Proceed with screenshots? (y/n): ").strip().lower()
    if proceed != 'y':
        print("❌ Screenshot phase cancelled by user.")
        return
    
    # Chrome profile option
    print("\n⚠️ IMPORTANT: Google may block automated browsers")
    print("\nScreenshot options:")
    print("1. Use your existing Chrome profile (RECOMMENDED - already logged in)")
    print("2. Use clean browser (may require manual login)")
    
    profile_choice = input("\nChoice (1 or 2): ").strip()
    use_existing_profile = (profile_choice == '1')
    
    if use_existing_profile:
        print("\n⚠️ IMPORTANT: Close ALL Chrome windows before continuing!")
        print("(The tool needs exclusive access to your Chrome profile)")
        input("Press ENTER when all Chrome windows are closed...")
    
    screenshot_tool = DriveScreenshotTool(screenshot_dir='forensic_screenshots')
    
    if not screenshot_tool.setup_browser(headless=False, use_existing_profile=use_existing_profile):
        print("❌ Browser setup failed. Exiting.")
        return
    
    screenshot_tool.login_to_google(skip_login=use_existing_profile)
    
    # Capture screenshots for all files
    print(f"\n📸 Capturing screenshots for {len(files)} files...")
    print("⚠️  During this process, NO file metadata should change")
    
    for i, file in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] Processing: {file['name']}")
        screenshot_tool.screenshot_file_details(file['id'], file['name'])
    
    screenshot_tool.close()
    
    print("\n✓ Screenshot capture complete")
    
    # ========================================
    # PHASE 5: POST-CAPTURE METADATA VERIFICATION
    # ========================================
    print("\n" + "=" * 70)
    print("PHASE 5: POST-CAPTURE Metadata Verification")
    print("=" * 70)
    
    print("\n📊 Re-capturing metadata to verify integrity...")
    
    # Get metadata again AFTER screenshots
    post_metadata = []
    for file in files:
        detailed = api_tool.service.files().get(
            fileId=file['id'],
            fields='id,name,mimeType,createdTime,modifiedTime,viewedByMeTime,size,owners'
        ).execute()
        post_metadata.append(detailed)
    
    # Export post-capture
    post_file = 'forensic_post_AFTER.json'
    with open(post_file, 'w', encoding='utf-8') as f:
        json.dump({
            'capture_time': datetime.now().isoformat(),
            'total_files': len(post_metadata),
            'purpose': 'VERIFICATION AFTER screenshot capture',
            'files': post_metadata
        }, f, indent=2)
    
    # Generate post-capture hash
    post_hash = verifier.generate_hash(post_metadata)
    
    print(f"✓ Post-capture metadata saved: {post_file}")
    print(f"✓ Post-capture hash (SHA-256): {post_hash}")
    
    # ========================================
    # PHASE 6: CRYPTOGRAPHIC VERIFICATION
    # ========================================
    print("\n" + "=" * 70)
    print("PHASE 6: CRYPTOGRAPHIC HASH VERIFICATION")
    print("=" * 70)
    
    print("\n🔐 Comparing hashes to verify no modifications occurred...")
    
    verification_result = verifier.verify_no_changes(baseline_metadata, post_metadata)
    
    # Print results
    print_verification_summary(verification_result)
    
    # Generate attestation
    attestation = verifier.generate_attestation(verification_result)
    attestation_file = 'forensic_attestation.txt'
    with open(attestation_file, 'w', encoding='utf-8') as f:
        f.write(attestation)
    
    print(f"✓ Attestation saved: {attestation_file}")
    
    # Export complete verification report
    verification_report = verifier.export_verification_report('forensic_verification.json')
    print(f"✓ Verification report saved: {verification_report}")
    
    # ========================================
    # FINAL SUMMARY
    # ========================================
    print("\n" + "=" * 70)
    print("FORENSIC WORKFLOW COMPLETE")
    print("=" * 70)
    
    print("\n📁 Generated Files:")
    print(f"  1. {baseline_file} - Metadata BEFORE screenshots")
    print(f"  2. {post_file} - Metadata AFTER screenshots")
    print(f"  3. {verification_report} - Hash verification details")
    print(f"  4. {attestation_file} - Formal attestation")
    print(f"  5. forensic_screenshots/ - Screenshot evidence")
    
    print("\n🔐 Cryptographic Verification:")
    print(f"  Before Hash: {baseline_hash}")
    print(f"  After Hash:  {post_hash}")
    
    if verification_result['match']:
        print(f"\n  ✓✓✓ PROOF: Hashes match - No modifications occurred ✓✓✓")
        print("\n✅ FORENSIC INTEGRITY CONFIRMED")
        print("   All file metadata remained unchanged during screenshot capture.")
        print("   The hash verification provides cryptographic proof.")
    else:
        print(f"\n  ✗✗✗ WARNING: Hashes do NOT match ✗✗✗")
        print("\n❌ FORENSIC INTEGRITY COMPROMISED")
        print("   Some file metadata changed during screenshot capture.")
        print(f"   See {verification_report} for details.")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    try:
        forensic_workflow_with_verification()
    except KeyboardInterrupt:
        print("\n\n❌ Workflow interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)