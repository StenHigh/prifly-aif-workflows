// Test-only adapter for the sealed notes fixture; not a generic UX oracle.
const fs=require('fs'),path=require('path');
(async()=>{
 const [library,taskFile,outDir]=process.argv.slice(2);
 const {chromium}=require(library);const task=JSON.parse(fs.readFileSync(taskFile));
 const read=n=>JSON.parse(fs.readFileSync(path.resolve(task.workspace,task.context.inputs[n].path)));
 const config=read('configuration'),environment=read('environment');
 const lens=(task.skill_refs[0].id.endsWith('/ui-bridge')||task.skill_refs[0].id.endsWith('/w6-product-ui-bridge'))?'ui':'ux';
 const browser=await chromium.launch({headless:true});fs.mkdirSync(outDir,{recursive:true});
 const observations=[];
 try{
  for(const scenario of config.scenarios.filter(s=>s.lens===lens)){
   const context=await browser.newContext({viewport:scenario.viewport});
   try{
    const page=await context.newPage(),url=environment.url.replace(/\/$/,'')+scenario.path;
    await page.goto(url,{waitUntil:'load'});
    const failures=[],notes=[];
    if(lens==='ui'){
     const metrics=await page.evaluate(()=>({viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,
      heading:document.querySelector('h1').textContent,bodyColor:getComputedStyle(document.body).color,
      buttonColor:getComputedStyle(document.querySelector('button')).color,buttonBackground:getComputedStyle(document.querySelector('button')).backgroundColor,
      label:document.querySelector('label').textContent,section:document.querySelector('section').getBoundingClientRect().toJSON()}));
     if(metrics.scrollWidth>metrics.viewport)failures.push(`Horizontal overflow: scrollWidth ${metrics.scrollWidth} > viewport ${metrics.viewport}`);
     notes.push(JSON.stringify(metrics));
     // Known fixture foreground/background colors, actual computed values above.
     notes.push('Declared design tokens: dark ink on white; white button text on blue. Screenshot requires visual inspection, DOM metrics alone are not a visual review.');
    }else{
     const empty=await page.locator('#empty').isVisible();if(!empty)failures.push('Initial empty state missing');
     await page.keyboard.press('Tab');const focus=await page.evaluate(()=>document.activeElement.id);
     const outline=await page.locator('#note').evaluate(e=>getComputedStyle(e).outlineStyle);
     if(focus!=='note'||outline==='none')failures.push('Keyboard input focus/outline missing');
     const label=await page.locator('#note').evaluate(e=>[...e.labels].map(x=>x.textContent));if(!label.includes('Note text'))failures.push('Input label missing');
     await page.keyboard.press('Tab');await page.keyboard.press('Enter');
     const error=await page.locator('#error').isVisible();if(!error)failures.push('Empty submit error missing');
     await page.locator('#note').fill('A test note');await page.locator('#save').click();
     const loading=await page.locator('#loading').isVisible();if(!loading)failures.push('Loading state missing');
     await page.waitForTimeout(650);
     const success=await page.locator('#success').isVisible(),copy=await page.locator('#success').textContent();
     if(!success||copy!=='Saved: A test note')failures.push('Save flow never reaches confirmation');
     notes.push(JSON.stringify({empty,focus,outline,label,error,loading,success,copy}));
    }
    const screenshot=path.join(outDir,lens+'-'+scenario.id+'.png');await page.screenshot({path:screenshot,fullPage:true});
    observations.push({scenario:scenario.id,viewport:scenario.viewport,url,observations:notes.join('\n'),failures,screenshot});
   }finally{await context.close()}
  }
  const result={lens,tool:'Playwright '+require(path.join(library,'package.json')).version+' / Chromium '+browser.version(),observations};
  fs.writeFileSync(path.join(outDir,'observations.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
 }finally{await browser.close()}
})().catch(e=>{console.error(String(e));process.exitCode=1});
