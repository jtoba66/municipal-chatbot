const { chromium } = require('playwright');

const FRONTEND = 'https://shine-royalty-california-heat.trycloudflare.com';

const results = [];

async function runTest(name, testFn) {
  try {
    await testFn();
    results.push({ name, status: 'PASS' });
    console.log(`✅ PASS: ${name}`);
  } catch (err) {
    results.push({ name, status: 'FAIL', error: err.message });
    console.log(`❌ FAIL: ${name} - ${err.message}`);
  }
}

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function getChatInput(page) {
  const selectors = [
    'input[class*="chat"]',
    'input[placeholder*="Type" i]',
    'input[placeholder*="message" i]',
    'textarea',
    'input[type="text"]',
    '[contenteditable="true"]'
  ];
  for (const sel of selectors) {
    try {
      const el = await page.$(sel);
      if (el && await el.isVisible()) return sel;
    } catch (e) {}
  }
  return null;
}

async function test1_PageLoad() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  page.on('pageerror', err => errors.push(err.message));
  
  await page.goto(FRONTEND, { waitUntil: 'networkidle', timeout: 30000 });
  await sleep(2000);
  
  if (errors.length > 0) throw new Error(`Console errors: ${errors.join(', ')}`);
  await browser.close();
}

async function test2_WelcomeScreen() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(FRONTEND, { waitUntil: 'networkidle', timeout: 30000 });
  
  await page.$eval('input', el => el.value = 'Test User').catch(() => {});
  await page.$eval('input[type="email"]', el => el.value = 'test@test.com').catch(() => {});
  await page.$eval('button', el => el.click());
  await sleep(3000);
  
  const chatInputSel = await getChatInput(page);
  if (!chatInputSel) throw new Error('Chat input not found after clicking Start');
  
  await browser.close();
}

async function test3_AddressQueryAsk() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(FRONTEND, { waitUntil: 'networkidle', timeout: 30000 });
  
  await page.$eval('input', el => el.value = 'Test User').catch(() => {});
  await page.$eval('input[type="email"]', el => el.value = 'test@test.com').catch(() => {});
  await page.$eval('button', el => el.click());
  await sleep(3000);
  
  const chatInputSel = await getChatInput(page);
  if (!chatInputSel) throw new Error('Chat input not found');
  
  await page.fill(chatInputSel, 'When is garbage at my area?');
  await page.press(chatInputSel, 'Enter');
  await sleep(5000);
  
  const content = await page.textContent('body');
  console.log('  [DEBUG] Response content:', content.substring(0, 500));
  
  // Check if response contains address-related content
  const lower = content.toLowerCase();
  if (!lower.includes('address') && !lower.includes('street') && !lower.includes('location')) {
    throw new Error('Bot did not ask for address');
  }
  
  await browser.close();
}

async function test4_AddressQueryGive() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(FRONTEND, { waitUntil: 'networkidle', timeout: 30000 });
  
  await page.$eval('input', el => el.value = 'Test User').catch(() => {});
  await page.$eval('input[type="email"]', el => el.value = 'test@test.com').catch(() => {});
  await page.$eval('button', el => el.click());
  await sleep(3000);
  
  const chatInputSel = await getChatInput(page);
  if (!chatInputSel) throw new Error('Chat input not found');
  
  await page.fill(chatInputSel, 'When is garbage at my area?');
  await page.press(chatInputSel, 'Enter');
  await sleep(3000);
  
  // Check response first
  let content = await page.textContent('body');
  console.log('  [DEBUG] After garbage Q:', content.substring(0, 300));
  
  // Try to find chat input again - use broader selector
  const inputEl = await page.$('input');
  if (inputEl) {
    await inputEl.fill('110 Fergus Avenue');
    await inputEl.press('Enter');
    await sleep(4000);
    
    content = await page.textContent('body');
    console.log('  [DEBUG] After address:', content.substring(0, 300));
    
    if (!content.toLowerCase().includes('tuesday')) {
      throw new Error('Bot did not return Tuesday');
    }
  } else {
    throw new Error('Could not find input after first response');
  }
  
  await browser.close();
}

