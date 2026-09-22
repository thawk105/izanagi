struct PolicyState { uint64_t aborts = 0ul; uint64_t locks = 0ul; uint64_t commits = 0ul; };
uint32_t policy_after_abort(PolicyState& s, const izanagi_silo_api::AbortContext&) noexcept {
  uint32_t encoded = (s.commits & 7ul) | ((s.locks & 7ul) << 3u);
  s.aborts += 1ul;
  return encoded;
}
izanagi_silo_api::LockResponse policy_on_lock_conflict(PolicyState& s, const izanagi_silo_api::LockContext& c) noexcept {
  uint32_t encoded = s.aborts & 7ul;
  s.locks += 1ul;
  izanagi_silo_api::PolicyAction action = izanagi_silo_api::PolicyAction::abort;
  if (c.attempt < 4u) {
    action = izanagi_silo_api::PolicyAction::retry;
  }
  return izanagi_silo_api::LockResponse{action, encoded};
}
void policy_on_commit(PolicyState& s, const izanagi_silo_api::CommitContext&) noexcept {
  s.commits += 1ul;
}
