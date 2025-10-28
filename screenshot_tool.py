#!/usr/bin/env python3
"""
Screenshot Tool for Google Drive Files - MANUAL CHROMEDRIVER for Chrome 141
Configured for Chrome version: 141.0.7390.123
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
from selenium.webdriver.chrome.service import Service

# ✅ MANUAL CHROMEDRIVER PATH (download instructions in CHROMEDRIVER_FIX_INSTRUCTIONS.md)
CHROMEDRIVER_PATH = r"C:\Users\rtrin\Downloads\chromedriver-141\chromedriver-win64\chromedriver.exe"


def _windows_chrome_profile_dir() -> str:
    """Best-effort guess for Windows Chrome profile directory."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidate = os.path.join(local_app_data, "Google", "Chrome", "User Data")
        if os.path.isdir(candidate):
            return candidate
    fallback = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data")
    return fallback


class DriveScreenshotTool:
    def __init__(self, screenshot_dir='screenshots'):
        """Initialize screenshot tool"""
        self.screenshot_dir = screenshot_dir
        os.makedirs(screenshot_dir, exist_ok=True)
        self.driver = None
        self.details_pane_open = False
        self.wait: WebDriverWait | None = None

    def setup_browser(self, headless=False, use_existing_profile=True):
        """Setup Chrome browser with manual ChromeDriver"""
        chrome_options = Options()

        if headless:
            chrome_options.add_argument('--headless=new')

        if use_existing_profile:
            user_data_dir = _windows_chrome_profile_dir()
            chrome_options.add_argument(f"user-data-dir={user_data_dir}")
            chrome_options.add_argument("--profile-directory=Default")
            print(f"✓ Using your existing Chrome profile")

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        try:
            # Check if ChromeDriver exists
            if not os.path.exists(CHROMEDRIVER_PATH):
                print(f"❌ ChromeDriver not found at: {CHROMEDRIVER_PATH}")
                print("\n💡 DOWNLOAD INSTRUCTIONS:")
                print("   1. Open PowerShell")
                print("   2. Run this command:")
                print('      Invoke-WebRequest -Uri "https://storage.googleapis.com/chrome-for-testing-public/141.0.7390.123/win64/chromedriver-win64.zip" -OutFile "$env:USERPROFILE\\Downloads\\chromedriver-141.zip"')
                print('      Expand-Archive -Path "$env:USERPROFILE\\Downloads\\chromedriver-141.zip" -DestinationPath "$env:USERPROFILE\\Downloads\\chromedriver-141" -Force')
                print("\n   Or manually download from:")
                print("   https://storage.googleapis.com/chrome-for-testing-public/141.0.7390.123/win64/chromedriver-win64.zip")
                print(f"   Extract to: {os.path.dirname(CHROMEDRIVER_PATH)}")
                return False
            
            print(f"📂 Using ChromeDriver: {CHROMEDRIVER_PATH}")
            service = Service(CHROMEDRIVER_PATH)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 10)
            print("✓ Browser initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize browser: {e}")
            print("\n💡 Troubleshooting:")
            print("   1. Check Chrome version matches ChromeDriver (141.0.7390.123)")
            print("   2. Verify ChromeDriver path exists")
            print("   3. Close all Chrome windows and try again")
            return False

    def login_to_google(self, skip_login=False):
        """Navigate to Google Drive"""
        print("\nNavigating to Google Drive...")
        self.driver.get('https://drive.google.com/drive/my-drive')

        if skip_login:
            print("⏳ Waiting for Drive to load...")
            time.sleep(5)
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label*="Search"]')))
                print("✓ Drive loaded successfully")
            except Exception:
                print("⚠️ Please log in if needed")
                input("Press ENTER when Drive is loaded...")
        else:
            print("\nPlease log in to Google Drive in the browser")
            input("Press ENTER when you're logged in...")

        print("✓ Ready to capture screenshots")

    def search_for_file(self, file_name: str) -> bool:
        """Search for a file"""
        print(f"  Searching for: {file_name}")
        try:
            search_box = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[aria-label="Search in Drive"]'))
            )
            search_box.clear()
            search_box.send_keys(file_name)
            search_box.send_keys(Keys.RETURN)
            time.sleep(3)
            print("  ✓ Search completed")
            return True
        except Exception as e:
            print(f"  ❌ Search failed: {e}")
            return False

    def open_details_pane_if_needed(self) -> bool:
        """Click 'i' icon to open details pane (one-time)"""
        if self.details_pane_open:
            print("  Details pane already open, skipping...")
            return True

        print("  Opening details pane via 'i' icon...")
        try:
            selectors = [
                '[aria-label="Details panel"]',
                '[aria-label="Show details"]',
                '[aria-label="Details"]',
                'button[aria-label*="etails"]',
                '[data-tooltip="Details panel"]',
                '[data-tooltip="Show details"]'
            ]

            info_icon = None
            for selector in selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if elem.is_displayed():
                        info_icon = elem
                        print(f"  Found 'i' icon")
                        break
                except Exception:
                    continue

            if not info_icon:
                print("  Trying JavaScript to find 'i' icon...")
                info_icon = self.driver.execute_script("""
                    let buttons = document.querySelectorAll('button');
                    for (let btn of buttons) {
                        let label = btn.getAttribute('aria-label') || '';
                        if (label.toLowerCase().includes('details') || label.toLowerCase().includes('info')) {
                            return btn;
                        }
                    }
                    return null;
                """)

            if not info_icon:
                print("  ⚠️ Could not find 'i' icon, assuming pane is already open")
                self.details_pane_open = True
                return True

            try:
                info_icon.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", info_icon)
            time.sleep(2)

            try:
                self.wait.until(EC.presence_of_element_located((By.XPATH, "//*[text()='Details' or text()='Activity']")))
                print("  ✓ Details pane opened successfully")
            except Exception:
                print("  ⚠️ Could not verify pane, continuing...")

            self.details_pane_open = True
            return True

        except Exception as e:
            print(f"  ⚠️ Error: {e}")
            self.details_pane_open = True
            return True

    def click_file_to_populate_details(self, file_name: str) -> bool:
        """LEFT CLICK file to populate details pane"""
        print("  Finding and clicking file...")

        try:
            target = None

            # Method 1: data-tooltip
            for elem in self.driver.find_elements(By.CSS_SELECTOR, '[data-tooltip]'):
                try:
                    tooltip = elem.get_attribute('data-tooltip')
                    if tooltip and file_name.lower() in tooltip.lower():
                        target = elem
                        print(f"  ✓ Found file via tooltip")
                        break
                except:
                    continue

            # Method 2: aria-label
            if not target:
                for elem in self.driver.find_elements(By.CSS_SELECTOR, '[aria-label]'):
                    try:
                        label = elem.get_attribute('aria-label')
                        if label and file_name.lower() in label.lower():
                            target = elem
                            print(f"  ✓ Found file via aria-label")
                            break
                    except:
                        continue

            # Method 3: Text content
            if not target:
                search_text = file_name[:30].replace("'", "\\'")
                for elem in self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{search_text}')]"):
                    try:
                        for xpath in ["./ancestor::div[@role='button'][1]", "./ancestor::div[@role='listitem'][1]", "./..", "./../../.."]:
                            try:
                                parent = elem.find_element(By.XPATH, xpath)
                                if parent.is_displayed() and parent.size['height'] > 20:
                                    target = parent
                                    print("  ✓ Found file via text")
                                    break
                            except:
                                continue
                        if target:
                            break
                    except:
                        continue

            # Method 4: JavaScript
            if not target:
                search_js = file_name[:30].replace("'", "\\'").lower()
                target = self.driver.execute_script(f"""
                    let selectors = ['[data-tooltip]', '[aria-label]', 'div[role="button"]', 'div[role="listitem"]'];
                    for (let sel of selectors) {{
                        for (let elem of document.querySelectorAll(sel)) {{
                            let text = (elem.innerText || elem.getAttribute('data-tooltip') || elem.getAttribute('aria-label') || '').toLowerCase();
                            if (text.includes('{search_js}') && elem.offsetParent) return elem;
                        }}
                    }}
                    return null;
                """)
                if target:
                    print("  ✓ Found file via JavaScript")

            if not target:
                print("  ❌ Could not find file element")
                return False

            # Scroll into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
            time.sleep(1)

            try:
                self.wait.until(EC.element_to_be_clickable(target))
            except:
                print("  ⚠️ Element not clickable, trying anyway...")

            # Try clicking (3 methods)
            clicked = False
            for method_name, click_func in [
                ("regular", lambda: target.click()),
                ("JavaScript", lambda: self.driver.execute_script("arguments[0].click();", target)),
                ("ActionChains", lambda: ActionChains(self.driver).move_to_element(target).pause(0.5).click().perform())
            ]:
                if not clicked:
                    try:
                        click_func()
                        time.sleep(2)
                        print(f"  ✓ Clicked file ({method_name})")
                        clicked = True
                    except Exception as e:
                        print(f"  {method_name} click failed: {e}")

            if not clicked:
                print("  ❌ All click methods failed")
                return False

            # Verify details populated
            print("  Verifying details populated...")
            time.sleep(2)
            try:
                self.wait.until(EC.presence_of_element_located((By.XPATH, "//*[text()='Details' or text()='Activity']")))
                details_panel = self.driver.find_element(By.CSS_SELECTOR, '[role="complementary"]')
                if len(details_panel.text.strip()) > 50:
                    print("  ✓ Details pane populated")
                else:
                    print("  ⚠️ Details might be light, continuing")
            except:
                print("  ⚠️ Could not verify, continuing...")

            return True

        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _ensure_tab(self, tab_text: str) -> bool:
        """Click a tab ('Details' or 'Activity')"""
        try:
            tab = self.driver.find_element(By.XPATH, f"//*[text()='{tab_text}']")
            if tab.is_displayed():
                try:
                    tab.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", tab)
                time.sleep(2)
                print(f"  ✓ Clicked {tab_text} tab")
                return True
        except:
            pass

        # JS fallback
        try:
            result = self.driver.execute_script(f"""
                let elements = [...document.querySelectorAll('*')];
                let el = elements.find(e => e.textContent.trim() === '{tab_text}' && e.offsetParent !== null);
                if (el) {{ el.click(); return true; }}
                return false;
            """)
            if result:
                time.sleep(2)
                print(f"  ✓ Clicked {tab_text} tab (JS)")
                return True
            print(f"  ⚠️ Could not click {tab_text} tab - may already be selected")
            return True
        except:
            return False

    def screenshot_file_details(self, file_id: str, file_name: str) -> list:
        """
        Capture 2 screenshots with 33% zoom:
        1) Details tab
        2) Activity tab
        """
        print(f"\n{'='*60}")
        print(f"Capturing: {file_name}")
        print(f"File ID: {file_id}")
        print(f"{'='*60}")

        screenshot_paths = []

        try:
            # Search for file
            if not self.search_for_file(file_name):
                print("  Search failed, returning to My Drive...")
                self.driver.get('https://drive.google.com/drive/my-drive')
                time.sleep(3)
                return []

            # Open details pane (one-time)
            if not self.open_details_pane_if_needed():
                print("  ⚠️ Could not open details pane")
                return []

            # Click file to populate details
            if not self.click_file_to_populate_details(file_name):
                print("  ⚠️ Could not click file")
                return []

            time.sleep(2)

            # Ensure Details tab is active
            print("\n  Ensuring Details tab is active...")
            self._ensure_tab("Details")

            # Create folder
            safe_filename = "".join(c for c in file_name if c.isalnum() or c in (' ', '_', '-')).strip() or "file"
            file_folder = os.path.join(self.screenshot_dir, safe_filename)
            os.makedirs(file_folder, exist_ok=True)
            print(f"  ✓ Using folder: {file_folder}")

            # Zoom to 33%
            print("\n  📷 Setting zoom to 50%...")
            try:
                self.driver.execute_script("document.body.style.zoom='0.50'")
                time.sleep(2)
                print("  ✓ Zoomed to 50%")
            except Exception as e:
                print(f"  ⚠️ Could not zoom: {e}")

            # Screenshot 1: Details
            print("\n  [1/2] Capturing Details tab...")
            ts1 = datetime.now().strftime('%Y%m%d_%H%M%S')
            p1 = os.path.join(file_folder, f"{ts1}_{safe_filename}.1.png")
            self.driver.save_screenshot(p1)
            print(f"  ✓ Saved: {os.path.basename(p1)}")
            screenshot_paths.append(p1)
            time.sleep(1)

            # Switch to Activity tab
            print("\n  [2/2] Switching to Activity tab...")
            self._ensure_tab("Activity")
            time.sleep(2)

            # Screenshot 2: Activity
            print("\n  Capturing Activity tab...")
            ts2 = datetime.now().strftime('%Y%m%d_%H%M%S')
            p2 = os.path.join(file_folder, f"{ts2}_{safe_filename}.2.png")
            self.driver.save_screenshot(p2)
            print(f"  ✓ Saved: {os.path.basename(p2)}")
            screenshot_paths.append(p2)

            # Reset zoom
            print("\n  Resetting zoom to 100%...")
            try:
                self.driver.execute_script("document.body.style.zoom='1.0'")
                time.sleep(1)
                print("  ✓ Zoom reset")
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

            # Emergency zoom reset
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
    print("This is a library module. Use forensic_workflow.py or forensic_tool_gui_pro.py")