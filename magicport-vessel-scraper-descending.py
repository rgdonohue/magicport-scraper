import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
from urllib.parse import urljoin
import browser_cookie3 
import re
from datetime import datetime, timedelta

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
        self.vessels_collected = 0
        self.target_count = 1027
        self.start_time = None
        self.vessels_per_minute = 0
        
        # Load Chrome cookies
        chrome_cookies = browser_cookie3.chrome(domain_name='magicport.ai')
        self.session.cookies.update(chrome_cookies)

    def estimate_completion(self):
        """Calculate estimated completion time based on current rate"""
        if not self.start_time or self.vessels_collected < 10:  # Need some data for meaningful estimate
            return "Calculating..."
            
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        self.vessels_per_minute = (self.vessels_collected / elapsed_time) * 60
        
        remaining_vessels = self.target_count - self.vessels_collected
        estimated_minutes = remaining_vessels / self.vessels_per_minute if self.vessels_per_minute > 0 else 0
        
        completion_time = datetime.now() + timedelta(minutes=estimated_minutes)
        
        return (f"Rate: {self.vessels_per_minute:.1f} vessels/min, "
                f"Est. completion: {completion_time.strftime('%H:%M:%S')}, "
                f"Est. time remaining: {int(estimated_minutes)} minutes")

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
                return None
            
            # Extract data from table rows
            rows = info_table.find_all('tr')
            for row in rows:
                header = row.find('th').text.strip()
                value = row.find('td').text.strip()
                field_name = header.lower().replace('/', '_').replace(' ', '_')
                details[field_name] = value
            
            # Get vessel name from h1 title
            name_elem = soup.find('h1')
            if name_elem:
                details['name'] = name_elem.text.strip()
            
            # Get country from flag text
            flag_text = soup.find('p', class_='text-style questions__item-content-message', string=lambda t: t and 'flag of' in t.lower())
            if flag_text:
                text = flag_text.text.strip()
                if "flag of" in text.lower():
                    after_flag = text.split("flag of", 1)[1].strip()
                    country_match = re.search(r'[A-Z]+(?:\s+[A-Z]+)*', after_flag)
                    if country_match:
                        country = country_match.group().title()
                        details['country'] = country
                    else:
                        details['country'] = '-'
                else:
                    details['country'] = '-'
            else:
                details['country'] = '-'
            
            # Get additional voyage information
            voyage_info = soup.find('div', string='Voyage Information')
            if voyage_info:
                voyage_section = voyage_info.find_parent('div')
                if voyage_section:
                    # Extract destination
                    dest_elem = voyage_section.find('div', string='Reported Destination')
                    if dest_elem:
                        details['reported_destination'] = dest_elem.find_next('div').text.strip()
                    
                    # Extract position
                    pos_elem = voyage_section.find('div', string='Latitude / Longitude')
                    if pos_elem:
                        details['position'] = pos_elem.find_next('div').text.strip()
                    
                    # Extract last position update
                    update_elem = voyage_section.find('div', string='Position Received')
                    if update_elem:
                        details['position_received'] = update_elem.find_next('div').text.strip()
            
            return details
            
        except Exception as e:
            logging.error(f"Error scraping vessel details from {vessel_url}: {str(e)}")
            return None

    def scrape_page(self, page_num, sort_type='desc'):
        """Scrape vessels from a single page"""
        if not self.start_time:
            self.start_time = datetime.now()
            
        url = f"{self.base_url}/vessels/fishing?page={page_num}&sort_type={sort_type}"
        
        try:
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all vessel cards
            vessel_cards = soup.find_all('div', {'class': 'card--vessel'})
            vessels_on_page = 0
            
            for card in vessel_cards:
                if self.vessels_collected >= self.target_count:
                    return False
                
                vessel_link = card.find('a', {'title': ' Vessel'})
                if vessel_link:
                    vessel_url = urljoin(self.base_url, vessel_link['href'])
                    vessel_details = self.get_vessel_details(vessel_url)
                    
                    if vessel_details:
                        self.vessels_data.append(vessel_details)
                        self.vessels_collected += 1
                        vessels_on_page += 1
            
            # Log progress after each page
            estimate = self.estimate_completion()
            logging.info(f"Page {page_num}: Added {vessels_on_page} vessels. "
                        f"Total: {self.vessels_collected}/{self.target_count}. {estimate}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error scraping page {page_num}: {str(e)}")
            return False

    def save_to_csv(self, filename='vessels_desc.csv'):
        """Save scraped data to CSV file, sorted alphabetically by name"""
        if not self.vessels_data:
            logging.error("No data to save")
            return
        
        # Convert to DataFrame and sort alphabetically by name
        df = pd.DataFrame(self.vessels_data)
        df = df.sort_values('name', ascending=True)
        
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
            for page in range(1, 4):
                logging.info(f"Scraping test page {page}")
                success = self.scrape_page(page)
                if not success:
                    break
                time.sleep(2)
            self.save_to_csv('test_vessels.csv')
            logging.info("Test scraping completed")
            return

        logging.info(f"Starting descending scrape to collect {self.target_count} vessels")
        page = 1
        while True:
            success = self.scrape_page(page, sort_type='desc')
            
            if not success:
                break
                
            page += 1
            time.sleep(2)
            
            if page % 20 == 0:
                self.save_to_csv(f'vessels_desc_progress_page{page}.csv')
        
        # Log final statistics
        total_time = datetime.now() - self.start_time
        final_rate = (self.vessels_collected / total_time.total_seconds()) * 60
        logging.info(f"Scraping completed. Total time: {total_time:.0f}, "
                    f"Final rate: {final_rate:.1f} vessels/min")
        
        # Final save of all data, sorted alphabetically
        self.save_to_csv('vessels_desc_final.csv')

if __name__ == "__main__":
    scraper = MagicPortScraper(test_mode=False)
    try:
        scraper.run()
    except Exception as e:
        logging.error(f"Scraping failed: {str(e)}") 