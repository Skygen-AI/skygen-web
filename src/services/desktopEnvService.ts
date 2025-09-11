import { tauriBridge } from '@/lib/tauri-bridge';
import { websocketService } from './websocketService';

export interface ScreenshotResponse {
  success: boolean;
  data?: string; // base64 image data
  error?: string;
}

export class DesktopEnvService {
  private static instance: DesktopEnvService;

  public static getInstance(): DesktopEnvService {
    if (!DesktopEnvService.instance) {
      DesktopEnvService.instance = new DesktopEnvService();
      DesktopEnvService.instance.setupWebSocketHandlers();
    }
    return DesktopEnvService.instance;
  }

  /**
   * Захват скриншота рабочего стола через desktop_env
   */
  async takeScreenshot(): Promise<ScreenshotResponse> {
    try {
      // Вызываем Tauri команду для скриншота через desktop_env
      const result = await tauriBridge.invoke('desktop_env_screenshot');
      
      return {
        success: true,
        data: result.screenshot_data // base64 encoded PNG
      };
    } catch (error) {
      console.error('Screenshot failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Screenshot failed'
      };
    }
  }

  /**
   * Проверка доступности desktop_env
   */
  async isAvailable(): Promise<boolean> {
    try {
      await tauriBridge.invoke('desktop_env_status');
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Получение системной информации
   */
  async getSystemInfo(): Promise<any> {
    try {
      return await tauriBridge.invoke('desktop_env_system_info');
    } catch (error) {
      console.error('Failed to get system info:', error);
      throw error;
    }
  }

  /**
   * Инициализация desktop_env
   */
  async initialize(): Promise<boolean> {
    try {
      await tauriBridge.invoke('desktop_env_init');
      return true;
    } catch (error) {
      console.error('Failed to initialize desktop_env:', error);
      return false;
    }
  }

  /**
   * Настройка обработчиков WebSocket сообщений
   */
  private setupWebSocketHandlers(): void {
    // Обработчик команд на скриншот
    websocketService.onMessage('screenshot_request', async (message) => {
      console.log('Received screenshot request:', message);
      
      if (message.type === 'screenshot_request') {
        try {
          const screenshot = await this.takeScreenshot();
          
          if (screenshot.success && screenshot.data) {
            // Отправляем скриншот обратно на сервер
            websocketService.sendScreenshot(message.task_id, screenshot.data);
          } else {
            // Отправляем ошибку
            websocketService.sendTaskResult(
              message.task_id, 
              false, 
              null, 
              screenshot.error || 'Failed to take screenshot'
            );
          }
        } catch (error) {
          console.error('Screenshot failed:', error);
          websocketService.sendTaskResult(
            message.task_id, 
            false, 
            null, 
            error instanceof Error ? error.message : 'Unknown error'
          );
        }
      }
    });

    // Обработчик других задач
    websocketService.onMessage('task', async (message) => {
      console.log('Received task:', message);
      
      if (message.type === 'task') {
        try {
          // Здесь можно добавить обработку других типов задач
          const result = await this.executeTask(message.action, message.payload);
          websocketService.sendTaskResult(message.task_id, true, result);
        } catch (error) {
          console.error('Task execution failed:', error);
          websocketService.sendTaskResult(
            message.task_id, 
            false, 
            null, 
            error instanceof Error ? error.message : 'Unknown error'
          );
        }
      }
    });
  }

  /**
   * Выполнение задачи
   */
  private async executeTask(action: string, payload: any): Promise<any> {
    switch (action) {
      case 'screenshot':
        return await this.takeScreenshot();
      
      default:
        throw new Error(`Unknown action: ${action}`);
    }
  }
}

export const desktopEnvService = DesktopEnvService.getInstance();
