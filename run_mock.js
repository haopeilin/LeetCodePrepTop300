const fs = require('fs');

global.document = {
  activeElements: {},
  getElementById(id) {
    if (!this.activeElements[id]) {
      const el = {
        id,
        innerHTML: '',
        textContent: '',
        children: [],
        appendChild(c) { this.children.push(c); },
        addEventListener() { },
        classList: { add() { }, remove() { } }
      };
      this.activeElements[id] = el;
      return el;
    }
    return this.activeElements[id];
  },
  createElement(tag) {
    return {
      tagName: tag,
      innerHTML: '',
      textContent: '',
      children: [],
      classList: { add() { }, remove() { } },
      appendChild(c) { this.children.push(c); },
      addEventListener() { }
    };
  },
  addEventListener(event, cb) {
    if (event === 'DOMContentLoaded') {
      setTimeout(cb, 10);
    }
  },
  querySelectorAll() { return [{ classList: { remove() { } } }]; }
};

global.window = {
  location: { href: '' }
};

const dataJs = fs.readFileSync('data.js', 'utf8');
eval(dataJs);
const appJs = fs.readFileSync('app.js', 'utf8');

try {
  eval(appJs);
  console.log("Evaluation initialized cleanly.");
} catch (e) {
  console.error("APP JS THREW:", e);
}

setTimeout(() => {
  console.log("resultsInfo textContent:", document.getElementById('resultsInfo').textContent);
  console.log("questionsListEl children:", document.getElementById('questionsList').children.length);
}, 200);
