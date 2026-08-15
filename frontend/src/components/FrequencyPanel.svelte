<script lang="ts">
  import { onMount } from 'svelte';
  
  export let telemetryData: any = {};
  
  // Example dummy animation or real data binding
  let frequency = 0;
  
  $: {
    if (telemetryData && telemetryData.type === 'frequency') {
      frequency = telemetryData.value;
    }
  }
</script>

<div class="panel frequency-panel">
  <div class="panel-header">
    <h2>01 FREKANS</h2>
    <div class="status-indicator active"></div>
  </div>
  
  <div class="panel-content">
    <div class="analog-display">
      <div class="value">{frequency.toFixed(2)} Hz</div>
      <div class="bar-container">
        <div class="bar" style="width: {Math.min(frequency, 100)}%;"></div>
      </div>
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
  
  .status-indicator {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #030;
  }
  
  .status-indicator.active {
    background: #0f0;
    box-shadow: 0 0 10px #0f0;
    animation: pulse 1.5s infinite;
  }
  
  .panel-content {
    display: flex;
    flex-direction: column;
    flex: 1;
    justify-content: center;
  }
  
  .analog-display {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .value {
    font-size: 2.5rem;
    text-align: right;
    text-shadow: 0 0 15px rgba(0,255,0,0.5);
  }
  
  .bar-container {
    height: 25px;
    background: rgba(0, 20, 0, 0.5);
    border: 1px solid #0f0;
    overflow: hidden;
  }
  
  .bar {
    height: 100%;
    background: linear-gradient(90deg, #050, #0f0);
    transition: width 0.2s ease-out;
    box-shadow: 0 0 10px #0f0;
  }
  
  @keyframes pulse {
    0% { opacity: 0.4; }
    50% { opacity: 1; box-shadow: 0 0 15px #0f0; }
    100% { opacity: 0.4; }
  }
</style>
