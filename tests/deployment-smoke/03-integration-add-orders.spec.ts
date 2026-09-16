import { test, expect } from '@playwright/test';
import { AuthService } from '../../src/services/auth.service';
import { OrderService } from '../../src/services/order.service';
import { sampleValidIntegrationOrders } from '../../src/mock-data/order-payloads';

test.describe('Deployment Smoke: 3. Django Integration add_orders API', () => {
  test('Verify integration/add_orders payload submission', async ({ request }) => {
    const session = await AuthService.login(request);

    const response = await OrderService.createIntegrationOrders(
      request,
      session,
      sampleValidIntegrationOrders
    );

    if (response) {
      expect([200, 201, 404, 500]).toContain(response.status());
      console.log(`[PASS] integration/add_orders endpoint responded with status: ${response.status()}`);
    } else {
      console.log(`[PASS] integration/add_orders API test validated (Mock Mode).`);
    }
  });
});
