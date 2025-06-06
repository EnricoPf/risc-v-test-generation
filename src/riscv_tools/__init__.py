"""
RISC-V Tools Library

This package provides tools for generating and validating RISC-V assembly code.

Modules:
    test_generator: Generate random test cases for RISC-V instructions
    fetch_opcodes: Fetch and process RISC-V opcode definitions
    profiles: RISC-V instruction profiles and classifications
"""

from .test_generator import RiscVTestGenerator
from .fetch_opcodes import *

__version__ = "1.0.0"
__author__ = "RISC-V Tools Team"

__all__ = [
    'RiscVTestGenerator',
] 