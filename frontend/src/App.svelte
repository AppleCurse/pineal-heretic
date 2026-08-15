<script lang="ts">
  import { onMount } from 'svelte';
  import { listen } from '@tauri-apps/api/event';
  import { invoke } from '@tauri-apps/api/core';
  
  import FrequencyPanel from './components/FrequencyPanel.svelte';
  import RadarPanel from './components/RadarPanel.svelte';
  import VaultPanel from './components/VaultPanel.svelte';
  import RealAspasiaPanel from './components/RealAspasiaPanel.svelte';
  import { scrapedUsername, scrapedBio, scrapedPosts, isScraping } from './store';

  let telemetryData: any = null;
  let targetUrl = "";
  
  onMount(() => {
    let unlisten: (() => void) | undefined;
    
    // Listen for telemetry events from Rust backend
    listen('pineal-telemetry', (event: any) => {
      try {
        if (event.payload && event.payload.data) {
          telemetryData = JSON.parse(event.payload.data);
        }
      } catch(e) {
        console.error("Telemetry parse error", e);
      }
    }).then(u => { unlisten = u; });
    
    return () => {
      if (unlisten) unlisten();
    };
  });
  
  async function triggerAnalysis() {
    if (!targetUrl) return;
    try {
      isScraping.set(true);
      telemetryData = { type: 'radar_alert', message: `HAYALET TARAYICI BAŞLATILDI: ${targetUrl}` };
      
      const profile: any = await invoke('run_osint_scraper', { targetUrl });
      
      if (profile.error) {
        telemetryData = { type: 'radar_alert', message: `HATA: ${profile.error}` };
      } else {
        telemetryData = { type: 'radar_alert', message: `VERİ ÇEKİLDİ: ${profile.username}` };
        
        // Mağazayı güncelle
        scrapedUsername.set(profile.username);
        scrapedBio.set(profile.biography || "");
        
        const postTexts = profile.posts
          .filter((p: any) => p.caption)
          .map((p: any) => p.caption);
          
        scrapedPosts.set(postTexts);
      }
    } catch (e) {
      telemetryData = { type: 'radar_alert', message: `ÇÖKME: ${e}` };
    } finally {
      isScraping.set(false);
    }
  }
</script>

<main class="cockpit-container">
  <div class="header-section">
    <div class="logo-area">
      <h1>[ PINEAL_HERETIC ]</h1>
      <span class="status-blink">SYS.ON // OTONOM_RADAR</span>
    </div>
    
    <div class="analysis-bar">
      <div class="input-wrapper">
        <span class="prompt">></span>
        <input type="text" bind:value={targetUrl} placeholder="HEDEF KİMLİĞİ GİRİN (Örn: https://x.com/hedef)" />
      </div>
      <button on:click={triggerAnalysis} class="btn-scan">
        <span class="btn-text">TARAMAYI BAŞLAT</span>
        <span class="btn-glitch"></span>
      </button>
    </div>
  </div>

  <div class="grid-layout">
    <div class="panel-wrapper"><FrequencyPanel {telemetryData} /></div>
    <div class="panel-wrapper"><RadarPanel {telemetryData} /></div>
    <div class="panel-wrapper"><VaultPanel /></div>
    <div class="panel-wrapper span-full"><RealAspasiaPanel /></div>
  </div>
  
  <div class="scanlines"></div>
</main>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    background-color: #020202;
    color: #0f0;
    font-family: 'Share Tech Mono', 'Courier New', monospace;
    overflow: hidden;
  }
  
  .cockpit-container {
    height: 100vh;
    display: flex;
    flex-direction: column;
    padding: 1.5rem;
    box-sizing: border-box;
    position: relative;
    z-index: 1;
    background: radial-gradient(circle at center, #051505 0%, #000 100%);
  }
  
  /* CRT Scanline Effect */
  .scanlines {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background: linear-gradient(
      to bottom,
      rgba(255,255,255,0),
      rgba(255,255,255,0) 50%,
      rgba(0,0,0,0.2) 50%,
      rgba(0,0,0,0.2)
    );
    background-size: 100% 4px;
    pointer-events: none;
    z-index: 999;
    opacity: 0.6;
  }
  
  .header-section {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #0f0;
    padding-bottom: 1rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 10px rgba(0,255,0,0.1);
  }
  
  .logo-area {
    display: flex;
    flex-direction: column;
  }
  
  h1 {
    margin: 0;
    color: #0f0;
    text-shadow: 0 0 8px #0f0;
    letter-spacing: 2px;
    font-size: 1.8rem;
  }
  
  .status-blink {
    font-size: 0.8rem;
    color: #0a0;
    animation: blink 2s infinite;
    margin-top: 4px;
  }
  
  .analysis-bar {
    display: flex;
    gap: 1rem;
    flex: 1;
    max-width: 600px;
    align-items: center;
  }
  
  .input-wrapper {
    display: flex;
    align-items: center;
    background: rgba(0, 20, 0, 0.5);
    border: 1px solid #0f0;
    flex: 1;
    padding: 0 10px;
  }
  
  .prompt {
    color: #0f0;
    font-weight: bold;
    margin-right: 10px;
  }
  
  .input-wrapper input {
    flex: 1;
    background: transparent;
    border: none;
    color: #0f0;
    padding: 10px 0;
    font-family: inherit;
    outline: none;
  }
  
  .btn-scan {
    position: relative;
    background: #0f0;
    color: #000;
    border: 1px solid #0f0;
    padding: 10px 20px;
    font-weight: bold;
    cursor: pointer;
    text-transform: uppercase;
    font-family: inherit;
    letter-spacing: 1px;
    overflow: hidden;
    transition: all 0.3s;
  }
  
  .btn-scan:hover {
    background: #1aff1a;
    box-shadow: 0 0 15px #0f0;
  }
  
  .btn-scan:active {
    transform: scale(0.98);
  }
  
  .grid-layout {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    grid-template-rows: auto 1fr;
    gap: 1.5rem;
    flex: 1;
    min-height: 0;
  }
  
  .panel-wrapper {
    display: flex;
    flex-direction: column;
    min-height: 0;
    border: 1px solid rgba(0, 255, 0, 0.3);
    background: rgba(0, 10, 0, 0.4);
    box-shadow: inset 0 0 20px rgba(0, 255, 0, 0.05);
    backdrop-filter: blur(2px);
  }
  
  .span-full {
    grid-column: 1 / -1;
  }
  
  @keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }
</style>
