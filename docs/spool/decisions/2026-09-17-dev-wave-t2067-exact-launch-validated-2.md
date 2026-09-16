---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2067-exact-launch-validated
seq: 2
---

## {{D:gate-core-drops-ratified-injection-port}}. gate core の v2 admission は exact LaunchValidatedFreeze だけに束ね、RatifiedFreeze の注入口を core から外す

**決定:** D1872 の実装にあたり、`_gate_check_core` の v2 枝は `ratified_error` の `freeze-ratify:` 翻訳 →
`launch_validated` 欠落なら refusal `v2-execution: launch-validate: LaunchValidatedFreeze exact type が必要` →
token 有りなら既存の sha256 照合、の順とし、拒否理由の集約 (known-axes / floor-null / budget-null / manifest) は
継続する (early return は足さない)。core の signature から `ratified` 引数を削り、`gate_check` の call site 2 箇所も
揃える。core の freeze 再読 (`verified` 未指定時の `_load_verified_freeze`) は残す。`gate_check` の public
`ratified=` / `ratified_error=`、`_gate_check_validated`、`run_block`、CLI は変えない。回帰 test は新規 file に置き、
既存 test file は編集しない。D1241 / D1313 の advisory / non-certifying 上限は解除しない。

**理由:**

- D65 決定 (5) の趣旨は gate core への注入口を最小にすることであり、受理に寄与しない `RatifiedFreeze` の
  注入口を core に残すのは「gate が 2 通りの意味を持つ」状態の残骸である。削除は 3 行で新機構を作らない。
  plan 子は「core への直接注入の負例を書くため」に保持を推奨したが、その負例は public `gate_check(ratified=…)`
  と初回 read 失敗 → 再読成功の race を組み合わせた負例 (旧 code では allowed=True) に置き換えられ、
  public API 越しの観測なので証拠力はむしろ上がる。
- 再読を撤去する案は、v1 と二読失敗の既存 refusal 集約 (二読目の例外本文・known record 欠落・null 診断)
  を失うか、例外を core へ渡す新 signature を要する。D1872 が名指すのは v2 の static self-load だけである。
- 負例の static loader fake は hash 一致の合成 RatifiedFreeze を返す形にする。AssertionError を投げる fake は
  旧 code も例外を捕捉して拒否するため、受理境界の証拠にならない。
- D1984 の本文には「二読 fallback の択一は未裁定」と読める記述が残るが、D1872 (先行) の後に書かれた不整合
  であり、後続の持ち越し本文と本依頼は D1872 を裁定済みとして扱う。本 wave はこれに従い、D1984 が決めた
  caller 閉包メタテストの不採用は動かさない。

**却下した選択肢:**

- core の `ratified` 引数を未使用のまま残す — 差分は最小だが、受理に寄与しない注入口が core に残り、
  後続が再配線する余地を残す。
- core の freeze 再読も撤去する — 既存の v1 / 二読失敗の refusal 集合を変えるか signature 拡大を要し、
  局所修正の範囲を超える。
- 型検査を `isinstance` に緩める — subclass が通る。exact type の既存契約を維持する。
- 変異の期待 node を代表 node だけで登録する — 期待 node は完全集合でなければ KILLED と数えられない
  (DW-M08)。probe 走で観測 node を集めてから本走 spec を確定する。
