namespace izanagi_silo_api {
enum class PolicyAction : uint32_t { retry = 0, abort = 1 };
enum class AbortReason : uint32_t { unset, lock_conflict, update_absent, read_tid, read_locked, node_validation, insert_node, scan_node };
struct AbortContext { AbortReason reason; uint64_t rand; };
struct LockContext { uint32_t attempt; uint64_t rand; };
struct LockResponse { PolicyAction action; uint32_t wait_us; };
struct CommitContext { };
}
namespace izanagi_silo_policy {
struct PolicyState;
uint32_t policy_after_abort(PolicyState&, const izanagi_silo_api::AbortContext&) noexcept;
izanagi_silo_api::LockResponse policy_on_lock_conflict(PolicyState&, const izanagi_silo_api::LockContext&) noexcept;
void policy_on_commit(PolicyState&, const izanagi_silo_api::CommitContext&) noexcept;
}
