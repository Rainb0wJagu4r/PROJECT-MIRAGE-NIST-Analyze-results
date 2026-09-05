import os
import sys
import numpy as np
import math

import file_parser
import nist_tests

def run_audit(file_path, output_path, alpha=0.01):
    print(f"\n=======================================================")
    print(f"Auditing MirageX (WRAITH v4) file: {file_path}")
    print(f"=======================================================")
    
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return False
        
    try:
        size_bytes = os.path.getsize(file_path)
        bits = file_parser.parse_file_to_bits(file_path, "bin")
        n_bits = len(bits)
        print(f"Loaded {n_bits:,} bits ({size_bytes:,} bytes)")
        
        # Distribution metrics
        ones_count = int(np.sum(bits))
        zeros_count = n_bits - ones_count
        bit_balance = (ones_count / n_bits) * 100.0
        
        if n_bits > 1:
            if np.all(bits == bits[0]):
                corr = 1.0
            else:
                corr = float(np.corrcoef(bits[:-1], bits[1:])[0, 1])
                if math.isnan(corr):
                    corr = 0.0
        else:
            corr = 0.0
            
        print(f"Bit Balance:        {bit_balance:.4f}% ones ({ones_count:,} ones, {zeros_count:,} zeros)")
        print(f"Serial Correlation: {corr:.6f}")
        
        results = []
        detailed_logs = []
        
        def run_test(name, test_func, *args):
            print(f" -> Running {name}...")
            try:
                p_val, passed, detail = test_func(bits, *args)
                results.append((name, p_val, passed, detail))
                detailed_logs.append(f"=== {name} ===\n{detail}\n\n")
            except Exception as e:
                results.append((name, "ERROR", False, f"Exception: {str(e)}"))
                detailed_logs.append(f"=== {name} ===\nError: {str(e)}\n\n")
                
        # Execute tests
        run_test("Frequency (Monobit) Test", nist_tests.frequency_monobit_test)
        run_test("Frequency Test within a Block (M=128)", nist_tests.frequency_block_test, 128)
        run_test("Runs Test", nist_tests.runs_test)
        run_test("Longest Run of Ones in a Block", nist_tests.longest_run_ones_test)
        run_test("Discrete Fourier Transform (Spectral) Test", nist_tests.spectral_test)
        run_test("Cumulative Sums (Cusum) Test (Forward)", nist_tests.cumulative_sums_test, 0)
        run_test("Cumulative Sums (Cusum) Test (Backward)", nist_tests.cumulative_sums_test, 1)
        run_test("Approximate Entropy Test (m=3)", nist_tests.approximate_entropy_test, 3)
        run_test("Serial Test (m=3)", nist_tests.serial_test, 3)
        run_test("Non-overlapping Template Matching (template=000000001)", nist_tests.non_overlapping_template_matching_test, "000000001", 1032)
        
        # Build report
        all_passed = True
        p_values_list = []
        for name, p_val, passed, detail in results:
            if not passed:
                all_passed = False
            if isinstance(p_val, tuple):
                p_values_list.extend(p_val)
            elif isinstance(p_val, (int, float)):
                p_values_list.append(p_val)

        overall_conclusion = "STATISTICALLY RANDOM — NIST STS PASS" if all_passed else "NON-RANDOM — POTENTIAL LEAKAGE"
        min_p = min(p_values_list) if p_values_list else 0.0
        max_p = max(p_values_list) if p_values_list else 0.0

        rel_path = file_path.replace(os.path.expanduser("~"), "~")
        report_header = (
            "======================================================================\n"
            "             NIST SP 800-22 AUDIT REPORT: MIRAGEX (WRAITH v4)         \n"
            "======================================================================\n"
            f"Target File:        {rel_path}\n"
            f"Architecture:       MirageX Ultra (ML-KEM-1024 / NIST Level 5)\n"
            f"Envelope Scheme:    Argon2id + ML-KEM-1024 -> HKDF-SHA512 -> AES-256-GCM\n"
            f"File Size:          {size_bytes:,} bytes\n"
            f"Sequence Length:    {n_bits:,} bits\n"
            f"Significance Level: {alpha}\n"
            f"Bit Balance:        {bit_balance:.4f}% ones\n"
            f"Serial Correlation: {corr:.6f}\n"
            f"Minimum P-value:    {min_p:.5f}\n"
            f"Maximum P-value:    {max_p:.5f}\n"
            f"Conclusion:         {overall_conclusion}\n"
            "----------------------------------------------------------------------\n"
            "WARNING: Passing NIST statistical tests does not constitute proof of\n"
            "         cryptographic security.\n"
            "======================================================================\n\n"
        )
        
        report_summary = "SUMMARY TABLE:\n"
        report_summary += f"{'Test Name':<55} | {'P-Value(s)':<18} | {'Status':<8}\n"
        report_summary += "-" * 88 + "\n"
        
        for name, p_val, passed, detail in results:
            if isinstance(p_val, tuple):
                p_str = ", ".join(f"{p:.5f}" for p in p_val)
            elif isinstance(p_val, float):
                p_str = f"{p_val:.5f}"
            else:
                p_str = str(p_val)
                
            status = "PASS" if passed else "FAIL"
            report_summary += f"{name:<55} | {p_str:<18} | {status:<8}\n"
            
        report_summary += "\n" + "=" * 88 + "\n\n"
        report_summary += f"OVERALL AUDIT RESULT: {overall_conclusion}\n\n"
        
        full_report = report_header + report_summary + "DETAILED TEST LOGS:\n\n" + "".join(detailed_logs)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write report to .NIST file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_report)
            
        print(f"Audit completed. Report saved to: {output_path}")
        print(f"Overall Result: {'PASS' if all_passed else 'FAIL'}")
        return {
            "file": os.path.basename(file_path),
            "bits": n_bits,
            "bytes": size_bytes,
            "balance": bit_balance,
            "correlation": corr,
            "min_p": min_p,
            "max_p": max_p,
            "all_passed": all_passed,
            "results": results
        }
        
    except Exception as e:
        print(f"Error auditing file {file_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    samples_dir = os.path.join(base_dir, "test_samples")
    reports_dir = os.path.join(base_dir, "reports", "miragex_v4_pqc")
    
    files_to_audit = [
        ("sample_data.bin.wraith", "miragex_ultra_sample_data.NIST"),
        ("structured_text.txt.wraith", "miragex_ultra_structured_text.NIST"),
        ("zeroes.bin.wraith", "miragex_ultra_zeroes.NIST"),
    ]
    
    audit_summaries = []
    for in_name, out_name in files_to_audit:
        in_path = os.path.join(samples_dir, in_name)
        out_path = os.path.join(reports_dir, out_name)
        res = run_audit(in_path, out_path)
        if res:
            audit_summaries.append((in_name, res))
            
    print("\n\n" + "="*90)
    print("                      MIRAGEX (WRAITH v4) AUDIT MATRIX SUMMARY")
    print("="*90)
    print(f"{'Sample / Payload':<30} | {'Bit Balance':<12} | {'Serial Corr':<12} | {'Min P-val':<10} | {'Status'}")
    print("-" * 90)
    for name, s in audit_summaries:
        status_str = "PASS (Random)" if s["all_passed"] else "FAIL"
        print(f"{name:<30} | {s['balance']:.2f}% ones   | {s['correlation']:.6f}   | {s['min_p']:.5f}    | {status_str}")
    print("="*90)
