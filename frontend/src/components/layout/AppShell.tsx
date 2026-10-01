import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../lib/auth';
import { Navbar } from './Navbar';
import {
  Package,
  TrendingUp,
  ShoppingBag,
  ClipboardList,
  BarChart3,
  Truck,
  Layers,
  UserCircle,
} from 'lucide-react';

interface NavItem {
  label: string;
  to: string;
  icon: React.ComponentType<{ className?: string }>;
}

export const AppShell: React.FC<{ children: React.ReactNode; title?: string }> = ({
  children,
  title,
}) => {
  const { user } = useAuth();

  const getNavItems = (): NavItem[] => {
    if (!user) return [];

    const roleUpper = user.role.toUpperCase();

    if (roleUpper === 'PRODUCER' || user.role === 'farmer' || user.role === 'fpo') {
      return [
        { label: 'My Listings', to: '/producer/listings', icon: Package },
        { label: 'Profile', to: '/producer/profile', icon: UserCircle },
        { label: 'Demand', to: '/forecast', icon: TrendingUp },
        { label: 'Market', to: '/market', icon: ShoppingBag },
        { label: 'Orders', to: '/orders', icon: ClipboardList },
        { label: 'Analytics', to: '/analytics', icon: BarChart3 },
      ];
    }


    if (roleUpper === 'BUYER' || user.role.startsWith('buyer_')) {
      return [
        { label: 'My Demands', to: '/buyer/requirements', icon: Layers },
        { label: 'Post Demand', to: '/buyer/requirements/new', icon: ShoppingBag },
        { label: 'Buyer Profile', to: '/buyer/profile', icon: UserCircle },
        { label: 'Market', to: '/market', icon: Package },
        { label: 'Orders', to: '/orders', icon: ClipboardList },
        { label: 'Analytics', to: '/analytics', icon: BarChart3 },
      ];
    }

    if (user.role === 'operator') {
      return [
        { label: 'Logistics', to: '/ops/logistics', icon: Truck },
        { label: 'Orders', to: '/orders', icon: ClipboardList },
        { label: 'Market', to: '/market', icon: ShoppingBag },
        { label: 'Demand', to: '/forecast', icon: TrendingUp },
        { label: 'Analytics', to: '/analytics', icon: BarChart3 },
      ];
    }

    // Default transporter or fallback
    return [
      { label: 'Orders', to: '/orders', icon: ClipboardList },
      { label: 'Market', to: '/market', icon: ShoppingBag },
      { label: 'Analytics', to: '/analytics', icon: BarChart3 },
    ];
  };

  const navItems = getNavItems();

  return (
    <div className="min-h-screen bg-bg flex flex-col text-ink">
      <Navbar title={title} />

      <div className="flex-1 flex max-w-7xl w-full mx-auto pb-16 lg:pb-0">
        {/* Desktop Sidebar (>= 1024px) */}
        <aside className="hidden lg:block w-60 border-r border-gray-200 py-6 px-4 bg-surface shrink-0">
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-primary-soft text-primary font-semibold'
                        : 'text-muted hover:bg-gray-100 hover:text-ink'
                    }`
                  }
                >
                  <Icon className="w-5 h-5 shrink-0" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 min-w-0">
          {children}
        </main>
      </div>

      {/* Mobile Bottom Navigation (< 1024px) */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 bg-surface border-t border-gray-200 px-2 py-1.5 flex justify-around items-center z-40">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex flex-col items-center py-1 px-2 rounded-lg text-[11px] font-medium transition-colors min-w-[56px] ${
                  isActive ? 'text-primary font-semibold' : 'text-muted hover:text-ink'
                }`
              }
            >
              <Icon className="w-5 h-5 mb-0.5" />
              <span className="truncate">{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </div>
  );
};
