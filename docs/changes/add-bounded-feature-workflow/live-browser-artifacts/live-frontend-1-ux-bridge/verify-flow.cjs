const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('/tmp/w2-browser/node_modules/playwright');

(async () => {
  const root = path.resolve(__dirname, '..');
  const task = JSON.parse(fs.readFileSync(path.join(root, 'task.json')));
  const readInput = name => JSON.parse(fs.readFileSync(path.join(root, task.context.inputs[name].path)));
  const configuration = readInput('configuration');
  const environment = readInput('environment');
  const scenario = configuration.scenarios.find(s => s.lens === 'ux' && s.check_id === 'ux_acceptance' && s.id === 'flow');
  const url = environment.url.replace(/\/$/, '') + scenario.path;
  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext({ viewport: scenario.viewport });
    const page = await context.newPage();
    const pageErrors = [];
    page.on('pageerror', error => pageErrors.push(error.message));
    await page.goto(url);
    const snapshot = () => page.evaluate(() => {
      const visible = id => !document.getElementById(id).hidden;
      const note = document.getElementById('note');
      return {
        focus: document.activeElement.id,
        outline: getComputedStyle(document.activeElement).outlineStyle,
        labels: Array.from(note.labels, label => label.textContent),
        inputValue: note.value,
        empty: visible('empty'), error: visible('error'), loading: visible('loading'), success: visible('success'),
        errorText: document.getElementById('error').textContent,
        errorRole: document.getElementById('error').getAttribute('role'),
        loadingRole: document.getElementById('loading').getAttribute('role'),
        successRole: document.getElementById('success').getAttribute('role'),
        successText: document.getElementById('success').textContent,
        saveDisabled: document.getElementById('save').disabled
      };
    });
    const initial = await snapshot();
    await page.screenshot({ path: path.join(__dirname, 'flow-initial.png') });
    await page.keyboard.press('Tab');
    const firstTab = await snapshot();
    await page.keyboard.press('Tab');
    const secondTab = await snapshot();
    await page.keyboard.press('Enter');
    const invalid = await snapshot();
    await page.screenshot({ path: path.join(__dirname, 'flow-error.png') });
    await page.keyboard.type('A test note');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter');
    const pending = await snapshot();
    await page.screenshot({ path: path.join(__dirname, 'flow-loading.png') });
    await page.locator('#success').waitFor({ state: 'visible' });
    const complete = await snapshot();
    await page.screenshot({ path: path.join(__dirname, 'flow-complete.png') });
    const observations = { scenario: scenario.id, viewport: scenario.viewport, url, initial, firstTab, secondTab, invalid, pending, complete, pageErrors };
    fs.writeFileSync(path.join(__dirname, 'keyboard-observations.json'), JSON.stringify(observations, null, 2) + '\n');
    console.log(JSON.stringify(observations));
    await context.close();
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
