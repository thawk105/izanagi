// EVOLVE-BLOCK-BEGIN silo-backoff-magnitude
#if BACKOFF_FIXED >= 0
    double now_backoff = (static_cast<uint64_t>(BACKOFF_FIXED) / 1000ULL == 0ULL) ? static_cast<double>(BACKOFF_FIXED) : ((static_cast<uint64_t>(BACKOFF_FIXED) / 1000ULL == 1ULL) ? static_cast<double>((static_cast<uint64_t>(BACKOFF_FIXED) % 1000ULL) + (((start * 0x9e3779b97f4a7c15ULL) >> 63) ? (2ULL * (static_cast<uint64_t>(BACKOFF_FIXED) % 1000ULL) - ((((start * 0x9e3779b97f4a7c15ULL) << 1) >> 1) % (2ULL * (static_cast<uint64_t>(BACKOFF_FIXED) % 1000ULL) + 1ULL))) : ((((start * 0x9e3779b97f4a7c15ULL) << 1) >> 1) % (2ULL * (static_cast<uint64_t>(BACKOFF_FIXED) % 1000ULL) + 1ULL)))) / 2.0 : ((static_cast<uint64_t>(BACKOFF_FIXED) / 1000ULL == 2ULL) ? static_cast<double>((static_cast<uint64_t>(BACKOFF_FIXED) % 1000ULL) + (((start * 0x9e3779b97f4a7c15ULL) >> 63) * (2ULL * (static_cast<uint64_t>(BACKOFF_FIXED) % 1000ULL)))) / 2.0 : static_cast<double>(static_cast<uint64_t>(BACKOFF_FIXED) % 1000ULL)));
#else
    double now_backoff = Backoff_.load(std::memory_order_acquire);
#endif
// EVOLVE-BLOCK-END silo-backoff-magnitude
