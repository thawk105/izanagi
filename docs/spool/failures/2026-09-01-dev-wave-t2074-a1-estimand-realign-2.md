---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t2074-a1-estimand-realign
seq: 2
---

## 新規

### {{F:child-worktree-sync-is-parent-duty}}. fix 子に worktree の同期をさせると sandbox の read-only `.git` で全損する [権限境界] [手順漏れ]

- 事象: 段 6 fix 3 巡目の prompt が子へ `git checkout -- .` と `git reset --hard <tip>` を
  実行させた。子は最初の command で落ち、資料の読取も修正も何もしないまま終了した。
  背景 log は空のまま rc=1 で、理由がどこにも出ないように見えた。
- 根本原因: linked worktree の `.git` は本体 repo 配下 (`<main>/.git/worktrees/<name>`) にあり、
  codex の workspace-write sandbox は cwd 配下しか書けない。
  `index.lock: Read-only file system` になる。子の権限境界の構造的帰結であって、
  子の判断ミスではない。
- 恒久対応: `DW-S05-C` が定める「実装子の prompt に入れる項目」の一つとして、
  **「親が対象 tip へ同期済みである」「git command を実行するな」を逐語で書く**を運用する。
  `DW-S05-A` 本文への収容は L1.5 の byte 予算に阻まれた (D782 の手順を最後まで適用し、
  意味等価な削減・別節・新規節のいずれも成立しないことを確認済み)。予算に空きが出た wave が
  同節へ畳む。
- 再発検知: 実装子・fix 子の prompt に `git checkout` / `git reset` / `git fetch` が
  含まれていないことを、投入前の親の点検項目にする。
- 補足 (理由の見つけ方): 背景 log が空で rc=1 のときは
  `<artifact-root>/<wave>/<job-id>/receipt.json` の `attempts[].failure_class` と
  同 directory の `attempt-0001.output.md` を読む。今回は `f43_fragment` と、
  子自身が書いた停止理由の逐語がそこにあった。

### {{F:child-cannot-run-tests-hides-trivial-defects}}. 実走できない子の静的検査は import 漏れを通す [検証の穴]

- 事象: 段 6 fix 3 巡目は 2 つの test file を 224 行書き換え、静的検査 (AST parse、
  call site の数え上げ) を自分で通したうえで返した。しかし `collections.Counter` の
  import を落としており、親の全走で `NameError: name 'Counter' is not defined` が出た。
  検出に全走 1 回 (7 分 25 秒 + queue 待ち) を要した。
- 根本原因: codex の sandbox は計算ノードの queue を引けない
  (`qstat -Q preflight rc=1`、runner rc=16、`child_started=false`)。
  子は `DW-S05-C` に従い「実装済み・未実走」と正しく申告したが、
  **親が統合前に構文・名前解決だけでも実測する義務がどこにも書かれていない。**
- 恒久対応: 統合 script に、所有 file を import する最小の実測を組み込む。
  全走より 3 桁安い。`DW-S05-C` 本文への収容は L1.5 の byte 予算に阻まれた。
- 再発検知: 統合 script に、所有 file を import する最小の実測を組み込む。

### {{F:mutation-drift-mask}}. 自己 blob 束縛が変異の単一理由性を壊し、冗長 gate 386 件を生む [恒真ゲート] [測定の歪み]

- 事象: 変異 harness を repo 内の production file へ当てると、狙った gate と無関係に
  **386 node が一律で赤になる**。`pipeline.py` を変異させた場合の実測値である。
  内訳は contract loader の drift 群 384 件、worktree 変更そのものを拒否する検査 1 件
  (`test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes`)、
  no-touch manifest 1 件 (`test_paper_story_a1_headline.py::test_existing_a1_non_touch_manifest_is_empty_from_base`)。
- 根本原因: 変異 harness は固定 commit の worktree で file を書き換えるが、
  `campaign_lock.py` の `CONTRACT_LOADER_RELATIVE_PATHS` と source closure は
  disk bytes が HEAD blob と一致することを要求する。変異は必ずこれを破る。
  結果として `DW-M01` が要求する「無効化時の赤理由が一つに絞れる」が成立しない。
- 恒久対応: `DW-M03` の「冗長 gate と明記して単独変異の証拠から外す」に従い、
  runner argv の `--deselect` で冗長 gate を外してから本走する。
  冗長 gate の集合は**推測せず、少数の変異を SURVIVED 期待で走らせて実測する**。
