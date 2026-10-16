// Qualification adapter, not a UX oracle or a shipping host dispatcher.
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const assert = require('assert/strict');

(async () => {
  const [library, pairFile, output] = process.argv.slice(2);
  const spec = JSON.parse(fs.readFileSync(pairFile));
  assert.deepEqual(spec.readers.map(x => x.lens), ['ui', 'ux']);
  // Fail before browser/data operations when an adapter cannot isolate readers.
  assert.equal(spec.context_mode, 'isolated', 'separate browser contexts required');
  assert.equal(new Set(spec.readers.map(x => x.identity)).size, 2, 'distinct test identities required');
  const {chromium} = require(library);
  const browser = await chromium.launch({headless: true});
  fs.mkdirSync(output, {recursive: true});
  const contexts = [], records = [];
  let arrived = 0, release;
  const barrier = new Promise(resolve => { release = resolve; });
  try {
    await Promise.all(spec.readers.map(async reader => {
      const task = JSON.parse(fs.readFileSync(reader.task));
      const read = name => JSON.parse(fs.readFileSync(path.resolve(task.workspace, task.context.inputs[name].path)));
      const config = read('configuration'), env = read('environment');
      const context = await browser.newContext(); contexts.push(context);
      const contextId = crypto.randomUUID();
      await context.addCookies([{name: 'w5_identity', value: reader.identity, url: env.url}]);
      const page = await context.newPage();
      await page.goto(env.url + '/index.html');
      assert.equal(await page.evaluate(async () => (await (await fetch('/whoami')).json()).identity), reader.identity);
      assert.equal(await page.evaluate(() => localStorage.getItem('w5_context')), null);
      await page.evaluate(value => localStorage.setItem('w5_context', value), contextId);
      // Synchronise actual ready contexts; timings below exclude this barrier.
      if (++arrived === 2) release();
      await Promise.race([barrier, new Promise((_, reject) => setTimeout(() => reject(Error('context barrier timeout')), 15000).unref())]);
      if (spec.hold_lens === reader.lens) {
        fs.writeFileSync(path.join(output, 'browser-active'), reader.lens);
        const deadline = Date.now() + 30000;
        while (!fs.existsSync(path.join(output, 'continue'))) {
          if (fs.existsSync(path.join(output, 'stop'))) throw Error('owned browser actor stopped after cancellation');
          if (Date.now() > deadline) throw Error('controller did not settle owned browser');
          await new Promise(resolve => setTimeout(resolve, 50));
        }
      }
      const started = performance.now(), observations = [];
      for (const scenario of config.scenarios.filter(s => s.lens === reader.lens)) {
        await page.setViewportSize(scenario.viewport);
        const url = env.url.replace(/\/$/, '') + scenario.path;
        await page.goto(url);
        assert.equal(await page.evaluate(() => localStorage.getItem('w5_context')), contextId);
        const failures = [], facts = [];
        if (reader.lens === 'ui') {
          const metrics = await page.evaluate(() => ({viewport: innerWidth, scrollWidth: document.documentElement.scrollWidth,
            heading: document.querySelector('h1').textContent, inputLabel: document.querySelector('label').textContent,
            bodyColor: getComputedStyle(document.body).color, buttonBackground: getComputedStyle(document.querySelector('button')).backgroundColor}));
          if (metrics.scrollWidth > metrics.viewport) failures.push('Horizontal overflow');
          if (metrics.heading !== 'Notes' || metrics.inputLabel !== 'Note text') failures.push('Known heading/label missing');
          if (!(await page.locator('#empty').isVisible())) failures.push('UI inherited UX state');
          facts.push(JSON.stringify(metrics));
        } else {
          assert(await page.locator('#empty').isVisible());
          await page.keyboard.press('Tab');
          const focus = await page.evaluate(() => document.activeElement.id);
          const outline = await page.locator('#note').evaluate(e => getComputedStyle(e).outlineStyle);
          if (focus !== 'note' || outline === 'none') failures.push('Keyboard focus missing');
          const labels = await page.locator('#note').evaluate(e => [...e.labels].map(x => x.textContent));
          if (!labels.includes('Note text')) failures.push('Input label missing');
          await page.keyboard.press('Tab'); await page.keyboard.press('Enter');
          if (!(await page.locator('#error').isVisible())) failures.push('Empty submit error missing');
          await page.locator('#note').fill('A test note'); await page.locator('#save').click();
          if (!(await page.locator('#loading').isVisible())) failures.push('Loading state missing');
          await page.waitForTimeout(650);
          const success = await page.locator('#success').isVisible(), copy = await page.locator('#success').textContent();
          if (!success || copy !== 'Saved: A test note') failures.push('Save flow never reaches confirmation');
          facts.push(JSON.stringify({focus, outline, labels, success, copy}));
        }
        const screenshot = path.join(output, reader.lens + '-' + scenario.id + '.png');
        await page.screenshot({path: screenshot, fullPage: true});
        observations.push({scenario: scenario.id, viewport: scenario.viewport, url, failures, screenshot,
          screenshot_sha256: 'sha256:' + crypto.createHash('sha256').update(fs.readFileSync(screenshot)).digest('hex'),
          observations: facts.join('\n') + '\nActual DOM/browser metrics; screenshot captured, no LLM visual assessment claimed.'});
      }
      const own = await page.evaluate(async () => (await (await fetch('/notes')).json()));
      assert.equal(own.identity, reader.identity);
      if (reader.lens === 'ui') assert.deepEqual(own.notes, [], 'UX data leaked into UI identity');
      if (reader.lens === 'ux' && !observations.some(x => x.failures.length)) assert.deepEqual(own.notes, ['A test note']);
      records.push({lens: reader.lens, attempt: task.attempt_id, identity: reader.identity, context_id: contextId,
        started_ms: started, finished_ms: performance.now(), notes: own.notes, observations});
    }));
    const overlap = Math.min(...records.map(x => x.finished_ms)) - Math.max(...records.map(x => x.started_ms));
    assert(overlap > 0, 'actual browser work did not overlap');
    const result = {tool: 'Playwright ' + require(path.join(library, 'package.json')).version + ' / Chromium ' + browser.version(),
      scope: 'deterministic browser fixture; no LLM/model/visual judgement', overlap_ms: overlap,
      readers: records.sort((a, b) => a.lens.localeCompare(b.lens))};
    fs.writeFileSync(path.join(output, 'observations.json'), JSON.stringify(result, null, 2) + '\n');
    console.log(JSON.stringify(result));
  } finally {
    await Promise.all(contexts.map(c => c.close()));
    await browser.close();
  }
})().catch(error => {console.error(String(error)); process.exitCode = 1;});
