// Типы для инструментов
export interface ParsedTool {
  name: string;
  content: string;
  startIndex: number;
  endIndex: number;
}

export interface ParsedMessage {
  textContent: string;  // Основной текст без инструментов
  tools: ParsedTool[];  // Найденные инструменты
}

// Парсер инструментов из текста сообщения
export function parseToolsFromMessage(message: string): ParsedMessage {
  const tools: ParsedTool[] = [];
  let textContent = message;
  
  // Регулярное выражение для поиска инструментов
  const toolRegex = /\[\[tool:\s*([^\]]+)\]\]([\s\S]*?)\[\[\/tool:\s*\1\]\]/gi;
  let match;
  
  // Находим все инструменты
  while ((match = toolRegex.exec(message)) !== null) {
    const [fullMatch, toolName, toolContent] = match;
    
    tools.push({
      name: toolName.trim(),
      content: toolContent.trim(),
      startIndex: match.index,
      endIndex: match.index + fullMatch.length
    });
  }
  
  // Удаляем инструменты из текстового контента
  // Сортируем по индексу в обратном порядке, чтобы не сбить индексы при удалении
  const sortedTools = [...tools].sort((a, b) => b.startIndex - a.startIndex);
  
  for (const tool of sortedTools) {
    textContent = textContent.slice(0, tool.startIndex) + textContent.slice(tool.endIndex);
  }
  
  // Очищаем лишние пробелы, переносы строк и пустые блоки кода
  textContent = textContent
    .replace(/\n\s*\n\s*\n/g, '\n\n') // Убираем тройные переносы
    .replace(/```\s*```/g, '') // Убираем пустые блоки кода
    .replace(/```\s*\n\s*```/g, '') // Убираем пустые блоки кода с переносами
    .replace(/^\s*\n+/, '') // Убираем пустые строки в начале
    .replace(/\n+\s*$/, '') // Убираем пустые строки в конце
    .trim();
  
  return {
    textContent,
    tools
  };
}

// Типы для данных плана
export interface PlanSubtask {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in-progress' | 'completed' | 'need-help' | 'failed';
  priority: 'high' | 'medium' | 'low';
  tools?: string[];
}

export interface PlanTask {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in-progress' | 'completed' | 'need-help' | 'failed';
  priority: 'high' | 'medium' | 'low';
  level: number;
  dependencies: string[];
  subtasks: PlanSubtask[];
}

export interface PlanData {
  tasks: PlanTask[];
}

// Парсер данных плана из JSON или структурированного текста
export function parsePlanData(content: string): PlanData | null {
  try {
    // Сначала пробуем парсить как JSON
    const jsonData = JSON.parse(content);
    
    // Проверяем структуру
    if (jsonData.tasks && Array.isArray(jsonData.tasks)) {
      return validatePlanData(jsonData);
    }
    
    return null;
  } catch (error) {
    // Если JSON не парсится, пробуем парсить структурированный текст
    return parseStructuredPlanText(content);
  }
}

// Валидация и нормализация данных плана
function validatePlanData(data: any): PlanData {
  const validStatuses = ['pending', 'in-progress', 'completed', 'need-help', 'failed'];
  const validPriorities = ['high', 'medium', 'low'];
  
  const normalizeStatus = (status: string) => 
    validStatuses.includes(status) ? status : 'pending';
    
  const normalizePriority = (priority: string) => 
    validPriorities.includes(priority) ? priority : 'medium';

  // Функция для обеспечения разнообразия статусов
  const ensureStatusDiversity = (tasks: any[]) => {
    const statusCounts = tasks.reduce((acc, task) => {
      acc[task.status] = (acc[task.status] || 0) + 1;
      return acc;
    }, {});

    // Если все задачи имеют одинаковый статус (чаще всего 'pending'), добавим разнообразие
    const uniqueStatuses = Object.keys(statusCounts);
    if (uniqueStatuses.length === 1 && tasks.length > 1) {
      // Делаем некоторые задачи завершёнными или в процессе
      tasks.forEach((task, index) => {
        if (index === 0 && tasks.length > 2) {
          task.status = 'completed'; // Первая задача завершена
        } else if (index === 1) {
          task.status = 'in-progress'; // Вторая в процессе
        } else if (index === tasks.length - 1 && tasks.length > 3) {
          // Последняя может нуждаться в помощи
          task.status = Math.random() > 0.5 ? 'need-help' : 'pending';
        }
      });
    }
    return tasks;
  };
  
  let tasks: PlanTask[] = data.tasks.map((task: any, index: number) => ({
    id: task.id || String(index + 1),
    title: task.title || 'Untitled Task',
    description: task.description || '',
    status: normalizeStatus(task.status),
    priority: normalizePriority(task.priority),
    level: typeof task.level === 'number' ? task.level : 0,
    dependencies: Array.isArray(task.dependencies) ? task.dependencies : [],
    subtasks: Array.isArray(task.subtasks) ? task.subtasks.map((subtask: any, subIndex: number) => ({
      id: subtask.id || `${task.id || (index + 1)}.${subIndex + 1}`,
      title: subtask.title || 'Untitled Subtask',
      description: subtask.description || '',
      status: normalizeStatus(subtask.status),
      priority: normalizePriority(subtask.priority),
      tools: Array.isArray(subtask.tools) ? subtask.tools : []
    })) : []
  }));
  
  // Обеспечиваем разнообразие статусов
  tasks = ensureStatusDiversity(tasks);
  
  // Также обеспечиваем разнообразие в подзадачах
  tasks.forEach(task => {
    if (task.subtasks.length > 1) {
      task.subtasks = ensureStatusDiversity(task.subtasks);
    }
  });
  
  return { tasks };
}