- 再発検知: 変異本走の前に較正走 (2 変異) を挟み、その回の冗長 gate 集合を実測する。
  本 wave では main 取り込みで集合が 383 → 386 へ増えており、
  較正を省いていれば `pipeline.py` 系 5 変異が全て食い違って 3 時間を失っていた。

### {{F:mutation-postcheck-unstable-under-parallel-sessions}}. 変異 harness の共有木事後検査は並行セッション下で必ず落ちる [外乱] [道具の前提ずれ]

- 事象: 変異 probe が 14 変異すべてを記録し終えた後、`rc=125`
  「source/main 共有木の観測 bytes が変化した」で落ちた。
- 根本原因: `tools/mutation_worktree.py` の事後検査は **primary worktree** と source の
  `git status --porcelain=v1 --untracked-files=all` と
  `git submodule status --recursive` の stdout bytes を走行前後で比較する。
  この機体では並行セッションが常時 worktree を作ったり畳んだりしており、
  主 worktree の untracked 一覧が数時間の走行中に動かない前提が成り立たない。
  submodule pointer は動いていないことを実測で確認した。
- 恒久対応: 変異の `--source-repo` を**独立 clone** にする。clone なら primary が clone 自身に
  なり、`git status -uall` が 0 行で安定する。`DW-O19` への収容は単節 byte 予算
  (残り 2 bytes) に阻まれたため、本項を手順の正本とする。submodule は
  `git -c protocol.file.allow=always` と URL の local 向け直しで network なしに引ける
  (main worktree 側は入れ子 submodule が未初期化なので、引き元は wave worktree にする)。
- 再発検知: 走行前に source と primary が同一 (= 独立 clone) であることを確認する。

### {{F:mutation-resume-cannot-recover-red-baseline}}. 変異 harness の `--resume` は赤い baseline から復帰できない [道具の前提ずれ]

- 事象: 変異本走の baseline が 1 件の赤 (`test_codex_worker_launch.py::test_limit_stop_is_never_accepted`、
  `codex_exit_code == -9` = 子 process の SIGKILL) で止まった。harness が出力した
  resume command をそのまま実行したところ、`baseline=0 run(s)` と表示して**即座に同じ理由で中止**した。
- 根本原因: `--resume` は記録済みの baseline 結果を再利用する。baseline が FAILED で
  記録されていると、走り直さずにその記録を読んで `production write を開始しない` へ落ちる。
  resume は「途中まで進んだ変異の続き」のための機構であって、baseline の赤からの復帰路ではない。
- 恒久対応: baseline が赤で止まったら、`DW-O19` の再走規則どおり**新しい scratch と
  `--out` / `--attempt-out`** で最初から走らせる。旧 container は `rm -rf` の後
  `git worktree prune` まで行う (登録残置は次走の共有木検査を止める)。
  `DW-M05` への収容は L1.5 の byte 予算に阻まれたため、本項を手順の正本とする。
- 再発検知: resume を打つ前に `baseline=N run(s)` の N を読む。0 なら resume では直らない。
- 補足: 元の赤自体は非決定的で、同 tip の全走は 39 分前に完全緑 (19212 passed) だった。
  計算ノードの高負荷 (並行セッション実測で load average 75) 下で子 process が
  SIGKILL される型である。

### {{F:recorded-node-id-does-not-round-trip-into-deselect}}. 記録側の node ID を `--deselect` へ渡しても静かに無視される [道具の前提ずれ] [恒真ゲート]

- 事象: 変異 harness が記録した失敗 node をそのまま `--deselect` へ渡したが、
  **5 件だけ外れず**、狙った gate 以外の赤が残って `DW-M08` の完全一致が成立しなかった。
  外れなかったのは parametrize id に改行と日本語を含む node である。
- 根本原因: 記録側は node ID を正規化しており、`\n` を `/n`、非 ASCII を `/uXXXX` へ
  置き換えている。この文字列は実際の node ID と一致しないため、
  pytest は**エラーも警告も出さずに無視する**。外れたつもりのまま走り、
  3 時間の走行が終わってから初めて食い違いとして現れる。
- 恒久対応: 外せない node は **file 単位の prefix deselect** へ置き換える
  (`--deselect` は node ID の前方一致を受け付ける)。置き換える前に、その file が
  狙った gate を 1 つも含まないことを確認する。
- 再発検知: deselect list を作った直後に、`::` より後ろに `/n` か `/u` を含む entry を
  機械的に洗い出す。含むものは file 単位へ畳む。
  本 wave では 386 件中 5 件が該当し、2 file に収まっていた。
