// Actual browser adapter for the notes fixture. Model reviewers choose verdicts.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
(async()=>{
 const library=process.argv[2],request=JSON.parse(fs.readFileSync(0,'utf8')),{chromium}=require(library);
 const browser=await chromium.launch({headless:true});
 try{
  if(request.operation==='admit'){
   const a=await browser.newContext(),b=await browser.newContext();assert.notEqual(a,b);
   await a.close();await b.close();console.log(JSON.stringify({available:true}));return;
  }
  const config=request.configuration,env=request.environment,binding=request.browser_session,lens=binding.lens;
  const folder=path.join(request.output_directory,crypto.randomUUID());fs.mkdirSync(folder,{recursive:true});
  const context=await browser.newContext({serviceWorkers:'block'});
  await context.route('**/*',route=>new URL(route.request().url()).origin===env.url?route.continue():route.abort());
  await context.addCookies([{name:'aif_identity',value:binding.allocation.token,url:env.url}]);
  try{
   const page=await context.newPage();await page.goto(env.url+'/index.html');
   const identity=await page.evaluate(async()=>await (await fetch('/__identity')).json());
   assert.equal(identity.identity_id,binding.identity_id);assert.equal(identity.context_id,binding.context_id);assert.equal(identity.session,env.session);
   assert.equal(await page.evaluate(()=>localStorage.getItem('reader_context')),null);
   await page.evaluate(value=>localStorage.setItem('reader_context',value),binding.context_id);
   if(request._hold){
    fs.writeFileSync(path.join(request.output_directory,'browser-active'),'owned UX context');
    const deadline=Date.now()+20000;
    while(!fs.existsSync(path.join(request.output_directory,'browser-continue'))){
     if(fs.existsSync(path.join(request.output_directory,'browser-stop')))throw Error('Owned browser stopped after native cancellation');
     if(Date.now()>deadline)throw Error('Controller did not settle owned browser');
     await new Promise(resolve=>setTimeout(resolve,50));
    }
   }
   const observations=[];
   const enabled=new Set(request.request.checks.filter(c=>c.enabled&&c.applicable).map(c=>c.id));
   for(const scenario of config.scenarios.filter(s=>s.lens===lens&&enabled.has(s.check_id))){
    await page.setViewportSize(scenario.viewport);const url=env.url+scenario.path;await page.goto(url);
    assert.equal(await page.evaluate(()=>localStorage.getItem('reader_context')),binding.context_id);
    const facts=[],failures=[];
    if(lens==='ui'){
     const metrics=await page.evaluate(()=>({viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,
      heading:document.querySelector('h1').textContent,label:document.querySelector('label').textContent,
      bodyColor:getComputedStyle(document.body).color,bodyBackground:getComputedStyle(document.body).backgroundColor,
      buttonColor:getComputedStyle(document.querySelector('button')).color,buttonBackground:getComputedStyle(document.querySelector('button')).backgroundColor}));
     if(metrics.scrollWidth>metrics.viewport)failures.push('Horizontal overflow');
     if(!(await page.locator('#empty').isVisible()))failures.push('Reader inherited another form state');
     facts.push(JSON.stringify(metrics));
    }else{
     const empty=await page.locator('#empty').isVisible();if(!empty)failures.push('Initial empty state missing');
     await page.keyboard.press('Tab');const focus=await page.evaluate(()=>document.activeElement.id);
     const outline=await page.locator('#note').evaluate(e=>getComputedStyle(e).outlineStyle);
     const labels=await page.locator('#note').evaluate(e=>[...e.labels].map(x=>x.textContent));
     if(focus!=='note'||outline==='none')failures.push('Keyboard focus/outline missing');
     if(!labels.includes('Note text'))failures.push('Input label missing');
     await page.keyboard.press('Tab');await page.keyboard.press('Enter');
     const error=await page.locator('#error').isVisible();if(!error)failures.push('Empty submit error missing');
     await page.locator('#note').fill('A test note');await page.locator('#save').click();
     const loading=await page.locator('#loading').isVisible();if(!loading)failures.push('Loading state missing');
     await page.waitForTimeout(650);
     const success=await page.locator('#success').isVisible(),copy=await page.locator('#success').textContent();
     if(!success||copy!=='Saved: A test note')failures.push('Save flow never reaches confirmation');
     facts.push(JSON.stringify({empty,focus,outline,labels,error,loading,success,copy}));
    }
    const screenshot=path.join(folder,lens+'-'+scenario.id+'.png');await page.screenshot({path:screenshot,fullPage:true});
    observations.push({scenario:scenario.id,viewport:scenario.viewport,url,observations:facts.join('\n'),failures,screenshot,
      screenshot_sha256:'sha256:'+crypto.createHash('sha256').update(fs.readFileSync(screenshot)).digest('hex')});
   }
   const result={protocol:'aif-feature-browser/1',status:'ready',lens,context_id:binding.context_id,identity_id:binding.identity_id,
    tool:'Playwright '+require(path.join(library,'package.json')).version+' / Chromium '+browser.version(),observations,
    note:'Actual observations and screenshots; the reviewer must inspect images and choose its own assessment.'};
   fs.writeFileSync(path.join(folder,'observations.json'),JSON.stringify(result,null,2)+'\n');
   fs.writeFileSync(path.join(request.output_directory,'observations.json'),JSON.stringify(result,null,2)+'\n');
   console.log(JSON.stringify(result));
  }finally{await context.close()}
 }finally{await browser.close()}
})().catch(error=>{console.error(String(error));process.exitCode=1});
