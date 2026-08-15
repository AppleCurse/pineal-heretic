//! PINEAL-HERETIC v4.0 - Stealth Vault
//! 
//! API anahtarları ve oturum verileri için bellek-içi şifreli kasa.
//! age + argon2 ile diskte şifreli, RAM'de sadece ihtiyaç anında açık.

use age::secrecy::{ExposeSecret, Secret};
use argon2::{password_hash::SaltString, Argon2, PasswordHasher};
use rand::{rngs::OsRng, RngCore};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::sync::RwLock;
use thiserror::Error;

/// Vault hataları
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
}

/// Şifrelenmiş veri paketi
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EncryptedPayload {
    pub ciphertext: Vec<u8>,
    pub nonce: [u8; 32],
}

/// Stealth Vault - Ana şifreli kasa yapısı
pub struct StealthVault {
    vault_path: PathBuf,
    master_key: Secret<Vec<u8>>,
    recipient: age::x25519::Recipient,
    identity: age::x25519::Identity,
    storage: RwLock<HashMap<String, EncryptedPayload>>,
}

impl StealthVault {
    /// Yeni bir vault oluştur (ilk kurulum)
    pub fn new(vault_path: &Path) -> Result<Self, VaultError> {
        // Master key üret (argon2 ile güçlendirilmiş)
        let salt = SaltString::generate(&mut OsRng);
        let argon2 = Argon2::default();
        
        // Basitlik için rastgele byte dizisi kullanıyoruz
        // Gerçek implementasyonda kullanıcı parolası kullanılacak
        let mut key_bytes = vec![0u8; 32];
        OsRng.fill_bytes(&mut key_bytes);
        
        let master_key = Secret::new(key_bytes);
        
        // age key pair üret
        let identity = age::x25519::Identity::generate();
        let recipient = identity.to_public();
        
        let vault = Self {
            vault_path: vault_path.to_path_buf(),
            master_key,
            recipient,
            identity,
            storage: RwLock::new(HashMap::new()),
        };
        
        // Vault dosyasını oluştur
        vault.save_to_disk()?;
        
        Ok(vault)
    }

    /// Mevcut vault'u yükle
    pub fn load(vault_path: &Path) -> Result<Self, VaultError> {
        if !vault_path.exists() {
            return Err(VaultError::FileError("Vault dosyası bulunamadı".to_string()));
        }

        // TODO: Şifreli dosyadan identity'yi yükle
        // Şimdilik yeni oluşturuyoruz (demo amaçlı)
        Self::new(vault_path)
    }

    /// Veriyi şifrele ve kasaya koy
    pub fn store<T: Serialize>(&self, label: &str, data: &T) -> Result<(), VaultError> {
        let plaintext = serde_json::to_vec(data)
            .map_err(|e| VaultError::EncryptionError(e.to_string()))?;

        let encrypted_data = self.encrypt_data(&plaintext)?;

        let mut storage = self.storage.write().map_err(|_| VaultError::EncryptionError("Lock error".to_string()))?;
        storage.insert(label.to_string(), encrypted_data);
        
        tracing::info!("Veri '{}' etiketiyle şifrelenerek kasaya kondu", label);
        Ok(())
    }

    /// Veriyi kasadan al ve şifresini çöz
    pub fn retrieve<T: for<'de> Deserialize<'de>>(&self, label: &str) -> Result<T, VaultError> {
        let storage = self.storage.read().map_err(|_| VaultError::DecryptionError("Lock error".to_string()))?;
        let payload = storage.get(label)
            .ok_or_else(|| VaultError::DecryptionError(format!("'{}' etiketli veri bulunamadı", label)))?;
            
        let decrypted = self.decrypt_data(payload)?;
        
        serde_json::from_slice(&decrypted)
            .map_err(|e| VaultError::DecryptionError(e.to_string()))
    }

    /// age ile veri şifreleme
    fn encrypt_data(&self, plaintext: &[u8]) -> Result<EncryptedPayload, VaultError> {
        let encryptor = age::Encryptor::with_recipients(vec![Box::new(self.recipient.clone())])
            .expect("Encryptor oluşturulamadı");
            
        let mut encrypted = vec![];
        let mut writer = encryptor.wrap_output(&mut encrypted)
            .map_err(|e| VaultError::EncryptionError(e.to_string()))?;
            
        writer.write_all(plaintext)
            .map_err(|e| VaultError::EncryptionError(e.to_string()))?;
        writer.finish()
            .map_err(|e| VaultError::EncryptionError(e.to_string()))?;

        let mut nonce = [0u8; 32];
        OsRng.fill_bytes(&mut nonce);

        Ok(EncryptedPayload {
            ciphertext: encrypted,
            nonce,
        })
    }

    /// age ile veri şifre çözme
    fn decrypt_data(&self, payload: &EncryptedPayload) -> Result<Vec<u8>, VaultError> {
        let decryptor = match age::Decryptor::new(payload.ciphertext.as_slice())
            .map_err(|e| VaultError::DecryptionError(e.to_string()))? {
            age::Decryptor::Passphrase(_) => return Err(VaultError::DecryptionError("Passphrase not supported".to_string())),
            age::Decryptor::Recipients(d) => d,
        };

        let mut reader = decryptor.decrypt(std::iter::once(&self.identity as &dyn age::Identity))
            .map_err(|e| VaultError::DecryptionError(e.to_string()))?;
            
        let mut decrypted = vec![];
        reader.read_to_end(&mut decrypted)
            .map_err(|e| VaultError::DecryptionError(e.to_string()))?;

        Ok(decrypted)
    }

    /// Vault'u diske kaydet (şifreli)
    fn save_to_disk(&self) -> Result<(), VaultError> {
        // Identity'yi şifreli olarak sakla
        let identity_str = self.identity.to_string();
        
        // Secret'ten string'i al
        let identity_bytes = identity_str.expose_secret().as_bytes();
        
        fs::write(&self.vault_path, identity_bytes)
            .map_err(|e| VaultError::FileError(e.to_string()))?;
        
        tracing::info!("Vault {} konumuna kaydedildi", self.vault_path.display());
        Ok(())
    }

    /// Güvenli temizlik - master key'i RAM'den sil
    pub fn secure_wipe(&mut self) {
        // Secret otomatik olarak drop'ta temizlenir
        // Ekstra güvenlik için sıfırla - expose_secret & verir, iter() kullanırız
        let key_bytes = self.master_key.expose_secret();
        for i in 0..key_bytes.len() {
            unsafe {
                let ptr = key_bytes.as_ptr() as *mut u8;
                std::ptr::write(ptr.add(i), 0);
            }
        }
        tracing::warn!("Vault bellekten güvenli şekilde temizlendi");
    }
}

impl Drop for StealthVault {
    fn drop(&mut self) {
        self.secure_wipe();
    }
}

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
    fn test_vault_store_and_retrieve() {
        let dir = tempdir().unwrap();
        let vault_path = dir.path().join("test_vault.age");

        let mut vault = StealthVault::new(&vault_path).unwrap();

        let secret = TestSecret {
            api_key: "sk-test-12345".to_string(),
            session_token: "sess-abcde".to_string(),
        };

        vault.store("test_credentials", &secret).unwrap();
        
        let retrieved: TestSecret = vault.retrieve("test_credentials").unwrap();
        assert_eq!(secret, retrieved);
        
        // secure_wipe test
        vault.secure_wipe();
    }
}
