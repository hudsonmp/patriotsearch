import os
import csv
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
PASSWORD = os.getenv("PASSWORD")
EMAIL = os.getenv("EMAIL")
BASE_URL = "https://phantombuster.com"
LOGIN_URL = f"{BASE_URL}/login"
STORY_URL = "https://phantombuster.com/5545975669954255/phantoms/1614677465262538/console"
POST_URL = "https://phantombuster.com/5545975669954255/phantoms/4610526994730617/console"

# Ensure data directory exists
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

def wait_for_navigation_and_network_idle(page):
    """Wait for navigation and network to be idle."""
    page.wait_for_load_state("networkidle")
    page.wait_for_load_state("domcontentloaded")

def handle_cookie_consent(page):
    """Handle the cookie consent dialog if it appears."""
    try:
        # Look for common cookie consent buttons
        selectors = [
            'button:has-text("Accept")',
            'button:has-text("Accept all")',
            'button:has-text("Allow all")',
            '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll',
            '[aria-label*="Accept"]',
            '[data-testid*="cookie-accept"]'
        ]
        
        for selector in selectors:
            try:
                button = page.locator(selector)
                if button.is_visible(timeout=1000):
                    print(f"Found cookie button with selector: {selector}")
                    button.click()
                    page.wait_for_timeout(1000)
                    return
            except:
                continue
                
    except Exception as e:
        print(f"Note: Cookie handling failed (this is okay): {str(e)}")

