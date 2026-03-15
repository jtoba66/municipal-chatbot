# Municipal Chatbot Agentic Actions Research

## Kitchener/Waterloo City Portals - Field Requirements for Automation

This document outlines the required fields for each citizen action to enable pre-written Playwright automation scripts (NOT LLM-based).

---

## 1. Report Pothole / Issue (311 Service Request)

### Kitchener
**Portal URL:** https://form.kitchener.ca/CSD/CCS/Report-a-problem

**Issue Types Available:**
- Graffiti
- Illegal sign
- Litter in a playground, park or trail
- Needles
- Parking complaint
- Property standards complaint
- Pothole
- Sidewalk snow clearing
- Sidewalk trip hazard
- Trail surface maintenance
- Other

**Required Fields:**
- Issue type (dropdown selection)
- Location details (street address, cross streets)
- Description of the issue
- Contact name and information (for follow-up)

**Optional Fields:**
- Photo upload (if applicable)

**Phone Alternative:** 519-741-2345

### Waterloo
**Portal URL:** https://forms.waterloo.ca/Website/Report-an-issue

**Required Fields:**
- Urgent? (Yes/No toggle)
- Issue description
- Location/address
- Contact information

**Notes:**
- For urgent issues (illegal parking, noise complaints, water/sewer), call 519-747-8785
- Non-urgent issues use the online form

---

## 2. Book Parking Permit

### Kitchener
**Portal URL:** https://kitchener.parkingpermit.site/signup

**Required Fields:**
- Preferred parking location (select from available garages/lots)
- Email address
- Vehicle licence plate number
- Phone number (cell recommended for "Call When Here" feature)

**Optional Fields:**
- Additional licence plates (up to 3 total, but only one vehicle allowed per day)

**Permit Options by Location:**
- Queen Street South (Lot 7)
- Charles Street West (Lot 15)
- Transit (Lot 22)
- King Street East (Lot 23)
- Bramm Street Yards (Lot 24)
- Charles & Benton parking garage
- Civic District parking garage
- Duke & Ontario parking garage
- Kitchener Market parking garage
- City Hall parking garage
- Water Street South (Lot 3)
- Ontario Street South (Lot 9)
- Green Street (Lot 12)
- Rotary (Lot 13)
- Centre In The Square (Lot 19A)

**Payment Methods:** VISA, MasterCard, Interac, Discover, American Express

**Note:** Monthly permits expire end of each month. Auto-renew available.

### Waterloo
**Portal URL:** https://www.waterloo.ca/parking/get-a-monthly-parking-permit/

**Required Fields:**
- Permit type selection (daytime, overnight, or 24-hour)
- Licence plate number
- Email address
- Payment information

**Overnight Parking Registration:** https://onp.cloud.waterloo.ca/
- Register vehicle before 2:15 a.m. to avoid ticket

---

## 3. Check Permit Status

### Kitchener Building Permits
**Portal URL:** https://onlineserviceportal2.kitchener.ca/citizenportal/app/landing

**Required Fields:**
- Address (property address)
- OR permit application number

**Features:**
- Check permit status within 2 business days of application
- Schedule inspections online
- View active permits and inspection history

**Alternative:** Call 519-741-2433

### Waterloo
**Contact:** Call Municipal Enforcement Services or visit in person

---

## 4. Pay Parking Ticket

### Kitchener
**Portal URL:** https://portal.gtechna.com/userportal/kitchener/ticketSearch1.xhtml

**Required Fields:**
- Ticket number (found under barcode or top right corner)

**Payment Fee:** $1.75 online transaction fee

**Payment Methods:** Visa, MasterCard

**Processing Time:** May take up to 14 days for ticket to appear in system

**Alternative Payment:**
- In person: City Hall Revenue Desk (200 King Street West) - cash, cheque, debit
- By mail: City of Kitchener - Revenue Division, P.O. Box 9058, Kitchener ON N2G 4G7
- Drop box: Young Street outside City Hall

**Dispute:** Call 519-741-2345 within 30 days

### Waterloo
**Portal URL:** https://amps.waterloo.ca/pay

**Required Fields (Parking Ticket):**
- Licence plate number
- Penalty notice number (under barcode, top right corner)

**Required Fields (Bylaw Ticket):**
- Name or business name
- Ticket number (starts with "E")

**Payment Methods:** Visa, MasterCard, American Express (credit cards only - no debit)

**Processing Time:** May take up to 15 days for ticket to appear

**Alternative Payment:**
- In person: City Hall, Municipal Enforcement Services (100 Regina St. S.)
- By mail or drop box: Municipal Enforcement Services, PO Box 337, Waterloo ON N2J 4A8

**Dispute:** Request screening review within 30 days at https://www.waterloo.ca/bylaws-and-enforcement/dispute-a-parking-or-bylaw-ticket/

---

## 5. Schedule Building Inspection

### Kitchener
**Portal URL:** https://onlineserviceportal2.kitchener.ca/citizenportal/app/landing

**Required Fields:**
- Permit number (must have active building permit)
- Property address
- Inspection type selection
- Preferred date/time

**Inspection Types:**
- Foundation inspection
- Framing inspection
- Electrical inspection
- plumbing inspection
- HVAC inspection
- Final inspection
- And project-specific inspections

**Note:** Must have approved building permit first. Book through online portal after permit is issued.

**Contact:** 519-741-2433 or building@kitchener.ca

### Waterloo
Building inspections are handled through the building permit process. Contact Building Services directly.

---

## Automation Notes

### Form Technologies Identified:
- **Kitchener:** Custom forms at form.kitchener.ca (likely SharePoint/InfoPath)
- **Kitchener Parking:** Third-party parking permit system (parkingpermit.site)
- **Kitchener Tickets:** GTechna portal (portal.gtechna.com)
- **Waterloo:** Custom forms at forms.waterloo.ca
- **Waterloo Tickets:** AMPS system (amps.waterloo.ca)

### Potential Challenges:
1. Session management - some forms may require session cookies
2. CAPTCHA - not observed but may be present
3. Dynamic form loading - some fields load via JavaScript
4. Payment processing - third-party payment gateways
5. Licence plate recognition - Kitchener uses LPR for parking

### Recommended Approach:
- Use Playwright with waitForSelector for dynamic content
- Implement screenshot comparison for form validation
- Handle multi-step form workflows
- Store session cookies for related operations

---

## Summary Table

| Action | City | Portal | Key Required Fields |
|--------|------|--------|---------------------|
| Report Issue | Kitchener | form.kitchener.ca | Issue type, location, description |
| Report Issue | Waterloo | forms.waterloo.ca | Urgency, description, location |
| Parking Permit | Kitchener | kitchener.parkingpermit.site | Location, email, licence plate |
| Parking Permit | Waterloo | waterloo.ca | Permit type, licence plate |
| Check Permit Status | Kitchener | onlineserviceportal2.kitchener.ca | Address or permit # |
| Pay Ticket | Kitchener | portal.gtechna.com | Ticket number |
| Pay Ticket | Waterloo | amps.waterloo.ca | Licence plate + ticket number |
| Schedule Inspection | Kitchener | onlineserviceportal2.kitchener.ca | Permit number, inspection type |

---

*Last Updated: March 2026*
*Research conducted for municipal chatbot automation project*