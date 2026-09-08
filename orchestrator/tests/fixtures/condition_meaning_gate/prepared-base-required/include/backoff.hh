#if BACKOFF_NOINLINE
__attribute__((noinline))
#endif
// EVOLVE-BLOCK-BEGIN silo-backoff-magnitude
#if BACKOFF_FIXED >= 0
    double now_backoff = static_cast<double>(BACKOFF_FIXED);
#else
    double now_backoff = Backoff_.load(std::memory_order_acquire);
#endif
// EVOLVE-BLOCK-END silo-backoff-magnitude
