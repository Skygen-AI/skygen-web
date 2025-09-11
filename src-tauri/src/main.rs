// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};
use tauri::State;
use std::sync::Mutex;
use base64::{Engine as _, engine::general_purpose};

#[derive(Debug, Serialize, Deserialize)]
struct ScreenshotResult {
    success: bool,
    screenshot_data: Option<String>,
    error: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct SystemInfo {
    platform: String,
    screen_width: u32,
    screen_height: u32,
}

// Состояние приложения
struct AppState {
    initialized: Mutex<bool>,
}

#[tauri::command]
async fn desktop_env_screenshot() -> Result<ScreenshotResult, String> {
    println!("Taking screenshot...");
    
    match take_screenshot_internal().await {
        Ok(screenshot_data) => Ok(ScreenshotResult {
            success: true,
            screenshot_data: Some(screenshot_data),
            error: None,
        }),
        Err(error) => Ok(ScreenshotResult {
            success: false,
            screenshot_data: None,
            error: Some(error),
        }),
    }
}

async fn take_screenshot_internal() -> Result<String, String> {
    use screenshots::Screen;
    
    let screens = Screen::all().map_err(|e| format!("Failed to get screens: {}", e))?;
    let screen = screens.into_iter().next().ok_or("No screen found")?;
    
    let image = screen.capture().map_err(|e| format!("Failed to capture screen: {}", e))?;
    
    // Используем встроенный метод для сохранения в PNG
    let mut png_bytes = Vec::new();
    {
        use image::{ImageBuffer, Rgba, ImageFormat};
        use std::io::Cursor;
        
        let (width, height) = (image.width(), image.height());
        let raw_data = image.as_raw().clone(); // Clone the data to own it
        let img_buffer = ImageBuffer::<Rgba<u8>, Vec<u8>>::from_raw(width, height, raw_data)
            .ok_or("Failed to create image buffer")?;
        
        let mut cursor = Cursor::new(&mut png_bytes);
        img_buffer.write_to(&mut cursor, ImageFormat::Png)
            .map_err(|e| format!("Failed to encode PNG: {}", e))?;
    }
    
    // Кодируем в base64
    let base64_data = general_purpose::STANDARD.encode(&png_bytes);
    Ok(base64_data)
}

#[tauri::command]
async fn desktop_env_system_info() -> Result<SystemInfo, String> {
    use screenshots::Screen;
    
    let screens = Screen::all().map_err(|e| format!("Failed to get screens: {}", e))?;
    let screen = screens.into_iter().next().ok_or("No screen found")?;
    
    Ok(SystemInfo {
        platform: std::env::consts::OS.to_string(),
        screen_width: screen.display_info.width,
        screen_height: screen.display_info.height,
    })
}

#[tauri::command]
async fn desktop_env_status() -> Result<String, String> {
    Ok("Desktop environment is available".to_string())
}

#[tauri::command]
async fn desktop_env_init(state: State<'_, AppState>) -> Result<String, String> {
    let mut initialized = state.initialized.lock().unwrap();
    *initialized = true;
    Ok("Desktop environment initialized".to_string())
}

#[tauri::command]
async fn request_screen_recording_permission() -> Result<bool, String> {
    #[cfg(target_os = "macos")]
    {
        use std::process::Command;
        
        // Проверяем текущий статус разрешения
        let output = Command::new("system_profiler")
            .args(&["SPConfigurationProfileDataType"])
            .output()
            .map_err(|e| format!("Failed to check permission: {}", e))?;
            
        if !output.status.success() {
            return Err("Failed to check screen recording permission".to_string());
        }
        
        // На macOS нужно запросить разрешение через системный диалог
        // Это происходит автоматически при первой попытке скриншота
        return Ok(true);
    }
    
    #[cfg(not(target_os = "macos"))]
    {
        Ok(true) // На других платформах разрешение не требуется
    }
}

#[tauri::command]
async fn request_accessibility_permission() -> Result<bool, String> {
    #[cfg(target_os = "macos")]
    {
        use std::process::Command;
        
        // Открываем настройки доступности
        let output = Command::new("open")
            .args(&["/System/Library/PreferencePanes/Security.prefPane"])
            .output()
            .map_err(|e| format!("Failed to open accessibility settings: {}", e))?;
            
        if !output.status.success() {
            return Err("Failed to open accessibility settings".to_string());
        }
        
        return Ok(true);
    }
    
    #[cfg(not(target_os = "macos"))]
    {
        Ok(true) // На других платформах разрешение не требуется
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(AppState {
            initialized: Mutex::new(false),
        })
        .invoke_handler(tauri::generate_handler![
            desktop_env_screenshot,
            desktop_env_system_info,
            desktop_env_status,
            desktop_env_init,
            request_screen_recording_permission,
            request_accessibility_permission
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn main() {
    run();
}
