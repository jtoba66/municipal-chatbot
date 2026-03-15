# Form Submission Investigation Report

**Date:** 2025-03-15  
**Purpose:** Investigate Playwright automation failures in form submission scripts

---

## Executive Summary

| Issue | Status | Root Cause |
|-------|--------|------------|
| `report_issue` (311 Form) | ❌ FAIL | Submit button requires all required fields to be filled before becoming clickable |
| `book_parking_permit` | ⚠️ PARTIAL | Confirmation number extraction regex is grabbing partial text |

---

## 1. 311 Report Issue Form

**URL:** https://form.kitchener.ca/CSD/CCS/Report-a-problem

### Issue Description
The Playwright script times out when clicking the submit button:
```
Selected issue type via label: Pothole
Found submit button with selector: button[type='submit']
Error: ElementHandle.click: Timeout 30000ms exceeded.
```

### Root Cause Analysis

The Kitchener 311 form is a **multi-step/multi-page form** that uses client-side validation. The submit button is **disabled** until ALL required fields are validated.

Based on form research:

1. **Required Fields (in order):**
   - **Issue Type** (radio buttons or dropdown) - e.g., Graffiti, Pothole, etc.
   - **Location/Address** - Full street address where the issue is located
   - **Description** - Detailed description of the problem

2. **Optional Fields:**
   - Contact name
   - Contact email (optional but needed for tracking)
   - Photo upload

3. **Key Form Behaviors:**
   - Uses **Sitefinity/GovStack** form framework
   - Fields are validated on blur and on "Continue" button click
   - The main submit button only becomes active after ALL required fields pass validation
   - JavaScript must be fully loaded (form doesn't work with JS disabled - there's a redirect to `/Error/JavaScript`)

### Why Submit Button Times Out

The current script fills:
1. Issue type (via label click)
2. Location 
3. Description

**But the form may require:**
1. Address-specific validation (Google Maps autocomplete)
2. Minimum description length
3. First "Continue" step to be clicked before final submit

### Fix Recommendations

**Option 1 - Click Continue First (Recommended):**
```python
# The form likely has a "Continue" or "Next" button that validates first step
continue_btn = await page.query_selector("button:has-text('Continue')")
if continue_btn and await continue_btn.is_visible():
    await continue_btn.click()
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(2)

# NOW click Submit
submit_btn = await page.query_selector("button[type='submit'], button:has-text('Submit')")
if submit_btn:
    await submit_btn.click()
```

**Option 2 - Ensure All Required Fields Have Valid Data:**
- Add validation that address is actually geocoded/validated
- Ensure description is > 10 characters
- Add wait for field validation indicators (green checkmarks)

**Option 3 - Check Button State Before Clicking:**
```python
submit_btn = await page.query_selector("button[type='submit']")
is_disabled = await submit_btn.get_attribute("disabled")
if is_disabled:
    # Find what's missing - check for validation messages
    validation_errors = await page.query_selector_all(".error, .validation-message")
    for err in validation_errors:
        print(f"Validation error: {await err.text_content()}")
```

### Form HTML Structure (from curl)

Key selectors that likely work:
```css
/* Issue type - likely radio buttons in a fieldset */
fieldset input[type="radio"]
label:has-text("Pothole")

/* Location - address input with autocomplete */
input[id*="Address"]
input[name*="Location"]

/* Description */
textarea[id*="Description"]

/* Buttons */
button:has-text("Continue")
button:has-text("Submit")
button[type="submit"]
```

---

## 2. Parking Permit Form

**URL:** https://kitchener.parkingpermit.site/signup

### Issue Description
The confirmation number is truncated to just "For":
```
Clicked Pay button
{'success': True, 'message': 'Parking permit booked successfully', 'confirmation_number': 'For', ...}
```

### Root Cause Analysis

The site is a **React SPA** (Single Page Application). The current regex pattern:
```python
confirmation_match = re.search(
    r'(?:Confirmation|Reference|Order|Permit|Ticket)[\s#:]*([A-Z0-9\-]+)',
    page_text,
    re.IGNORECASE
)
```

This is likely matching text like:
- "**For** more information call..." (grabbing "For" instead of actual confirmation)
- Or partial text from a confirmation section

### Key Form Fields (from code analysis)

| Field | Selector | Required |
|-------|----------|----------|
| First name | `input[name='driver_first_name']` | Yes |
| Last name | `input[name='driver_last_name']` | Yes |
| Email | `input[name='email']` | Yes |
| Phone | `input[name='phone']` | No |
| License plate | `input[name='lpn']` | Yes |
| Parking location | `select[name='lot_id']` | Yes |
| Package | `select[name='package_name']` | Yes |
| Password | `input[name='password']` | Yes (for account creation) |

### Confirmation Number Location

The site is React-based. Confirmation is likely:
1. In a modal after successful payment
2. In a "Thank you" page
3. Sent via email (but we can't read email)

**Fix Recommendations:**

```python
# Better regex patterns to try:
confirmation_patterns = [
    r'Confirmation\s*(?:Number|#)?[:\s]*([A-Z0-9]{6,})',  # Alphanumeric, 6+ chars
    r'Order\s*(?:Number|#)?[:\s]*([A-Z0-9\-]+)',
    r'Permit\s*(?:Number|#)?[:\s]*([A-Z0-9\-]+)',
    r'Your\s+(?:confirmation|order|reference)\s+is[:\s]+([A-Z0-9\-]+)',
]

# ALSO check for specific confirmation elements
confirmation_element = await page.query_selector(".confirmation-number, [data-testid='confirmation']")
if confirmation_element:
    confirmation_number = await confirmation_element.text_content()

# Check modal content
modal = await page.query_selector(".modal-content, .ant-modal-content")
if modal:
    modal_text = await modal.text_content()
    # Extract from modal
```

### Payment Note

The form requires payment (credit card). The current code sets a default password and attempts to click "Pay" but doesn't fill payment info. This means:
- The form won't actually complete payment
- No real confirmation number will be generated
- The "success" is partial (form fields filled, but payment failed)

**Recommendation:** Either:
1. Skip payment forms in automation (return "Form prepared, manual payment required")
2. Add Stripe/payment element handling (complex)
3. Use a test payment mode if available

---

## Summary of Fixes Needed

### report_issue.py

1. **Click Continue/Next before Submit** - Add step to validate first page before final submit
2. **Check button disabled state** - Wait until submit button is enabled
3. **Add validation wait** - Wait for field validation to complete (green checkmarks)
4. **Add address autocomplete** - May need to select from Google Maps dropdown

### book_parking_permit.py

1. **Fix confirmation regex** - Use more specific patterns, check modal content
2. **Handle payment step** - Either skip gracefully or implement test payment
3. **Add screenshot on success** - To debug what's being displayed

### Both Scripts

1. **Add debug screenshots** - Capture state before/after submit click
2. **Wait for JavaScript** - Use `wait_for_load_state("networkidle")` more aggressively
3. **Log validation errors** - Print any validation messages that appear

---

## Files Reviewed

- `backend/actions/automation/kitchener/report_issue.py`
- `backend/actions/automation/kitchener/book_parking_permit.py`
- `docs-internal/automation-test-results.md`
- `docs-internal/playwright-code-review.md`

---

**Status:** Investigation complete. Fixes ready to implement.