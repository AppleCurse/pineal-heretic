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
      await invoke('start_analysis', { targetUrl });
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
    overflow: hidden;
  }
  
  .container {
    height: 100vh;
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
    background: #111;
    border: 1px solid #555;
    color: #0f0;
    padding: 0.5rem;
    font-family: inherit;
  }
  
  .analysis-bar button {
    background: #f00;
    color: #fff;
    border: none;
    padding: 0.5rem 1rem;
    font-weight: bold;
    cursor: pointer;
    text-shadow: 0 0 5px #fff;
    transition: background 0.2s;
  }
  
  .analysis-bar button:hover {
    background: #ff3333;
    box-shadow: 0 0 10px #f00;
  }
  
  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto 1fr;
    gap: 1rem;
    flex: 1;
    min-height: 0;
  }
  
  .grid-item {
    display: flex;
    flex-direction: column;
    min-height: 0;
  }
  
  .grid-item.aspasia {
    grid-column: 1 / -1;
  }
</style>
