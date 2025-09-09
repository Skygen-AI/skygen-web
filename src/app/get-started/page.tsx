"use client";

import React, { useState } from "react";
import { Monitor, Smartphone, Globe, ArrowLeft, Download, ExternalLink, Apple } from "lucide-react";
import Link from "next/link";

export default function GetStartedPage() {
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);

  const platforms = [
    {
      id: "web",
      title: "Web",
      description: "Run  directly in your browser",
      icon: Globe,
      color: "from-blue-500 to-cyan-500",
      buttons: [{ label: "Launch Web App", icon: ExternalLink }]
    },
    {
      id: "desktop",
      title: "Desktop",
      description: "Download native app for macOS, Windows, Linux",
      icon: Monitor,
      color: "from-purple-500 to-pink-500",
      buttons: [
        { label: "macOS", icon: Apple },
        { label: "Windows", icon: Download },
        { label: "Linux", icon: Download }
      ]
    },
    {
      id: "mobile",
      title: "Mobile",
      description: "Get Skygen on iOS and Android",
      icon: Smartphone,
      color: "from-green-500 to-emerald-500",
      buttons: [
        { label: "App Store", icon: Apple },
        { label: "Google Play", icon: Download }
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-black text-white flex flex-col">
      {/* Header */}
      <header className="p-6">
        <Link 
          href="/" 
          className="inline-flex items-center space-x-2 text-white/70 hover:text-white transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
          <span>Back to Home</span>
        </Link>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-6">
        <div className="max-w-4xl w-full text-center">
          {/* Title */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-4">
            Choose Your Platform
          </h1>
          <p className="text-xl text-white/70 mb-12 max-w-2xl mx-auto">
            Select how you&apos;d like to experience Skygen. Available on all your favorite devices.
          </p>

          {/* Platform Cards */}
          <div className="grid md:grid-cols-3 gap-6 mb-8">
            {platforms.map((platform) => {
              const Icon = platform.icon;
              const isSelected = selectedPlatform === platform.id;
              
              return (
                <div
                  key={platform.id}
                  onClick={() => setSelectedPlatform(platform.id)}
                  className={`
                    relative p-8 rounded-2xl border-2 cursor-pointer transition-all duration-300 hover:scale-105
                    ${isSelected 
                      ? 'border-white bg-white/10 scale-105' 
                      : 'border-white/20 bg-white/5 hover:border-white/40'
                    }
                  `}
                >
                  {/* Gradient Background */}
                  <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${platform.color} opacity-10`} />
                  
                  {/* Content */}
                  <div className="relative z-10">
                    <div className={`inline-flex p-4 rounded-xl bg-gradient-to-br ${platform.color} mb-6`}>
                      <Icon className="h-8 w-8 text-white" />
                    </div>
                    
                    <h3 className="text-2xl font-semibold mb-3">{platform.title}</h3>
                    <p className="text-white/70 mb-6">{platform.description}</p>
                    
                    {isSelected && (
                      <div className="space-y-3">
                        {platform.buttons.map((button, index) => {
                          const ButtonIcon = button.icon;
                          return (
                            <button 
                              key={index}
                              className="w-full inline-flex items-center justify-center space-x-2 bg-white text-black px-6 py-3 rounded-full font-semibold hover:bg-white/90 transition-colors"
                            >
                              <ButtonIcon className="h-4 w-4" />
                              <span>{button.label}</span>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Additional Info */}
          {selectedPlatform && (
            <div className="text-center text-white/60 text-sm">
              <p>All platforms sync your data automatically</p>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="p-6 text-center">
        <p className="text-white/40 text-sm">
          Need help? Contact our support team
        </p>
      </footer>
    </div>
  );
}
