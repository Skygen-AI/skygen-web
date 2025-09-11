export interface TaskMessage {
  type: 'task';
  task_id: string;
  action: string;
  payload: any;
}

export interface ScreenshotMessage {
  type: 'screenshot_request';
  task_id: string;
}

export interface TaskResultMessage {
  type: 'task_result';
  task_id: string;
  success: boolean;
  result?: any;
  error?: string;
}

export type WebSocketMessage = TaskMessage | ScreenshotMessage | TaskResultMessage;

export class WebSocketService {
  private static instance: WebSocketService;
  private ws: WebSocket | null = null;
  private url: string = 'ws://localhost:8000/v1/ws/agent';
  private token: string | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private messageHandlers: Map<string, (message: WebSocketMessage) => void> = new Map();

  public static getInstance(): WebSocketService {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService();
    }
    return WebSocketService.instance;
  }

  /**
   * Подключение к WebSocket серверу
   */
  async connect(token: string): Promise<boolean> {
    this.token = token;
    
    return new Promise((resolve, reject) => {
      try {
        // Добавляем токен как query parameter
        const wsUrl = `${this.url}?token=${encodeURIComponent(token)}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          resolve(true);
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.handleDisconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Отключение от WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Отправка сообщения
   */
  send(message: WebSocketMessage): boolean {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
      return true;
    }
    console.warn('WebSocket is not connected');
    return false;
  }

  /**
   * Регистрация обработчика сообщений
   */
  onMessage(type: string, handler: (message: WebSocketMessage) => void): void {
    this.messageHandlers.set(type, handler);
  }

  /**
   * Удаление обработчика сообщений
   */
  offMessage(type: string): void {
    this.messageHandlers.delete(type);
  }

  /**
   * Проверка состояния подключения
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Обработка входящих сообщений
   */
  private handleMessage(message: WebSocketMessage): void {
    console.log('Received WebSocket message:', message);
    
    const handler = this.messageHandlers.get(message.type);
    if (handler) {
      handler(message);
    } else {
      console.warn(`No handler for message type: ${message.type}`);
    }
  }

  /**
   * Обработка отключения с автореконнектом
   */
  private handleDisconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts && this.token) {
      setTimeout(() => {
        console.log(`Attempting to reconnect... (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
        this.reconnectAttempts++;
        this.connect(this.token!).catch(console.error);
      }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts)); // Exponential backoff
    }
  }

  /**
   * Отправка результата выполнения задачи
   */
  sendTaskResult(taskId: string, success: boolean, result?: any, error?: string): boolean {
    return this.send({
      type: 'task_result',
      task_id: taskId,
      success,
      result,
      error
    });
  }

  /**
   * Отправка скриншота
   */
  sendScreenshot(taskId: string, screenshotData: string): boolean {
    return this.sendTaskResult(taskId, true, {
      type: 'screenshot',
      data: screenshotData,
      timestamp: new Date().toISOString()
    });
  }
}

export const websocketService = WebSocketService.getInstance();
