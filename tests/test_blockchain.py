"""
test_blockchain.py — Pytest suite verifying the cryptographic properties and linking
of the decentralized ledger module.
"""
import sys
import os
import pytest
import hashlib

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import blockchain
from backend.gcp_manager import db

def test_hash_string_consistency():
    """Verify hash_string outputs consistent SHA-256 checksums."""
    test_str = "hello"
    expected = hashlib.sha256(test_str.encode("utf-8")).hexdigest()
    assert blockchain.hash_string(test_str) == expected
    assert blockchain.hash_string(test_str) == blockchain.hash_string(test_str)

def test_verify_empty_chain():
    """Verify full chain audits succeed on empty datasets without raising errors."""
    # Ensure ledger is temporarily empty or verify behavior
    report = blockchain.verify_full_chain()
    assert "chain_intact" in report
    assert isinstance(report["chain_intact"], bool)
    assert "total_entries" in report

def test_sequential_hash_linking():
    """Verify sequential ledger updates build cryptographically linked structures."""
    cid = "CS-TEST-99"
    event1 = "COMPLAINT_SUBMITTED"
    event2 = "AI_ANALYZED"
    
    # Write block 1
    block1 = blockchain.add_entry(cid, event1, "TestActor1")
    # Write block 2
    block2 = blockchain.add_entry(cid, event2, "TestActor2")
    
    # The second block's prev_hash must be the SHA-256 of the first block
    import json
    expected_hash = blockchain.hash_string(
        json.dumps(block1, sort_keys=True, ensure_ascii=False, default=str)
    )
    assert block2["prev_hash"] == expected_hash

def test_nonexistent_complaint_ledger():
    """Verify non-existent ID queries return empty collections gracefully."""
    res = blockchain.get_complaint_ledger("CS-NONEXISTENT")
    assert isinstance(res, list)
    assert len(res) == 0
