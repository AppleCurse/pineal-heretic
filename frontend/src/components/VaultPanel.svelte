<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';
  
  let keyInput = "";
  let valInput = "";
  let masterPassword = "";
  let vaultStatus = "KİLİTLİ (PAROLA BEKLENİYOR)";
  let vaultLog = "";
  let isUnlocked = false;

  async function unlockVault() {
    if (!masterPassword) return;
    try {
      vaultStatus = "KİLİT AÇILIYOR...";
      const res: string = await invoke('unlock_vault', { password: masterPassword });
      vaultLog = res;
      vaultStatus = "GÜVENLİ (MÜHÜRLÜ)";
      isUnlocked = true;
      masterPassword = ""; // Clear password from UI memory
    } catch(err) {
      vaultLog = `HATA: ${err}`;
      vaultStatus = "İHLAL RİSKİ";
    }
  }

  async function sealCredentials() {
    try {
      vaultStatus = "MÜHÜRLENİYOR...";
      const res: string = await invoke('set_vault_credentials', { key: keyInput, value: valInput });
      vaultLog = res;
      vaultStatus = "GÜVENLİ (MÜHÜRLÜ)";
      keyInput = "";
      valInput = "";
    } catch(err) {
      vaultLog = `HATA: ${err}`;
      vaultStatus = "İHLAL RİSKİ";
    }
  }
</script>

<div class="panel vault-panel">
  <div class="panel-header">
    <h2>03 GİZLİ KASA</h2>
    <div class="lock-icon">{isUnlocked ? '🔓' : '🔒'}</div>
  </div>
  
  <div class="panel-content">
    <div class="status-box" class:alert={vaultStatus === 'İHLAL RİSKİ'}>
      DURUM: {vaultStatus}
    </div>
    
    {#if !isUnlocked}
      <div class="form-group">
        <input type="password" bind:value={masterPassword} placeholder="Master Parola (Zorunlu)" />
        <button on:click={unlockVault}>KİLİDİ AÇ / OLUŞTUR</button>
      </div>
    {:else}
      <div class="form-group">
        <input type="text" bind:value={keyInput} placeholder="Anahtar (Örn: OPENAI_API_KEY)" />
        <input type="password" bind:value={valInput} placeholder="Değer (Gizli)" />
        <button on:click={sealCredentials}>KASAYA MÜHÜRLE</button>
      </div>
    {/if}
    
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
