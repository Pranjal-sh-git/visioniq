import React, { useState } from 'react';
import {
  Sparkles,
  Mail,
  Lock,
  User,
  ArrowRight,
  ArrowLeft,
  Eye,
  EyeOff,
  CheckCircle2,
  AlertCircle,
  KeyRound,
  UserCheck,
  Shield,
  Layers,
  Video,
} from 'lucide-react';

interface AuthPageProps {
  onLoginSuccess: (user: { name: string; email: string; isGuest?: boolean }) => void;
  onBack?: () => void;
  intendedTab?: 'image' | 'video' | 'landing';
}

export const AuthPage: React.FC<AuthPageProps> = ({
  onLoginSuccess,
  onBack,
  intendedTab = 'image',
}) => {
  const [authMode, setAuthMode] = useState<'signin' | 'signup'>('signin');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  // Sign In Form State
  const [signInEmail, setSignInEmail] = useState('');
  const [signInPassword, setSignInPassword] = useState('');
  const [signInErrors, setSignInErrors] = useState<{ email?: string; password?: string }>({});

  // Sign Up Form State
  const [signUpName, setSignUpName] = useState('');
  const [signUpEmail, setSignUpEmail] = useState('');
  const [signUpPassword, setSignUpPassword] = useState('');
  const [signUpConfirmPassword, setSignUpConfirmPassword] = useState('');
  const [signUpErrors, setSignUpErrors] = useState<{
    name?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
  }>({});

  const validateEmail = (email: string): boolean => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
  };

  const handleSignInSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const errors: { email?: string; password?: string } = {};

    if (!signInEmail.trim()) {
      errors.email = 'Email address is required';
    } else if (!validateEmail(signInEmail)) {
      errors.email = 'Please enter a valid email address';
    }

    if (!signInPassword) {
      errors.password = 'Password is required';
    } else if (signInPassword.length < 4) {
      errors.password = 'Password must be at least 4 characters';
    }

    setSignInErrors(errors);

    if (Object.keys(errors).length === 0) {
      const isDemo =
        signInEmail.trim().toLowerCase() === 'test@gmail.com' &&
        signInPassword === 'test@1234';

      const rawName = signInEmail.split('@')[0] || 'user';
      const userName = isDemo ? 'Demo User' : rawName.charAt(0).toUpperCase() + rawName.slice(1);
      const userData = {
        name: userName,
        email: signInEmail.trim(),
        isGuest: false,
      };

      localStorage.setItem('visioniq_demo_session', 'true');
      localStorage.setItem('visioniq_user', JSON.stringify(userData));
      onLoginSuccess(userData);
    }
  };

  const handleSignUpSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const errors: {
      name?: string;
      email?: string;
      password?: string;
      confirmPassword?: string;
    } = {};

    if (!signUpName.trim()) {
      errors.name = 'Full name is required';
    } else if (signUpName.trim().length < 2) {
      errors.name = 'Name must be at least 2 characters';
    }

    if (!signUpEmail.trim()) {
      errors.email = 'Email address is required';
    } else if (!validateEmail(signUpEmail)) {
      errors.email = 'Please enter a valid email address';
    }

    if (!signUpPassword) {
      errors.password = 'Password is required';
    } else if (signUpPassword.length < 6) {
      errors.password = 'Password must be at least 6 characters';
    }

    if (!signUpConfirmPassword) {
      errors.confirmPassword = 'Please confirm your password';
    } else if (signUpPassword !== signUpConfirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

   setSignUpErrors(errors);

    if (Object.keys(errors).length === 0) {
      const userData = {
        name: signUpName.trim(),
        email: signUpEmail.trim(),
        isGuest: false,
      };

      localStorage.setItem('visioniq_demo_session', 'true');
      localStorage.setItem('visioniq_user', JSON.stringify(userData));
      onLoginSuccess(userData);
    }
  };

  const handleAutofillDemo = () => {
    setSignInEmail('test@gmail.com');
    setSignInPassword('test@1234');
    setSignInErrors({});
    setNotification('Demo credentials autofilled! Click "Sign In" to proceed.');
    setTimeout(() => setNotification(null), 3500);
  };

  const handleContinueAsGuest = () => {
    const guestUser = {
      name: 'Guest User',
      email: 'guest@visioniq.ai',
      isGuest: true,
    };
    localStorage.setItem('visioniq_demo_session', 'true');
    localStorage.setItem('visioniq_user', JSON.stringify(guestUser));
    onLoginSuccess(guestUser);
  };

  const handleForgotPassword = (e: React.MouseEvent) => {
    e.preventDefault();
    setNotification('Demo Mode: Use test@gmail.com / test@1234 or any email to log in directly.');
    setTimeout(() => setNotification(null), 4000);
  };

  const getSubheading = (isSignUp: boolean) => {
    if (isSignUp) {
      if (intendedTab === 'video') return 'Create an account to explore Video Intelligence';
      if (intendedTab === 'image') return 'Create an account to explore Image Intelligence';
      return 'Get started with VisionIQ Multimodal Studio';
    }
    if (intendedTab === 'video') return 'Sign in to access Video Intelligence & Moments';
    if (intendedTab === 'image') return 'Sign in to access Image Intelligence & Vector RAG';
    return 'Sign in to access VisionIQ Multimodal Studio';
  };

  return (
    <div className="auth-page-wrapper">
      <div className="auth-container">
        {/* Left Side: Brand & Value Highlights */}
        <div className="auth-brand-side">
          <div className="auth-brand-header-row">
            <div className="auth-brand-header">
              <div className="brand-icon-wrapper">
                <Sparkles className="brand-icon" size={20} />
              </div>
              <div className="brand-text-group">
                <div className="brand-title">
                  Vision<span className="brand-accent">IQ</span>
                </div>
                <div className="brand-subtitle">Multimodal Intelligence</div>
              </div>
            </div>

            {onBack && (
              <button
                type="button"
                id="btn-auth-back-overview"
                className="auth-back-btn"
                onClick={onBack}
                title="Return to Overview"
              >
                <ArrowLeft size={14} />
                <span>Overview</span>
              </button>
            )}
          </div>

          <div className="auth-hero-copy">
            <h2>See, Understand, & Query with Foundation Multimodal AI</h2>
            <p>
              Seamlessly identify real-world products, books, and objects with zero-shot vision, query grounded catalog specs with vector RAG, and retrieve temporal video moments.
            </p>
          </div>

          <div className="auth-features-list">
            <div className="auth-feature-pill">
              <div className="auth-feature-icon-box">
                <Layers size={16} />
              </div>
              <div>
                <strong>Zero-Shot Image Vision</strong>
                <p>Recognize real-world products & extract specifications</p>
              </div>
            </div>

            <div className="auth-feature-pill">
              <div className="auth-feature-icon-box">
                <Video size={16} />
              </div>
              <div>
                <strong>Temporal Video Moments</strong>
                <p>Jump to exact transcript timestamps with natural language</p>
              </div>
            </div>

            <div className="auth-feature-pill">
              <div className="auth-feature-icon-box">
                <Shield size={16} />
              </div>
              <div>
                <strong>Azure AI Foundry RAG</strong>
                <p>Grounded search across product catalogs with cosine similarity</p>
              </div>
            </div>
          </div>

          <div className="auth-azure-tag">
            <Sparkles size={13} className="btn-icon-mint" />
            <span>Powered by Azure OpenAI & Azure AI Search</span>
          </div>
        </div>

        {/* Right Side: Authentication Card */}
        <div className="auth-form-side">
          <div className="auth-card">
            <div className="auth-mode-toggle" role="tablist">
              <button
                type="button"
                id="auth-tab-signin"
                role="tab"
                aria-selected={authMode === 'signin'}
                className={`auth-toggle-btn ${authMode === 'signin' ? 'active' : ''}`}
                onClick={() => {
                  setAuthMode('signin');
                  setSignInErrors({});
                }}
              >
                <KeyRound size={15} />
                <span>Sign In</span>
              </button>
              <button
                type="button"
                id="auth-tab-signup"
                role="tab"
                aria-selected={authMode === 'signup'}
                className={`auth-toggle-btn ${authMode === 'signup' ? 'active' : ''}`}
                onClick={() => {
                  setAuthMode('signup');
                  setSignUpErrors({});
                }}
              >
                <UserCheck size={15} />
                <span>Sign Up</span>
              </button>
            </div>

            {notification && (
              <div className="auth-notification-banner">
                <CheckCircle2 size={16} className="notification-icon" />
                <span>{notification}</span>
              </div>
            )}

            {authMode === 'signin' ? (
              <form onSubmit={handleSignInSubmit} className="auth-form" noValidate>
                <div className="auth-form-header">
                  <h3>Welcome back</h3>
                  <p>{getSubheading(false)}</p>
                </div>

                <div className="form-group">
                  <label htmlFor="signin-email">Email Address</label>
                  <div className={`input-icon-wrapper ${signInErrors.email ? 'input-error' : ''}`}>
                    <Mail size={16} className="input-field-icon" />
                    <input
                      id="signin-email"
                      type="email"
                      placeholder="name@company.com"
                      value={signInEmail}
                      onChange={(e) => {
                        setSignInEmail(e.target.value);
                        if (signInErrors.email) {
                          setSignInErrors((prev) => ({ ...prev, email: undefined }));
                        }
                      }}
                      autoComplete="email"
                    />
                  </div>
                  {signInErrors.email && (
                    <div className="inline-error-msg">
                      <AlertCircle size={13} />
                      <span>{signInErrors.email}</span>
                    </div>
                  )}
                </div>

                <div className="form-group">
                  <div className="label-row">
                    <label htmlFor="signin-password">Password</label>
                    <a
                      href="#forgot-password"
                      className="forgot-password-link"
                      onClick={handleForgotPassword}
                    >
                      Forgot password?
                    </a>
                  </div>
                  <div className={`input-icon-wrapper ${signInErrors.password ? 'input-error' : ''}`}>
                    <Lock size={16} className="input-field-icon" />
                    <input
                      id="signin-password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Enter your password"
                      value={signInPassword}
                      onChange={(e) => {
                        setSignInPassword(e.target.value);
                        if (signInErrors.password) {
                          setSignInErrors((prev) => ({ ...prev, password: undefined }));
                        }
                      }}
                      autoComplete="current-password"
                    />
                    <button
                      type="button"
                      className="password-toggle-btn"
                      onClick={() => setShowPassword(!showPassword)}
                      tabIndex={-1}
                      title={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                  {signInErrors.password && (
                    <div className="inline-error-msg">
                      <AlertCircle size={13} />
                      <span>{signInErrors.password}</span>
                    </div>
                  )}
                </div>

                <button type="submit" id="btn-signin-submit" className="btn-auth-primary">
                  <span>Sign In</span>
                  <ArrowRight size={16} />
                </button>

                <div className="auth-demo-box">
                  <div className="demo-box-top">
                    <div className="demo-badge">Presentation Demo</div>
                    <button
                      type="button"
                      className="btn-demo-autofill"
                      onClick={handleAutofillDemo}
                      title="Quickly fill demo credentials"
                    >
                      Auto-fill
                    </button>
                  </div>
                  <div className="demo-box-credentials">
                    <div className="demo-cred-row">
                      <span className="demo-cred-label">Email:</span>
                      <code className="demo-cred-value">test@gmail.com</code>
                    </div>
                    <div className="demo-cred-row">
                      <span className="demo-cred-label">Password:</span>
                      <code className="demo-cred-value">test@1234</code>
                    </div>
                  </div>
                  <p className="demo-box-note">
                    Demo credentials: test@gmail.com / test@1234
                  </p>
                </div>

                <div className="auth-divider">
                  <span>or</span>
                </div>

                <button
                  type="button"
                  id="btn-guest-continue"
                  className="btn-guest-secondary"
                  onClick={handleContinueAsGuest}
                >
                  <User size={16} />
                  <span>Continue as Guest</span>
                </button>
              </form>
            ) : (
              <form onSubmit={handleSignUpSubmit} className="auth-form" noValidate>
                <div className="auth-form-header">
                  <h3>Create an account</h3>
                  <p>{getSubheading(true)}</p>
                </div>

                <div className="form-group">
                  <label htmlFor="signup-name">Full Name</label>
                  <div className={`input-icon-wrapper ${signUpErrors.name ? 'input-error' : ''}`}>
                    <User size={16} className="input-field-icon" />
                    <input
                      id="signup-name"
                      type="text"
                      placeholder="Alex Mercer"
                      value={signUpName}
                      onChange={(e) => {
                        setSignUpName(e.target.value);
                        if (signUpErrors.name) {
                          setSignUpErrors((prev) => ({ ...prev, name: undefined }));
                        }
                      }}
                      autoComplete="name"
                    />
                  </div>
                  {signUpErrors.name && (
                    <div className="inline-error-msg">
                      <AlertCircle size={13} />
                      <span>{signUpErrors.name}</span>
                    </div>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor="signup-email">Email Address</label>
                  <div className={`input-icon-wrapper ${signUpErrors.email ? 'input-error' : ''}`}>
                    <Mail size={16} className="input-field-icon" />
                    <input
                      id="signup-email"
                      type="email"
                      placeholder="name@company.com"
                      value={signUpEmail}
                      onChange={(e) => {
                        setSignUpEmail(e.target.value);
                        if (signUpErrors.email) {
                          setSignUpErrors((prev) => ({ ...prev, email: undefined }));
                        }
                      }}
                      autoComplete="email"
                    />
                  </div>
                  {signUpErrors.email && (
                    <div className="inline-error-msg">
                      <AlertCircle size={13} />
                      <span>{signUpErrors.email}</span>
                    </div>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor="signup-password">Password</label>
                  <div className={`input-icon-wrapper ${signUpErrors.password ? 'input-error' : ''}`}>
                    <Lock size={16} className="input-field-icon" />
                    <input
                      id="signup-password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="At least 6 characters"
                      value={signUpPassword}
                      onChange={(e) => {
                        setSignUpPassword(e.target.value);
                        if (signUpErrors.password) {
                          setSignUpErrors((prev) => ({ ...prev, password: undefined }));
                        }
                      }}
                      autoComplete="new-password"
                    />
                    <button
                      type="button"
                      className="password-toggle-btn"
                      onClick={() => setShowPassword(!showPassword)}
                      tabIndex={-1}
                      title={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                  {signUpErrors.password && (
                    <div className="inline-error-msg">
                      <AlertCircle size={13} />
                      <span>{signUpErrors.password}</span>
                    </div>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor="signup-confirm-password">Confirm Password</label>
                  <div className={`input-icon-wrapper ${signUpErrors.confirmPassword ? 'input-error' : ''}`}>
                    <Lock size={16} className="input-field-icon" />
                    <input
                      id="signup-confirm-password"
                      type={showConfirmPassword ? 'text' : 'password'}
                      placeholder="Re-enter your password"
                      value={signUpConfirmPassword}
                      onChange={(e) => {
                        setSignUpConfirmPassword(e.target.value);
                        if (signUpErrors.confirmPassword) {
                          setSignUpErrors((prev) => ({ ...prev, confirmPassword: undefined }));
                        }
                      }}
                      autoComplete="new-password"
                    />
                    <button
                      type="button"
                      className="password-toggle-btn"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      tabIndex={-1}
                      title={showConfirmPassword ? 'Hide password' : 'Show password'}
                    >
                      {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                  {signUpErrors.confirmPassword && (
                    <div className="inline-error-msg">
                      <AlertCircle size={13} />
                      <span>{signUpErrors.confirmPassword}</span>
                    </div>
                  )}
                </div>

                <button type="submit" id="btn-signup-submit" className="btn-auth-primary">
                  <span>Create Account</span>
                  <ArrowRight size={16} />
                </button>

                <div className="auth-divider">
                  <span>or</span>
                </div>

                <button
                  type="button"
                  id="btn-guest-signup"
                  className="btn-guest-secondary"
                  onClick={handleContinueAsGuest}
                >
                  <User size={16} />
                  <span>Continue as Guest</span>
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
