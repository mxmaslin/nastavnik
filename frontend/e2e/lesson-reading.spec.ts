import { test, expect } from '@playwright/test';

test.describe('Урок — фаза чтения', () => {
  test('переход к вопросам открывается после выбора урока', async ({ page }) => {
    await page.goto('/');
    await page
      .getByRole('button', { name: /Introduction to Python Programming/i })
      .click({ timeout: 30_000 });

    await expect(page.getByRole('button', { name: 'Перейти к вопросам' })).toBeVisible({
      timeout: 20_000,
    });
    await expect(page.getByText(/Текст для ознакомления/i)).toBeVisible();

    await page.getByRole('button', { name: 'Перейти к вопросам' }).click();
    await expect(page.getByRole('radio').first()).toBeVisible({ timeout: 15_000 });
    await page.getByRole('radio').first().click();
    await page.getByRole('button', { name: 'Отправить' }).click();
  });
});
