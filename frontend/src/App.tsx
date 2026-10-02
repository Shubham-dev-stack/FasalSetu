import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './lib/auth';
import { LoginPage } from './pages/login/LoginPage';
import { AppShell } from './components/layout/AppShell';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { PlaceholderPage } from './pages/placeholder/PlaceholderPage';
import { ListingsPage } from './pages/producer/ListingsPage';
import { NewListingPage } from './pages/producer/NewListingPage';
import { ProducerProfilePage } from './pages/producer/ProducerProfilePage';
import { RequirementsPage } from './pages/buyer/RequirementsPage';
import { NewRequirementPage } from './pages/buyer/NewRequirementPage';
import { MatchPage } from './pages/buyer/MatchPage';
import { BuyerProfilePage } from './pages/buyer/BuyerProfilePage';
import { MarketplacePage } from './pages/market/MarketplacePage';
import { OrdersPage } from './pages/orders/OrdersPage';
import { OrderDetailPage } from './pages/orders/OrderDetailPage';
import { ForecastPage } from './pages/forecast/ForecastPage';

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
              <ProtectedLayout title="My Produce Listings">
                <ListingsPage />
              </ProtectedLayout>
            }
          />

          <Route
            path="/producer/listings/new"
            element={
              <ProtectedLayout title="Publish Produce Lot">
                <NewListingPage />
              </ProtectedLayout>
            }
          />

          <Route
            path="/producer/profile"
            element={
              <ProtectedLayout title="Producer Profile">
                <ProducerProfilePage />
              </ProtectedLayout>
            }
          />


          <Route
            path="/buyer/requirements"
            element={
              <ProtectedLayout title="My Procurement Requirements">
                <RequirementsPage />
              </ProtectedLayout>
            }
          />

          <Route
            path="/buyer/requirements/new"
            element={
              <ProtectedLayout title="Post Procurement Requirement">
                <NewRequirementPage />
              </ProtectedLayout>
            }
          />

          <Route
            path="/buyer/requirements/:id/match"
            element={
              <ProtectedLayout title="Matching & Multi-Source Allocation">
                <MatchPage />
              </ProtectedLayout>
            }
          />

          <Route
            path="/buyer/profile"
            element={
              <ProtectedLayout title="Buyer Organization Profile">
                <BuyerProfilePage />
              </ProtectedLayout>
            }
          />

          <Route
            path="/market"
            element={
              <ProtectedLayout title="Unified Marketplace">
                <MarketplacePage />
              </ProtectedLayout>
            }
          />

          <Route
            path="/forecast"
            element={
              <ProtectedLayout title="Demand Intelligence">
                <ForecastPage />
              </ProtectedLayout>
            }
          />

          <Route
            path="/orders"
            element={
              <ProtectedLayout title="Order Management">
                <OrdersPage />
              </ProtectedLayout>
            }
          />

          <Route
            path="/orders/:id"
            element={
              <ProtectedLayout title="Order Details">
                <OrderDetailPage />
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
