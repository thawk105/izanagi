# 段 4 変異事前登録 — B-10 analysis_commit 束縛の除去

`DW-M01` に従い実装前に登録する。各変異について、位置・期待 kill・**同じ入力を拒否する層が
前後に無いこと**をコードで確認した根拠を書く。走行は段 6 の fix 後、`tools/mutation_harness.py`
で baseline 緑を確認してから行う。

本 wave は受理集合を**拡大**する (これまで拒否していた HEAD-only drift を通す)。
したがって M1〜M3 が「拡大が実際に起きたこと」、M4 が「拡大しすぎていないこと」を担う。

## M1 — core() へ analysis_commit を戻す

- **位置:** `orchestrator/campaign/b10_backoff_shape_sweep.py`、`PreregistrationBinding.core()`。
  削除した `"analysis_commit": self.analysis_commit,` の 1 行を復元する。
- **期待 kill:** 新設の WAL resume 正例テスト。`analysis_commit` だけ異なる 2 binding の
  `core()` / `as_dict()` / `binding_sha256` が一致しなくなり、`assert_resumable_binding` が
  `PreflightError("resume-binding")` を上げる。
- **単一理由性:** 正例テストは `analysis_code_sha256` を両側で同値にするため、
  `assert_resumable_binding` 内の他の拒否条件 (`:1556-1563` の lock/WAL 存在検査、
  `:1573-1585` の BUILD_START 比較) はいずれも通る。拒否理由は core() の差だけになる。
  前段に同じ入力を拒否する層はない — `load_preregistration` はテストを経由しない。
- **kill 判定:** 受理集合が「HEAD-only drift を拒否する」方向へ戻ることを確認する。
  診断文字列だけの赤は kill にしない (`DW-M03`)。

## M2 — 過去 block row の analysis_commit 比較を戻す

- **位置:** 同 file、`_validate_prior_block_records` の比較連鎖。
  削除した `or row.get("analysis_commit") != prereg.binding.analysis_commit \` を復元する。
- **期待 kill:** 新設の block row 正例テスト。row の `analysis_commit` が記録時 HEAD、
  現在 binding が再開時 HEAD なので不一致で `resume-binding` になる。
- **単一理由性:** M1 を適用しない状態では `row.get("preregistration_binding") !=
  prereg.binding.as_dict()` (`:2385`) に `analysis_commit` が入らないため、この比較を通る。
  正例 row は `analysis_code_sha256` を両側で同値にするので `:2387` も通る。
  よって赤理由はこの 1 行だけである。
- **kill 判定:** 同上。

## M3 — 過去 block row の source_commit 比較を戻す

- **位置:** 同 file、同じ比較連鎖。
  削除した `or row.get("source_commit") != prereg.binding.analysis_commit \` を復元する。
- **期待 kill:** 同じ block row 正例テスト。row の `source_commit` は投入時 HEAD なので
  再開時 HEAD と不一致になる。
- **単一理由性:** M2 と独立に適用する。M2 を適用しない状態では `analysis_commit` 比較が
  無いため、赤理由はこの 1 行だけである。M2 と M3 を同時に適用しない。
- **kill 判定:** 同上。

## M4 — core() から analysis_code_sha256 を外す (緩めていないことの保護)

- **位置:** 同 file、`PreregistrationBinding.core()`。
  `"analysis_code_sha256": self.analysis_code_sha256,` の 1 行を削除する。
- **期待 kill:** 新設の WAL resume 負例テスト。解析コードの内容ハッシュが違う束縛が
  通ってしまい、`PreflightError` が上がらなくなって assert が赤になる。
- **単一理由性:** 負例テストは `analysis_code_sha256` だけを変え、他の field を同値にする。
  `assert_resumable_binding` の中で内容ハッシュ差を拒否しているのは `core()` 経由の
  `as_dict()` 比較と `binding_sha256` 比較だけである。block row 側の明示的
  `analysis_code_sha256` 比較 (`:2387`) は別のテストが通る経路であり、この負例テストは
  `assert_resumable_binding` だけを呼ぶので前後の冗長 gate はない。
- **kill 判定:** 受理集合が「内容ハッシュ違いを受理する」方向へ広がることを確認する。
  これが SURVIVED なら本 wave は規律 7 の名の下に内容束縛まで緩めたことになるので、
  fix なしに段 7 へ進まない。

## 登録しないもの (理由を残す)

- **block record 生成側の provenance 保持 (`:3030`) と Markdown レポート行 (`:2655`)。**
  現行のテストは `_validate_prior_block_records` へ手作りの row を渡す経路しか持たず、
  `run_formal` の row 構築とレポート書き出しを通るテストが存在しない
  (`orchestrator/tests/test_b10_backoff_shape_sweep.py` に該当 test なし)。
  したがってこの位置の変異を kill できる実効 gate が無い。`DW-M01` に従い**登録しない**。
  新設テストに置く「受理後の row に旧 `analysis_commit` / `source_commit` が残る」assert は、
  現に剥ぎ取る機構が無いため**恒真に近い記述用の assert** である。保護と数えない。
  実装子には `:2655` と `:3030` を変更しないことを禁止事項として個別に渡す。
