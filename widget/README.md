# Municipal Chat Widget

Embeddable chat widget for Kitchener/Waterloo municipal services.

## Quick Start

Add this script to your website:

```html
<script src="https://your-cdn.com/municipal-chat.js"></script>
```

Or use the standalone HTML file for testing.

## Features

- ✅ Self-contained - No build step required
- ✅ Responsive - Works on mobile and desktop
- ✅ Accessible - Keyboard navigation support
- ✅ Customizable - API URL can be configured
- ✅ Persistent - Remembers user session in localStorage

## Configuration

Set the API URL before loading the script:

```html
<script>
  window.municipalChatApiUrl = 'http://localhost:8000';
</script>
<script src="municipal-chat.js"></script>
```

## API

The widget exposes a global `MunicipalChat` object:

```javascript
MunicipalChat.open()   // Open the chat widget
MunicipalChat.close()  // Close the chat widget
MunicipalChat.destroy() // Remove the widget from page
```

## Demo Mode

When the backend API is unavailable, the widget works in demo mode with preset responses for:
- Garbage collection
- Parking
- Permits
- Property taxes
- 311 services