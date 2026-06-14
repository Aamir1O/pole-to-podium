'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Flag, 
  BrainCircuit, 
  User, 
  Users2, 
  Spline, 
  BarChart3, 
  Calendar 
} from 'lucide-react';

const NAV_ITEMS = [
  { path: '/', label: 'Home', icon: LayoutDashboard },
  { path: '/race-center', label: 'Race Center', icon: Flag },
  { path: '/predictions', label: 'Predictions', icon: BrainCircuit },
  { path: '/drivers', label: 'Drivers', icon: User },
  { path: '/teams', label: 'Teams', icon: Users2 },
  { path: '/telemetry', label: 'Telemetry', icon: Spline },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
];

export default function Navbar() {
  const pathname = usePathname();
  const [nextRace, setNextRace] = useState<string>('Loading...');

  useEffect(() => {
    // Fetch next race info from the dashboard endpoint
    fetch('http://127.0.0.1:8000/api/v1/dashboard')
      .then((res) => res.json())
      .then((data) => {
        if (data.next_race && data.next_race.name) {
          setNextRace(data.next_race.name);
        } else {
          setNextRace('Season Complete');
        }
      })
      .catch(() => setNextRace('Spanish Grand Prix')); // Fallback
  }, []);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-neutral-900 bg-black/95 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        
        {/* Brand Logo */}
        <div className="flex items-center gap-3">
          <Link href="/" className="flex items-center gap-2 font-sans text-lg font-black tracking-tight text-white uppercase">
            <span>
              Pole <span className="text-red-600">to</span> Podium
            </span>
          </Link>
          <div className="hidden h-5 w-[1px] bg-neutral-800 sm:block"></div>
          
          {/* Next Race indicator */}
          <div className="hidden items-center gap-1.5 rounded-full border border-neutral-900 bg-neutral-950 px-3 py-1 font-mono text-xs font-semibold sm:flex">
            <Calendar className="h-3 w-3 text-neutral-500" />
            <span className="text-neutral-500 uppercase tracking-wider">Next Round:</span>
            <span className="text-red-500 uppercase font-bold">{nextRace}</span>
          </div>
        </div>

        {/* Desktop Navigation Links */}
        <nav className="hidden items-center gap-1 md:flex">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.path;
            return (
              <Link
                key={item.path}
                href={item.path}
                className={`flex items-center gap-1.5 rounded-md px-3 py-2 text-xs font-semibold transition-all duration-150 ${
                  isActive 
                    ? 'bg-neutral-900 text-white border-b-2 border-red-600 rounded-b-none' 
                    : 'text-neutral-400 hover:bg-neutral-950 hover:text-neutral-200'
                }`}
              >
                <Icon className={`h-3.5 w-3.5 ${isActive ? 'text-red-500' : 'text-neutral-500'}`} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Mobile menu trigger / next race fallback for small views */}
        <div className="flex items-center gap-2 md:hidden">
          <div className="flex items-center gap-1 rounded-full border border-neutral-900 bg-neutral-950 px-2.5 py-0.5 font-mono text-[10px] font-bold">
            <span className="text-red-500 uppercase">{nextRace}</span>
          </div>
        </div>

      </div>
      
      {/* Mobile nav bar under logo for small screens */}
      <div className="border-t border-neutral-950 bg-black/40 py-1 md:hidden">
        <div className="flex justify-around px-2">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.path;
            return (
              <Link
                key={item.path}
                href={item.path}
                className={`flex flex-col items-center gap-0.5 py-1 text-[9px] font-bold ${
                  isActive ? 'text-red-500' : 'text-neutral-500'
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                <span>{item.label.split(' ')[0]}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </header>
  );
}
