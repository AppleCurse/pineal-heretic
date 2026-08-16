<script lang="ts">
  import { onMount } from 'svelte';
  
  export let telemetryData: any = {};
  
  // Gerçek frekans verileri - Rust backend'den geliyor
  let ritualMatchScore = 0;
  let playlistResonance = 0;
  let envyIntensity = 0;
  let overallFrequency = "unknown";
  
  $: {
    if (telemetryData && telemetryData.type === 'frequency_update') {
      ritualMatchScore = telemetryData.ritual_match_score * 100;
      playlistResonance = telemetryData.playlist_resonance * 100;
      envyIntensity = telemetryData.envy_intensity * 100;
      overallFrequency = telemetryData.overall_frequency;
    }
  }
  
  // Ortalama frekans hesapla
  let averageFrequency = 0;
  $: {
    averageFrequency = (ritualMatchScore + playlistResonance + envyIntensity) / 3;
  }
</script>

<div class="panel frequency-panel">
  <div class="panel-header">
    <h2>01 FREKANS</h2>
    <div class="status-indicator active"></div>
  </div>
  
  <div class="panel-content">
    <div class="analog-display">
      <!-- Ritual Match Score -->
      <div class="metric">
        <div class="label">RITÜEL UYUMU</div>
        <div class="value">{ritualMatchScore.toFixed(1)}%</div>
        <div class="bar-container">
          <div class="bar ritual" style="width: {Math.min(ritualMatchScore, 100)}%;"></div>
        </div>
      </div>
      
      <!-- Playlist Resonance -->
      <div class="metric">
        <div class="label">PLAYLIST REZONANSI</div>
        <div class="value">{playlistResonance.toFixed(1)}%</div>
        <div class="bar-container">
          <div class="bar playlist" style="width: {Math.min(playlistResonance, 100)}%;"></div>
        </div>
      </div>
      
      <!-- Envy Intensity -->
      <div class="metric">
        <div class="label">KISKANÇLIK ŞİDDETİ</div>
        <div class="value">{envyIntensity.toFixed(1)}%</div>
        <div class="bar-container">
          <div class="bar envy" style="width: {Math.min(envyIntensity, 100)}%;"></div>
        </div>
      </div>
      
      <!-- Overall Frequency -->
      <div class="metric overall">
        <div class="label">ORTALAMA FREKANS</div>
        <div class="value large">{averageFrequency.toFixed(1)}%</div>
        <div class="frequency-label">{overallFrequency}</div>
      </div>
    </div>
  </div>
</div>

<style>
  .panel {
    border: 1px solid rgba(0, 255, 100, 0.3);
    background: rgba(10, 15, 10, 0.8);
    padding: 1rem;
    color: #0f0;
    font-family: 'Courier New', Courier, monospace;
    box-shadow: inset 0 0 10px rgba(0, 255, 100, 0.1);
  }
  
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(0, 255, 100, 0.3);
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
  }
  
  h2 {
    margin: 0;
    font-size: 1.2rem;
    letter-spacing: 2px;
  }
  
  .status-indicator {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #333;
  }
  
  .status-indicator.active {
    background: #0f0;
    box-shadow: 0 0 8px #0f0;
    animation: pulse 2s infinite;
  }
  
  .analog-display {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .metric {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .label {
    font-size: 0.75rem;
    letter-spacing: 1px;
    color: rgba(0, 255, 100, 0.7);
    text-transform: uppercase;
  }
  
  .value {
    font-size: 1.5rem;
    text-align: right;
    font-weight: bold;
  }
  
  .value.large {
    font-size: 2.5rem;
    color: #0f0;
    text-shadow: 0 0 10px rgba(0, 255, 100, 0.5);
  }
  
  .frequency-label {
    font-size: 0.9rem;
    text-align: right;
    color: rgba(0, 255, 100, 0.8);
    font-style: italic;
  }
  
  .bar-container {
    height: 20px;
    background: #111;
    border: 1px solid #333;
    overflow: hidden;
  }
  
  .bar {
    height: 100%;
    transition: width 0.3s ease-out;
  }
  
  .bar.ritual {
    background: linear-gradient(90deg, #0a0, #0f0);
  }
  
  .bar.playlist {
    background: linear-gradient(90deg, #0a5, #0fa);
  }
  
  .bar.envy {
    background: linear-gradient(90deg, #a00, #f00);
  }
  
  @keyframes pulse {
    0% { opacity: 0.5; }
    50% { opacity: 1; }
    100% { opacity: 0.5; }
  }
</style>
