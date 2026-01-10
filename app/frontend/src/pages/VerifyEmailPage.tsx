import { useState, useEffect } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Building2, CheckCircle2, AlertCircle, Mail, ArrowRight, Loader2 } from 'lucide-react';
import { authApi, AuthApiError } from '../api/auth';

// Blueprint grid background component
function BlueprintGrid() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `
            linear-gradient(to right, #1e3a5f 1px, transparent 1px),
            linear-gradient(to bottom, #1e3a5f 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
        }}
      />
      <div
        className="absolute inset-0 opacity-[0.015]"
        style={{
          backgroundImage: `
            linear-gradient(to right, #1e3a5f 1px, transparent 1px),
            linear-gradient(to bottom, #1e3a5f 1px, transparent 1px)
          `,
          backgroundSize: '8px 8px',
        }}
      />
      <svg className="absolute top-20 left-1/4 w-64 h-64 text-slate-200/30" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="0.5" strokeDasharray="4 2" />
        <circle cx="50" cy="50" r="35" fill="none" stroke="currentColor" strokeWidth="0.5" />
        <circle cx="50" cy="50" r="25" fill="none" stroke="currentColor" strokeWidth="0.5" strokeDasharray="2 4" />
      </svg>
      <div className="absolute top-8 left-8 w-16 h-16 border-l-2 border-t-2 border-slate-200/20" />
      <div className="absolute bottom-8 right-8 w-16 h-16 border-r-2 border-b-2 border-slate-200/20" />
    </div>
  );
}

type VerificationStatus = 'verifying' | 'success' | 'error' | 'no-token';

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [status, setStatus] = useState<VerificationStatus>('verifying');
  const [error, setError] = useState<string | null>(null);
  const [isResending, setIsResending] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);

  useEffect(() => {
    if (!token) {
      setStatus('no-token');
      return;
    }

    const verifyEmail = async () => {
      try {
        await authApi.verifyEmail(token);
        setStatus('success');
      } catch (err) {
        const message = err instanceof AuthApiError ? err.message : 'Failed to verify email';
        setError(message);
        setStatus('error');
      }
    };

    verifyEmail();
  }, [token]);

  const handleResendVerification = async () => {
    setIsResending(true);
    setResendSuccess(false);
    try {
      await authApi.resendVerification();
      setResendSuccess(true);
    } catch (err) {
      const message = err instanceof AuthApiError ? err.message : 'Failed to resend verification email';
      setError(message);
    } finally {
      setIsResending(false);
    }
  };

  const handleContinue = () => {
    navigate('/explore');
  };

  return (
    <div className="min-h-screen flex bg-gradient-to-b from-slate-50 to-white relative overflow-hidden">
      <BlueprintGrid />

      {/* Gradient orbs */}
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-amber-400/10 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-teal-400/10 rounded-full blur-3xl" />

      <div className="flex-1 flex items-center justify-center px-4 py-12 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          {/* Logo */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-center mb-8"
          >
            <Link to="/" className="inline-flex items-center gap-3 group">
              <div className="relative w-12 h-12 rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center overflow-hidden shadow-lg">
                <Building2 className="w-6 h-6 text-amber-400" />
                <div className="absolute inset-0 bg-gradient-to-t from-amber-500/20 to-transparent" />
              </div>
              <div className="flex flex-col text-left">
                <span className="font-semibold text-slate-900 tracking-tight text-lg">CodeCheck</span>
                <span className="text-[10px] font-medium text-amber-600 tracking-widest uppercase">Calgary</span>
              </div>
            </Link>
          </motion.div>

          {/* Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-2xl shadow-xl shadow-slate-900/5 border border-slate-200 p-8"
          >
            {/* Verifying state */}
            {status === 'verifying' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-8"
              >
                <div className="mx-auto w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mb-6">
                  <Loader2 className="w-8 h-8 text-amber-600 animate-spin" />
                </div>
                <h2 className="text-2xl font-bold text-slate-900 mb-3">Verifying your email</h2>
                <p className="text-slate-600">
                  Please wait while we verify your email address...
                </p>
              </motion.div>
            )}

            {/* Success state */}
            {status === 'success' && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center"
              >
                <div className="mx-auto w-16 h-16 bg-teal-100 rounded-full flex items-center justify-center mb-6">
                  <CheckCircle2 className="w-8 h-8 text-teal-600" />
                </div>
                <h2 className="text-2xl font-bold text-slate-900 mb-3">Email verified!</h2>
                <p className="text-slate-600 mb-8">
                  Your email has been verified successfully. You now have full access to CodeCheck Calgary.
                </p>
                <motion.button
                  onClick={handleContinue}
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                  className="w-full btn btn-primary py-3 text-base font-semibold hover:bg-amber-600 transition-colors group"
                >
                  <span className="flex items-center justify-center gap-2">
                    Continue to app
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </span>
                </motion.button>
              </motion.div>
            )}

            {/* Error state */}
            {status === 'error' && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center"
              >
                <div className="mx-auto w-16 h-16 bg-rose-100 rounded-full flex items-center justify-center mb-6">
                  <AlertCircle className="w-8 h-8 text-rose-600" />
                </div>
                <h2 className="text-2xl font-bold text-slate-900 mb-3">Verification failed</h2>
                <p className="text-slate-600 mb-2">
                  {error || 'We could not verify your email address.'}
                </p>
                <p className="text-sm text-slate-500 mb-8">
                  The verification link may have expired or already been used.
                </p>

                {resendSuccess ? (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-6 p-4 bg-teal-50 border border-teal-200 rounded-xl flex items-start gap-3"
                  >
                    <CheckCircle2 className="w-5 h-5 text-teal-500 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-teal-700">
                      A new verification email has been sent. Please check your inbox.
                    </p>
                  </motion.div>
                ) : (
                  <motion.button
                    onClick={handleResendVerification}
                    disabled={isResending}
                    whileHover={{ scale: 1.01 }}
                    whileTap={{ scale: 0.99 }}
                    className="w-full btn btn-secondary py-3 text-base font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-700 transition-colors mb-4"
                  >
                    {isResending ? (
                      <span className="flex items-center justify-center gap-2">
                        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                            fill="none"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          />
                        </svg>
                        Sending...
                      </span>
                    ) : (
                      <span className="flex items-center justify-center gap-2">
                        <Mail className="w-5 h-5" />
                        Resend verification email
                      </span>
                    )}
                  </motion.button>
                )}

                <Link
                  to="/login"
                  className="block w-full btn btn-outline py-3 text-base font-semibold hover:bg-slate-50 transition-colors"
                >
                  Back to sign in
                </Link>
              </motion.div>
            )}

            {/* No token state */}
            {status === 'no-token' && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center"
              >
                <div className="mx-auto w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mb-6">
                  <Mail className="w-8 h-8 text-amber-600" />
                </div>
                <h2 className="text-2xl font-bold text-slate-900 mb-3">Verify your email</h2>
                <p className="text-slate-600 mb-8">
                  Please check your inbox for a verification email and click the link to verify your account.
                </p>

                {resendSuccess ? (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-6 p-4 bg-teal-50 border border-teal-200 rounded-xl flex items-start gap-3"
                  >
                    <CheckCircle2 className="w-5 h-5 text-teal-500 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-teal-700">
                      A new verification email has been sent. Please check your inbox.
                    </p>
                  </motion.div>
                ) : (
                  <>
                    <p className="text-sm text-slate-500 mb-6">
                      Did not receive the email? Check your spam folder or request a new one.
                    </p>
                    <motion.button
                      onClick={handleResendVerification}
                      disabled={isResending}
                      whileHover={{ scale: 1.01 }}
                      whileTap={{ scale: 0.99 }}
                      className="w-full btn btn-primary py-3 text-base font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-amber-600 transition-colors mb-4"
                    >
                      {isResending ? (
                        <span className="flex items-center justify-center gap-2">
                          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                            <circle
                              className="opacity-25"
                              cx="12"
                              cy="12"
                              r="10"
                              stroke="currentColor"
                              strokeWidth="4"
                              fill="none"
                            />
                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            />
                          </svg>
                          Sending...
                        </span>
                      ) : (
                        <span className="flex items-center justify-center gap-2">
                          <Mail className="w-5 h-5" />
                          Resend verification email
                        </span>
                      )}
                    </motion.button>
                  </>
                )}

                <Link
                  to="/login"
                  className="block w-full btn btn-outline py-3 text-base font-semibold hover:bg-slate-50 transition-colors"
                >
                  Back to sign in
                </Link>
              </motion.div>
            )}
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}

export default VerifyEmailPage;
