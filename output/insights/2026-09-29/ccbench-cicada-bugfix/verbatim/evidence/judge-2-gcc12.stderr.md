# judge-2 gcc12 の stderr (逐語、request 36352.nqsv、rc=1)

```
error: 選定した macro context における TRACE=0 正規化 preprocess 出力の同一性、および include 活性の同一性を確認できない: source_digest: cc/cicada/transaction.cc の条件指令が未知マクロ ['INLINE_VERSION_OPT', 'INLINE_VERSION_PROMOTION', 'SINGLE_EXEC', 'WORKER1_INSERT_DELAY_RPHASE'] を参照 — 実 TU 供給マクロ・先行する #define・CONTEXT_MACROS・builtin のいずれでもなく、digest はこの条件枝をどの文脈でも覆えない (TU 注入マクロ GLOBAL_VALUE_DEFINE 型の identity 死角、偽 cache hit の運び屋) ため fails-closed で停止 (T-148)。既知の文脈マクロなら CONTEXT_MACROS への登録 (= 両文脈 digest 化) が正しい封鎖で、この検査の緩和ではない (規律2)。
```
