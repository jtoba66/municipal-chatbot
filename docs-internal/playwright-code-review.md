# Playwright Automation Scripts — Code Review

**Reviewer:** Monica  
**Date:** 2025-01-14  
**Files Reviewed:**
- `backend/actions/automation/kitchener/report_issue.py`
- `backend/actions/automation/kitchener/book_parking_permit.py`
- `backend/actions/automation/kitchener/schedule_inspection.py`

---

## Executive Summary

| Area | Rating | Notes |
|------|--------|-------|
| Code Quality & Structure | ⚠️ Needs Work | Repetitive patterns, some inconsistencies |
| Error Handling | ✅ Good | Comprehensive try/except blocks, screenshots on failure |
| Selector Stability | ❌ Weak | Over-reliance on fuzzy selectors; high breakage risk |
| Security Concerns | ⚠️ Minor Issues | Hardcoded credentials, password handling |
| Return Format Consistency | ✅ Good | All three use structured result classes with `to_dict()` |

**Overall Verdict:** 🔄 **Changes Requested** — Address selector fragility before production use.

---

## 1. Code Quality & Structure

### What's Good
- **Result classes**: Each script has a dedicated result class (`ReportIssueResult`, `ParkingPermitResult`, `InspectionResult`) with `to_dict()` — clean and consistent.
- **Input validation**: All three scripts validate required fields before launching the browser.
- **Async/await**: Proper use of Playwright's async API.
- **Separation of concerns**: Helper functions like `get_parking_locations()`, `get_issue_form_fields()` are extracted cleanly.

### What Needs Fixes

#### Duplicate Code Patterns
All three scripts contain identical boilerplate for:
- Browser launch/context setup
- Timeout configuration
- Screenshot-on-error logic
- Confirmation extraction regex

**Recommendation:** Extract a base class or shared utilities:
```python
# e.g., shared/base_automation.py
class BaseAutomation:
    async def _launch_browser(self, headless: bool) -> Browser:
        ...
    async def _handle_error(self, page: Page, error: Exception):
        ...
```

#### Inconsistent Variable Naming
- `report_issue.py` uses `issue_type_filled`, `location_filled`, `desc_filled` (booleans)
- `schedule_inspection.py` uses `permit_filled`, `type_filled`, `date_filled`
- `book_parking_permit.py` doesn't use boolean flags at all

**Recommendation:** Standardize on one pattern across all files.

---

## 2. Error Handling

### What's Good
- Comprehensive try/except blocks wrapping the entire flow
- Screenshots captured on failure (`/tmp/report_issue_error.png`, etc.)
- Browser cleanup in `finally`-like pattern (try/except blocks closing browser)
- All validation errors return structured results with `success=False`

### Gaps
- No retry logic for transient failures (network timeouts, page load flakes)
- `page` variable referenced in exception handler but may not be defined if browser launch fails
- Silent failures: if a form field isn't found, the script continues without warning

**Example issue in `report_issue.py`:**
```python
except Exception as e:
    print(f"Error reporting issue: {e}")
    try:
        await page.screenshot(path="/tmp/report_issue_error.png")  # page may not exist
    except:
        pass
```

**Recommendation:** Initialize `page = None` before the try block and check before using in exception handler.

---

## 3. Selector Stability ⚠️ CRITICAL

This is the biggest risk. All three scripts use **fallback selector chains** — iterating through multiple selector candidates until one works. This is a maintenance nightmare.

### Problematic Patterns

**Example from `report_issue.py`:**
```python
issue_type_selectors = [
    "select[id*='IssueType']",
    "select[id*='issueType']",
    "select[name*='IssueType']",
    "select[name*='issue_type']",
    "select[id*='category']",        # Too generic — will match anything with "category"
    "select[name*='category']",      # Same problem
    "#IssueType",
    "#issueType"
]
```

This approach:
1. **Will match wrong fields** if a page has multiple elements matching broad patterns like `id*='category'`
2. **Hides real errors** — if the exact field doesn't exist, the script silently uses a wrong field
3. **Becomes stale** — site changes invalidate selectors unpredictably

### Better Approach

1. **Discover selectors once**, then hard-code the working ones per environment
2. **Use Playwright's test ids** (`data-testid`) where possible (requires site cooperation)
3. **Add logging** when falling back to a selector so you know which one actually matched
4. **Validate fields** after filling — check the value was actually set

**Quick fix for existing code** — add logging to fallback selectors:
```python
for sel in location_selectors:
    try:
        location_input = await page.query_selector(sel)
        if location_input:
            print(f"Found location input with selector: {sel}")  # Already exists — good!
            break
    except:
        continue
```
The logging is there in some places but not consistently. Add it everywhere.

---

## 4. Security Concerns

### Issues Found

| Issue | Location | Severity |
|-------|----------|----------|
| Hardcoded default password | `book_parking_permit.py` line ~137 | Medium |
| Screenshot path exposure | All three scripts write to `/tmp/` | Low |
| No HTTPS enforcement check | All three scripts use plain URLs | Low |
| Comment about payment data | `book_parking_permit.py` notes sensitive data | Informational |

**Specific code in `book_parking_permit.py`:**
```python
password_input = await page.query_selector("input[name='password']")
if password_input:
    await password_input.fill("TempPass123!")  # Hardcoded default
    print("Set temporary password")
```

**Recommendation:**
- Never set default passwords — let the form handle account creation or fail explicitly
- Remove or make the password a parameter with no default
- Screenshots in `/tmp/` are fine for debugging but ensure they're deleted after use or not written in production

---

## 5. Return Format Consistency

### ✅ Good — All three follow the same pattern:
```python
class XxxResult:
    success: bool
    message: str
    confirmation_number: str | None
    error: str | None  # Only in some
    
    def to_dict(self) -> dict
```

### Minor Inconsistency
- `InspectionResult` has an extra field: `scheduled_date`
- Others don't have equivalent date fields

This is acceptable since the data models differ per use case, but document the differences.

---

## Recommendations (Priority Order)

### 🔴 High Priority
1. **Fix selector stability** — add logging to every selector fallback, validate filled values
2. **Remove hardcoded password** in `book_parking_permit.py`

### 🟡 Medium Priority
3. **Extract shared base class** for browser launch/error handling to reduce duplication
4. **Add retry logic** for flaky network conditions (2-3 retries with exponential backoff)
5. **Initialize variables properly** before try/except to avoid undefined reference in error handlers

### 🟢 Low Priority
6. **Standardize boolean flag naming** across scripts
7. **Add environment config** (e.g., `HEADLESS_MODE`, `SCREENSHOT_PATH`) instead of hardcoding
8. **Consider using Playwright's `locator` API** over `query_selector` for better reliability

---

## Testing Notes

- All three scripts include `if __name__ == "__main__"` test blocks — good
- No unit tests exist — consider adding pytest with Playwright's test runner
- The URLs in `schedule_inspection.py` note that the original URL returned 404 — verify these are correct in staging

---

**Reviewed by:** Monica  
**Status:** 🔄 Changes Requested