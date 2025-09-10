"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, ChevronRight, Check, Sparkles, Shield, Zap, Settings } from "lucide-react";

interface OnboardingStep {
  id: number;
  title: string;
  description: string;
  content: string;
  icon: React.ReactNode;
  features?: string[];
}

const onboardingSteps: OnboardingStep[] = [
  {
    id: 1,
    title: "Добро пожаловать в Skygen",
    description: "Ваш умный AI-ассистент",
    content: "Skygen — это современная платформа искусственного интеллекта, которая поможет вам автоматизировать задачи, получать быстрые ответы и повышать продуктивность.",
    icon: <Sparkles className="w-8 h-8" />,
    features: [
      "Интеллектуальные диалоги",
      "Автоматизация задач",
      "Персонализированные рекомендации"
    ]
  },
  {
    id: 2,
    title: "Безопасность и Приватность",
    description: "Ваши данные под защитой",
    content: "Мы серьезно относимся к безопасности ваших данных. Все взаимодействия зашифрованы, а личная информация остается конфиденциальной.",
    icon: <Shield className="w-8 h-8" />,
    features: [
      "Сквозное шифрование",
      "Локальное хранение данных",
      "Соответствие GDPR"
    ]
  },
  {
    id: 3,
    title: "Быстрый Старт",
    description: "Начните использовать прямо сейчас",
    content: "Skygen готов к работе! Вы можете начать общение с AI, настроить персональные предпочтения и изучить доступные функции.",
    icon: <Zap className="w-8 h-8" />,
    features: [
      "Мгновенные ответы",
      "Интуитивный интерфейс",
      "Множество возможностей"
    ]
  },
  {
    id: 4,
    title: "Настройка",
    description: "Персонализируйте под себя",
    content: "Настройте Skygen под свои потребности: выберите тему оформления, языковые предпочтения и другие параметры.",
    icon: <Settings className="w-8 h-8" />,
    features: [
      "Темная/светлая тема",
      "Языковые настройки",
      "Пользовательские команды"
    ]
  }
];

export default function FirstTimePage() {
  const [currentStep, setCurrentStep] = useState(0);
  const router = useRouter();

  const handleNext = () => {
    if (currentStep < onboardingSteps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = () => {
    router.push("/chat");
  };

  const currentStepData = onboardingSteps[currentStep];

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-3xl">
        {/* Custom Stepper */}
        <div className="flex items-center justify-center mb-16">
          <div className="flex items-center space-x-8">
            {onboardingSteps.map((_, index) => (
              <div key={index} className="flex items-center">
                <div
                  className={`
                    w-10 h-10 rounded-full border-2 flex items-center justify-center transition-all duration-300
                    ${index < currentStep 
                      ? "bg-black border-black text-white" 
                      : index === currentStep 
                      ? "bg-white border-black text-black" 
                      : "bg-white border-gray-300 text-gray-300"
                    }
                  `}
                >
                  {index < currentStep ? (
                    <Check className="w-5 h-5" />
                  ) : (
                    <span className="text-sm font-medium">{index + 1}</span>
                  )}
                </div>
                {index < onboardingSteps.length - 1 && (
                  <div 
                    className={`
                      w-16 h-0.5 mx-4 transition-all duration-300
                      ${index < currentStep ? "bg-black" : "bg-gray-300"}
                    `}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Main Card */}
        <div className="bg-white border border-gray-200 rounded-none p-12 mb-12 shadow-sm">
          {/* Icon */}
          <div className="flex justify-center mb-8">
            <div className="p-6 border border-gray-200 rounded-none">
              {currentStepData.icon}
            </div>
          </div>

          {/* Content */}
          <div className="text-center space-y-8">
            <div>
              <h1 className="text-4xl font-bold text-black mb-4">
                {currentStepData.title}
              </h1>
              <p className="text-xl text-gray-600 mb-8">
                {currentStepData.description}
              </p>
            </div>

            <p className="text-gray-800 leading-relaxed text-lg max-w-2xl mx-auto">
              {currentStepData.content}
            </p>

            {/* Features */}
            {currentStepData.features && (
              <div className="mt-12 space-y-4">
                {currentStepData.features.map((feature, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-center space-x-4 text-gray-800"
                  >
                    <div className="w-2 h-2 bg-black rounded-full flex-shrink-0" />
                    <span className="text-lg">{feature}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Navigation Buttons */}
        <div className="flex justify-center space-x-6">
          <button
            onClick={handlePrevious}
            disabled={currentStep === 0}
            className="flex items-center space-x-3 px-8 py-4 border border-gray-300 text-gray-600 hover:border-gray-400 hover:text-gray-800 transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:border-gray-300 disabled:hover:text-gray-600"
          >
            <ChevronLeft className="w-5 h-5" />
            <span className="font-medium">Назад</span>
          </button>

          {currentStep < onboardingSteps.length - 1 ? (
            <button
              onClick={handleNext}
              className="flex items-center space-x-3 px-8 py-4 bg-black text-white hover:bg-gray-800 transition-all duration-200"
            >
              <span className="font-medium">Далее</span>
              <ChevronRight className="w-5 h-5" />
            </button>
          ) : (
            <button
              onClick={handleComplete}
              className="flex items-center space-x-3 px-10 py-4 bg-black text-white hover:bg-gray-800 transition-all duration-200"
            >
              <span className="font-medium">Начать работу</span>
              <ChevronRight className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Simple Progress indicator */}
        <div className="flex justify-center mt-12 space-x-3">
          {onboardingSteps.map((_, index) => (
            <div
              key={index}
              className={`
                h-1 transition-all duration-300
                ${index === currentStep
                  ? "w-8 bg-black"
                  : index < currentStep
                  ? "w-4 bg-black"
                  : "w-4 bg-gray-300"
                }
              `}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
