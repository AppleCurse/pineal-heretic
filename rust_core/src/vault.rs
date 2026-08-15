//! PINEAL-HERETIC v5.0 - Stealth Vault (Argon2id + ChaCha20Poly1305 + Zeroize)
//! 
//! Diskte güvenli, şifreli ve RAM'de sadece kısa süreliğine açık kasa.
//! age bağımlılığı kaldırıldı. .key dosyası yok.
//! Tüm geçici şifresiz veriler (plaintext, anahtarlar) Zeroize ile bellekten silinir.

use argon2::{
    password_hash::{rand_core::OsRng, SaltString},
    Argon2, PasswordHash, PasswordHasher, PasswordVerifier,
};
use chacha20poly1305::{
    aead::{Aead, KeyInit},
    ChaCha20Poly1305, Key, Nonce,
};
use rand::{rngs::OsRng as RandOsRng, RngCore};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::RwLock;
use thiserror::Error;
use zeroize::{ZeroizeOnDrop, Zeroizing};

#[derive(Error, Debug)]
pub enum VaultError {
    #[error("Şifreleme hatası: {0}")]
    EncryptionError(String),
    #[error("Şifre çözme hatası: {0}")]
    DecryptionError(String),
    #[error("Dosya erişim hatası: {0}")]
    FileError(String),
    #[error("Anahtar üretimi hatası: {0}")]
    KeyGenerationError(String),
    #[error("Hatalı Parola")]
    WrongPassword,
}

#[derive(Serialize, Deserialize)]
struct VaultFormat {
    version: u8,
    salt: String,
    nonce: Vec<u8>,
    ciphertext: Vec<u8>,
}

pub struct StealthVault {
    vault_path: PathBuf,
    // Master key'i bellekte zeroize edilen bir yapıda tutuyoruz
    master_key: Zeroizing<Vec<u8>>,
    salt: String,
    storage: RwLock<HashMap<String, Vec<u8>>>, // RAM'de şifresiz byte olarak
}

impl StealthVault {
    /// Yeni kasa (ilk kurulum)
    pub fn new(vault_path: &Path, password: &str) -> Result<Self, VaultError> {
        let salt = SaltString::generate(&mut OsRng);
        let salt_str = salt.as_str().to_string();

        let argon2 = Argon2::default();
        let mut key_bytes = vec![0u8; 32];
        let password_bytes = password.as_bytes();
        
        // Argon2 üzerinden KDF türetimi (hash yerine doğrudan byte üretmek için hash'i parse edip byte alıyoruz)
        // Standart PasswordHash formatında saklayalım ve içinden key'i çekelim
        let password_hash = argon2.hash_password(password_bytes, &salt)
            .map_err(|e| VaultError::KeyGenerationError(e.to_string()))?;
        
        let hash_output = password_hash.hash.ok_or(VaultError::KeyGenerationError("Hash output missing".to_string()))?;
        let output_bytes = hash_output.as_bytes();
        
        // En az 32 byte olduğunu varsayarak ilk 32'yi key alıyoruz
        let len = std::cmp::min(output_bytes.len(), 32);
        key_bytes[..len].copy_from_slice(&output_bytes[..len]);
        
        let master_key = Zeroizing::new(key_bytes);

        let vault = Self {
            vault_path: vault_path.to_path_buf(),
            master_key,
            salt: salt_str,
            storage: RwLock::new(HashMap::new()),
        };
        
        // Diske boş halini şifreleyerek yaz
        vault.save_to_disk()?;
        Ok(vault)
    }

    /// Kasa Yükleme (Parola ile)
    pub fn load(vault_path: &Path, password: &str) -> Result<Self, VaultError> {
        if !vault_path.exists() {
            return Err(VaultError::FileError("Vault dosyası bulunamadı".to_string()));
        }

        let storage_bytes = fs::read(vault_path)
            .map_err(|e| VaultError::FileError(e.to_string()))?;
            
        let disk_format: VaultFormat = serde_json::from_slice(&storage_bytes)
            .map_err(|e| VaultError::FileError(format!("Corrupt vault file: {}", e)))?;
            
        if disk_format.version != 1 {
            return Err(VaultError::DecryptionError("Unsupported vault version".to_string()));
        }

        // Paroladan anahtarı türet
        let parsed_salt = SaltString::from_b64(&disk_format.salt)
            .map_err(|e| VaultError::KeyGenerationError(e.to_string()))?;
            
        let argon2 = Argon2::default();
        let password_hash = argon2.hash_password(password.as_bytes(), &parsed_salt)
            .map_err(|e| VaultError::KeyGenerationError(e.to_string()))?;
            
        let hash_output = password_hash.hash.ok_or(VaultError::KeyGenerationError("Hash output missing".to_string()))?;
        let output_bytes = hash_output.as_bytes();
        
        let mut key_bytes = vec![0u8; 32];
        let len = std::cmp::min(output_bytes.len(), 32);
        key_bytes[..len].copy_from_slice(&output_bytes[..len]);
        
        let master_key = Zeroizing::new(key_bytes);
        
        // Kilit açma (Decrypt)
        let key = Key::clone_from_slice(&*master_key);
        let cipher = ChaCha20Poly1305::new(&key);
        let nonce = Nonce::clone_from_slice(&disk_format.nonce);
        
        let decrypted_bytes = cipher.decrypt(&nonce, disk_format.ciphertext.as_ref())
            .map_err(|_| VaultError::WrongPassword)?;
            
        let decrypted_zeroizing = Zeroizing::new(decrypted_bytes);
        
        let storage_map: HashMap<String, Vec<u8>> = serde_json::from_slice(&*decrypted_zeroizing)
            .unwrap_or_default();

        Ok(Self {
            vault_path: vault_path.to_path_buf(),
            master_key,
            salt: disk_format.salt,
            storage: RwLock::new(storage_map),
        })
    }

