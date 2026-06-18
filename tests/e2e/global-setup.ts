import { request } from '@playwright/test';
import { mkdirSync, writeFileSync } from 'node:fs';

const HA_URL = process.env.HA_URL || 'http://localhost:8123';
const CLIENT_ID = `${HA_URL}/`;
const USERNAME = 'test';
const PASSWORD = 'testtest1';

/**
 * Onboard (first run) or log in (subsequent runs) against the real HA container,
 * then persist the resulting tokens into localStorage as `hassTokens` so every
 * spec starts authenticated. Mirrors how the HA frontend stores its session.
 */
async function obtainTokens(): Promise<Record<string, unknown>> {
  const api = await request.newContext();

  // First run: onboarding is open and creates the owner user.
  const onboard = await api.post(`${HA_URL}/api/onboarding/users`, {
    data: { client_id: CLIENT_ID, name: 'Test', username: USERNAME, password: PASSWORD, language: 'en' },
  });

  let code: string;
  if (onboard.ok()) {
    code = (await onboard.json()).auth_code;
  } else {
    // Already onboarded — drive the login flow with the same credentials.
    const flow = await (
      await api.post(`${HA_URL}/auth/login_flow`, {
        data: { client_id: CLIENT_ID, handler: ['homeassistant', null], redirect_uri: CLIENT_ID },
      })
    ).json();
    const step = await (
      await api.post(`${HA_URL}/auth/login_flow/${flow.flow_id}`, {
        data: { client_id: CLIENT_ID, username: USERNAME, password: PASSWORD },
      })
    ).json();
    code = step.result;
  }

  const token = await (
    await api.post(`${HA_URL}/auth/token`, {
      form: { client_id: CLIENT_ID, code, grant_type: 'authorization_code' },
    })
  ).json();

  // Finish the remaining onboarding steps. The browser UI forces the onboarding
  // wizard until core_config + analytics + integration are all marked done — even
  // when the user already exists (e.g. created by the integration test conftest).
  const auth = { Authorization: `Bearer ${token.access_token}` };
  for (const step of ['core_config', 'analytics', 'integration']) {
    await api.post(`${HA_URL}/api/onboarding/${step}`, {
      headers: auth,
      data: step === 'integration' ? { client_id: CLIENT_ID, redirect_uri: CLIENT_ID } : {},
    });
  }
  await api.dispose();

  return {
    access_token: token.access_token,
    token_type: 'Bearer',
    refresh_token: token.refresh_token,
    expires_in: token.expires_in,
    hassUrl: HA_URL,
    clientId: CLIENT_ID,
    expires: Date.now() + token.expires_in * 1000,
  };
}

export default async function globalSetup(): Promise<void> {
  const tokens = await obtainTokens();
  // Write the Playwright storageState directly: HA reads its session from the
  // `hassTokens` localStorage entry, so seeding it authenticates every spec
  // without driving the login UI (and avoids any navigation race).
  const state = {
    cookies: [],
    origins: [
      {
        origin: HA_URL,
        localStorage: [
          { name: 'hassTokens', value: JSON.stringify(tokens) },
          { name: 'selectedLanguage', value: '"en"' },
        ],
      },
    ],
  };
  mkdirSync('./.auth', { recursive: true });
  writeFileSync('./.auth/state.json', JSON.stringify(state, null, 2));
}
