struct PolicyState { uint32_t m0 = 0u; uint32_t m1 = 0u; uint32_t m2 = 0u; uint32_t m3 = 0u; uint32_t m4 = 0u; uint32_t m5 = 0u; uint32_t m6 = 0u; uint32_t m7 = 0u; uint32_t m8 = 0u; uint32_t m9 = 0u; uint32_t m10 = 0u; uint32_t m11 = 0u; uint32_t m12 = 0u; uint32_t m13 = 0u; uint32_t m14 = 0u; uint32_t m15 = 0u; };
uint32_t policy_after_abort(PolicyState&, const izanagi_silo_api::AbortContext&) noexcept {
  return 0u;
}
izanagi_silo_api::LockResponse policy_on_lock_conflict(PolicyState&, const izanagi_silo_api::LockContext&) noexcept {
  return izanagi_silo_api::LockResponse{izanagi_silo_api::PolicyAction::abort, 0u};
}
void policy_on_commit(PolicyState&, const izanagi_silo_api::CommitContext&) noexcept {
}
