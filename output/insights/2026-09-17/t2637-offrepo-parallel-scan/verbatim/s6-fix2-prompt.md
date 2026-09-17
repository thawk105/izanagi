単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2637-impl

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2637-offrepo-parallel-scan/artifacts/dev-wave-t2637-offrepo-parallel-scan/s6-a.md` — レビュー A (GO、nit A1 / A2 / A3)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2637-offrepo-parallel-scan/artifacts/dev-wave-t2637-offrepo-parallel-scan/s6-b.md` — レビュー B (GO、nit B9 / B10 / B11)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2637-offrepo-parallel-scan/s6-fix-prompt.md` — 現行設計の仕様 (directory 1 個 = 1 task、work queue、walk key)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2637-offrepo-parallel-scan/s4-adjudication.md` — 段 4 裁定 (§2 実装仕様、§3 受理条件、§4 変異 matrix)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2637-impl/tools/audit_dangling_commits.py` — 編集対象 (現行 = 段 5 + 段 6 fix、未 commit)。`_process_offrepo_iteration` (910〜975)、`_merge_offrepo_candidates` (1094〜1115)、`_enumerate_offrepo_candidates` (1117〜1180)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2637-impl/orchestrator/tests/test_audit_dangling_commits.py` — 編集対象。`test_parallel_offrepo_scan_preserves_failure_counts` (1340 付近)、`test_parallel_offrepo_scan_preserves_first_seen` (1394〜1440)、`test_parallel_offrepo_scan_propagates_worker_exception` (1519〜1540)

repo root は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2637-impl` とする。**大きい file を全文 `cat` しないこと。** `grep -n` で位置を出し `sed -n` で 200 行以内ずつ読む。

## この段の仕事

レビュー 2 本は GO (must-fix 0) だった。次の nit 4 件だけを最小差分で直す。設計・受理集合・報告行は変えない。

1. **A1 / B11 — 同値 walk key の OID 挿入順。** 同じ file が複数 OID の候補になるとき (同 basename・同 size・同 mode の候補 metadata が複数)、file key が同値になり `sorted(keys, key=keys.__getitem__)` の安定 sort が辞書挿入順に依存して逐次版の OID 挿入順と異なりうる。逐次版は `same_prefilter` の候補列の順 (= `candidates` に現れた順) で OID を挿入する。**key に「同じ file 内での候補列の順番」を tie-break として含める** (例: key の末尾要素を `(0, filename, position)` にする、または key を `(walk_key, position)` の tuple にする)。`_process_offrepo_iteration` の `same_prefilter` の enumerate 位置を使う。`_merge_offrepo_candidates` と `ordered` 再構築の比較も同じ key で行う。`test_parallel_offrepo_scan_preserves_first_seen` に、同じ file が 2 つの OID (A, B) の候補で、別 file (hardlink) が B だけの候補になる fixture (レビュー A の反例: `R/a/deep/same.py` と `R/b/other.py` が hardlink、候補列 `same.py→A, same.py→B, other.py→B`) を足し、OID 挿入順 `[A, B]` を workers=4 で assert する。
2. **A2 / B10 — 同一 worker 内の複数 `onerror`。** `test_parallel_offrepo_scan_preserves_failure_counts` の読めない dir を workers (4) より多く (5 個以上) にし、workers=4 で少なくとも 1 worker が 2 回以上 `onerror` を経験する構成にする。期待 failures を更新 (入れ子 root の重複計数も含めて独立に手書き)。root 実行時は当該 assert だけ skip (既存の `os.geteuid() == 0` の扱いに合わせる)。
3. **A3 — M5 の局所 witness。** `test_parallel_offrepo_scan_preserves_first_seen` に、同じ worker が同一 group (同 inode の hardlink 2 path) の後順 task → 前順 task の順で処理する状況を固定する (task 処理関数を wrap し、workers=2 以上で片方の worker を Barrier で止め、もう片方に後順 task と前順 task を続けて処理させる)。代表 path が前順 (key 最小) になることを直接 assert する。
4. **B9 — 例外 test の join 検証。** `test_parallel_offrepo_scan_propagates_worker_exception` を、1 worker が例外を投げる間に別 worker がまだ task を処理中 (wrap で数百 ms 遅延) の構成にし、再送出が全 worker の終了を待ってから起きること (`threading.active_count()` の復元、または遅延 worker の完了 flag が再送出時点で立っている) を assert する。

**禁止:** 上の 4 件以外の変更 (production の他の関数、他の test、docs、`.claude/**`、`hooks/**`、他の `tools/**`、`conftest.py`)。`git add` / `git commit`。既存 test の期待値の変更 (段 5・6 の新設 test の中身は上の 4 件の範囲で変えてよい)。実根 `/work/1/SFC/tanab/dev-wave-jobs` の走査。テストを甘くして緑にすること。parametrize id は ASCII のみ。

## test の実走

`PYTHONPATH=. python3 orchestrator/tests/test_audit_dangling_commits.py` を走らせ、緑には実走件数を併記する。走らなければ「実装済み・未実走」と書き `closed` と書かない。各 nit について、検査を一時除去 (または tie-break を外す等の反実仮想) で赤化することを確かめて報告する。

## 完了報告に必ず含める

- 変更 file と関数の一覧 (file:line)。
- 実走した件数と結果。反実仮想の赤化結果 (4 件)。
- 変異 matrix M5 の対象行 (old の逐語) が変わったかどうか (key の形が変わるなら新しい old を書く)。

## 出力形式

**出力は file に書かず、最終メッセージの本文に全文を書け。** 見出しはすべて `##` (H2) で書き、最後の節は必ず `## 総括` とする。`### 総括` と書いてはならない。予算が尽きそうなら、その時点の結論を出力形式どおりに書いて終われ (無出力が最悪)。

節の順:

## 変更一覧
## 実走結果
## 変異 matrix への影響
## 総括
