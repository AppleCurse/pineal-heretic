<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';
  
  let valInput = "";
  let vaultStatus = "API ANAHTARI BEKLENİYOR";
  let vaultLog = "";

  async function saveCredentials() {
    if (!valInput) return;
    try {
      vaultStatus = "KAYDEDİLİYOR...";
      // Arka planda otomatik şifre ile kasayı aç
      await invoke('unlock_vault', { password: "pineal_default_admin" });
      
      // API Anahtarını kaydet
      const res: string = await invoke('set_vault_credentials', { key: "OPENROUTER_API_KEY", value: valInput });
      vaultLog = "API Anahtarı başarıyla sisteme gömüldü!";
      vaultStatus = "SİSTEM AKTİF";
      valInput = "";
    } catch(err) {
      vaultLog = `HATA: ${err}`;
      vaultStatus = "BAĞLANTI HATASI";
    }
  }
</script>

<div class="panel vault-panel">
  <div class="panel-header">
    <h2>03 GİZLİ KASA</h2>
    <div class="lock-icon">🔓</div>
  </div>
  
  <div class="panel-content">
    <div class="status-box" class:alert={vaultStatus === 'İHLAL RİSKİ'}>
      DURUM: {vaultStatus}
    </div>
    
    <div class="form-group">
      <input type="password" bind:value={valInput} placeholder="OpenRouter API Key Girin" />
      <button on:click={saveCredentials}>SİSTEME KAYDET</button>
    </div>
    
    {#if vaultLog}
      <div class="vault-log">> {vaultLog}</div>
    {/if}
  </div>
</div>

<style>
  .panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 1rem;
    color: #0f0;
    font-family: 'Share Tech Mono', monospace;
  }
  
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(0, 255, 0, 0.3);
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
  }
  
  h2 {
    margin: 0;
    font-size: 1.1rem;
    letter-spacing: 2px;
    text-shadow: 0 0 5px #0f0;
  }
  
  .lock-icon {
    color: #0f0;
  }
  
  .panel-content {
    display: flex;
    flex-direction: column;
    flex: 1;
  }
  
  .status-box {
    padding: 0.5rem;
    background: rgba(0, 20, 0, 0.6);
    border: 1px dashed #0f0;
    margin-bottom: 1rem;
    text-align: center;
    font-weight: bold;
    font-size: 0.9rem;
  }
  
  .status-box.alert {
    border-color: #f00;
    color: #f00;
    background: rgba(20, 0, 0, 0.6);
    animation: flash 1s infinite;
  }
  
  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  input {
    background: rgba(0, 20, 0, 0.5);
    border: 1px solid #0f0;
    color: #0f0;
    padding: 0.5rem;
    font-family: inherit;
    outline: none;
  }
  
  input::placeholder {
    color: rgba(0, 255, 0, 0.4);
  }
  
  button {
    background: transparent;
    color: #0f0;
    border: 1px solid #0f0;
    padding: 0.5rem;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.2s;
    text-transform: uppercase;
  }
  
  button:hover {
    background: #0f0;
    color: #000;
    box-shadow: 0 0 10px #0f0;
  }
  
  .vault-log {
    margin-top: 1rem;
    font-size: 0.8rem;
    opacity: 0.8;
    background: rgba(0,0,0,0.5);
    padding: 0.5rem;
    border-left: 2px solid #0f0;
    word-wrap: break-word;
  }
  
  @keyframes flash {
    0%, 100% { box-shadow: inset 0 0 10px rgba(255,0,0,0.2); }
    50% { box-shadow: inset 0 0 20px rgba(255,0,0,0.5); }
  }
</style>
