import selenium
import os
import time
import shutil
import warnings
import re
import mysql.connector

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.select import Select


class patientData:
    '''
    Quick obj. to store recorded patient data
        -- potential to build in data validation for missing information
    '''

    def __init__(self, site, subjectID, birthDate, sex, randID, previousTreatment, severity, status, cohort,
                 status_date):
        self.site = site
        self.subjectID = subjectID
        self.birthDate = birthDate
        self.sex = sex
        self.randID = randID
        self.previousTreatment = previousTreatment
        self.severity = severity
        self.cohort = cohort
        self.status = status
        self.status_date = status_date


def importChromeDriver():
    '''
    Manages the Selenium ChromeDriver and the relevant options/modifications
    :return:
    '''
    try:
        options = Options()

        # Standard installations for chromedriver operation
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-infobars')
        options.add_argument('--incognito')
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument('--disable-dev-shm-usage')
        options.add_experimental_option('prefs', {
            'download.default_directory': r'C:\Users\mdier\Downloads',
            'download.prompt_for_download': False,
            'download.directory_upgrade': False,
            'safebrowsing.enabled': True
        })

        # Testing purposed
        options.add_argument('--start-maximized')
        options.headless = False

        # Instantiate ChromeDriver Object
        driver = webdriver.Chrome('chromedriver.exe', options=options)
        driver.maximize_window()

        return driver, True
    except:
        raise warnings('Error building chrome webdriver - address before continuing')
        return None, False


def loginPage(driver):
    '''
    Manages the login to the test website
    :param driver: ChromeDriver
    :return: Chromedriver and progress report
    '''
    try:
        # Username and Password - in real life use cases this should be
        #       1) Protected either in a database, or at very minimum encrypted
        #       2) Up the user to input if those so choose to do so. Input Box in HTML, Login API, tkinter, etc

        user_credentials: dict = {'username': 'mattgdierker@gmail.com',
                                  'password': '12Cooper34!!',
                                  'loginURL': 'https://rtsm-val.veeva.com/VEV-901/'}

        # Navigate to the webpage
        driver.get(user_credentials['loginURL'])

        # Enter in user credentials
        username_field: str = '/html/body/form/table[2]/tbody/tr[1]/td[2]/input'
        username_element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, username_field)))
        username_element.send_keys(user_credentials['username'])

        password_field: str = '/html/body/form/table[2]/tbody/tr[2]/td[2]/input'
        password_element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, password_field)))
        password_element.send_keys(user_credentials['password'])

        # Locate the Proceed button
        proceed_field: str = '/html/body/form/div[8]/table/tbody/tr/td[2]/input'
        proceed_element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, proceed_field))).click()

        # Alternative if .click() isn't working - simply for the sake of demonstration
        # username_field: str = ''
        # username_element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, username_field)))
        # driver.execute_script('arguments[0].click();',username_element)

        return driver, True, user_credentials
    except:
        warnings.warn('Failure logging into web page - please ensure accuracy of username and password. If the error'
                      'still persists, please reach out a member of the Veeva Systems RTSM Team for assistance.')
        return driver, False, None


