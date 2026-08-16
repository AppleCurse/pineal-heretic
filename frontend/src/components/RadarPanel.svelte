<script lang="ts">
  export let telemetryData: any = {};
  
  // Tactical Radar Panel
  let alerts: string[] = [];
  let sweepSpeed = 2.0;  // saniye - varsayilan
  let radarIntensity = 0.2;  // grid opacity
  
  $: {
    if (telemetryData && telemetryData.type === 'radar_alert') {
      alerts = [telemetryData.message, ...alerts].slice(0, 5);
    }
    // FAZ 4B: FrequencyUpdate telemetrisi → radar animasyonu guncelle
    if (telemetryData && telemetryData.type === 'frequency_update') {
      const ritual = telemetryData.ritual_match_score ?? 0;
      const envy = telemetryData.envy_intensity ?? 0;
      const playlist = telemetryData.playlist_resonance ?? 0;
      const avgScore = (ritual + envy + playlist) / 3;

      // Skor 0 → 2 sn (yavas), Skor 1 → 0.4 sn (cok hizli)
      sweepSpeed = Math.max(0.4, 2.0 - avgScore * 1.6);
      // Skor 0 → 0.2 opacity, Skor 1 → 0.6 opacity
      radarIntensity = 0.2 + avgScore * 0.4;

      alerts = [`⚡ Frekans: R=${ritual.toFixed(2)} P=${playlist.toFixed(2)} E=${envy.toFixed(2)}`, ...alerts].slice(0, 5);
    }
  }
</script>

<div class="panel radar-panel">
  <div class="panel-header">
    <h2>02 TAKTİK RADAR</h2>
    <div class="radar-sweep-label">⚡</div>
  </div>
  
  <div class="panel-content">
    <div class="radar-circle" style="--sweep-speed:{sweepSpeed}s; --radar-intensity:{radarIntensity}">
      <div class="sweep"></div>
      <div class="grid"></div>
    </div>
    
    <div class="alert-log">
      {#each alerts as alert}
        <div class="alert-item">> {alert}</div>
      {/each}
      {#if alerts.length === 0}
        <div class="alert-item text-muted">> Radar temiz...</div>
      {/if}
    </div>
  </div>
</div>

<style>
  .panel {
    border: 1px solid rgba(0, 150, 255, 0.3);
    background: rgba(10, 15, 25, 0.8);
    padding: 1rem;
    color: #0cf;
    font-family: 'Courier New', Courier, monospace;
    box-shadow: inset 0 0 10px rgba(0, 150, 255, 0.1);
  }
  
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(0, 150, 255, 0.3);
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
  }
  
  h2 {
    margin: 0;
    font-size: 1.2rem;
    letter-spacing: 2px;
  }
  
  .radar-circle {
    position: relative;
    width: 120px;
    height: 120px;
    border: 1px solid #0cf;
    border-radius: 50%;
    margin: 0 auto 1rem;
    overflow: hidden;
    background: radial-gradient(circle, rgba(0,204,255,0.1) 0%, rgba(0,0,0,0) 70%);
  }
  
  .grid {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image: 
      linear-gradient(#0cf 1px, transparent 1px),
      linear-gradient(90deg, #0cf 1px, transparent 1px);
    background-size: 20px 20px;
    opacity: 0.2;
    border-radius: 50%;
  }
  
  .sweep {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 50%;
    height: 2px;
    background: linear-gradient(90deg, rgba(0,204,255,0) 0%, #0cf 100%);
    transform-origin: left center;
    animation: sweep var(--sweep-speed, 2s) linear infinite;
  }
  
  .grid {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image: 
      linear-gradient(#0cf 1px, transparent 1px),
      linear-gradient(90deg, #0cf 1px, transparent 1px);
    background-size: 20px 20px;
    opacity: var(--radar-intensity, 0.2);
    border-radius: 50%;
  }
  
  .alert-log {
    height: 100px;
    overflow-y: auto;
    font-size: 0.9rem;
    background: rgba(0,0,0,0.5);
    padding: 0.5rem;
    border: 1px solid rgba(0, 150, 255, 0.2);
  }
  
  .alert-item {
    margin-bottom: 0.25rem;
  }
  
  .text-muted {
    opacity: 0.5;
  }
  
  @keyframes sweep {
    to { transform: rotate(360deg); }
  }
</style>
