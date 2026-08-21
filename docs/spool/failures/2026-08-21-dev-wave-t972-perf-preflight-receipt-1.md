---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-21
wave: dev-wave-t972-perf-preflight-receipt
seq: 1
---

## 新規

### {{F:dev-wave-author-prompt-missing-total-heading}}. 段5 author への prompt に `## 総括` 見出し必須の指示を書き忘れた [手順漏れ]

- 事象: 段2 (plan)・段3 (consult) の prompt には `## 総括` 見出し必須を明記したが、段5 (author)
  の prompt には同じ指示を書き忘れた。実装子は複雑な実装 (3ファイル・580行) を正しく完了し
  commit もしなかったが、完了報告に `## 総括` が無く `check_codex_output.py` の rc=1 で不採用に
  なった。実装自体は無傷だったため実害は軽微だが、原因特定に往復が生じた。
- 根本原因: DW-O01 の「prompt は `## 総括` 必須」は段を問わない一般規律だが、段ごとに個別の
  prompt を都度手書きするため、書き忘れが構造的に起こりうる。
- 恒久対応: 実装なし (段8 自己改善候補として、段5/6 (author/fix) prompt テンプレへの
  チェックリスト追記を検討する)。
- 再発検知: 各段の codex 投入前に `## 総括` 見出しの有無を prompt 本文で目視確認する。

### {{F:mutation-harness-orphan-hold-dual-sidecar}}. 変異harness の orphan-hold 復旧は2種類の sidecar を両方削除しないと再投入できない [手順漏れ]

- 事象: 変異matrix 投入中に dispatch queue timeout (signal 15、rc=16) で orphan-hold が発火した。
  harness のエラーメッセージに従い repo 内 `output/pegasus-dispatch/orphan-hold.json` と
  対応 submission_dir を削除・dirty file を復元して再投入したところ、今度は job-dir 側の
  `<out>.orphan-stop.json` (別 sidecar) が残っていたため fail-closed で即停止した。
  同じ復旧手順の文言 (「hold と sidecar を手動削除する」) が両方を指していたが、2 種類の
  sidecar が別々のタイミングで検出されるため、1 回で両方削除する判断ができなかった。
- 根本原因: orphan-hold の証跡が repo 内 (`output/pegasus-dispatch/orphan-hold.json`) と
  job-dir 側 (`<--out 値>.orphan-stop.json`) の2箇所に分散しており、harness は起動時に
  job-dir 側だけを先にチェックするため、両方の存在を1回のエラーメッセージでは提示しない。
- 恒久対応: 実装なし (段8 自己改善候補として、orphan-hold 発生時に両 sidecar のパスを
  同時に提示するよう harness 側の改善を次タスク候補にする)。
- 再発検知: orphan-hold 発生時は `output/pegasus-dispatch/orphan-hold.json` と
  `<--out 値>.orphan-stop.json` の両方の存在を確認してから復旧完了と判断する。

### {{F:t972-independent-journal-validator-missed-by-consumer-search}}. resume classifier とは独立した第2の journal 検証機構を consumer 探索で見落とした [設計調査漏れ]

- 事象: 受入全走2回目で `test_degraded_launch_threads_expected_use_perf_to_every_consumer` が
  赤になった。原因は `s8b_ratified_freeze.py._JOURNAL_KEYS` (event 種別ごとの exact key
  allowlist、`_validate_journal` が使う) が `perf-preflight` event を未知として拒否していた
  ため。DW-O26 に従い journal 検証の consumer を探索した際、`_JOURNAL_KEYS`/`_validate_journal`
  自体は grep でヒットしていたが、具体的な識別子 (resume classifier の関数名など) での
  絞り込み検索を行った結果、この完全に独立した第2の検証系を誤って除外していた。
  `s8b_floor_contract.py` の resume classifier (`classify_journal_resume_state`) を安全拡張
  すれば journal 検証は尽くしたと誤認し、同じ journal.jsonl を検証するもう1つの独立した
  gate の存在に気づかなかった。
- 根本原因: 同一ファイル (journal.jsonl) に対して独立した複数の検証機構が並存している設計は
  grep ベースの consumer 探索では発見しづらい。「〜を検証する関数」という機能名での検索は
  同型だが別名・別モジュールの検証系を取りこぼす。
- 恒久対応: 実装なし (段8 自己改善候補として、journal/manifest 等の共有ファイルに対する
  consumer 探索は、機能名でなく「そのファイルを読む全 producer/consumer」を
  import グラフや `open()`/`json.load()` 呼び出し元から機械的に列挙する手法を検討する)。
- 再発検知: 共有ファイルへ新しい event/key を追加する変更では、そのファイルを読む全モジュールを
  ファイル名そのもの (`journal.jsonl`, `manifest.json` 等の文字列) で grep し、関数名の
  絞り込みより先に候補モジュール一覧を確定してから絞り込む。

### {{F:t972-closure-drift-recurred-twice-same-wave}}. 呼び出しグラフ inventory drift が同一 wave 内で2回連続発生した [検査見落とし]

- 事象: fix2 で `test_official_perf_closure.py::test_official_perf_surface_inventory_is_exact`
  の drift (未登録呼び出し1件) を解消したが、直後の fix3 (`_validate_journal` から
  `validate_perf_preflight_receipt` を呼ぶ新設コード) が別の未登録呼び出し関係を生み、
  受入全走2回目で再び同じテストが赤になった。
- 根本原因: このテストは AST ベースの exact match (`_production_predicates()` /
  `_expected_predicates()`) で「production コードのどの関数がどの関数を呼ぶか」を網羅登録する
  設計であり、fix のたびに新設した呼び出し関係を都度 `_REVIEWED_PREDICATES` へ追加登録しないと
  検出され続ける。1回 fix した経験から「もう drift は無い」と判断してしまい、fix3 の新設呼び出しを
  同じ観点で確認しなかった。
- 恒久対応: 実装なし (運用規律として、`_production_predicates()`/`_expected_predicates()` を
  直接呼ぶ確認スクリプトは既に確立済み。以後の fix では production コードへの追加行が新しい
  呼び出し関係を生むたびに、drift チェックを都度 (1回だけでなく fix 追加ごとに) 実行する)。
- 再発検知: production コードを変更する fix を追加するたびに、コミット前に
  `_production_predicates()`/`_expected_predicates()` を直接呼ぶ drift 検査を実行する。
  「前回 fix2 で直したから今回は無いはず」という推測で省略しない。

### {{F:focused-run-concurrent-dispatch-false-red}}. 受入以外の焦点走でも並行 dispatch が false red を出す [計測汚染]

- 事象: DW-O26 の consumer test 探索で、変更した test file 全体 (test_s8b_floor_campaign.py、
  9000行超) を単独走させた際、別の consumer test (test_official_perf_closure.py) を同時に
  dispatch していたところ 9 件の失敗が出た。同じ file を他の並行 dispatch なしで再実行すると
  401 passed, 2 skipped で全緑だった。9 件はいずれも本物の regression ではなく、隣接 dispatch
  との干渉による false red だった。
- 根本原因: 既存メモリ (no-concurrent-dispatch-during-acceptance) は「受入全走」中の並行
  dispatch 禁止として記録されていたが、通常の焦点走 (受入前の consumer test 確認) でも
  同型の干渉が起きることは未確認だった。
- 恒久対応: 実装なし (運用規律として、受入全走に限らず焦点走全般を並行 dispatch させない
  ことを次タスク候補にする)。
- 再発検知: 複数の焦点走を投入する際は、並行させず 1 本ずつ完了を待ってから次を投げる。
