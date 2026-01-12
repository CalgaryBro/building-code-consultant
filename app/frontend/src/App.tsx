import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './contexts/AuthContext';
import { Layout } from './components/Layout';
import { ChatWidget } from './components/ChatWidget';
import { LandingPage } from './pages/LandingPage';
import { ExplorePage } from './pages/ExplorePage';
import { GuidePage } from './pages/GuidePage';
import { ReviewPage } from './pages/ReviewPage';
import { PermitsPage } from './pages/PermitsPage';
import { PermitApplicationPage } from './pages/PermitApplicationPage';
import { PermitDetailsPage } from './pages/PermitDetailsPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { ForgotPasswordPage } from './pages/ForgotPasswordPage';
import { ResetPasswordPage } from './pages/ResetPasswordPage';
import { VerifyEmailPage } from './pages/VerifyEmailPage';
import { HelpPage } from './pages/HelpPage';
import { ContactPage } from './pages/ContactPage';
import { PrivacyPage } from './pages/PrivacyPage';
import { TermsPage } from './pages/TermsPage';
import { AdminDashboardPage } from './pages/AdminDashboardPage';
import { AdminUsersPage } from './pages/AdminUsersPage';
import { ReviewQueuePage } from './pages/ReviewQueuePage';
import { SettingsPage } from './pages/SettingsPage';
import { DSSPCalculatorPage } from './pages/DSSPCalculatorPage';
import { QuantitySurveyPage } from './pages/QuantitySurveyPage';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Landing page has its own layout */}
            <Route path="/" element={<LandingPage />} />

            {/* Auth pages - no layout needed */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="/verify-email" element={<VerifyEmailPage />} />

            {/* Static pages - no layout needed */}
            <Route path="/help" element={<HelpPage />} />
            <Route path="/contact" element={<ContactPage />} />
            <Route path="/privacy" element={<PrivacyPage />} />
            <Route path="/terms" element={<TermsPage />} />

            {/* App pages with shared layout */}
            <Route
              path="/explore"
              element={
                <Layout>
                  <ExplorePage />
                </Layout>
              }
            />
            <Route
              path="/guide"
              element={
                <Layout>
                  <GuidePage />
                </Layout>
              }
            />
            <Route
              path="/review"
              element={
                <Layout>
                  <ReviewPage />
                </Layout>
              }
            />
            <Route
              path="/permits"
              element={
                <Layout>
                  <PermitsPage />
                </Layout>
              }
            />
            <Route
              path="/permits/new"
              element={
                <Layout>
                  <PermitApplicationPage />
                </Layout>
              }
            />
            <Route
              path="/permits/:id"
              element={
                <Layout>
                  <PermitDetailsPage />
                </Layout>
              }
            />
            <Route
              path="/permits/:id/edit"
              element={
                <Layout>
                  <PermitApplicationPage />
                </Layout>
              }
            />

            {/* Review Queue - for reviewers and admins */}
            <Route
              path="/review-queue"
              element={
                <Layout>
                  <ReviewQueuePage />
                </Layout>
              }
            />

            {/* Admin pages */}
            <Route
              path="/admin"
              element={
                <Layout>
                  <AdminDashboardPage />
                </Layout>
              }
            />
            <Route
              path="/admin/users"
              element={
                <Layout>
                  <AdminUsersPage />
                </Layout>
              }
            />

            {/* DSSP Calculator */}
            <Route
              path="/dssp"
              element={
                <Layout>
                  <DSSPCalculatorPage />
                </Layout>
              }
            />

            {/* Quantity Survey Calculator */}
            <Route
              path="/quantity-survey"
              element={
                <Layout>
                  <QuantitySurveyPage />
                </Layout>
              }
            />

            {/* Settings */}
            <Route
              path="/settings"
              element={
                <Layout>
                  <SettingsPage />
                </Layout>
              }
            />
          </Routes>

          {/* Floating Chat Widget - appears on all pages */}
          <ChatWidget />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
