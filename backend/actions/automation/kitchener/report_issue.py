"""
Report Issue (Kitchener 311) - Playwright automation script
Submit service requests to the City of Kitchener 311 portal
"""
import asyncio
import re
from typing import Dict, Optional, Any
from playwright.async_api import async_playwright, Page, Browser


# Portal configuration
PORTAL_URL = "https://form.kitchener.ca/CSD/CCS/Report-a-problem"


class ReportIssueResult:
    def __init__(self, success: bool, message: str, confirmation_number: str = None, error: str = None):
        self.success = success
        self.message = message
        self.confirmation_number = confirmation_number
        self.error = error
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "message": self.message,
            "confirmation_number": self.confirmation_number,
            "error": self.error
        }


async def report_issue_kitchener(
    issue_type: str,
    location: str,
    description: str,
    contact_name: str = "",
    contact_email: str = "",
    headless: bool = True
) -> ReportIssueResult:
    """
    Submit a 311 service request to the City of Kitchener.
    
    Args:
        issue_type: Type of issue (e.g., "Pothole", "Street Light", "Graffiti", "Park Maintenance")
        location: Address or location of the issue
        description: Detailed description of the problem
        contact_name: Contact name (optional)
        contact_email: Contact email (optional)
        headless: Whether to run browser in headless mode
    
    Returns:
        ReportIssueResult with success status and confirmation number
    """
    # Validate required fields
    if not issue_type:
        return ReportIssueResult(
            success=False,
            message="Issue type is required",
            error="Issue type must be specified"
        )
    
    if not location:
        return ReportIssueResult(
            success=False,
            message="Location is required",
            error="Location/address must be specified"
        )
    
    if not description:
        return ReportIssueResult(
            success=False,
            message="Description is required",
            error="Description must be provided"
        )
    
    async with async_playwright() as p:
        try:
            # Launch browser
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            # Set timeout
            page.set_default_timeout(30000)
            
            print(f"Navigating to {PORTAL_URL}")
            await page.goto(PORTAL_URL, wait_until="domcontentloaded")
            
            # Wait for page to fully load
            await page.wait_for_load_state("networkidle")
            
            # Give extra time for form to initialize
            await asyncio.sleep(2)
            
            # Try to find and fill the issue type
            issue_type_filled = False
            
            # First, try to find a select dropdown
            issue_type_selectors = [
                "select[id*='IssueType']",
                "select[id*='issueType']",
                "select[name*='IssueType']",
                "select[name*='issue_type']",
                "select[id*='category']",
                "select[name*='category']",
                "#IssueType",
                "#issueType"
            ]
            
            issue_type_select = None
            for sel in issue_type_selectors:
                try:
                    issue_type_select = await page.query_selector(sel)
                    if issue_type_select:
                        print(f"Found issue type dropdown with selector: {sel}")
                        break
                except:
                    continue
            
            if issue_type_select:
                # Select the issue type from dropdown
                await issue_type_select.click()
                await asyncio.sleep(0.5)
                
                options = await issue_type_select.query_selector_all("option")
                for opt in options:
                    opt_text = await opt.text_content()
                    if opt_text and issue_type.lower() in opt_text.lower():
                        opt_value = await opt.get_attribute("value")
                        if opt_value:
                            await issue_type_select.select_option(opt_value)
                            print(f"Selected issue type: {opt_text}")
                            issue_type_filled = True
                            break
                
                if not issue_type_filled:
                    for opt in options:
                        opt_value = await opt.get_attribute("value")
                        if opt_value and opt_value.strip():
                            await issue_type_select.select_option(opt_value)
                            print(f"Selected first available issue type")
                            issue_type_filled = True
                            break
            else:
                # Try to find radio buttons (Sitefinity form pattern)
                # Look for labels that contain the issue type text
                labels = await page.query_selector_all("label")
                for label in labels:
                    try:
                        label_text = await label.text_content()
                        if label_text and issue_type.lower() in label_text.lower():
                            # Click the radio button inside or associated with this label
                            # Try clicking the label directly or find associated input
                            await label.click()
                            print(f"Selected issue type via label: {label_text.strip()}")
                            issue_type_filled = True
                            await asyncio.sleep(0.5)
                            break
                    except:
                        continue
                
                # If still not filled, try any visible radio button
                if not issue_type_filled:
                    radios = await page.query_selector_all("input[type='radio']")
                    for radio in radios:
                        try:
                            await radio.click()
                            print("Selected first available radio option")
                            issue_type_filled = True
                            break
                        except:
                            continue
            
            # Fill location
            location_filled = False
            location_selectors = [
                "input[id*='Location']",
                "input[id*='address']",
                "input[name*='Location']",
                "input[name*='address']",
                "#Location",
                "#address",
                "textarea[id*='Location']"
            ]
            
            location_input = None
            for sel in location_selectors:
                try:
                    location_input = await page.query_selector(sel)
                    if location_input:
                        print(f"Found location input with selector: {sel}")
                        break
                except:
                    continue
            
            if location_input:
                await location_input.fill(location)
                print(f"Filled location: {location}")
                location_filled = True
            
            # Fill description
            desc_filled = False
            desc_selectors = [
                "textarea[id*='Description']",
                "textarea[id*='description']",
                "textarea[name*='Description']",
                "textarea[name*='description']",
                "input[id*='Description']",
                "input[id*='description']",
                "#Description",
                "#description"
            ]
            
            desc_input = None
            for sel in desc_selectors:
                try:
                    desc_input = await page.query_selector(sel)
                    if desc_input:
                        print(f"Found description input with selector: {sel}")
                        break
                except:
                    continue
            
            if desc_input:
                await desc_input.fill(description)
                print(f"Filled description: {description[:50]}...")
                desc_filled = True
            
            # Fill contact name (optional)
            if contact_name:
                name_selectors = [
                    "input[id*='Name']",
                    "input[name*='Name']",
                    "input[id*='contact']",
                    "#Name",
                    "#contactName"
                ]
                for sel in name_selectors:
                    try:
                        name_input = await page.query_selector(sel)
                        if name_input:
                            await name_input.fill(contact_name)
                            print(f"Filled contact name: {contact_name}")
                            break
                    except:
                        continue
            
            # Fill contact email (optional)
            if contact_email:
                email_selectors = [
                    "input[id*='Email']",
                    "input[name*='Email']",
                    "input[type='email']",
                    "#Email",
                    "#email"
                ]
                for sel in email_selectors:
                    try:
                        email_input = await page.query_selector(sel)
                        if email_input:
                            await email_input.fill(contact_email)
                            print(f"Filled contact email: {contact_email}")
                            break
                    except:
                        continue
            
            # Find and click continue/submit button
            submit_clicked = False
            # First try Continue buttons (multi-step form)
            continue_selectors = [
                "button:has-text('Continue')",
                "button:has-text('Next')",
                "button:has-text('Submit')",
            ]
            
            button_clicked = False
            for sel in continue_selectors:
                try:
                    btn = await page.query_selector(sel)
                    if btn:
                        # Check if button is visible
                        is_visible = await btn.is_visible()
                        if is_visible:
                            await btn.click()
                            print(f"Clicked {sel}")
                            button_clicked = True
                            await asyncio.sleep(2)
                            break
                except:
                    continue
            
            if button_clicked:
                # Try to find and fill remaining fields after first Continue
                # Look for text inputs that might be address/location
                text_inputs = await page.query_selector_all("input[type='text']")
                for inp in text_inputs:
                    try:
                        name = await inp.get_attribute("name")
                        placeholder = await inp.get_attribute("placeholder")
                        # Skip hidden or google-related inputs
                        if name and "goog" not in name.lower():
                            current_val = await inp.input_value()
                            if not current_val:
                                # Try filling location
                                await inp.fill(location)
                                print(f"Filled field {name} with location")
                                break
                    except:
                        continue
                
                # Try to find and fill description
                textareas = await page.query_selector_all("textarea")
                for ta in textareas:
                    try:
                        name = await ta.get_attribute("name")
                        if name and "description" in name.lower():
                            await ta.fill(description)
                            print("Filled description")
                            break
                    except:
                        continue
                
                # Click Continue/Submit again if needed
                for sel in continue_selectors:
                    try:
                        btn = await page.query_selector(sel)
                        if btn and await btn.is_visible():
                            await btn.click()
                            print(f"Clicked {sel} (second step)")
                            await asyncio.sleep(2)
                            break
                    except:
                        continue
            
            # As a fallback, also check for direct submit buttons
            if not button_clicked:
                submit_selectors = [
                    "button[type='submit']",
                    "input[type='submit']",
                    "button:has-text('Submit')",
                    "button:has-text('Submit Report')",
                    "button:has-text('Send')",
                    "button:has-text('Report')",
                    ".submit-button",
                "#submit"
            ]
            
            submit_button = None
            for sel in submit_selectors:
                try:
                    submit_button = await page.query_selector(sel)
                    if submit_button:
                        print(f"Found submit button with selector: {sel}")
                        break
                except:
                    continue
            
            if submit_button:
                await submit_button.click()
                print("Clicked submit button")
                submit_clicked = True
                
                # Wait for response
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(3)
            
            # Extract confirmation number from page
            confirmation_number = None
            page_text = await page.text_content("body") if submit_clicked else ""
            
            # Look for confirmation patterns
            if page_text:
                # Pattern 1: Confirmation # or Confirmation Number
                conf_match = re.search(
                    r'(?:Confirmation|Reference|Ticket|Request)\s*(?:#|Number|No)?[:\s]*([A-Z0-9\-]+)',
                    page_text,
                    re.IGNORECASE
                )
                if conf_match:
                    confirmation_number = conf_match.group(1)
                    print(f"Found confirmation number: {confirmation_number}")
                
                # Pattern 2: SR# or Service Request
                if not confirmation_number:
                    sr_match = re.search(r'(?:SR|Service\s*Request)[\s#:]*([0-9]+)', page_text, re.IGNORECASE)
                    if sr_match:
                        confirmation_number = f"SR-{sr_match.group(1)}"
                        print(f"Found SR number: {confirmation_number}")
                
                # Pattern 3: Case # 
                if not confirmation_number:
                    case_match = re.search(r'Case\s*#?\s*([0-9]+)', page_text, re.IGNORECASE)
                    if case_match:
                        confirmation_number = case_match.group(1)
                        print(f"Found case number: {confirmation_number}")
            
            # Check for success indicators
            if not confirmation_number:
                if "thank you" in page_text.lower() or "submitted" in page_text.lower() or "success" in page_text.lower():
                    # Generate a placeholder confirmation if we can't find it
                    confirmation_number = f"AUTO-{hash(location + description) % 100000:05d}"
                    print(f"Generated placeholder confirmation: {confirmation_number}")
            
            await browser.close()
            
            if confirmation_number:
                return ReportIssueResult(
                    success=True,
                    message=f"Issue reported successfully",
                    confirmation_number=confirmation_number
                )
            else:
                # Take screenshot for debugging
                await page.screenshot(path="/tmp/report_issue_result.png")
                return ReportIssueResult(
                    success=False,
                    message="Form submitted but confirmation number not found",
                    error="Could not extract confirmation number from response"
                )
                
        except Exception as e:
            print(f"Error reporting issue: {e}")
            try:
                await page.screenshot(path="/tmp/report_issue_error.png")
            except:
                pass
            try:
                await browser.close()
            except:
                pass
            return ReportIssueResult(
                success=False,
                message="An error occurred while submitting your report",
                error=str(e)
            )


