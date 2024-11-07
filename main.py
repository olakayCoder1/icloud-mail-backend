from flask import Flask , request
from flask_restful import Api , Resource
from flask_cors import CORS
# from scrape.helpers.icloud import ICloudManager
import uuid, threading , logging, traceback
from flask import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time , requests 

app = Flask(__name__)

api = Api(app)

CORS(app)




class ICloudManager:

    def __init__(self) -> None:
        pass

    def get_otp_from_json_file(self, identifier, attempt=12):
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
    

    def send_icloud_mail(self, data , **kwargs):

        
        email = data['email']
        password = data['password']
        identifier = data['identifier']
        password = data['password']
        title = data['subject']
        body = data['body']
        queue_id = data['queue_id']

        driver = webdriver.Chrome() 

        driver.get("https://www.icloud.com/mail/")


        # programmerolakay@icloud.com

        # Wait for the button to be clickable and then click it
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "sign-in-button"))).click()

        try:

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

        time.sleep(2)
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

                                # print(to_field.get_attribute('outerHTML'))
                                to_field.click()


                                # get the send button here

                                # Locate the textarea inside the to_field and wait for it to be clickable
                                textarea = to_field.find_element(By.CSS_SELECTOR, "textarea")
                                WebDriverWait(driver, 10).until(
                                    EC.element_to_be_clickable(textarea)
                                )
                                # Option 1: Use ActionChains to click and type
                                actions = ActionChains(driver)
                                actions.move_to_element(to_field).click().send_keys("olanrewaju@prembly.com").perform()

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
                                iframe = WebDriverWait(driver, 10).until(
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
                                new_modal = WebDriverWait(driver, 10).until(
                                    EC.visibility_of_element_located((By.CSS_SELECTOR, "ui-pane.modal"))
                                )
                                # Now, locate and click the 'Send' button
                                # First, find the send button by aria-label
                                # send_button = WebDriverWait(new_modal, 10).until(
                                #     EC.element_to_be_clickable((By.CSS_SELECTOR, "ui-button[aria-label='Send Message']"))
                                # )
                                # send_button.click()
                                # print("Clicked the 'Send Message' button.")
                                print(new_modal.get_attribute('outerHTML'))

                                # ui-activity-indicator



                                # confirm if the send botton is clickable 
                                buttons = WebDriverWait(new_modal, 10).until(
                                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ui-button"))
                                )
                                # Step 2: Loop through the buttons and click the one with the text "Send Message"
                                for button in buttons:
                                    print("********"*20)
                                    print(button.get_attribute('outerHTML'))
                                    # Check the aria-label or other attributes to match the button
                                    aria_label = button.get_attribute('aria-label')
                                    
                                    if aria_label == "Send Message":
                                        # Click the button
                                        button.click()
                                        print("Clicked the 'Send Message' button.")
                                        break  # Exit the loop after clicking the button


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
                    

        time.sleep(300)
        # driver.switch_to.default_content()
        # Close the browser
        driver.quit()




class IcloudMailSender(Resource):
    def post(self):
        data = request.get_json()
        required_fields = ["queue_id", "to", "subject", "body","email","password"]
        if not all(field in data for field in required_fields):
            return {"status": "error", "message": "Missing required fields"}, 400

        
        identifier = str(uuid.uuid4())
        # email_thread.start()
        data['identifier'] = identifier
        email_thread = threading.Thread(
            target=ICloudManager().send_icloud_mail, args=(data,),
            kwargs={}
        )
        email_thread.start()
        return {"status": "queued", "queue_id": data['queue_id'], 'identifier':identifier }, 202



class OTPSubmission(Resource):

    def post(self):
        data = request.get_json()
        required_fields = ["identifier", "otp"]
        if not all(field in data for field in required_fields):
            return {"status": False, "message": "Missing required fields"}, 400
        

        identifier = data["identifier"]
        otp = data["otp"]
        
        # Load existing OTP data from the JSON file
        try:
            with open("otp_credentials.json", "r") as f:
                otp_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            otp_data = {}  # Initialize an empty dict if the file doesn't exist or is invalid

        # Update the identifier key with the new OTP
        otp_data[identifier] = otp
        
        # Save the updated data back to the JSON file
        with open("otp_credentials.json", "w") as f:
            json.dump(otp_data, f, indent=4)
        


        return  {"status": True , "message": "OTP submitted successfully"}, 200
    

class HelloWorld(Resource):

    def get(self):
        return {'message': 'Hello, World!'}
    

api.add_resource(HelloWorld,"/")
api.add_resource(IcloudMailSender,"/send-webhook-mail")
api.add_resource(OTPSubmission,"/submit-otp")


if __name__ ==  '__main__':
    app.run(debug=True)  # run the app in debug mode