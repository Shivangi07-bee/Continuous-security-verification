
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');

test('web application files exist', () => {
  for (const file of ['web/index.html', 'web/app.js', 'web/style.css']) {
    assert.ok(fs.existsSync(file), `${file} must exist`);
  }
});

test('HTML page is not empty', () => {
  const html = fs.readFileSync('web/index.html', 'utf8');
  assert.ok(html.trim().length > 0);
  assert.match(html, /<html/i);
});

test('JavaScript application is not empty', () => {
  const app = fs.readFileSync('web/app.js', 'utf8');
  assert.ok(app.trim().length > 0);
});
