struct PolicyState { uint32_t m = 0u; };
uint32_t helper(bool b) noexcept { if (b) { return 1u; } else { return 0u; } }
uint32_t policy_after_abort(PolicyState&, const izanagi_silo_api::AbortContext&) noexcept {
  return 0u;
}
izanagi_silo_api::LockResponse policy_on_lock_conflict(PolicyState&, const izanagi_silo_api::LockContext&) noexcept {
  return izanagi_silo_api::LockResponse{izanagi_silo_api::PolicyAction::abort, 0u};
}
void policy_on_commit(PolicyState&, const izanagi_silo_api::CommitContext&) noexcept {
}
