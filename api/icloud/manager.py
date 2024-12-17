# type: ignore
import logging, traceback, threading
from flask import json 
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException,StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time , requests 
from flask import Blueprint

from api.icloud.models import Account
from ..helpers.utils import db


lock = threading.Lock()


class ICloudManager:

    def __init__(self):
        self.driver = None
        self.found_not_now_button = False

        # Initialize the browser on app start
        self.initialize_browser()

    
    def initialize_browser(self):
        """Start the browser session when the app starts."""
        # Set up Chrome options for headless mode (no GUI)
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run Chrome in headless mode
        chrome_options.add_argument("--no-sandbox")  # Necessary for environments like Docker
        chrome_options.add_argument("--disable-dev-shm-usage")  # Prevents issues in some environments

        try:
            # Initialize the WebDriver with the options
            # self.driver = webdriver.Chrome()      
            self.driver = webdriver.Chrome(options=chrome_options)
            print("Browser initialized successfully.")
        except Exception as e:
            logging.error(f"Error initializing the browser: {e}")
            self.driver = None


    def login_to_icloud(self, email, password, identifier):
        # with lock:
        # Set up Chrome options for headless mode
        if not self.driver:
            raise Exception("Browser is not initialized.")
        
        # chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Ensure Chrome runs in headless mode
        # chrome_options.add_argument("--no-sandbox")  # Necessary for environments like Docker
        # chrome_options.add_argument("--disable-dev-shm-usage")  # Prevents issues in some environments

        # Initialize the Chrome WebDriver with the options
        # self.driver = webdriver.Chrome()
        # self.driver = webdriver.Chrome()
        # self.driver = webdriver.Chrome(options=chrome_options)

        self.driver.get("https://www.icloud.com/mail/")

        # Wait for the button to be clickable and then click it
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "sign-in-button"))).click()
        email_send_is_successfull = False
        try:
            time.sleep(1)

            self.driver.switch_to.frame("aid-auth-widget") 

            input_field = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.TAG_NAME, "input"))
            )
            input_field.send_keys(email)

            button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "sign-in"))
            )
            button.click() 

            password_input_field = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, "password_text_field"))
            )
            password_input_field.send_keys(password)

            button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "sign-in"))
            )

            button.click() 
            

        finally:
            # Switch back to the main document
            self.driver.switch_to.default_content()

        time.sleep(3)
        otp = None
        # try:
        #     otp = ICloudManager().get_otp_from_json_file(identifier)
        #     # Interacting with the otp session
        #     self.driver.switch_to.frame("aid-auth-widget") 

        #     # Get all input elements in the frame
        #     input_fields = WebDriverWait(self.driver, 10).until(
        #         EC.presence_of_all_elements_located((By.TAG_NAME, "input"))
        #     )

        #     print(input_fields)
        #     print(otp)
        #     print(otp)
        #     print(otp)

        #     if otp:
        #         time.sleep(2)
        #         # Iterate over each input element and interact with them
        #         for index, input_field in zip(otp,input_fields):
        #             # Check if the element is visible and enabled before sending keys
        #             if input_field.is_displayed() and input_field.is_enabled():
        #                 input_field.send_keys(otp)
                        
        #             else:
        #                 print(f"Input field {index} is not interactable")
        #                 time.sleep(2)
        #                 if input_field.is_displayed() and input_field.is_enabled():
        #                     input_field.send_keys(otp)
        #     else:
        #         print("Failed to retrieve OTP after retries.")
        #         raise
        
        # finally:
        #     # Switch back to the main document
        #     self.driver.switch_to.default_content()
        # Retry fetching input fields if they become stale
        retry_attempts = 3
        otp = ICloudManager().get_otp_from_json_file(str(identifier))
        while retry_attempts > 0:
            try:
                self.driver.switch_to.frame("aid-auth-widget")
                # Get all input elements in the frame
                input_fields = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "input"))
                )

                print(input_fields)

                if otp and input_fields:
                    time.sleep(2)
                    # Iterate over each input element and interact with them
                    for index, input_field in zip(otp, input_fields):
                        try:
                            # Check if the element is visible and enabled before sending keys
                            if input_field.is_displayed() and input_field.is_enabled():
                                input_field.send_keys(otp)
                            else:
                                print(f"Input field {index} is not interactable")
                                time.sleep(2)
                                if input_field.is_displayed() and input_field.is_enabled():
                                    input_field.send_keys(otp)
                        except StaleElementReferenceException:
                            # If the element is stale, just retry fetching it and interacting with it
                            print(f"Input field {index} is stale, retrying...")
                            time.sleep(1)
                            retry_attempts -= 1
                            break  # Break the loop to retry fetching the elements
                    else:
                        break  # If no StaleElementReferenceException, exit the loop

                else:
                    print("Failed to retrieve OTP after retries.")
                    raise

            except Exception as e:
                print(f"Stale element reference exception: {e}")
                retry_attempts -= 1
                time.sleep(2)  # Optionally, wait before retrying
                if retry_attempts == 0:
                    raise e  # After all attempts, raise the exception if still stale
            finally:
                # Switch back to the main document
                self.driver.switch_to.default_content()

        time.sleep(5)
        
        if otp:
            try:
                # Interacting with the otp session
                self.driver.switch_to.frame("aid-auth-widget") 

                # Get all input elements in the frame
                button_fields = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "button"))
                )

                # Trust this browser? Question
                # Loop over each button and check if its text matches "Not Now"
                for button in button_fields:
                    if button.text.strip() == "Not Now":  
                        button.click() 
                        self.found_not_now_button = True
                        print("Clicked the 'Not Now' button in the main document.")
                        break 
            finally:
                # Switch back to the main document
                self.driver.switch_to.default_content()


    def send_email(self,email, subject, body ,queue_id):
        # with lock:
        if not self.driver:
            # raise Exception("No active WebDriver session. Please login first.")
            return self.send_notification_to_user(
                identifier=email,
                queue_id=queue_id,
                success=False,
                message="No active session login required"
            )
        
        email_send_is_successfull = False

        if self.found_not_now_button:
            try:
                # Try to locate and click the "New Message" button in the main document
                buttons = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "button"))
                )

                for button in buttons:
                    if button.text.strip() == "New Message":
                        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//button")))
                        button.click()
                        print("Clicked the 'New Message' button in the main document.")
                        break
                else:
                    # If "New Message" button is not found in the main document, switch to iframe and search there
                    print("Main document 'New Message' button not found. Switching to iframe.")
                    try:
                        # Switch to the iframe by its data-name attribute
                        WebDriverWait(self.driver, 10).until(
                            EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[data-name='mail2']"))
                        )
                        print("Switched to iframe with data-name='mail2'.")

                        # Locate the "Compose new message" button by its aria-label attribute
                        compose_button = WebDriverWait(self.driver, 20).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "ui-button[aria-label='Compose new message']"))
                        )
                        compose_button.click()
                        print("Clicked the 'Compose new message' button.")

                        time.sleep(10)
                        # send email
                        try:
                            # Wait for the overlay to disappear
                            WebDriverWait(self.driver, 10).until(
                                EC.invisibility_of_element_located((By.CSS_SELECTOR, "div[style*='opacity: 0.4']"))
                            )

                            modal = WebDriverWait(self.driver, 10).until(
                                EC.visibility_of_element_located((By.CSS_SELECTOR, "ui-pane.modal"))
                            )
                            # Wait for the ui-autocomplete-token-field element to be visible and clickable
                            to_field = WebDriverWait(modal, 10).until(
                                EC.visibility_of_element_located((By.CSS_SELECTOR, "ui-autocomplete-token-field[role='list']"))
                            )
                            to_field = WebDriverWait(modal, 10).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, "ui-autocomplete-token-field[role='list']"))
                            )

                            to_field.click()

                            # Locate the textarea inside the to_field and wait for it to be clickable
                            textarea = to_field.find_element(By.CSS_SELECTOR, "textarea")
                            WebDriverWait(self.driver, 10).until(
                                EC.element_to_be_clickable(textarea)
                            )
                            # Option 1: Use ActionChains to click and type
                            actions = ActionChains(self.driver)
                            # actions.move_to_element(to_field).click().send_keys("olanrewajuabdulkabeer@outlook.com").perform()
                            actions.move_to_element(to_field).click().send_keys(email).perform()

                            time.sleep(1)
                            subject_field_container = WebDriverWait(self.driver, 10).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, "ui-text-area"))
                            )
                            subject_field  = subject_field_container.find_element(By.CSS_SELECTOR, "textarea")
                            print("SUBJECT FIELD:::  ", subject_field)
                            subject_field.click()  # Click to focus on the "Subject" field
                            subject_field.send_keys(subject)  
                            time.sleep(1)
                            # Fill in the "Body" field
                            # Switch to the iframe to enter the email body
                            WebDriverWait(self.driver, 10).until(
                                EC.frame_to_be_available_and_switch_to_it((By.CLASS_NAME, "remote-ui-application-i-frame-view"))
                            )
                            print("Switched to iframe.")

                            # Locate the email body element inside the iframe
                            email_body_element = WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located(
                                    (By.CSS_SELECTOR, "div[role='textbox'][aria-label='Compose message body']")
                                )
                            )
                            print("Found the email body element.")

                            # Enter the email message
                            email_body_element.send_keys(body) 
                            print("Entered the email message.")
                            time.sleep(1)

                            self.driver.switch_to.parent_frame() 

                            modal_two = WebDriverWait(self.driver, 10).until(
                                EC.visibility_of_element_located((By.CSS_SELECTOR, "ui-pane.modal"))
                            )

                            # find the send message button and click it
                            send_button = WebDriverWait(modal_two, 10).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, "ui-button[aria-label='Send Message']"))
                            )

                            send_button.click()
                            time.sleep(15)


                            email_send_is_successfull = True

                            # send notification to user for successfull email sent 
                        except (TimeoutException, NoSuchElementException) as e:
                            logging.error(e)
                            logging.error(traceback.print_exc())
                            print(f"An element was not found or could not be interacted with: {e}")


                    except (TimeoutException, NoSuchElementException) as e:
                        logging.error(e)
                        logging.error(traceback.print_exc())
                        print(f"Could not find or click the 'Compose new message' button: {e}")
                    

            except (TimeoutException, NoSuchElementException) as e:
                logging.error(e)
                logging.error(traceback.print_exc())
                print(f"'New Message' button not found or not clickable: {e}")
                self.driver = None

            finally:
                self.driver.switch_to.default_content()
        
        else:
            driver.quit()
        
        return self.send_notification_to_user(
                identifier=email,
                queue_id=queue_id,
                success=email_send_is_successfull
            )

                        
            
    def close_session(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            return True


    def get_otp_from_json_file_old(self, identifier, attempt=12):
        otp = None
        while attempt > 0:
            try:
                with open("otp_credentials.json", "r") as f:
                    data = json.load(f)
                
                # print(data)
                valid_otp = data.get(identifier)  # Use 'identifier' here
                if valid_otp:
                    return valid_otp
                else:
                    raise ValueError("OTP not found for the given identifier.")
            except Exception as e:
                print(e)
                time.sleep(10)
                attempt -= 1  
                
        return otp

    
    def get_otp_from_json_file(self, identifier, attempt=12):
        otp = None
        while attempt > 0:
            try:
                # with lock:  # Use the lock to ensure thread safety
                with open("otp_credentials.json", "r") as f:
                    data = json.load(f)
            
                # print(data)
                valid_otp = data.get(identifier)  # Use 'identifier' here
                if valid_otp:
                    # Save the updated data back to the JSON file
                    data[identifier] = {
                        "otp":valid_otp.get("otp"),
                        "status": True
                    }
                    # # update the account to active if exist 
                    # account = Account.get_or_create(email=valid_otp['email'])
                    # account.is_active = True
                    # db.session.commit()

                    with open("otp_credentials.json", "w") as f:
                        json.dump(data, f, indent=4)

                    return valid_otp.get("otp")
                else:
                    raise ValueError("OTP not found for the given identifier.")
            except Exception as e:
                print(e)
                time.sleep(10)
                attempt -= 1
        return otp
    

    def remove_otp_from_json_file(self,identifier, attempt=3):
        while attempt > 0:
            try:
                # with lock:  # Use the lock to ensure thread safety
                with open("otp_credentials.json", "r") as f:
                    data = json.load(f)

                # delete the identifier from the data dict
                if identifier in data:
                    if data[identifier].get("status") == True:
                        del data[identifier]

                        with open("otp_credentials.json", "w") as f:
                            json.dump(data, f, indent=4)
                        
                        return True
                    
                else:
                    return False
                        
                    
            except Exception as e:
                print(e)
                attempt -1
                time.sleep(1)

        return False
    


    def add_otp_to_json_file(self,identifier, otp,email):
        # Load existing OTP data from the JSON file
        try:
            with open("otp_credentials.json", "r") as f:
                otp_data = json.load(f)
        except Exception as e:
            otp_data = {}  # Initialize an empty dict if the file doesn't exist or is invalid

        # Update the identifier key with the new OTP
        otp_data[identifier] = {
            "otp":otp,
            "email":email,
            "status": False
        }
        # Save the updated data back to the JSON file
        with open("otp_credentials.json", "w") as f:
            json.dump(otp_data, f, indent=4)




    def get_otp_from_api(self,request_id, retries=3):
        url = "https://your-api-url.com/get-otp" 
        payload = {'request_id': request_id}
        
        for attempt in range(retries):
            try:
                response = requests.post(url, json=payload)
                response.raise_for_status()  # Raise an error for bad responses
                return response.json().get('otp')  # Adjust according to your API response
            except requests.RequestException as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2)  # Wait before retrying
        return None  # Return None if all attempts fail
    


    def send_notification_to_user(self, identifier, queue_id, success , **kwargs):
        response = {
            "success": success,
            "message": kwargs.get("message",''),
            "identifier": identifier,
            "queue_id": queue_id,
            "email":kwargs.get("email")
        }
        return response


    def send_icloud_mail(self, data , **kwargs):

        
        email = data['email']
        password = data['password']
        identifier = data['identifier']
        title = data['subject']
        body = data['body']
        queue_id = data['queue_id']

        # Set up Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Ensure Chrome runs in headless mode
        chrome_options.add_argument("--no-sandbox")  # Necessary for environments like Docker
        chrome_options.add_argument("--disable-dev-shm-usage")  # Prevents issues in some environments

        # Initialize the Chrome WebDriver with the options
        driver = webdriver.Chrome(options=chrome_options)

        driver.get("https://www.icloud.com/mail/")

        # Wait for the button to be clickable and then click it
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "sign-in-button"))).click()
        email_send_is_successfull = False
        try:
            time.sleep(1)

            driver.switch_to.frame("aid-auth-widget") 

            input_field = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.TAG_NAME, "input"))
            )
            input_field.send_keys(email)

            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "sign-in"))
            )
            button.click() 

            password_input_field = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "password_text_field"))
            )
            password_input_field.send_keys(password)

            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "sign-in"))
            )

            button.click() 
            

        finally:
            # Switch back to the main document
            driver.switch_to.default_content()

        time.sleep(3)
        otp = None
        try:
            otp = ICloudManager().get_otp_from_json_file(identifier)
            # Interacting with the otp session
            driver.switch_to.frame("aid-auth-widget") 

            # Get all input elements in the frame
            input_fields = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "input"))
            )

            if otp:
                # Iterate over each input element and interact with them
                for index, input_field in zip(otp,input_fields):
                    # Check if the element is visible and enabled before sending keys
                    if input_field.is_displayed() and input_field.is_enabled():
                        input_field.send_keys(otp)
                        time.sleep(1)
                        break
                        
                    else:
                        print(f"Input field {index} is not interactable")
                        time.sleep(2)
                        if input_field.is_displayed() and input_field.is_enabled():
                            input_field.send_keys(otp)
            else:
                print("Failed to retrieve OTP after retries.")
                raise
           
        finally:
            # Switch back to the main document
            driver.switch_to.default_content()

        time.sleep(5)
        
        if otp:
            found_not_now_button = False
            try:
                # Interacting with the otp session
                driver.switch_to.frame("aid-auth-widget") 

                # Get all input elements in the frame
                button_fields = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "button"))
                )

                # Trust this browser? Question
                # Loop over each button and check if its text matches "Not Now"
                for button in button_fields:
                    if button.text.strip() == "Not Now":  
                        button.click() 
                        found_not_now_button = True
                        print("Clicked the 'Not Now' button in the main document.")
                        break 
            finally:
                # Switch back to the main document
                driver.switch_to.default_content()

            if found_not_now_button:
                try:
                    # Try to locate and click the "New Message" button in the main document
                    buttons = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.TAG_NAME, "button"))
                    )

                    for button in buttons:
                        if button.text.strip() == "New Message":
                            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, ".//button")))
                            button.click()
                            print("Clicked the 'New Message' button in the main document.")
                            break
                    else:
                        # If "New Message" button is not found in the main document, switch to iframe and search there
                        print("Main document 'New Message' button not found. Switching to iframe.")
                        try:
                            # Switch to the iframe by its data-name attribute
                            WebDriverWait(driver, 10).until(
                                EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[data-name='mail2']"))
                            )
                            print("Switched to iframe with data-name='mail2'.")

                            # Locate the "Compose new message" button by its aria-label attribute
                            compose_button = WebDriverWait(driver, 15).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, "ui-button[aria-label='Compose new message']"))
                            )
                            compose_button.click()
                            print("Clicked the 'Compose new message' button.")

                            time.sleep(10)
                            # send email
                            try:
                                # Wait for the overlay to disappear
                                WebDriverWait(driver, 10).until(
                                    EC.invisibility_of_element_located((By.CSS_SELECTOR, "div[style*='opacity: 0.4']"))
                                )

                                modal = WebDriverWait(driver, 10).until(
                                    EC.visibility_of_element_located((By.CSS_SELECTOR, "ui-pane.modal"))
                                )
                                # Wait for the ui-autocomplete-token-field element to be visible and clickable
                                to_field = WebDriverWait(modal, 10).until(
                                    EC.visibility_of_element_located((By.CSS_SELECTOR, "ui-autocomplete-token-field[role='list']"))
                                )
                                to_field = WebDriverWait(modal, 10).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, "ui-autocomplete-token-field[role='list']"))
                                )

                                to_field.click()

                                # Locate the textarea inside the to_field and wait for it to be clickable
                                textarea = to_field.find_element(By.CSS_SELECTOR, "textarea")
                                WebDriverWait(driver, 10).until(
                                    EC.element_to_be_clickable(textarea)
                                )
                                # Option 1: Use ActionChains to click and type
                                actions = ActionChains(driver)
                                actions.move_to_element(to_field).click().send_keys("olanrewajuabdulkabeer@outlook.com").perform()
                                # actions.move_to_element(to_field).click().send_keys("olanrewaju@prembly.com").perform()

                                time.sleep(1)
                                subject_field_container = WebDriverWait(driver, 10).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, "ui-text-area"))
                                )
                                subject_field  = subject_field_container.find_element(By.CSS_SELECTOR, "textarea")
                                print("SUBJECT FIELD:::  ", subject_field)
                                subject_field.click()  # Click to focus on the "Subject" field
                                subject_field.send_keys(title)  
                                time.sleep(1)
                                # Fill in the "Body" field
                                # Switch to the iframe to enter the email body
                                WebDriverWait(driver, 10).until(
                                    EC.frame_to_be_available_and_switch_to_it((By.CLASS_NAME, "remote-ui-application-i-frame-view"))
                                )
                                print("Switched to iframe.")

                                # Locate the email body element inside the iframe
                                email_body_element = WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located(
                                        (By.CSS_SELECTOR, "div[role='textbox'][aria-label='Compose message body']")
                                    )
                                )
                                print("Found the email body element.")

                                # Enter the email message
                                email_body_element.send_keys(body) 
                                print("Entered the email message.")
                                time.sleep(1)

                                driver.switch_to.parent_frame() 

                                modal_two = WebDriverWait(driver, 10).until(
                                    EC.visibility_of_element_located((By.CSS_SELECTOR, "ui-pane.modal"))
                                )

                                # find the send message button and click it
                                send_button = WebDriverWait(modal_two, 10).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, "ui-button[aria-label='Send Message']"))
                                )

                                send_button.click()
                                time.sleep(15)


                                email_send_is_successfull = True


                                # send notification to user for successfull email sent 


                            except (TimeoutException, NoSuchElementException) as e:
                                logging.error(e)
                                logging.error(traceback.print_exc())
                                print(f"An element was not found or could not be interacted with: {e}")
                            

                        except (TimeoutException, NoSuchElementException) as e:
                            logging.error(e)
                            logging.error(traceback.print_exc())
                            print(f"Could not find or click the 'Compose new message' button: {e}")

                        

                except (TimeoutException, NoSuchElementException) as e:
                    logging.error(e)
                    logging.error(traceback.print_exc())
                    print(f"'New Message' button not found or not clickable: {e}")

                finally:

                    driver.quit()
            
            else:
                driver.quit()

                    

        time.sleep(30)
        # driver.switch_to.default_content()
        # Close the browser
        driver.quit()


        self.send_notification_to_user(
            identifier=identifier,
            queue_id=queue_id,
            success=email_send_is_successfull
        )
        

