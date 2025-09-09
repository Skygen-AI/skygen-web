"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  CheckCircle2,
  Circle,
  CircleAlert,
  CircleDotDashed,
  CircleX,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

// Type definitions
interface Subtask {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in-progress' | 'completed' | 'need-help' | 'failed';
  priority: 'high' | 'medium' | 'low';
  tools?: string[]; // Optional array of MCP server tools
}

interface Task {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in-progress' | 'completed' | 'need-help' | 'failed';
  priority: 'high' | 'medium' | 'low';
  level: number;
  dependencies: string[];
  subtasks: Subtask[];
}

interface PlanProps {
  tasks?: Task[];
  executionSpeed?: number; // Скорость выполнения (в миллисекундах)
}

// Initial task data
const initialTasks: Task[] = [
  {
    id: "1",
    title: "Research Project Requirements",
    description:
      "Gather all necessary information about project scope and requirements",
    status: "in-progress",
    priority: "high",
    level: 0,
    dependencies: [],
    subtasks: [
      {
        id: "1.1",
        title: "Interview stakeholders",
        description:
          "Conduct interviews with key stakeholders to understand needs",
        status: "completed",
        priority: "high",
        tools: ["communication-agent", "meeting-scheduler"],
      },
      {
        id: "1.2",
        title: "Review existing documentation",
        description:
          "Go through all available documentation and extract requirements",
        status: "in-progress",
        priority: "medium",
        tools: ["file-system", "browser"],
      },
      {
        id: "1.3",
        title: "Compile findings report",
        description:
          "Create a comprehensive report of all gathered information",
        status: "need-help",
        priority: "medium",
        tools: ["file-system", "markdown-processor"],
      },
    ],
  },
  {
    id: "2",
    title: "Design System Architecture",
    description: "Create the overall system architecture based on requirements",
    status: "in-progress",
    priority: "high",
    level: 0,
    dependencies: [],
    subtasks: [
      {
        id: "2.1",
        title: "Define component structure",
        description: "Map out all required components and their interactions",
        status: "pending",
        priority: "high",
        tools: ["architecture-planner", "diagramming-tool"],
      },
      {
        id: "2.2",
        title: "Create data flow diagrams",
        description:
          "Design diagrams showing how data will flow through the system",
        status: "pending",
        priority: "medium",
        tools: ["diagramming-tool", "file-system"],
      },
      {
        id: "2.3",
        title: "Document API specifications",
        description: "Write detailed specifications for all APIs in the system",
        status: "pending",
        priority: "high",
        tools: ["api-designer", "openapi-generator"],
      },
    ],
  },
  {
    id: "3",
    title: "Implementation Planning",
    description: "Create a detailed plan for implementing the system",
    status: "pending",
    priority: "medium",
    level: 1,
    dependencies: ["1", "2"],
    subtasks: [
      {
        id: "3.1",
        title: "Resource allocation",
        description: "Determine required resources and allocate them to tasks",
        status: "pending",
        priority: "medium",
        tools: ["project-manager", "resource-calculator"],
      },
      {
        id: "3.2",
        title: "Timeline development",
        description: "Create a timeline with milestones and deadlines",
        status: "pending",
        priority: "high",
        tools: ["timeline-generator", "gantt-chart-creator"],
      },
      {
        id: "3.3",
        title: "Risk assessment",
        description:
          "Identify potential risks and develop mitigation strategies",
        status: "pending",
        priority: "medium",
        tools: ["risk-analyzer"],
      },
    ],
  },
  {
    id: "4",
    title: "Development Environment Setup",
    description: "Set up all necessary tools and environments for development",
    status: "in-progress",
    priority: "high",
    level: 0,
    dependencies: [],
    subtasks: [
      {
        id: "4.1",
        title: "Install development tools",
        description:
          "Set up IDEs, version control, and other necessary development tools",
        status: "pending",
        priority: "high",
        tools: ["shell", "package-manager"],
      },
      {
        id: "4.2",
        title: "Configure CI/CD pipeline",
        description: "Set up continuous integration and deployment pipelines",
        status: "pending",
        priority: "medium",
        tools: ["github-actions", "gitlab-ci", "jenkins-connector"],
      },
      {
        id: "4.3",
        title: "Set up testing framework",
        description: "Configure automated testing frameworks for the project",
        status: "pending",
        priority: "high",
        tools: ["test-runner", "shell"],
      },
    ],
  },
  {
    id: "5",
    title: "Initial Development Sprint",
    description: "Execute the first development sprint based on the plan",
    status: "pending",
    priority: "medium",
    level: 1,
    dependencies: ["4"],
    subtasks: [
      {
        id: "5.1",
        title: "Implement core features",
        description:
          "Develop the essential features identified in the requirements",
        status: "pending",
        priority: "high",
        tools: ["code-assistant", "github", "file-system", "shell"],
      },
      {
        id: "5.2",
        title: "Perform unit testing",
        description: "Create and execute unit tests for implemented features",
        status: "pending",
        priority: "medium",
        tools: ["test-runner", "code-coverage-analyzer"],
      },
      {
        id: "5.3",
        title: "Document code",
        description: "Create documentation for the implemented code",
        status: "pending",
        priority: "low",
        tools: ["documentation-generator", "markdown-processor"],
      },
    ],
  },
];

