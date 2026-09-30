namespace izanagi_silo_order_api {
enum class AbortReason : uint32_t { unset, lock_conflict, update_absent, read_tid, read_locked, node_validation, insert_node, scan_node };
struct TxnContext { uint32_t write_count; uint64_t rand; };
struct EntryContext { uint32_t epoch; uint32_t tid; bool locked; };
struct AbortContext { AbortReason reason; uint64_t rand; };
struct CommitContext { };
}
namespace izanagi_silo_order {
struct OrderState;
bool order_enabled(OrderState&, const izanagi_silo_order_api::TxnContext&) noexcept;
uint64_t order_priority(OrderState&, const izanagi_silo_order_api::EntryContext&) noexcept;
void order_after_abort(OrderState&, const izanagi_silo_order_api::AbortContext&) noexcept;
void order_on_commit(OrderState&, const izanagi_silo_order_api::CommitContext&) noexcept;
}
