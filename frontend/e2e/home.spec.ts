import { test, expect } from '@playwright/test';

test.describe('Главная и список уроков', () => {
  test('заголовок и seeded-урок с API', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Nastavnik' })).toBeVisible();
    await expect(
      page.getByRole('button', { name: /Introduction to Python Programming/i })
    ).toBeVisible({ timeout: 30_000 });
  });

  test('кнопка статистики с главной', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('button', { name: /View Statistics/i })).toBeVisible();
  });
});
