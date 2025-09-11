"use client";

import React, { useState } from "react";
import { SignInPage } from "../../components/ui/sign-in";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import Squares from "../../components/Squares";
import { swiftBridge } from "@/lib/swift-bridge";
import { AuthService } from "@/services/authService";

const testimonials = [
  {
    avatarSrc: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=face",
    name: "Alex Chen",
    handle: "@alexchen",
    text: "Skygen transformed our workflow completely. The AI capabilities are incredible!"
  },
  {
    avatarSrc: "https://images.unsplash.com/photo-1494790108755-2616b056b2d2?w=100&h=100&fit=crop&crop=face",
    name: "Sarah Kim",
    handle: "@sarahk",
    text: "Best platform I've used for AI automation. Highly recommend!"
  },
  {
    avatarSrc: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop&crop=face",
    name: "Mike Johnson",
    handle: "@mikej",
    text: "The ease of use and powerful features make this a game changer."
  }
];

export default function RegisterPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  const authService = AuthService.getInstance();

  const handleSignIn = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccess(null);
    
    const formData = new FormData(e.currentTarget);
    const email = formData.get('email') as string;
    const password = formData.get('password') as string;
    
    try {
      // Регистрируемся через бэкенд API
      const result = await authService.signupAndLogin(email, password);
      
      setSuccess(`Welcome ${result.user.email}! Registration successful.`);
      
      // Небольшая задержка перед редиректом
      setTimeout(() => {
        if (swiftBridge.isNativeApp()) {
          swiftBridge.navigateTo('/skygen-setup');
        } else {
          window.location.href = '/skygen-setup';
        }
      }, 1500);
      
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignIn = () => {
    // Navigate to /allow page after successful Google registration
    if (swiftBridge.isNativeApp()) {
      swiftBridge.navigateTo('/allow');
    } else {
      // Fallback for web version
      window.location.href = '/allow';
    }
  };

  const handleResetPassword = () => {
    // Reset password functionality placeholder
  };

  const handleCreateAccount = () => {
    // This would typically switch to a different mode or page
  };

  return (
    <div className="min-h-screen bg-black relative overflow-hidden">
      <Squares 
        direction="diagonal"
        speed={0.05}
        borderColor="rgba(255, 255, 255, 0.03)"
        squareSize={60}
        hoverFillColor="rgba(255, 255, 255, 0.02)"
        className=""
      />
      
      {/* Back button */}
      <Link 
        href="/"
        className="absolute top-6 left-6 z-20 p-3 rounded-lg bg-white/10 hover:bg-white/20 border border-white/20 text-white transition-all duration-200 group"
      >
        <ArrowLeft size={20} className="transition-transform group-hover:-translate-x-1" />
      </Link>
      
      <div className="relative z-10">
        {/* Error/Success Messages */}
        {(error || success) && (
          <div className="fixed top-6 right-6 z-50 max-w-md">
            {error && (
              <div className="bg-red-500/90 backdrop-blur-sm text-white p-4 rounded-lg shadow-lg border border-red-400/30">
                <div className="flex items-center space-x-2">
                  <span className="text-red-200">❌</span>
                  <span>{error}</span>
                </div>
              </div>
            )}
            {success && (
              <div className="bg-green-500/90 backdrop-blur-sm text-white p-4 rounded-lg shadow-lg border border-green-400/30">
                <div className="flex items-center space-x-2">
                  <span className="text-green-200">✅</span>
                  <span>{success}</span>
                </div>
              </div>
            )}
          </div>
        )}

        <SignInPage
          title={<span className="font-light text-white tracking-tighter">Join Skygen</span>}
          description={isLoading ? "Creating your account..." : "Create your account and start your AI journey with us"}
          heroImageSrc="https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=800&h=1200&fit=crop"
          testimonials={testimonials}
          onSignIn={handleSignIn}
          onGoogleSignIn={handleGoogleSignIn}
          onResetPassword={handleResetPassword}
          onCreateAccount={handleCreateAccount}
          disabled={isLoading}
        />
      </div>
    </div>
  );
}
