import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
from urllib.parse import urljoin
import browser_cookie3 
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class MagicPortScraper:
    def __init__(self, test_mode=False):
        self.base_url = 'https://magicport.ai'
        self.session = requests.Session()
        self.vessels_data = []
        self.test_mode = test_mode
        
        # Load Chrome cookies
        chrome_cookies = browser_cookie3.chrome(domain_name='magicport.ai')
        self.session.cookies.update(chrome_cookies)

    def test_access(self):
        """Test if we can access the vessels page"""
        try:
            response = self.session.get(f"{self.base_url}/vessels/fishing")
            if "Log in" in response.text:
                logging.error("Access denied - not logged in")
                return False
            logging.info("Successfully accessed vessels page")
            return True
        except Exception as e:
            logging.error(f"Error testing access: {str(e)}")
            return False

    def get_vessel_details(self, vessel_url):
        """Scrape detailed information for a single vessel"""
        try:
            response = self.session.get(vessel_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Initialize details dictionary with URL
            details = {'url': vessel_url}
            
            # Find the General Information table
            info_table = soup.find('table', {'class': 'table--prop'})
            if not info_table:
                logging.warning(f"Could not find general information table for {vessel_url}")
                return None
            
            # Extract data from table rows
            rows = info_table.find_all('tr')
            for row in rows:
                header = row.find('th').text.strip()
                value = row.find('td').text.strip()
                
                # Clean up field names by removing special characters and spaces
                field_name = header.lower().replace('/', '_').replace(' ', '_')
                details[field_name] = value
            
            # Get vessel name from h1 title
            name_elem = soup.find('h1')
            if name_elem:
                details['name'] = name_elem.text.strip()
            
            # Get country from flag text
            flag_text = soup.find('p', class_='text-style questions__item-content-message', text=lambda t: t and 'flag of' in t.lower())
            logging.info(f"Flag text element found: {flag_text is not None}")
            
            if flag_text:
                text = flag_text.text.strip()
                logging.info(f"Raw flag text: {text}")
                
                # Extract the capitalized text following "flag of"
                if "flag of" in text.lower():
                    # Get the text after "flag of"
                    after_flag = text.split("flag of", 1)[1].strip()
                    # Find all consecutive uppercase words
                    country_match = re.search(r'[A-Z]+(?:\s+[A-Z]+)*', after_flag)
                    if country_match:
                        # Convert country to title case (first letter of each word capitalized)
                        country = country_match.group().title()
                        logging.info(f"Extracted country: {country}")
                        details['country'] = country
                    else:
                        logging.info("No uppercase country name found")
                        details['country'] = '-'
                else:
                    logging.info("No 'flag of' found in text")
                    details['country'] = '-'
            else:
                logging.info("No flag text element found")
                details['country'] = '-'
            
            # Get additional voyage information
            voyage_info = soup.find('div', text='Voyage Information')
            if voyage_info:
                voyage_section = voyage_info.find_parent('div')
                if voyage_section:
                    # Extract destination
                    dest_elem = voyage_section.find('div', text='Reported Destination')
                    if dest_elem:
                        details['reported_destination'] = dest_elem.find_next('div').text.strip()
                    
                    # Extract position
                    pos_elem = voyage_section.find('div', text='Latitude / Longitude')
                    if pos_elem:
                        details['position'] = pos_elem.find_next('div').text.strip()
                    
                    # Extract last position update
                    update_elem = voyage_section.find('div', text='Position Received')
                    if update_elem:
                        details['position_received'] = update_elem.find_next('div').text.strip()
            
            logging.info(f"Successfully scraped details for vessel: {details.get('name', 'Unknown')}")
            return details
            
        except Exception as e:
            logging.error(f"Error scraping vessel details from {vessel_url}: {str(e)}")
            return None

    def scrape_page(self, page_num):
        """Scrape vessels from a single page"""
        url = f"{self.base_url}/vessels/fishing?page={page_num}"
        
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all vessel cards
            vessel_cards = soup.find_all('div', {'class': 'card--vessel'})
            
            for card in vessel_cards:
                # Get vessel URL from the "Show vessel" link
                vessel_link = card.find('a', {'title': ' Vessel'})
                if vessel_link:
                    vessel_url = urljoin(self.base_url, vessel_link['href'])
                    
                    # Get detailed vessel information
                    vessel_details = self.get_vessel_details(vessel_url)
                    if vessel_details:
                        self.vessels_data.append(vessel_details)
                        logging.info(f"Scraped vessel: {vessel_details.get('name', 'Unknown')}")
        
            return True
            
        except Exception as e:
            logging.error(f"Error scraping page {page_num}: {str(e)}")
            return False

    def get_total_pages(self):
        """Get total number of pages to scrape"""
        try:
            response = self.session.get(f"{self.base_url}/vessels/fishing")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find last page number from pagination
            pagination = soup.find('ul', {'class': 'pagination'})
            if not pagination:
                logging.error("Could not find pagination element")
                return None
            
            # Find all page links
            page_links = pagination.find_all('a', {'class': 'pagination__item-link'})
            logging.info(f"Found {len(page_links)} pagination links")
            
            # Look for the last numbered page (before the locked pages)
            for link in reversed(page_links):
                try:
                    page_num = int(link.text.strip())
                    logging.info(f"Found last page number: {page_num}")
                    return page_num
                except ValueError:
                    continue
            
            logging.error("Could not determine last page number")
            return None
            
        except Exception as e:
            logging.error(f"Error getting total pages: {str(e)}")
            return None

    def save_to_csv(self, filename='vessels.csv'):
        """Save scraped data to CSV file"""
        if not self.vessels_data:
            logging.error("No data to save")
            return
        
        df = pd.DataFrame(self.vessels_data)
        
        # Reorder columns to put name first and url last
        cols = df.columns.tolist()
        if 'name' in cols and 'url' in cols:
            cols.remove('name')
            cols.remove('url')
            cols = ['name'] + cols + ['url']
            df = df[cols]
        
        df.to_csv(filename, index=False)
        logging.info(f"Data saved to {filename}")

    def run(self):
        """Main scraping process"""
        if not self.test_access():
            return
            
        if self.test_mode:
            logging.info("Running in test mode - will scrape first 3 pages")
            for page in range(1, 4):  # Pages 1-3
                logging.info(f"Scraping test page {page}")
                success = self.scrape_page(page)
                if not success:
                    logging.error(f"Failed to scrape test page {page}")
                time.sleep(2)  # Be nice to the server
            self.save_to_csv('test_vessels.csv')
            logging.info("Test scraping completed")
            return
        
        total_pages = self.get_total_pages()
        if not total_pages:
            return
            
        logging.info(f"Starting scrape of {total_pages} pages")
        
        for page in range(1, total_pages + 1):
            logging.info(f"Scraping page {page} of {total_pages}")
            success = self.scrape_page(page)
            
            if not success:
                logging.error(f"Failed to scrape page {page}")
                continue
                
            # Be nice to the server
            time.sleep(2)
            
        self.save_to_csv()
        logging.info("Scraping completed")

if __name__ == "__main__":
    # No need for credentials when using browser cookies
    scraper = MagicPortScraper(test_mode=False)  # Switch to full scrape mode
    try:
        scraper.run()
        if scraper.vessels_data:  # Only save if we have data
            scraper.save_to_csv('magicport_fishing_vessels_full.csv')
    except Exception as e:
        logging.error(f"Scraping failed: {str(e)}") 