async function test5_TicketQuery() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(FRONTEND, { waitUntil: 'networkidle', timeout: 30000 });
  
  await page.$eval('input', el => el.value = 'Test User').catch(() => {});
  await page.$eval('input[type="email"]', el => el.value = 'test@test.com').catch(() => {});
  await page.$eval('button', el => el.click());
  await sleep(3000);
  
  const chatInputSel = await getChatInput(page);
  if (!chatInputSel) throw new Error('Chat input not found');
  
  await page.fill(chatInputSel, 'How do I pay my parking ticket?');
  await page.press(chatInputSel, 'Enter');
  await sleep(4000);
  
  const content = await page.textContent('body');
  if (!content.toLowerCase().includes('pay')) throw new Error('No payment info returned');
  
  await browser.close();
}

async function test6_LocationQuery() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(FRONTEND, { waitUntil: 'networkidle', timeout: 30000 });
  
  await page.$eval('input', el => el.value = 'Test User').catch(() => {});
  await page.$eval('input[type="email"]', el => el.value = 'test@test.com').catch(() => {});
  await page.$eval('button', el => el.click());
  await sleep(3000);
  
  const chatInputSel = await getChatInput(page);
  if (!chatInputSel) throw new Error('Chat input not found');
  
  await page.fill(chatInputSel, 'Where is the nearest recycling depot?');
  await page.press(chatInputSel, 'Enter');
  await sleep(4000);
  
  const content = await page.textContent('body');
  if (!content.toLowerCase().includes('recycl')) throw new Error('No recycling info returned');
  
  await browser.close();
}

async function test7_GeneralQuery() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(FRONTEND, { waitUntil: 'networkidle', timeout: 30000 });
  
  await page.$eval('input', el => el.value = 'Test User').catch(() => {});
  await page.$eval('input[type="email"]', el => el.value = 'test@test.com').catch(() => {});
  await page.$eval('button', el => el.click());
  await sleep(3000);
  
  const chatInputSel = await getChatInput(page);
  if (!chatInputSel) throw new Error('Chat input not found');
  
  await page.fill(chatInputSel, 'How do I apply for a building permit?');
  await page.press(chatInputSel, 'Enter');
  await sleep(4000);
  
  const content = await page.textContent('body');
  if (!content.toLowerCase().includes('permit')) throw new Error('No permit info returned');
  
  await browser.close();
}

(async () => {
  console.log('🧪 Starting Municipal Chatbot Tests\n');
  
  await runTest('1. Page Load', test1_PageLoad);
  await runTest('2. Welcome Screen', test2_WelcomeScreen);
  await runTest('3. Address Query - Ask for address', test3_AddressQueryAsk);
  await runTest('4. Address Query - Give address', test4_AddressQueryGive);
  await runTest('5. Ticket Query', test5_TicketQuery);
  await runTest('6. Location Query', test6_LocationQuery);
  await runTest('7. General Query', test7_GeneralQuery);
  
  console.log('\n📊 Summary:');
  const passed = results.filter(r => r.status === 'PASS').length;
  const failed = results.filter(r => r.status === 'FAIL').length;
  console.log(`Passed: ${passed}/${results.length}`);
  console.log(`Failed: ${failed}/${results.length}`);
  
  let md = '# Municipal Chatbot Automated Test Results\n\n';
  md += `**Date:** ${new Date().toISOString()}\n`;
  md += `**Frontend:** ${FRONTEND}\n\n`;
  md += '## Test Results\n\n';
  md += '| Test | Status |\n|------|--------|\n';
  results.forEach(r => {
    md += `| ${r.name} | ${r.status === 'PASS' ? '✅ PASS' : `❌ FAIL: ${r.error}`} |\n`;
  });
  md += `\n## Summary\n- **Passed:** ${passed}/${results.length}\n- **Failed:** ${failed}/${results.length}\n`;
  
  const fs = require('fs');
  fs.writeFileSync('/home/joe/workspace-scout/municipal-chatbot/automated-test-results.md', md);
  console.log('\n📄 Results saved to automated-test-results.md');
})();