"use client";

import React, { useState, useEffect, useRef } from "react";
import { Eye, EyeOff, Github, Twitter, Linkedin, Mail, Lock, User, X } from "lucide-react";
import Link from "next/link";
import Squares from "./Squares";
import { swiftBridge } from "@/lib/swift-bridge";

interface FormFieldProps {
  type: string;
  placeholder: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  icon: React.ReactNode;
  showToggle?: boolean;
  onToggle?: () => void;
  showPassword?: boolean;
}

const AnimatedFormField: React.FC<FormFieldProps> = ({
  type,
  placeholder,
  value,
  onChange,
  icon,
  showToggle,
  onToggle,
  showPassword
}) => {
  const [isFocused, setIsFocused] = useState(false);

  return (
    <div className="relative group">
      <div
        className="relative overflow-hidden rounded-lg border border-white/20 bg-white/5 transition-all duration-300 ease-in-out"
      >
        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-white/60 transition-colors duration-200 group-focus-within:text-white">
          {icon}
        </div>
        
        <input
          type={type}
          value={value}
          onChange={onChange}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          className="w-full bg-transparent pl-10 pr-12 py-3 text-white placeholder:text-white/40 focus:outline-none"
          placeholder=""
        />
        
        <label className={`absolute left-10 top-1/2 -translate-y-1/2 text-sm pointer-events-none transition-opacity duration-200 ${
          isFocused || value 
            ? 'opacity-0' 
            : 'opacity-60 text-white'
        }`}>
          {placeholder}
        </label>

        {showToggle && (
          <button
            type="button"
            onClick={onToggle}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-white/60 hover:text-white transition-colors"
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        )}
      </div>
    </div>
  );
};

const SocialButton: React.FC<{ icon: React.ReactNode; name: string; onClick?: () => void }> = ({ icon, name, onClick }) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <button
      className="relative group p-3 rounded-lg border border-white/20 bg-white/5 hover:bg-white/10 transition-all duration-300 ease-in-out overflow-hidden"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onClick}
    >
      <div className={`absolute inset-0 bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-pink-500/20 transition-transform duration-500 ${
        isHovered ? 'translate-x-0' : '-translate-x-full'
      }`} />
      <div className="relative text-white group-hover:text-white transition-colors">
        {icon}
      </div>
    </button>
  );
};



interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onClose }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    console.log('Form submitted:', { email, password, rememberMe });
    setIsSubmitting(false);
    onClose();
    
    // Navigate to /allow page after successful login
    if (swiftBridge.isNativeApp()) {
      swiftBridge.navigateTo('/allow');
    } else {
      // Fallback for web version
      window.location.href = '/allow';
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4"
      onClick={handleBackdropClick}
    >
      <div className="relative w-full max-w-md">
        <div className="bg-black/90 backdrop-blur-xl border border-white/20 rounded-2xl p-8 shadow-2xl relative overflow-hidden">
          <Squares 
            direction="diagonal"
            speed={0.05}
            borderColor="rgba(255, 255, 255, 0.0)"
            squareSize={50}
            hoverFillColor="rgba(255, 255, 255, 0)"
            className=""
          />
          
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-10 p-2 rounded-lg bg-white/10 hover:bg-white/20 border border-white/20 text-white transition-all duration-200"
          >
            <X size={18} />
          </button>

          <div className="text-center mb-8 relative z-10">
            <h1 className="text-3xl font-bold text-white mb-2">
              Welcome Back
            </h1>
            <p className="text-white/60">
              Sign in to continue
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6 relative z-10">
            <AnimatedFormField
              type="email"
              placeholder="Email Address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              icon={<Mail size={18} />}
            />

            <AnimatedFormField
              type={showPassword ? "text" : "password"}
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              icon={<Lock size={18} />}
              showToggle
              onToggle={() => setShowPassword(!showPassword)}
              showPassword={showPassword}
            />

            <div className="flex items-center justify-between">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 text-white bg-white/10 border-white/20 rounded focus:ring-white focus:ring-2"
                />
                <span className="text-sm text-white/60">Remember me</span>
              </label>
              
              <button
                type="button"
                className="text-sm text-white hover:underline"
              >
                Forgot password?
              </button>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full relative group bg-white text-black py-3 px-4 rounded-lg font-medium transition-all duration-300 ease-in-out hover:bg-white/90 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed overflow-hidden"
            >
              <span className={`transition-opacity duration-200 ${isSubmitting ? 'opacity-0' : 'opacity-100'}`}>
                Sign In
              </span>
              
              {isSubmitting && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                </div>
              )}
              
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-black/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000 ease-in-out" />
            </button>
          </form>

          <div className="mt-8 relative z-10">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-white/20" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-black text-white/60">Or continue with</span>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-3 gap-3">
              <SocialButton icon={<Github size={20} />} name="GitHub" onClick={() => window.location.href = '/chat'} />
              <SocialButton icon={<Twitter size={20} />} name="Twitter" onClick={() => window.location.href = '/chat'} />
              <SocialButton icon={<Linkedin size={20} />} name="LinkedIn" onClick={() => window.location.href = '/chat'} />
            </div>
          </div>

          <div className="mt-8 text-center relative z-10">
            <p className="text-sm text-white/60">
              Don&apos;t have an account?{' '}
              <Link
                href="/register"
                className="text-white hover:underline font-medium"
                onClick={onClose}
              >
                Sign up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
