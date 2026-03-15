"""
Pay Parking Ticket - Kitchener
Playwright automation script for paying parking tickets via the City of Kitchener portal
"""
import asyncio
import re
from typing import Dict, Optional, Any
from playwright.async_api import async_playwright, Page, Browser


# Portal configuration
PORTAL_URL = "https://portal.gtechna.com/userportal/kitchener/ticketSearch1.xhtml"
TRANSACTION_FEE = 1.75


class PayTicketResult:
    def __init__(self, success: bool, message: str, confirmation_number: str = None, amount_due: float = None, error: str = None):
        self.success = success
        self.message = message
        self.confirmation_number = confirmation_number
        self.amount_due = amount_due
        self.error = error
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "message": self.message,
            "confirmation_number": self.confirmation_number,
            "amount_due": self.amount_due,
            "error": self.error
        }


async def pay_ticket_kitchener(ticket_number: str, headless: bool = True) -> PayTicketResult:
    """
    Pay a parking ticket for the City of Kitchener.
    
    Args:
        ticket_number: The parking ticket number (e.g., A123456)
        headless: Whether to run browser in headless mode
    
    Returns:
        PayTicketResult with success status and details
    """
    if not ticket_number or not re.match(r'^[A-Z0-9]{6,}$', ticket_number.upper()):
        return PayTicketResult(
            success=False,
            message="Invalid ticket number format",
            error="Ticket number must be at least 6 alphanumeric characters"
        )
    
    ticket_number = ticket_number.upper()
    
    async with async_playwright() as p:
        try:
            # Launch browser
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            # Set longer timeout for page operations
            page.set_default_timeout(30000)
            
            print(f"Navigating to {PORTAL_URL}")
            await page.goto(PORTAL_URL, wait_until="domcontentloaded")
            
            # Wait for page to load
            await page.wait_for_load_state("networkidle")
            
            # Look for ticket search input
            # The page structure may vary, try multiple selectors
            selectors = [
                "input[id*='ticket']",
                "input[name*='ticket']",
                "input[id*='infraction']",
                "input[name*='number']",
                "input[id*='number']",
                "input[type='text']",
                "#ticketNumber",
                "#ticket_number"
            ]
            
            ticket_input = None
            for sel in selectors:
                try:
                    ticket_input = await page.query_selector(sel)
                    if ticket_input:
                        print(f"Found ticket input with selector: {sel}")
                        break
                except:
                    continue
            
            if not ticket_input:
                # Take screenshot for debugging
                await page.screenshot(path="/tmp/ticket_page.png")
                await browser.close()
                return PayTicketResult(
                    success=False,
                    message="Could not find ticket number input field",
                    error="Form structure may have changed"
                )
            
            # Enter ticket number
            await ticket_input.fill(ticket_number)
            print(f"Entered ticket number: {ticket_number}")
            
            # Look for search button
            search_button = None
            button_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Search')",
                "button:has-text('Find')",
                "button:has-text('Look')"
            ]
            
            for sel in button_selectors:
                try:
                    search_button = await page.query_selector(sel)
                    if search_button:
                        print(f"Found search button with selector: {sel}")
                        break
                except:
                    continue
            
            if search_button:
                await search_button.click()
                await page.wait_for_load_state("networkidle")
            
            # Wait a bit for results
            await asyncio.sleep(2)
            
            # Check for ticket information
            # Look for amount due
            amount_match = None
            try:
                page_text = await page.content()
                # Look for dollar amounts
                amount_patterns = re.findall(r'\$[\d,]+\.?\d*', page_text)
                if amount_patterns:
                    # Get the first significant amount (likely the fine)
                    for amt in amount_patterns:
                        num = float(amt.replace('$', '').replace(',', ''))
                        if num > 10:  # Minimum fine amount
                            amount_match = num
                            break
            except Exception as e:
                print(f"Error extracting amount: {e}")
            
            # Look for ticket details
            ticket_info = await extract_ticket_info(page)
            
            if not ticket_info:
                # Check for "not found" message
                page_text = await page.text_content("body")
                if "not found" in page_text.lower() or "invalid" in page_text.lower():
                    await browser.close()
                    return PayTicketResult(
                        success=False,
                        message=f"Ticket {ticket_number} not found in the system",
                        error="Ticket may not exist or may have already been paid"
                    )
                
                # Take screenshot for debugging
                await page.screenshot(path="/tmp/ticket_result.png")
                await browser.close()
                return PayTicketResult(
                    success=False,
                    message="Could not find ticket information",
                    error="Ticket details not displayed"
                )
            
            # For now, we can't complete payment without user interaction
            # This is by design - we show the user the details and they confirm
            await browser.close()
            
            return PayTicketResult(
                success=True,
                message=f"Found ticket {ticket_number}",
                amount_due=amount_match or ticket_info.get("amount"),
                confirmation_number=None  # Would be set after payment
            )
            
        except Exception as e:
            print(f"Error paying ticket: {e}")
            try:
                await page.screenshot(path="/tmp/ticket_error.png")
            except:
                pass
            await browser.close()
            return PayTicketResult(
                success=False,
                message="An error occurred while processing your ticket",
                error=str(e)
            )


async def extract_ticket_info(page: Page) -> Optional[Dict[str, Any]]:
    """
    Extract ticket information from the page.
    """
    info = {}
    
    try:
        # Get page text
        body_text = await page.text_content("body")
        
        # Extract common ticket details
        # Ticket number
        if match := re.search(r'Ticket\s*(?:Number|No|#)?[:\s]*([A-Z0-9]+)', body_text, re.IGNORECASE):
            info["ticket_number"] = match.group(1)
        
        # Amount
        if match := re.search(r'\$[\d,]+\.?\d*', body_text):
            amount_str = match.group().replace('$', '').replace(',', '')
            info["amount"] = float(amount_str)
        
        # Date
        if match := re.search(r'Date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', body_text):
            info["date"] = match.group(1)
        
        # Location
        if match := re.search(r'Location[:\s]*([^<\n]+)', body_text, re.IGNORECASE):
            info["location"] = match.group(1).strip()
        
        # Status
        if "paid" in body_text.lower():
            info["status"] = "paid"
        elif "outstanding" in body_text.lower() or "due" in body_text.lower():
            info["status"] = "outstanding"
        
    except Exception as e:
        print(f"Error extracting ticket info: {e}")
    
    return info if info else None


async def get_ticket_details(ticket_number: str) -> Dict[str, Any]:
    """
    Get ticket details without attempting payment.
    Useful for checking ticket status.
    """
    result = await pay_ticket_kitchener(ticket_number, headless=True)
    return result.to_dict()


# For testing
if __name__ == "__main__":
    async def test():
        # Test with a sample ticket number
        result = await pay_ticket_kitchener("A123456", headless=True)
        print(result.to_dict())
    
    asyncio.run(test())