const fs = require('fs');
const jsdom = require('jsdom');
const { JSDOM } = jsdom;
const html = fs.readFileSync('index.html', 'utf8');
const dom = new JSDOM(html, { runScripts: 'dangerously', resources: 'usable' });
dom.window.addEventListener('error', (event) => {
  console.log('JS Error:', event.error);
});
setTimeout(() => {
  const el = dom.window.document.getElementById('questionsList');
  if (el) console.log('Items in list:', el.children.length);
  else console.log('questionsList null');
  process.exit();
}, 2000);
