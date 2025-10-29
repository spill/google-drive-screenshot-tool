#!/usr/bin/env python3
"""
UI Metadata Scraper for Google Drive
Scrapes metadata from Drive's web interface (no API needed)
WITH DUPLICATE FILE HANDLING
"""

import time
import json
from datetime import datetime
import re
from difflib import SequenceMatcher
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ==============================================================================
# DUPLICATE FILE HANDLING FUNCTIONS (same as screenshot_tool.py)
# ==============================================================================

def parse_index_from_search(search_term: str):
    """Parse index notation from search term"""
    patterns = [r'\s*\[(\d+)\]\s*$', r'\s*#(\d+)\s*$', r'\s*\((\d+)\)\s*$']
    
    for pattern in patterns:
        match = re.search(pattern, search_term)
        if match:
            index = int(match.group(1))
            clean_term = re.sub(pattern, '', search_term).strip()
            return (clean_term, index)
    
    return (search_term, None)


def calculate_similarity(search_term: str, candidate: str) -> float:
    """Calculate how similar two strings are (0.0 to 1.0)"""
    search_lower = search_term.lower().strip()
    candidate_lower = candidate.lower().strip()
    
    if search_lower == candidate_lower:
        return 1.0
    
    if search_lower in candidate_lower:
        return 0.85 + (0.15 * len(search_lower) / len(candidate_lower))
    
    base_similarity = SequenceMatcher(None, search_lower, candidate_lower).ratio()
    
    search_words = set(search_lower.split())
    candidate_words = set(candidate_lower.split())
    word_overlap = len(search_words & candidate_words) / max(len(search_words), 1)
    
    return (base_similarity * 0.7) + (word_overlap * 0.3)


def find_best_match(search_term: str, candidates: list, threshold=0.6):
    """Find best matching file with duplicate detection"""
    if not candidates:
        return (None, 0, "No candidates", None)
    
    clean_search, requested_index = parse_index_from_search(search_term)
    
    scored = []
    for name, elem in candidates:
        score = calculate_similarity(clean_search, name)
        if score >= threshold:
            scored.append((name, elem, score))
    
    if not scored:
        return (None, 0, f"No matches above {threshold:.0%}", None)
    
    scored.sort(key=lambda x: x[2], reverse=True)
    
    has_duplicates = len([s for s in scored if s[2] >= scored[0][2] - 0.05]) > 1
    
    if has_duplicates and not requested_index:
        print(f"  ⚠️  WARNING: {len(scored)} similar files found!")
        print(f"  💡 Use index notation: '{clean_search} [2]' to pick specific file")
        for i, (name, _, score) in enumerate(scored[:5], 1):
            print(f"     {i}. {name} ({score:.0%})")
    
    if requested_index and 1 <= requested_index <= len(scored):
        name, elem, score = scored[requested_index - 1]
        reason = f"Selected by index #{requested_index}"
    else:
        name, elem, score = scored[0]
        reason = "Highest similarity" + (" (duplicates exist!)" if has_duplicates else "")
    
    return (elem, score, reason, name)


# ==============================================================================
# MAIN UI SCRAPER CLASS
# ==============================================================================

