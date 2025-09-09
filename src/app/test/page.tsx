"use client"

import React from "react"

export default function TestPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-200 flex items-center justify-center p-8">
      <div className="flex flex-col items-center space-y-6">
        {/* Прямоугольник с градиентной рамкой */}
        <div className="relative">
          {/* Градиентный фон с анимацией */}
          <div 
            className="w-96 h-32 rounded-2xl shadow-xl"
            style={{
              background: 'linear-gradient(90deg, #ee7752, #e73c7e, #23a6d5, #23d5ab, #ee7752,  #e73c7e, #23a6d5)',
              backgroundSize: '200% 100%',
              animation: 'seamless-flow 2s linear infinite'
            }}
          >
          </div>
          
          {/* Белый полупрозрачный квадрат поверх с текстом */}
          <div 
            className="absolute inset-1 bg-white rounded-xl flex items-center justify-center"
            style={{
              opacity: 0.89
            }}
          >
            <h1 className="text-4xl font-bold text-black-800">Agent mode</h1>
          </div>
        </div>
      </div>
    </div>
  )
}
