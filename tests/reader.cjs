/* Run against a built site served over HTTP. Playwright is a QA-only dependency. */
const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const base = (process.env.MINI_TEST_URL || 'http://127.0.0.1:8765/').replace(/\/?$/, '/');
const readingKey = 'mini-novels:reading:v1';
const first = 'stories/016_ship_without_a_front_01.html';
const fifth = 'stories/020_ship_without_a_front_05.html';
const report = [];
const pass = message => { report.push(message); console.log('PASS', message); };
(async () => {
  const browser = await chromium.launch({headless:true, ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH} : {})});
  try {
    const ctx = await browser.newContext({viewport:{width:1280,height:900}});
    const p = await ctx.newPage();
    const errors=[];
    p.on('pageerror',error=>errors.push(error.message));
    await p.goto(base);
    const total = await p.locator('[data-work]').count();
    const shorts = await p.locator('[data-kind="short"]').count();
    const serials = await p.locator('[data-kind="serial"]').count();
    await p.getByRole('button',{name:'短編',exact:true}).click();
    assert.equal(await p.locator('[data-work]:visible').count(),shorts);
    await p.getByRole('button',{name:'連載・中編',exact:true}).click();
    assert.equal(await p.locator('[data-work]:visible').count(),serials);
    await p.getByRole('button',{name:'すべて',exact:true}).click();
    await p.getByRole('searchbox').fill('型推論');
    assert.equal(await p.locator('[data-work]:visible').count(),1);
    await p.getByRole('searchbox').fill('見つからない作品123');
    assert(await p.locator('.empty-search').isVisible());
    await p.getByRole('button',{name:'検索をリセット'}).click();
    assert.equal(await p.locator('[data-work]:visible').count(),total);
    pass('Catalog search, filters, empty state, and reset');

    await p.goto(base+fifth);
    await p.getByRole('button',{name:'表示',exact:true}).click();
    await p.getByRole('button',{name:'夜',exact:true}).click();
    await p.getByRole('button',{name:'特大',exact:true}).click();
    await p.getByRole('button',{name:'ゴシック',exact:true}).click();
    assert.equal(await p.locator('html').getAttribute('data-theme'),'night');
    assert.equal(await p.getByRole('button',{name:'夜',exact:true}).getAttribute('aria-pressed'),'true');
    await p.keyboard.press('Escape');
    assert.equal(await p.locator('dialog[open]').count(),0);
    assert.equal(await p.evaluate(()=>document.activeElement.textContent.trim()),'あ 表示');
    await p.reload();
    assert.equal(await p.locator('html').getAttribute('data-size'),'xlarge');
    assert.equal(await p.locator('html').getAttribute('data-font'),'sans');
    assert.equal(await p.locator('html').getAttribute('data-theme'),'night');
    await p.getByRole('button',{name:'表示',exact:true}).click();
    await p.getByRole('button',{name:'標準の表示に戻す'}).click();
    await p.keyboard.press('Escape');
    pass('Reading settings persist, pressed state and Escape/focus return');

    await p.getByRole('button',{name:'目次',exact:true}).click();
    await p.locator('#contents-dialog').getByRole('link',{name:'二',exact:true}).click();
    assert.equal(await p.locator('dialog[open]').count(),0);
    assert(p.url().endsWith('#section-3'));
    await p.waitForTimeout(400);
    assert(await p.evaluate(()=>scrollY>1000));
    pass('Section navigation closes the dialog and resolves original anchors');

    await p.locator('#p-40').evaluate(node=>node.scrollIntoView());
    await p.waitForTimeout(400);
    const saved = await p.evaluate(key=>JSON.parse(localStorage.getItem(key))['020_ship_without_a_front_05'],readingKey);
    assert(saved.anchor);
    await p.goto(base);
    assert(await p.locator('[data-continue]').isVisible());
    assert((await p.locator('.continue-link').getAttribute('href')).endsWith('#resume'));
    await p.locator('.continue-link').click();
    await p.waitForFunction(()=>scrollY>1000);
    await p.waitForTimeout(1800);
    const top = await p.locator('#'+saved.anchor).evaluate(node=>node.getBoundingClientRect().top);
    assert(Math.abs(top-32)<100,`restored block top=${top}`);
    pass('Reading position saves and restores through the home page');

    await p.setViewportSize({width:390,height:844});
    await p.waitForTimeout(400);
    await p.goto(base+fifth+'#resume');
    await p.waitForTimeout(1800);
    const mobileTop = await p.locator('#'+saved.anchor).evaluate(node=>node.getBoundingClientRect().top);
    assert(Math.abs(mobileTop-32)<100,`mobile restored block top=${mobileTop}`);
    pass('Paragraph-based resume survives a changed viewport');

    await p.goto(base+first);
    await p.locator('#story-end').evaluate(node=>node.scrollIntoView());
    await p.waitForTimeout(400);
    await p.goto(base);
    assert((await p.locator('.continue-link').getAttribute('href')).includes('017_ship_without_a_front_02'));
    pass('Finishing an episode offers the next episode');

    await p.goto(base+'archive/stories/008_summer_of_type_inference.html');
    assert(await p.locator('.archive-notice').isVisible());
    const editionHref = await p.locator('.edition-link a').getAttribute('href');
    assert(editionHref.endsWith('stories/008_summer_of_type_inference.html'));
    await p.locator('#p-20').evaluate(node=>node.scrollIntoView());
    await p.waitForTimeout(400);
    const keys = await p.evaluate(key=>Object.keys(JSON.parse(localStorage.getItem(key))),readingKey);
    assert(keys.includes('archive/008_summer_of_type_inference'));
    pass('Initial editions retain distinct history and a current-edition link');

    const routes=['','works/ship-without-a-front.html','works/my-own-work.html',fifth,'stories/001_world_without_world.html','stories/008_summer_of_type_inference.html','about.html','archive/index.html'];
    for (const width of [320,390,768,1440]) {
      await p.setViewportSize({width,height:900});
      for (const route of routes) {
        await p.goto(base+route);
        const overflow=await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
        assert(!overflow,`${width}px horizontal overflow: ${route}`);
      }
    }
    pass('Eight page types have no horizontal overflow at 320/390/768/1440px');

    await p.setViewportSize({width:390,height:844});
    await p.goto(base+fifth);
    await p.getByRole('button',{name:'表示',exact:true}).click();
    await p.getByRole('button',{name:'特大',exact:true}).click();
    assert(!(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth)));
    await p.keyboard.press('Escape');
    await p.evaluate(()=>document.documentElement.style.fontSize='200%');
    assert(!(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth)));
    pass('Large reader type and 200% root text remain within the viewport');

    const nojs = await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});
    const np = await nojs.newPage();
    await np.goto(base+fifth);
    assert((await np.locator('.story-body').textContent()).includes('図書室に入って、イオは歩く音を小さくした。'));
    assert(!(await np.locator('.reader-controls').isVisible()));
    await np.goto(base);
    assert.equal(await np.locator('[data-work]:visible').count(),total);
    await nojs.close();
    pass('All story content and catalog links work without JavaScript');

    const blocked = await browser.newContext();
    await blocked.addInitScript(()=>Object.defineProperty(window,'localStorage',{get(){throw new Error('Storage denied');}}));
    const bp = await blocked.newPage();
    const blockedErrors=[];
    bp.on('pageerror',e=>blockedErrors.push(e.message));
    await bp.goto(base+fifth);
    await bp.getByRole('button',{name:'表示',exact:true}).click();
    await bp.getByRole('button',{name:'夜',exact:true}).click();
    assert.equal(await bp.locator('html').getAttribute('data-theme'),'night');
    assert((await bp.locator('#storage-note').textContent()).includes('保存ができません'));
    assert.equal(blockedErrors.length,0);
    await blocked.close();
    pass('Blocked storage leaves the reader and settings usable');
    assert.deepEqual(errors,[]);
    pass('No uncaught browser errors');
    console.log(`${report.length} browser checks passed.`);
    await ctx.close();
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