def subjectPage(driver):
    '''
    Downloads relevant data through the subject page
    :param driver: ChromeDriver
    :return: Chromedriver and progress report
    '''
    try:

        # Navigate to the subjects page
        subject_tab_field: str = '/html/body/form/table[2]/tbody/tr/td[1]/table/tbody/tr/td[1]/table/tbody/tr/td/a'
        subject_tab_element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, subject_tab_field)))
        subject_tab_element.click()

        # Data is luckily stored in a
        main_table_field = '/html/body/form/table[3]/tbody/tr[2]/td/div/table'
        main_table_element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, main_table_field)))

        # So we have different ways to go about stripping this data,
        # the first is to get it directly from the table on the landing page
        '''
        # Create list to store patient data objs.
        table_data: list = []
        for row in table_element.find_elements(By.CLASS_NAME, 'mygrid'):
            # Pull in all the col. data from the rows
            row_data: list = row.find_elements_by_tag_name('td')
            # Append data to list to store information
            table_data.append(patientData(row_data[1].text, row_data[2].text, row_data[3].text, row_data[4].text,
                                          row_data[5].text, row_data[6].text, row_data[7].text, row_data[8].text,
                                          row_data[9].text, row_data[10].text, row_data[11].text, row_data[12].text))
        '''

        # The second would be to export - depending on use cases this may save time with data formatting down the line
        '''
        subject_tab_field: str = '/html/body/form/table[3]/tbody/tr[1]/td/div/table/tbody/tr/td[1]/div/a[2]'
        subject_tab_element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, subject_tab_field)))
        subject_tab_element.click()
        '''

        # The third (and point of this would be to navigate through the loading screen - note that the more
        # screen that we open, the higher the risk of failure within the script if a page doesn't load
        row_index = 1
        table_data: list = []

        # Loop through the table rows
        for row in main_table_element.find_elements(By.CLASS_NAME, 'mygrid'):
            if row_index - 1 <= len(main_table_element.find_elements(By.CLASS_NAME, 'mygrid')):

                # Choose the menu item (triple dot) from each row by modifying the tr value
                menu_element = f'/html/body/form/table[3]/tbody/tr[2]/td/div/table/tbody/tr[{row_index}]/td[1]/a'
                menu_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, menu_element)))
                menu_element.click()

                # Swap to new pop-up window
                driver.switch_to_window(driver.window_handles[1])

                # Choose the menu item (triple dot) from each row by modifying the tr value
                view_information_field = f'lnkView2'
                view_information_element = WebDriverWait(driver, 30).until(
                    EC.visibility_of_element_located((By.ID, view_information_field))).click()

                # Wait for new popup - then switch to window
                time.sleep(1.5)
                driver.switch_to_window(driver.window_handles[1])

                sub_table_field: str = '/html/body/form/div[3]/table'
                sub_table_element = WebDriverWait(driver, 30).until(
                    EC.visibility_of_element_located((By.XPATH, sub_table_field)))

                # Append data to table
                table_rows = sub_table_element.find_elements(By.TAG_NAME, 'TR')

                # loop through the new pop-up table rows and append the data - these are variable in length
                tmp_dict: dict = {}
                for row_iterator in range(len(table_rows)):
                    # If the value is not already w/in the dictionary
                    if str(table_rows[row_iterator].find_elements(By.TAG_NAME, 'TD')[0].text) not in tmp_dict.keys():

                        # If there is a dropdown and no input tags as a row value
                        if len(table_rows[row_iterator].find_elements(By.TAG_NAME, 'SELECT')) >= 1 and len(
                                table_rows[row_iterator].find_elements(By.TAG_NAME, 'INPUT')) == 0:
                            value = ''
                            for select_option in table_rows[row_iterator].find_elements(By.TAG_NAME, 'SELECT'):
                                value = Select(select_option).first_selected_option.text
                            tmp_dict[
                                str(table_rows[row_iterator].find_elements(By.TAG_NAME, 'TD')[0].text).replace(':',
                                                                                                               '')] = value

                        # If there is a dropdown and input tags - i.e for a date
                        elif len(table_rows[row_iterator].find_elements(By.TAG_NAME, 'INPUT')) == 2 and len(
                                table_rows[row_iterator].find_elements(By.TAG_NAME, 'SELECT')) >= 1:

                            # Find Date
                            day_of_month = table_rows[row_iterator].find_elements(By.NAME, 'compBirthDate$txtDay')[
                                0].get_attribute('value')
                            # Find Month
                            for select_option in table_rows[row_iterator].find_elements(By.TAG_NAME, 'SELECT'):
                                month = Select(select_option).first_selected_option.text
                            # Find Year
                            year = table_rows[row_iterator].find_elements(By.NAME, 'compBirthDate$txtYear')[
                                0].get_attribute('value')
                            full_date: str = ' '.join([day_of_month, month, year])
                            tmp_dict[str(table_rows[row_iterator].find_elements(By.TAG_NAME, 'TD')[0].text).replace(':',
                                                                                                                    '')] = full_date
                        # For plain text drop downs
                        else:
                            tmp_dict[
                                str(table_rows[row_iterator].find_elements(By.TAG_NAME, 'TD')[0].text).replace(':',
                                                                                                               '')] = str(
                                table_rows[row_iterator].find_elements(By.CLASS_NAME, 'leftval')[0].text)
                    else:
                        pass

                # Fill in any missing data w/ None values - in prod we would want more reliable data handling
                data_points: list = ['Site Number', 'Subject ID', 'Date of Birth', 'Sex', 'Rand ID', 'Previous Treatment',
                                     'Severity', 'Cohort', 'Status', 'Status Date', 'Next Event']
                for column in data_points:
                    if column not in tmp_dict.keys():
                        tmp_dict[column] = None

                # Append patient data to list
                table_data.append(tmp_dict)

                # Leave popup
                driver.close()
                driver.switch_to_window(driver.window_handles[0])
                row_index += 1
            else:
                break

        return driver, True, table_data
    except:
        warnings.warn('Failure reading data on the subjects page')
        return driver, False, None


