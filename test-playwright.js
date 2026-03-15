const { chromium } = require('playwright');

async function runTests() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  let errors = [];
  
  // Capture console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(`Console Error: ${msg.text()}`);
    }
  });
  
  page.on('pageerror', err => {
    errors.push(`Page Error: ${err.message}`);
  });

  console.log('=== MUNICIPAL CHATBOT PLAYWRIGHT TEST ===\n');
  
  // Test 1: Load the page
  console.log('Test 1: Loading the page...');
  try {
    await page.goto('https://shine-royalty-california-heat.trycloudflare.com', { timeout: 30000 });
    console.log('✓ Page loaded successfully');
  } catch (e) {
    console.log(`✗ Failed to load page: ${e.message}`);
    await browser.close();
    process.exit(1);
  }
  
  // Wait a moment for any JS to load
  await page.waitForTimeout(2000);
  
  // Test 2: Enter user info
  console.log('\nTest 2: Entering user info...');
  try {
    // Look for name input
    const nameInput = await page.locator('input[name="name"], input[placeholder*="name" i], input#name').first();
    await nameInput.waitFor({ timeout: 5000 });
    await nameInput.fill('Test User');
    console.log('✓ Filled name');
    
    // Look for email input
    const emailInput = await page.locator('input[name="email"], input[placeholder*="email" i], input#email').first();
    await emailInput.fill('test@example.com');
    console.log('✓ Filled email');
    
    // Click Start Chatting button
    const startButton = await page.locator('button:has-text("Start"), button:has-text("Chat"), button[type="submit"]').first();
    await startButton.click();
    console.log('✓ Clicked Start Chatting');
    
    await page.waitForTimeout(2000);
    console.log('✓ User info submitted');
  } catch (e) {
    console.log(`✗ Failed to enter user info: ${e.message}`);
    errors.push(`User Info Entry Error: ${e.message}`);
  }
  
  // Test 3: Address query - garbage
  console.log('\nTest 3: Testing garbage query...');
  try {
    const chatInput = await page.locator('input[placeholder*="message" i], input[type="text"]').last();
    await chatInput.fill('When is garbage at my home?');
    await chatInput.press('Enter');
    console.log('✓ Sent garbage query');
    
    await page.waitForTimeout(3000);
    
    // Check if it asks for address
    const pageContent = await page.textContent('body');
    if (pageContent.toLowerCase().includes('address')) {
      console.log('✓ System asked for address');
      
      // Enter address
      await chatInput.fill('110 Fergus Avenue');
      await chatInput.press('Enter');
      console.log('✓ Sent address');
      
      await page.waitForTimeout(3000);
      
      const responseContent = await page.textContent('body');
      if (responseContent.toLowerCase().includes('tuesday')) {
        console.log('✓ Got Tuesday response');
      } else {
        console.log('✗ Did not get Tuesday response');
        errors.push('Garbage query: Expected Tuesday response');
      }
    } else {
      console.log('✗ System did not ask for address');
      errors.push('Garbage query: Did not ask for address');
    }
  } catch (e) {
    console.log(`✗ Garbage query failed: ${e.message}`);
    errors.push(`Garbage Query Error: ${e.message}`);
  }
  
  // Test 4: Parking ticket query
  console.log('\nTest 4: Testing parking ticket query...');
  try {
    const chatInput = await page.locator('input[placeholder*="message" i], input[type="text"]').last();
    await chatInput.fill('How do I pay my parking ticket?');
    await chatInput.press('Enter');
    console.log('✓ Sent parking ticket query');
    
    await page.waitForTimeout(3000);
    
    const responseContent = await page.textContent('body');
    if (responseContent.toLowerCase().includes('pay') || responseContent.toLowerCase().includes('ticket') || responseContent.toLowerCase().includes('online')) {
      console.log('✓ Got payment info');
    } else {
      console.log('✗ Did not get payment info');
      errors.push('Parking ticket query: No payment info returned');
    }
  } catch (e) {
    console.log(`✗ Parking ticket query failed: ${e.message}`);
    errors.push(`Parking Ticket Query Error: ${e.message}`);
  }
  
  // Test 5: Location query - recycling depot
  console.log('\nTest 5: Testing recycling depot query...');
  try {
    const chatInput = await page.locator('input[placeholder*="message" i], input[type="text"]').last();
    await chatInput.fill('Where is the nearest recycling depot?');
    await chatInput.press('Enter');
    console.log('✓ Sent recycling depot query');
    
    await page.waitForTimeout(3000);
    
    const responseContent = await page.textContent('body');
    if (responseContent.toLowerCase().includes('recycling') || responseContent.toLowerCase().includes('depot') || responseContent.toLowerCase().includes('location') || responseContent.toLowerCase().includes('facility')) {
      console.log('✓ Got facility info');
    } else {
      console.log('✗ Did not get facility info');
      errors.push('Recycling depot query: No facility info returned');
    }
  } catch (e) {
    console.log(`✗ Recycling depot query failed: ${e.message}`);
    errors.push(`Recycling Depot Query Error: ${e.message}`);
  }
  
  // Test 6: General query - building permit
  console.log('\nTest 6: Testing building permit query...');
  try {
    const chatInput = await page.locator('input[placeholder*="message" i], input[type="text"]').last();
    await chatInput.fill('How do I apply for a building permit?');
    await chatInput.press('Enter');
    console.log('✓ Sent building permit query');
    
    await page.waitForTimeout(3000);
    
    const responseContent = await page.textContent('body');
    if (responseContent.toLowerCase().includes('permit') || responseContent.toLowerCase().includes('apply') || responseContent.toLowerCase().includes('building')) {
      console.log('✓ Got building permit info');
    } else {
      console.log('✗ Did not get building permit info');
      errors.push('Building permit query: No info returned');
    }
  } catch (e) {
    console.log(`✗ Building permit query failed: ${e.message}`);
    errors.push(`Building Permit Query Error: ${e.message}`);
  }
  
  // Summary
  console.log('\n=== TEST RESULTS ===');
  console.log(`Total errors: ${errors.length}`);
  
  if (errors.length > 0) {
    console.log('\nErrors found:');
    errors.forEach(e => console.log(`  - ${e}`));
  }
  
  await browser.close();
  console.log('\nTest completed.');
}

runTests().catch(err => {
  console.error('Test failed:', err);
  process.exit(1);
});