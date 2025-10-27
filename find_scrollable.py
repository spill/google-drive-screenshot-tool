#!/usr/bin/env python3
"""
Google Drive Scrollable Element Finder
This will help us identify the CORRECT element to scroll
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys


def find_scrollable_elements():
    """Find all scrollable elements on the page"""
    
    print("=" * 70)
    print("SCROLLABLE ELEMENT FINDER")
    print("=" * 70)
    print("\n⚠️  IMPORTANT: Close ALL Chrome windows before continuing!")
    print("(The script needs exclusive access to your Chrome profile)\n")
    input("Press ENTER when all Chrome windows are closed...")
    
    # Setup browser with your profile
    chrome_options = Options()
    user_data_dir = r"C:\Users\rtrin\AppData\Local\Google\Chrome\User Data"
    chrome_options.add_argument(f"user-data-dir={user_data_dir}")
    chrome_options.add_argument("--profile-directory=Default")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    print("\nStarting Chrome...")
    driver = webdriver.Chrome(options=chrome_options)
    
    print("=" * 70)
    print("SCROLLABLE ELEMENT FINDER")
    print("=" * 70)
    
    # Navigate to Drive
    print("\n1. Navigating to Google Drive...")
    driver.get('https://drive.google.com/drive/my-drive')
    time.sleep(5)
    
    print("\n2. Now:")
    print("   - Search for a file")
    print("   - Right-click it")
    print("   - Click 'View details'")
    print("   - Make sure the details pane is open on the right")
    print("\nPress ENTER when the details pane is visible...")
    input()
    
    print("\n3. Analyzing the page for scrollable elements...")
    
    # Find all potentially scrollable elements
    script = """
    let scrollableElements = [];
    let allElements = document.querySelectorAll('*');
    
    for (let elem of allElements) {
        let style = window.getComputedStyle(elem);
        let overflowY = style.overflowY;
        let scrollHeight = elem.scrollHeight;
        let clientHeight = elem.clientHeight;
        
        // Check if element can scroll
        if ((overflowY === 'auto' || overflowY === 'scroll') && scrollHeight > clientHeight) {
            let info = {
                tag: elem.tagName,
                classes: elem.className,
                id: elem.id,
                scrollHeight: scrollHeight,
                clientHeight: clientHeight,
                canScroll: scrollHeight - clientHeight,
                role: elem.getAttribute('role'),
                ariaLabel: elem.getAttribute('aria-label')
            };
            scrollableElements.push(info);
        }
    }
    
    return scrollableElements;
    """
    
    scrollable = driver.execute_script(script)
    
    print(f"\n✓ Found {len(scrollable)} scrollable elements:\n")
    
    for i, elem in enumerate(scrollable, 1):
        print(f"Element #{i}:")
        print(f"  Tag: {elem['tag']}")
        print(f"  Classes: {elem['classes'][:100]}")
        print(f"  ID: {elem['id']}")
        print(f"  Role: {elem['role']}")
        print(f"  Aria-label: {elem['ariaLabel']}")
        print(f"  scrollHeight: {elem['scrollHeight']}px")
        print(f"  clientHeight: {elem['clientHeight']}px")
        print(f"  Can scroll: {elem['canScroll']}px")
        print("-" * 70)
    
    print("\n4. Now let's try scrolling each one...\n")
    
    # Try scrolling each element
    for i in range(len(scrollable)):
        print(f"Testing element #{i+1}...")
        
        result = driver.execute_script(f"""
        let allElements = document.querySelectorAll('*');
        let scrollableElements = [];
        
        for (let elem of allElements) {{
            let style = window.getComputedStyle(elem);
            let overflowY = style.overflowY;
            if ((overflowY === 'auto' || overflowY === 'scroll') && elem.scrollHeight > elem.clientHeight) {{
                scrollableElements.push(elem);
            }}
        }}
        
        if (scrollableElements[{i}]) {{
            let elem = scrollableElements[{i}];
            let beforeScroll = elem.scrollTop;
            elem.scrollTop = elem.scrollHeight;
            let afterScroll = elem.scrollTop;
            return {{
                before: beforeScroll,
                after: afterScroll,
                worked: afterScroll > beforeScroll
            }};
        }}
        return null;
        """)
        
        if result and result['worked']:
            print(f"  ✓✓✓ ELEMENT #{i+1} SCROLLED! ✓✓✓")
            print(f"      Before: {result['before']}px, After: {result['after']}px")
            print(f"      This is probably the right one!")
        else:
            print(f"  ✗ Didn't scroll")
        
        time.sleep(1)
    
    print("\n5. Checking for specific Google Drive selectors...")
    
    selectors_to_try = [
        '[role="complementary"]',
        '.a-Ub-c',
        '[data-focus-id="DriveDetailsSidebarContainer"]',
        'div[role="dialog"]',
        '.drive-viewer-pane',
        'div[jsname]',
    ]
    
    for selector in selectors_to_try:
        try:
            elem = driver.find_element(By.CSS_SELECTOR, selector)
            info = driver.execute_script("""
                let elem = arguments[0];
                return {
                    scrollHeight: elem.scrollHeight,
                    clientHeight: elem.clientHeight,
                    scrollTop: elem.scrollTop,
                    overflowY: window.getComputedStyle(elem).overflowY
                };
            """, elem)
            
            print(f"\nSelector: {selector}")
            print(f"  Found: YES")
            print(f"  scrollHeight: {info['scrollHeight']}px")
            print(f"  clientHeight: {info['clientHeight']}px")
            print(f"  overflowY: {info['overflowY']}")
            print(f"  Scrollable: {info['scrollHeight'] > info['clientHeight']}")
            
        except:
            print(f"\nSelector: {selector}")
            print(f"  Found: NO")
    
    print("\n" + "=" * 70)
    print("Press ENTER to close browser...")
    input()
    
    driver.quit()


if __name__ == '__main__':
    find_scrollable_elements()