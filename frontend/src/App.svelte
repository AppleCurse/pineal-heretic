<script lang="ts">
  import { onMount } from 'svelte';
  import { listen } from '@tauri-apps/api/event';
  import { invoke } from '@tauri-apps/api/core';

  import FrequencyPanel from './components/FrequencyPanel.svelte';
  import RadarPanel from './components/RadarPanel.svelte';
  import VaultPanel from './components/VaultPanel.svelte';
  import AspasiaPanel from './components/AspasiaPanel.svelte';

  let telemetryData: any = null;
  let targetUrl = "";
  
  // Frekans parametreleri
  let userRituals = "";
  let userPlaylist = "";
  let userEnvies = "";

  onMount(async () => {
    // Listen for telemetry events from Rust backend
    const unlisten = await listen('pineal-telemetry', (event: any) => {
      try {
        if (event.payload && event.payload.data) {
          telemetryData = JSON.parse(event.payload.data);
        }
      } catch(e) {
        console.error("Telemetry parse error", e);
      }
    });

    return () => {
      unlisten();
    };
  });

  async function triggerAnalysis() {
    if (!targetUrl) return;
    try {
      // Frekans parametrelerini array'e çevir ve Rust'a gönder
      const rituals = userRituals.split(',').map((s: string) => s.trim()).filter((s: string) => s.length > 0);
      const playlist = userPlaylist.split(',').map((s: string) => s.trim()).filter((s: string) => s.length > 0);
      const envies = userEnvies.split(',').map((s: string) => s.trim()).filter((s: string) => s.length > 0);
      
      await invoke('start_analysis', { 
        targetUrl,
        scraperType: "x_twitter",
        userRituals: rituals,
        userPlaylist: playlist,
        userEnvies: envies
      });
      telemetryData = { type: 'radar_alert', message: `ANALİZ BAŞLADI: ${targetUrl}` };
    } catch (e) {
      telemetryData = { type: 'radar_alert', message: `HATA: ${e}` };
    }
  }
</script>

<main class="container">
  <div class="header-section">
    <h1>PINEAL HERETIC // KOKPİT</h1>
    <div class="analysis-bar">
      <input type="text" bind:value={targetUrl} placeholder="HEDEF URL GİRİN (Örn: https://x.com/target)" />
      <button on:click={triggerAnalysis}>ANALİZ BAŞLAT</button>
    </div>
  </div>

  <!-- Frekans Giriş Alanı -->
  <div class="frequency-input-section">
    <div class="freq-input-group">
      <label>RİTÜELLER (virgülle ayır):</label>
      <input type="text" bind:value={userRituals} placeholder="gece_kodlama, kahve_ritueli, yalnızlık" />
    </div>
    <div class="freq-input-group">
      <label>PLAYLIST (virgülle ayır):</label>
      <input type="text" bind:value={userPlaylist} placeholder="dark_synth, ambient, post_punk" />
    </div>
    <div class="freq-input-group">
      <label>İMRENDİKLERİ (virgülle ayır):</label>
      <input type="text" bind:value={userEnvies} placeholder="odaklanma, disiplin, yaratıcılık" />
    </div>
  </div>

  <div class="grid">
    <div class="grid-item"><FrequencyPanel {telemetryData} /></div>
    <div class="grid-item"><RadarPanel {telemetryData} /></div>
    <div class="grid-item"><VaultPanel {telemetryData} /></div>
    <div class="grid-item aspasia"><AspasiaPanel {telemetryData} /></div>
  </div>
</main>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    background-color: #050505;
    color: #fff;
    font-family: 'Courier New', Courier, monospace;
    overflow-x: hidden;
    overflow-y: auto;
  }

  .container {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    padding: 1rem;
    box-sizing: border-box;
  }

  .header-section {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 2px solid #333;
    padding-bottom: 1rem;
    margin-bottom: 1rem;
  }

  h1 {
    margin: 0;
    color: #fff;
    text-shadow: 0 0 10px rgba(255,255,255,0.5);
    letter-spacing: 4px;
  }

  .analysis-bar {
    display: flex;
    gap: 1rem;
    flex: 1;
    max-width: 600px;
  }

  .analysis-bar input {
    flex: 1;
    background: rgba(0,0,0,0.8);
    border: 1px solid #0cf;
    color: #0cf;
    padding: 0.5rem;
    font-family: inherit;
  }

  .analysis-bar button {
    background: #0cf;
    color: #000;
    border: none;
    padding: 0.5rem 1rem;
    font-weight: bold;
    cursor: pointer;
    transition: background 0.2s;
  }

  .analysis-bar button:hover {
    background: #5df;
  }

  /* Frekans Giriş Alanı */
  .frequency-input-section {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-bottom: 1rem;
    padding: 1rem;
    background: rgba(10, 15, 25, 0.5);
    border: 1px solid rgba(0, 150, 255, 0.2);
  }

  .freq-input-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .freq-input-group label {
    font-size: 0.8rem;
    color: #0cf;
    opacity: 0.8;
  }

  .freq-input-group input {
    background: rgba(0,0,0,0.8);
    border: 1px solid rgba(0, 150, 255, 0.3);
    color: #0cf;
    padding: 0.5rem;
    font-family: inherit;
    font-size: 0.9rem;
  }

  .freq-input-group input:focus {
    outline: none;
    border-color: #0cf;
    box-shadow: 0 0 5px rgba(0, 204, 255, 0.5);
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
    flex: 1;
  }

  .grid-item {
    min-height: 200px;
  }

  .grid-item.aspasia {
    grid-column: span 2;
  }

  @media (max-width: 768px) {
    .header-section {
      flex-direction: column;
      gap: 1rem;
    }

    .analysis-bar {
      width: 100%;
      max-width: none;
    }

    .frequency-input-section {
      grid-template-columns: 1fr;
    }

    .grid {
      grid-template-columns: 1fr;
    }

    .grid-item.aspasia {
      grid-column: span 1;
    }
  }
</style>