class DriveUIScraper:
    """
    Scrapes file metadata from Google Drive UI
    Used when API authentication is not available
    """
    
    def __init__(self, driver):
        """
        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
    
    def search_file_in_ui(self, file_name):
        """
        Search for a file using Drive's search box
        
        Args:
            file_name: Name of file to search for
            
        Returns:
            bool: True if found, False otherwise
        """
        try:
            # Find search box
            search_box = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[aria-label*="Search"]'))
            )
            
            # Clear and enter search term
            search_box.clear()
            search_box.send_keys(file_name)
            
            from selenium.webdriver.common.keys import Keys
            search_box.send_keys(Keys.RETURN)
            
            time.sleep(3)  # Wait for results
            
            return True
            
        except Exception as e:
            print(f"Search failed: {e}")
            return False
    
    def open_details_panel_ui(self, file_name):
        """
        Open the details panel for a file - WITH FUZZY MATCHING & DUPLICATE DETECTION
        
        Args:
            file_name: Name of file
            
        Returns:
            bool: True if opened, False otherwise
        """
        try:
            print(f"  Opening details panel for: {file_name}")
            
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.common.action_chains import ActionChains
            
            # Wait for search results to load
            time.sleep(3)
            
            # Collect all potential file elements
            all_elements = []
            for selector in ['[data-tooltip]', '[aria-label]', 'div[role="button"]', 'div[role="listitem"]']:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    all_elements.extend(elements)
                except Exception:
                    continue
            
            print(f"  Found {len(all_elements)} potential elements")
            
            # Extract candidates
            candidates = []
            for elem in all_elements:
                try:
                    name = None
                    
                    tooltip = elem.get_attribute('data-tooltip')
                    if tooltip and len(tooltip) > 0:
                        name = tooltip
                    
                    if not name:
                        label = elem.get_attribute('aria-label')
                        if label and len(label) > 0:
                            name = label
                    
                    if not name:
                        text = elem.text.strip()
                        if text and len(text) > 0 and len(text) < 200:
                            name = text
                    
                    if name:
                        candidates.append((name, elem))
                except Exception:
                    continue
            
            print(f"  Extracted {len(candidates)} file names")
            
            # Find best match with duplicate detection
            target, score, reason, match_name = find_best_match(file_name, candidates, threshold=0.6)
            
            if not target:
                print(f"  ✗ {reason}")
                return False
            
            print(f"  ✓ Matched: '{match_name}'")
            print(f"  Similarity: {score:.0%}")
            print(f"  Reason: {reason}")
            
            # Click to select
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
                time.sleep(1)
                target.click()
                time.sleep(1.5)
                print(f"  ✓ File selected")
            except Exception as e:
                print(f"  Click failed: {e}")
                return False
            
            # Right-click and open details
            actions = ActionChains(self.driver)
            actions.context_click(target).perform()
            time.sleep(2)
            
            # Click "File information" from context menu
            detail_opened = False
            for option in ["File information", "View details", "Details", "Show details"]:
                try:
                    detail_option = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{option}')]")
                    detail_option.click()
                    print(f"  ✓ Clicked '{option}' from menu")
                    time.sleep(3)
                    detail_opened = True
                    break
                except:
                    continue
            
            if detail_opened:
                print(f"  ✓ Details pane opened")
                return True
            else:
                # Try Alt+Right as backup
                print(f"  Trying keyboard shortcut...")
                actions.send_keys(Keys.ESCAPE).perform()
                time.sleep(1)
                actions = ActionChains(self.driver)
                actions.key_down(Keys.ALT).send_keys(Keys.ARROW_RIGHT).key_up(Keys.ALT).perform()
                time.sleep(3)
                return True
            
        except Exception as e:
            print(f"  ✗ Failed to open details panel: {e}")
            return False
    
    def scrape_metadata_from_details(self):
        """
        Scrape metadata from the open details panel
        Uses multiple methods to find each field
        
        Returns:
            dict: Scraped metadata
        """
        metadata = {
            'scrape_time': datetime.now().isoformat(),
            'scrape_method': 'ui',
        }
        
        print("  Scraping metadata from details panel...")
        
        # Helper function to find text by label
        def find_field_value(labels):
            """Try multiple labels and methods to find a field"""
            for label in labels:
                # Method 1: XPath following-sibling
                try:
                    elem = self.driver.find_element(
                        By.XPATH, 
                        f"//*[contains(text(), '{label}')]/following-sibling::*[1]"
                    )
                    value = elem.text.strip()
                    if value:
                        return value
                except:
                    pass
                
                # Method 2: Parent then next div
                try:
                    elem = self.driver.find_element(
                        By.XPATH,
                        f"//*[contains(text(), '{label}')]/parent::*/following-sibling::*[1]"
                    )
                    value = elem.text.strip()
                    if value:
                        return value
                except:
                    pass
                
                # Method 3: JavaScript search
                try:
                    value = self.driver.execute_script(f"""
                        let elements = [...document.querySelectorAll('*')];
                        let label = elements.find(el => el.textContent.includes('{label}'));
                        if (label && label.nextElementSibling) {{
                            return label.nextElementSibling.textContent.trim();
                        }}
                        return null;
                    """)
                    if value:
                        return value
                except:
                    pass
            
            return 'Unknown'
        
        # Scrape each field with multiple possible labels
        metadata['type'] = find_field_value(['Type', 'File type', 'Kind'])
        print(f"    Type: {metadata['type']}")
        
        metadata['size'] = find_field_value(['Size', 'Storage used'])
        print(f"    Size: {metadata['size']}")
        
        metadata['owner'] = find_field_value(['Owner', 'Owned by'])
        print(f"    Owner: {metadata['owner']}")
        
        metadata['modifiedTime'] = find_field_value(['Modified', 'Last modified', 'Modified by me'])
        print(f"    Modified: {metadata['modifiedTime']}")
        
        metadata['viewedByMeTime'] = find_field_value(['Opened', 'Opened by me', 'Last opened'])
        print(f"    Opened: {metadata['viewedByMeTime']}")
        
        metadata['createdTime'] = find_field_value(['Created', 'Date created'])
        print(f"    Created: {metadata['createdTime']}")
        
        metadata['location'] = find_field_value(['Location', 'Folder', 'Parent folder'])
        print(f"    Location: {metadata['location']}")
        
        # Check if we got actual data
        has_data = any(v != 'Unknown' for k, v in metadata.items() if k not in ['scrape_time', 'scrape_method'])
        
        if not has_data:
            print("  ⚠️ Warning: No metadata found, all fields returned 'Unknown'")
            print("  This might mean the details panel isn't properly loaded")
        else:
            print("  ✓ Metadata scraped successfully")
        
        return metadata
    
    def scrape_file_metadata(self, file_name):
        """
        Complete workflow: search, open details, scrape, close
        
        Args:
            file_name: Name of file
            
        Returns:
            dict: Scraped metadata or None if failed
        """
        print(f"\nScraping metadata for: {file_name}")
        
        # Search for file
        if not self.search_file_in_ui(file_name):
            print(f"  ✗ Could not search for file")
            return None
        
        # Open details panel
        if not self.open_details_panel_ui(file_name):
            print(f"  ✗ Could not open details panel")
            return None
        
        # Scrape metadata
        metadata = self.scrape_metadata_from_details()
        metadata['name'] = file_name
        
        # Close details panel (ESC key)
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains
        try:
            actions = ActionChains(self.driver)
            actions.send_keys(Keys.ESCAPE).perform()
            time.sleep(1)
        except:
            pass
        
        print(f"  ✓ Metadata scraped successfully")
        return metadata
    
    def scrape_multiple_files(self, file_names, callback=None):
        """
        Scrape metadata for multiple files
        
        Args:
            file_names: List of file names
            callback: Optional callback function(progress, file_name)
            
        Returns:
            list: List of metadata dicts
        """
        all_metadata = []
        total = len(file_names)
        
        for i, file_name in enumerate(file_names, 1):
            if callback:
                callback(i / total, file_name)
            
            metadata = self.scrape_file_metadata(file_name)
            if metadata:
                all_metadata.append(metadata)
            
            # Brief pause between files
            time.sleep(1)
        
        return all_metadata


def generate_hash_from_scraped_data(metadata_list):
    """
    Generate SHA-256 hash from scraped metadata
    
    Args:
        metadata_list: List of metadata dicts
        
    Returns:
        str: SHA-256 hash
    """
    import hashlib
    
    # Sort for consistency
    sorted_json = json.dumps(metadata_list, sort_keys=True)
    
    # Generate hash
    hash_obj = hashlib.sha256(sorted_json.encode('utf-8'))
    return hash_obj.hexdigest()


if __name__ == '__main__':
    print("UI Metadata Scraper Module")
    print("Import this into your workflow for hybrid mode")