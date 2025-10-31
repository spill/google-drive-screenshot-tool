#!/usr/bin/env python3
"""
Analyze API Extraction Results
Identifies files without revisions that need screenshot capture
"""

import json
import os
import sys
from datetime import datetime


def analyze_extraction_results(baseline_file):
    """
    Analyze API extraction and identify files needing screenshots
    
    Args:
        baseline_file: Path to BASELINE.json file
    """
    print("=" * 80)
    print("API EXTRACTION ANALYSIS")
    print("=" * 80)
    
    # Load the baseline
    print(f"\n📂 Loading: {baseline_file}")
    
    if not os.path.exists(baseline_file):
        print(f"❌ File not found: {baseline_file}")
        return
    
    with open(baseline_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    files = data.get('files', [])
    session_id = data.get('session_id', 'unknown')
    
    print(f"✓ Loaded session: {session_id}")
    print(f"✓ Total files: {len(files)}")
    
    # Analyze each file
    print("\n" + "=" * 80)
    print("ANALYZING FILES FOR REVISION ACCESS")
    print("=" * 80)
    
    files_with_revisions = []
    files_without_revisions = []
    files_without_revisions_details = []
    
    for file_data in files:
        metadata = file_data.get('metadata', {})
        file_name = metadata.get('name', 'Unknown')
        file_id = file_data.get('file_id') or metadata.get('id', 'unknown')
        revision_count = file_data.get('revision_count', 0)
        comment_count = file_data.get('comment_count', 0)
        perm_count = file_data.get('permission_count', 0)
        
        if revision_count > 0:
            files_with_revisions.append({
                'name': file_name,
                'id': file_id,
                'revisions': revision_count,
                'comments': comment_count,
                'permissions': perm_count
            })
        else:
            files_without_revisions.append(file_name)
            files_without_revisions_details.append({
                'file_id': file_id,
                'file_name': file_name,
                'reason': 'No revisions accessible via API',
                'comment_count': comment_count,
                'permission_count': perm_count
            })
    
    # Report
    print(f"\n✓ Files with complete API access: {len(files_with_revisions)}")
    print(f"⚠️  Files WITHOUT revisions: {len(files_without_revisions)}")
    
    if files_with_revisions:
        print(f"\n" + "-" * 80)
        print(f"FILES WITH COMPLETE API ACCESS ({len(files_with_revisions)}):")
        print("-" * 80)
        for i, f in enumerate(files_with_revisions[:10], 1):
            print(f"  {i}. {f['name']}")
            print(f"     ↳ {f['revisions']} revisions, {f['comments']} comments, {f['permissions']} permissions")
        if len(files_with_revisions) > 10:
            print(f"  ... and {len(files_with_revisions) - 10} more")
    
    if files_without_revisions:
        print(f"\n" + "=" * 80)
        print(f"⚠️  FILES WITHOUT REVISIONS ({len(files_without_revisions)}):")
        print("=" * 80)
        print("\nThese files did not provide revision history via the API.")
        print("This typically means you have view-only or comment-only access.\n")
        
        for i, fname in enumerate(files_without_revisions, 1):
            print(f"  {i}. {fname}")
        
        print(f"\n" + "-" * 80)
        print("💡 RECOMMENDATION:")
        print("-" * 80)
        print("Use the Hybrid Workflow to capture Activity logs via screenshots:")
        print("  1. Run: python simple_hybrid_example.py")
        print("  2. Select the BASELINE file when prompted")
        print("  3. Follow the guided workflow")
        print("-" * 80)
        
        # Save report
        base_dir = os.path.dirname(baseline_file)
        
        # TXT report
        txt_report = os.path.join(base_dir, f'session_{session_id}_NEEDS_SCREENSHOTS.txt')
        with open(txt_report, 'w', encoding='utf-8') as f:
            f.write("FILES NEEDING SCREENSHOT CAPTURE\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Session ID: {session_id}\n")
            f.write(f"Analysis Date: {datetime.now().isoformat()}\n")
            f.write(f"Total Files Analyzed: {len(files)}\n")
            f.write(f"Files Without Revisions: {len(files_without_revisions)}\n\n")
            f.write("=" * 70 + "\n\n")
            f.write("REASON:\n")
            f.write("These files did not provide revision history via Google Drive API.\n")
            f.write("This typically means you have view-only or comment-only access.\n\n")
            f.write("SOLUTION:\n")
            f.write("Use the hybrid workflow to capture Activity logs via screenshots:\n")
            f.write("  python simple_hybrid_example.py\n\n")
            f.write("=" * 70 + "\n\n")
            f.write("FILE LIST:\n\n")
            for i, fname in enumerate(files_without_revisions, 1):
                f.write(f"{i}. {fname}\n")
        
        print(f"\n✓ TXT report saved: {os.path.basename(txt_report)}")
        
        # JSON report
        json_report = os.path.join(base_dir, f'session_{session_id}_NEEDS_SCREENSHOTS.json')
        with open(json_report, 'w', encoding='utf-8') as f:
            json.dump({
                'session_id': session_id,
                'analysis_date': datetime.now().isoformat(),
                'total_files': len(files),
                'files_with_revisions': len(files_with_revisions),
                'files_without_revisions': len(files_without_revisions),
                'files': files_without_revisions_details
            }, f, indent=2)
        
        print(f"✓ JSON report saved: {os.path.basename(json_report)}")
        
        # Create screenshot queue directly (without needing external imports)
        queue_path = f'screenshot_queue_{session_id}.json'
        queue_data = {
            'created': datetime.now().isoformat(),
            'session_id': session_id,
            'total_files': len(files_without_revisions),
            'files': [
                {
                    'file_name': fname,
                    'file_id': next((f['file_id'] for f in files_without_revisions_details if f['file_name'] == fname), 'unknown'),
                    'reason': 'No revisions accessible via API',
                    'screenshot_tabs': ['Details', 'Activity']
                }
                for fname in files_without_revisions
            ]
        }
        
        try:
            with open(queue_path, 'w', encoding='utf-8') as f:
                json.dump(queue_data, f, indent=2)
            print(f"✓ Screenshot queue created: {queue_path}")
            print("\n💡 Ready for hybrid workflow! Just run:")
            print(f"   python simple_hybrid_example.py")
        except Exception as e:
            print(f"\n⚠️  Could not create screenshot queue: {e}")
    else:
        print(f"\n" + "=" * 80)
        print("✓✓✓ EXCELLENT! ALL FILES HAVE COMPLETE API ACCESS ✓✓✓")
        print("=" * 80)
        print("\nAll files provided complete revision histories.")
        print("No screenshot capture needed!")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


def main():
    """Main entry point"""
    print("=" * 80)
    print("API EXTRACTION ANALYZER")
    print("=" * 80)
    
    # Check for exports directory
    exports_dir = 'GoogleDrive_Exports'
    
    if not os.path.exists(exports_dir):
        print(f"\n❌ {exports_dir} folder not found")
        print("\n💡 Run forensic_tool_gui_pro.py first to extract API data")
        return
    
    # Find BASELINE files
    baseline_files = [
        os.path.join(exports_dir, f) 
        for f in os.listdir(exports_dir) 
        if 'BASELINE' in f and f.endswith('.json')
    ]
    
    if not baseline_files:
        print(f"\n❌ No BASELINE.json files found in {exports_dir}")
        print("\n💡 Run forensic_tool_gui_pro.py first to extract API data")
        return
    
    print(f"\n📂 Found {len(baseline_files)} baseline file(s):")
    for i, f in enumerate(baseline_files, 1):
        filename = os.path.basename(f)
        filesize = os.path.getsize(f)
        print(f"   {i}. {filename} ({filesize:,} bytes)")
    
    # Select file
    if len(baseline_files) == 1:
        baseline_file = baseline_files[0]
        print(f"\n✓ Using: {os.path.basename(baseline_file)}")
    else:
        choice = input("\nWhich file to analyze? (1-N): ").strip()
        try:
            idx = int(choice) - 1
            baseline_file = baseline_files[idx]
            print(f"✓ Using: {os.path.basename(baseline_file)}")
        except:
            print("❌ Invalid choice")
            return
    
    # Analyze
    analyze_extraction_results(baseline_file)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)