import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class StampDutyRateScraper:
    """
    Scrapes the latest UK stamp duty rates and rules from gov.uk
    """
    
    def __init__(self):
        self.base_url = "https://www.gov.uk"
        self.residential_rates_url = f"{self.base_url}/stamp-duty-land-tax/residential-property-rates"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_page(self, url: str) -> BeautifulSoup:
        """Fetch and parse a webpage"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_rate_table(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract stamp duty rate table from the page"""
        rates = []
        
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) > 1:
                headers = [th.get_text(strip=True) for th in rows[0].find_all(['th', 'td'])]
                
                if any('rate' in header.lower() or 'sdlt' in header.lower() for header in headers):
                    for row in rows[1:]:
                        cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                        if len(cells) >= 2:
                            rate_info = {
                                'band': cells[0],
                                'rate': cells[1] if len(cells) > 1 else '',
                                'raw_cells': cells
                            }
                            rates.append(rate_info)
        
        return rates
    
    def parse_monetary_value(self, text: str) -> Optional[int]:
        """Extract monetary value from text like '£125,000' or 'Up to £125,000'"""
        text = re.sub(r'^(up to|the next|the remaining amount|the portion from|the portion above)', '', text.lower())
        
        money_pattern = r'£([\d,]+(?:\.\d{2})?)'
        matches = re.findall(money_pattern, text)
        
        if matches:
            amount_str = matches[-1].replace(',', '')
            try:
                return int(float(amount_str))
            except ValueError:
                return None
        
        million_pattern = r'£?([\d.]+)\s*million'
        million_match = re.search(million_pattern, text.lower())
        if million_match:
            try:
                return int(float(million_match.group(1)) * 1000000)
            except ValueError:
                return None
        
        return None
    
    def parse_rate_percentage(self, text: str) -> Optional[float]:
        """Extract percentage rate from text like '5%' or 'Zero'"""
        if 'zero' in text.lower() or text.strip() == '':
            return 0.0
        
        percentage_pattern = r'(\d+(?:\.\d+)?)%'
        match = re.search(percentage_pattern, text)
        if match:
            return float(match.group(1)) / 100
        
        return None
    
    def extract_standard_rates(self, soup: BeautifulSoup) -> List[Tuple[int, float]]:
        """Extract standard residential property rates"""
        rates = []
        rate_tables = self.extract_rate_table(soup)
        
        for rate_info in rate_tables:
            threshold = self.parse_monetary_value(rate_info['band'])
            rate = self.parse_rate_percentage(rate_info['rate'])
            
            if threshold is not None and rate is not None:
                rates.append((threshold, rate))
        
        rates.sort(key=lambda x: x[0])
        return rates
    
    def extract_first_time_buyer_info(self, soup: BeautifulSoup) -> Dict:
        """Extract first-time buyer information"""
        ftb_info = {
            'nil_rate_threshold': None,
            'relief_threshold': None,
            'rates': []
        }
        
        text = soup.get_text()
        
        ftb_pattern = r'no SDLT up to £([\d,]+)'
        match = re.search(ftb_pattern, text)
        if match:
            ftb_info['nil_rate_threshold'] = int(match.group(1).replace(',', ''))
        
        relief_pattern = r'price is over £([\d,]+).*cannot claim.*relief'
        match = re.search(relief_pattern, text)
        if match:
            ftb_info['relief_threshold'] = int(match.group(1).replace(',', ''))
        
        return ftb_info
    
    def extract_additional_property_info(self, soup: BeautifulSoup) -> Dict:
        """Extract additional property surcharge information"""
        additional_info = {
            'surcharge_rate': None,
            'applies_to': []
        }
        
        text = soup.get_text()
        
        surcharge_patterns = [
            r'pay (\d+)% on top.*additional',
            r'(\d+)% surcharge.*additional property',
            r'(\d+)% on top.*SDLT rates.*additional'
        ]
        
        for pattern in surcharge_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                additional_info['surcharge_rate'] = float(match.group(1)) / 100
                break
        
        return additional_info
    
    def extract_examples(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract worked examples from the page"""
        examples = []
        
        example_sections = soup.find_all(['div', 'section'], class_=re.compile(r'example|calculation'))
        
        if not example_sections:
            text = soup.get_text()
            example_pattern = r'Example\s*\n(.*?)(?=Example|\n\n|$)'
            matches = re.findall(example_pattern, text, re.DOTALL | re.IGNORECASE)
            
            for match in matches:
                examples.append({
                    'type': 'text_example',
                    'content': match.strip()
                })
        
        return examples
    
    def get_latest_rates(self) -> Dict:
        """Main method to retrieve all current stamp duty information"""
        print("Fetching latest UK stamp duty rates from gov.uk...")
        
        soup = self.fetch_page(self.residential_rates_url)
        if not soup:
            return {"error": "Failed to fetch data from gov.uk"}
        
        standard_rates = self.extract_standard_rates(soup)
        ftb_info = self.extract_first_time_buyer_info(soup)
        additional_info = self.extract_additional_property_info(soup)
        examples = self.extract_examples(soup)
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'source_url': self.residential_rates_url,
            'standard_rates': standard_rates,
            'first_time_buyer': ftb_info,
            'additional_property': additional_info,
            'examples': examples,
            'raw_rate_data': self.extract_rate_table(soup)
        }
        
        return result
    
    def save_rates_to_file(self, filename: str = None) -> str:
        """Save the retrieved rates to a JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"uk_stamp_duty_rates_{timestamp}.json"
        
        rates_data = self.get_latest_rates()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(rates_data, f, indent=2, ensure_ascii=False)
        
        print(f"Rates saved to {filename}")
        return filename
    
    def format_rates_for_code(self, rates_data: Dict) -> str:
        """Format the extracted rates as Python code for the calculator"""
        if 'error' in rates_data:
            return f"# Error: {rates_data['error']}"
        
        code_lines = [
            "# UK Stamp Duty Rates - Auto-generated from gov.uk",
            f"# Retrieved: {rates_data['timestamp']}",
            f"# Source: {rates_data['source_url']}",
            "",
            "# Standard residential rates"
        ]
        
        if rates_data['standard_rates']:
            code_lines.append("standard_bands = [")
            for threshold, rate in rates_data['standard_rates']:
                code_lines.append(f"    ({threshold}, {rate}),")
            code_lines.append("]")
        
        if rates_data['first_time_buyer']['nil_rate_threshold']:
            ftb_threshold = rates_data['first_time_buyer']['nil_rate_threshold']
            code_lines.extend([
                "",
                "# First-time buyer rates",
                f"first_time_buyer_nil_threshold = {ftb_threshold}"
            ])
        
        if rates_data['additional_property']['surcharge_rate']:
            surcharge = rates_data['additional_property']['surcharge_rate']
            code_lines.extend([
                "",
                "# Additional property surcharge",
                f"additional_property_surcharge = {surcharge}"
            ])
        
        return "\n".join(code_lines)