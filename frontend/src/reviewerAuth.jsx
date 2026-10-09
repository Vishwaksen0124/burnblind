import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import {
  beginReviewerSignIn,
  completeReviewerPasswordChallenge,
  restoreReviewerSession,
  reviewerAuthEnabled,
  signOutReviewer,
} from './auth.js';

const ReviewerAuthContext = createContext(null);

export function ReviewerAuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [loadingSession, setLoadingSession] = useState(true);
  const [signInOpen, setSignInOpen] = useState(false);
  const [signInMessage, setSignInMessage] = useState('');

  useEffect(() => {
    let active = true;
    restoreReviewerSession()
      .then((current) => { if (active) setSession(current); })
      .catch(() => { if (active) setSession(null); })
      .finally(() => { if (active) setLoadingSession(false); });
    return () => { active = false; };
  }, []);

  const value = useMemo(() => ({
    session,
    loadingSession,
    enabled: reviewerAuthEnabled,
    openSignIn(message = '') { setSignInMessage(message); setSignInOpen(true); },
    closeSignIn() { setSignInOpen(false); },
    async signIn(username, password) {
      const result = await beginReviewerSignIn(username, password);
      if (!result.challenge) {
        setSession(result);
        setSignInOpen(false);
      }
      return result;
    },
    async completePasswordChallenge(username, password, challengeSession) {
      const result = await completeReviewerPasswordChallenge(username, password, challengeSession);
      setSession(result);
      setSignInOpen(false);
    },
    async signOut() {
      try { await signOutReviewer(); }
      finally { setSession(null); }
    },
  }), [session, loadingSession]);

  return <ReviewerAuthContext.Provider value={value}>
    {children}
    {signInOpen && <ReviewerSignInDialog
      message={signInMessage}
      enabled={reviewerAuthEnabled}
      onSignIn={value.signIn}
      onCompleteChallenge={value.completePasswordChallenge}
      onClose={value.closeSignIn}
    />}
  </ReviewerAuthContext.Provider>;
}

export function useReviewerAuth() {
  const value = useContext(ReviewerAuthContext);
  if (!value) throw new Error('useReviewerAuth must be used inside ReviewerAuthProvider');
  return value;
}

function ReviewerSignInDialog({ message, enabled, onSignIn, onCompleteChallenge, onClose }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [challenge, setChallenge] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      if (challenge) {
        await onCompleteChallenge(challenge.username, newPassword, challenge.session);
      } else {
        const result = await onSignIn(email, password);
        if (result.challenge) setChallenge(result);
      }
    } catch (cause) {
      setError(cause.message || 'Sign-in failed. Check the reviewer account details.');
    } finally {
      setBusy(false);
    }
  }

  return <div className="reviewer-auth-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <section className="reviewer-auth-dialog" role="dialog" aria-modal="true" aria-labelledby="reviewer-auth-title">
      <button className="reviewer-auth-close" onClick={onClose} aria-label="Close sign-in">×</button>
      <p className="eyebrow">BURNBLIND · REVIEWER ACCESS</p>
      <h2 id="reviewer-auth-title">{challenge ? 'Set your password' : 'Sign in to review'}</h2>
      <p className="reviewer-auth-copy">{message || 'Reviewer accounts are invited by the BurnBlind administrator. Event and report views remain public.'}</p>
      {!enabled && <p className="reviewer-auth-error">Reviewer sign-in is not configured for this deployment yet.</p>}
      {enabled && <form onSubmit={submit}>
        {!challenge && <>
          <label>Email<input type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
          <label>Password<input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
        </>}
        {challenge && <>
          <p className="reviewer-auth-challenge">A temporary password was used. Choose a new password to finish signing in.</p>
          <label>New password<input type="password" autoComplete="new-password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} minLength={12} required /></label>
        </>}
        {error && <p className="reviewer-auth-error" role="alert">{error}</p>}
        <button className="action-button" type="submit" disabled={busy}>{busy ? 'Checking…' : challenge ? 'Set password and continue' : 'Sign in'}</button>
      </form>}
      <small>Sign-in tokens stay in this browser tab and are sent only to BurnBlind’s protected review routes.</small>
    </section>
  </div>;
}
