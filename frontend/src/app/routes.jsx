import { Navigate } from 'react-router'
import { RequireAuth, RootLayout } from './session.jsx'
import { Forbidden, LoadingState, NotFound, RouteError } from '../components/ui.jsx'
import { ADMINS, REVIEWERS } from './navigation.js'
import { PRODUCT_NAME } from '../product.js'

// Each area is a lazy chunk: landing (GSAP), auth (video), shell and pages load independently.
const lazyNamed = (loader, name) => async () => ({ Component: (await loader())[name] })
const pages = () => import('./AppPages.jsx')
const authPages = () => import('../features/auth/AuthPages.jsx')
const page = (path, name, title) => ({ path, lazy: lazyNamed(pages, name), handle: { title } })
const indexPage = (name, title) => ({ index: true, lazy: lazyNamed(pages, name), handle: { title } })
// Legal area: one route line per page so each owner swaps only its own line (placeholder -> real page).
const legalShared = () => import('../features/legal/shared/LegalShared.jsx')
const placeholders = () => import('../features/legal/shared/Placeholders.jsx')
const legalPage = (path, loader, name, title) => ({ path, lazy: lazyNamed(loader, name), handle: { title } })
const authPage = (path, name, title, media) => ({ path, lazy: lazyNamed(authPages, name), handle: { title, authMedia: media } })

export const routes = [{
  id: 'root',
  element: <RootLayout />,
  errorElement: <RouteError />,
  hydrateFallbackElement: <LoadingState label={`Loading ${PRODUCT_NAME}…`} />,
  children: [
    { index: true, lazy: lazyNamed(() => import('../features/landing/LandingPage.jsx'), 'default'), handle: { title: PRODUCT_NAME } },
    {
      lazy: lazyNamed(() => import('../features/auth/AuthLayout.jsx'), 'default'),
      children: [
        authPage('login', 'LoginPage', 'Sign in', 'login'),
        authPage('signup', 'SignUpPage', 'Create account', 'signup'),
        authPage('forgot-password', 'ForgotPasswordPage', 'Forgot password', 'recovery'),
        authPage('verify-otp', 'VerifyOtpPage', 'Verify code', 'recovery'),
        authPage('reset-password', 'ResetPasswordPage', 'Reset password', 'recovery'),
        authPage('auth/callback', 'OAuthCallbackPage', 'Signing in', 'login'),
      ],
    },
    {
      path: 'app',
      element: <RequireAuth />,
      // First-login terms: accepted server-side before any Workbench page renders.
      children: [{ lazy: lazyNamed(() => import('../features/resources/TermsGate.jsx'), 'TermsGate'), children: [{
        lazy: lazyNamed(() => import('./AppShell.jsx'), 'default'),
        children: [
          { index: true, element: <Navigate to="dashboard" replace /> },
          { path: 'legal', lazy: lazyNamed(legalShared, 'LegalLayout'), children: [
            { index: true, element: <Navigate to="documents" replace /> },
            legalPage('dashboard', placeholders, 'LegalDashboardPlaceholder', 'Legal dashboard'),
            legalPage('documents', () => import('../features/legal/documents/DocumentsPage.jsx'), 'DocumentsPage', 'Documents'),
            legalPage('source', () => import('../features/legal/source/SourcePage.jsx'), 'SourcePage', 'Source viewer'),
            legalPage('contracts', () => import('../features/legal/contracts/ContractsPage.jsx'), 'ContractsPage', 'Contracts'),
            legalPage('reviews', () => import('../features/legal/reviews/ReviewsPage.jsx'), 'ReviewsPage', 'Review queue'),
            legalPage('compliance', placeholders, 'CompliancePlaceholder', 'Compliance'),
            legalPage('regulatory', placeholders, 'RegulatoryPlaceholder', 'Regulatory intelligence'),
            legalPage('summaries', placeholders, 'SummariesPlaceholder', 'Summaries'),
            legalPage('assistant', () => import('../features/legal/assistant/AssistantPage.jsx'), 'default', 'Legal assistant'),
            legalPage('obligations', placeholders, 'ObligationsPlaceholder', 'Obligations and tasks'),
            legalPage('audit', placeholders, 'LegalAuditPlaceholder', 'Legal audit and exports'),
          ] },
          page('dashboard', 'DashboardPage', 'Dashboard'),
          page('workspace', 'WorkspacePage', 'AI Workspace'),
          page('workspace/voice', 'VoiceWorkspacePage', 'Voice query'),
          page('agents', 'AgentsPage', 'Agents'),
          page('pid', 'PidPage', 'P&ID Intelligence'),
          page('maintenance', 'MaintenancePage', 'Maintenance & Sensors'),
          { path: 'operations', children: [
            { index: true, element: <Navigate to="handover" replace /> },
            page(':view', 'OperationsPage', 'Operations'),
          ] },
          page('knowledge', 'KnowledgePage', 'Knowledge'),
          page('gaps', 'GapsPage', 'Knowledge Gaps'),
          page('approvals', 'ApprovalsPage', 'Approvals'),
          page('executions', 'ExecutionsPage', 'Executions'),
          { path: 'audit', element: <RequireAuth roles={REVIEWERS} />, children: [indexPage('AuditPage', 'Audit')] },
          page('sovereignty', 'SovereigntyPage', 'Private runtime'),
          page('resources', 'ResourcesPage', 'Government Resources'),
          page('help', 'HelpPage', 'Help & Resources'),
          { path: 'admin', element: <RequireAuth roles={ADMINS} />, children: [
            indexPage('AdminPage', 'Administration'),
            page('*', 'AdminPage', 'Administration'),
          ] },
          page('profile', 'ProfilePage', 'Profile'),
          { path: '*', element: <NotFound />, handle: { title: 'Page not found' } },
        ],
      }] }],
    },
    { path: '403', element: <main id="main" className="standalone"><Forbidden /></main>, handle: { title: 'Access restricted' } },
    { path: '*', element: <main id="main" className="standalone"><NotFound /></main>, handle: { title: 'Page not found' } },
  ],
}]
