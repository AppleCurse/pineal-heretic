<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';
  import { onMount, afterUpdate } from 'svelte';
  
  export let telemetryData: any = {};
  
  let messages: {sender: string, text: string}[] = [
    { sender: 'ASPASIA', text: 'Sistem çevrimiçi. Emirlerinizi bekliyorum şefim.' }
  ];
  let inputMessage = "";
  let chatContainer: HTMLElement;
  
  async function sendMessage() {
    if (!inputMessage.trim()) return;
    
    messages = [...messages, { sender: 'SİZ', text: inputMessage }];
    let currentInput = inputMessage;
    inputMessage = "";
    
    try {
      // In Phase 4, we query Aspasia via Tauri IPC
      const response: string = await invoke('query_aspasia');
      messages = [...messages, { sender: 'ASPASIA', text: response }];
    } catch (error) {
      messages = [...messages, { sender: 'SİSTEM', text: `HATA: ${error}` }];
    }
  }
  
  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') {
      sendMessage();
    }
  }
  
  afterUpdate(() => {
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  });
</script>

<div class="panel aspasia-panel">
  <div class="panel-header">
    <h2>04 ASPASIA (DOĞAL DİL ARAYÜZÜ)</h2>
    <div class="typing-indicator">...</div>
  </div>
  
  <div class="panel-content">
    <div class="chat-container" bind:this={chatContainer}>
      {#each messages as msg}
        <div class="message {msg.sender === 'SİZ' ? 'user' : 'aspasia'}">
          <strong>[{msg.sender}]</strong> {msg.text}
        </div>
      {/each}
    </div>
    
    <div class="input-area">
      <span class="prompt">></span>
      <input type="text" bind:value={inputMessage} on:keydown={handleKeydown} placeholder="Komut girin..." />
      <button on:click={sendMessage}>İLET</button>
    </div>
  </div>
</div>

<style>
  .panel {
    border: 1px solid rgba(255, 0, 255, 0.3);
    background: rgba(15, 10, 20, 0.8);
    padding: 1rem;
    color: #f0f;
    font-family: 'Courier New', Courier, monospace;
    box-shadow: inset 0 0 10px rgba(255, 0, 255, 0.1);
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255, 0, 255, 0.3);
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
  }
  
  h2 {
    margin: 0;
    font-size: 1.2rem;
    letter-spacing: 2px;
  }
  
  .typing-indicator {
    animation: blink 1s infinite;
  }
  
  .panel-content {
    display: flex;
    flex-direction: column;
    flex: 1;
    overflow: hidden;
  }
  
  .chat-container {
    flex: 1;
    overflow-y: auto;
    padding: 0.5rem;
    background: rgba(0,0,0,0.5);
    border: 1px solid rgba(255,0,255,0.2);
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .message {
    padding: 0.5rem;
    background: rgba(255,0,255,0.1);
    border-left: 2px solid #f0f;
  }
  
  .message.user {
    background: rgba(0,255,255,0.1);
    border-left: none;
    border-right: 2px solid #0ff;
    color: #0ff;
    align-self: flex-end;
    text-align: right;
  }
  
  .input-area {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(0,0,0,0.8);
    border: 1px solid #f0f;
    padding: 0.5rem;
  }
  
  .prompt {
    font-weight: bold;
  }
  
  input {
    flex: 1;
    background: transparent;
    border: none;
    color: #f0f;
    font-family: inherit;
    outline: none;
  }
  
  button {
    background: #f0f;
    color: #000;
    border: none;
    padding: 0.5rem 1rem;
    font-weight: bold;
    cursor: pointer;
    transition: background 0.2s;
  }
  
  button:hover {
    background: #ff55ff;
  }
  
  @keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
  }
</style>
