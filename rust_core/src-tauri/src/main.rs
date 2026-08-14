//! PINEAL HERETIC - Tauri Uygulama Ana Giriş Noktası
//! 
//! Bu dosya Tauri uygulamasının başlangıç noktasıdır.
//! CoreState'i başlatır, IPC komutlarını kaydeder ve telemetri köprüsünü kurar.

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use pineal_heretic_core::{
    ChiefEngine, AspasiaEngine, EventBus, TaskManager, StealthVault,
};
use pineal_heretic_core::tauri_bridge::{CoreState, setup_telemetry_bridge};
use std::sync::Arc;
use tokio::sync::Mutex;

fn main() {
    // Core bileşenleri başlat
    let event_bus = EventBus::new(100);
    
    let chief = ChiefEngine::new(100);
    
    let aspasia = AspasiaEngine::new(chief.clone(), "dummy_api_key".to_string());
    
    let vault = StealthVault::new_default().expect("Vault oluşturulamadı");
    
    let task_manager = TaskManager::new(
        event_bus.clone(),
        chief.clone(),
    );
    
    // CoreState oluştur
    let core_state = CoreState {
        task_manager: Arc::new(task_manager),
        aspasia: Arc::new(Mutex::new(aspasia)),
        vault: Arc::new(Mutex::new(vault)),
        event_bus: event_bus.clone(),
    };
    
    // Telemetri alıcısı oluştur
    let telemetry_rx = event_bus.subscribe_telemetry();
    
    // Tauri uygulamasını başlat
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(core_state)
        .invoke_handler(tauri::generate_handler![
            tauri_bridge::start_analysis,
            tauri_bridge::query_aspasia,
            tauri_bridge::set_vault_credentials,
        ])
        .setup(move |app| {
            // Telemetri köprüsünü kur
            let app_handle = app.handle().clone();
            setup_telemetry_bridge(app_handle, telemetry_rx);
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("Tauri uygulaması başlatılırken hata oluştu");
}
