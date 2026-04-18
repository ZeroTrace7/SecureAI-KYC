'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Sparkles, LayoutDashboard, FileText, Activity, Users, Settings, LogOut } from 'lucide-react';
import BrandName from '@/components/BrandName';

export default function Sidebar() {
  const pathname = usePathname();

  const links = [
    { name: 'Overview',       href: '/dashboard',            icon: LayoutDashboard },
    { name: 'Documents',      href: '/dashboard/documents',  icon: FileText },
    { name: 'Risk Analytics', href: '/dashboard/analytics',  icon: Activity },
    { name: 'Team Hub',       href: '/dashboard/team',       icon: Users },
  ];

  return (
    <aside className="w-64 border-r border-stone-200 bg-white backdrop-blur-xl flex flex-col pt-6 pb-4 animate-slide-in-left shadow-sm z-20">
      {/* Logo */}
      <div className="px-6 mb-8 mt-2">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center shadow-[0_0_15px_rgba(249,115,22,0.3)] group-hover:shadow-[0_0_22px_rgba(249,115,22,0.5)] transition-all duration-300 animate-bounce-subtle">
            <Sparkles className="w-4 h-4 text-white group-hover:rotate-12 transition-transform duration-300" />
          </div>
          {/* Rotating English / Hindi brand name */}
          <BrandName
            className="text-xl font-semibold tracking-tight text-stone-900 group-hover:text-orange-600 transition-colors duration-200"
          />
        </Link>
      </div>

      {/* Navigation */}
      <div className="flex-1 px-4 space-y-1">
        <div className="px-2 mb-2 text-xs font-semibold uppercase tracking-wider text-stone-400">
          Command Center
        </div>
        {links.map((link, i) => {
          const isActive = pathname === link.href;
          const Icon = link.icon;
          return (
            <Link
              key={link.name}
              href={link.href}
              style={{ animationDelay: `${i * 60}ms` }}
              className={`animate-fade-in flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 hover:-translate-x-0.5 ${
                isActive
                  ? 'bg-orange-50 text-orange-600 border border-orange-200 shadow-sm'
                  : 'text-stone-500 hover:text-stone-900 hover:bg-stone-50 border border-transparent hover:border-stone-100'
              }`}
            >
              <Icon className={`w-5 h-5 transition-transform duration-200 ${isActive ? 'scale-110' : 'group-hover:scale-110'}`} />
              {link.name}
            </Link>
          );
        })}
      </div>

      {/* Bottom Actions */}
      <div className="px-4 pt-6 mt-6 border-t border-stone-200 space-y-1">
        <Link
          href="/dashboard/settings"
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-stone-500 hover:text-stone-900 hover:bg-stone-50 transition-all duration-200 hover:translate-x-0.5 border border-transparent hover:border-stone-100"
        >
          <Settings className="w-5 h-5 hover:rotate-90 transition-transform duration-300" />
          Settings
        </Link>
        <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-red-500 hover:text-red-700 hover:bg-red-50 transition-all duration-200 hover:translate-x-0.5 border border-transparent hover:border-red-100">
          <LogOut className="w-5 h-5 transition-transform duration-200 group-hover:translate-x-1" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
