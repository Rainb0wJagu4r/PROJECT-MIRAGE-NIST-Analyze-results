import math
import numpy as np
from scipy.special import gammaincc

def norm_cdf(x: float) -> float:
    """Standard normal cumulative distribution function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def frequency_monobit_test(bits: np.ndarray) -> tuple[float, bool, str]:
    """
    1. Frequency (Monobit) Test
    Checks if the proportion of zeroes and ones is approximately 0.5.
    """
    n = len(bits)
    if n == 0:
        return 0.0, False, "Empty sequence"
    
    # Convert 0 to -1 and 1 to 1
    y = 2 * bits.astype(np.int8) - 1
    s_n = np.sum(y)
    s_obs = abs(s_n) / math.sqrt(n)
    p_value = math.erfc(s_obs / math.sqrt(2.0))
    
    passed = p_value >= 0.01
    ones_ratio = np.sum(bits) / n
    detail = (f"Sequence length (n): {n}\n"
              f"Ones ratio: {ones_ratio:.4f}\n"
              f"Sum statistic (S_n): {s_n}\n"
              f"Test statistic (S_obs): {s_obs:.4f}\n"
              f"P-value: {p_value:.6f}")
    return p_value, passed, detail

def frequency_block_test(bits: np.ndarray, block_size: int = 128) -> tuple[float, bool, str]:
    """
    2. Frequency Test within a Block (Block Frequency Test)
    Checks if the density of ones in blocks of size M is approximately M/2.
    """
    n = len(bits)
    if n < block_size or block_size <= 0:
        return 0.0, False, f"Sequence length ({n}) too small for block size ({block_size})"
        
    num_blocks = n // block_size
    # Reshape and compute proportion of ones in each block
    blocks = bits[:num_blocks * block_size].reshape((num_blocks, block_size))
    block_proportions = np.sum(blocks, axis=1) / block_size
    
    # Compute chi-square statistic
    chi_sq = 4.0 * block_size * np.sum((block_proportions - 0.5) ** 2)
    p_value = gammaincc(num_blocks / 2.0, chi_sq / 2.0)
    
    passed = p_value >= 0.01
    detail = (f"Block size (M): {block_size}\n"
              f"Number of blocks (N): {num_blocks}\n"
              f"Chi-square statistic: {chi_sq:.4f}\n"
              f"P-value: {p_value:.6f}")
    return p_value, passed, detail

def runs_test(bits: np.ndarray) -> tuple[float, bool, str]:
    """
    3. Runs Test
    Checks if the total number of runs (consecutive identical bits) is as expected.
    """
    n = len(bits)
    if n == 0:
        return 0.0, False, "Empty sequence"
        
    # Proportion of ones
    pi = np.sum(bits) / n
    
    # Prerequisite: Frequency test check
    # If the frequency of ones is not close to 0.5, the runs test is not applicable.
    freq_deviation = abs(pi - 0.5)
    threshold = 2.0 / math.sqrt(n)
    if freq_deviation >= threshold:
        detail = (f"Frequency deviation (|pi - 0.5| = {freq_deviation:.4f}) "
                  f"exceeds threshold ({threshold:.4f}).\n"
                  f"Runs test is not applicable. P-value set to 0.0.")
        return 0.0, False, detail
        
    # Count runs (number of changes + 1)
    # y[i] != y[i-1]
    changes = np.sum(bits[:-1] != bits[1:])
    observed_runs = changes + 1
    
    # Expected runs
    expected_runs = 2.0 * n * pi * (1.0 - pi)
    
    # Denominator
    denominator = 2.0 * math.sqrt(2.0 * n) * pi * (1.0 - pi)
    if denominator == 0:
        return 0.0, False, "Zero denominator in runs calculation"
        
    p_value = math.erfc(abs(observed_runs - expected_runs) / denominator)
    passed = p_value >= 0.01
    
    detail = (f"Ones ratio (pi): {pi:.4f}\n"
              f"Observed runs: {observed_runs}\n"
              f"Expected runs: {expected_runs:.2f}\n"
              f"P-value: {p_value:.6f}")
    return p_value, passed, detail

def longest_run_ones_test(bits: np.ndarray) -> tuple[float, bool, str]:
    """
    4. Test for the Longest Run of Ones in a Block
    Checks if the longest run of ones in blocks matches expectations.
    """
    n = len(bits)
    
    # Determine parameters M, K, and probabilities based on length n
    if n < 128:
        return 0.0, False, f"Sequence length ({n}) too small (min 128 required)"
    elif n < 6272:
        block_size = 8
        K = 3
        expected_pi = [0.2148, 0.3672, 0.2305, 0.1875]
        # Bins: <=1, 2, 3, >=4
        def get_bin(run_len):
            if run_len <= 1: return 0
            if run_len == 2: return 1
            if run_len == 3: return 2
            return 3
    elif n < 750000:
        block_size = 128
        K = 5
        expected_pi = [0.1174, 0.2430, 0.2493, 0.1752, 0.1027, 0.1124]
        # Bins: <=4, 5, 6, 7, 8, >=9
        def get_bin(run_len):
            if run_len <= 4: return 0
            if run_len >= 9: return 5
            return run_len - 4
    else:
        block_size = 10000
        K = 6
        expected_pi = [0.0882, 0.2092, 0.2483, 0.1933, 0.1208, 0.0675, 0.0727]
        # Bins: <=10, 11, 12, 13, 14, 15, >=16
        def get_bin(run_len):
            if run_len <= 10: return 0
            if run_len >= 16: return 6
            return run_len - 10
            
    num_blocks = n // block_size
    counts = np.zeros(K + 1, dtype=int)
    
    # Process each block
    for i in range(num_blocks):
        block = bits[i * block_size : (i + 1) * block_size]
        # Compute longest run of ones in this block
        max_run = 0
        current_run = 0
        for bit in block:
            if bit == 1:
                current_run += 1
                if current_run > max_run:
                    max_run = current_run
            else:
                current_run = 0
        counts[get_bin(max_run)] += 1
        
    # Calculate chi-square
    expected_counts = num_blocks * np.array(expected_pi)
    chi_sq = np.sum(((counts - expected_counts) ** 2) / expected_counts)
    p_value = gammaincc(K / 2.0, chi_sq / 2.0)
    
    passed = p_value >= 0.01
    
    counts_str = ", ".join(f"Bin {i}: {c}" for i, c in enumerate(counts))
    detail = (f"Sequence length (n): {n}\n"
              f"Block size (M): {block_size}\n"
              f"Number of blocks (N): {num_blocks}\n"
              f"Observed counts: {counts_str}\n"
              f"Chi-square statistic: {chi_sq:.4f}\n"
              f"P-value: {p_value:.6f}")
    return p_value, passed, detail

def spectral_test(bits: np.ndarray) -> tuple[float, bool, str]:
    """
    5. Discrete Fourier Transform (Spectral) Test
    Detects periodic patterns using FFT.
    """
    n = len(bits)
    if n < 16:
        return 0.0, False, "Sequence too short for FFT (min 16 required)"
        
    # Convert to +1 / -1
    y = 2 * bits.astype(float) - 1
    # FFT
    s = np.fft.fft(y)
    # Modulus of first half
    m = np.abs(s)[:n // 2]
    
    # Threshold
    t = math.sqrt(2.995732274 * n)
    # Expected number of peaks under threshold (95%)
    n0 = 0.95 * n / 2.0
    # Observed number of peaks under threshold
    n1 = np.sum(m < t)
    
    # Deviation
    d = (n1 - n0) / math.sqrt(n * 0.95 * 0.05 / 4.0)
    p_value = math.erfc(abs(d) / math.sqrt(2.0))
    passed = p_value >= 0.01
    
    detail = (f"Sequence length (n): {n}\n"
              f"Threshold (T): {t:.4f}\n"
              f"Expected peaks < T (N0): {n0:.1f}\n"
              f"Observed peaks < T (N1): {n1}\n"
              f"Deviation (d): {d:.4f}\n"
              f"P-value: {p_value:.6f}")
    return p_value, passed, detail

def cumulative_sums_test(bits: np.ndarray, mode: int = 0) -> tuple[float, bool, str]:
    """
    6. Cumulative Sums (Cusum) Test
    Checks the maximum excursion of a random walk.
    mode = 0 (Forward), mode = 1 (Backward)
    """
    n = len(bits)
    if n == 0:
        return 0.0, False, "Empty sequence"
        
    # Reverse if backward mode
    data = bits[::-1] if mode == 1 else bits
    
    # Convert to +1 / -1 and compute cumulative sum
    y = 2 * data.astype(int) - 1
    s = np.cumsum(y)
    
    z = np.max(np.abs(s))
    if z == 0:
        return 0.0, False, "Max excursion is 0 (totally flat sequence). P-value: 0.0"
        
    # Calculate P-value summation
    # Limit ranges for k
    start_1 = int(math.floor((-n / z + 1) / 4.0))
    end_1 = int(math.floor((n / z - 1) / 4.0))
    start_2 = int(math.floor((-n / z - 3) / 4.0))
    end_2 = int(math.floor((n / z - 1) / 4.0))
    
    sqrt_n = math.sqrt(n)
    
    sum1 = 0.0
    for k in range(start_1, end_1 + 1):
        term1 = norm_cdf((4 * k + 1) * z / sqrt_n)
        term2 = norm_cdf((4 * k - 1) * z / sqrt_n)
        sum1 += (term1 - term2)
        
    sum2 = 0.0
    for k in range(start_2, end_2 + 1):
        term1 = norm_cdf((4 * k + 3) * z / sqrt_n)
        term2 = norm_cdf((4 * k + 1) * z / sqrt_n)
        sum2 += (term1 - term2)
        
    p_value = 1.0 - sum1 + sum2
    # Bound to [0.0, 1.0] in case of small floating precision errors
    p_value = max(0.0, min(1.0, p_value))
    
    passed = p_value >= 0.01
    mode_str = "Backward" if mode == 1 else "Forward"
    detail = (f"Mode: {mode_str}\n"
              f"Sequence length (n): {n}\n"
              f"Max excursion (z): {z}\n"
              f"P-value: {p_value:.6f}")
    return p_value, passed, detail

def approximate_entropy_test(bits: np.ndarray, block_size: int = 3) -> tuple[float, bool, str]:
    """
    7. Approximate Entropy Test
    Checks frequency of overlapping patterns of length m.
    """
    n = len(bits)
    m = block_size
    if n < (2 ** m):
        return 0.0, False, f"Sequence length ({n}) too small for block size ({m}) (min {2**m} required)"
        
    def phi_m(x, pattern_len):
        l = len(x)
        # Pad with first pattern_len - 1 elements
        padded = np.concatenate([x, x[:pattern_len - 1]])
        
        # Fast conversion of sliding blocks to integers
        vals = np.zeros(l, dtype=np.int32)
        for j in range(pattern_len):
            vals += (padded[j:j+l].astype(np.int32) << (pattern_len - 1 - j))
            
        counts = np.bincount(vals, minlength=2**pattern_len)
        probs = counts / l
        # Calculate entropy (ignoring zero counts)
        non_zero = probs[probs > 0]
        return np.sum(non_zero * np.log(non_zero))

    phi_current = phi_m(bits, m)
    phi_next = phi_m(bits, m + 1)
    
    apen = phi_current - phi_next
    chi_sq = 2.0 * n * (math.log(2.0) - apen)
    
    dof = 2 ** (m - 1)
    p_value = gammaincc(dof, chi_sq / 2.0)
    passed = p_value >= 0.01
    
    detail = (f"Block length (m): {m}\n"
              f"Sequence length (n): {n}\n"
              f"Approximate Entropy (ApEn): {apen:.6f}\n"
              f"Chi-square statistic: {chi_sq:.4f}\n"
              f"Degrees of freedom: {2 ** m}\n"
              f"P-value: {p_value:.6f}")
    return p_value, passed, detail

def serial_test(bits: np.ndarray, block_size: int = 3) -> tuple[tuple[float, float], bool, str]:
    """
    8. Serial Test
    Tests frequency of all 2^m patterns. Returns P1 and P2.
    """
    n = len(bits)
    m = block_size
    if m < 3:
        return (0.0, 0.0), False, "Block length m must be >= 3 for serial test"
    if n < (2 ** m):
        return (0.0, 0.0), False, f"Sequence length ({n}) too small for block size ({m})"
        
    def psi_sq_m(x, pattern_len):
        l = len(x)
        # Pad with first pattern_len - 1 elements
        padded = np.concatenate([x, x[:pattern_len - 1]])
        
        # Fast conversion of sliding blocks to integers
        vals = np.zeros(l, dtype=np.int32)
        for j in range(pattern_len):
            vals += (padded[j:j+l].astype(np.int32) << (pattern_len - 1 - j))
            
        counts = np.bincount(vals, minlength=2**pattern_len)
        psi_sq = (2**pattern_len / l) * np.sum(counts.astype(float) ** 2) - l
        return psi_sq

    psi_m = psi_sq_m(bits, m)
    psi_m1 = psi_sq_m(bits, m - 1) if m - 1 > 0 else 0.0
    psi_m2 = psi_sq_m(bits, m - 2) if m - 2 > 0 else 0.0
    
    del_psi = psi_m - psi_m1
    del2_psi = psi_m - 2.0 * psi_m1 + psi_m2
    
    p_val1 = gammaincc(2**(m-2), del_psi / 2.0)
    p_val2 = gammaincc(2**(m-3), del2_psi / 2.0)
    
    passed = (p_val1 >= 0.01) and (p_val2 >= 0.01)
    
    detail = (f"Block length (m): {m}\n"
              f"Psi^2_{m}: {psi_m:.4f}\n"
              f"Psi^2_{m-1}: {psi_m1:.4f}\n"
              f"Psi^2_{m-2}: {psi_m2:.4f}\n"
              f"Delta Psi^2 (nabla): {del_psi:.4f}\n"
              f"Delta^2 Psi^2 (nabla^2): {del2_psi:.4f}\n"
              f"P-value 1: {p_val1:.6f}\n"
              f"P-value 2: {p_val2:.6f}")
    return (p_val1, p_val2), passed, detail

def non_overlapping_template_matching_test(bits: np.ndarray, template_str: str = "000000001", block_size: int = 1032) -> tuple[float, bool, str]:
    """
    9. Non-overlapping Template Matching Test
    Counts occurrences of non-periodic templates.
    """
    n = len(bits)
    template = np.array([int(c) for c in template_str if c in ('0', '1')], dtype=np.uint8)
    m = len(template)
    
    if m == 0:
        return 0.0, False, "Invalid empty template string"
        
    num_blocks = n // block_size
    if num_blocks == 0:
        return 0.0, False, f"Sequence length ({n}) too small for block size ({block_size})"
        
    # Convert bits to ASCII string representation for C-speed counting
    bit_chars = (bits[:num_blocks * block_size] + 48).tobytes().decode('ascii')
    counts = np.zeros(num_blocks, dtype=int)
    for i in range(num_blocks):
        sub = bit_chars[i * block_size : (i + 1) * block_size]
        counts[i] = sub.count(template_str)
        
    # Expected mean and variance (NIST SP 800-22 formulas)
    mu = (block_size - m + 1) / (2.0 ** m)
    variance = block_size * ((1.0 / (2.0 ** m)) - ((2.0 * m - 1.0) / (2.0 ** (2.0 * m))))
    
    if variance == 0:
        return 0.0, False, "Zero variance in template matching calculation"
        
    # Compute chi-square
    chi_sq = np.sum(((counts - mu) ** 2) / variance)
    p_value = gammaincc(num_blocks / 2.0, chi_sq / 2.0)
    passed = p_value >= 0.01
    
    counts_str = ", ".join(f"Block {i}: {c}" for i, c in enumerate(counts))
    detail = (f"Template: {template_str} (length {m})\n"
              f"Block size (M): {block_size}\n"
              f"Number of blocks (N): {num_blocks}\n"
              f"Expected mean per block (mu): {mu:.4f}\n"
              f"Expected variance: {variance:.4f}\n"
              f"Observed counts: {counts_str}\n"
              f"Chi-square statistic: {chi_sq:.4f}\n"
              f"P-value: {p_value:.6f}")
    return p_value, passed, detail
