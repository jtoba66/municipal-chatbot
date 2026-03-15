# City Contact Methods: Kitchener & Waterloo

Research for implementing "live agent handoff" for municipal chatbot.

## Summary

Both cities have established 311-style contact systems but **no public API** for programmatic request submission. Requests are handled through web forms, phone, and email, with internal ticketing systems (specific vendor not publicly documented).

---

## City of Kitchener

### Contact Channels

| Channel | Details |
|---------|---------|
| **Phone** | 519-741-2345 (24/7) |
| **TTY** | 1-866-969-9994 |
| **General Email** | info@kitchener.ca |
| **Online Portal** | MyKitchener (my.kitchener.ca) |
| **Report Problem Form** | https://form.kitchener.ca/CSD/CCS/Report-a-problem |
| **Contact Form** | https://form.kitchener.ca/CSD/CCS/Contact-us |

### How Citizens Submit Requests

1. **MyKitchener Portal** - Requires free account signup. Contains "Report a problem" widget.
2. **Online Form (No account required)** - https://form.kitchener.ca/CSD/CCS/Report-a-problem
   - Categories: Graffiti, illegal signs, litter, needles, parking complaints, property standards, potholes, snow clearing, sidewalk hazards, trail maintenance, other
   - Can upload photos
   - Requires: address, description, optional contact info for follow-up
3. **Phone** - 519-741-2345 for any issue

### Ticketing System

- **Unknown**: No public documentation found indicating which ticketing system Kitchener uses. Internal system not exposed via API.

### API Access

- **No public API available** for submitting requests programmatically
- Open Data portal exists at https://open-kitchenergis.opendata.arcgis.com/ but does not include service request submission API

### Digital Innovation Team Contact

- **Nicole Amaral** - Director, Digital Kitchener Innovation Lab
  - Email: nicole.amaral@kitchener.ca (inferred from pattern)
  - Leads Digital Kitchener strategy and AI initiatives
  - Started role February 3, 2025

---

## City of Waterloo

### Contact Channels

| Channel | Details |
|---------|---------|
| **Phone (General)** | 519-886-1550 |
| **Phone (Bylaw)** | 519-747-8785 |
| **Report Issue Form** | https://forms.waterloo.ca/Website/Report-an-issue |
| **Media Inquiries** | communications@waterloo.ca |
| **In Person** | 100 Regina Street South, City Hall |

### How Citizens Submit Requests

1. **Online Form** - https://forms.waterloo.ca/Website/Report-an-issue
   - Separates urgent vs non-urgent issues
   - Urgent: illegal parking, noise complaints, water/sewer, downed trees, road issues
   - Non-urgent: via online form
2. **Phone** - Various numbers for different departments (see above)
3. **In Person** - City Hall or Service Centre

### Ticketing System

- **Unknown**: No public documentation found

### API Access

- **No public API** for submitting requests programmatically

---

## Recommendations for Live Agent Handoff

Since no API exists, options for chatbot integration are:

1. **Email-based handoff** - Send formatted email to info@kitchener.ca or use Waterloo's form programmatically (may need CAPTCHA handling)
2. **Form submission simulation** - POST to the web form endpoints (requires checking if CSRF/protection in place)
3. **Direct phone numbers** - Provide click-to-call links for chatbot to surface
4. **Partner with Digital teams** - Contact Nicole Amaral (Kitchener) to discuss potential future API integration or pilot programs

### Key Email Addresses

- Kitchener general: **info@kitchener.ca**
- Waterloo media: **communications@waterloo.ca**

---

## Open Questions

- What internal ticketing system do either city use? (Could enable future API integration if known)
- Any existing integration partners or civic tech relationships?
- Would either city be open to a pilot API integration?

---

*Research date: 2025-03-15*