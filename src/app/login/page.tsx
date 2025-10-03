"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { SignInPage } from "../../components/ui/sign-in";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import Squares from "../../components/Squares";
import { swiftBridge } from "@/lib/swift-bridge";
import { authService } from "@/services/authService";

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

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const router = useRouter();
  
  // DEV MODE: Автоматический логин при загрузке страницы
  useEffect(() => {
    const isDev = process.env.NEXT_PUBLIC_DEV_MODE === 'true';
    
    if (isDev) {
      const devEmail = process.env.NEXT_PUBLIC_DEV_USER || 'dev@skygen.local';
      const devPassword = process.env.NEXT_PUBLIC_DEV_PASSWORD || 'dev123';
      
      // Автоматически логиним через 500мс
      const timer = setTimeout(async () => {
        console.log('[DEV MODE] Auto-login enabled');
        try {
          await authService.login(devEmail, devPassword);
          setSuccess('🔧 Dev mode: Auto-logged in!');
          
          setTimeout(() => {
            router.push('/allow');
          }, 1000);
        } catch (err) {
          console.error('[DEV MODE] Auto-login failed:', err);
          // В dev-режиме игнорируем ошибку и продолжаем
        }
      }, 500);
      
      return () => clearTimeout(timer);
    }
  }, [router]);

  const handleSignIn = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccess(null);
    
    const formData = new FormData(e.currentTarget);
    const email = formData.get('email') as string;
    const password = formData.get('password') as string;
    
    try {
      // Авторизуемся через бэкенд API
      const result = await authService.login(email, password);
      
      setSuccess('Login successful! Redirecting...');
      console.log('Login successful, attempting redirect to /allow');
      
      // Небольшая задержка перед редиректом
      setTimeout(() => {
        console.log('Executing redirect to /allow');
        router.push('/allow');
      }, 1000);
      
    } catch (error) {
      console.error('Login error:', error);
      setError(error instanceof Error ? error.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignIn = () => {
    // TODO: Implement Google OAuth
    setError('Google Sign-In not implemented yet');
  };

  const handleResetPassword = () => {
    setError('Password reset not implemented yet');
  };

  const handleCreateAccount = () => {
    if (swiftBridge.isNativeApp()) {
      swiftBridge.navigateTo('/register');
    } else {
      window.location.href = '/register';
    }
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
          title={<span className="font-light text-white tracking-tighter">Welcome Back</span>}
          description={isLoading ? "Signing you in..." : "Sign in to continue your AI journey"}
          heroImageSrc="https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=800&h=1200&fit=crop"
          testimonials={testimonials}
          onSignIn={handleSignIn}
          onGoogleSignIn={handleGoogleSignIn}
          onResetPassword={handleResetPassword}
          onCreateAccount={handleCreateAccount}
          disabled={isLoading}
          isLoginMode={true}
        />
      </div>
    </div>
  );
}
