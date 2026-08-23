import os
import numpy as np
import file_parser
import nist_tests

def run_all_tests_on(bits: np.ndarray, name: str):
    print(f"\n======================================")
    print(f"Running NIST tests on: {name} ({len(bits)} bits)")
    print(f"======================================")
    
    # 1. Monobit
    p, passed, det = nist_tests.frequency_monobit_test(bits)
    print(f"1. Monobit: P-value={p:.6f}, Passed={passed}")
    
    # 2. Block Frequency
    p, passed, det = nist_tests.frequency_block_test(bits, block_size=16)
    print(f"2. Block Frequency (M=16): P-value={p:.6f}, Passed={passed}")
    
    # 3. Runs
    p, passed, det = nist_tests.runs_test(bits)
    print(f"3. Runs: P-value={p:.6f}, Passed={passed}")
    
    # 4. Longest Run
    p, passed, det = nist_tests.longest_run_ones_test(bits)
    print(f"4. Longest Run of 1s: P-value={p:.6f}, Passed={passed}")
    
    # 5. FFT
    p, passed, det = nist_tests.spectral_test(bits)
    print(f"5. DFT (FFT): P-value={p:.6f}, Passed={passed}")
    
    # 6. Cusum Forward
    p, passed, det = nist_tests.cumulative_sums_test(bits, mode=0)
    print(f"6. Cusum Forward: P-value={p:.6f}, Passed={passed}")
    
    # 7. Approximate Entropy
    p, passed, det = nist_tests.approximate_entropy_test(bits, block_size=2)
    print(f"7. Approx Entropy (m=2): P-value={p:.6f}, Passed={passed}")
    
    # 8. Serial
    p_tuple, passed, det = nist_tests.serial_test(bits, block_size=3)
    print(f"8. Serial (m=3): P-values={p_tuple[0]:.6f}, {p_tuple[1]:.6f}, Passed={passed}")
    
    # 9. Template Matching
    p, passed, det = nist_tests.non_overlapping_template_matching_test(bits, template_str="01", block_size=32)
    print(f"9. Template Matching ('01', M=32): P-value={p:.6f}, Passed={passed}")

def test_file_parser():
    print("\n======================================")
    print("Testing File Parser Module")
    print("======================================")
    
    # Define test patterns
    ref_bits = np.array([1, 0, 1, 1, 0, 0, 1, 1], dtype=np.uint8) # Binary representation of 0xB3 or 179
    # In binary representation, MSB-first: 10110011 -> 0xB3
    
    # 1. Test raw binary file
    bin_path = "test_data.bin"
    with open(bin_path, "wb") as f:
        f.write(bytes([0xB3]))
        
    parsed_bin = file_parser.parse_file_to_bits(bin_path, "bin")
    print(f"Raw binary parsing matches ref: {np.array_equal(parsed_bin, ref_bits)} (Parsed: {parsed_bin})")
    
    # 2. Test text bin file
    txt_path = "test_data.txt"
    with open(txt_path, "w") as f:
        f.write("1 0 1 1\n 0 0 1 1") # formatting check (whitespace ignore)
        
    parsed_txt = file_parser.parse_file_to_bits(txt_path, "txt_bin")
    print(f"Text binary parsing matches ref: {np.array_equal(parsed_txt, ref_bits)} (Parsed: {parsed_txt})")
    
    # 3. Test hex file
    hex_path = "test_data.hex"
    with open(hex_path, "w") as f:
        f.write("B3")
        
    parsed_hex = file_parser.parse_file_to_bits(hex_path, "hex")
    print(f"Hex parsing matches ref: {np.array_equal(parsed_hex, ref_bits)} (Parsed: {parsed_hex})")
    
    # Clean up
    for path in [bin_path, txt_path, hex_path]:
        if os.path.exists(path):
            os.remove(path)

if __name__ == "__main__":
    test_file_parser()
    
    # Run test on 2000 bits alternating sequence
    alt_bits = np.tile([0, 1], 1000)
    run_all_tests_on(alt_bits, "Alternating 0,1 sequence")
    
    # Run test on 2000 bits pseudorandom sequence
    np.random.seed(42)
    rand_bits = np.random.randint(0, 2, 2000, dtype=np.uint8)
    run_all_tests_on(rand_bits, "NumPy random sequence")
