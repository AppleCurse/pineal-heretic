<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';
  
  export let telemetryData: any = {};

  let targetData = {
    bio: '',
    posts: []
  };
  
  let analysis: any = null;
  let loading = false;
  
  async function analyzeTarget() {
    loading = true;
    try {
      analysis = await invoke('analyze_with_aspasia', {
        targetData: targetData
      });
      console.log(analysis);
    } catch (e) {
      console.error('Aspasia error:', e);
    }
    loading = false;
  }
</script>

<div class="aspasia-panel">
  <h3>🧠 ASPASIA v5.0 (DOPAMINE ENGINE)</h3>
  
  <div class="input-section">
    <textarea bind:value={targetData.bio} placeholder="Hedef bio..."></textarea>
    <button on:click={analyzeTarget} disabled={loading}>
      {loading ? 'Analyzing...' : 'ANALYZE TARGET'}
    </button>
  </div>
  
  {#if analysis}
    <div class="results">
      <div class="metrics-grid">
        <div class="metric-card dark-triad">
          <h4>Dark Triad</h4>
          <div class="meter">
            <label>Machiavellianism</label>
            <progress value={analysis.psychological_profile.dark_triad.machiavellianism} max="1"></progress>
          </div>
          <div class="meter">
            <label>Narcissism</label>
            <progress value={analysis.psychological_profile.dark_triad.narcissism} max="1"></progress>
          </div>
          <div class="meter">
            <label>Psychopathy</label>
            <progress value={analysis.psychological_profile.dark_triad.psychopathy} max="1"></progress>
          </div>
        </div>

        <div class="metric-card dopamine-profile">
          <h4>Addiction Potential</h4>
          <div class="meter alert">
            <label>Exploitability</label>
            <progress value={analysis.psychological_profile.exploitability} max="1"></progress>
            <span>{(analysis.psychological_profile.exploitability * 100).toFixed(0)}%</span>
          </div>
          <div class="meter alert">
            <label>Addiction Risk</label>
            <progress value={analysis.strategy.addiction_potential} max="1"></progress>
            <span>{(analysis.strategy.addiction_potential * 100).toFixed(0)}%</span>
          </div>
          <div class="meter alert">
            <label>Compliance Prob.</label>
            <progress value={analysis.strategy.compliance_probability} max="1"></progress>
            <span>{(analysis.strategy.compliance_probability * 100).toFixed(0)}%</span>
          </div>
        </div>
      </div>

      <div class="info-row">
        <span class="tag">Wound: {analysis.psychological_profile.core_wound}</span>
        <span class="tag">Attachment: {analysis.psychological_profile.attachment}</span>
        <span class="tag">Pacing: {analysis.dopamine_profile.optimal_schedule}</span>
        <span class="tag warning">{analysis.warning}</span>
      </div>
      
      <div class="strategy">
        <h4>Interaction Sequence (Dopamine Loop)</h4>
        <div class="sequence-list">
          {#each analysis.strategy.sequence as step, i}
            <div class="step-card {step.mechanism === 'jackpot' ? 'jackpot' : step.mechanism === 'near_miss' ? 'near-miss' : 'loss'}">
              <div class="step-header">
                <span class="step-num">[{i+1}] {step.phase}</span>
                <span class="spike">Dopamine Spike: {(step.dopamine_spike).toFixed(1)}</span>
                <span class="delay">Wait: {step.delay}s</span>
              </div>
              <p class="content">{step.content}</p>
              <div class="mechanisms">
                <small>{step.mechanism}</small>
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .aspasia-panel {
    background: rgba(10, 10, 10, 0.9);
    border: 1px solid #0f0;
    padding: 20px;
    color: #0f0;
    font-family: 'Share Tech Mono', 'Courier New', monospace;
    height: 100%;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
  }
  
  h3 {
    margin-top: 0;
    text-shadow: 0 0 5px #0f0;
    text-align: center;
    border-bottom: 1px solid #0f0;
    padding-bottom: 10px;
  }

  h4 {
    margin-top: 0;
    color: #fff;
    text-shadow: 0 0 3px #fff;
  }
  
  .input-section {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 20px;
  }
  
  textarea {
    background: #000;
    color: #0f0;
    border: 1px solid #0f0;
    padding: 10px;
    font-family: inherit;
    resize: vertical;
    min-height: 80px;
  }
  
  button {
    background: #0f0;
    color: #000;
    border: none;
    padding: 10px;
    font-weight: bold;
    cursor: pointer;
    text-transform: uppercase;
  }
  
  button:hover {
    background: #fff;
  }
  
  button:disabled {
    background: #333;
    color: #666;
    cursor: not-allowed;
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
  }

  .metric-card {
    background: #111;
    border: 1px dashed #0f0;
    padding: 15px;
  }
  
  .meter {
    margin: 10px 0;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .meter label {
    width: 140px;
    font-size: 0.9em;
  }
  
  progress {
    flex-grow: 1;
    height: 8px;
    background: #1a1a1a;
    border: 1px solid #333;
  }
  
  progress::-webkit-progress-value {
    background: #0f0;
    box-shadow: 0 0 5px #0f0;
  }

  .meter.alert progress::-webkit-progress-value {
    background: #f00;
    box-shadow: 0 0 5px #f00;
  }

  .info-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 20px;
  }

  .tag {
    background: #0f0;
    color: #000;
    padding: 3px 8px;
    font-size: 0.9em;
    font-weight: bold;
  }

  .tag.warning {
    background: #f00;
    color: #fff;
  }

  .sequence-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .step-card {
    background: #1a1a1a;
    border-left: 3px solid #0f0;
    padding: 10px 15px;
  }

  .step-card.jackpot { border-left-color: #ff0; }
  .step-card.near-miss { border-left-color: #f0f; }
  .step-card.loss { border-left-color: #555; }

  .step-header {
    display: flex;
    justify-content: space-between;
    font-size: 0.8em;
    color: #888;
    margin-bottom: 5px;
  }

  .step-num { color: #0f0; }
  
  .content {
    margin: 5px 0;
    color: #fff;
  }

  .mechanisms {
    text-align: right;
    color: #555;
  }
</style>
