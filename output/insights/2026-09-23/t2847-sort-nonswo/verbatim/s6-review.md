## 所見

1. **must-fix — build 照合失敗時に、判定に必要な記録が消える。** [起動器:188](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:188) で作った記録は、[同:198](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:198) や [同:217](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:217) の照合が失敗すると返されない。呼び手も成功後にしか `result["builds"]` へ格納しないため、特に `CXX_DEFINES` 不一致時に configure argv、Cache、flags.make 原文を失う。[prereg:10](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/prereg.md:10) が要求する投入記録を、失敗例で残せない。**修正案:** 各 build の記録を照合前から result に保持し、失敗理由を追記して保存する。段 A の分類と rc=1 は維持する。

2. **should — C 行統計が verifier の受理する v3 を数えない。** [起動器:261](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:261) は 7 field のみを受理するが、[parse.py:355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-sort-nonswo/orchestrator/verifier/parse.py:355) は 7・10 field を受理し、どちらも `write_count` は field 6。現行 Silo の出力は [transaction.cc:594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-sort-nonswo/external/ccbench/cc/silo/transaction.cc:594) の 7 field なので予定 run では発火しない見込みだが、v3 では verifier が成功しても到達統計が取得不能になる。**修正案:** 7・10 field を受理し、両形式で `fields[6]` を読む。

3. **should — run 開始不能を「実行完了」と報告しうる。** [起動器:244](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:244) は `OSError` 等を捕まえて `rc=None` のまま返し、[同:407](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:407) はその trace を verifier に渡す。最後は [同:414](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:414) で launcher rc=0 となる。これは [実装依頼:35](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/codex/prompt-author.md:35) の「0＝実行完了」と合わない。**修正案:** 起動例外を run failure として記録し、verifier を呼ばず、launcher rc を非 0 にする。未実走行へ観測済みの分類を付けない。

4. **should — 出力先の準備失敗は `finally` の外にある。** [起動器:320](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:320) の `out.mkdir()`、空判定、`verifier.mkdir()` が失敗すると、`meta.json`・`result.json` を書く [同:430](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:430) に達せず、規定の rc=2 にもならない。**修正案:** 出力先準備を preflight の `try` 内へ移し、書ける状態になった後は両 JSON の書込みをそれぞれ試みる。

5. **nit — v3 を扱わない前提を実装報告が明示していない。** [実装報告:46](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/codex/s5-author.md:46) は C 行を「7 field」と断定しているが、verifier は v3 の 10 field も受理する。**修正案:** 所見 2 の修正と合わせて報告を訂正する。

## 照合結果

分類は [段 A:119–122](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:119)、[段 B:129–140](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:129)、[段 C:141–158](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:141)、[段 D:159–176](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:159) に対応する。対照の失敗優先、R3/R4 の対照依存、timeout → signal → 正 rc → verifier → I/N → S の順序、`=16`・`≥17`・各 `<` 境界、S＝serializable かつ certified、空履歴＝`stats.txns == 0` に食い違いは見つからなかった。rc と verdict の照合も [prereg:53–55](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/prereg.md:53) に沿う。

build argv は [s5 `_build_broken`:231–260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-sort-nonswo/orchestrator/campaign/s5_permutation_coverage.py:231) と指定の置換以外で一致する。gate と両 build は同じ [applied 文脈:388–391](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:388) にあり、`CXX_DEFINES = ... -DSORT_VARIANT=<v>` の照合は恒真・恒偽ではない。`applied` は body 例外時も [finally で復元](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-sort-nonswo/orchestrator/campaign/patchharness.py:260) する。

run は `subprocess.run` の timeout で直接の子プロセスを kill・wait し、通常終了の負の signal rc と経過秒を記録する。trace の環境・cwd・`log/`、timeout run の verifier 省略、verifier の argv・cwd・300 秒 timeout・1 run 1 回・Recorder 経由も s5 と一致する。差し替え名は記録され、s5 の関数本体は差し替えていない。予定された build・scratch・出力は out-dir 下で、repo tracked file への書込みは見つからなかった。

**過剰・削除:** 分類の独立 oracle 記録、依存物と compiler の準備、出力監査にはこの 1 回の投入で用途がある。削ってよい明確な不要機能は見つからなかった。

## 総括

**NO-GO。** 投入前の must-fix は **所見 1（build 不一致時にも実 argv・Cache・flags.make を保存すること）**。実走は行っておらず、上記は静的検査の結論である。