---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-t2867-silo-contrast-impl
seq: 3
---

## 再発

### F649

- **再発: 2026-09-29** — silo-function-policy 軸の生成器対照 ([T-2867]) の driver の単位実行を、テストは `measure_slot` を差し替えて確かめていたため、1 job の全 slot で 1 つの authorization session を共有する欠陥 (session は最初の計測 identity に束縛される) が緑のまま残り、計算ノードの生死確認で 3 本とも stock の後に `binding mismatch` で止まった。実物の `authorization_session`・`_authorize_measurement`・claim を通す結合テストを足し (修正前のコードでは同じ例外で赤)、slot ごとに session を開いて直した。記録 `output/insights/2026-09-29/t2867-silo-policy-contrast-impl/README.md` §4。

### F1054

- **再発: 2026-09-29** — 同じ対照の round tool のテストは coder の出力を axis と implementation を直接持つ object で与えていたが、coder role の実出力は runbook §1(b) のとおり `proposal` だけを top key に持つ object で、round tool がそれを剥がさずに `coder` の値として包み、実 LLM の初回の原提案で driver の preview が schema 不合格にした (LLM 2 系列で A を誤って 1 消費)。role の実出力と同じ形のテストを足し、round tool が `proposal` を展開するよう直した。記録は同じ insight §4。
