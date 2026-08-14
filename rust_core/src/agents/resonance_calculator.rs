use ndarray::{Array1, ArrayView1};

/// Resonance Calculator Ajanı
/// Kullanıcı ve hedef vektörleri arasındaki kosinüs benzerliğini hesaplar.
/// Ortak veri yoksa asla sahte skor uydurmaz (0.0 döner).
pub struct ResonanceCalculator;

impl ResonanceCalculator {
    pub fn new() -> Self {
        Self
    }

    /// Kosinüs benzerliği hesaplar
    /// Vektörler boş veya uyumsuz ise 0.0 döner (sahte skor üretmez)
    pub fn calculate_resonance(&self, user_vector: &[f64], target_vector: &[f64]) -> f64 {
        // Veri yoksa sahte skor üretme
        if user_vector.is_empty() || target_vector.is_empty() {
            return 0.0;
        }

        // Vektör boyutları eşleşmeli
        if user_vector.len() != target_vector.len() {
            return 0.0;
        }

        let user_array: Array1<f64> = Array1::from_vec(user_vector.to_vec());
        let target_array: Array1<f64> = Array1::from_vec(target_vector.to_vec());

        Self::cosine_similarity(user_array.view(), target_array.view())
    }

    /// Kosinüs benzerliği formülü
    fn cosine_similarity(a: ArrayView1<f64>, b: ArrayView1<f64>) -> f64 {
        let dot_product = a.dot(&b);
        let magnitude_a = a.dot(&a).sqrt();
        let magnitude_b = b.dot(&b).sqrt();

        // Sıfıra bölme hatasını önle
        if magnitude_a == 0.0 || magnitude_b == 0.0 {
            return 0.0;
        }

        let similarity = dot_product / (magnitude_a * magnitude_b);
        
        // Sonucu [-1, 1] aralığında sınırla
        similarity.max(-1.0).min(1.0)
    }
}

impl Default for ResonanceCalculator {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_perfect_match() {
        let calc = ResonanceCalculator::new();
        let v1 = vec![1.0, 2.0, 3.0];
        let v2 = vec![1.0, 2.0, 3.0];
        
        let result = calc.calculate_resonance(&v1, &v2);
        assert!((result - 1.0).abs() < 1e-10); // Mükemmel eşleşme = 1.0
    }

    #[test]
    fn test_no_match() {
        let calc = ResonanceCalculator::new();
        let v1 = vec![1.0, 0.0, 0.0];
        let v2 = vec![0.0, 1.0, 0.0];
        
        let result = calc.calculate_resonance(&v1, &v2);
        assert_eq!(result, 0.0); // Dik vektörler = 0.0
    }

    #[test]
    fn test_empty_vectors() {
        let calc = ResonanceCalculator::new();
        let v1: Vec<f64> = vec![];
        let v2: Vec<f64> = vec![];
        
        let result = calc.calculate_resonance(&v1, &v2);
        assert_eq!(result, 0.0); // Boş vektör = 0.0 (sahte skor yok)
    }

    #[test]
    fn test_mismatched_lengths() {
        let calc = ResonanceCalculator::new();
        let v1 = vec![1.0, 2.0];
        let v2 = vec![1.0, 2.0, 3.0];
        
        let result = calc.calculate_resonance(&v1, &v2);
        assert_eq!(result, 0.0); // Uyuşmaz uzunluk = 0.0 (sahte skor yok)
    }

    #[test]
    fn test_opposite_directions() {
        let calc = ResonanceCalculator::new();
        let v1 = vec![1.0, 0.0];
        let v2 = vec![-1.0, 0.0];
        
        let result = calc.calculate_resonance(&v1, &v2);
        assert!((result + 1.0).abs() < 1e-10); // Zıt yön = -1.0
    }
}
