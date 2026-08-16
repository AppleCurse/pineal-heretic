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
    gap: 1rem;
  }
  
  .value {
    font-size: 2rem;
    text-align: right;
  }
  
  .bar-container {
    height: 20px;
    background: #111;
    border: 1px solid #333;
    overflow: hidden;
  }
  
  .bar {
    height: 100%;
    background: linear-gradient(90deg, #050, #0f0);
    transition: width 0.2s ease-out;
  }
  
  @keyframes pulse {
    0% { opacity: 0.5; }
    50% { opacity: 1; }
    100% { opacity: 0.5; }
  }
</style>
