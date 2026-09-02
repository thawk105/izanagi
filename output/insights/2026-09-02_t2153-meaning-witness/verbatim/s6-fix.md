## 閉じた所見

pytest が基盤障害で未実走のため、以下は実装完了ですが `closed` とは申告しません。

- fix-1: [condition_meaning_gate.py:2389](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:2389) で所有 TU 全体を計装し、実 CMake から導出した compile command を再利用。[同:2248](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:2248) の一時 shadow にだけ計装 TU を書き、元ソースは不変です。
- fix-2: [condition_meaning_gate.py:2213](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:2213) は開始行の一意性と挿入位置だけを決定。物理行による深さ計算と対応 `#endif` 探索を削除しました。
- fix-3: [test_condition_meaning_gate.py:738](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/tests/test_condition_meaning_gate.py:738) 以降へ前方 `#undef`、行継続、コメント、raw string、完了 marker 欠落の負例を追加しました。
- fix-4: [condition_meaning_gate.py:10](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:10) で主張境界を所有 TU の compile-time 枝選択へ限定し、[同:2563](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:2563) で専用 reason code を使用。[同:515](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:515) の admission コメントも `proof_kind` 境界へ修正しました。
- fix-5: [screening_driver.py:175](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/screening_driver.py:175) を `declaration=None` へ戻し、[test_screening_driver.py:227](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/tests/test_screening_driver.py:227) の追加検査も撤回。両ファイルは HEAD と完全一致しています。

## 変更した file

- [condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py): 所有 TU 全体の実 compile-command 前処理、限定 reason、証拠検査を実装。
- [test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/tests/test_condition_meaning_gate.py): 実 CMake・実コンパイラを使う正負例を追加。
- `screening_driver.py`、`test_screening_driver.py`: 段 5 の変更を差し戻したため最終差分なし。
- `s3_lock_coverage.py`、`s5_permutation_coverage.py`、`t152_write_intent_coverage.py` と対応テスト: 段 5 の未 commit 差分を維持し、本段では変更していません。
- docs、patches、external、台帳、`condition_gate_test_support.py` は変更していません。

## 走らせた検査

- `python3 tools/run_tests.py orchestrator/tests/test_condition_meaning_gate.py -k 'compile_time_branch_selection' -q`: `qstat -Q` の `EACCTAUTH Unknown user-id` により child 開始前 rc=16。node 実走 0 件で、実装済み・未実走です。
- `--collect-only` も同じく child 開始前 rc=16。pytest green は申告しません。
- 実 CMake・実 C++ コンパイラによる直接診断: 正例、前方 `#undef`、完了 marker 欠落、block comment、raw string、行継続、argv drift が想定結果。
- `py_compile`、production/test module import、`git diff --check`、`check_codex_agents.py`、`check_docs.py`: green。
- screening 2 file の HEAD 完全一致検査: green。

## 新しい負例の発火点

- 前方 `#undef`: [condition_meaning_gate.py:2412](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:2412) の全ソース計装を断片計装へ戻すと false-green。
- 行継続されたコメント内 `#endif`: [同:2460](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:2460) の計装所有 TU 入力を断片へ戻すと検査が崩れます。
- block comment／raw string 内の宣言行: [同:2313](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:2313) の展開用 marker と [同:2375](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:2375) のコンパイラ出力計数が発火点です。
- 完了 marker 不観測: [同:2494](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:2494) の `(1,1)/(0,1)` exact 検査を選択数だけへ緩めると green になります。
- 要求値以外の argv drift: [同:3025](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:3025) の正規化 argv 比較を外すと forged green が通ります。
- 開始指令重複と非識別は、それぞれ [同:2223](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:2223) と [同:2487](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2153-author/orchestrator/campaign/condition_meaning_gate.py:2487) に照準しています。

## 受理・拒否の挙動

段 5 で false-green だった、所有 TU 前方の `#undef`、コメントや raw string 内の擬似指令、行継続で外側条件内に残る指令は red になります。

有効な入れ子や前方 block comment は、物理行 regex による誤拒否を受けず、コンパイラ観測が `(1,1)/(0,1)` なら green です。対象 8 macro、未登録 macro、旧 BACKOFF 宣言の受理境界は維持しています。

screening は従来どおり `unestablished` で、実効配線は S3・S5・T152 の3面だけです。

## 波及の可能性

- compile-time evidence の proof kind、reason code、witness ID、record/admission ID は変わります。
- compile-time witness は CMake configure を伴うため、3 driver の preflight 時間が増えます。
- reason code や evidence schema を独自に exact 解釈する所有外 consumer は追随が必要です。
- 共有 fixture は利用のみで変更なし。legacy BACKOFF caller と screening の挙動は不変です。
- 新 test node の所要時間台帳追随は段 7 の親作業として残ります。

## 総括

fix-1 から fix-5 の実装変更は完了しました。  
screening 差分は完全に撤回済みです。  
許可外 file、docs、patch、CCBench、台帳、commit は触っていません。  
pytest は基盤障害で未実走のため、所見を `closed` とは申告しません。