def login_to_phantombuster(page):
    """Handle login to Phantombuster with enhanced error handling and verification."""
    print("Starting login process...")
    
    try:
        # Navigate to login page and wait for load
        print("Navigating to login page...")
        page.goto(LOGIN_URL, wait_until="networkidle")
        page.wait_for_timeout(2000)  # Give extra time for JS to load
        
        # Handle any cookie consent
        handle_cookie_consent(page)
        
        # Try to find login elements using multiple approaches
        print("Looking for login elements...")
        
        # First attempt - direct XPath
        email_selectors = [
            '//input[@type="email"]',
            '//input[@name="email"]',
            '//input[contains(@placeholder, "email")]',
            '//input[contains(@placeholder, "Email")]'
        ]
        
        password_selectors = [
            '//input[@type="password"]',
            '//input[@name="password"]',
            '//input[contains(@placeholder, "password")]',
            '//input[contains(@placeholder, "Password")]'
        ]
        
        button_selectors = [
            '//button[contains(text(), "Sign in")]',
            '//button[contains(text(), "Log in")]',
            '//button[@type="submit"]',
            '//button[contains(@class, "login")]',
            '//button[contains(@class, "signin")]'
        ]
        
        # Try each selector until we find the elements
        email_input = None
        password_input = None
        login_button = None
        
        print("Searching for email input...")
        for selector in email_selectors:
            try:
                element = page.locator(selector).first
                if element.is_visible(timeout=2000):
                    email_input = element
                    print(f"Found email input with: {selector}")
                    break
            except:
                continue
                
        print("Searching for password input...")
        for selector in password_selectors:
            try:
                element = page.locator(selector).first
                if element.is_visible(timeout=2000):
                    password_input = element
                    print(f"Found password input with: {selector}")
                    break
            except:
                continue
                
        print("Searching for login button...")
        for selector in button_selectors:
            try:
                element = page.locator(selector).first
                if element.is_visible(timeout=2000):
                    login_button = element
                    print(f"Found login button with: {selector}")
                    break
            except:
                continue
        
        # Verify we found all elements
        if not all([email_input, password_input, login_button]):
            raise Exception("Could not find all login elements")
            
        # Fill in the form
        print("Filling login form...")
        email_input.fill(EMAIL)
        page.wait_for_timeout(500)
        password_input.fill(PASSWORD)
        page.wait_for_timeout(500)
        
        # Click the button
        print("Clicking login button...")
        login_button.click()
        
        # Wait for navigation with multiple success paths
        print("Waiting for successful login...")
        page.wait_for_url(lambda url: "/phantoms" in url, timeout=30000)
        wait_for_navigation_and_network_idle(page)
        
        # Verify login success
        if "/phantoms" in page.url:
            print("Successfully logged in!")
            return True
        else:
            raise Exception("Login failed - not redirected to expected page")
            
    except Exception as e:
        print(f"Login failed: {str(e)}")
        try:
            page.screenshot(path="login_error.png")
            print(f"Error screenshot saved to login_error.png")
            with open("error_page.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            print("Saved error page HTML to error_page.html")
        except:
            print("Failed to save error debugging info")
        raise

def scroll_to_load_all_content(page):
    """Scroll page to load all content with enhanced waiting."""
    print("Starting content loading process...")
    
    try:
        # Initial wait for page load
        wait_for_navigation_and_network_idle(page)
        
        # Wait for table to be present using XPath
        page.wait_for_selector("//table", timeout=30000)
        
        print("Scrolling to load all content...")
        last_height = page.evaluate("document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 30
        
        while scroll_attempts < max_scroll_attempts:
            # Scroll to bottom
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            wait_for_navigation_and_network_idle(page)
            
            # Calculate new scroll height
            new_height = page.evaluate("document.body.scrollHeight")
            
            if new_height == last_height:
                scroll_attempts += 1
                if scroll_attempts >= 3:
                    break
            else:
                scroll_attempts = 0
                last_height = new_height
        
        print("Finished loading all content!")
        
    except Exception as e:
        print(f"Error during content loading: {str(e)}")
        raise

def extract_table_data(page):
    """Extract data from the table using XPath selectors."""
    print("Starting data extraction...")
    
    try:
        # Wait for table and verify it's visible
        table = page.locator("//table")
        expect(table).to_be_visible(timeout=30000)
        
        # Get headers with XPath
        headers = []
        header_cells = page.locator("//table//th").all()
        if not header_cells:
            raise Exception("No table headers found")
        
        for cell in header_cells:
            header_text = cell.inner_text().strip()
            if header_text:
                headers.append(header_text)
        
        print(f"Found {len(headers)} columns: {', '.join(headers)}")
        
        # Get data rows using XPath
        data = []
        rows = page.locator("//table//tr[position()>1]").all()  # Skip header row
        
        for row_idx, row in enumerate(rows, 1):
            cells = row.locator(".//td").all()
            row_data = {}
            
            for i, cell in enumerate(cells):
                if i < len(headers):
                    cell_text = cell.inner_text().strip()
                    row_data[headers[i]] = cell_text
            
            if row_data:
                data.append(row_data)
                if row_idx % 50 == 0:
                    print(f"Processed {row_idx} rows...")
        
        print(f"Extracted {len(data)} rows of data")
        return headers, data
        
    except Exception as e:
        print(f"Error during data extraction: {str(e)}")
        page.screenshot(path="extraction_error.png")
        print("Saved error screenshot to extraction_error.png")
        raise

def save_to_csv(data, headers, file_path):
    """Save extracted data to CSV file with error handling."""
    print(f"Saving data to {file_path}...")
    
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"Successfully saved {len(data)} rows to {file_path}")
        
    except Exception as e:
        print(f"Error saving data: {str(e)}")
        raise

def main():
    print("Starting Phantombuster data extraction...")
    
    # Validate environment variables
    if not EMAIL or not PASSWORD:
        raise ValueError("EMAIL and PASSWORD environment variables must be set")
    
    # Get user input for extraction type
    while True:
        extract_type = input("Enter extraction type (post/story): ").lower()
        if extract_type in ['post', 'story']:
            break
        print("Invalid input. Please enter 'post' or 'story'.")
    
    target_url = POST_URL if extract_type == 'post' else STORY_URL
    output_file = data_dir / f"{extract_type}_data.csv"
    
    with sync_playwright() as p:
        # Launch browser with specific options
        browser = p.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )
        
        # Create context with viewport and user agent
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        
        # Enable longer timeouts for stability
        context.set_default_timeout(30000)
        
        page = context.new_page()
        
        try:
            # Execute main workflow
            login_to_phantombuster(page)
            
            print(f"Navigating to {extract_type} page...")
            page.goto(target_url)
            wait_for_navigation_and_network_idle(page)
            
            scroll_to_load_all_content(page)
            headers, data = extract_table_data(page)
            save_to_csv(data, headers, output_file)
            
            print("Data extraction completed successfully!")
            
        except Exception as e:
            print(f"An error occurred during execution: {str(e)}")
            raise
            
        finally:
            print("Cleaning up...")
            context.close()
            browser.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Script failed: {str(e)}")
        exit(1)

