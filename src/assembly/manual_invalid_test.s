# Test invalid instructions
add x1, x2, x3      # Valid
add x50, x1, x2     # Invalid register (x50 > x31)
addi x1, x2, 5000   # Invalid immediate (out of range)
invalid_instr x1    # Invalid instruction name 