export default function Plan({ 
  tasks: initialTasksProp, 
  executionSpeed = 2000 
}: PlanProps) {
  const [tasks, setTasks] = useState<Task[]>(initialTasksProp || initialTasks);
  const [expandedTasks, setExpandedTasks] = useState<string[]>(
    initialTasksProp && initialTasksProp.length > 0 ? [initialTasksProp[0].id] : ["1"]
  );
  const [expandedSubtasks, setExpandedSubtasks] = useState<{
    [key: string]: boolean;
  }>({});

  const [executionQueue, setExecutionQueue] = useState<Array<{
    taskId: string;
    subtaskId?: string;
    action: 'start' | 'complete' | 'fail' | 'need-help';
    delay: number;
  }>>([]);

  // Add support for reduced motion preference
  const prefersReducedMotion = 
    typeof window !== 'undefined' 
      ? window.matchMedia('(prefers-reduced-motion: reduce)').matches 
      : false;

  // Генерация очереди выполнения с учетом зависимостей
  const generateExecutionQueue = useCallback((taskList: Task[]) => {
    const queue: Array<{
      taskId: string;
      subtaskId?: string;
      action: 'start' | 'complete' | 'fail' | 'need-help';
      delay: number;
    }> = [];

    let currentDelay = 1000; // Начальная задержка

    taskList.forEach((task, taskIndex) => {
      // Добавляем задачи в очередь с учетом зависимостей
      const dependencyDelay = task.dependencies.length * 2000;
      
      // Запуск задачи
      queue.push({
        taskId: task.id,
        action: 'start',
        delay: currentDelay + dependencyDelay
      });

      // Подзадачи выполняются параллельно
      task.subtasks.forEach((subtask, subtaskIndex) => {
        const randomDelay = Math.random() * 3000 + 1000; // 1-4 секунды
        
        // Запуск подзадачи
        queue.push({
          taskId: task.id,
          subtaskId: subtask.id,
          action: 'start',
          delay: currentDelay + dependencyDelay + 500 + (subtaskIndex * 200)
        });

        // Завершение подзадачи (случайное)
        const completionActions: Array<'complete' | 'fail' | 'need-help'> = ['complete', 'complete', 'complete', 'need-help', 'fail'];
        const randomAction = completionActions[Math.floor(Math.random() * completionActions.length)];
        
        queue.push({
          taskId: task.id,
          subtaskId: subtask.id,
          action: randomAction,
          delay: currentDelay + dependencyDelay + randomDelay + 2000
        });
      });

      // Завершение основной задачи
      const taskCompletionDelay = Math.max(...task.subtasks.map(() => Math.random() * 4000 + 3000));
      queue.push({
        taskId: task.id,
        action: Math.random() > 0.8 ? 'need-help' : 'complete',
        delay: currentDelay + dependencyDelay + taskCompletionDelay
      });

      currentDelay += 6000; // Интервал между началом задач
    });

    setExecutionQueue(queue.sort((a, b) => a.delay - b.delay));
  }, []);

  // Инициализация при монтировании компонента
  React.useEffect(() => {
    const tasksToUse = initialTasksProp || initialTasks;
    
    // Устанавливаем задачи
    if (initialTasksProp) {
      setTasks(initialTasksProp);
    }
    
    // Автоматически разворачиваем первую задачу
    if (tasksToUse.length > 0) {
      setExpandedTasks([tasksToUse[0].id]);
    }
    
    // Генерируем очередь выполнения
    generateExecutionQueue(tasksToUse);
  }, []); // Выполняется только при монтировании

  // Отслеживаем завершённые задачи для автоматического скрытия
  const [completedTasksTracker, setCompletedTasksTracker] = React.useState<Set<string>>(new Set());
  const [closingTasks, setClosingTasks] = React.useState<Set<string>>(new Set());

  React.useEffect(() => {
    const currentCompleted = new Set(tasks.filter(task => task.status === 'completed').map(task => task.id));
    const newlyCompleted = [...currentCompleted].filter(id => !completedTasksTracker.has(id));
    
    if (newlyCompleted.length > 0) {
      // Через 5 секунд после завершения скрываем раздел
      const timeouts = newlyCompleted.map(taskId => {
        // Через 3 секунды показываем индикацию закрытия
        const warningTimeout = setTimeout(() => {
          setClosingTasks(prev => new Set([...prev, taskId]));
        }, 3000);

        // Через 5 секунд закрываем раздел
        const closeTimeout = setTimeout(() => {
          setExpandedTasks(prev => prev.filter(id => id !== taskId));
          setClosingTasks(prev => {
            const newSet = new Set(prev);
            newSet.delete(taskId);
            return newSet;
          });
        }, 5000);

        return [warningTimeout, closeTimeout];
      }).flat();

      // Обновляем трекер
      setCompletedTasksTracker(currentCompleted);

      return () => {
        timeouts.forEach(timeout => clearTimeout(timeout));
      };
    }
  }, [tasks, completedTasksTracker]);

  // Автоматическое выполнение плана
  useEffect(() => {
    if (executionQueue.length === 0) return;

    const processQueue = () => {
      if (executionQueue.length === 0) return;

      const nextItem = executionQueue[0];
      const timeout = setTimeout(() => {
        executeAction(nextItem);
        setExecutionQueue(prev => prev.slice(1));
      }, nextItem.delay);

      return () => clearTimeout(timeout);
    };

    return processQueue();
  }, [executionQueue]);

  // Выполнение действия
  const executeAction = useCallback((item: typeof executionQueue[0]) => {
    setTasks(prev => prev.map(task => {
      if (task.id !== item.taskId) return task;

      if (item.subtaskId) {
        // Обновляем подзадачу
        return {
          ...task,
          subtasks: task.subtasks.map(subtask => {
            if (subtask.id !== item.subtaskId) return subtask;
            
            // Не изменяем статус если задача уже завершена, провалена или требует помощи
            if (subtask.status === 'completed' || subtask.status === 'failed') {
              return subtask;
            }
            
            const newStatus = item.action === 'start' ? 'in-progress' : 
                             item.action === 'complete' ? 'completed' :
                             item.action === 'fail' ? 'failed' :
                             'need-help';
            
            return { ...subtask, status: newStatus as any };
          })
        };
      } else {
        // Обновляем основную задачу
        // Не изменяем статус если задача уже завершена, провалена или требует помощи
        if (task.status === 'completed' || task.status === 'failed') {
          return task;
        }
        
        const newStatus = item.action === 'start' ? 'in-progress' : 
                         item.action === 'complete' ? 'completed' :
                         item.action === 'fail' ? 'failed' :
                         'need-help';
        
        return { ...task, status: newStatus as any };
      }
    }));

    // Автоматически разворачиваем активные задачи
    if (item.action === 'start' && !item.subtaskId) {
      setExpandedTasks(prev => [...new Set([...prev, item.taskId])]);
    }
  }, []);

  // Toggle task expansion
  const toggleTaskExpansion = (taskId: string) => {
    setExpandedTasks((prev) =>
      prev.includes(taskId)
        ? prev.filter((id) => id !== taskId)
        : [...prev, taskId],
    );
  };

  // Toggle subtask expansion
  const toggleSubtaskExpansion = (taskId: string, subtaskId: string) => {
    const key = `${taskId}-${subtaskId}`;
    setExpandedSubtasks((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  // Toggle task status
  const toggleTaskStatus = (taskId: string) => {
    setTasks((prev) =>
      prev.map((task) => {
        if (task.id === taskId) {
          // Toggle the status
          const statuses: Array<"completed" | "in-progress" | "pending" | "need-help" | "failed"> = ["completed", "in-progress", "pending", "need-help", "failed"];
          const currentIndex = Math.floor(Math.random() * statuses.length);
          const newStatus = statuses[currentIndex];

          // If task is now completed, mark all subtasks as completed
          const updatedSubtasks = task.subtasks.map((subtask) => ({
            ...subtask,
            status: newStatus === "completed" ? "completed" : subtask.status,
          }));

          return {
            ...task,
            status: newStatus,
            subtasks: updatedSubtasks,
          };
        }
        return task;
      }),
    );
  };

  // Toggle subtask status
  const toggleSubtaskStatus = (taskId: string, subtaskId: string) => {
    setTasks((prev) =>
      prev.map((task) => {
        if (task.id === taskId) {
          const updatedSubtasks = task.subtasks.map((subtask) => {
            if (subtask.id === subtaskId) {
              const newStatus: "pending" | "in-progress" | "completed" | "need-help" | "failed" =
                subtask.status === "completed" ? "pending" : "completed";
              return { ...subtask, status: newStatus };
            }
            return subtask;
          });

          // Calculate if task should be auto-completed when all subtasks are done
          const allSubtasksCompleted = updatedSubtasks.every(
            (s) => s.status === "completed",
          );

          return {
            ...task,
            subtasks: updatedSubtasks,
            status: allSubtasksCompleted ? "completed" : task.status,
          };
        }
        return task;
      }),
    );
  };

  // Animation variants with reduced motion support
  const taskVariants = {
    hidden: { 
      opacity: 0, 
      y: prefersReducedMotion ? 0 : -5 
    },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { 
        type: (prefersReducedMotion ? "tween" : "spring") as "tween" | "spring", 
        stiffness: 500, 
        damping: 30,
        duration: prefersReducedMotion ? 0.2 : undefined
      }
    },
    exit: {
      opacity: 0,
      y: prefersReducedMotion ? 0 : -5,
      transition: { duration: 0.15 }
    }
  };

  const subtaskListVariants = {
    hidden: { 
      opacity: 0, 
      height: 0,
      overflow: "hidden" 
    },
    visible: { 
      height: "auto", 
      opacity: 1,
      overflow: "visible",
      transition: { 
        duration: 0.25, 
        staggerChildren: prefersReducedMotion ? 0 : 0.05,
        when: "beforeChildren",
        ease: [0.2, 0.65, 0.3, 0.9] as [number, number, number, number] // Custom easing curve for Apple-like feel
      }
    },
    exit: {
      height: 0,
      opacity: 0,
      overflow: "hidden",
      transition: { 
        duration: 0.2,
        ease: [0.2, 0.65, 0.3, 0.9] as [number, number, number, number]
      }
    }
  };

  const subtaskVariants = {
    hidden: { 
      opacity: 0, 
      x: prefersReducedMotion ? 0 : -10 
    },
    visible: { 
      opacity: 1, 
      x: 0,
      transition: { 
        type: (prefersReducedMotion ? "tween" : "spring") as "tween" | "spring", 
        stiffness: 500, 
        damping: 25,
        duration: prefersReducedMotion ? 0.2 : undefined
      }
    },
    exit: {
      opacity: 0,
      x: prefersReducedMotion ? 0 : -10,
      transition: { duration: 0.15 }
    }
  };

  const subtaskDetailsVariants = {
    hidden: { 
      opacity: 0, 
      height: 0,
      overflow: "hidden"
    },
    visible: { 
      opacity: 1, 
      height: "auto",
      overflow: "visible",
      transition: { 
        duration: 0.25,
        ease: [0.2, 0.65, 0.3, 0.9] as [number, number, number, number]
      }
    }
  };

  // Status badge animation variants
  const statusBadgeVariants = {
    initial: { scale: 1 },
    animate: { 
      scale: prefersReducedMotion ? 1 : [1, 1.08, 1],
      transition: { 
        duration: 0.35,
        ease: [0.34, 1.56, 0.64, 1] as [number, number, number, number] // Springy custom easing for bounce effect
      }
    }
  };

  return (
    <div className="w-full max-w-full">
      <motion.div 
        className="bg-neutral-50 border-neutral-200 rounded-lg border overflow-hidden w-full max-h-[500px] sm:max-h-[600px] md:max-h-[700px]"
        initial={{ opacity: 0, y: 10 }}
        animate={{ 
          opacity: 1, 
          y: 0,
          transition: {
            duration: 0.3,
            ease: [0.2, 0.65, 0.3, 0.9]
          }
        }}
      >
        <div className="p-3 overflow-y-auto max-h-full">
          <ul className="space-y-1">
              {tasks.map((task, index) => {
                const isExpanded = expandedTasks.includes(task.id);
                const isCompleted = task.status === "completed";
                const isClosing = closingTasks.has(task.id);

                return (
                  <motion.li
                    key={task.id}
                    className={` ${index !== 0 ? "mt-1 pt-2" : ""} `}
                    initial="hidden"
                    animate="visible"
                    variants={taskVariants}
                  >
                    {/* Task row */}
                    <motion.div 
                      className={`group flex items-center px-2 sm:px-3 py-1.5 rounded-md transition-colors ${
                        task.status === 'in-progress' 
                          ? 'bg-blue-50 border border-blue-200' 
                          : task.status === 'need-help'
                          ? 'bg-yellow-50 border border-yellow-200'
                          : isClosing
                          ? 'bg-gray-100 border border-gray-300'
                          : ''
                      }`}
                      whileHover={{ 
                        backgroundColor: task.status === 'in-progress' 
                          ? "rgba(59, 130, 246, 0.1)" 
                          : "rgba(0,0,0,0.03)",
                        transition: { duration: 0.2 }
                      }}
                      animate={{
                        boxShadow: task.status === 'in-progress' 
                          ? ["0 0 0 0 rgba(59, 130, 246, 0)", "0 0 0 4px rgba(59, 130, 246, 0.1)", "0 0 0 0 rgba(59, 130, 246, 0)"]
                          : "0 0 0 0 rgba(0,0,0,0)",
                        opacity: isClosing ? [1, 0.5, 1] : 1
                      }}
                      transition={{
                        boxShadow: {
                          duration: 2,
                          repeat: task.status === 'in-progress' ? Infinity : 0,
                          ease: "easeInOut"
                        },
                        opacity: {
                          duration: 0.8,
                          repeat: isClosing ? Infinity : 0,
                          ease: "easeInOut"
                        }
                      }}
                    >
                      <motion.div
                        className="mr-2 flex-shrink-0 cursor-pointer"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleTaskStatus(task.id);
                        }}
                        whileTap={{ scale: 0.9 }}
                        whileHover={{ scale: 1.1 }}
                      >
                        <AnimatePresence mode="wait">
                          <motion.div
                            key={task.status}
                            initial={{ opacity: 0, scale: 0.8, rotate: -10 }}
                            animate={{ opacity: 1, scale: 1, rotate: 0 }}
                            exit={{ opacity: 0, scale: 0.8, rotate: 10 }}
                            transition={{
                              duration: 0.2,
                              ease: [0.2, 0.65, 0.3, 0.9]
                            }}
                          >
                            {task.status === "completed" ? (
                              <CheckCircle2 className="h-4.5 w-4.5 text-green-500" />
                            ) : task.status === "in-progress" ? (
                              <motion.div
                                animate={{ 
                                  scale: [1, 1.1, 1],
                                  rotate: [0, 180, 360]
                                }}
                                transition={{ 
                                  duration: 2,
                                  repeat: Infinity,
                                  ease: "easeInOut"
                                }}
                              >
                                <CircleDotDashed className="h-4.5 w-4.5 text-blue-500" />
                              </motion.div>
                            ) : task.status === "need-help" ? (
                              <motion.div
                                animate={{ 
                                  x: [-2, 2, -2, 2, 0],
                                  scale: [1, 1.05, 1]
                                }}
                                transition={{ 
                                  duration: 0.5,
                                  repeat: Infinity,
                                  repeatDelay: 2
                                }}
                              >
                                <CircleAlert className="h-4.5 w-4.5 text-yellow-500" />
                              </motion.div>
                            ) : task.status === "failed" ? (
                              <CircleX className="h-4.5 w-4.5 text-red-500" />
                            ) : (
                              <Circle className="text-neutral-500 h-4.5 w-4.5" />
                            )}
                          </motion.div>
                        </AnimatePresence>
                      </motion.div>

                      <motion.div
                        className="flex min-w-0 flex-grow cursor-pointer items-center justify-between"
                        onClick={() => toggleTaskExpansion(task.id)}
                      >
                        <div className="mr-2 flex-1 truncate">
                          <span
                            className={`${isCompleted ? "text-neutral-500 line-through" : ""}`}
                          >
                            {task.title}
                          </span>
                        </div>

                        <div className="flex flex-shrink-0 items-center space-x-1 sm:space-x-2 text-xs">
                          {task.dependencies.length > 0 && (
                            <div className="flex items-center mr-1 sm:mr-2">
                              <div className="flex flex-wrap gap-0.5 sm:gap-1">
                                {task.dependencies.map((dep, idx) => (
                                  <motion.span
                                    key={idx}
                                    className="bg-neutral-100 text-neutral-700 rounded px-1.5 py-0.5 text-[10px] font-medium shadow-sm"
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{
                                      duration: 0.2,
                                      delay: idx * 0.05
                                    }}
                                    whileHover={{ 
                                      y: -1, 
                                      backgroundColor: "rgba(0,0,0,0.1)",
                                      transition: { duration: 0.2 } 
                                    }}
                                  >
                                    {dep}
                                  </motion.span>
                                ))}
                              </div>
                            </div>
                          )}

                          <motion.span
                            className={`rounded px-1.5 py-0.5 ${
                              task.status === "completed"
                                ? "bg-green-100 text-green-700"
                                : task.status === "in-progress"
                                  ? "bg-blue-100 text-blue-700"
                                  : task.status === "need-help"
                                    ? "bg-yellow-100 text-yellow-700"
                                    : task.status === "failed"
                                      ? "bg-red-100 text-red-700"
                                      : "bg-neutral-100 text-neutral-500"
                            }`}
                            variants={statusBadgeVariants}
                            initial="initial"
                            animate="animate"
                            key={task.status} // Force animation on status change
                          >
                            {task.status}
                          </motion.span>
                        </div>
                      </motion.div>
                    </motion.div>

                    {/* Subtasks - staggered */}
                    <AnimatePresence mode="wait">
                      {isExpanded && task.subtasks.length > 0 && (
                        <motion.div 
                          className="relative overflow-hidden"
                          variants={subtaskListVariants}
                          initial="hidden"
                          animate="visible"
                          exit="hidden"
                        >
                          {/* Vertical connecting line aligned with task icon */}
                          <div className="absolute top-0 bottom-0 left-[20px] border-l-2 border-dashed border-neutral-300" />
                          <ul className="border-neutral-200 mt-1 mr-2 mb-1.5 ml-3 space-y-0.5">
                            {task.subtasks.map((subtask) => {
                              const subtaskKey = `${task.id}-${subtask.id}`;
                              const isSubtaskExpanded = expandedSubtasks[subtaskKey];

                              return (
                                <motion.li
                                  key={subtask.id}
                                  className="group flex flex-col py-0.5 pl-6"
                                  onClick={() =>
                                    toggleSubtaskExpansion(task.id, subtask.id)
                                  }
                                  variants={subtaskVariants}
                                  initial="hidden"
                                  animate="visible"
                                  exit="exit"
                                >
                                  <motion.div 
                                    className="flex flex-1 items-center rounded-md p-1"
                                    whileHover={{ 
                                      backgroundColor: "rgba(0,0,0,0.03)",
                                      transition: { duration: 0.2 }
                                    }}
                                  >
                                    <motion.div
                                      className="mr-2 flex-shrink-0 cursor-pointer"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        toggleSubtaskStatus(task.id, subtask.id);
                                      }}
                                      whileTap={{ scale: 0.9 }}
                                      whileHover={{ scale: 1.1 }}
                                    >
                                      <AnimatePresence mode="wait">
                                        <motion.div
                                          key={subtask.status}
                                          initial={{ opacity: 0, scale: 0.8, rotate: -10 }}
                                          animate={{ opacity: 1, scale: 1, rotate: 0 }}
                                          exit={{ opacity: 0, scale: 0.8, rotate: 10 }}
                                          transition={{
                                            duration: 0.2,
                                            ease: [0.2, 0.65, 0.3, 0.9]
                                          }}
                                        >
                                          {subtask.status === "completed" ? (
                                            <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                                          ) : subtask.status === "in-progress" ? (
                                            <motion.div
                                              animate={{ 
                                                scale: [1, 1.1, 1],
                                                rotate: [0, 180, 360]
                                              }}
                                              transition={{ 
                                                duration: 1.5,
                                                repeat: Infinity,
                                                ease: "easeInOut"
                                              }}
                                            >
                                              <CircleDotDashed className="h-3.5 w-3.5 text-blue-500" />
                                            </motion.div>
                                          ) : subtask.status === "need-help" ? (
                                            <motion.div
                                              animate={{ 
                                                x: [-1, 1, -1, 1, 0],
                                                scale: [1, 1.05, 1]
                                              }}
                                              transition={{ 
                                                duration: 0.4,
                                                repeat: Infinity,
                                                repeatDelay: 2
                                              }}
                                            >
                                              <CircleAlert className="h-3.5 w-3.5 text-yellow-500" />
                                            </motion.div>
                                          ) : subtask.status === "failed" ? (
                                            <CircleX className="h-3.5 w-3.5 text-red-500" />
                                          ) : (
                                            <Circle className="text-neutral-500 h-3.5 w-3.5" />
                                          )}
                                        </motion.div>
                                      </AnimatePresence>
                                    </motion.div>

                                    <span
                                      className={`cursor-pointer text-sm ${subtask.status === "completed" ? "text-neutral-500 line-through" : ""}`}
                                    >
                                      {subtask.title}
                                    </span>
                                  </motion.div>

                                  <AnimatePresence mode="wait">
                                    {isSubtaskExpanded && (
                                      <motion.div 
                                        className="text-neutral-500 border-neutral-300 mt-1 ml-1.5 border-l border-dashed pl-5 text-xs overflow-hidden"
                                        variants={subtaskDetailsVariants}
                                        initial="hidden"
                                        animate="visible"
                                        exit="hidden"
                                      >
                                        <p className="py-1">{subtask.description}</p>
                                        {subtask.tools && subtask.tools.length > 0 && (
                                          <div className="mt-0.5 mb-1 flex flex-wrap items-center gap-1.5">
                                            <span className="text-neutral-500 font-medium">
                                              MCP Servers:
                                            </span>
                                            <div className="flex flex-wrap gap-1">
                                              {subtask.tools.map((tool, idx) => (
                                                <motion.span
                                                  key={idx}
                                                  className="bg-neutral-100 text-neutral-700 rounded px-1.5 py-0.5 text-[10px] font-medium shadow-sm"
                                                  initial={{ opacity: 0, y: -5 }}
                                                  animate={{ 
                                                    opacity: 1, 
                                                    y: 0,
                                                    transition: {
                                                      duration: 0.2,
                                                      delay: idx * 0.05
                                                    }
                                                  }}
                                                  whileHover={{ 
                                                    y: -1, 
                                                    backgroundColor: "rgba(0,0,0,0.1)",
                                                    transition: { duration: 0.2 } 
                                                  }}
                                                >
                                                  {tool}
                                                </motion.span>
                                              ))}
                                            </div>
                                          </div>
                                        )}
                                      </motion.div>
                                    )}
                                  </AnimatePresence>
                                </motion.li>
                              );
                            })}
                          </ul>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.li>
                );
              })}
            </ul>
          </div>
      </motion.div>
    </div>
  );
}
