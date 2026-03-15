# Kitchener/Waterloo Municipal Portal Research

Research Date: March 2025
Purpose: Find publicly accessible municipal services (no login required) for chatbot integration

---

## Summary Table

| Feature | Portal URL | Login Required? | Fields Needed | Automatable? |
|---------|-----------|-----------------|---------------|---------------|
| Permit status (Kitchener) | https://www.kitchener.ca/maps | **No** | Address (for map search) | ✅ Yes |
| Permit status (Waterloo) | https://opendata-city-of-waterloo.opendata.arcgis.com/ | No | N/A (browse datasets) | ✅ Yes (API) |
| Permit status (Cambridge) | https://permits.cambridge.ca/searchPermit | **Yes** | Must sign in | ❌ No |
| Service request (Kitchener) | https://form.kitchener.ca/CSD/CCS/Report-a-problem | No (but account helps) | Address, description | ⚠️ Limited |
| Service request (Waterloo) | N/A - no 311 system | - | - | - |
| Road closures | https://www.waterloo.ca/roads-and-cycling/check-road-sidewalk-and-trail-closures/ | **No** | None (view map/table) | ✅ Yes |
| Road closures (Region) | https://www.regionofwaterloo.ca/en/living-here/construction-and-road-closures.aspx | **No** | None (view all) | ✅ Yes |
| Utility lookup (Kitchener) | https://www.kitchenerutilities.ca/en/my-account.aspx | **Yes** | Account # | ❌ No |
| Utility lookup (Waterloo) | https://cityofwaterloo.idoxs.ca/ | **Yes** | Account code | ❌ No |
| Community events (Waterloo) | https://www.waterloo.ca/create-waterloo/city-events/ | **No** | None | ✅ Yes |
| Community events (Kitchener) | https://www.kitchener.ca/en/things-to-do.aspx | **No** | None | ✅ Yes |
| Property tax lookup | N/A | **Yes** | Account required | ❌ No |
| Parking ticket (Waterloo) | https://amps.waterloo.ca/pay | **No** | License plate + Ticket # | ✅ Yes |
| Parking ticket (Kitchener) | https://www.kitchener.ca/bylaws-and-enforcement/parking-tickets/ | Unknown | Unknown | Unknown |

---

## Detailed Findings

### 1. Permit Status Lookup

#### Kitchener ✅ PUBLIC
- **URL**: https://www.kitchener.ca/maps
- **Method**: Interactive mapping tool → Property Viewer → Enable "Building Permits" layer
- **Data**: Permits from 1986 to today, updated daily
- **No login required** - anyone can view the map and search by address
- **Open Data API**: https://open-kitchenergis.opendata.arcgis.com/datasets/KitchenerGIS::building-permits

#### Waterloo ✅ PUBLIC (Open Data)
- **URL**: https://opendata-city-of-waterloo.opendata.arcgis.com/
- **Search**: "building permits"
- **Contains**: Issued, Complete, or Occupancy Final permits

#### Cambridge ❌ LOGIN REQUIRED
- **URL**: https://permits.cambridge.ca/searchPermit
- **Status**: Shows "Your session is about to expire" - requires authentication

---

### 2. Service Request Tracking (311)

#### Kitchener ⚠️ LIMITED
- **URL**: https://form.kitchener.ca/CSD/CCS/Report-a-problem
- **Login**: Not required to submit, but MyKitchener account helps track status
- **Fields**: Address, description, photos (optional)
- **Tracking**: With account, can track via MyKitchener dashboard

#### Waterloo
- **No 311 system** - uses direct contact via website
- **URL**: https://www.waterloo.ca/council-and-city-administration/call-or-visit-us/

---

### 3. Road Closure Alerts

#### Waterloo ✅ PUBLIC
- **URL**: https://www.waterloo.ca/roads-and-cycling/check-road-sidewalk-and-trail-closures/
- **Features**:
  - Interactive map (shows Kitchener, Waterloo, Region closures)
  - Current road closure table
  - Future road closure table
  - Sidewalk/trail closures
- **No login required**

#### Region of Waterloo ✅ PUBLIC
- **URL**: https://www.regionofwaterloo.ca/en/living-here/construction-and-road-closures.aspx
- **Open Data**: https://rowopendata-rmw.opendata.arcgis.com/maps/City-of-Waterloo::traffic-closures
- **Updates**: Daily at 7am, 1pm, 5pm

---

### 4. Utility/Bill Lookup

#### Kitchener Utilities ❌ LOGIN REQUIRED
- **URL**: https://www.kitchenerutilities.ca/en/my-account.aspx
- **Status**: Requires online account registration
- **Note**: Green Button data available for download after login

#### Waterloo ❌ LOGIN REQUIRED
- **URL**: https://cityofwaterloo.idoxs.ca/
- **Status**: Requires My Account (account code from bill)
- **Note**: Sign up for e-billing available but still requires account

---

### 5. Community Events

#### Waterloo ✅ PUBLIC
- **URL**: https://www.waterloo.ca/create-waterloo/city-events/
- **Content**: Free, family-friendly city events
- **No login required** - simple HTML page with event listings

#### Kitchener ✅ PUBLIC
- **URL**: https://www.kitchener.ca/en/things-to-do.aspx
- **Content**: Events calendar

---

### 6. Property Tax Lookup

#### General ❌ LOGIN REQUIRED
- Both Kitchener and Waterloo require account creation to view tax details
- **Kitchener**: https://www.kitchener.ca/taxes-utilities-and-finance/property-taxes/
- **Waterloo**: https://www.waterloo.ca/en/government/property-taxes-and-finance.aspx
- Tax certificates available (official document showing outstanding balance) but require request process

---

### 7. Parking Ticket Lookup

#### Waterloo ✅ PUBLIC (Lookup Only)
- **URL**: https://amps.waterloo.ca/pay
- **Fields**: License plate + Ticket number
- **Note**: "Additional outstanding parking tickets... may not be displayed if issued within last 15 days"
- **Payment**: Requires credit card (Visa, MasterCard, Amex)

#### Kitchener
- **URL**: https://www.kitchener.ca/bylaws-and-enforcement/parking-tickets/
- Requires further investigation for specific lookup tool

---

## Recommendations for Chatbot

### HIGH PRIORITY - Automatable Now:
1. **Road Closures** - Public API/map, easiest to integrate
2. **Kitchener Building Permits** - Public map, good data source
3. **Waterloo Community Events** - Public HTML, easy to scrape
4. **Parking Ticket Lookup** - Waterloo works with plate+# lookup

### MEDIUM PRIORITY - Requires Account:
1. **Service Request Tracking** - Would need users to provide account or use reference #

### LOW PRIORITY - Not Recommended:
- Utility lookups (require login)
- Property tax (require login)
- Cambridge permits (require login)

---

## Data Sources (APIs & Open Data)

- Kitchener Open Data: https://open-kitchenergis.opendata.arcgis.com/
- Waterloo Open Data: https://data.waterloo.ca/
- Region of Waterloo Open Data: https://rowopendata-rmw.opendata.arcgis.com/