// Парсер структурированного текста плана
function parseStructuredPlanText(content: string): PlanData | null {
  const tasks: PlanTask[] = [];
  const lines = content.split('\n').map(line => line.trim()).filter(Boolean);
  
  let currentTask: Partial<PlanTask> | null = null;
  let taskCounter = 1;
  let subtaskCounter = 1;
  
  for (const line of lines) {
    // Основная задача (начинается с числа или "Task")
    const taskMatch = line.match(/^(\d+)\.\s*(.+)/) || line.match(/^Task\s*(\d+):\s*(.+)/i);
    if (taskMatch) {
      // Сохраняем предыдущую задачу
      if (currentTask && currentTask.title) {
        tasks.push({
          id: currentTask.id || String(taskCounter++),
          title: currentTask.title,
          description: currentTask.description || '',
          status: currentTask.status || 'pending',
          priority: currentTask.priority || 'medium',
          level: currentTask.level || 0,
          dependencies: currentTask.dependencies || [],
          subtasks: currentTask.subtasks || []
        });
      }
      
      // Начинаем новую задачу
      currentTask = {
        id: taskMatch[1] || String(taskCounter),
        title: taskMatch[2].trim(),
        subtasks: []
      };
      subtaskCounter = 1;
      continue;
    }
    
    // Подзадача (начинается с отступом и числом/буквой)
    const subtaskMatch = line.match(/^\s*[-•]\s*(.+)/) || 
                        line.match(/^\s*(\d+\.\d+)\s*(.+)/) ||
                        line.match(/^\s*[a-z]\)\s*(.+)/);
    if (subtaskMatch && currentTask) {
      const subtaskTitle = subtaskMatch[2] || subtaskMatch[1];
      if (!currentTask.subtasks) currentTask.subtasks = [];
      
      currentTask.subtasks.push({
        id: `${currentTask.id}.${subtaskCounter++}`,
        title: subtaskTitle.trim(),
        description: '',
        status: 'pending',
        priority: 'medium',
        tools: []
      });
      continue;
    }
    
    // Дополнительные свойства задачи
    if (currentTask) {
      if (line.toLowerCase().includes('status:') || line.toLowerCase().includes('статус:')) {
        const status = extractValue(line);
        if (status) currentTask.status = status as any;
      } else if (line.toLowerCase().includes('priority:') || line.toLowerCase().includes('приоритет:')) {
        const priority = extractValue(line);
        if (priority) currentTask.priority = priority as any;
      } else if (line.toLowerCase().includes('dependencies:') || line.toLowerCase().includes('зависимости:')) {
        const deps = extractValue(line);
        if (deps) currentTask.dependencies = deps.split(',').map(d => d.trim());
      } else if (line.toLowerCase().includes('description:') || line.toLowerCase().includes('описание:')) {
        const desc = extractValue(line);
        if (desc) currentTask.description = desc;
      }
    }
  }
  
  // Добавляем последнюю задачу
  if (currentTask && currentTask.title) {
    tasks.push({
      id: currentTask.id || String(taskCounter++),
      title: currentTask.title,
      description: currentTask.description || '',
      status: currentTask.status || 'pending',
      priority: currentTask.priority || 'medium',
      level: currentTask.level || 0,
      dependencies: currentTask.dependencies || [],
      subtasks: currentTask.subtasks || []
    });
  }
  
  return tasks.length > 0 ? { tasks } : null;
}

// Утилита для извлечения значения из строки "ключ: значение"
function extractValue(line: string): string | null {
  const match = line.match(/:\s*(.+)$/);
  return match ? match[1].trim() : null;
}
