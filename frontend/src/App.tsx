import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './lib/auth';
import { LoginPage } from './pages/login/LoginPage';
import { AppShell } from './components/layout/AppShell';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { PlaceholderPage } from './pages/placeholder/PlaceholderPage';

const ProtectedLayout: React.FC<{ children: React.ReactNode; title?: string }> = ({
  children,
  title,
}) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center">
        <div className="flex items-center space-x-2 text-muted text-sm">
          <span className="animate-spin inline-block w-5 h-5 border-2 border-primary border-t-transparent rounded-full" />
          <span>Verifying session...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <AppShell title={title}>{children}</AppShell>;
};

const PublicOnlyRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center">
        <div className="flex items-center space-x-2 text-muted text-sm">
          <span className="animate-spin inline-block w-5 h-5 border-2 border-primary border-t-transparent rounded-full" />
          <span>Loading...</span>
        </div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public login */}
          <Route
            path="/login"
            element={
              <PublicOnlyRoute>
                <LoginPage />
              </PublicOnlyRoute>
            }
          />

          {/* Protected Routes */}
          <Route
            path="/"
            element={
              <ProtectedLayout title="Phase 1 Foundation Dashboard">
                <DashboardPage />
              </ProtectedLayout>
            }
          />

          <Route
            path="/producer/listings"
            element={
              <ProtectedLayout title="My Listings">
                <PlaceholderPage
                  title="My Listings"
                  phase="Phase 4 — Producer Listing Flow"
                  description="Publish crop lots with quantity, ask prices, and demand intelligence assistance."
                />
              </ProtectedLayout>
            }
          />

          <Route
            path="/buyer/requirements"
            element={
              <ProtectedLayout title="Buyer Requirements">
                <PlaceholderPage
                  title="Buyer Requirements"
                  phase="Phase 5 — Buyer Matching Engine"
                  description="Define demand specifications and review greedy bilateral matches against active producer lots."
                />
              </ProtectedLayout>
            }
          />

          <Route
            path="/market"
            element={
              <ProtectedLayout title="Market Discovery">
                <PlaceholderPage
                  title="Market Discovery"
                  phase="Phase 5 — Unified Marketplace"
                  description="Browse active crop listings, view benchmark price bands, and find supply by regional hub."
                />
              </ProtectedLayout>
            }
          />

          <Route
            path="/forecast"
            element={
              <ProtectedLayout title="Demand Intelligence">
                <PlaceholderPage
                  title="Demand Intelligence"
                  phase="Phase 3 — ML Demand Forecast"
                  description="7-day demand projections across regional hubs powered by LightGBM model inferences."
                />
              </ProtectedLayout>
            }
          />

          <Route
            path="/orders"
            element={
              <ProtectedLayout title="Order Management">
                <PlaceholderPage
                  title="Order Management"
                  phase="Phase 7 — Order Lifecycle & Settlement"
                  description="Track lifecycle status from PLACED through CONFIRMED, DISPATCHED, and DELIVERED."
                />
              </ProtectedLayout>
            }
          />

          <Route
            path="/ops/logistics"
            element={
              <ProtectedLayout title="Logistics & Fleet Dispatch">
                <PlaceholderPage
                  title="Logistics & Fleet Dispatch"
                  phase="Phase 6 — Transport Optimization"
                  description="Dispatch dedicated vehicles, evaluate empty-haul charges, and track regional transport."
                />
              </ProtectedLayout>
            }
          />

          <Route
            path="/analytics"
            element={
              <ProtectedLayout title="Impact Analytics">
                <PlaceholderPage
                  title="Impact Analytics"
                  phase="Phase 9 — Impact Analytics"
                  description="Track farmer net price realizations vs APMC benchmarks and platform waste reduction."
                />
              </ProtectedLayout>
            }
          />

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
