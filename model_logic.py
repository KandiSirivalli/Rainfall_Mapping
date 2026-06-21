import numpy as np

class DeepRainModel:
    """
    Pure NumPy implementation of the DeepRain-Ops inference engine.
    Supports Section 7.2.2 (Layer Freezing) and 7.2.3 (AdaBN).
    """
    def __init__(self, layer_dims):
        # Initialize weights for a multi-layer network
        # layer_dims example: [4096, 128, 64, 32, 1] 
        # (Input: 64x64 flattened, Output: 1 mm/hr)
        self.weights = []
        self.biases = []
        self.frozen_limit = 12 # Protocol 7.2.2: First 12 layers frozen
        
        for i in range(len(layer_dims) - 1):
            # He initialization for ReLU
            w = np.random.randn(layer_dims[i], layer_dims[i+1]) * np.sqrt(2/layer_dims[i])
            b = np.zeros((1, layer_dims[i+1]))
            self.weights.append(w)
            self.biases.append(b)

    def relu(self, x):
        return np.maximum(0, x)

    def forward(self, x):
        """Standard Forward Pass"""
        activations = [x]
        for i in range(len(self.weights)):
            z = np.dot(activations[-1], self.weights[i]) + self.biases[i]
            # Final layer is linear for regression (Rainfall Rate)
            a = self.relu(z) if i < len(self.weights) - 1 else z
            activations.append(a)
        return activations

    def fine_tune_step(self, x, y_true, lr=0.0001):
        """
        Implementation of 7.2.2: Target Site Fine-Tuning.
        Only updates weights for layers index >= 12.
        """
        acts = self.forward(x)
        error = acts[-1] - y_true
        delta = error

        for i in reversed(range(len(self.weights))):
            if i >= self.frozen_limit:
                # Calculate Gradients
                grad_w = np.dot(acts[i].T, delta)
                grad_b = np.sum(delta, axis=0, keepdims=True)
                
                # Update weights (Tuning only regression layers)
                self.weights[i] -= lr * grad_w
                self.biases[i] -= lr * grad_b
            
            # Backpropagate error to frozen layers (without updating them)
            if i > 0:
                # Derivative of ReLU
                delta = np.dot(delta, self.weights[i].T) * (acts[i] > 0)
        
        return np.mean(np.square(error))

    def apply_adabn(self, local_data):
        """
        Implementation of 7.2.3: Adaptive Batch Normalization.
        Adjusts global features to local site statistics.
        """
        # BN_adapted(x) = (x - μ_target) / √(σ²_target + ε)
        mu_target = np.mean(local_data, axis=0)
        sigma_target = np.std(local_data, axis=0)
        epsilon = 1e-5
        
        # This statistics shift aligns S-band/C-band differences (7.4.2)
        normalized_data = (local_data - mu_target) / np.sqrt(sigma_target**2 + epsilon)
        return normalized_data, mu_target, sigma_target

def quantile_mapping(z_source, cdf_source, inv_cdf_target):
    """
    Implementation of 7.4.2: Quantile Mapping for Frequency Calibration.
    Aligns C-band (France/Japan) to S-band (NEXRAD) scales.
    """
    # Simplified mapping logic
    # Z_corrected = F_target^-1 ( F_source ( Z_source ) )
    return inv_cdf_target(cdf_source(z_source))

# Example Usage for the Flask App
def get_initialized_model():
    # Input: 4 polarimetric variables flattened from a small patch
    return DeepRainModel([256, 128, 64, 32, 16, 8, 4, 2, 1, 1, 1, 1, 1, 1, 1])