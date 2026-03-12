# SOLUTION: Data layout booleans

# --- Matrix A (M x H) ---
# Natural: M-rows along Y, H-cols along X (H aligns with reduction axis)
A_GLOBAL_TRANSPOSE = False
A_MEMORY_TRANSPOSE = True

# --- Matrix B (H x N) ---
# Transposed: H-rows along X (aligns with reduction axis), N-cols along Y
B_GLOBAL_TRANSPOSE = True
B_MEMORY_TRANSPOSE = True

# --- Matrix C (M x N) ---
# Natural: M-rows along Y, N-cols along X (matches output distribution)
C_GLOBAL_TRANSPOSE = False
C_MEMORY_TRANSPOSE = True