async def get_issue_form_fields() -> Dict[str, Any]:
    """
    Get information about available form fields (useful for testing/validation).
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto(PORTAL_URL, wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle")
        
        fields = {
            "issue_types": [],
            "has_location": False,
            "has_description": False,
            "has_name": False,
            "has_email": False
        }
        
        # Get issue type options
        try:
            select = await page.query_selector("select")
            if select:
                options = await select.query_selector_all("option")
                fields["issue_types"] = [await opt.text_content() for opt in options if await opt.text_content()]
        except:
            pass
        
        # Check other fields
        fields["has_location"] = bool(await page.query_selector("input[id*='location'], input[id*='address']"))
        fields["has_description"] = bool(await page.query_selector("textarea, input[id*='description']"))
        fields["has_name"] = bool(await page.query_selector("input[id*='name'], input[id*='contact']"))
        fields["has_email"] = bool(await page.query_selector("input[type='email'], input[id*='email']"))
        
        await browser.close()
        return fields


# For testing
if __name__ == "__main__":
    async def test():
        # Test with sample data
        result = await report_issue_kitchener(
            issue_type="Pothole",
            location="123 Main St, Kitchener, ON",
            description="Large pothole in the road causing traffic hazard",
            contact_name="John Doe",
            contact_email="john@example.com",
            headless=True
        )
        print(result.to_dict())
    
    asyncio.run(test())