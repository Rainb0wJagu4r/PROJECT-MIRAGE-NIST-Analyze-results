# NIST SP 800-22 Randomness Analyzer & Cryptographic Audit Tool

A self-contained, high-performance Python application designed to evaluate the statistical randomness of encrypted files, cryptographic ciphers, and random number generator (RNG) outputs. It implements a robust subset of the **NIST SP 800-22** statistical test suite.

This project includes both a responsive **Desktop GUI** (with background multi-threading, live progress, and summary visualizations) and a **CLI Auditor** to batch-process files and export official audit reports.

---

## 📂 Directory Structure

*   [`gui.py`](gui.py) - Desktop application built with Python's native Tkinter. Handles file loading, parameter settings, background execution, summary tables, log views, and report generation.
*   [`nist_tests.py`](nist_tests.py) - Mathematical implementations of the 9 core NIST SP 800-22 tests using NumPy and SciPy.
*   [`file_parser.py`](file_parser.py) - Ingests raw binary bytes (`.bin`/`.dat`), ASCII bits (text files with `'0'` and `'1'` characters), and hexadecimal strings. Includes auto-detection.
*   [`audit_wraith.py`](audit_wraith.py) - CLI script to automate audit runs on `.wraith` encrypted envelopes and output official audit logs.
*   [`test_nist.py`](test_nist.py) - Automated validation script running unit tests on the parser and test suite using random and alternating patterns.
*   `reports/` - Subdirectory containing the official `.NIST` audit logs of our cryptographic files.
    *   [`reports/2_wraith_home.NIST`](reports/2_wraith_home.NIST) - Audit log for the home directory `2.wraith` envelope (16,814,104 bits).
    *   [`reports/2_wraith_downloads.NIST`](reports/2_wraith_downloads.NIST) - Audit log for the downloads directory `2.wraith` copy (14,243,008 bits).
*   [`requirements.txt`](requirements.txt) - Python dependencies (`numpy` and `scipy`).
*   [`run.sh`](run.sh) - Helper bash script to execute the GUI application.
*   [`LICENSE`](LICENSE) - Open source MIT License details.

---

## ⚙️ Setup and Installation

### 1. Prerequisites
Ensure you have **Python 3.9+** or **Python 3.13** installed (with `tkinter` configured).

### 2. Install Dependencies
Create a virtual environment to keep your system clean, then install `numpy` and `scipy`:
```bash
# Create virtual environment
python3 -m venv venv

# Install requirements
venv/bin/pip install -r requirements.txt
```

---

## 🚀 How to Run

### Run the GUI Application
Launch the graphical interface using the helper script:
```bash
chmod +x run.sh
./run.sh
```

### Run the CLI Auditor
Perform the cryptographic audit on the `.wraith` files and generate reports:
```bash
venv/bin/python audit_wraith.py
```

### Run Unit Tests
Verify the code correctness and view test runs:
```bash
venv/bin/python test_nist.py
```

---

## 📈 Implemented NIST SP 800-22 Tests

The following tests are implemented within [`nist_tests.py`](nist_tests.py) with a default significance level of $\alpha = 0.01$:

1.  **Frequency (Monobit) Test:** Evaluates if the proportion of zeroes and ones is approximately 0.5.
2.  **Frequency Test within a Block (M=128):** Checks the density of ones inside block segments of size $M$.
3.  **Runs Test:** Measures the frequency of identical consecutive bits (runs).
4.  **Longest Run of Ones in a Block:** Examines if the longest consecutive block runs of ones match theoretical expectations.
5.  **Discrete Fourier Transform (Spectral) Test:** Detects periodic features (repetitive patterns) using FFT.
6.  **Cumulative Sums (Cusum) Test (Forward & Backward):** Analyzes the maximum excursion of a random walk.
7.  **Approximate Entropy Test (m=3):** Measures overlapping pattern frequency consistency.
8.  **Serial Test (m=3):** Compares the distribution of $2^m$ overlapping patterns.
9.  **Non-overlapping Template Matching Test:** Counts non-overlapping occurrences of templates (default `000000001`).

---

## 🛡️ Audit Results Summary (`.wraith` Files)

Below is the summary of the P-values calculated during the audits of our encrypted `.wraith` envelopes. Both files pass all tests since all P-values are $\ge 0.01$.

| Test Name | P-Value (`2_wraith_home.NIST`) | Status | P-Value (`2_wraith_downloads.NIST`) | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Frequency (Monobit) Test** | 0.63962 | **PASS** | 0.44508 | **PASS** |
| **Frequency Test within a Block (M=128)** | 0.02114 | **PASS** | 0.61479 | **PASS** |
| **Runs Test** | 0.76536 | **PASS** | 0.55698 | **PASS** |
| **Longest Run of Ones in a Block** | 0.16742 | **PASS** | 0.20274 | **PASS** |
| **Discrete Fourier Transform (Spectral)** | 0.76154 | **PASS** | 0.77380 | **PASS** |
| **Cumulative Sums (Cusum) Forward** | 0.53217 | **PASS** | 0.77256 | **PASS** |
| **Cumulative Sums (Cusum) Backward** | 0.93625 | **PASS** | 0.74689 | **PASS** |
| **Approximate Entropy Test (m=3)** | 0.70137 | **PASS** | 0.71896 | **PASS** |
| **Serial Test (m=3)** | 0.45438, 0.18741 | **PASS** | 0.45945, 0.25991 | **PASS** |
| **Non-overlapping Template Matching** | 0.93547 | **PASS** | 0.99931 | **PASS** |
| **OVERALL RESULT** | **SECURE / RANDOM** | **PASS** | **SECURE / RANDOM** | **PASS** |

---

## 📄 License
This project is licensed under the MIT License - see the [`LICENSE`](LICENSE) file for details.
