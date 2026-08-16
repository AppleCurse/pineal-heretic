<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';

  export let telemetryData: any = {};

  let passwordInput = "";
  let keyInput = "";
  let valInput = "";
  let vaultStatus = "GÜVENLİ (MÜHÜRLÜ)";
  let vaultLog = "";
  let isVaultOpen = false;

  async function createVault() {
    if (!passwordInput) {
      vaultLog = "HATA: Parola gerekli";
      return;
    }
    try {
      vaultStatus = "OLUŞTURULUYOR...";
      const res: string = await invoke('create_vault', { password: passwordInput });
      vaultLog = res;
      vaultStatus = "AÇIK";
      isVaultOpen = true;
      passwordInput = "";
    } catch(err) {
      vaultLog = `HATA: ${err}`;
      vaultStatus = "İHLAL RİSKİ";
    }
  }

  async function openVault() {
    if (!passwordInput) {
      vaultLog = "HATA: Parola gerekli";
      return;
    }
    try {
      vaultStatus = "AÇILIYOR...";
      const res: string = await invoke('open_vault', { password: passwordInput });
      vaultLog = res;
      vaultStatus = "AÇIK";
      isVaultOpen = true;
      passwordInput = "";
    } catch(err) {
      vaultLog = `HATA: ${err}`;
      vaultStatus = "İHLAL RİSKİ";
    }
  }

  async function sealCredentials() {
    if (!isVaultOpen) {
      vaultLog = "HATA: Önce kasayı açın";
      return;
    }
    try {
      vaultStatus = "MÜHÜRLENİYOR...";
      const res: string = await invoke('set_vault_credentials', { key: keyInput, value: valInput });
      vaultLog = res;
      vaultStatus = "AÇIK";
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
    <div class="lock-icon">{isVaultOpen ? '🔓' : '🔒'}</div>
  </div>

  <div class="panel-content">
    <div class="status-box" class:alert={vaultStatus === 'İHLAL RİSKİ'}>
      DURUM: {vaultStatus}
    </div>

    <!-- Parola Girişi -->
    <div class="form-group">
      <input type="password" bind:value={passwordInput} placeholder="MASTER PAROLA" />
      <div class="button-row">
        <button class="btn-create" on:click={createVault}>KASA OLUŞTUR</button>
        <button class="btn-open" on:click={openVault}>KASA AÇ</button>
      </div>
    </div>

    <!-- Kimlik Bilgisi Girişi (sadece kasa açıkken) -->
    {#if isVaultOpen}
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
    border: 1px solid rgba(255, 165, 0, 0.3);
    background: rgba(20, 15, 10, 0.8);
    padding: 1rem;
    color: #fa0;
    font-family: 'Courier New', Courier, monospace;
    box-shadow: inset 0 0 10px rgba(255, 165, 0, 0.1);
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255, 165, 0, 0.3);
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
  }

  h2 {
    margin: 0;
    font-size: 1.2rem;
    letter-spacing: 2px;
  }

  .status-box {
    padding: 0.5rem;
    background: rgba(0,0,0,0.5);
    border: 1px dashed #fa0;
    margin-bottom: 1rem;
    text-align: center;
    font-weight: bold;
  }

  .status-box.alert {
    border-color: #f00;
    color: #f00;
    animation: flash 1s infinite;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  input {
    background: rgba(0,0,0,0.8);
    border: 1px solid #fa0;
    color: #fa0;
    padding: 0.5rem;
    font-family: inherit;
  }

  .button-row {
    display: flex;
    gap: 0.5rem;
  }

  button {
    background: #fa0;
    color: #000;
    border: none;
    padding: 0.5rem;
    font-weight: bold;
    cursor: pointer;
    transition: background 0.2s;
    flex: 1;
  }

  button:hover {
    background: #ffb732;
  }

  .btn-create {
    background: #0cf;
    color: #000;
  }

  .btn-create:hover {
    background: #5df;
  }

  .btn-open {
    background: #0f0;
    color: #000;
  }

  .btn-open:hover {
    background: #5f5;
  }

  .vault-log {
    margin-top: 1rem;
    font-size: 0.9rem;
    opacity: 0.8;
    word-break: break-all;
  }

  @keyframes flash {
    0%, 100% { background: rgba(255,0,0,0.1); }
    50% { background: rgba(255,0,0,0.3); }
  }
</style>
