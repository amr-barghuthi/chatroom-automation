import * as dotenv from 'dotenv';
dotenv.config();

export const ENV = {
  BASE_URL: process.env.BASE_URL || 'https://chatroom.app',
  API_URL: process.env.API_URL || 'https://api.chatroom.app',
  COUNTRY_CODE: process.env.COUNTRY_CODE || '+972',
  TEST_USER_PHONE: process.env.TEST_USER_PHONE || '+972598847044',
  TEST_USER_MOBILE: process.env.TEST_USER_MOBILE || '0598847044',
  TEST_USER_PASSWORD: process.env.TEST_USER_PASSWORD || '12345678',
  INTEGRATION_API_TOKEN: process.env.INTEGRATION_API_TOKEN || 'chatroom_integration_token_live_xyz123',
};
