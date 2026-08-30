import os
import numpy as np

def clean_binary_string(text: str) -> str:
    """Removes all non-binary ('0' or '1') characters from the text."""
    # Using a fast translation map to filter characters
    allowed = set("01")
    return "".join(c for c in text if c in allowed)

def clean_hex_string(text: str) -> str:
    """Removes all non-hexadecimal characters from the text."""
    allowed = set("0123456789abcdefABCDEF")
    return "".join(c for c in text if c in allowed)

def inspect_wraith_envelope(file_path: str) -> dict:
    """
    Inspects a .wraith file and parses its header metadata.
    Returns metadata dict including mode, header size, and payload offset.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    with open(file_path, 'rb') as f:
        magic = f.read(8)
        
    info = {
        "is_wraith": False,
        "mode_byte": None,
        "mode_name": "Unknown",
        "header_size": 0,
        "file_size": os.path.getsize(file_path)
    }
    
    if magic.startswith(b"MIRAGE\x01"):
        info["is_wraith"] = True
        mode = magic[7] if len(magic) >= 8 else None
        info["mode_byte"] = mode
        if mode == 0x01:
            info["mode_name"] = "AES-256-GCM Single Block"
            info["header_size"] = 8 + 16 + 12 + 16 + 8 # 60 bytes
        elif mode == 0x02:
            info["mode_name"] = "AES-256-GCM Dual Block (Plausible Deniability)"
            info["header_size"] = 8 + 16 + 12 + 16 + 8 # 60 bytes
        elif mode == 0x03:
            info["mode_name"] = "Mirage-C4 Cascade (Camellia-256-CTR -> ARIA-256-CTR -> ChaCha20 -> AES-256-GCM)"
            # Magic (8) + Salt (16) + Camellia IV (16) + ARIA IV (16) + ChaCha IV (16) + AES IV (12) + Tag (16) + Len (8) = 108
            info["header_size"] = 108
        elif mode == 0x04:
            info["mode_name"] = "Mirage-C4 Dual Block Cascade (Plausible Deniability)"
            info["header_size"] = 108
        elif magic.startswith(b"MIRAGE_PART"):
            info["mode_name"] = "Mirage Split Container Fragment"
            info["header_size"] = 12
    return info

def parse_file_to_bits(file_path: str, format_type: str = 'auto', offset: int = 0, max_bytes: int = None) -> np.ndarray:
    """
    Parses a file and returns a NumPy array of bits (0 and 1).
    
    Parameters:
        file_path (str): Path to the file.
        format_type (str): Format type ('auto', 'bin', 'txt_bin', 'hex').
        offset (int): Byte offset to start reading from.
        max_bytes (int, optional): Maximum number of bytes to read.
        
    Returns:
        np.ndarray: Array of uint8 containing 0s and 1s.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    # Read the file content with offset and length
    with open(file_path, 'rb') as f:
        if offset > 0:
            f.seek(offset)
        if max_bytes is not None and max_bytes > 0:
            raw_data = f.read(max_bytes)
        else:
            raw_data = f.read()
        
    if format_type == 'auto':
        # Let's try to detect the file format.
        # Check if the file is valid ASCII/UTF-8 and contains mostly '0', '1', whitespace, or hex.
        try:
            sample_text = raw_data[:4096].decode('utf-8')
            cleaned_bin = clean_binary_string(sample_text)
            cleaned_hex = clean_hex_string(sample_text)
            
            # If the file contains only 0s, 1s, and whitespace, it's txt_bin
            non_whitespace = "".join(sample_text.split())
            if len(cleaned_bin) > 0 and len(cleaned_bin) == len(non_whitespace):
                format_type = 'txt_bin'
            elif len(cleaned_hex) > 0 and len(cleaned_hex) == len(non_whitespace) and len(cleaned_bin) < len(cleaned_hex):
                format_type = 'hex'
            else:
                format_type = 'bin'
        except UnicodeDecodeError:
            format_type = 'bin'
            
    if format_type == 'bin':
        # Raw binary file
        return np.unpackbits(np.frombuffer(raw_data, dtype=np.uint8))
        
    elif format_type == 'txt_bin':
        # Text representation of binary ('010010...')
        text = raw_data.decode('utf-8', errors='ignore')
        cleaned = clean_binary_string(text)
        if not cleaned:
            return np.array([], dtype=np.uint8)
        # Fast conversion
        ascii_bytes = cleaned.encode('ascii')
        return np.frombuffer(ascii_bytes, dtype=np.uint8) - 48 # ASCII '0' is 48
        
    elif format_type == 'hex':
        # Text representation of hexadecimal ('4f2b...')
        text = raw_data.decode('utf-8', errors='ignore')
        cleaned = clean_hex_string(text)
        if len(cleaned) % 2 != 0:
            cleaned = cleaned[:-1] # Ensure even length for byte conversion
        if not cleaned:
            return np.array([], dtype=np.uint8)
        byte_data = bytes.fromhex(cleaned)
        return np.unpackbits(np.frombuffer(byte_data, dtype=np.uint8))
        
    else:
        raise ValueError(f"Unknown format type: {format_type}")

