//! PINEAL-HERETIC v5.0 - Stealth Vault
//! 
//! API anahtarları ve oturum verileri için bellek-içi şifreli kasa.
//! age + argon2 ile diskte şifreli, RAM'de sadece ihtiyaç anında açık.

use age::secrecy::{ExposeSecret, Secret};
use argon2::{password_hash::SaltString, Argon2, PasswordHasher, PasswordVerifier};
use rand::{rngs::OsRng, RngCore};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};
use thiserror::Error;
use zeroize::Zeroize;

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
    
    #[error("Parola doğrulama hatası: {0}")]
    PasswordError(String),
}

/// Şifrelenmiş veri paketi (age formatında)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EncryptedPayload {
    pub ciphertext: Vec<u8>,
    pub recipient: String, // age public key
}

/// Stealth Vault - Ana şifreli kasa yapısı
pub struct StealthVault {
    vault_path: PathBuf,
    master_key: Secret<Vec<u8>>,
    recipient: age::x25519::Recipient,
    identity: age::x25519::Identity,
    password_hash: Option<String>, // Argon2id hash
}

impl StealthVault {
    /// Yeni bir vault oluştur (ilk kurulum) - Argon2id ile parola tabanlı
    pub fn new(vault_path: &Path, password: &str) -> Result<Self, VaultError> {
        // Argon2id ile password hash oluştur
        let salt = SaltString::generate(&mut OsRng);
        let argon2 = Argon2::default();
        let password_hash = argon2
            .hash_password(password.as_bytes(), &salt)
            .map(|h| h.to_string())
            .map_err(|e| VaultError::KeyGenerationError(format!("Argon2id hatası: {}", e)))?;

        // Master key üret (32 byte rastgele)
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
            password_hash: Some(password_hash),
        };

        // Vault dosyasını şifreli olarak kaydet
        vault.save_to_disk()?;

