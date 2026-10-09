import { expect, test, type Page } from '@playwright/test';

const ADDR = '7HpRv8WbbJ9x2rRqWJq2aT7Y3yWZQm1v5NfH6r4kQzVb';

/** A stand-in for the hiring desk API, so the flow can be walked without a store or a chain. */
async function fakeDesk(page: Page) {
  const desk = { state: 'none' as string, hired: 214, trader: null as unknown };
  await page.route('**/api/**', async (route) => {
    const url = route.request().url();
    if (url.includes('/api/register')) desk.state = desk.state === 'none' ? 'pending' : desk.state;
    if (url.includes('/api/trader')) {
      if (desk.state !== 'minted') return route.fulfill({ status: 409, contentType: 'application/json', body: JSON.stringify({ ...desk, cap: 1111, error: 'locked' }) });
      const body = JSON.parse(route.request().postData() ?? '{}');
      desk.trader = { ...body.trader, hiredAt: Date.now() };
      desk.state = 'hired';
    }
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ state: desk.state, hired: desk.hired, cap: 1111, trader: desk.trader ?? undefined }) });
  });
  return desk;
}

test('hire through an Investor, follow another trader, and both survive a reload', async ({ page }, info) => {
  const desk = await fakeDesk(page);
  await page.goto('/hire');
  await expect(page.getByText('214/1111 Investors Hired')).toBeVisible();
  await page.getByLabel('Your public Solana address').fill(ADDR);
  await page.getByRole('button', { name: 'register' }).click();
  await expect(page.getByText('is registered')).toBeVisible();
  await page.screenshot({ path: `screenshots/${info.project.name}-hire.png`, fullPage: true });

  // The worker sees the comment and sends the Investor.
  desk.state = 'minted';
  desk.hired = 215;
  await page.reload();
  await expect(page.getByText('Your Investor is in')).toBeVisible();
  await page.getByLabel('Surname').fill('');
  await page.getByRole('button', { name: 'sign the paperwork' }).click();
  await expect(page.getByRole('alert')).toHaveText('A surname, please.');
  await page.getByLabel('Surname').fill('Pemberton-Smythe!');
  await expect(page.getByLabel('Surname')).toHaveValue('pemberton-smythe');
  await page.getByRole('radio', { name: 'the sniper' }).click();
  await page.getByRole('radio', { name: 'olive' }).click();
  await page.screenshot({ path: `screenshots/${info.project.name}-hire-form.png`, fullPage: true });
  await page.getByRole('button', { name: 'sign the paperwork' }).click();
  await expect(page.getByRole('heading', { name: 'pemberton-smythe' })).toBeVisible();
  // Locked: no way to let them go.
  await expect(page.getByRole('button', { name: /let pemberton-smythe go/ })).toHaveCount(0);
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
});

test('a trader saved to an Investor appears on a new device with the same address', async ({ page }) => {
  const desk = await fakeDesk(page);
  desk.state = 'hired';
  desk.trader = { name: 'fairweather', archetype: 'quant', risk: 0.4, patience: 0.6, seed: 5, hiredAt: 1, look: { skin: 2, hair: 1, hairStyle: 0, suit: 1, tie: 2 } };
  await page.addInitScript((a) => localStorage.setItem('steve-s-investors:investor-address', JSON.stringify(a)), ADDR);
  await page.goto('/hire');
  await expect(page.getByRole('heading', { name: 'fairweather' })).toBeVisible();
});

test('before launch the hiring desk is closed', async ({ page }) => {
  await page.goto('/hire');
  await expect(page.getByText('Hiring opens when the token launches.')).toBeVisible();
  await expect(page.getByRole('button', { name: 'register' })).toBeDisabled();
  await expect(page.getByText('at launch')).toBeVisible();
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
  await expect(page.getByRole('heading', { name: /one gets fired/ })).toBeVisible({ timeout: 60_000 });
  console.log(`caught up 30 days in ${Date.now() - t0} ms`);
});

test('the address field refuses secrets and non-addresses', async ({ page }) => {
  await fakeDesk(page);
  await page.goto('/hire');
  const field = page.getByLabel('Your public Solana address');
  await field.fill('abandon '.repeat(11) + 'about');
  await page.getByRole('button', { name: 'register' }).click();
  await expect(field).toHaveValue('');
  await expect(page.getByRole('alert')).toContainText('recovery phrase');
  await field.fill('not-an-address');
  await page.getByRole('button', { name: 'register' }).click();
  await expect(page.getByRole('alert')).toContainText('Solana address');
});
