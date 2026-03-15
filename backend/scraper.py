#!/usr/bin/env python3
"""
Municipal Data Scraper for Chatbot Knowledge Base
Scrapes Kitchener/Waterloo region municipal websites
"""
import os
import sys
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin
from typing import List, Dict, Tuple
import time

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
DOCS_DIR = DATA_DIR / "documents"
CHROMA_DIR = DATA_DIR / "chroma_db"

# URLs to scrape
SCRAPE_URLS = [
    {
        "url": "https://www.regionofwaterloo.ca/en/living-here/garbage.aspx",
        "category": "garbage",
        "filename": "region_garbage.txt"
    },
    {
        "url": "https://www.kitchener.ca/en/parking.aspx",
        "category": "parking",
        "filename": "kitchener_parking.txt"
    },
    {
        "url": "https://www.kitchener.ca/en/parking/parking-tickets.aspx",
        "category": "parking",
        "filename": "parking_tickets.txt"
    },
    {
        "url": "https://www.kitchener.ca/en/bylaws-and-enforcement/parking-bylaws.aspx",
        "category": "bylaws",
        "filename": "parking_bylaws.txt"
    },
    {
        "url": "https://www.kitchener.ca/en/bylaws-and-enforcement/how-to-report-a-problem-or-make-a-bylaw-complaint.aspx",
        "category": "bylaws",
        "filename": "report_bylaw.txt"
    },
    {
        "url": "https://www.kitchener.ca/en/development-and-construction/apply-for-a-building-permit.aspx",
        "category": "permits",
        "filename": "building_permits.txt"
    },
    {
        "url": "https://www.kitchener.ca/en/development-and-construction/building-permit-fees.aspx",
        "category": "permits",
        "filename": "permit_fees.txt"
    },
    {
        "url": "https://www.kitchener.ca/taxes-utilities-and-finance/property-taxes/paying-your-taxes/",
        "category": "taxes",
        "filename": "property_taxes.txt"
    },
    {
        "url": "https://www.kitchener.ca/en/contact-us.aspx",
        "category": "contact",
        "filename": "contact_us.txt"
    },
    {
        "url": "https://www.kitchener.ca/living-in-kitchener/leaves-snow-and-garbage/",
        "category": "garbage",
        "filename": "yard_waste.txt"
    }
]


def fetch_page(url: str, timeout: int = 30) -> Tuple[str, str]:
    """
    Fetch a webpage and return title and content.
    
    Returns:
        Tuple of (title, content)
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Get title
        title = ""
        if soup.title:
            title = soup.title.string or ""
        elif soup.find('h1'):
            title = soup.find('h1').get_text(strip=True)
        
        # Remove unwanted elements
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()
        
        # Get main content
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup.body
        
        if main_content:
            # Get text content
            text = main_content.get_text(separator='\n', strip=True)
            # Clean up whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            content = '\n'.join(lines)
        else:
            content = soup.get_text(separator='\n', strip=True)
        
        return title, content
        
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return "", ""


def clean_content(content: str, max_length: int = 10000) -> str:
    """Clean and truncate content"""
    # Remove excessive whitespace
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    content = '\n'.join(lines)
    
    # Truncate if too long
    if len(content) > max_length:
        content = content[:max_length] + "\n\n[Content truncated...]"
    
    return content


def save_document(filename: str, title: str, content: str, url: str):
    """Save content to a text file"""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    
    filepath = DOCS_DIR / filename
    
    # Add source reference at top
    full_content = f"""Source: {url}
Title: {title}
Category: municipal_services

{content}
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    print(f"Saved: {filepath} ({len(content)} chars)")


def scrape_all(delay: float = 1.0) -> List[Dict]:
    """
    Scrape all configured URLs.
    
    Args:
        delay: Delay between requests in seconds
    
    Returns:
        List of scraped document info
    """
    results = []
    
    for item in SCRAPE_URLS:
        url = item["url"]
        filename = item["filename"]
        
        title, content = fetch_page(url)
        
        if content:
            content = clean_content(content)
            save_document(filename, title, content, url)
            
            results.append({
                "url": url,
                "filename": filename,
                "title": title,
                "content_length": len(content)
            })
        
        # Respectful delay
        time.sleep(delay)
    
    return results


