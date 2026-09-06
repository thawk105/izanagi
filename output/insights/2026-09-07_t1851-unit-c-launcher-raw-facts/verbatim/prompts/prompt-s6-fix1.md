単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s4-adjudication.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s4-adjudication.md` — 親の段 4 裁定 (4 節 plan v2 — C1a)。本 fix は 4 節 2 (副作用前の検査で `use_perf_from_receipt` を呼ぶ) の帰結として発火した在庫検査の赤を閉じる
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/focus-2-failure.txt` — 親の焦点走で出た赤の全文 (1 node)
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s5-launcher.patch` — 実装子の差分 (launcher が `use_perf_from_receipt` を `_checked_reservation_policy` で呼び、official + receipt + True を拒否する guard を持つ)
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/prompt-s5-launcher.md` — 実装子の契約 (本 fix も同じ権限境界・禁止事項を継承する)

作業 repository は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-c-fix1` (branch `fix-dev-wave-t1851-unit-c-1`、base `04f06d032` + 実装子 patch 適用済み、未 commit) である。コードはすべてこの worktree の中で読み書きする。

## 所有 path (これ以外は 1 byte も変更しない)

- `orchestrator/tests/test_official_perf_closure.py`

`s8b_floor_attempt_launcher.py`、`test_s8b_floor_attempt_launcher.py`、他の production / test file、docs は所有外である。所有外に必要な変更が見つかったら実装せず完了報告に書け。docs の編集と commit はしない。

## 依頼 — perf 参照 file の在庫検査へ launcher を登録する

赤: `test_official_perf_closure.py::test_outer_perf_file_and_added_guard_inventory_is_exact` が `unreviewed: orchestrator/campaign/s8b_floor_attempt_launcher.py` で落ちる。`_production_perf_files()` (`:516`) が、launcher の `_checked_reservation_policy` 内の `use_perf_from_receipt(...)` 呼出し (追跡対象 call) と `expected_use_perf` を含む `if` を検出したためである。設計どおりの発火であり、**検査の regex・意味・既存 entry は 1 つも変えない**。次を足す。

1. `_REVIEWED_PERF_FILES` (`:44-`) へ `"orchestrator/campaign/s8b_floor_attempt_launcher.py"` を、既存 entry と同じ形の理由 comment 付きで足す (例: perf の bool を receipt から機械導出して capture kwargs と照合するだけで、perf を起動しない。起動は `capture_measure_point` が持つ)。alphabetical な位置に置く。
2. `_REVIEWED_PREDICATES` (`:106-`) へ `_Predicate("A", "orchestrator/campaign/s8b_floor_attempt_launcher.py", "_checked_reservation_policy", "use_perf_from_receipt")` を足す (surface "A" は `s8b_floor_campaign._assert_perf_mode` と同じ導出鎖。**新しい surface 文字を作らない** — `test_official_perf_surface_inventory_is_exact` が surface 集合を exact に pin している)。count は現物の呼出し回数 (1 のはず) を AST で数えて確かめる。
3. `_REVIEWED_GUARDS` (`:266-`) へ `_GuardSpec("A", "orchestrator/campaign/s8b_floor_attempt_launcher.py", "_checked_reservation_policy", (<names>), (<guards>))` を足す。`names` と `guards` の値は推測せず、この file の `_production_guards()` (`:701-`) が launcher の現物から実際に導出する値 (ast.unparse 正規化後) を、`python3 -c` か小さな一時 script で**実測して**写す (一時 script は repo に残さない)。少なくとも `mode == 'official' and receipt is not None and expected_use_perf` 相当の guard と `capture_use_perf is not expected_use_perf` 相当の guard が入る。
4. 自走 harness `python3 orchestrator/tests/test_official_perf_closure.py` (`_run()` :916) を実走し、全 test が緑であることを確かめる (`PYTHONPATH=.` を付ける)。pytest wrapper は sandbox で動かないので試みても失敗するなら理由を書く。
5. 変異の非恒真性 (`test_outer_perf_file_mutations_are_not_tautologies`、`test_closure_inventory_mutations_are_not_tautologies`) が引き続き緑であることを確かめる。

## 検査・報告 (DW-S05-C を継承)

- 緑には実走 nodeid・範囲を併記する。実走不能なら「実装済み・未実走」と書く。
- 既存テストの期待値を変えない (反転・緩和・skip・削除は禁止)。赤なら登録が誤りとして報告して止まる。
- 期待値へ揮発 payload を焼き込まない。
- 完了報告に、所有外への波及 (無いはず) を静的列挙する。
- commit しない。docs を編集しない。

## 制約

- 出力へ結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力の最後に `## 総括` 節を置き、変更 file と行数、実走結果 (nodeid 範囲と passed / failed 件数)、所有外への波及を 8 行以内で書け。
