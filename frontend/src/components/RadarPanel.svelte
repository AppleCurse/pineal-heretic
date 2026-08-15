<script lang="ts">
  export let telemetryData: any = {};
  
  // Tactical Radar Panel
  let alerts: string[] = [];
  
  $: {
    if (telemetryData && telemetryData.type === 'radar_alert') {
      alerts = [telemetryData.message, ...alerts].slice(0, 5);
    }
  }
</script>

<div class="panel radar-panel">
  <div class="panel-header">
    <h2>02 TAKTİK RADAR</h2>
    <div class="radar-sweep"></div>
  </div>
  
  <div class="panel-content">
    <div class="radar-circle">
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
  
  .panel-content {
    display: flex;
    flex-direction: column;
    flex: 1;
    align-items: center;
  }
  
  .radar-circle {
    position: relative;
    width: 140px;
    height: 140px;
    border: 1px solid #0f0;
    border-radius: 50%;
    margin: 0 auto 1.5rem;
    overflow: hidden;
    background: radial-gradient(circle, rgba(0,255,0,0.1) 0%, rgba(0,0,0,0) 70%);
    box-shadow: 0 0 15px rgba(0,255,0,0.2);
  }
  
  .grid {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image: 
      linear-gradient(rgba(0,255,0,0.3) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,255,0,0.3) 1px, transparent 1px);
    background-size: 20px 20px;
    border-radius: 50%;
  }
  
  .sweep {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 50%;
    height: 2px;
    background: linear-gradient(90deg, rgba(0,255,0,0) 0%, #0f0 100%);
    transform-origin: left center;
    animation: sweep 2s linear infinite;
    box-shadow: 0 0 10px #0f0;
  }
  
  .alert-log {
    width: 100%;
    flex: 1;
    overflow-y: auto;
    font-size: 0.85rem;
    background: rgba(0, 20, 0, 0.5);
    padding: 0.5rem;
    border: 1px solid rgba(0, 255, 0, 0.2);
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .alert-item {
    padding-left: 0.5rem;
    border-left: 2px solid #0f0;
  }
  
  .text-muted {
    opacity: 0.5;
    border-left: 2px solid transparent;
  }
  
  @keyframes sweep {
    to { transform: rotate(360deg); }
  }
</style>
