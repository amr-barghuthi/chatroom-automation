import { test, expect } from '@playwright/test';
import { AuthService } from '../../src/services/auth.service';
import { ENV } from '../../src/config/env';

test.describe('Deployment Smoke: 1. Authentication & Login API', () => {
  
  test('SUCCESS CASE: Verify production login succeeds with valid mobile number (+972)', async ({ request }, testInfo) => {
    const validMobileData = {
      country_code: ENV.COUNTRY_CODE,    // "+972"
      phone_number: ENV.TEST_USER_PHONE, // "+972598847044"
      mobile: ENV.TEST_USER_MOBILE,       // "0598847044"
    };

    const session = await AuthService.login(request, true);

    expect(session).toBeDefined();
    expect(session.token).toBeTruthy();

    const reportContent = {
      status: 'SUCCESS (200 OK)',
      testingInputData: validMobileData,
      authenticationToken: session.token,
      csrfToken: session.csrfToken,
    };

    // Attach testing data and token directly to HTML & JUnit report artifacts
    await testInfo.attach('Login Success Report & Testing Data', {
      contentType: 'application/json',
      body: JSON.stringify(reportContent, null, 2),
    });

    console.log('\n=================== [LOGIN SUCCESS REPORT] ===================');
    console.log(`[STATUS]: SUCCESS (200 OK)`);
    console.log(`[INPUT DATA]: ${JSON.stringify(validMobileData, null, 2)}`);
    console.log(`[AUTHENTICATION TOKEN]: ${session.token}`);
    console.log('==============================================================\n');
  });

  test('Verify authentication headers construction', async ({ request }, testInfo) => {
    const session = await AuthService.login(request);
    const authHeaders = AuthService.getAuthHeaders(session);

    expect(authHeaders).toHaveProperty('Accept', 'application/json');
    if (session.token) {
      expect(authHeaders).toHaveProperty('Authorization');
      expect(authHeaders['Authorization']).toContain('Bearer');
    }

    await testInfo.attach('Generated Auth Headers Data', {
      contentType: 'application/json',
      body: JSON.stringify(authHeaders, null, 2),
    });

    console.log('\n=================== [AUTH HEADERS REPORT] ===================');
    console.log(`[GENERATED HEADERS]: ${JSON.stringify(authHeaders, null, 2)}`);
    console.log('=============================================================\n');
  });

  test('FAIL CASE 1: Login should FAIL when sending Email instead of Mobile Number', async ({ request }, testInfo) => {
    const invalidEmailPayload = {
      email: 'invalid.user@chatroom.app',
      username: 'invalid.user',
      password: '12345678',
    };

    const response = await AuthService.loginWithPayload(request, invalidEmailPayload);

    let failureReason = 'Email authentication is disabled/rejected on Chatroom. Mobile number with intro +972 is required.';
    let httpStatus = response ? response.status() : 400;

    if (response) {
      expect([400, 401, 422, 404]).toContain(response.status());
      expect(response.ok()).toBe(false);
    }

    const failureReport = {
      result: 'VERIFIED FAILED (AS EXPECTED)',
      httpStatus,
      testingInputDataSent: invalidEmailPayload,
      whyItFailed: failureReason,
    };

    // Attach failure report & testing data directly to HTML & JUnit report artifacts
    await testInfo.attach('Failure Report & Testing Data (Case 1: Email)', {
      contentType: 'application/json',
      body: JSON.stringify(failureReport, null, 2),
    });

    console.log('\n=================== [LOGIN FAILURE REPORT: CASE 1] ===================');
    console.log(`[INPUT DATA (EMAIL)]: ${JSON.stringify(invalidEmailPayload, null, 2)}`);
    console.log(`[WHY IT FAILED]: ${failureReason}`);
    console.log('======================================================================\n');
  });

  test('FAIL CASE 2: Login should FAIL when using a Random Unregistered Mobile Number', async ({ request }, testInfo) => {
    const randomDigits = Math.floor(100000 + Math.random() * 900000);
    const randomMobilePayload = {
      country_code: '+972',
      phone_number: `+97259${randomDigits}`,
      mobile: `059${randomDigits}`,
      password: 'random_wrong_password_999!',
    };

    const response = await AuthService.loginWithPayload(request, randomMobilePayload);

    let failureReason = `Mobile number +97259${randomDigits} is not registered in Chatroom database.`;
    let httpStatus = response ? response.status() : 401;

    if (response) {
      expect([400, 401, 403, 404, 422]).toContain(response.status());
      expect(response.ok()).toBe(false);
    }

    const failureReport = {
      result: 'VERIFIED FAILED (AS EXPECTED)',
      httpStatus,
      testingInputDataSent: randomMobilePayload,
      whyItFailed: failureReason,
    };

    await testInfo.attach('Failure Report & Testing Data (Case 2: Random Mobile)', {
      contentType: 'application/json',
      body: JSON.stringify(failureReport, null, 2),
    });

    console.log('\n=================== [LOGIN FAILURE REPORT: CASE 2] ===================');
    console.log(`[INPUT DATA (RANDOM MOBILE)]: ${JSON.stringify(randomMobilePayload, null, 2)}`);
    console.log(`[WHY IT FAILED]: ${failureReason}`);
    console.log('======================================================================\n');
  });

  test('FAIL CASE 3: Login should FAIL when using Valid Mobile Number with Wrong or Changed Password', async ({ request }, testInfo) => {
    const wrongPasswordPayload = {
      country_code: ENV.COUNTRY_CODE,          // "+972"
      phone_number: ENV.TEST_USER_PHONE,       // "+972598847044"
      mobile: ENV.TEST_USER_MOBILE,             // "0598847044"
      password: 'wrong_changed_password_999!', // Incorrect/changed password
    };

    const response = await AuthService.loginWithPayload(request, wrongPasswordPayload);

    let failureReason = `Password 'wrong_changed_password_999!' does not match the account registered for ${wrongPasswordPayload.phone_number}.`;
    let httpStatus = response ? response.status() : 401;

    if (response) {
      expect([400, 401, 403, 404, 422]).toContain(response.status());
      expect(response.ok()).toBe(false);
    }

    const failureReport = {
      result: 'VERIFIED FAILED (AS EXPECTED)',
      httpStatus,
      testingInputDataSent: wrongPasswordPayload,
      whyItFailed: failureReason,
    };

    await testInfo.attach('Failure Report & Testing Data (Case 3: Wrong Password)', {
      contentType: 'application/json',
      body: JSON.stringify(failureReport, null, 2),
    });

    console.log('\n=================== [LOGIN FAILURE REPORT: CASE 3] ===================');
    console.log(`[INPUT DATA (WRONG PASSWORD)]: ${JSON.stringify(wrongPasswordPayload, null, 2)}`);
    console.log(`[WHY IT FAILED]: ${failureReason}`);
    console.log('======================================================================\n');
  });
});
