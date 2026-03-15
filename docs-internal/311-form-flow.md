# Kitchener 311 Form Flow Documentation

## Overview
**URL**: https://form.kitchener.ca/CSD/CCS/Report-a-problem  
**Form Type**: Multi-step wizard form (Govstack platform)  
**Authentication**: SSO (MyKitchener) - authenticated users skip contact info steps

---

## Issue Types (Step 1)

The form starts with selecting **one** issue type from radio buttons:

| Issue Type | Value (UUID) |
|------------|---------------|
| Graffiti | `a87cf194-b055-40dc-97b2-ad1101338789` |
| Illegal sign | `4a4cb9cd-70b2-431a-9008-b1702e2430ae` |
| Litter in a playground, park or trail | `be98faaf-3e7e-49c0-b581-ad1101338789` |
| Needles | `f9b38b49-dc12-447a-b248-ad1101338789` |
| Parking complaint | `e1451db1-98ca-4c82-bd2f-ad1101338789` |
| Property standards complaint | `1d651705-b965-48d6-86ec-ad1101338789` |
| Pothole | `035d892d-0bee-4012-ac1b-ad1101338789` |
| Sidewalk snow clearing | `878cb749-f900-46c3-8c2e-ae32013627d4` |
| Sidewalk trip hazard | `3f5c980a-9265-4437-a5d1-ad1101338789` |
| Trail surface maintenance | `fcf3a5bc-feaf-4126-94bf-ad1101338789` |
| Other | `84d7b292-8da8-4948-abf6-ad1101338789` |

**Required**: Yes  
**Selector**: `input[name="Q_f301a496-1419-4950-8605-ad11013358d7_0"]`  
**Continue Button**: `<button type="submit" name="_ACTION" value="Continue">`

---

## Step 2: Issue-Specific Details

After selecting an issue type and clicking Continue, fields change based on selection:

### Pothole
| Field Label | Field Type | Required | Selector |
|-------------|------------|----------|----------|
| Where is the pothole located? | TextField | Yes | `input[name="Q_be887341-c392-4d88-acda-ad11013b0cd0_0"]` |
| Please provide additional details about the location... | TextField | Yes | `input[name="Q_41f30d61-e166-40b6-9e18-ad11013b3b59_0"]` |
| What is the approximate size, depth and shape of the pothole? | TextField | Yes | `input[name="Q_70ecb92a-793c-4dee-b6e4-ad11013b58dc_0"]` |
| Would you like to include a photo of the pothole? | RadioButtonList | Yes | `input[name="Q_afafc15c-2411-4c02-9196-ecc43c27fea9_0"]` |

**Photo Options**:
- Yes: `e48f93c9-7f10-442c-b03d-c09f28c654b0`
- No: `1b92d1cd-ce40-443c-8193-1bd6b259be33`

### Graffiti
| Field Label | Field Type | Required |
|-------------|------------|----------|
| What is the location of the graffiti? | TextField | Yes |
| Where on the property, building, structure is the graffiti located? | TextField | Yes |
| Is the graffiti located on (choose one): | RadioButtonList | Yes |
| Would you like to include a photo of the graffiti? | RadioButtonList | Yes |

### Litter in a playground, park or trail
| Field Label | Field Type | Required |
|-------------|------------|----------|
| What is the name of the playground, park or trail...? (optional) | TextField | No |
| If you do not know the name..., what is the closest intersection or street address? | TextField | Yes |
| Where in the playground, park or trail is the litter located? | TextField | Yes |
| Please describe the litter: | TextField | Yes |
| Would you like to include a photo of the litter? | RadioButtonList | Yes |

### Needles
| Field Label | Field Type | Required |
|-------------|------------|----------|
| Where are the needles located? Provide as much information as you can... | TextField | Yes |

### Parking complaint
| Field Label | Field Type | Required |
|-------------|------------|----------|
| Where is the vehicle located? | TextField | Yes |
| Are you the owner or the tenant at the property? | RadioButtonList | Yes |
| Please describe the vehicle: | TextField | Yes |
| What would you like to report (choose one): | RadioButtonList | Yes |
| Would you like to include a photo of the parking infraction? | RadioButtonList | Yes |

### Sidewalk trip hazard
| Field Label | Field Type | Required |
|-------------|------------|----------|
| Where is the location of the tripping hazard? | TextField | Yes |
| Please describe the issue with the sidewalk: | TextField | Yes |
| Would you like to include a photo of the sidewalk trip hazard? | RadioButtonList | Yes |

### Trail surface maintenance
| Field Label | Field Type | Required |
|-------------|------------|----------|
| What is the name of the trail (or park the trail is located in)? (optional) | TextField | No |
| If you do not know the name..., what is the closest street address or intersection? | TextField | Yes |
| Where on the trail is the issue located? | TextField | Yes |
| Please describe the issue: | TextField | Yes |
| Would you like to include a photo of the trail issue? | RadioButtonList | Yes |

### Other
| Field Label | Field Type | Required |
|-------------|------------|----------|
| Please describe the problem: | TextArea | Yes |

---

## Step 3: Photo Upload (Conditional)

**Trigger**: When photo question is answered "Yes"

| Field Label | Field Type | Required |
|-------------|------------|----------|
| Upload photo | FileUpload | No |

---

## Step 4+: Contact Information

**Note**: This step was not observed in testing because SSO authentication is active. For non-authenticated users, expected fields:

- First Name
- Last Name  
- Email Address
- Phone Number
- (Optional) Address

---

## Step N: Submit

- Button: `<button type="submit" name="_ACTION" value="Submit">`
- Validation: All required fields must be filled
- Success: Shows "Thank you for submitting this problem." message

---

## Form Submission Details

### Hidden Fields
| Field | Value |
|-------|-------|
| `__RequestVerificationToken` | CSRF token (changes each request) |
| `FormId` | `f6e6e08c-f309-4f1c-bbf2-ad110132c378` |
| `PageIndex` | Starts at 0, increments with each step |
| `ssoActive` | `True` (when authenticated) |

### Request Flow
1. GET `/CSD/CCS/Report-a-problem` - Initial form load
2. POST with `_ACTION=Continue` - Proceed to next step
3. Form uses AJAX refresh (`_ACTION=REFRESH`) when selecting radio options
4. Each POST returns new token in response

### Selectors for Automation

**Issue Type Selection**:
```javascript
// Select pothole
page.click('input[value="035d892d-0bee-4012-ac1b-ad1101338789"]')
```

**Continue Button**:
```javascript
page.click('button[name="_ACTION"][value="Continue"]')
```

**Submit Button**:
```javascript
page.click('button[name="_ACTION"][value="Submit"]')
```

---

## Validation Notes

- All text fields trim whitespace on submit
- Required fields marked with `class="FRM_form-group required"`
- Form prevents navigation with unsaved changes (beforeunload event)
- When SSO is active, contact info is auto-populated and step is skipped

---

## Page Index Reference

| PageIndex | Step Description |
|-----------|------------------|
| 0 | Issue type selection (Step 1) |
| 1 | Issue-specific details (Step 2) |
| 2 | Photo upload or Contact info (Step 3) |
| N | Review/Submit |

---

*Document generated: 2026-03-15*
*Testing notes: SSO authentication was active during testing, so contact info steps were not observed.*