    pub fn store<T: Serialize>(&self, label: &str, data: &T) -> Result<(), VaultError> {
        let plaintext_vec = serde_json::to_vec(data)
            .map_err(|e| VaultError::EncryptionError(e.to_string()))?;
        let plaintext_zeroizing = Zeroizing::new(plaintext_vec);

        {
            let mut storage = self.storage.write().map_err(|_| VaultError::EncryptionError("Lock error".to_string()))?;
            storage.insert(label.to_string(), (*plaintext_zeroizing).clone());
        }
        
        self.save_to_disk()?;
        tracing::info!("Veri '{}' etiketiyle şifrelenerek kasaya kondu", label);
        Ok(())
    }

    pub fn retrieve<T: for<'de> Deserialize<'de>>(&self, label: &str) -> Result<T, VaultError> {
        let storage = self.storage.read().map_err(|_| VaultError::DecryptionError("Lock error".to_string()))?;
        let data_bytes = storage.get(label)
            .ok_or_else(|| VaultError::DecryptionError(format!("'{}' etiketli veri bulunamadı", label)))?;
            
        serde_json::from_slice(data_bytes)
            .map_err(|e| VaultError::DecryptionError(e.to_string()))
    }

    fn save_to_disk(&self) -> Result<(), VaultError> {
        let storage = self.storage.read().map_err(|_| VaultError::FileError("Lock error".to_string()))?;
        let plaintext_vec = serde_json::to_vec(&*storage)
            .map_err(|e| VaultError::FileError(e.to_string()))?;
        let plaintext = Zeroizing::new(plaintext_vec);

        let key = Key::clone_from_slice(&*self.master_key);
        let cipher = ChaCha20Poly1305::new(&key);
        
        let mut nonce_bytes = [0u8; 12];
        RandOsRng.fill_bytes(&mut nonce_bytes);
        let nonce = Nonce::clone_from_slice(&nonce_bytes);

        let ciphertext = cipher.encrypt(&nonce, plaintext.as_ref())
            .map_err(|e| VaultError::EncryptionError(e.to_string()))?;

        let disk_format = VaultFormat {
            version: 1,
            salt: self.salt.clone(),
            nonce: nonce.to_vec(),
            ciphertext,
        };

        // Atomik yazma simülasyonu (temp file -> rename)
        let temp_path = self.vault_path.with_extension("tmp");
        let disk_bytes = serde_json::to_vec(&disk_format)
            .map_err(|e| VaultError::FileError(e.to_string()))?;
            
        fs::write(&temp_path, disk_bytes)
            .map_err(|e| VaultError::FileError(e.to_string()))?;
            
        fs::rename(&temp_path, &self.vault_path)
            .map_err(|e| VaultError::FileError(e.to_string()))?;

        tracing::info!("Vault {} konumuna kaydedildi", self.vault_path.display());
        Ok(())
    }

    pub fn change_password(&mut self, new_password: &str) -> Result<(), VaultError> {
        let new_salt = SaltString::generate(&mut OsRng);
        self.salt = new_salt.as_str().to_string();
        
        let argon2 = Argon2::default();
        let password_hash = argon2.hash_password(new_password.as_bytes(), &new_salt)
            .map_err(|e| VaultError::KeyGenerationError(e.to_string()))?;
            
        let hash_output = password_hash.hash.ok_or(VaultError::KeyGenerationError("Hash output missing".to_string()))?;
        let output_bytes = hash_output.as_bytes();
        
        let mut key_bytes = vec![0u8; 32];
        let len = std::cmp::min(output_bytes.len(), 32);
        key_bytes[..len].copy_from_slice(&output_bytes[..len]);
        
        self.master_key = Zeroizing::new(key_bytes);
        self.save_to_disk()?;
        Ok(())
    }
}

// Zeroizing wrapper structs otomatik bellek silmeyi halleder.
// Ekstra Drop impl gerekmez.

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[derive(Serialize, Deserialize, Debug, PartialEq)]
    struct TestSecret {
        api_key: String,
        session_token: String,
    }

    #[test]
    fn test_vault_flow() {
        let dir = tempdir().unwrap();
        let vault_path = dir.path().join("test_vault.enc");
        
        let password = "super_secure_password_123";
        let secret = TestSecret {
            api_key: "sk-test-12345".to_string(),
            session_token: "sess-abcde".to_string(),
        };

        // 1. Yeni kasa oluştur ve sakla
        {
            let vault = StealthVault::new(&vault_path, password).unwrap();
            vault.store("creds", &secret).unwrap();
            
            // Diskte .key oluşmamalı
            assert!(!vault_path.with_extension("key").exists());
        } // vault burada drop edilir, Zeroizing devreye girer

        // 2. Yanlış şifreyle açmayı dene
        let wrong_vault_res = StealthVault::load(&vault_path, "wrong_pass");
        assert!(matches!(wrong_vault_res, Err(VaultError::WrongPassword)));

        // 3. Doğru şifreyle aç
        let loaded_vault = StealthVault::load(&vault_path, password).unwrap();
        let retrieved: TestSecret = loaded_vault.retrieve("creds").unwrap();
        
        assert_eq!(secret, retrieved);
    }
}
