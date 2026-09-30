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
  await page.getByRole('button', { name: 'yes, let them go' }).click();
  await expect(page.getByLabel('Surname')).toBeVisible();
});

test('a long gap since the last deploy is replayed in chunks without freezing the page', async ({ page }) => {
  // Pretend it is 30 days after the build.
  await page.addInitScript(() => {
    const offset = 30 * 24 * 3600 * 1000;
    const real = Date.now.bind(Date);
    Date.now = () => real() + offset;
  });
  const t0 = Date.now();
  await page.goto('/');
  await expect(page.getByText('Reading the books.')).toBeVisible();
  await expect(page.getByRole('heading', { name: /a trading floor/ })).toBeVisible({ timeout: 60_000 });
  console.log(`caught up 30 days in ${Date.now() - t0} ms`);
});

test('a wallet address builds a trader, and secrets are refused', async ({ page }) => {
  await page.goto('/hire');
  const wallet = page.getByLabel(/Solana wallet/);
  await wallet.fill('abandon '.repeat(11) + 'about');
  await expect(wallet).toHaveValue('');
  await expect(page.locator('#wallet-note')).toContainText('recovery phrase');
  await wallet.fill('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');
  await expect(page.getByText('Built from your wallet.')).toBeVisible();
  const name = await page.getByLabel('Surname').inputValue();
  expect(name.length).toBeGreaterThan(2);
  // The same wallet always makes the same trader.
  await page.reload();
  await page.getByLabel(/Solana wallet/).fill('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');
  await expect(page.getByLabel('Surname')).toHaveValue(name);
  await page.getByRole('button', { name: 'sign the paperwork' }).click();
  await expect(page.getByRole('link', { name: /Toke…Q5DA/ })).toHaveAttribute('href', /solscan\.io\/account\/TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA/);
  await page.getByRole('button', { name: new RegExp(`let ${name} go`) }).click();
  await page.getByRole('button', { name: 'yes, let them go' }).click();
});
