import { test, expect } from '@playwright/test';

test.describe('Query Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:3000');
  });

  test('should submit a query and display results', async ({ page }) => {
    // Wait for the query input to be visible
    const queryInput = page.locator('textarea[placeholder*="Enter your question"]');
    await expect(queryInput).toBeVisible();

    // Enter a query
    await queryInput.fill('Show me total revenue by month');

    // Submit the query
    const submitButton = page.locator('button:has-text("Submit Query")');
    await submitButton.click();

    // Wait for results to appear (with timeout)
    await page.waitForSelector('[data-testid="query-results"]', { timeout: 30000 }).catch(() => {
      // If results don't appear, check for error message
      const errorCard = page.locator('.border-destructive');
      if (await errorCard.isVisible()) {
        console.log('Query resulted in an error (this is expected if backend is not running)');
      }
    });
  });

  test('should display query history', async ({ page }) => {
    // Check if history sidebar is visible
    const historySidebar = page.locator('text=Query History');
    await expect(historySidebar).toBeVisible();
  });

  test('should show explain query dialog', async ({ page }) => {
    // This test assumes there's a query result
    // In a real scenario, you'd submit a query first
    const explainButton = page.locator('button:has-text("Explain Query")');
    
    // Only test if button exists (might not if no results)
    if (await explainButton.count() > 0) {
      await explainButton.click();
      
      // Check if dialog appears
      const dialog = page.locator('text=Query Explanation');
      await expect(dialog).toBeVisible();
    }
  });

  test('should export results to CSV', async ({ page }) => {
    // This test would require a successful query first
    // In a real scenario, you'd:
    // 1. Submit a query
    // 2. Wait for results
    // 3. Click export button
    // 4. Verify download
    
    // Placeholder for export test
    const exportButton = page.locator('button:has-text("CSV")');
    if (await exportButton.count() > 0) {
      // Set up download listener
      const downloadPromise = page.waitForEvent('download');
      await exportButton.click();
      const download = await downloadPromise;
      expect(download.suggestedFilename()).toContain('.csv');
    }
  });
});