def adminPage(driver):
    '''
    Navigates to the admin Inventory page to capture a screenshot
    '''
    try:

        # Utilize action chain for hover button
        action = ActionChains(driver)
        admin_field: str = '/html/body/form/table[2]/tbody/tr/td[1]/table/tbody/tr/td[9]/table/tbody/tr/td/a'
        admin_element = driver.find_element_by_xpath(admin_field)
        action.move_to_element(admin_element).perform()

        # Find inventory link
        inventory_field: str = '/html/body/form/table[2]/tbody/tr/td[1]/div[1]/table/tbody/tr[3]/td/table/tbody/tr/td/a'
        inventory_element = driver.find_element_by_xpath(inventory_field)
        action.move_to_element(inventory_element).click().perform()

        # Wait for webpage to load
        inventory_on_screen: str = '/html/body/form/div[3]/table/tbody/tr/td/span'
        view_information_element = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, inventory_on_screen)))

        # Save screenshot
        file_name: str = 'IWouldLoveToBeAPartOfYourRTSMTeam.png'
        driver.save_screenshot(file_name)

        # Close out of the chrome driver
        driver.quit()
        return True, file_name
    except:
        warnings.warn('Error on the Admin page getting inventory information')
        return False, None


def exportData(user_credentials, data):
    '''
    Exports data from returned data table and inserts into mySQL database
    :param data: Dictionary Object
    :return:
    '''
    try:
        # Connect to mysql database
        db_connect = mysql.connector.connect(
            host="localhost",
            user='root',
            password='testpassword',
            database='technical_schema'
        )
        cursor = db_connect.cursor()

        if user_credentials is not None:

            # Search the database - if the user credentials aren't in there (I.e. PK not in use, insert data)
            user_cred_query = "SELECT username FROM credentials WHERE username  = %s"
            user_cred_pk = user_credentials['username']
            cursor.execute(user_cred_query, (user_cred_pk,))
            result = cursor.fetchone()

            if result is None:
                # SQL Insert Credentials
                insert_credentials_query = "INSERT INTO credentials (username, password, loginUrl) VALUES (%s, %s, %s)"
                user_credentials: list = ["mattgdierker@gmail.com", "12Cooper34!!", "https://rtsm-val.veeva.com/VEV-901/"]
                cursor.execute(insert_credentials_query, user_credentials)
                db_connect.commit()
                print('User credentials were inserted into the database')
            else:
                print('User credentials already exist')

        if data is not None:
            for patient_data in data:
                # Search the database - if the user credentials aren't in there (I.e. PK not in use, insert data)
                subject_query = "SELECT subjectID FROM data_pull WHERE subjectID = %s"
                subject_pk = patient_data['Subject ID']
                cursor.execute(subject_query, (subject_pk,))
                result = cursor.fetchone()

                if result is None:
                    # SQL Insert Credentials
                    insert_patient_query = "INSERT INTO data_pull (siteNumber, subjectID, DOB, sex, randID, " \
                                           "previousTreatment, severity, cohort, status, statusDate, nextEvent) VALUES (%s, %s, %s, %s, %s," \
                                           " %s, %s, %s, %s, %s, %s)"

                    patient_data: list = [patient_data['Site Number'], patient_data['Subject ID'], patient_data['Date of Birth'], patient_data['Sex'],
                                          patient_data['Rand ID'], patient_data['Previous Treatment'], patient_data['Severity'], patient_data['Cohort'],
                                          patient_data['Status'], patient_data['Status Date'], patient_data['Next Event']]

                    cursor.execute(insert_patient_query, patient_data)
                    db_connect.commit()
                    print('Patient data was inserted into the database')
                else:
                    print('Patient data already exists within the database')

        # Break connection
        cursor.close()
        db_connect.close()
        return True
    except:
        warnings.warn('Failure appending data to tables')
        return False


def portalDriver():
    '''
    Navigates through the test webportal and returns dataframe
    :return:
    '''

    progressing: bool = True
    while progressing is True:
        # Imports ChromeDriver Automation
        driver, progressing = importChromeDriver()

        # Navigates through the login page
        driver, progressing, user_credentials = loginPage(driver)

        # Downloads patient data
        driver, progressing, data = subjectPage(driver)

        # Captures screen shot of the admin page
        progressing, screenshot = adminPage(driver)

        # Exports data to mysql (localhost) db
        progressing = exportData(user_credentials, data)

        # kills the program
        progressing = False
    quit()

if __name__ == "__main__":
    portalDriver()
