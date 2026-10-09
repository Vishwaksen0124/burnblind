const region = import.meta.env.VITE_COGNITO_REGION || 'us-east-2';
const userPoolId = import.meta.env.VITE_COGNITO_USER_POOL_ID || '';
const clientId = import.meta.env.VITE_COGNITO_CLIENT_ID || '';
const storageKey = 'burnblind.reviewer.session.v1';

export const reviewerAuthEnabled = Boolean(userPoolId && clientId);

async function cognito(target, payload) {
  const response = await fetch(`https://cognito-idp.${region}.amazonaws.com/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-amz-json-1.1',
      'X-Amz-Target': `AWSCognitoIdentityProviderService.${target}`,
    },
    body: JSON.stringify(payload),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.message || result.__type?.split('#').at(-1) || 'Reviewer sign-in failed.');
  return result;
}

export async function beginReviewerSignIn(username, password) {
  const result = await cognito('InitiateAuth', {
    AuthFlow: 'USER_PASSWORD_AUTH',
    ClientId: clientId,
    AuthParameters: { USERNAME: username.trim(), PASSWORD: password },
  });
  if (result.ChallengeName === 'NEW_PASSWORD_REQUIRED') {
    return { challenge: true, session: result.Session, username: username.trim() };
  }
  return storeAuthentication(result.AuthenticationResult);
}

export async function completeReviewerPasswordChallenge(username, newPassword, session) {
  const result = await cognito('RespondToAuthChallenge', {
    ChallengeName: 'NEW_PASSWORD_REQUIRED',
    ClientId: clientId,
    Session: session,
    ChallengeResponses: { USERNAME: username, NEW_PASSWORD: newPassword },
  });
  return storeAuthentication(result.AuthenticationResult);
}

export async function restoreReviewerSession() {
  const stored = readSession();
  if (!stored) return null;
  if (tokenExpiresSoon(stored.accessToken)) {
    if (!stored.refreshToken) return clearSession();
    try {
      const refreshed = await cognito('InitiateAuth', {
        AuthFlow: 'REFRESH_TOKEN_AUTH',
        ClientId: clientId,
        AuthParameters: { REFRESH_TOKEN: stored.refreshToken },
      });
      return storeAuthentication({ ...refreshed.AuthenticationResult, RefreshToken: stored.refreshToken });
    } catch {
      return clearSession();
    }
  }
  return publicSession(stored);
}

export async function getValidReviewerToken() {
  const stored = readSession();
  if (!stored?.idToken) throw new Error('Your reviewer session has expired. Sign in again.');
  if (!tokenExpiresSoon(stored.accessToken)) return stored.accessToken;
  if (!stored.refreshToken) {
    clearSession();
    throw new Error('Your reviewer session has expired. Sign in again.');
  }
  try {
    const refreshed = await cognito('InitiateAuth', {
      AuthFlow: 'REFRESH_TOKEN_AUTH',
      ClientId: clientId,
      AuthParameters: { REFRESH_TOKEN: stored.refreshToken },
    });
    return storeAuthentication({ ...refreshed.AuthenticationResult, RefreshToken: stored.refreshToken }).token;
  } catch {
    clearSession();
    throw new Error('Your reviewer session has expired. Sign in again.');
  }
}

export async function signOutReviewer() {
  const stored = readSession();
  try {
    if (stored?.accessToken) await cognito('GlobalSignOut', { AccessToken: stored.accessToken });
  } finally {
    clearSession();
  }
}

function storeAuthentication(result) {
  if (!result?.IdToken || !result?.AccessToken) throw new Error('The identity provider returned an incomplete reviewer session.');
  const session = {
    idToken: result.IdToken,
    accessToken: result.AccessToken,
    refreshToken: result.RefreshToken || readSession()?.refreshToken || null,
  };
  window.sessionStorage.setItem(storageKey, JSON.stringify(session));
  return publicSession(session);
}

function publicSession(session) {
  const claims = decodeToken(session.idToken);
  return {
    token: session.accessToken,
    reviewerId: claims.sub,
    email: claims.email || claims.username || 'Reviewer',
  };
}

function readSession() {
  try {
    return JSON.parse(window.sessionStorage.getItem(storageKey) || 'null');
  } catch {
    return null;
  }
}

function clearSession() {
  window.sessionStorage.removeItem(storageKey);
  return null;
}

function tokenExpiresSoon(token) {
  try {
    return decodeToken(token).exp * 1000 < Date.now() + 60_000;
  } catch {
    return true;
  }
}

function decodeToken(token) {
  const payload = token.split('.')[1].replaceAll('-', '+').replaceAll('_', '/');
  return JSON.parse(window.atob(payload.padEnd(Math.ceil(payload.length / 4) * 4, '=')));
}
