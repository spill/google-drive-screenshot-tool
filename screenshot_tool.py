#!/usr/bin/env python3
"""
Screenshot Tool for Google Drive Files - Version 5
SOLUTION: Zoom to 50% to capture all content in one screenshot
"""

import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys


class DriveScreenshotTool:
    def __init__(self, screenshot_dir='screenshots'):
        """Initialize screenshot tool"""
        self.screenshot_dir = screenshot_dir
        os.makedirs(screenshot_dir, exist_ok=True)
        self.driver = None
        
    def setup_browser(self, headless=False, use_existing_profile=False):
        """Setup Chrome browser"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument('--headless')
        
        if use_existing_profile:
            user_data_dir = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data")
            chrome_options.add_argument(f"user-data-dir={user_data_dir}")
            chrome_options.add_argument("--profile-directory=Default")
            print("✓ Using your existing Chrome profile")
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✓ Browser initialized")
            return True
        except Exception as e:
            print(f"Failed to initialize browser: {e}")
            return False
    
    def login_to_google(self, skip_login=False):
        """Navigate to Google Drive"""
        print("\nNavigating to Google Drive...")
        self.driver.get('https://drive.google.com/drive/my-drive')
        
        if skip_login:
            print("⏳ Waiting for Drive to load...")
            time.sleep(5)
            try:
                wait = WebDriverWait(self.driver, 10)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label*="Search"]')))
                print("✓ Drive loaded successfully")
            except:
                print("⚠️ Please log in if needed")
                input("Press ENTER when Drive is loaded...")
        else:
            print("\nPlease log in to Google Drive in the browser")
            input("Press ENTER when you're logged in...")
        
        print("✓ Ready to capture screenshots")
    
    def search_for_file(self, file_name):
        """Search for a file"""
        print(f"  Searching for: {file_name}")
        try:
            search_box = self.driver.find_element(By.CSS_SELECTOR, 'input[aria-label="Search in Drive"]')
            search_box.clear()
            search_box.send_keys(file_name)
            search_box.send_keys(Keys.RETURN)
            time.sleep(3)
            print(f"  ✓ Search completed")
            return True
        except Exception as e:
            print(f"  ❌ Search failed: {e}")
            return False
    
    def open_details_pane(self, file_name):
        """Open details pane via right-click menu"""
        print(f"  Opening details pane...")
        try:
            time.sleep(2)
            
            # Find file in list
            file_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-tooltip]')
            target = None
            
            for elem in file_elements:
                tooltip = elem.get_attribute('data-tooltip')
                if tooltip and file_name.lower() in tooltip.lower():
                    target = elem
                    print(f"  ✓ Found file: {tooltip}")
                    break
            
            if not target:
                # Alternate method
                file_elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{file_name[:20]}')]")
                if file_elements:
                    for elem in file_elements:
                        parent = elem.find_element(By.XPATH, "./ancestor::div[@role='button' or @role='listitem'][1]")
                        if parent:
                            target = parent
                            break
            
            if not target:
                print(f"  ⚠️ Could not find file")
                return False
            
            # Right-click
            actions = ActionChains(self.driver)
            actions.context_click(target).perform()
            time.sleep(1)
            
            # Click "View details"
            for option in ["View details", "Details", "File information"]:
                try:
                    detail_option = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{option}')]")
                    detail_option.click()
                    print(f"  ✓ Clicked '{option}'")
                    time.sleep(2)
                    return True
                except:
                    continue
            
            # Keyboard shortcut fallback
            actions = ActionChains(self.driver)
            actions.key_down(Keys.CONTROL).key_down(Keys.ALT).send_keys('d').key_up(Keys.ALT).key_up(Keys.CONTROL).perform()
            time.sleep(2)
            return True
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def screenshot_file_details(self, file_id, file_name):
        """
        Capture 2 screenshots with 50% zoom:
        1. Details tab (all info visible)
        2. Activity tab (all history visible)
        """
        print(f"\n{'='*60}")
        print(f"Capturing: {file_name}")
        print(f"File ID: {file_id}")
        print(f"{'='*60}")
        
        screenshot_paths = []
        
        try:
            # Search and open details
            if not self.search_for_file(file_name):
                self.driver.get('https://drive.google.com/drive/my-drive')
                time.sleep(3)
            
            if not self.open_details_pane(file_name):
                print("  ⚠️ Could not open details pane")
                return []
            
            time.sleep(2)
            
            # ===== ALWAYS CLICK DETAILS TAB FIRST =====
            # Google Drive remembers the last tab (Details or Activity)
            # We need to explicitly click Details for every file
            print("\n  Ensuring Details tab is active...")
            details_tab_clicked = False
            
            # Method 1: Direct click on Details
            try:
                details_tab = self.driver.find_element(By.XPATH, "//*[text()='Details']")
                if details_tab.is_displayed():
                    details_tab.click()
                    print("  ✓ Clicked Details tab")
                    details_tab_clicked = True
                    time.sleep(2)
            except Exception as e:
                print(f"  Details tab click failed: {e}")
            
            # Method 2: JavaScript fallback
            if not details_tab_clicked:
                try:
                    result = self.driver.execute_script("""
                        let elements = [...document.querySelectorAll('*')];
                        let details = elements.find(el => 
                            el.textContent.trim() === 'Details' && 
                            el.offsetParent !== null
                        );
                        if (details) {
                            details.click();
                            return true;
                        }
                        return false;
                    """)
                    if result:
                        print("  ✓ Clicked Details tab (JavaScript)")
                        time.sleep(2)
                    else:
                        print("  ⚠️ Could not click Details tab - may already be selected")
                except:
                    print("  ⚠️ Could not click Details tab - may already be selected")
            
            safe_filename = "".join(c for c in file_name if c.isalnum() or c in (' ', '_', '-'))
            
            # Create folder for this file's screenshots
            file_folder = os.path.join(self.screenshot_dir, safe_filename)
            os.makedirs(file_folder, exist_ok=True)
            print(f"  ✓ Created folder: {safe_filename}/")
            
            # ===== ZOOM TO 33% =====
            print("\n  📷 Setting zoom to 33% (to capture all content)...")
            self.driver.execute_script("document.body.style.zoom='0.33'")
            time.sleep(2)
            print("  ✓ Zoomed to 33%")
            
            # ===== SCREENSHOT 1: DETAILS TAB =====
            print("\n  [1/2] Capturing Details tab...")
            print("         (Includes: Type, Size, Owner, Modified, Opened, Created)")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            path = os.path.join(
                file_folder,
                f"{timestamp}_{safe_filename}.1.png"
            )
            self.driver.save_screenshot(path)
            print(f"  ✓ Saved: {safe_filename}/{timestamp}_{safe_filename}.1.png")
            screenshot_paths.append(path)
            time.sleep(1)
            
            # ===== CLICK ACTIVITY TAB =====
            print("\n  [2/2] Switching to Activity tab...")
            activity_clicked = False
            
            # Method 1: Direct click
            try:
                activity_tab = self.driver.find_element(By.XPATH, "//*[text()='Activity']")
                if activity_tab.is_displayed():
                    activity_tab.click()
                    print("  ✓ Clicked Activity tab")
                    activity_clicked = True
                    time.sleep(3)
            except Exception as e:
                print(f"  Method 1 failed: {e}")
            
            # Method 2: JavaScript
            if not activity_clicked:
                try:
                    result = self.driver.execute_script("""
                        let elements = [...document.querySelectorAll('*')];
                        let activity = elements.find(el => 
                            el.textContent.trim() === 'Activity' && 
                            el.offsetParent !== null
                        );
                        if (activity) {
                            activity.click();
                            return true;
                        }
                        return false;
                    """)
                    if result:
                        print("  ✓ Clicked Activity tab (JavaScript)")
                        activity_clicked = True
                        time.sleep(3)
                except Exception as e:
                    print(f"  Method 2 failed: {e}")
            
            if not activity_clicked:
                print("  ⚠️ WARNING: Could not click Activity tab!")
                print("              Screenshot will show Details tab only")
            
            # ===== SCREENSHOT 2: ACTIVITY TAB =====
            print("\n  Capturing Activity tab...")
            print("         (Includes: All edit history, viewers, comments)")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            path = os.path.join(
                file_folder,
                f"{timestamp}_{safe_filename}.2.png"
            )
            self.driver.save_screenshot(path)
            print(f"  ✓ Saved: {safe_filename}/{timestamp}_{safe_filename}.2.png")
            screenshot_paths.append(path)
            
            # ===== RESET ZOOM =====
            print("\n  Resetting zoom to 100%...")
            self.driver.execute_script("document.body.style.zoom='1.0'")
            time.sleep(1)
            print("  ✓ Zoom reset")
            
            # Close details pane
            try:
                actions = ActionChains(self.driver)
                actions.send_keys(Keys.ESCAPE).perform()
                time.sleep(1)
                print("  ✓ Closed details pane")
            except:
                pass
            
            print(f"\n{'='*60}")
            print(f"✓ SUCCESS: {len(screenshot_paths)} screenshots captured")
            print(f"{'='*60}\n")
            return screenshot_paths
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            
            # Emergency: reset zoom
            try:
                self.driver.execute_script("document.body.style.zoom='1.0'")
            except:
                pass
            
            return screenshot_paths
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            print("\n✓ Browser closed")


if __name__ == '__main__':
    print("This is a library module. Use forensic_workflow.py to run the tool.")