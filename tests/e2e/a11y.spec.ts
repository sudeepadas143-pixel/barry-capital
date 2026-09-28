import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

for (const path of ['/', '/traders', '/firm', '/hire', '/books']) {
  test(`no accessibility violations on ${path}`, async ({ page }) => {
    await page.goto(path);
    await page.evaluate(() => document.fonts.ready);
    const res = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
    const summary = res.violations.map((v) => `${v.id} (${v.impact}): ${v.nodes.length} × ${v.nodes.slice(0, 3).map((n) => n.target.join(' ')).join(' | ')}`);
    expect(summary, summary.join('\n')).toEqual([]);
  });
}

test('trader panel is accessible', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: /^Desk 3,/ }).click();
  const res = await new AxeBuilder({ page }).include('.panel').withTags(['wcag2a', 'wcag2aa']).analyze();
  expect(res.violations.map((v) => v.id)).toEqual([]);
});
