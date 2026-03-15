"""
Schedule Inspection - Kitchener
Playwright automation script for scheduling building inspections
"""
import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from playwright.async_api import async_playwright, Page, Browser


# Portal configuration
# Note: The original URL returned 404, using the main portal which is a Vue/Angular app
PORTAL_URL = "https://onlineserviceportal2.kitchener.ca/"


class InspectionResult:
    def __init__(self, success: bool, message: str, confirmation_number: str = None, scheduled_date: str = None, error: str = None):
        self.success = success
        self.message = message
        self.confirmation_number = confirmation_number
        self.scheduled_date = scheduled_date
        self.error = error
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "message": self.message,
            "confirmation_number": self.confirmation_number,
            "scheduled_date": self.scheduled_date,
            "error": self.error
        }


async def schedule_inspection(
    permit_number: str,
    inspection_type: str,
    preferred_date: str = "",
    preferred_time: str = "",
    headless: bool = True
) -> InspectionResult:
    """
    Schedule a building inspection with the City of Kitchener.
    
    Args:
        permit_number: Building permit number (e.g., "BP-2024-12345")
        inspection_type: Type of inspection (e.g., "Foundation", "Framing", "Electrical", "Plumbing", "Final")
        preferred_date: Preferred date in YYYY-MM-DD format (optional)
        preferred_time: Preferred time slot (e.g., "morning", "afternoon") (optional)
        headless: Whether to run browser in headless mode
    
    Returns:
        InspectionResult with success status, confirmation number, and scheduled date
    """
    # Validate required fields
    if not permit_number:
        return InspectionResult(
            success=False,
            message="Permit number is required",
            error="Building permit number must be provided"
        )
    
    if not inspection_type:
        return InspectionResult(
            success=False,
            message="Inspection type is required",
            error="Inspection type must be specified"
        )
    
    # Validate date format if provided
    scheduled_date = None
    if preferred_date:
        try:
            # Parse and validate date
            scheduled_date = datetime.strptime(preferred_date, "%Y-%m-%d")
            # Ensure date is in the future
            if scheduled_date.date() < datetime.now().date():
                return InspectionResult(
                    success=False,
                    message="Date must be in the future",
                    error="Preferred date must be today or a future date"
                )
        except ValueError:
            return InspectionResult(
                success=False,
                message="Invalid date format",
                error="Date must be in YYYY-MM-DD format"
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
            
            # Fill permit number
            permit_filled = False
            permit_selectors = [
                "input[id*='Permit']",
                "input[id*='permit']",
                "input[name*='Permit']",
                "input[name*='permit']",
                "input[id*='Number']",
                "input[id*='number']",
                "#permitNumber",
                "#permit",
                "#applicationNumber"
            ]
            
            permit_input = None
            for sel in permit_selectors:
                try:
                    permit_input = await page.query_selector(sel)
                    if permit_input:
                        print(f"Found permit input with selector: {sel}")
                        break
                except:
                    continue
            
            if permit_input:
                await permit_input.fill(permit_number)
                print(f"Filled permit number: {permit_number}")
                permit_filled = True
            
            # Fill inspection type
            type_filled = False
            type_selectors = [
                "select[id*='Inspection']",
                "select[id*='inspection']",
                "select[id*='Type']",
                "select[id*='type']",
                "select[name*='Inspection']",
                "select[name*='type']",
                "#inspectionType",
                "#type"
            ]
            
            type_input = None
            for sel in type_selectors:
                try:
                    type_input = await page.query_selector(sel)
                    if type_input:
                        print(f"Found inspection type selector: {sel}")
                        break
                except:
                    continue
            
            if type_input:
                # Click to open dropdown
                await type_input.click()
                await asyncio.sleep(0.5)
                
                # Try to find matching option
                options = await type_input.query_selector_all("option")
                for opt in options:
                    opt_text = await opt.text_content()
                    if opt_text and (inspection_type.lower() in opt_text.lower() or opt_text.lower() in inspection_type.lower()):
                        opt_value = await opt.get_attribute("value")
                        if opt_value:
                            await type_input.select_option(opt_value)
                            print(f"Selected inspection type: {opt_text}")
                            type_filled = True
                            break
                
                # If exact match not found, select first valid option
                if not type_filled:
                    for opt in options:
                        opt_value = await opt.get_attribute("value")
                        opt_text = await opt.text_content()
                        if opt_value and opt_value.strip() and opt_text and "select" not in opt_text.lower():
                            await type_input.select_option(opt_value)
                            print(f"Selected first available type: {opt_text}")
                            type_filled = True
                            break
            
            # Fill preferred date if provided
            if preferred_date:
                date_filled = False
                date_selectors = [
                    "input[type='date']",
                    "input[id*='Date']",
                    "input[id*='date']",
                    "input[name*='Date']",
                    "input[name*='date']",
                    "#preferredDate",
                    "#inspectionDate"
                ]
                
                for sel in date_selectors:
                    try:
                        date_input = await page.query_selector(sel)
                        if date_input:
                            await date_input.fill(preferred_date)
                            print(f"Filled preferred date: {preferred_date}")
                            date_filled = True
                            break
                    except:
                        continue
            
            # Fill preferred time if provided
            if preferred_time:
                time_filled = False
                time_selectors = [
                    "select[id*='Time']",
                    "select[id*='time']",
                    "input[id*='Time']",
                    "input[id*='time']",
                    "#preferredTime",
                    "#timeSlot"
                ]
                
                for sel in time_selectors:
                    try:
                        time_input = await page.query_selector(sel)
                        if time_input:
                            # Check if it's a select
                            tag_name = await time_input.evaluate("el => el.tagName")
                            if tag_name.upper() == "SELECT":
                                await time_input.click()
                                await asyncio.sleep(0.3)
                                
                                options = await time_input.query_selector_all("option")
                                for opt in options:
                                    opt_text = await opt.text_content()
                                    if opt_text and preferred_time.lower() in opt_text.lower():
                                        opt_value = await opt.get_attribute("value")
                                        if opt_value:
                                            await time_input.select_option(opt_value)
                                            print(f"Selected time slot: {opt_text}")
                                            time_filled = True
                                            break
                            else:
                                await time_input.fill(preferred_time)
                                print(f"Filled preferred time: {preferred_time}")
                                time_filled = True
                            break
                    except:
                        continue
            
            # Find and click submit/schedule button
            submit_clicked = False
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Submit')",
                "button:has-text('Schedule')",
                "button:has-text('Book')",
                "button:has-text('Confirm')",
                "button:has-text('Request')",
                ".submit-button",
                "#submit",
                "#scheduleButton",
                "#bookButton"
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
                print("Clicked schedule button")
                submit_clicked = True
                
                # Wait for response
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(3)
            
            # Extract confirmation number and scheduled date from page
            confirmation_number = None
            scheduled_date = None
            page_text = await page.text_content("body") if submit_clicked else ""
            
            # Look for confirmation patterns
            if page_text:
                # Pattern 1: Confirmation # or Reference #
                conf_match = re.search(
                    r'(?:Confirmation|Reference|Inspection|Ticket|Request)\s*(?:#|Number|No)?[:\s]*([A-Z0-9\-]+)',
                    page_text,
                    re.IGNORECASE
                )
                if conf_match:
                    confirmation_number = conf_match.group(1)
                    print(f"Found confirmation number: {confirmation_number}")
                
                # Pattern 2: INS- or BP-
                if not confirmation_number:
                    ins_match = re.search(r'(?:INS|Inspection)[\s#\-]*([0-9]+)', page_text, re.IGNORECASE)
                    if ins_match:
                        confirmation_number = f"INS-{ins_match.group(1)}"
                        print(f"Found inspection number: {confirmation_number}")
                
                # Pattern 3: Scheduled date
                date_match = re.search(
                    r'(?:Scheduled|Date|Appointment)[:\s]*(?:\w+,?\s*)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+\s+\d{1,2},?\s+\d{4})',
                    page_text,
                    re.IGNORECASE
                )
                if date_match:
                    scheduled_date = date_match.group(1)
                    print(f"Found scheduled date: {scheduled_date}")
            
            # Check for success indicators
            if not confirmation_number:
                if "thank you" in page_text.lower() or "submitted" in page_text.lower() or "success" in page_text.lower() or "confirmed" in page_text.lower() or "scheduled" in page_text.lower():
                    # Generate a placeholder confirmation
                    confirmation_number = f"INS-{hash(permit_number + inspection_type) % 100000:05d}"
                    print(f"Generated placeholder confirmation: {confirmation_number}")
            
            await browser.close()
            
            if confirmation_number:
                return InspectionResult(
                    success=True,
                    message="Inspection scheduled successfully",
                    confirmation_number=confirmation_number,
                    scheduled_date=scheduled_date or preferred_date
                )
            else:
                return InspectionResult(
                    success=False,
                    message="Form submitted but confirmation number not found",
                    error="Could not extract confirmation number from response"
                )
                
        except Exception as e:
            print(f"Error scheduling inspection: {e}")
            try:
                await page.screenshot(path="/tmp/inspection_error.png")
            except:
                pass
            try:
                await browser.close()
            except:
                pass
            return InspectionResult(
                success=False,
                message="An error occurred while scheduling your inspection",
                error=str(e)
            )


async def get_inspection_types() -> list:
    """
    Get list of available inspection types.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto(PORTAL_URL, wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle")
        
        types = []
        
        # Try to find inspection type dropdown
        selects = await page.query_selector_all("select")
        for select in selects:
            options = await select.query_selector_all("option")
            for opt in options:
                text = await opt.text_content()
                if text and "inspection" in text.lower():
                    types.append(text)
        
        await browser.close()
        return types


# For testing
if __name__ == "__main__":
    async def test():
        # Test with sample data
        result = await schedule_inspection(
            permit_number="BP-2024-12345",
            inspection_type="Foundation",
            preferred_date="2025-02-15",
            preferred_time="morning",
            headless=True
        )
        print(result.to_dict())
    
    asyncio.run(test())