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
  
  .typing-indicator {
    animation: blink 1s infinite;
    color: #0f0;
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
    background: rgba(0, 20, 0, 0.5);
    border: 1px solid rgba(0, 255, 0, 0.2);
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .message {
    padding: 0.5rem;
    background: rgba(0, 255, 0, 0.1);
    border-left: 2px solid #0f0;
  }
  
  .message.user {
    background: rgba(0, 100, 0, 0.3);
    border-left: none;
    border-right: 2px solid #0a0;
    color: #0f0;
    align-self: flex-end;
    text-align: right;
  }
  
  .input-area {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(0, 20, 0, 0.8);
    border: 1px solid #0f0;
    padding: 0.5rem;
  }
  
  .prompt {
    font-weight: bold;
    color: #0f0;
  }
  
  input {
    flex: 1;
    background: transparent;
    border: none;
    color: #0f0;
    font-family: inherit;
    outline: none;
  }
  
  button {
    background: transparent;
    color: #0f0;
    border: 1px solid #0f0;
    padding: 0.5rem 1rem;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  button:hover {
    background: #0f0;
    color: #000;
    box-shadow: 0 0 10px #0f0;
  }
  
  @keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
  }
</style>
