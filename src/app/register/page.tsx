"use client";

import React from "react";
import { SignInPage } from "../../components/ui/sign-in";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import Squares from "../../components/Squares";
import { swiftBridge } from "@/lib/swift-bridge";

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
  const handleSignIn = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const email = formData.get('email');
    const password = formData.get('password');
    const rememberMe = formData.get('rememberMe');
    
    console.log('Sign up submitted:', { email, password, rememberMe });
    
    // Navigate to /allow page after successful registration
    if (swiftBridge.isNativeApp()) {
      swiftBridge.navigateTo('/allow');
    } else {
      // Fallback for web version
      window.location.href = '/allow';
    }
  };

  const handleGoogleSignIn = () => {
    console.log('Google sign up clicked');
    
    // Navigate to /allow page after successful Google registration
    if (swiftBridge.isNativeApp()) {
      swiftBridge.navigateTo('/allow');
    } else {
      // Fallback for web version
      window.location.href = '/allow';
    }
  };

  const handleResetPassword = () => {
    console.log('Reset password clicked');
    alert("Reset password functionality");
  };

  const handleCreateAccount = () => {
    console.log('Create account clicked');
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
        <SignInPage
          title={<span className="font-light text-white tracking-tighter">Join Skygen</span>}
          description="Create your account and start your AI journey with us"
          heroImageSrc="https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=800&h=1200&fit=crop"
          testimonials={testimonials}
          onSignIn={handleSignIn}
          onGoogleSignIn={handleGoogleSignIn}
          onResetPassword={handleResetPassword}
          onCreateAccount={handleCreateAccount}
        />
      </div>
    </div>
  );
}
