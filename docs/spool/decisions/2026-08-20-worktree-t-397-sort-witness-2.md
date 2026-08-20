---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: worktree-t-397-sort-witness
seq: 2
---

## {{D:sort-witness-p1-narrowed}}. D146 決定10 (byte-binding blocker) を、land を妨げない意味で解消済みへ narrow する

**決定:** D146 決定10「本 wave では実装しない」の根拠だった byte-binding blocker
(`orchestrator/verifier/` 全 Python が committed qualification evidence
`output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json` の `binding.runtime_modules` へ
束縛され、編集すると再束縛検査が赤になる) は、**land・テスト・受入を妨げる意味では解消済み**と
確定する。ただし解消の範囲を精密に限定する — 「evidence が現行 bytes を再認証できる」ことまでは
主張しない。

**根拠:**
- 唯一の live テスト束縛 `test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head`
  (`orchestrator/tests/test_silo_ladder_rung1_evidence.py`) は、無関係な2 wave
  (commit `17bd4099` [T-452]/[T-453] 2026-08-05、`78b3c0ae` [T-816] 2026-08-12) が
  「現行 bytes は歴史 evidence と一致すべき」から「歴史 golden を凍結保持し現行との不一致を正と
  する」へ既に設計変更しており、`orchestrator/verifier/` への追加編集で失敗しない
  (実測、git blame/git show で意図を確認)。
- `orchestrator/tests/test_silo_ladder_rung1_driver.py` の
  `test_runtime_binding_covers_all_execution_semantics_modules` は `orchestrator/verifier` の
  `rglob("*.py")` を今も binding scope に含めており、選択肢 (b) (scope 縮小) は取られていない —
  縮小でなく「歴史 vs 現行の不一致を許容する」設計への一般化である。
- `validate_current_bindings`/`validate_raw_bundle` (`orchestrator/campaign/silo_ladder_rung1.py`)
  の raw 再計算比較はなお `==` (一致) を要求するが、呼び出し元は実 job の `collect`/
  `verify-result` 経路 (`silo_ladder_rung1.py:4754,4866` 付近) だけであり、
  リポジトリ全体を grep しても実凍結 evidence に対してこれらの関数を呼ぶテストは 0 件
  (`test_silo_ladder_rung1_evidence.py` は `validate_current_bindings`/`validate_raw_bundle`/
  `validate_evidence` のいずれも呼ばない)。したがって本 wave のテスト・受入では発火しない。

**理由:**
- D138 決定4 が `IntegrityWitness` の構造化表現の新設を要求しており、その新設が
  「実 job を再走しない限り一切できない」状態のまま放置されるのは規律5 (段階導入) にも規律3
  (正しさシグナルを後付けにしない) にも反する。land を妨げない事実が実測で確定した以上、
  実装を止め続ける理由がなくなった。
- 一方で「evidence が現行 bytes を再認証できる」という主張はしていない。これは実 job での
  rung-1 campaign 再走 (T-410 ruling の裁定パッケージ選択肢 a) でしか得られず、本 wave の
  scope 外のまま持ち越す。

**却下した選択肢:**
- D146 決定10 をそのまま維持し、[T-397]/[T-410] を再度「実装しない」で閉じる —
  land を妨げないという実測結果と矛盾し、二重登録のまま停滞を繰り返すだけになる。
- `validate_current_bindings`/`validate_raw_bundle` の `==` 要求も本 wave で解消する —
  実 job 経路の再設計 (rung-1 campaign 再走または binding scope の D96 級再裁定) が要り、
  sort 軸の witness 追加という本 wave の scope を大きく超える。
