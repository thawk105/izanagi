#include <atomic>
#include <cstdint>

static std::atomic<std::uint64_t> Backoff_{3};
static int permutation_control = 0;

double observe_backoff(std::uint64_t start) {
#include "../../include/backoff.hh"
    return now_backoff;
}

int main() {
    return (observe_backoff(1) < 0.0) + permutation_control;
}