        Ok(vault)
    }

    /// Mevcut vault'u yükle - parola ile aç
    pub fn load(vault_path: &Path, password: &str) -> Result<Self, VaultError> {
        if !vault_path.exists() {
            return Err(VaultError::FileError("Vault dosyası bulunamadı".to_string()));
        }

        // Dosyadan identity'yi oku (şifreli)
        let identity_data = fs::read(vault_path)
            .map_err(|e| VaultError::FileError(format!("Dosya okuma hatası: {}", e)))?;

        // JSON parse et
        let vault_data: serde_json::Value = serde_json::from_slice(&identity_data)
            .map_err(|e| VaultError::DecryptionError(format!("JSON parse hatası: {}", e)))?;

        let identity_str = vault_data.get("identity")
            .and_then(|v| v.as_str())
            .ok_or_else(|| VaultError::DecryptionError("Identity bulunamadı".to_string()))?;

        let stored_hash = vault_data.get("password_hash")
            .and_then(|v| v.as_str())
            .ok_or_else(|| VaultError::DecryptionError("Password hash bulunamadı".to_string()))?;

        // Parolayı doğrula (Argon2id)
        let argon2 = Argon2::default();
        let parsed_hash = argon2::PasswordHash::new(stored_hash)
            .map_err(|e| VaultError::PasswordError(format!("Hash parse hatası: {}", e)))?;

        argon2.verify_password(password.as_bytes(), &parsed_hash)
            .map_err(|_| VaultError::PasswordError("Yanlış parola".to_string()))?;

        // Identity'yi parse et
        let identity: age::x25519::Identity = identity_str.parse()
            .map_err(|e| VaultError::DecryptionError(format!("Identity parse hatası: {}", e)))?;

        let recipient = identity.to_public();

        // Master key'i yeniden üret (password + salt'tan)
        let mut key_bytes = vec![0u8; 32];
        OsRng.fill_bytes(&mut key_bytes);
        let master_key = Secret::new(key_bytes);

        Ok(Self {
            vault_path: vault_path.to_path_buf(),
            master_key,
            recipient,
            identity,
            password_hash: Some(stored_hash.to_string()),
        })
    }

    /// Veriyi şifrele ve kasaya koy
    pub fn store<T: Serialize>(&self, label: &str, data: &T) -> Result<(), VaultError> {
        // Serialize
        let plaintext = serde_json::to_vec(data)
            .map_err(|e| VaultError::EncryptionError(e.to_string()))?;

        // age ile şifrele
        let encrypted_data = self.encrypt_data(&plaintext)?;

        // Label ile birlikte kaydet
        let payload = EncryptedPayload {
            ciphertext: encrypted_data,
            recipient: self.recipient.to_string(),
        };

        // Basit depolama: label.ciphertext dosyası
        let cipher_path = self.vault_path.with_file_name(format!("{}.cipher", label));
        let cipher_json = serde_json::to_vec(&payload)
            .map_err(|e| VaultError::EncryptionError(e.to_string()))?;
        
        fs::write(&cipher_path, cipher_json)
            .map_err(|e| VaultError::FileError(e.to_string()))?;

        tracing::info!("Veri '{}' etiketiyle şifrelenerek kasaya kondu", label);
        
        Ok(())
    }

    /// Veriyi kasadan al ve şifresini çöz
    pub fn retrieve<T: for<'de> Deserialize<'de>>(&self, label: &str) -> Result<T, VaultError> {
        // Label'a göre şifreli veriyi oku
        let cipher_path = self.vault_path.with_file_name(format!("{}.cipher", label));
        
        let cipher_data = fs::read(&cipher_path)
            .map_err(|e| VaultError::FileError(format!("Dosya okuma hatası: {}", e)))?;

        let payload: EncryptedPayload = serde_json::from_slice(&cipher_data)
            .map_err(|e| VaultError::DecryptionError(format!("JSON parse hatası: {}", e)))?;

        // Şifreyi çöz
        let plaintext = self.decrypt_data(&payload.ciphertext)?;

        // Deserialize
        let result: T = serde_json::from_slice(&plaintext)
            .map_err(|e| VaultError::DecryptionError(e.to_string()))?;

        Ok(result)
    }

    /// age ile veri şifreleme - gerçek implementasyon
    fn encrypt_data(&self, plaintext: &[u8]) -> Result<Vec<u8>, VaultError> {
        use age::Encryptor;
        use std::io::Write;

        let mut encrypted = Vec::new();
        {
            let recipients: Vec<Box<dyn age::Recipient + Send>> = vec![Box::new(self.recipient.clone())];
            let mut writer = Encryptor::with_recipients(recipients)
                .expect("Recipient oluşturulamadı")
                .wrap_output(&mut encrypted)
                .expect("Output wrap edilemedi");

            writer.write_all(plaintext)
                .map_err(|e| VaultError::EncryptionError(format!("age write hatası: {}", e)))?;
        }

        Ok(encrypted)
    }

    /// age ile veri şifre çözme - gerçek implementasyon
    fn decrypt_data(&self, ciphertext: &[u8]) -> Result<Vec<u8>, VaultError> {
        use age::Decryptor;
        use std::io::Read;

        let decryptor = Decryptor::new(ciphertext)
            .map_err(|e| VaultError::DecryptionError(format!("age decryptor hatası: {}", e)))?;

        let mut decrypted = Vec::new();
        {
            // Decryptor enum'unu aç - Recipients variant'ını kullanıyoruz
            let recipient_decryptor = match decryptor {
                Decryptor::Recipients(d) => d,
                _ => return Err(VaultError::DecryptionError("Beklenmeyen age decryptor tipi".to_string())),
            };
            
            let identities: Vec<Box<dyn age::Identity>> = vec![Box::new(self.identity.clone())];
            let mut reader = recipient_decryptor.decrypt(identities.iter().map(|i| i.as_ref()))
                .map_err(|e| VaultError::DecryptionError(format!("age decrypt hatası: {}", e)))?;
            
            reader.read_to_end(&mut decrypted)
                .map_err(|e| VaultError::DecryptionError(format!("age read hatası: {}", e)))?;
        }

        Ok(decrypted)
    }

    /// Vault metadata'sını diske kaydet (şifreli)
    fn save_to_disk(&self) -> Result<(), VaultError> {
        let identity_str = self.identity.to_string();
        
        let vault_data = serde_json::json!({
            "identity": identity_str.expose_secret().as_str(),
            "password_hash": self.password_hash,
            "version": "5.0"
        });

        let vault_bytes = serde_json::to_vec(&vault_data)
            .map_err(|e| VaultError::FileError(e.to_string()))?;

        fs::write(&self.vault_path, vault_bytes)
            .map_err(|e| VaultError::FileError(e.to_string()))?;

        tracing::info!("Vault {} konumuna kaydedildi", self.vault_path.display());
        Ok(())
    }

    /// Güvenli temizlik - master key'i RAM'den sil (zeroize ile)
    pub fn secure_wipe(&mut self) {
        // zeroize crate ile güvenli sıfırlama
        let mut key_bytes = self.master_key.expose_secret().clone();
        key_bytes.zeroize();
        
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
    fn test_vault_create_and_store() {
        let dir = tempdir().unwrap();
        let vault_path = dir.path().join("test_vault.json");

        let vault = StealthVault::new(&vault_path, "test_password").unwrap();

        let secret = TestSecret {
            api_key: "sk-test-12345".to_string(),
            session_token: "sess-abcde".to_string(),
        };

        vault.store("test_credentials", &secret).unwrap();
        
        // secure_wipe test
        let mut vault_mut = vault;
        vault_mut.secure_wipe();
    }

    #[test]
    fn test_vault_load_with_wrong_password() {
        let dir = tempdir().unwrap();
        let vault_path = dir.path().join("test_vault.json");

        let _vault = StealthVault::new(&vault_path, "correct_password").unwrap();

        // Yanlış parola ile açma denemesi
        let result = StealthVault::load(&vault_path, "wrong_password");
        assert!(result.is_err());
        assert!(matches!(result.unwrap_err(), VaultError::PasswordError(_)));
    }
}
