import { writable } from 'svelte/store';

export const scrapedUsername = writable('');
export const scrapedBio = writable('');
export const scrapedPosts = writable<string[]>([]);
export const isScraping = writable(false);
export const autoTriggerLLM = writable(false);
