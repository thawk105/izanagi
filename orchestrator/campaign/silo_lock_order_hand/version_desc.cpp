struct OrderState {};
bool order_enabled(OrderState&, const izanagi_silo_order_api::TxnContext&) noexcept {
  return true;
}
uint64_t order_priority(OrderState&, const izanagi_silo_order_api::EntryContext& e) noexcept {
  return (static_cast<uint64_t>(e.epoch) << 29u) | static_cast<uint64_t>(e.tid);
}
void order_after_abort(OrderState&, const izanagi_silo_order_api::AbortContext&) noexcept {}
void order_on_commit(OrderState&, const izanagi_silo_order_api::CommitContext&) noexcept {}
