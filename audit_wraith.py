import os
import sys
import numpy as np

# Add parent directory to path so we can import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import file_parser
import nist_tests

def run_audit(file_path: str, output_path: str):
    print(f"Auditing file: {file_path}")
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return False
        
    try:
        # Load and parse bits
        bits = file_parser.parse_file_to_bits(file_path, "bin")
        n_bits = len(bits)
        size_bytes = os.path.getsize(file_path)
        alpha = 0.01
        
        print(f"Loaded {n_bits:,} bits ({size_bytes:,} bytes)")
        
        # We will run all 9 tests
        results = []
        detailed_logs = []
        
        # Helper to run a test
        def run_test(name, test_func, *args):
            print(f" Running {name}...")
            try:
                p, passed, detail = test_func(bits, *args)
                results.append((name, p, passed, detail))
                detailed_logs.append(f"=== {name} ===\n{detail}\n\n")
            except Exception as ex:
                results.append((name, "ERROR", False, f"Exception: {str(ex)}"))
                detailed_logs.append(f"=== {name} ===\nError: {str(ex)}\n\n")
                
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
        for name, p_val, passed, detail in results:
            if not passed:
                all_passed = False

        overall_conclusion = "STATISTICALLY RANDOM — NIST STS PASS" if all_passed else "NON-RANDOM — POTENTIAL LEAKAGE"

        report_header = (
            "======================================================================\n"
            "                      NIST SP 800-22 AUDIT REPORT                     \n"
            "======================================================================\n"
            f"Target File:        {file_path}\n"
            f"File Size:          {size_bytes:,} bytes\n"
            f"Sequence Length:    {n_bits:,} bits\n"
            f"Significance Level: {alpha}\n"
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
        
        # Write report to .NIST file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_report)
            
        print(f"Audit completed. Report saved to: {output_path}")
        print(f"Overall Result: {'PASS' if all_passed else 'FAIL'}\n")
        return True
        
    except Exception as e:
        print(f"Error auditing file {file_path}: {str(e)}")
        return False

if __name__ == "__main__":
    # Audit 1
    run_audit(
        os.path.expanduser("~/2.wraith"), 
        os.path.expanduser("~/2.wraith.NIST")
    )
    
    # Audit 2
    run_audit(
        os.path.expanduser("~/Downloads/untitled folder/2.wraith"), 
        os.path.expanduser("~/Downloads/untitled folder/2.wraith.NIST")
    )
