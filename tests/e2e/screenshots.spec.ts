import { expect, test } from '@playwright/test';

const PAGES = [
  ['home', '/'],
  ['traders', '/traders'],
  ['firm', '/firm'],
  ['hire', '/hire'],
  ['books', '/books'],
] as const;

for (const [name, path] of PAGES) {
  test(`screenshot ${name}`, async ({ page }, info) => {
    await page.goto(path);
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(400);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow, 'no horizontal scroll').toBeLessThanOrEqual(0);
    await page.screenshot({ path: `screenshots/${info.project.name}-${name}.png`, fullPage: true });
  });
}

test('trader panel opens from a desk', async ({ page }, info) => {
  await page.goto('/');
  await page.getByRole('button', { name: /^Desk 1,/ }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.waitForTimeout(300);
  await page.screenshot({ path: `screenshots/${info.project.name}-panel.png` });
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).toHaveCount(0);
});
