PASSWORD = "olakay@pyDev1"
email = "olakaycoder1@gmail.com"
from flask import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
import time , requests 



class ICloudManager:

    def __init__(self) -> None:
        pass

    def get_otp_from_json_file(self, identifier, attempt=5):
        otp = None
        while attempt > 0:
            try:
                with open("otp_credentials.json", "r") as f:
                    data = json.load(f)
                
                print(data)
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
    

    def send_icloud_mail(self, email, password , title , body, request_id , **kwargs):
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

        try:


            # Interacting with the otp session
            driver.switch_to.frame("aid-auth-widget") 


            # Get all input elements in the frame
            input_fields = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "input"))
            )

            # Iterate over each input element and interact with them
            for index, input_field in enumerate(input_fields):
                # Check if the element is visible and enabled before sending keys
                if input_field.is_displayed() and input_field.is_enabled():
                    # make api call to get  the otp from database
                    otp = self.get_otp_from_api(request_id)
                    if otp:
                        input_field.send_keys(otp)
                    else:
                        print("Failed to retrieve OTP after retries.")

                else:
                    print(f"Input field {index} is not interactable")
                    time.sleep(2)
                    if input_field.is_displayed() and input_field.is_enabled():
                        input_field.send_keys(index)
        finally:
            # Switch back to the main document
            driver.switch_to.default_content()



        time.sleep(5)
        # driver.switch_to.default_content()
        # Close the browser
        driver.quit()





res = ICloudManager().get_otp_from_json_file('1882821')