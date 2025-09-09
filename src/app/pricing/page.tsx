"use client";

import React from "react";
import { PricingSection } from "../../components/ui/pricing";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

const pricingPlans = [
  {
    name: "Starter",
    info: "Perfect for individuals getting started with AI",
    price: {
      monthly: 0,
      yearly: 0,
    },
    features: [
      { text: "5 AI agents per month" },
      { text: "Basic automation templates" },
      { text: "Email support" },
      { text: "Community access" },
      { text: "Standard integrations" },
    ],
    btn: {
      text: "Get Started",
      href: "/register",
    },
  },
  {
    name: "Professional",
    info: "Ideal for growing teams and businesses",
    price: {
      monthly: 29,
      yearly: 290,
    },
    features: [
      { text: "Unlimited AI agents" },
      { text: "Advanced automation workflows", tooltip: "Create complex multi-step automations" },
      { text: "Priority support" },
      { text: "Custom integrations" },
      { text: "Analytics dashboard" },
      { text: "Team collaboration tools" },
      { text: "API access" },
    ],
    btn: {
      text: "Start Free Trial",
      href: "/register",
    },
    highlighted: true,
  },
  {
    name: "Enterprise",
    info: "For large organizations with custom needs",
    price: {
      monthly: 99,
      yearly: 990,
    },
    features: [
      { text: "Everything in Professional" },
      { text: "Dedicated account manager" },
      { text: "Custom AI model training" },
      { text: "On-premise deployment" },
      { text: "Advanced security features" },
      { text: "24/7 phone support" },
      { text: "SLA guarantees" },
      { text: "White-label solutions" },
    ],
    btn: {
      text: "Contact Sales",
      href: "/contact",
    },
  },
];

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-black relative overflow-hidden">
      {/* Back button */}
      <Link 
        href="/"
        className="absolute top-6 left-6 z-20 p-3 rounded-lg bg-white/10 hover:bg-white/20 border border-white/20 text-white transition-all duration-200 group"
      >
        <ArrowLeft size={20} className="transition-transform group-hover:-translate-x-1" />
      </Link>
      
      <div className="relative z-10 min-h-screen py-32">
        <div className="container mx-auto px-8">
          <PricingSection
            heading="Choose Your Skygen Plan"
            description="Scale your AI automation with flexible pricing that grows with your business"
            plans={pricingPlans}
            className="text-white"
          />
        </div>
      </div>
    </div>
  );
}
