"use client";

import React from "react";
import LightRays from "../../components/LightRays";
import { ArrowRight, Sparkles, Brain, Zap, Target } from "lucide-react";

export default function WelcomePage() {
  const handleGetStarted = () => {
    // Button handler - no redirect
    console.log("Button clicked");
  };

  return (
    <div className="relative h-dvh w-dvw overflow-hidden bg-black">
      {/* LightRays Background */}
      <div className="absolute inset-0">
        <LightRays
          raysOrigin="top-center"
          raysColor="#F9CB99"
          raysSpeed={0.8}
          lightSpread={5}
          rayLength={100}
          pulsating={false}
          fadeDistance={2}
          saturation={0.9}
          followMouse={false}
          mouseInfluence={0}
          noiseAmount={0.05}
          distortion={0}
          className="w-full h-full"
        />
      </div>

      {/* Dark gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/20 via-black/40 to-black/80" />

      {/* Content */}
      <div className="relative z-10 flex h-full flex-col items-center justify-center px-4 text-center">
        <div className="max-w-4xl space-y-8">
          {/* Logo/Brand */}
          <div className="flex items-center justify-center space-x-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-stone-700 to-stone-800">
              <Sparkles className="h-6 w-6 text-stone-200" />
            </div>
            <span className="text-3xl font-bold" style={{color: '#D4C4A8'}}>
              Skygen
            </span>
          </div>

          {/* Main heading */}
          <div className="space-y-4">
            <h2 className="text-4xl font-bold text-white sm:text-5xl lg:text-6xl">
              Welcome to the{" "}
              <span className="inline font-bold text-4xl sm:text-5xl lg:text-6xl" style={{color: '#D4C4A8'}}>
                future
              </span>
            </h2>
            <p className="mx-auto max-w-2xl text-lg text-gray-300 sm:text-xl">
              Next-generation intelligent assistant that understands your
              tasks and helps solve them with incredible efficiency
            </p>
          </div>

          {/* Features */}
          <div className="grid gap-6 sm:grid-cols-3">
            <div className="space-y-2">
              <div className="mx-auto h-12 w-12 rounded-lg bg-stone-800/30 border border-stone-700/40 flex items-center justify-center backdrop-blur-sm">
                <Brain className="h-6 w-6 text-stone-300" />
              </div>
              <h3 className="font-semibold text-stone-200">Smart</h3>
              <p className="text-sm text-stone-400">
                Understands context and suggests solutions
              </p>
            </div>
            <div className="space-y-2">
              <div className="mx-auto h-12 w-12 rounded-lg bg-stone-800/30 border border-stone-700/40 flex items-center justify-center backdrop-blur-sm">
                <Zap className="h-6 w-6 text-stone-300" />
              </div>
              <h3 className="font-semibold text-stone-200">Fast</h3>
              <p className="text-sm text-stone-400">
                Instant answers to your questions
              </p>
            </div>
            <div className="space-y-2">
              <div className="mx-auto h-12 w-12 rounded-lg bg-stone-800/30 border border-stone-700/40 flex items-center justify-center backdrop-blur-sm">
                <Target className="h-6 w-6 text-stone-300" />
              </div>
              <h3 className="font-semibold text-stone-200">Precise</h3>
              <p className="text-sm text-stone-400">
                Executes tasks with high accuracy
              </p>
            </div>
          </div>

          {/* CTA Button */}
          <div className="pt-8">
            <button
              onClick={handleGetStarted}
              className="group inline-flex items-center space-x-3 rounded-full bg-gradient-to-r from-stone-600 to-stone-700 px-8 py-4 text-lg font-semibold text-white shadow-lg transition-all duration-200 hover:scale-105 hover:shadow-xl hover:from-stone-500 hover:to-stone-600"
            >
              <span>Get Started</span>
              <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
            </button>
          </div>

          {/* Subtitle */}
          <p className="text-sm text-stone-500">
            Press ⌘K for quick task creation
          </p>
        </div>
      </div>
    </div>
  );
}
