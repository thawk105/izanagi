## 所見

### 1. must-fix — checker が対象 path を厳密に制限していない

段 4 R1 は `-r` による全 path 列挙を要求し、その目的を exact-path gate としている [`s4-ruling.md:20`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/s4-ruling.md:20)。段 2 の継承契約も差分集合を厳密に `{cc/silo/transaction.cc}` とする [`s2-plan.md:103`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/s2-plan.md:103)。

実装は `-r` 自体は使っているものの [`check_trace0_preprocess_identity.py:107`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:107)、`_validate_diff()` は任意個の regular C/C++ source/header の `M` を許し、path allowlist を検査していない [`check_trace0_preprocess_identity.py:156`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:156)。テストにも「対象ファイルに加えて別の C++ file が M」の負例がない [`test_check_trace0_preprocess_identity.py:198`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_check_trace0_preprocess_identity.py:198)。

実 pin 対は実際に一ファイルだけなので今回得た JSON の内容自体は正しいが、checker の受理集合は裁定より広い。

**成果物影響:** 別の trace-only C++ file を同じ commit で変更しても checker が緑になり、未承認 emitter semantics に基づく certified membership／レポート行を承認可能になる。

### 2. blocker — 新テストの self-run harness が既存 meta-test を満たさず、受入が実際に赤

新テストは `_run_self()` 内で `pytest.main()` を呼び、`__main__` から `_run_self()` を呼ぶ構造になっている [`test_check_trace0_preprocess_identity.py:310`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_check_trace0_preprocess_identity.py:310)。しかし既存 meta-test は `__main__` より後の文字列だけを調べ、signal を `_run(` または `pytest.main` 等に限定する [`test_plain_runner_coverage.py:25`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_plain_runner_coverage.py:25)、[`test_plain_runner_coverage.py:35`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/tests/test_plain_runner_coverage.py:35)。`_run_self(` は `_run(` に一致せず、`pytest.main` は `__main__` より前なので認識されない。

これは推測ではなく、親の焦点走行が当該ファイルを offender として失敗している [`focus1.log:30`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/focus1.log:30)。段 5 報告の「plain-runner meta-test 用の自己実行 harness あり」 [`s5-unit-b.md:31`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/s5-unit-b.md:31) は、存在の説明としては正しいが効力を過大評価している。なお同報告は pytest 緑を主張しておらず、「未実走」と明記した点は正直である。

**成果物影響:** 受入レポートが `1 failed` のままになり、この wave は land できず、certified 選択・台帳は旧状態から前進しない。

### 3. must-fix — R6 の「復元 clone 上で checker 再走」を証明する evidence が不足

bundle は存在し、一時 clone の HEAD も新 SHA である。一方、復元 script は clone 後に `grep` するだけで、checker を呼んでいない [`make-bundle.sh:17`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/make-bundle.sh:17)。また checker の JSON は repo path を記録しない [`check_trace0_preprocess_identity.py:329`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/tools/check_trace0_preprocess_identity.py:329)。

g++-11/12 の保存済み JSON は新 SHA に対して pass しているが、元 checkout と復元 clone のどちらを `--repo` に使ったか区別できない。したがって「実際には復元 clone で走らせた」可能性は否定しないものの、R6 の監査可能な証拠にはなっていない [`s4-ruling.md:38`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/s4-ruling.md:38)。

**成果物影響:** 台帳で「bundle から復元した SHA を checker 済み」と記録できず、承認手番へ渡す proof chain の参照が未確定になる。

### 4. must-fix — R12 の TRACE=1 実 emitter 検査が未実施

段 4 は実 TRACE=1 build/run で、C 一件、宣言件数と R/W 実数、末尾 E 一件を機械照合するよう要求する [`s4-ruling.md:71`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/s4-ruling.md:71)。段 5 報告は build・実 trace とも未実走と明記している [`s5-unit-a.md:65`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t756-fn2-trace-v2/s5-unit-a.md:65)。現時点の job artifact にも実 trace や照合結果はない。

