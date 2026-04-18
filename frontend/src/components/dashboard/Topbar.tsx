'use client';

import { useState, useEffect } from 'react';
import { Bell, Search } from 'lucide-react';

const USER_NAMES = [
  "Aarav Sharma",
  "Riya Patel",
  "Vikram Singh",
  "Neha Gupta",
  "Rahul Kumar",
  "Priya Desai",
  "Aditya Kapoor",
  "Ananya Joshi",
  "Karthik Reddy",
  "Meera Iyer"
];

export default function Topbar() {
  const [userName, setUserName] = useState("Admin");
  const [initials, setInitials] = useState("AD");

  useEffect(() => {
    const randomIndex = Math.floor(Math.random() * USER_NAMES.length);
    const selectedName = USER_NAMES[randomIndex];
    setUserName(selectedName);
    
    const nameParts = selectedName.split(' ');
    if (nameParts.length >= 2) {
      setInitials(`${nameParts[0][0]}${nameParts[1][0]}`);
    } else {
      setInitials(selectedName.substring(0, 2).toUpperCase());
    }
  }, []);

  return (
    <header className="h-16 px-6 border-b border-stone-200 bg-white/80 backdrop-blur-md flex items-center justify-between z-20 sticky top-0">
      
      {/* Global Search Mock */}
      <div className="flex items-center max-w-md w-full relative">
        <Search className="w-4 h-4 text-stone-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input 
          type="text" 
          placeholder="Search extracted names, OCR IDs, or document hashes..."
          className="w-full pl-10 pr-4 py-2 bg-stone-50 border border-stone-200 rounded-lg text-sm text-stone-900 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500 transition-all placeholder-stone-400"
        />
      </div>

      <div className="flex items-center gap-6">
        {/* Notifications */}
        <button className="relative p-2 text-stone-400 hover:text-stone-900 transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-orange-500 border border-white"></span>
        </button>

        {/* User Profile */}
        <div className="flex items-center gap-3 border-l border-stone-200 pl-6 cursor-pointer group">
          <div className="text-right hidden sm:block">
            <p className="text-sm font-medium text-stone-900 group-hover:text-orange-600 transition-colors">{userName}</p>
          </div>
          <div className="w-9 h-9 rounded-full bg-stone-100 border border-stone-200 flex items-center justify-center font-bold text-stone-700 transform transition-transform hover:scale-105">
            {initials}
          </div>
        </div>
      </div>
      
    </header>
  );
}
