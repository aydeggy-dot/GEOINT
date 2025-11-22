import { Routes, Route, Link } from 'react-router-dom'
import { Suspense, lazy } from 'react'
import { useAuth } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'

// Lazy load pages for code splitting
const MapPage = lazy(() => import('./pages/MapPage'))
const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const ReportPage = lazy(() => import('./pages/ReportPage'))
const IncidentListPage = lazy(() => import('./pages/IncidentListPage'))
const IncidentDetailPage = lazy(() => import('./pages/IncidentDetailPage'))
const NearbyPage = lazy(() => import('./pages/NearbyPage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
const Setup2FAPage = lazy(() => import('./pages/Setup2FAPage'))
const AdminDashboardPage = lazy(() => import('./pages/AdminDashboardPage'))
const AdminUsersPage = lazy(() => import('./pages/AdminUsersPage'))
const AdminVerifyIncidentsPage = lazy(() => import('./pages/AdminVerifyIncidentsPage'))
const AdminAuditLogsPage = lazy(() => import('./pages/AdminAuditLogsPage'))

// Loading component
function LoadingFallback() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="flex flex-col items-center space-y-4">
        <div className="w-16 h-16 border-4 border-green-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-gray-600">Loading...</p>
      </div>
    </div>
  )
}

// Layout component with navigation
function Layout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user, logout } = useAuth()

  const handleLogout = async () => {
    try {
      await logout()
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Header */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-8">
              {/* Logo */}
              <Link to="/" className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-green-600 rounded-full"></div>
                <span className="font-bold text-xl text-gray-900">
                  Nigeria Security EWS
                </span>
              </Link>

              {/* Navigation Links */}
              {isAuthenticated && (
                <div className="hidden md:flex space-x-4">
                  <NavLink href="/">Map</NavLink>
                  <NavLink href="/dashboard">Dashboard</NavLink>
                  <NavLink href="/incidents">Incidents</NavLink>
                  <NavLink href="/nearby">Nearby</NavLink>
                  {user?.roles && (user.roles.includes('super_admin') || user.roles.includes('admin')) && (
                    <NavLink href="/admin">Admin</NavLink>
                  )}
                </div>
              )}
            </div>

            {/* Right Side Actions */}
            <div className="flex items-center space-x-4">
              {isAuthenticated ? (
                <>
                  <Link
                    to="/report"
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors"
                  >
                    Report Incident
                  </Link>

                  {/* User Menu */}
                  <div className="flex items-center space-x-3">
                    <span className="text-sm text-gray-700">{user?.email}</span>
                    <Link
                      to="/settings/2fa"
                      className="text-sm text-gray-700 hover:text-gray-900"
                    >
                      2FA
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="text-sm text-gray-700 hover:text-gray-900 font-medium"
                    >
                      Logout
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="text-sm text-gray-700 hover:text-gray-900 font-medium"
                  >
                    Login
                  </Link>
                  <Link
                    to="/register"
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                  >
                    Sign Up
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main>{children}</main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-sm text-gray-500">
            <p>Nigeria Security Early Warning System &copy; 2025</p>
            <p className="mt-1">Real-time security incident mapping and analysis</p>
          </div>
        </div>
      </footer>
    </div>
  )
}

// Navigation Link Component
function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  const isActive = window.location.pathname === href

  return (
    <Link
      to={href}
      className={`inline-flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
        isActive
          ? 'text-green-600 bg-green-50'
          : 'text-gray-700 hover:text-green-600 hover:bg-gray-50'
      }`}
    >
      {children}
    </Link>
  )
}

function App() {
  const { isAuthenticated } = useAuth()

  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected Routes */}
        <Route
          path="/"
          element={
            <Layout>
              <ProtectedRoute>
                <MapPage />
              </ProtectedRoute>
            </Layout>
          }
        />
        <Route
          path="/dashboard"
          element={
            <Layout>
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            </Layout>
          }
        />
        <Route
          path="/report"
          element={
            <Layout>
              <ProtectedRoute>
                <ReportPage />
              </ProtectedRoute>
            </Layout>
          }
        />
        <Route
          path="/incidents"
          element={
            <Layout>
              <ProtectedRoute>
                <IncidentListPage />
              </ProtectedRoute>
            </Layout>
          }
        />
        <Route
          path="/incidents/:id"
          element={
            <Layout>
              <ProtectedRoute>
                <IncidentDetailPage />
              </ProtectedRoute>
            </Layout>
          }
        />
        <Route
          path="/nearby"
          element={
            <Layout>
              <ProtectedRoute>
                <NearbyPage />
              </ProtectedRoute>
            </Layout>
          }
        />
        <Route
          path="/settings/2fa"
          element={
            <Layout>
              <ProtectedRoute>
                <Setup2FAPage />
              </ProtectedRoute>
            </Layout>
          }
        />

        {/* Admin Routes */}
        <Route
          path="/admin"
          element={
            <Layout>
              <ProtectedRoute>
                <AdminDashboardPage />
              </ProtectedRoute>
            </Layout>
          }
        />
        <Route
          path="/admin/users"
          element={
            <Layout>
              <ProtectedRoute>
                <AdminUsersPage />
              </ProtectedRoute>
            </Layout>
          }
        />
        <Route
          path="/admin/incidents/verify"
          element={
            <Layout>
              <ProtectedRoute>
                <AdminVerifyIncidentsPage />
              </ProtectedRoute>
            </Layout>
          }
        />
        <Route
          path="/admin/audit-logs"
          element={
            <Layout>
              <ProtectedRoute>
                <AdminAuditLogsPage />
              </ProtectedRoute>
            </Layout>
          }
        />

        {/* 404 Page */}
        <Route
          path="*"
          element={
            <Layout>
              <NotFoundPage />
            </Layout>
          }
        />
      </Routes>
    </Suspense>
  )
}

// 404 Page
function NotFoundPage() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-gray-900">404</h1>
        <p className="mt-4 text-xl text-gray-600">Page not found</p>
        <Link
          to="/"
          className="mt-8 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
        >
          Go Home
        </Link>
      </div>
    </div>
  )
}

export default App
