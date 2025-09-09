"use client";

import React from "react";
import { motion } from "framer-motion";
import Plan from "./Plan";
import { ParsedTool, parsePlanData } from "@/utils/toolParser";

interface ToolRendererProps {
  tools: ParsedTool[];
  isTypingComplete: boolean;
}

export function ToolRenderer({ tools, isTypingComplete }: ToolRendererProps) {
  if (!isTypingComplete || tools.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 space-y-3">
      {tools.map((tool, index) => (
        <motion.div
          key={`${tool.name}-${index}`}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ 
            duration: 0.3, 
            delay: 0.2 + (index * 0.1),
            ease: "easeOut"
          }}
        >
          {renderTool(tool)}
        </motion.div>
      ))}
    </div>
  );
}

function renderTool(tool: ParsedTool): React.ReactNode {
  const toolName = tool.name.toLowerCase().trim();
  
  switch (toolName) {
    case 'plan':
    case 'planning':
    case 'planner':
    case 'task':
    case 'tasks':
      return renderPlanTool(tool);
    
    default:
      // Для неизвестных инструментов показываем заглушку
      return (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="text-sm font-medium text-yellow-800 mb-1">
            Неизвестный инструмент: {tool.name}
          </div>
          <pre className="text-xs text-yellow-700 overflow-auto">
            {tool.content}
          </pre>
        </div>
      );
  }
}

function renderPlanTool(tool: ParsedTool): React.ReactNode {
  const planData = parsePlanData(tool.content);
  
  if (!planData) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <div className="text-sm font-medium text-red-800 mb-1">
          Ошибка парсинга плана
        </div>
        <div className="text-xs text-red-700">
          Не удалось распарсить данные плана. Проверьте формат.
        </div>
      </div>
    );
  }

  return <Plan tasks={planData.tasks} />;
}
