#include <atomic>
#include <cstdint>
#include <izanagi_prepared_dependency.hh>

#if IZANAGI_PREPARED_DEPENDENCY != 1
#error "prepared dependency header has the wrong value"
#endif

static std::atomic<std::uint64_t> Backoff_{3};

double observe_backoff(std::uint64_t start) {
#include "../../include/backoff.hh"
    return now_backoff;
}

int main() {
    return observe_backoff(1) < 0.0;
}