ビルド不能なら未実測記録で閉じられる契約だが、少なくとも試行した証拠が必要。

**成果物影響:** FN-2 の台帳状態を実測済みとして閉じられず、閉じれば C/R/W/E framing の実在を確認していない偽の closure になる。

## C++ 側の確認結果

C++ 実装そのものには新たな blocker は見つからなかった。

- 追加された C と説明コメントは `#if TRACE` の 584–634 内、E とコメントは 694–699 内。`cc/silo/transaction.cc` に `#ifdef TRACE` はない。
- Silo の `emit_commit` 呼び出しは削除済み。C は `writePhase()` 内の直接出力一箇所だけで、`writePhase()` の caller も commit 成功経路の一箇所だけ（新 commit `cc/silo/transaction.cc:584–617,706–712`）。
- 宣言件数は `read_set_.size()` / `write_set_.size()` で、その直後に同じ集合を `continue`・条件分岐なしで一巡するため、正常出力経路では R/W 件数が一致する（同 `:602–617`）。
- E は entry X、UPDATE/DELETE retention X、write loop、`clear_shadow()` の後（同 `:618–698`）。正常経路に早期 return/goto はなく、E は一箇所だけ。異常停止・例外・`ERR` では E が出ないが、これは未完 txn として検出させる設計どおり。
- `izanagi_txid` は別々の `#if TRACE` 間でも同じ関数 scope にあり、TRACE=1 で E から可視。TRACE=0 では宣言・参照がともに除去される。
- SI は v1 のまま。承認 pipeline は既存 `trace_*.log` のある directory を拒否するため通常経路では混在しない [`pipeline.py:323`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-fn2-trace-v2/orchestrator/campaign/pipeline.py:323)。ただし C++ 単体では `IZANAGI_TRACE_DIR` 未指定時に `.` を使い、thread file を遅延 truncate するため、再利用 directory に古い別 protocol の高 thid file が残る経路はある。これは R11 の手順 4 hard block を維持すべき根拠であり、現 wave の新規逸脱ではない。

## R1〜R12 照合

| 裁定 | 状態 | 判定 |
|---|---|---|
| R1 | `diff-tree --raw -r -z --no-renames` は実装。exact-path 制約は欠落 | 部分実装 |
| R2 | include marker 化＋文字列比較を実装、条件枝移動テストあり | 準拠 |
| R3 | `--cxx` 必須、path/version 報告あり。実 pin 対 g++-11/12 の pass artifact あり | 準拠 |
| R4 | 事前登録済み、負例は message 断片を検査。変異 matrix は段 6 後段待ち | 現時点準拠 |
| R5 | Silo の `emit_commit` を置換、SI helper/call は維持 | 準拠 |
| R6 | bundle/clone は実施。復元 clone 上の checker 再走 evidence が識別不能 | 部分実装 |
| R7 | submodule worktree と committed gitlink は d706650 に復元済み | 準拠、段 7 の限定記録待ち |
| R8 | checker 名・保証文言とも「TU 同一」を避けた弱い名称 | 準拠 |
| R9 | 実装 scope は守る。限定 closure の台帳記録は段 7 待ち | 未記録 |
| R10 | 新 commit の親は d706650。最終 topology は人間手番のまま | 裁定どおり |
| R11 | SI v1 は不変。手順 4 前の三択裁定は未解決 | 意図した scope-out／hard block 継続 |
| R12 | TRACE=1 build・実 trace・framing 照合なし | 未実装 |

既存 tracked test の削除・改変はなく、新 module 名や fixture 名の衝突もない。現行 pin・gitlink・承認定数および live pipeline の受理集合も変わっていない。ただし新 test file の存在によって既存 plain-runner meta-test が赤になるため、repository acceptance は現に変化している。

## 総括

blocker は「新テストの self-run harness が既存 meta-test を満たさず、受入が実際に赤」の 1 件。段 4 裁定には exact-path、復元 clone evidence、R12 でも未準拠が残るため、現 snapshot は準拠不可・fix 必須。