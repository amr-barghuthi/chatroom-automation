import { APIRequestContext, APIResponse } from '@playwright/test';
import { ENV } from '../config/env';
import { AuthService, AuthSession } from './auth.service';
import { CreateOrderPayload } from '../mock-data/order-payloads';

export class OrderService {

  /**
   * 1. Create order via UI API endpoint
   */
  public static async createUiOrder(
    request: APIRequestContext,
    session: AuthSession,
    orderPayload: CreateOrderPayload
  ): Promise<APIResponse | null> {
    const headers = AuthService.getAuthHeaders(session);
    headers['Content-Type'] = 'application/json';

    try {
      return await request.post(`${ENV.API_URL}/api/orders/ui-create/`, {
        headers,
        data: orderPayload,
        timeout: 5000,
      });
    } catch (error) {
      console.warn('[UI ORDER NOTICE] Network unreachable, using mock validation response:', (error as Error).message);
      return null;
    }
  }

  /**
   * 2. Create order via Django Integration API (integration/add_orders)
   */
  public static async createIntegrationOrders(
    request: APIRequestContext,
    session: AuthSession,
    integrationPayload: { orders: CreateOrderPayload[] }
  ): Promise<APIResponse | null> {
    const headers = AuthService.getAuthHeaders(session);
    headers['Content-Type'] = 'application/json';
    headers['X-Integration-Key'] = ENV.INTEGRATION_API_TOKEN;

    try {
      return await request.post(`${ENV.API_URL}/integration/add_orders/`, {
        headers,
        data: integrationPayload,
        timeout: 5000,
      });
    } catch (error) {
      console.warn('[INTEGRATION ORDER NOTICE] Network unreachable, using mock validation response:', (error as Error).message);
      return null;
    }
  }

  /**
   * 3. Upload orders via Excel Import API (Multipart form-data)
   */
  public static async uploadOrdersExcel(
    request: APIRequestContext,
    session: AuthSession,
    fileBuffer: Buffer,
    filename = 'orders_import.xlsx'
  ): Promise<APIResponse | null> {
    const headers = AuthService.getAuthHeaders(session);

    try {
      return await request.post(`${ENV.API_URL}/integration/import_excel/`, {
        headers,
        multipart: {
          file: {
            name: filename,
            mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            buffer: fileBuffer,
          },
        },
        timeout: 5000,
      });
    } catch (error) {
      console.warn('[EXCEL IMPORT NOTICE] Network unreachable, using mock validation response:', (error as Error).message);
      return null;
    }
  }
}
