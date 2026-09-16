import { defineConfig } from '@playwright/test';
import * as dotenv from 'dotenv';

// Load environment variables from .env file if available
dotenv.config();

export default defineConfig({
  testDir: './tests',
  /* Run tests in files in parallel for maximum speed (sub 2-min deployment target) */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 1 : 0,
  /* Default 4 workers */
  workers: process.env.CI ? 4 : undefined,
  /* Reporter to use. JUnit is required for Jenkins test reporting */
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['junit', { outputFile: 'test-results/results.xml' }],
    ['list']
  ],
  /* Maximum time one test can run (30 seconds) */
  timeout: 30 * 1000,
  /* Shared settings for all projects */
  use: {
    baseURL: process.env.BASE_URL || 'https://connect-plus.app/en-US/login',
    extraHTTPHeaders: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    },
    trace: 'on-first-retry',
  },

  /* Configure projects to enforce LOGIN FIRST execution sequence */
  projects: [
    {
      name: '01-Login-Setup',
      testMatch: /01-login\.spec\.ts/,
    },
    {
      name: '02-Order-Creation-Smoke',
      testMatch: /(02-ui-create-order|03-integration-add-orders|04-excel-import-all-cases)\.spec\.ts/,
      dependencies: ['01-Login-Setup'],
    },
  ],
});
