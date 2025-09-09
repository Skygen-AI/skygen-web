"use client";

import React, { useState } from "react";
import { 
  Monitor, 
  Smartphone, 
  Tablet, 
  Laptop, 
  HardDrive,
  Settings as SettingsIcon,
  Wind,
  MessageCircle,
  Wifi,
  WifiOff,
  MoreVertical,
  Eye,
  Trash2,
  Settings
} from "lucide-react";
import { Sidebar, SidebarBody, SidebarLink } from "../../components/ui/sidebar";

interface Device {
  id: string;
  name: string;
  type: 'desktop' | 'laptop' | 'mobile' | 'tablet';
  os: string;
  browser: string;
  location: string;
  lastActive: string;
  isOnline: boolean;
  isCurrent: boolean;
  ipAddress: string;
}

const mockDevices: Device[] = [
  {
    id: "1",
    name: "MacBook Pro",
    type: "laptop",
    os: "macOS Sonoma 14.6",
    browser: "Chrome 120.0",
    location: "Moscow, Russia",
    lastActive: "Active now",
    isOnline: true,
    isCurrent: true,
    ipAddress: "192.168.1.15"
  },
  {
    id: "2",
    name: "iPhone 15 Pro",
    type: "mobile",
    os: "iOS 17.2",
    browser: "Safari",
    location: "Moscow, Russia",
    lastActive: "2 hours ago",
    isOnline: false,
    isCurrent: false,
    ipAddress: "192.168.1.22"
  },
  {
    id: "3",
    name: "iPad Air",
    type: "tablet",
    os: "iPadOS 17.2",
    browser: "Safari",
    location: "Moscow, Russia",
    lastActive: "1 day ago",
    isOnline: false,
    isCurrent: false,
    ipAddress: "192.168.1.18"
  },
  {
    id: "4",
    name: "Windows Desktop",
    type: "desktop",
    os: "Windows 11 Pro",
    browser: "Edge 120.0",
    location: "Saint Petersburg, Russia",
    lastActive: "3 days ago",
    isOnline: false,
    isCurrent: false,
    ipAddress: "95.161.45.123"
  }
];

function DeviceIcon({ type, className }: { type: Device['type']; className?: string }) {
  switch (type) {
    case 'desktop':
      return <Monitor className={className} />;
    case 'laptop':
      return <Laptop className={className} />;
    case 'mobile':
      return <Smartphone className={className} />;
    case 'tablet':
      return <Tablet className={className} />;
    default:
      return <Monitor className={className} />;
  }
}


function DeviceRow({ device }: { device: Device }) {
  const [showActions, setShowActions] = useState(false);

  return (
    <div className="relative group flex items-center gap-4 px-4 py-3 hover:bg-neutral-50 dark:hover:bg-neutral-800/50 border-b border-neutral-200 dark:border-neutral-700 last:border-b-0">
      {/* Device Icon */}
      <div className="relative flex-shrink-0">
        <div className="h-8 w-8 rounded-lg bg-neutral-100 dark:bg-neutral-700 flex items-center justify-center">
          <DeviceIcon type={device.type} className="h-4 w-4 text-neutral-600 dark:text-neutral-400" />
        </div>
        {/* Online Status */}
        <div className={`absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border border-white dark:border-neutral-800 ${
          device.isOnline ? 'bg-neutral-900 dark:bg-neutral-100' : 'bg-neutral-400'
        }`} />
      </div>

      {/* Device Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h3 className="font-medium text-neutral-900 dark:text-neutral-100 truncate text-sm">
            {device.name}
          </h3>
          {device.isCurrent && (
            <span className="px-1.5 py-0.5 bg-neutral-100 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300 text-xs rounded">
              Current
            </span>
          )}
          {device.isOnline && (
            <Wifi size={12} className="text-neutral-900 dark:text-neutral-100 flex-shrink-0" />
          )}
          {!device.isOnline && (
            <WifiOff size={12} className="text-neutral-400 flex-shrink-0" />
          )}
        </div>
        
        <div className="flex items-center gap-4 text-xs text-neutral-600 dark:text-neutral-400 mt-0.5">
          <span>{device.os}</span>
          <div className="flex items-center gap-1">
            <span className={device.isOnline ? "text-neutral-900 dark:text-neutral-100" : "text-neutral-500 dark:text-neutral-400"}>
              {device.isOnline ? "Online" : "Offline"}
            </span>
          </div>
        </div>
      </div>

      {/* IP Address */}
      <div className="text-xs text-neutral-400 dark:text-neutral-600 font-mono flex-shrink-0">
        {device.ipAddress}
      </div>

      {/* Actions Menu */}
      <div className="relative flex-shrink-0">
        <button 
          onClick={() => setShowActions(!showActions)}
          className="p-1 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-700 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <MoreVertical size={14} className="text-neutral-500" />
        </button>
        
        {showActions && (
          <div className="absolute right-0 top-8 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg shadow-lg py-1 z-10 min-w-[140px]">
            <button className="w-full px-3 py-2 text-left text-sm hover:bg-neutral-50 dark:hover:bg-neutral-700 flex items-center gap-2">
              <Eye size={14} />
              View Details
            </button>
            <button className="w-full px-3 py-2 text-left text-sm hover:bg-neutral-50 dark:hover:bg-neutral-700 flex items-center gap-2">
              <Settings size={14} />
              Manage
            </button>
            <hr className="my-1 border-neutral-200 dark:border-neutral-700" />
            <button className="w-full px-3 py-2 text-left text-sm hover:bg-neutral-50 dark:hover:bg-neutral-700 text-neutral-600 dark:text-neutral-400 flex items-center gap-2">
              <Trash2 size={14} />
              Remove
            </button>
          </div>
        )}
      </div>
    </div>
  );
}


