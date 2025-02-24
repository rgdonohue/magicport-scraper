# MagicPort Vessel Scraper

A Python-based web scraper for extracting vessel information from MagicPort.ai. This tool collects detailed information about fishing vessels, including their specifications, current location, and voyage information.

## Features

- Automated scraping of vessel information from MagicPort.ai
- Browser cookie authentication
- Detailed vessel information extraction including:
  - Vessel specifications
  - Current position
  - Voyage information
  - Country registration
  - Destination details
- CSV export functionality
- Configurable test mode for development
- Comprehensive logging system

## Requirements

- Python 3.x
- Required packages:
  - requests
  - beautifulsoup4
  - pandas
  - browser_cookie3

## Installation

To set up the MagicPort Vessel Scraper, follow these steps:

1. **Clone the Repository**: Use the following command to clone the repository to your local machine:
   ```bash
   git clone https://github.com/yourusername/magicport-vessel-scraper.git
   ```
   Replace `yourusername` with your GitHub username.

2. **Navigate to the Project Directory**: Change into the project directory:
   ```bash
   cd magicport-vessel-scraper
   ```

3. **Install Required Packages**: Ensure you have `pip` installed, then run:
   ```bash
   pip install -r requirements.txt
   ```
   This command will install all the necessary packages listed in the `requirements.txt` file.

4. **Verify Installation**: After installation, you can verify that the packages are installed correctly by running:
   ```bash
   pip list
   ```
   Ensure that `requests`, `beautifulsoup4`, `pandas`, and `browser_cookie3` are listed.

5. **Set Up Your Environment**: Make sure you have Python 3.x installed and configured properly on your system.

Now you are ready to use the scraper!

## Usage

1. Ensure you are logged into MagicPort.ai in your Chrome browser
2. Run the scraper:
```bash
python magicport-vessel-scraper.py
```

By default, this will scrape all available pages and save the results to `magicport_fishing_vessels_full.csv`.

### Test Mode

For development purposes, you can run the scraper in test mode by modifying the script:
```bash
scraper = MagicPortScraper(test_mode=True)
``` 

This will only scrape the first 3 pages and save to `test_vessels.csv`.

## Methodology

### Authentication
- Utilizes browser cookies from Chrome for authentication
- Automatically checks access permissions before scraping

### Scraping Process
1. **Page Navigation**
   - Determines total number of pages to scrape
   - Iterates through each page systematically

2. **Data Collection**
   - Extracts vessel cards from each page
   - Follows links to detailed vessel pages
   - Collects comprehensive vessel information:
     - General specifications
     - Vessel name
     - Country registration
     - Current position
     - Voyage information
     - Destination details

3. **Data Processing**
   - Cleans and standardizes field names
   - Structures data for CSV export
   - Handles missing data gracefully

### Rate Limiting
- Implements a 2-second delay between page requests
- Respects server resources

### Error Handling
- Comprehensive logging system
- Graceful handling of network errors
- Continues scraping even if individual vessel pages fail

## Output

The scraper generates a CSV file containing all vessel information with the following key fields:
- name
- mmsi
- imo
- call_sign
- vessel_type__sub_type
- gross_tonnage
- deadweight
- length
- year_built
- built_at_(shipyard)
- country
- url

## Limitations

- Requires active login session in Chrome browser
- Rate limited to respect server resources
- Dependent on MagicPort.ai's HTML structure

## Error Handling

The scraper includes comprehensive error handling and logging:
- Network request failures
- HTML parsing errors
- Missing data fields
- Authentication issues

All errors are logged with timestamps and detailed error messages.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

