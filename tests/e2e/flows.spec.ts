import { expect, test } from '@playwright/test';

test('hire a trader, follow another, and both survive a reload', async ({ page }, info) => {
  await page.goto('/hire');
  await page.getByRole('button', { name: 'sign the paperwork' }).click();
  await expect(page.getByRole('alert')).toHaveText('A surname, please.');
  await page.getByLabel('Surname').fill('Pemberton-Smythe!');
  await expect(page.getByLabel('Surname')).toHaveValue('pemberton-smythe');
  await page.getByRole('radio', { name: 'the sniper' }).click();
  await page.getByRole('radio', { name: 'olive' }).click();
  await page.screenshot({ path: `screenshots/${info.project.name}-hire-form.png`, fullPage: true });
  await page.getByRole('button', { name: 'sign the paperwork' }).click();
  await expect(page.getByRole('heading', { name: 'pemberton-smythe' })).toBeVisible();
  await page.screenshot({ path: `screenshots/${info.project.name}-hire-file.png`, fullPage: true });

  await page.goto('/');
  await expect(page.getByRole('button', { name: /Desk 12, pemberton-smythe, yours/ })).toBeVisible();

  await page.getByRole('button', { name: /^Desk 2,/ }).click();
  const dialog = page.getByRole('dialog');
  await dialog.getByRole('button', { name: 'follow' }).click();
  await expect(dialog.getByRole('button', { name: 'following' })).toHaveAttribute('aria-pressed', 'true');
  await page.keyboard.press('Escape');
  await expect(page.getByRole('link', { name: '1 followed' })).toBeVisible();

  await page.reload();
  await expect(page.getByRole('link', { name: '1 followed' })).toBeVisible();
  await expect(page.getByRole('button', { name: /Desk 12, pemberton-smythe, yours/ })).toBeVisible();

  // Let them go.
  await page.goto('/hire');
  await page.getByRole('button', { name: /let pemberton-smythe go/ }).click();
  await page.getByRole('button', { name: 'yes, hand over the box' }).click();
  await expect(page.getByLabel('Surname')).toBeVisible();
});