def create_sample_documents():
    """Create sample documents if scraping fails"""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    
    samples = [
        ("garbage_schedule.txt", """Garbage and Recycling Schedule - City of Kitchener

Weekly Collection: Garbage is collected weekly on your designated collection day. Place bins at the curb by 7:00 AM.

Blue Box Recycling: Place blue box at the curb on your collection day. Accepts paper, cardboard, glass, plastic, and metal.

Green Bin: Organic waste is collected weekly. Includes food scraps, yard waste, soiled paper.

Large Items: Collection available for large items. Call 519-741-2345 to schedule.

Holiday Schedule: No collection on Christmas Day, New Year's Day. Check website for schedule.

Contact: 519-741-2345 or visit kitchener.ca/waste"""),
        
        ("parking_tickets.txt", """Parking Tickets - City of Kitchener

Payment Options:
- Online: kitchener.ca/parking
- In Person: City Hall, 200 King St W
- By Phone: 519-741-2345

Payment Deadline: 30 days from issue date

Penalties:
- First 7 days: Pay early amount to reduce fine
- After 30 days: Additional penalties may apply
- After 60 days: Vehicle may be booted or towed

Disputes:
- Submit a Parking Ticket Review Request online
- Or file an appeal in person at City Hall
- Must file within 30 days of ticket date

Overnight Parking: No overnight street parking without permit (Dec 1 - Mar 31)"""),
        
        ("parking_bylaws.txt", """Parking Bylaws - City of Kitchener

No Parking Zones:
- Within 3 meters of a fire hydrant
- Within 6 meters of an intersection
- On sidewalks or crosswalks
- In front of driveways
- In designated no parking zones

Accessible Parking:
- Must display valid accessible parking permit
- Only park in designated accessible spaces
- Violation fine: $300+

Fire Routes:
- No stopping or standing in fire routes
- Violation fine: $400+

Commercial Vehicles:
- No parking of commercial vehicles on residential streets overnight
- Maximum 6 hours in residential areas"""),
        
        ("building_permits.txt", """Building Permits - City of Kitchener

When Permits Required:
- New construction
- Renovations over $10,000 value
- Structural changes
- Electrical work
- Plumbing
- HVAC installation
- Decks over 10 sq meters
- Swimming pools

Application Process:
1. Complete application form
2. Submit required drawings/documents
3. Pay permit fees
4. Schedule inspections

Required Documents:
- Site plan
- Floor plans
- Elevation drawings
- Structural calculations (if applicable)
- Energy efficiency compliance

Processing Time: 10-15 business days (typical)

Fees: Based on project value. Use online fee calculator at kitchener.ca/permits

Contact: Building Division 519-741-2328"""),
        
        ("property_taxes.txt", """Property Taxes - City of Kitchener

Payment Methods:
- Online: kitchener.ca/taxes (credit card, debit, e-transfer)
- In Person: City Hall, 200 King St W
- By Mail: PO Box 1118, Station G, Kitchener ON N2G 4G7
- Pre-authorized payment plan
- Bank/Financial Institution: Add as payee

Tax Due Dates:
- Interim: Last day of January, March, May, July
- Final: Last day of September

Installments: Quarterly installments available

Assessment: MPAC (Municipal Property Assessment Corporation) handles property assessments

Appeals: File with MPAC for assessment appeals

Contact: 519-741-2345 or taxes@kitchener.ca"""),
        
        ("contact_us.txt", """Contact City of Kitchener

General Inquiries: 519-741-2345

City Hall:
- Address: 200 King Street West, Kitchener, ON N2G 4G7
- Hours: Monday-Friday 8:30 AM - 4:30 PM

Department Phone Numbers:
- Building Permits: 519-741-2328
- Parking: 519-741-2310
- Taxes: 519-741-2345
- By-Law Enforcement: 519-741-2325
- Garbage/Recycling: 519-741-2345
- Water: 519-741-2345

Online: kitchener.ca
Email: contact@kitchener.ca

Emergency After Hours: 519-741-2345 (for urgent issues only)

Region of Waterloo: 519-575-4400
Police (non-emergency): 519-653-7700
Fire (non-emergency): 519-741-0191"""),
        
        ("report_bylaw.txt", """Reporting Bylaw Violations - City of Kitchener

What to Report:
- Noise complaints
- Property standards violations
- Parking violations
- Illegal dumping
- Unlicensed businesses
- Animal complaints
- Snow/ice violations

How to Report:
1. Online: kitchener.ca/report (fastest method)
2. Phone: 519-741-2325
3. In Person: City Hall

Information Needed:
- Location of violation
- Description of issue
- Date/time observed
- Photos (if possible)
- Your contact info (optional but helps follow-up)

Response Time: Typically 3-5 business days

Anonymous Reports: Accepted but may delay investigation"""),
        
        ("permit_fees.txt", """Building Permit Fees - City for Kitchener

Fee Calculation: Based on the value of the construction project.

Residential:
- New construction: $1.50 per $1,000 of value
- Renovations: $1.50 per $1,000 of value
- Decks/Sheds: Flat fee based on size
- Pools: $200 flat fee

Commercial:
- New construction: $1.75 per $1,000 of value
- Renovations: $1.50 per $1,000 of value
- Tenant improvements: $1.25 per $1,000 of value

Other Fees:
- Permit review deposit: 50% of estimated fees
- Additional inspections: $75 per inspection
- Permit revision: $75 minimum
- Conditional permit: Additional 25%

Minimum Fee: $75 for most permits

Use online fee calculator: kitchener.ca/building-fees"""),
        
        ("yard_waste.txt", """Yard Waste and Seasonal Collection - Kitchener

Yard Waste Collection:
- April - November: Weekly collection
- December - March: Every two weeks

Accepted Items:
- Leaves
- Grass clippings
- Tree branches (bundled)
- Garden plants
- Fruit/vegetable scraps

Packaging:
- Use designated yard waste bags (available at retailers)
- Maximum 50 lbs per bag
- Branches: max 4 feet long, 2 inches diameter, bundled

Christmas Trees:
- Collected in January
- Remove all decorations and stands
- Place at curb

Leaf Vacuum Program:
- Available in fall for bagged leaves
- Check website for schedule

Composting: Backyard composting encouraged year-round""")
    ]
    
    for filename, content in samples:
        filepath = DOCS_DIR / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Created sample: {filepath}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Municipal Data Scraper")
    parser.add_argument("--sample", action="store_true", help="Create sample documents without scraping")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests")
    args = parser.parse_args()
    
    if args.sample:
        print("Creating sample documents...")
        create_sample_documents()
    else:
        print(f"Scraping {len(SCRAPE_URLS)} URLs...")
        results = scrape_all(delay=args.delay)
        print(f"\nScraped {len(results)} pages successfully")


if __name__ == "__main__":
    main()