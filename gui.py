import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import json
import subprocess
import math

import file_parser
import nist_tests

class NistAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NIST SP 800-22 Cryptographic Analysis Framework")
        self.root.geometry("1100x780")
        self.root.minsize(950, 650)
        
        # Paths for Project Mirage integration
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.abspath(os.path.join(script_dir, "..", "project"))
        self.avalanche_results_path = os.path.join(self.project_dir, "avalanche_results.json")
        self.avalanche_script_path = os.path.join(self.project_dir, "avalanche_test.js")
        
        # Variables
        self.file_path_var = tk.StringVar()
        self.format_var = tk.StringVar(value="Auto-detect")
        
        # Test Parameters
        self.block_size_var = tk.StringVar(value="128")
        self.block_entropy_var = tk.StringVar(value="3")
        self.template_str_var = tk.StringVar(value="000000001")
        self.template_block_var = tk.StringVar(value="1032")
        self.alpha_var = tk.StringVar(value="0.01")
        
        # Sidebar variables
        self.passed_tests_var = tk.StringVar(value="Tests Passed: -")
        self.min_p_var = tk.StringVar(value="Minimum P-value: -")
        self.max_p_var = tk.StringVar(value="Maximum P-value: -")
        self.bit_balance_var = tk.StringVar(value="Bit Balance: -")
        self.serial_corr_var = tk.StringVar(value="Serial Correlation: -")
        self.plaintext_sac_var = tk.StringVar(value="Plaintext SAC: -")
        self.key_sac_var = tk.StringVar(value="Key SAC: -")
        
        # Test selection variables
        self.tests_to_run = {
            "Frequency (Monobit) Test": tk.BooleanVar(value=True),
            "Frequency Test within a Block": tk.BooleanVar(value=True),
            "Runs Test": tk.BooleanVar(value=True),
            "Longest Run of Ones in a Block": tk.BooleanVar(value=True),
            "Discrete Fourier Transform (Spectral) Test": tk.BooleanVar(value=True),
            "Cumulative Sums (Cusum) Test (Forward)": tk.BooleanVar(value=True),
            "Cumulative Sums (Cusum) Test (Backward)": tk.BooleanVar(value=True),
            "Approximate Entropy Test": tk.BooleanVar(value=True),
            "Serial Test": tk.BooleanVar(value=True),
            "Non-overlapping Template Matching Test": tk.BooleanVar(value=True),
        }
        
        # Store results for report export
        self.latest_report_text = ""
        self.is_running = False
        
        self.setup_ui()
        self.load_avalanche_results()
        
    def setup_ui(self):
        # Configure grid expansion: Notebook gets column 0, Sidebar gets column 1
        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(3, weight=1)
        
        # 1. File Selection Frame (Spans both columns)
        file_frame = ttk.LabelFrame(self.root, text=" 1. Select Input File ", padding=10)
        file_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=15, pady=10)
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="File Path:").grid(row=0, column=0, sticky="w", padx=(0,5))
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, state="readonly")
        file_entry.grid(row=0, column=1, sticky="ew", padx=5)
        
        browse_btn = ttk.Button(file_frame, text="Browse...", command=self.browse_file)
        browse_btn.grid(row=0, column=2, padx=5)
        
        # Format detection selection
        ttk.Label(file_frame, text="Format:").grid(row=1, column=0, sticky="w", pady=(10, 0))
        format_combo = ttk.Combobox(file_frame, textvariable=self.format_var, state="readonly", 
                                    values=["Auto-detect", "Raw Binary (bytes)", "ASCII Binary (0s & 1s)", "Hexadecimal String"])
        format_combo.grid(row=1, column=1, sticky="w", pady=(10, 0), padx=5)
        
        # Info labels
        self.info_label = ttk.Label(file_frame, text="Select a file to inspect size and bits.", font=("Helvetica", 11, "italic"))
        self.info_label.grid(row=1, column=2, sticky="e", pady=(10, 0))
        
        # 2. Main Config Frame (Spans both columns)
        config_panes = ttk.Frame(self.root)
        config_panes.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=15, pady=5)
        config_panes.columnconfigure(0, weight=1)
        config_panes.columnconfigure(1, weight=1)
        
        # Parameters Sub-Frame (Left)
        param_frame = ttk.LabelFrame(config_panes, text=" 2. Test Parameters ", padding=10)
        param_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        param_frame.columnconfigure(1, weight=1)
        
        # Row 0: Block Size (Block Frequency)
        ttk.Label(param_frame, text="Block Size (M) [Block Freq]:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(param_frame, textvariable=self.block_size_var, width=12).grid(row=0, column=1, sticky="w", padx=10)
        
        # Row 1: Block Size (Entropy/Serial)
        ttk.Label(param_frame, text="Block Length (m) [Entropy/Serial]:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(param_frame, textvariable=self.block_entropy_var, width=12).grid(row=1, column=1, sticky="w", padx=10)
        
        # Row 2: Template String
        ttk.Label(param_frame, text="Template Pattern [Template Match]:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(param_frame, textvariable=self.template_str_var, width=15).grid(row=2, column=1, sticky="w", padx=10)
        
        # Row 3: Template Block Size
        ttk.Label(param_frame, text="Template Block Size (M_temp):").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(param_frame, textvariable=self.template_block_var, width=12).grid(row=3, column=1, sticky="w", padx=10)
        
        # Row 4: Alpha
        ttk.Label(param_frame, text="Significance Level (alpha):").grid(row=4, column=0, sticky="w", pady=5)
        ttk.Entry(param_frame, textvariable=self.alpha_var, width=12).grid(row=4, column=1, sticky="w", padx=10)
        
        # Tests Checklist Sub-Frame (Right)
        checklist_frame = ttk.LabelFrame(config_panes, text=" 3. Select NIST Tests to Run ", padding=10)
        checklist_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        checklist_frame.columnconfigure(0, weight=1)
        
        # Create a scrollable canvas for checklist
        checklist_canvas = tk.Canvas(checklist_frame, borderwidth=0, highlightthickness=0, height=130)
        checklist_scrollbar = ttk.Scrollbar(checklist_frame, orient="vertical", command=checklist_canvas.yview)
        scrollable_check_frame = ttk.Frame(checklist_canvas)
        
        scrollable_check_frame.bind(
            "<Configure>",
            lambda e: checklist_canvas.configure(
                scrollregion=checklist_canvas.bbox("all")
            )
        )
        
        checklist_canvas.create_window((0, 0), window=scrollable_check_frame, anchor="nw")
        checklist_canvas.configure(yscrollcommand=checklist_scrollbar.set)
        
        checklist_canvas.pack(side="left", fill="both", expand=True)
        checklist_scrollbar.pack(side="right", fill="y")
        
        # Add tests checkboxes
        for test_name, var in self.tests_to_run.items():
            ttk.Checkbutton(scrollable_check_frame, text=test_name, variable=var).pack(anchor="w", pady=2)
            
        # Select all / Clear all buttons in checklist frame header area
        btns_subframe = ttk.Frame(checklist_frame)
        btns_subframe.pack(side="bottom", fill="x", pady=(5,0))
        ttk.Button(btns_subframe, text="Select All", width=12, command=self.select_all_tests).pack(side="left", padx=5)
        ttk.Button(btns_subframe, text="Clear All", width=12, command=self.clear_all_tests).pack(side="left", padx=5)
        
        # 3. Action Panel (Spans both columns)
        action_frame = ttk.Frame(self.root)
        action_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=15, pady=10)
        
        self.run_btn = ttk.Button(action_frame, text="Run NIST Analysis", command=self.start_analysis, width=22)
        self.run_btn.pack(side="left", padx=5)
        
        self.status_var = tk.StringVar(value="Status: Ready")
        self.status_label = ttk.Label(action_frame, textvariable=self.status_var, font=("Helvetica", 11, "bold"))
        self.status_label.pack(side="left", padx=15)
        
        self.progress_bar = ttk.Progressbar(action_frame, orient="horizontal", mode="indeterminate", length=200)
        
        # 4. Results Notebook Frame (Column 0, weight 3)
        results_frame = ttk.Frame(self.root)
        results_frame.grid(row=3, column=0, sticky="nsew", padx=(15, 5), pady=(5, 15))
        
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Tab 1: Summary Treeview
        summary_tab = ttk.Frame(self.notebook)
        self.notebook.add(summary_tab, text="Analysis Summary")
        
        # Treeview Scrollbar
        tree_scroll = ttk.Scrollbar(summary_tab)
        tree_scroll.pack(side="right", fill="y")
        
        # Treeview Columns
        columns = ("test_name", "p_value", "status", "summary")
        self.tree = ttk.Treeview(summary_tab, columns=columns, show="headings", yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.config(command=self.tree.yview)
        
        self.tree.heading("test_name", text="Test Name")
        self.tree.heading("p_value", text="P-Value(s)")
        self.tree.heading("status", text="Status (alpha)")
        self.tree.heading("summary", text="Summary Details")
        
        self.tree.column("test_name", width=220, anchor="w")
        self.tree.column("p_value", width=140, anchor="center")
        self.tree.column("status", width=110, anchor="center")
        self.tree.column("summary", width=300, anchor="w")
        
        # Styling tag colors
        self.tree.tag_configure("pass", foreground="green", font=("Helvetica", 10, "bold"))
        self.tree.tag_configure("fail", foreground="red", font=("Helvetica", 10, "bold"))
        self.tree.tag_configure("info", foreground="blue")
        
        # Tab 2: Detailed Text Log
        log_tab = ttk.Frame(self.notebook)
        self.notebook.add(log_tab, text="Detailed Output Log")
        
        log_scroll = ttk.Scrollbar(log_tab)
        log_scroll.pack(side="right", fill="y")
        
        self.log_text = tk.Text(log_tab, wrap="word", yscrollcommand=log_scroll.set, font=("Courier", 10))
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.config(command=self.log_text.yview)
        
        log_action_bar = ttk.Frame(log_tab)
        log_action_bar.pack(side="bottom", fill="x", pady=5)
        self.save_btn = ttk.Button(log_action_bar, text="Save Report to File", command=self.save_report, state="disabled")
        self.save_btn.pack(side="right", padx=10)
        
        # 5. Side Panel: Cryptographic Analysis Sidebar (Column 1, weight 1)
        sidebar = ttk.LabelFrame(self.root, text=" Cryptographic Audit Framework ", padding=10)
        sidebar.grid(row=3, column=1, sticky="nsew", padx=(5, 15), pady=(5, 15))
        
        # NIST STS Statistics
        ttk.Label(sidebar, text="NIST STS", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(5, 2))
        ttk.Label(sidebar, textvariable=self.passed_tests_var, font=("Helvetica", 10)).pack(anchor="w", pady=1)
        ttk.Label(sidebar, textvariable=self.min_p_var, font=("Helvetica", 10)).pack(anchor="w", pady=1)
        ttk.Label(sidebar, textvariable=self.max_p_var, font=("Helvetica", 10)).pack(anchor="w", pady=1)
        
        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=8)
        
        # Avalanche Effect Panel
        ttk.Label(sidebar, text="Avalanche Effect (Mirage-C4)", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(0, 2))
        ttk.Label(sidebar, textvariable=self.plaintext_sac_var, font=("Helvetica", 10)).pack(anchor="w", pady=1)
        ttk.Label(sidebar, textvariable=self.key_sac_var, font=("Helvetica", 10)).pack(anchor="w", pady=1)
        self.avalanche_btn = ttk.Button(sidebar, text="Run Avalanche Test", command=self.start_avalanche_test)
        self.avalanche_btn.pack(fill="x", pady=(5, 0))
        
        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=8)
        
        # Distribution Panel
        ttk.Label(sidebar, text="Distribution Metrics", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(0, 2))
        ttk.Label(sidebar, textvariable=self.bit_balance_var, font=("Helvetica", 10)).pack(anchor="w", pady=1)
        ttk.Label(sidebar, textvariable=self.serial_corr_var, font=("Helvetica", 10)).pack(anchor="w", pady=1)
        
        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=8)
        
        # Global Decision Box
        self.decision_label = tk.Label(sidebar, text="WAITING FOR ANALYSIS", bg="#e0e0e0", fg="black",
                                      font=("Helvetica", 10, "bold"), relief="solid", bd=1, pady=6)
        self.decision_label.pack(fill="x", pady=5)
        
        # Disclaimer
        disclaimer_lbl = ttk.Label(sidebar, text="⚠ Passing NIST statistical tests does not constitute proof of cryptographic security.",
                                  font=("Helvetica", 9, "italic"), foreground="#804040", wraplength=180, justify="center")
        disclaimer_lbl.pack(fill="x", pady=(15, 0))
        
    def select_all_tests(self):
        for var in self.tests_to_run.values():
            var.set(True)
            
    def clear_all_tests(self):
        for var in self.tests_to_run.values():
            var.set(False)
            
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Open Encrypted or Random Data File",
            filetypes=[("All Files", "*.*"), ("Binary Files", "*.bin;*.dat;*.out"), ("Text Files", "*.txt")]
        )
        if file_path:
            self.file_path_var.set(file_path)
            self.inspect_file(file_path)
            
    def inspect_file(self, file_path):
        try:
            size_bytes = os.path.getsize(file_path)
            total_bits = size_bytes * 8
            
            format_type = self.format_var.get()
            if format_type == "ASCII Binary (0s & 1s)":
                total_bits = size_bytes  
            elif format_type == "Hexadecimal String":
                total_bits = size_bytes * 4  
                
            size_str = f"{size_bytes:,} bytes"
            if size_bytes > 1024 * 1024:
                size_str += f" ({size_bytes / (1024*1024):.2f} MB)"
            elif size_bytes > 1024:
                size_str += f" ({size_bytes / 1024:.2f} KB)"
                
            self.info_label.config(text=f"Size: {size_str} | Estimated: {total_bits:,} bits")
        except Exception as e:
            self.info_label.config(text=f"Error reading file size: {str(e)}")
            
    def load_avalanche_results(self):
        if os.path.exists(self.avalanche_results_path):
            try:
                with open(self.avalanche_results_path, "r") as f:
                    data = json.load(f)
                    p_sac = data.get("plaintext_sac", 0.0)
                    k_sac = data.get("key_sac", 0.0)
                    self.plaintext_sac_var.set(f"Plaintext SAC: {p_sac:.3f}%")
                    self.key_sac_var.set(f"Key SAC: {k_sac:.3f}%")
            except Exception as e:
                print(f"Error loading avalanche results: {e}")
                
    def start_avalanche_test(self):
        self.avalanche_btn.config(state="disabled")
        self.status_var.set("Status: Running Avalanche Test...")
        self.progress_bar.pack(side="right", padx=10)
        self.progress_bar.start(10)
        
        thread = threading.Thread(target=self.run_avalanche_thread)
        thread.daemon = True
        thread.start()
        
    def run_avalanche_thread(self):
        try:
            # Run the node script in project directory
            subprocess.run(["node", self.avalanche_script_path], cwd=self.project_dir, 
                           capture_output=True, text=True, check=True)
            self.root.after(0, self.on_avalanche_success)
        except Exception as e:
            self.root.after(0, lambda: self.on_avalanche_error(str(e)))
            
    def on_avalanche_success(self):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.avalanche_btn.config(state="normal")
        self.status_var.set("Status: Avalanche Test Completed")
        self.load_avalanche_results()
        messagebox.showinfo("Success", "Strict Avalanche Criterion (SAC) analysis completed successfully!")
        
    def on_avalanche_error(self, err_msg):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.avalanche_btn.config(state="normal")
        self.status_var.set("Status: Avalanche Test Failed")
        messagebox.showerror("Error", f"Failed to run avalanche test:\n{err_msg}")
        
    def start_analysis(self):
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showwarning("No File Selected", "Please select an encrypted or random file to analyze.")
            return
            
        if not os.path.exists(file_path):
            messagebox.showerror("File Error", "The selected file does not exist.")
            return
            
        # Parse inputs
        try:
            block_size = int(self.block_size_var.get())
            block_entropy = int(self.block_entropy_var.get())
            template_str = self.template_str_var.get()
            template_block = int(self.template_block_var.get())
            alpha = float(self.alpha_var.get())
            
            if block_size <= 0 or block_entropy <= 0 or template_block <= 0:
                raise ValueError("Sizes must be positive integers.")
            if not 0 < alpha < 1:
                raise ValueError("Alpha must be between 0 and 1.")
        except ValueError as e:
            messagebox.showerror("Parameter Error", f"Invalid parameters: {str(e)}")
            return
            
        # Check if at least one test is selected
        any_test = any(var.get() for var in self.tests_to_run.values())
        if not any_test:
            messagebox.showwarning("No Tests Selected", "Please select at least one NIST test to run.")
            return
            
        # Disable UI and start thread
        self.is_running = True
        self.run_btn.config(state="disabled")
        self.progress_bar.pack(side="right", padx=10)
        self.progress_bar.start(10)
        self.status_var.set("Status: Loading & Parsing file...")
        
        # Clear previous tree and text
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.log_text.delete(1.0, tk.END)
        self.save_btn.config(state="disabled")
        
        # Map combobox to parser format
        fmt_map = {
            "Auto-detect": "auto",
            "Raw Binary (bytes)": "bin",
            "ASCII Binary (0s & 1s)": "txt_bin",
            "Hexadecimal String": "hex"
        }
        format_type = fmt_map[self.format_var.get()]
        
        thread = threading.Thread(target=self.run_analysis_thread, 
                                  args=(file_path, format_type, block_size, block_entropy, template_str, template_block, alpha))
        thread.daemon = True
        thread.start()
        
    def run_analysis_thread(self, file_path, format_type, block_size, block_entropy, template_str, template_block, alpha):
        try:
            # 1. Parse File
            bits = file_parser.parse_file_to_bits(file_path, format_type)
            n = len(bits)
            
            if n == 0:
                self.root.after(0, lambda: self.on_error("File yielded 0 bits of data. Make sure format is correct."))
                return
                
            self.root.after(0, lambda: self.status_var.set(f"Status: Running tests on {n:,} bits..."))
            
            results = []
            detailed_logs = []
            
            # Helper to check if test is enabled
            def run_if_selected(name, test_func, *args):
                if self.tests_to_run[name].get():
                    self.root.after(0, lambda: self.status_var.set(f"Status: Running {name}..."))
                    try:
                        p, passed, detail = test_func(bits, *args)
                        results.append((name, p, passed, detail))
                        detailed_logs.append(f"=== {name} ===\n{detail}\n\n")
                    except Exception as ex:
                        results.append((name, "ERROR", False, f"Exception: {str(ex)}"))
                        detailed_logs.append(f"=== {name} ===\nError occurred: {str(ex)}\n\n")
            
            # Run enabled tests
            run_if_selected("Frequency (Monobit) Test", nist_tests.frequency_monobit_test)
            run_if_selected("Frequency Test within a Block", nist_tests.frequency_block_test, block_size)
            run_if_selected("Runs Test", nist_tests.runs_test)
            run_if_selected("Longest Run of Ones in a Block", nist_tests.longest_run_ones_test)
            run_if_selected("Discrete Fourier Transform (Spectral) Test", nist_tests.spectral_test)
            run_if_selected("Cumulative Sums (Cusum) Test (Forward)", nist_tests.cumulative_sums_test, 0)
            run_if_selected("Cumulative Sums (Cusum) Test (Backward)", nist_tests.cumulative_sums_test, 1)
            run_if_selected("Approximate Entropy Test", nist_tests.approximate_entropy_test, block_entropy)
            run_if_selected("Serial Test", nist_tests.serial_test, block_entropy)
            run_if_selected("Non-overlapping Template Matching Test", nist_tests.non_overlapping_template_matching_test, template_str, template_block)
            
            # Process results for UI update
            self.root.after(0, lambda: self.on_success(file_path, n, results, detailed_logs, alpha, bits))
            
        except Exception as e:
            self.root.after(0, lambda: self.on_error(f"Analysis failed: {str(e)}"))
            
    def on_success(self, file_path, n_bits, results, detailed_logs, alpha, bits):
        self.is_running = False
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.run_btn.config(state="normal")
        self.status_var.set("Status: Analysis Completed")
        
        # Calculate Distribution Metrics
        ones_ratio = np.sum(bits) / len(bits)
        bit_balance = ones_ratio * 100
        
        if len(bits) > 1:
            if np.all(bits == bits[0]):
                corr = 1.0
            else:
                corr = np.corrcoef(bits[:-1], bits[1:])[0, 1]
                if math.isnan(corr):
                    corr = 0.0
        else:
            corr = 0.0
            
        # Update Sidebar
        self.bit_balance_var.set(f"Bit Balance: {bit_balance:.2f}% ones")
        self.serial_corr_var.set(f"Serial Correlation: {corr:.4f}")
        
        # Calculate NIST STS Statistics
        p_values_list = []
        passed_count = 0
        total_tests = len(results)
        
        for name, p_val, passed, detail in results:
            if passed:
                passed_count += 1
            if isinstance(p_val, tuple):
                p_values_list.extend(p_val)
            elif isinstance(p_val, (int, float)):
                p_values_list.append(p_val)
                
        min_p = min(p_values_list) if p_values_list else 0.0
        max_p = max(p_values_list) if p_values_list else 0.0
        
        self.passed_tests_var.set(f"Tests Passed: {passed_count} / {total_tests}")
        self.min_p_var.set(f"Minimum P-value: {min_p:.5f}" if p_values_list else "Minimum P-value: -")
        self.max_p_var.set(f"Maximum P-value: {max_p:.5f}" if p_values_list else "Maximum P-value: -")
        
        # Update Global Decision Label
        all_passed = (passed_count == total_tests)
        if all_passed:
            self.decision_label.config(text="NIST STS: PASS", bg="#d4edda", fg="#155724")
        else:
            self.decision_label.config(text="NIST STS: FAIL", bg="#f8d7da", fg="#721c24")
            
        overall_conclusion = "STATISTICALLY RANDOM — NIST STS PASS" if all_passed else "NON-RANDOM — POTENTIAL LEAKAGE"
        
        # Build Report Header
        report_header = (
            "======================================================================\n"
            "                      NIST SP 800-22 ANALYSIS REPORT                  \n"
            "======================================================================\n"
            f"File Analyzed:      {file_path}\n"
            f"Sequence Length:    {n_bits:,} bits\n"
            f"Significance Level: {alpha}\n"
            f"Conclusion:         {overall_conclusion}\n"
            "----------------------------------------------------------------------\n"
            "WARNING: Passing NIST statistical tests does not constitute proof of\n"
            "         cryptographic security.\n"
            "======================================================================\n\n"
        )
        
        report_summary = "SUMMARY TABLE:\n"
        report_summary += f"{'Test Name':<45} | {'P-Value(s)':<18} | {'Status':<8}\n"
        report_summary += "-" * 78 + "\n"
        
        # Populate Treeview and build summary text
        for name, p_val, passed, detail in results:
            if isinstance(p_val, tuple):
                p_str = ", ".join(f"{p:.5f}" for p in p_val)
            elif isinstance(p_val, float):
                p_str = f"{p_val:.5f}"
            else:
                p_str = str(p_val)
                
            status = "PASS" if passed else "FAIL"
            tag = "pass" if passed else "fail"
            
            lines = detail.strip().split('\n')
            summary_line = lines[1] if len(lines) > 1 else lines[0]
            summary_line = summary_line.replace("\t", " ").strip()
            
            self.tree.insert("", "end", values=(name, p_str, status, summary_line), tags=(tag,))
            report_summary += f"{name:<45} | {p_str:<18} | {status:<8}\n"
            
        report_summary += "\n" + "=" * 78 + "\n\n"
        
        # Populate log pane
        self.log_text.insert(tk.END, report_header)
        self.log_text.insert(tk.END, report_summary)
        self.log_text.insert(tk.END, "DETAILED TEST LOGS:\n\n")
        
        for log in detailed_logs:
            self.log_text.insert(tk.END, log)
            
        self.latest_report_text = report_header + report_summary + "DETAILED TEST LOGS:\n\n" + "".join(detailed_logs)
        self.save_btn.config(state="normal")
        
        self.notebook.select(0)
        
    def on_error(self, message):
        self.is_running = False
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.run_btn.config(state="normal")
        self.status_var.set("Status: Error Occurred")
        messagebox.showerror("Error", message)
        
    def save_report(self):
        if not self.latest_report_text:
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Save Analysis Report",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")]
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.latest_report_text)
                messagebox.showinfo("Report Saved", f"Analysis report successfully saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Could not save report: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = NistAnalyzerApp(root)
    root.mainloop()
