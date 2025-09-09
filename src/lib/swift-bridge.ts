// Swift-JavaScript Bridge for Skygen Native
// Provides seamless communication between Next.js and Swift backend

declare global {
  interface Window {
    webkit?: {
      messageHandlers?: {
        overlay?: {
          postMessage: (message: any) => void;
        };
      };
    };
  }
}

export class SwiftBridge {
  private static instance: SwiftBridge;
  
  public static getInstance(): SwiftBridge {
    if (!SwiftBridge.instance) {
      SwiftBridge.instance = new SwiftBridge();
    }
    return SwiftBridge.instance;
  }
  
  private constructor() {
    console.log('🌉 Swift Bridge initialized');
  }
  
  // Check if we're running in Swift WebView
  public isNativeApp(): boolean {
    return !!(window.webkit?.messageHandlers?.overlay);
  }
  
  // Send message to Swift
  public sendMessage(action: string, params?: Record<string, any>) {
    if (!this.isNativeApp()) {
      console.warn('⚠️ Not running in native app, message ignored:', action);
      return;
    }
    
    const message = { action, ...params };
    window.webkit!.messageHandlers!.overlay!.postMessage(message);
    console.log('📤 Sent to Swift:', message);
  }
  
  // MARK: - Overlay Controls
  public showOverlay() {
    this.sendMessage('showOverlay');
  }
  
  public hideOverlay() {
    this.sendMessage('hideOverlay');
  }
  
  // MARK: - Outline Controls
  public startOutline(color: string, width: number, blur: number) {
    this.sendMessage('startOutline', { color, width, blur });
  }
  
  public stopOutline() {
    this.sendMessage('stopOutline');
  }
  
  public updateOutline(color: string, width: number, blur: number) {
    this.sendMessage('updateOutline', { color, width, blur });
  }
  
  // MARK: - Navigation Controls
  public navigateTo(path: string) {
    this.sendMessage('navigateTo', { path });
  }
  
  // MARK: - Utility Methods
  public getEnvironment(): 'native' | 'web' {
    return this.isNativeApp() ? 'native' : 'web';
  }
  
  public log(message: string) {
    console.log(`[${this.getEnvironment().toUpperCase()}] ${message}`);
  }
}

// Global instance
export const swiftBridge = SwiftBridge.getInstance();
