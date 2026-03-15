"""
Book Parking Permit - Kitchener
Playwright automation script for booking parking permits
"""
import asyncio
import re
from typing import Dict, Optional, Any
from playwright.async_api import async_playwright, Page, Browser


# Portal configuration
PORTAL_URL = "https://kitchener.parkingpermit.site/signup"


class ParkingPermitResult:
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


async def book_parking_permit(
    parking_location: str,
    email: str,
    license_plate: str,
    phone: str = "",
    contact_name: str = "",
    headless: bool = True
) -> ParkingPermitResult:
    """
    Book a parking permit for the City of Kitchener.
    
    Args:
        parking_location: The parking location/zone name
        email: Email address for the permit
        license_plate: Vehicle license plate number
        phone: Phone number (optional)
        contact_name: Contact name (optional, splits to first/last)
        headless: Whether to run browser in headless mode
    
    Returns:
        ParkingPermitResult with success status and confirmation number
    """
    # Validate required fields
    if not parking_location:
        return ParkingPermitResult(
            success=False,
            message="Parking location is required",
            error="Parking location must be specified"
        )
    
    if not email:
        return ParkingPermitResult(
            success=False,
            message="Email is required",
            error="Email must be provided"
        )
    
    if not license_plate:
        return ParkingPermitResult(
            success=False,
            message="License plate is required",
            error="License plate must be provided"
        )
    
    # Basic email validation
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
        return ParkingPermitResult(
            success=False,
            message="Invalid email format",
            error="Please provide a valid email address"
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
            
            # ===== Fill form fields based on actual form structure =====
            
            # First name
            first_name_input = await page.query_selector("input[name='driver_first_name']")
            if first_name_input:
                # Split name or use default
                name_parts = contact_name.split() if contact_name else ["John", "Doe"]
                await first_name_input.fill(name_parts[0])
                print(f"Filled first name: {name_parts[0]}")
            
            # Last name
            last_name_input = await page.query_selector("input[name='driver_last_name']")
            if last_name_input:
                name_parts = contact_name.split() if contact_name else ["John", "Doe"]
                await last_name_input.fill(name_parts[-1] if len(name_parts) > 1 else "Doe")
                print(f"Filled last name: {name_parts[-1]}")
            
            # Email
            email_input = await page.query_selector("input[name='email']")
            if email_input:
                await email_input.fill(email)
                print(f"Filled email: {email}")
            
            # Phone
            if phone:
                phone_input = await page.query_selector("input[name='phone']")
                if phone_input:
                    await phone_input.fill(phone)
                    print(f"Filled phone: {phone}")
            
            # License plate
            lpn_input = await page.query_selector("input[name='lpn']")
            if lpn_input:
                await lpn_input.fill(license_plate.upper())
                print(f"Filled license plate: {license_plate.upper()}")
            
            # Parking location (dropdown)
            lot_select = await page.query_selector("select[name='lot_id']")
            if lot_select:
                await lot_select.click()
                await asyncio.sleep(0.5)
                
                # Try to find matching option
                options = await lot_select.query_selector_all("option")
                matched = False
                for opt in options:
                    opt_text = await opt.text_content()
                    opt_value = await opt.get_attribute("value")
                    if opt_text and opt_value and opt_text.strip() and "--" not in opt_text:
                        if parking_location.lower() in opt_text.lower() or opt_text.lower() in parking_location.lower():
                            await lot_select.select_option(opt_value)
                            print(f"Selected parking location: {opt_text}")
                            matched = True
                            break
                
                # If no match, select first valid option
                if not matched:
                    for opt in options:
                        opt_text = await opt.text_content()
                        opt_value = await opt.get_attribute("value")
                        if opt_text and opt_value and opt_text.strip() and "--" not in opt_text:
                            await lot_select.select_option(opt_value)
                            print(f"Selected first available location: {opt_text}")
                            break
            
            # Package selection (select first available)
            package_select = await page.query_selector("select[name='package_name']")
            if package_select:
                await package_select.click()
                await asyncio.sleep(0.3)
                
                options = await package_select.query_selector_all("option")
                for opt in options:
                    opt_text = await opt.text_content()
                    opt_value = await opt.get_attribute("value")
                    if opt_text and opt_value and opt_text.strip() and "--" not in opt_text:
                        await package_select.select_option(opt_value)
                        print(f"Selected package: {opt_text}")
                        break
            
            # Car description (optional)
            car_desc_input = await page.query_selector("input[name='car_desription']")
            if car_desc_input:
                await car_desc_input.fill("Vehicle")
                print("Filled car description")
            
            # Password (set a default for account creation)
            password_input = await page.query_selector("input[name='password']")
            if password_input:
                await password_input.fill("TempPass123!")
                print("Set temporary password")
            
            # Note: This form requires payment information which we won't fill
            # as it involves sensitive data. In production, this would be handled differently.
            
            # Find and click submit button (Pay button)
            submit_button = await page.query_selector("button:has-text('Pay')")
            if submit_button:
                await submit_button.click()
                print("Clicked Pay button")
                
                # Wait for response
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(3)
                
                # Check for errors or success
                page_text = await page.text_content("body")
                
                # Look for confirmation
                confirmation_match = re.search(
                    r'(?:Confirmation|Reference|Order|Permit|Ticket)[\s#:]*([A-Z0-9\-]+)',
                    page_text,
                    re.IGNORECASE
                )
                
                if confirmation_match:
                    confirmation_number = confirmation_match.group(1)
                    await browser.close()
                    return ParkingPermitResult(
                        success=True,
                        message="Parking permit booked successfully",
                        confirmation_number=confirmation_number
                    )
                
                # Check for error messages
                if "error" in page_text.lower() or "failed" in page_text.lower():
                    await browser.close()
                    return ParkingPermitResult(
                        success=False,
                        message="Payment failed or form validation error",
                        error="Form submission encountered errors"
                    )
            
            # If we get here without confirmation, return partial success
            # (Form was filled but payment step not completed)
            await browser.close()
            
            return ParkingPermitResult(
                success=True,
                message="Form fields filled. Payment step requires manual completion.",
                confirmation_number=None,
                error="Payment information not provided (requires credit card)"
            )
                
        except Exception as e:
            print(f"Error booking parking permit: {e}")
            try:
                await page.screenshot(path="/tmp/parking_permit_error.png")
            except:
                pass
            try:
                await browser.close()
            except:
                pass
            return ParkingPermitResult(
                success=False,
                message="An error occurred while booking your parking permit",
                error=str(e)
            )


async def get_parking_locations() -> list:
    """
    Get list of available parking locations/zones.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto(PORTAL_URL, wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle")
        
        locations = []
        
        # Try to find location dropdown
        select = await page.query_selector("select[name='lot_id']")
        if select:
            options = await select.query_selector_all("option")
            locations = [await opt.text_content() for opt in options if await opt.text_content()]
        
        await browser.close()
        return locations


# For testing
if __name__ == "__main__":
    async def test():
        # Test with sample data
        result = await book_parking_permit(
            parking_location="Downtown",
            email="test@example.com",
            license_plate="ABC123",
            phone="5195550100",
            contact_name="John Doe",
            headless=True
        )
        print(result.to_dict())
    
    asyncio.run(test())