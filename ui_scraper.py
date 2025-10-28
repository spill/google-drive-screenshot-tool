#!/usr/bin/env python3
"""
UI Metadata Scraper for Google Drive
Scrapes metadata from Drive's web interface (no API needed)
"""

import time
import json
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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
        Open the details panel for a file - FIND FILE FIRST, THEN RIGHT-CLICK
        
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
            
            # STEP 1: FIND THE FILE using multiple methods
            target = None
            
            # Method 1: data-tooltip attribute
            print(f"  Searching for file (method 1: tooltip)...")
            file_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-tooltip]')
            for elem in file_elements:
                tooltip = elem.get_attribute('data-tooltip')
                if tooltip and file_name.lower() in tooltip.lower():
                    target = elem
                    print(f"  ✓ Found via tooltip: {tooltip}")
                    break
            
            # Method 2: aria-label attribute
            if not target:
                print(f"  Searching for file (method 2: aria-label)...")
                file_elements = self.driver.find_elements(By.CSS_SELECTOR, '[aria-label]')
                for elem in file_elements:
                    label = elem.get_attribute('aria-label')
                    if label and file_name.lower() in label.lower():
                        target = elem
                        print(f"  ✓ Found via aria-label: {label}")
                        break
            
            # Method 3: Text content in clickable elements
            if not target:
                print(f"  Searching for file (method 3: text content)...")
                try:
                    search_text = file_name[:30] if len(file_name) > 30 else file_name
                    file_elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{search_text}')]")
                    for elem in file_elements:
                        tag = elem.tag_name.lower()
                        role = elem.get_attribute('role')
                        if tag in ['div', 'button', 'a'] or role in ['button', 'listitem', 'link']:
                            target = elem
                            print(f"  ✓ Found via text content ({tag})")
                            break
                except:
                    pass
            
            if not target:
                print(f"  ✗ Could not find file using any method")
                return False
            
            # STEP 2: CLICK TO SELECT THE FILE
            print(f"  Selecting file...")
            clicked = False
            
            click_methods = [
                ("direct click", lambda: target.click()),
                ("ActionChains", lambda: ActionChains(self.driver).move_to_element(target).click().perform()),
                ("JavaScript", lambda: self.driver.execute_script("arguments[0].click();", target)),
                ("scroll + click", lambda: (self.driver.execute_script("arguments[0].scrollIntoView(true);", target), time.sleep(0.5), target.click())),
            ]
            
            for method_name, click_func in click_methods:
                try:
                    click_func()
                    time.sleep(1.5)
                    print(f"  ✓ File selected ({method_name})")
                    clicked = True
                    break
                except Exception as e:
                    print(f"  {method_name} failed: {str(e)[:50]}")
                    continue
            
            if not clicked:
                print(f"  ✗ Could not click file with any method")
                return False
            
            # STEP 3: RIGHT-CLICK AND CLICK "FILE INFORMATION"
            print(f"  Opening details pane via right-click...")
            actions = ActionChains(self.driver)
            
            # Right-click on the selected file
            actions.context_click(target).perform()
            time.sleep(2)
            
            # Click "File information" from context menu
            detail_opened = False
            for option in ["File information", "View details", "Details", "Show details", "Open details panel"]:
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
                print(f"  ✗ Could not find 'File information' in context menu")
                # Try Alt+Right as backup
                print(f"  Trying Alt + Right Arrow as backup...")
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