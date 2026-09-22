struct PolicyState { uint32_t m = 0u; };
uint32_t helper(uint32_t a, uint64_t b) noexcept { uint32_t x = a + b; x -= 1ul; x *= 2u; x /= 1ul; x %= 13u; x &= 7u; x |= 1u; x ^= 2u; x <<= 1u; x >>= 1u; bool q = (a < b) || (a >= b); q = !q && (a == b); return q ? ~x : -x; }
uint32_t policy_after_abort(PolicyState&, const izanagi_silo_api::AbortContext&) noexcept {
  return 0u;
}
izanagi_silo_api::LockResponse policy_on_lock_conflict(PolicyState&, const izanagi_silo_api::LockContext&) noexcept {
  return izanagi_silo_api::LockResponse{izanagi_silo_api::PolicyAction::abort, 0u};
}
void policy_on_commit(PolicyState&, const izanagi_silo_api::CommitContext&) noexcept {
}
