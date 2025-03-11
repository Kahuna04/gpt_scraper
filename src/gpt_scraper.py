import os
import time
import csv
import argparse
import logging
import tempfile
import shutil
import getpass
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
import undetected_chromedriver as uc

# Configure logging with both file and console handlers
def setup_logging():
    logger = logging.getLogger('ChatGPTScraper')
    logger.setLevel(logging.DEBUG)

    # Create console handler with a higher log level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)

    # Create file handler for all logs
    file_handler = logging.FileHandler('chatgpt_scraper.log')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# Load environment variables for credentials
load_dotenv()

class ChatGPTScraper:
    """
    A class to automate interactions with ChatGPT using Selenium.
    Logs in, sends prompts, collects responses, and exports data to CSV.
    """

    def __init__(self, headless=False, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.logger.info("Initializing ChatGPT scraper")

        options = uc.ChromeOptions()
        if headless:
            self.logger.info("Running in headless mode")
            options.add_argument('--headless=new')

        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument("--window-size=800,600")

        # Create a temporary directory for user data
        self.temp_dir = tempfile.mkdtemp()
        self.logger.debug(f"Created temporary directory: {self.temp_dir}")
        options.add_argument(f'--user-data-dir={self.temp_dir}')

        try:
            self.logger.info("Setting up Chrome driver using undetected_chromedriver")
            self.driver = uc.Chrome(options=options)

            # Minimize the window if not in headless mode
            if not headless:
                self.logger.info("Minimizing browser window")
                self.driver.minimize_window

            # Set timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.set_script_timeout(30)
            self.driver.implicitly_wait(10)
            self.logger.debug("Timeouts set: page load=30s, script=30s, implicit wait=10s")

        except Exception as e:
            self.logger.error(f"Failed to initialize Chrome driver: {e}")
            raise

        self.session = requests.Session()
        self.conversation_data = []
        self.logger.info("ChatGPT scraper initialized successfully")

    def login(self, max_retries=3):
        """Log into ChatGPT with provided credentials using specific XPaths."""
        self.logger.info("Starting login process")
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Login attempt {attempt + 1} of {max_retries}")
                self.driver.get("https://chat.openai.com/auth/login")
                time.sleep(10)
                self.logger.debug("Page loaded, waiting 10 seconds")

                # Click the Log in button
                self.logger.info("Looking for login button")
                login_button = WebDriverWait(self.driver, 30).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='login-button']"))
                )
                login_button.click()
                self.logger.info("Clicked login button")

                # Wait for the login form to be visible
                self.logger.info("Waiting for login form to appear")
                WebDriverWait(self.driver, 30).until(
                    EC.visibility_of_element_located((By.XPATH, "/html/body/div/main/section/div[1]/h1"))
                )
                self.logger.info("Login form visible")

                # Enter email
                self.logger.info("Looking for email input field")
                email_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "email-input")) 
                )
                email_input.send_keys(os.getenv('EMAIL'))

                # Click Continue button
                self.logger.info("Looking for continue button")
                continue_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.NAME, "continue"))
                )
                continue_button.click()
                self.logger.info("Clicked continue after email")

                # Wait for password page header to be visible
                self.logger.info("Waiting for password page to load")
                WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, "//*[@id='auth0-widget']/main/section/div/div/header/h1"))
                )
                self.logger.info("Password page loaded")

                # Enter password
                self.logger.info("Looking for password input field")
                password_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "password"))
                )
                password_input.send_keys(os.getenv('PASSWORD'))

                # Click the continue button for password submission
                self.logger.info("Looking for password submit button")
                submit_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.NAME, "action"))
                )
                submit_button.click()
                self.logger.info("Clicked continue after password")

                # Wait for the chat interface to load
                self.logger.info("Waiting for chat interface to load")
                WebDriverWait(self.driver, 30).until(
                    EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/div/div[1]/div[2]/main/div[1]/div[2]/div/div/div/div/div[1]/div/div/div"))
                )
                self.logger.info("Successfully logged in! Chat interface loaded.")

                # Additional delay to ensure everything is fully loaded
                time.sleep(3)
                self.logger.debug("Waiting additional 3 seconds for complete load")
                return True

            except (TimeoutException, NoSuchElementException) as e:
                self.logger.error(f"Login attempt {attempt + 1} failed: {str(e)}")
                self.logger.debug(f"Current URL: {self.driver.current_url}")

                # Take screenshot on failure
                screenshot_path = f"login_error_attempt{attempt + 1}_{int(time.time())}.png"
                self.driver.save_screenshot(screenshot_path)
                self.logger.info(f"Screenshot saved to {screenshot_path}")

                if attempt < max_retries - 1:
                    self.logger.info(f"Retrying login (attempt {attempt + 2})...")
                    # Refresh the page for a clean retry
                    try:
                        self.driver.refresh()
                        time.sleep(3)
                    except:
                        self.logger.warning("Failed to refresh page, reloading entirely")
                        try:
                            self.driver.get("https://chat.openai.com/auth/login")
                            time.sleep(3)
                        except:
                            self.logger.error("Failed to reload page")
                else:
                    self.logger.error(f"All {max_retries} login attempts failed")
                    return False

        return False

    def send_prompt(self, prompt, max_retries=2, wait_timeout=20):
        """Send a prompt to ChatGPT, wait for complete response, and return it."""
        self.logger.info(f"Preparing to send prompt: {prompt[:50]}..." if len(prompt) > 50 else prompt)

        for attempt in range(max_retries):
            try:
                # Count existing responses before sending the prompt
                existing_responses = len(self.driver.find_elements(By.CSS_SELECTOR, "div.markdown"))
                self.logger.debug(f"Found {existing_responses} existing responses before sending prompt")

                # Find the input field and send the prompt
                self.logger.info("Looking for input textbox")
                input_field = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div#prompt-textarea"))
                )
                input_field.clear()
                self.logger.debug("Input field cleared")

                # Send prompt character by character for better visibility
                self.logger.info("Typing prompt character by character")
                for char in prompt:
                    input_field.send_keys(char)
                    time.sleep(0.01)
                self.logger.debug("Finished typing prompt")

                # Click the send button
                self.logger.info("Looking for send button")
                send_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='send-button']"))
                )
                send_button.click()
                self.logger.info("Prompt sent, waiting for response")

                # Wait for a new response to appear (response count increases)
                self.logger.info("Waiting for new response to appear...")

                def response_count_increased(driver):
                    current_count = len(driver.find_elements(By.CSS_SELECTOR, "div.markdown"))
                    return current_count > existing_responses

                WebDriverWait(self.driver, wait_timeout).until(response_count_increased)
                self.logger.info("New response detected")
                
                # Wait for the response to complete
                self.logger.info("Waiting for response to complete...")
                speech_button_selector = "button[data-testid='composer-speech-button']"
                WebDriverWait(self.driver, wait_timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, speech_button_selector))
                )
                self.logger.info("Composer speech button found - response is complete")

                # Small additional delay to ensure response is fully rendered
                time.sleep(2)

                # Get the last response from ChatGPT
                self.logger.info("Looking for response elements")
                responses = self.driver.find_elements(By.CSS_SELECTOR, "div.markdown")
                if responses:
                    latest_response = responses[-1].text
                    self.logger.info(f"Response received ({len(latest_response)} characters)")

                    # Store the conversation exchange
                    self.logger.debug("Storing conversation exchange")
                    self.conversation_data.append({
                        "role": "user",
                        "content": prompt
                    })
                    self.conversation_data.append({
                        "role": "ChatGPT",
                        "content": latest_response
                    })

                    return latest_response
                else:
                    self.logger.warning(f"No response found on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        self.logger.info("Retrying to get response...")
                        time.sleep(3)
                    else:
                        self.logger.error("All attempts to get response failed")
                        return None

            except (TimeoutException, NoSuchElementException) as e:
                self.logger.error(f"Error sending prompt (attempt {attempt + 1}): {str(e)}")

                if attempt < max_retries - 1:
                    self.logger.info(f"Retrying prompt (attempt {attempt + 2})...")
                    time.sleep(3)
                else:
                    return None

        return None

    def export_to_csv(self, output_file="output/chatgpt_conversation.csv"):
        """Export the conversation data to a CSV file with a unique timestamp."""
        self.logger.info(f"Preparing to export conversation to CSV")
        try:
            if not self.conversation_data:
                self.logger.warning("No conversation data to export")
                return False

            # Create a unique filename with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")

            # Extract base directory and filename parts
            output_dir = os.path.dirname(output_file)
            filename_base, filename_ext = os.path.splitext(os.path.basename(output_file))

            # Create new filename with timestamp
            unique_filename = f"{filename_base}_{timestamp}{filename_ext}"
            final_output_path = os.path.join(output_dir, unique_filename)

            self.logger.debug(f"Preparing to write {len(self.conversation_data)} entries to {final_output_path}")

            # Ensure directory exists
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                self.logger.debug(f"Created output directory: {output_dir}")

            with open(final_output_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Role", "Content"])
                self.logger.debug("Wrote header row")

                for entry in self.conversation_data:
                    writer.writerow([entry["role"], entry["content"]])
                    self.logger.debug(f"Wrote entry for {entry['role']}")

            self.logger.info(f"Conversation successfully exported to {final_output_path}")
            return final_output_path  # Return the actual path used
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {str(e)}")
            return False

    def close(self):
        """Close the browser and clean up resources."""
        self.logger.info("Preparing to close browser and clean up resources")
        if hasattr(self, 'driver'):
            self.logger.info("Waiting before closing browser")
            time.sleep(5)
            self.logger.info("Closing browser")
            try:
                self.driver.quit()
                self.logger.debug("Browser closed successfully")
            except Exception as e:
                self.logger.warning(f"Error closing browser: {e}")

        # Clean up the temporary directory
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            self.logger.info(f"Cleaning up temporary directory: {self.temp_dir}")
            try:
                shutil.rmtree(self.temp_dir)
                self.logger.debug("Temporary directory removed")
            except Exception as e:
                self.logger.warning(f"Error cleaning up temporary directory: {e}")

        self.logger.info("ChatGPT scraper closed successfully")


def main():
    """Main function to run the ChatGPT scraper from command line."""
    logger = setup_logging()
    logger.info("Starting ChatGPT Scraper Application")

    parser = argparse.ArgumentParser(description='ChatGPT Scraper')
    parser.add_argument('--email', type=str, help='ChatGPT login email')
    parser.add_argument('--password', type=str, help='ChatGPT login password')
    parser.add_argument('--prompt', type=str, help='Initial prompt to send to ChatGPT')
    parser.add_argument('--reply', type=str, help='Reply to ChatGPT\'s response')
    parser.add_argument('--output', type=str, default='output/chatgpt_conversation.csv', help='Output CSV file')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--wait-timeout', type=int, default=120, help='Timeout in seconds to wait for response completion')

    args = parser.parse_args()
    logger.info(f"Command line arguments processed")

    if args.debug:
        # Set log level to DEBUG if --debug flag is provided
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # Use environment variables, command line arguments, or prompt for input
    email = args.email or os.getenv('EMAIL')
    if not email:
        logger.info("Email not provided via arguments or environment, prompting user")
        email = input("Enter your email: ")

    password = args.password or os.getenv('PASSWORD')
    if not password:
        logger.info("Password not provided via arguments or environment, prompting user")
        password = getpass.getpass("Enter your password: ")

    initial_prompt = args.prompt
    if not initial_prompt:
        logger.info("Initial prompt not provided via arguments, prompting user")
        initial_prompt = input("Enter your initial prompt: ")

    # Initialize the scraper with headless mode preference
    headless_mode = args.headless
    logger.info(f"Running with UI {'hidden' if headless_mode else 'visible'}")

    scraper = None
    try:
        logger.info("Creating ChatGPTScraper instance")
        scraper = ChatGPTScraper(
            headless=headless_mode, 
            logger=logger
        )

        # Login
        logger.info("Attempting to login")
        if scraper.login(max_retries=3):
            logger.info("Login successful, proceeding with prompts")

            # Send initial prompt and get response
            logger.info("Sending initial prompt")
            initial_response = scraper.send_prompt(initial_prompt, max_retries=2, wait_timeout=args.wait_timeout)
            if initial_response:
                logger.info("Received response to initial prompt")
                print("\nChatGPT Response to Initial Prompt:")
                print("="*50)
                print(initial_response)
                print("="*50)

                # Ask for reply prompt if not provided
                reply_prompt = args.reply
                if not reply_prompt:
                    logger.info("Reply prompt not provided via arguments, prompting user")
                    reply_prompt = input("Enter your reply prompt: ")

                # Send reply prompt
                logger.info("Sending reply prompt")
                reply_response = scraper.send_prompt(reply_prompt, max_retries=2, wait_timeout=args.wait_timeout)
                if reply_response:
                    logger.info("Received response to reply prompt")
                    print("\nChatGPT Response to Reply:")
                    print("="*50)
                    print(reply_response)
                    print("="*50)
                else:
                    logger.warning("No response received to reply prompt")
            else:
                logger.warning("No response received to initial prompt")

            # Export conversation to CSV
            export_result = scraper.export_to_csv(args.output)
            if export_result:
                logger.info(f"Conversation exported to {export_result}")
                print(f"\nConversation exported to {export_result}")
        else:
            logger.error("Login failed, cannot proceed")
            print("ERROR: Failed to log in to ChatGPT. Check your credentials and try again.")

    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
        print("\nScript interrupted. Cleaning up...")

    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        print(f"ERROR: An unexpected error occurred: {e}")

    finally:
        logger.info("Cleaning up resources")
        if scraper:
            scraper.close()

        logger.info("ChatGPT Scraper execution completed")


if __name__ == "__main__":
    main()
