from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import time
import csv

def cookies(driver):
    driver.get("https://www.parcelforce.com")
    time.sleep(5) 

#--------------- (1) Read Postcodes from CSV File ---------------#

def read_postcodes_from_csv(PostcodeSample):
    postcodes = []
    with open(PostcodeSample, 'r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            postcodes.append(row[0])
    return postcodes



#------------------- (2) Define Parcel Sizes -------------------#

parcel_sizes = {
    "small": {"weight": "2", "length": "45", "width": "35", "height": "16"},
    "medium": {"weight": "20", "length": "61", "width": "46", "height": "46"},
    "large": {"weight": "30", "length": "150", "width": "50", "height": "50"}
                                                                    }


#---------------------- (3) Retrieve Quote ----------------------#

def get_quote(driver, collection_postcode, delivery_postcode, weight, length, width, height, parcel_size):
    driver.get("https://www.parcelforce.com")
    
    # Input collection postcode
    collection_postcode_input = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "qb-sender-postcode")))
    collection_postcode_input.send_keys(collection_postcode)
    
    # Input delivery postcode
    delivery_postcode_input = driver.find_element(By.ID, "qb-recipient-postcode")
    delivery_postcode_input.send_keys(delivery_postcode)
    
    # Input parcel details
    weight_input = driver.find_element(By.ID, "qb-weight-0")
    weight_input.send_keys(weight)
    
    length_input = driver.find_element(By.ID, "qb-depth-0")
    length_input.send_keys(length)
    
    width_input = driver.find_element(By.ID, "qb-width-0")
    width_input.send_keys(width)
    
    height_input = driver.find_element(By.ID, "qb-height-0")
    height_input.send_keys(height)
    
    # Click submit button
    button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div/div/div/div/div/div[2]/div[1]/div[1]/div/div/div/div/div[2]/form/div/div[2]/input")))
    button.click()
    
    return extract_quote(driver, parcel_size)

#------------------ (4) Extract Quote to Database ------------------#

def extract_quote(driver, parcel_size):
    quotes = {}

    xpaths = {
        "small": {
            "standard_drop_off": "/html/body/div[1]/div/div/div[1]/div[2]/div/div/div/div/div[1]/div[4]/div[2]/p[2]/span[1]/strong",
            "standard_door_to_door": "/html/body/div[1]/div/div/div[1]/div[2]/div/div/div/div/div[1]/div[2]/div[2]/p[2]/span[1]/strong",
            "next_day_drop_off": "/html/body/div[1]/div/div/div[1]/div[2]/div/div/div/div/div[2]/div[4]/div[2]/p[2]/span[1]/strong",
            "next_day_door_to_door": "/html/body/div[1]/div/div/div[1]/div[2]/div/div/div/div/div[2]/div[2]/div[2]/p[2]/span[1]/strong"
        },
        "medium": {
            "standard_drop_off": "/html/body/div[1]/div/div/div[1]/div[2]/div/div/div/div/div[1]/div[4]/div[2]/p[2]/span[1]/strong",
            "standard_door_to_door": "/html/body/div[1]/div/div/div[1]/div[2]/div/div/div/div/div[1]/div[2]/div[2]/p[2]/span[1]/strong",
            "next_day_drop_off": "/html/body/div[1]/div/div/div[1]/div[2]/div/div/div/div/div[2]/div[4]/div[2]/p[2]/span[1]/strong",
            "next_day_door_to_door": "/html/body/div[1]/div/div/div[1]/div[2]/div/div/div/div/div[2]/div[2]/div[2]/p[2]/span[1]/strong"
        },
        "large": {
            "standard_drop_off": "/html/body/div[1]/div/div/div[1]/div[2]/div/div/div/div/div[1]/div[3]/div[2]/p[2]/span[1]/strong",
            "standard_door_to_door": "/html/body/div[1]/div/div/div[1]/div[2]/div/div/div/div/div[1]/div[2]/div[2]/p[2]/span[1]/strong",
        }
    }

    parcel_xpaths = xpaths.get(parcel_size, {})
    for quote_type, xpath in xpaths.get(parcel_size, {}).items():
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
            quote_element = driver.find_element(By.XPATH, xpath)
            quote_value = quote_element.text
            quote_price = float(quote_value.replace('£', ''))
            quotes[quote_type] = quote_price
        except Exception as e:
            print(f"Error extracting quote for {quote_type}: {e}")
            quotes[quote_type] = None
        
    return quotes


#------------------ (5) Write Quote to CSV file ------------------#

def write_quotes_to_csv(quotes_list, output_file):
    with open(output_file, "w", newline="") as csvfile:
        fieldnames = ["Delivery Postcode", "Parcel Size", "STD Drop-off", "NDD Drop-off", "STD D2D", "NDD D2D"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for quote_values in quotes_list:
            writer.writerow(quote_values)


#------------------ (6) Running Web Scraper ------------------#

def main():
    driver = uc.Chrome(headless=False, use_subprocess=False)
    cookies(driver)
    postcodes = read_postcodes_from_csv("PostcodeSample.csv")
    results = []

    for postcode in postcodes:
        for size, dimensions in parcel_sizes.items():
            quotes = get_quote(driver, "N16 8AG", postcode, **dimensions, parcel_size=size)
            results.append({
                "Delivery Postcode": postcode,
                "Parcel Size": size,
                "STD Drop-off": quotes.get('standard_drop_off'),
                "NDD Drop-off": quotes.get('next_day_drop_off'),
                "STD D2D": quotes.get('standard_door_to_door'),
                "NDD D2D": quotes.get('next_day_door_to_door')
            })

    write_quotes_to_csv(results, "Parcelforce_quotes.csv")
    print("Quotes saved to Parcelforce_quotes.csv")
    driver.quit()

if __name__ == "__main__":
    main()