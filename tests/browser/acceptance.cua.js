// Reusable browser acceptance journey for the Codex CUA browser surface.
// Import this module in cua_repl; call runAcceptance({tab,browser,nodeRepl}).
// tab must already point to the running synthetic dashboard. No live providers.
export async function runAcceptance({tab,browser,nodeRepl}) {
  const checks=[];
  function assert(ok,name) {if (!ok) throw new Error(name);checks.push(name);}
  async function settle() {
    // A marker after all app content ensures that a rerun has finished.
    await tab.playwright.getByText("Financial Dashboard · Synthetic demonstration / controlled prototype · Financial statement exploration · No investment recommendations",{exact:true}).waitFor({state:"visible",timeoutMs:15000});
  }
  async function load(symbol) {
    await tab.playwright.getByRole("textbox",{name:"Stock symbol",exact:true}).fill(symbol);
    await tab.playwright.getByRole("button",{name:"Load",exact:true}).click();
    // Wait for the resolved company text or error that belongs to this request.
    const expected={"DEMO-A":"Example Manufacturing","DEMO-B":"Northstar Systems","DEMO-PARTIAL":"Partial-statement scenario","DEMO-BANK":"Synthetic bank scenario","DEMO-OPENING":"Missing opening balance scenario","DEMO-TWO":"Two-year history scenario","DEMO-ETF":"Unsupported instrument scenario","DEMO-NOQUOTE":"Unavailable quote scenario"}[symbol];
    if(expected) await tab.playwright.getByText(expected,{exact:true}).waitFor({state:"visible",timeoutMs:15000});
    else await tab.playwright.getByText(symbol+" ·",{exact:false}).waitFor({state:"visible",timeoutMs:15000});
    await settle();
  }
  await load("DEMO-A");
  assert((await tab.playwright.getByRole("tab").count())===4,"four tabs");
  assert(await tab.playwright.getByText("SYNTHETIC DEMO",{exact:true}).isVisible(),"synthetic notice");
  await tab.playwright.getByRole("tab",{name:"Financials",exact:true}).click();
  assert(await tab.playwright.getByRole("row",{name:"Current ratio D 2.50x 2.00x 2.00x",exact:true}).isVisible(),"golden current ratios");
  assert(await tab.playwright.getByRole("row",{name:"Return on equity D 26.67% 26.18% 22.22%",exact:true}).isVisible(),"golden ROE");
  await tab.playwright.getByRole("combobox",{name:"Monetary units",exact:true}).click();
  await tab.playwright.getByRole("option",{name:"Thousands",exact:true}).click();
  await tab.playwright.getByRole("row",{name:"Total revenue S 1,500,000.00 1,200,000.00 1,000,000.00",exact:true}).waitFor({state:"visible",timeoutMs:15000});
  assert(await tab.playwright.getByRole("row",{name:"Current ratio D 2.50x 2.00x 2.00x",exact:true}).isVisible(),"units preserve ratios");
  for(const name of ["Valuation","Comparisons"]) {
    await tab.playwright.getByRole("tab",{name,exact:true}).click();
    assert(await tab.playwright.getByText("Planned — not included in this release",{exact:true}).filter({visible:true}).isVisible(),name+" planned");
  }
  await tab.playwright.getByRole("combobox",{name:"Monetary units",exact:true}).click();
  await tab.playwright.getByRole("option",{name:"Millions",exact:true}).click();
  await settle();
  await load("DEMO-B");
  await tab.playwright.getByRole("tab",{name:"Overview",exact:true}).click();
  assert(await tab.playwright.getByText("86.40 USD",{exact:true}).isVisible(),"second-company quote");
  assert(!(await tab.playwright.getByText("Example Manufacturing",{exact:true}).isVisible()),"no prior company mislabeled");
  await tab.playwright.getByRole("button",{name:"Zoom in",exact:true}).click();
  await tab.playwright.getByRole("button",{name:"Reset axes",exact:true}).click();
  checks.push("Plotly zoom/reset controls");
  for(const [symbol,notice] of [
    ["DEMO-PARTIAL","Partial annual data:"],
    ["DEMO-BANK","Standard industrial-company ratios are suppressed"],
    ["DEMO-TWO","Only 2 reported annual years available"],
    ["DEMO-OPENING","Calculation notes"],
    ["DEMO-ETF","Unsupported instrument: annual company statements"],
    ["DEMO-NOQUOTE","Market data: Quote unavailable"],
  ]) {
    await load(symbol);
    await tab.playwright.getByRole("tab",{name:symbol==="DEMO-NOQUOTE"?"Overview":"Financials",exact:true}).click();
    await tab.playwright.getByText(notice,{exact:false}).filter({visible:true}).first().waitFor({state:"visible",timeoutMs:15000});
    assert(await tab.playwright.getByText(notice,{exact:false}).filter({visible:true}).first().isVisible(),symbol+" reason");
    assert((await tab.playwright.getByRole("tab").count())===4,symbol+" tabs retained");
  }
  await load("AAPL");
  assert(await tab.playwright.getByText("Symbol not available in synthetic demo.",{exact:false}).isVisible(),"unknown real symbol explained");
  assert((await tab.playwright.getByRole("tab").count())===4,"error tabs retained");
  await load("DEMO-A");
  await tab.playwright.getByRole("tab",{name:"Financials",exact:true}).click();
  const viewport=await browser.capabilities.get("viewport");
  await viewport.set({width:390,height:844});
  await tab.playwright.domSnapshot();
  const dimensions=await tab.playwright.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,tables:[...document.querySelectorAll('.table-scroll')].filter(e=>e.clientWidth>0).map(e=>({client:e.clientWidth,scroll:e.scrollWidth}))}));
  assert(dimensions.width===390 && dimensions.scroll<=390,"mobile no page overflow");
  assert(dimensions.tables.every(t=>t.scroll>t.client),"mobile financial tables contained");
  await tab.playwright.locator('.table-scroll').first().press("ArrowRight");
  await tab.playwright.locator('.table-scroll').first().press("ArrowRight");
  await tab.playwright.domSnapshot();
  assert((await tab.playwright.evaluate(()=>document.querySelector('.table-scroll').scrollLeft))>0,"keyboard table scrolling");
  await viewport.reset();
  await tab.playwright.getByRole("tab",{name:"Overview",exact:true}).click();
  nodeRepl.write({status:"passed",checks});
  return checks;
}
