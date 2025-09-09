"use client";

import React from "react";
import {
  Stepper,
  StepperIndicator,
  StepperItem,
  StepperTitle,
  StepperTrigger,
} from "../../components/ui/stepper";

const steps = [
  {
    step: 1,
    title: "System",
  },
  {
    step: 2,
    title: "Files", 
  },
  {
    step: 3,
    title: "Security",
  },
];

export default function DependenciesPage() {
  const handleGoToChat = () => {
    window.location.href = '/chat';
  };

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center p-8">
      <div className="text-center">
        <p className="text-gray-800 text-lg mb-8">
          Here are going to be dependencies at some point...
        </p>
        
        {/* Stepper Component */}
        <div className="mx-auto max-w-xl space-y-8 text-center min-w-[400px] mb-8">
          <Stepper defaultValue={2} className="items-start gap-4">
            {steps.map(({ step, title }) => (
              <StepperItem key={step} step={step} className="flex-1">
                <StepperTrigger className="w-full flex-col items-start gap-2 text-center">
                  <StepperIndicator asChild className="h-1 w-full bg-border">
                    <span className="sr-only">{step}</span>
                  </StepperIndicator>
                  <div className="space-y-0.5">
                    <StepperTitle>{title}</StepperTitle>
                  </div>
                </StepperTrigger>
              </StepperItem>
            ))}
          </Stepper>
        </div>
        
        <button
          onClick={handleGoToChat}
          className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg transition-colors"
        >
          Go to Chat
        </button>
      </div>
    </div>
  );
}