export default function DevicesPage() {
  // Sidebar navigation links
  const sidebarLinks = [
    {
      label: "Chat",
      href: "/chat",
      icon: <MessageCircle className="text-neutral-200 dark:text-neutral-200 h-7 w-7 flex-shrink-0" />
    },
    {
      label: "Devices",
      href: "/devices",
      icon: <Monitor className="text-neutral-200 dark:text-neutral-200 h-7 w-7 flex-shrink-0" />
    },
    {
      label: "Settings",
      href: "/settings",
      icon: <SettingsIcon className="text-neutral-200 dark:text-neutral-200 h-7 w-7 flex-shrink-0" />
    }
  ];

  return (
    <div className="h-dvh w-dvw text-neutral-900 bg-neutral-900 dark:text-neutral-100 dark:bg-neutral-950">
      <div className="flex h-full">
        {/* Main Sidebar */}
        <Sidebar animate={true}>
          <SidebarBody className="justify-between gap-10">
            <div className="flex flex-col flex-1 overflow-y-auto overflow-x-hidden">
              {/* Skygen Title */}
              <SidebarLink
                link={{
                  label: "Skygen",
                  href: "#",
                  icon: <Wind className="h-6 w-6 text-neutral-200 dark:text-neutral-200 flex-shrink-0" style={{ transform: "scaleX(-1)" }} />
                }}
                className="px-2 py-4 pointer-events-none"
              />
              
              {/* Отступ после названия */}
              <div className="h-6"></div>
              
              {/* Navigation Links */}
              {sidebarLinks.map((link, idx) => (
                <SidebarLink key={idx} link={link} />
              ))}
            </div>
            
            {/* User Profile */}
            <div>
              <SidebarLink
                link={{
                  label: "Egor Andreev",
                  href: "#",
                  icon: (
                    <div className="h-10 w-10 min-h-10 min-w-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-medium text-base flex-shrink-0" style={{ transform: "translateX(-3px)" }}>
                      <span className="leading-none">EA</span>
                    </div>
                  )
                }}
              />
            </div>
          </SidebarBody>
        </Sidebar>

        {/* Main Content */}
        <main className="flex min-w-0 flex-1 flex-col bg-[#F8F8F6] dark:bg-neutral-900">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-6 border-b border-neutral-200 dark:border-neutral-700">
            <div>
              <h1 className="text-3xl font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
                Device Management
              </h1>
              <p className="text-neutral-600 dark:text-neutral-400">
                Manage and monitor your connected devices
              </p>
            </div>
            
            <button className="px-4 py-2 bg-neutral-900 dark:bg-neutral-700 text-white rounded-lg hover:opacity-90 transition-opacity">
              Add Device
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-auto px-6 py-6">
            <div className="mx-auto max-w-5xl">
              {/* Devices List */}
              <div>
                <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
                  Your Devices
                </h2>
                {/* Table Container */}
                <div className="bg-white dark:bg-neutral-800 rounded-xl border border-neutral-200 dark:border-neutral-700 overflow-hidden">
                  {mockDevices.map((device) => (
                    <DeviceRow key={device.id} device={device} />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
