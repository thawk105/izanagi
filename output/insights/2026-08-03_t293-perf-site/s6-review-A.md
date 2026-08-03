結論は **NO-GO**。静的レビューで must-fix 3 件です。pytest、probe、PBS job は実行していません。

## 所見

### 1. 実コードを測定できなくても `ok=true`・終了 0 になる

`file:line`: [t293_perf_site_probe.py:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:145)、[同:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:169)、[同:181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:181)、[同:221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:221)、[同:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:225)

**深刻度:** must-fix

**成果物影響:** 実コードを一度も呼べなかった artifact まで「実コード実測済み」として材料レポート・台帳・ユーザー裁定の受理集合へ入り得る。

**失敗シナリオ:** `qualification.submission` の import が依存欠落などで失敗する。二つの `real_*` field にはエラーが入るが、その後 `simulated_smoke` を skip し、無条件で `payload["ok"] = True`、rc 0 になる。PBS もその 0 を保存して成功終了する。

同じ問題は `_executable`、`prepare_toolchain`、独立 smoke の予期しない内部例外にもある。環境上の正常な否定結果と、測定器自体の故障を `except Exception` で同じ envelope に潰している。

`ok_semantics` は「測定手順を最後まで実行できた」と定義しているが、import 失敗や smoke 例外ではその定義自体が偽である。また候補利用可否を表す独立した top-level verdict がなく、`ok=true` と job rc 0 が通常の成功に見える。

### 2. 「候補 2 本が機能する」は測っていない

`file:line`: [brief.md:8](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/brief.md:8)、[t293_perf_site_probe.py:141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:141)、[同:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:162)、[同:193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:193)、[submission.py:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/orchestrator/qualification/submission.py:73)

**深刻度:** must-fix

**成果物影響:** 非選択候補が壊れていても「policy の 2 本は現用可能」と材料レポートへ記録でき、D96 裁定で壊れた fallback を受理集合に残し得る。

**失敗シナリオ:** 2 本とも `exists/is_file/executable=true` だが、第1候補だけが正常、第2候補は `--version` または `perf stat` に失敗する。`_executable` は第1のファイルで `break` し、`prepare_toolchain` と独立 smoke もその選択済み path だけを実行する。第2候補は `os.access(X_OK)` までしか測られず、両方正常な場合と区別できない。

したがって、この実装が答えられるのは「production resolver が現在選んだ最初の候補」についてだけである。brief の問いを list-level usability に狭めるか、各候補を個別に実行して per-candidate verdict を出す必要がある。

### 3. marker は `prepare_toolchain` 実行の証拠にならない

`file:line`: [brief.md:46](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/brief.md:46)、[同:50](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/brief.md:50)、[t293_perf_site_probe.pbs:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:15)、[同:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:23)

**深刻度:** must-fix

**成果物影響:** probe 未実行・途中死の job を実コード測定済みとして台帳と裁定パッケージへ採用できる。

**失敗シナリオ:** marker を書いた直後、Python 起動前または実行中に job が kill／walltime 終了する。marker は残るが `prepare_toolchain` は呼ばれていない。さらに所見 1 の import 失敗なら、marker、`probe.rc=0`、会計上の正常終了まで揃い得る。

brief の「marker の実在で (a) を確かめる」は偽である。marker は計算ノードで shell が開始した証拠に限定し、実コード測定の受理には rc 0、parse 可能な JSON、期待 field の完備、エラー不在を別途要求すべきである。

### 4. `real_prepare_toolchain.ok` は perf の機能 verdict ではない

`file:line`: [brief.md:46](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/brief.md:46)、[t293_perf_site_probe.py:175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:175)、[submission.py:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/orchestrator/qualification/submission.py:105)

**深刻度:** should-fix

**成果物影響:** 材料レポートが cc／dependency の失敗を perf failure と取り違え、policy 変更方向の裁定を誤り得る。

**失敗シナリオ:** perf は正常だが `gcc-13` が無い、または perf smoke 後の gflags/glog 検査が失敗する。いずれも `real_prepare_toolchain.ok=false` で、安定した `failure_stage` field はなく、自由文メッセージの解析が必要になる。

`simulated_smoke` は field 名と `note` で模擬だと明示されている点はよい。しかし実態は argv の再実装であり、production の `<not supported>`／`<not counted>` 判定は適用せず raw 出力を置くだけである。brief の指示どおり裁定根拠の主軸にはできない。

### 5. 測定結果が期待 commit／policy hash に fail-closed で束縛されない

`file:line`: [brief.md:3](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/brief.md:3)、[同:38](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/brief.md:38)、[t293_perf_site_probe.pbs:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:23)、[t293_perf_site_probe.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:51)、[同:137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:137)

**深刻度:** should-fix

**成果物影響:** 別 checkout／別 policy を測った値が基準 commit の証拠として台帳へ結び付く可能性がある。

**失敗シナリオ:** qsub の cwd を取り違える、または投入後・実行前に共有 worktree の policy/submission が変わる。probe は実際の policy SHA を記録するが期待値と比較せず、依然 `ok=true`・rc 0 になる。

レビュー時点では HEAD `1a3604b126c853fc98426f0dbf67b7dde96fa3da`、policy SHA-256 `b1c42e493148517cf4adc055999c5706eb3f15500c57bfcb0dbfc2a36ac961ac` で brief と一致した。ただし job 自身はこの束縛を強制しない。

### 6. 事前登録した C1/M1 は false-success 経路を検出しない

`file:line`: [s4-adjudication.md:24](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s4-adjudication.md:24)、[同:29](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s4-adjudication.md:29)、[同:35](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s4-adjudication.md:35)、[t293_perf_site_probe.py:136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:136)、[同:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:162)

**深刻度:** should-fix

**成果物影響:** 変異台帳が top-level fail-closed を裏取りしたように見え、所見 1 を持つ実装を受理し得る。

**失敗シナリオ:** C1 と M1 の前後で `resolved` は反転しても、`ok=true`・rc 0 は不変である。したがって import failure／smoke failure が成功になる経路には検出力がない。また policy の read site は、候補表示用の line 136 と resolver 入力の line 162 に分かれている。どちらを `/bin/true` に変えるかで結果が異なり、現状の事前登録は単一 anchor になっていない。

## 実コード性・書込失敗の静的照合

- `_executable` は import した実物を直接呼んでいる。
- `prepare_toolchain` も実物を直接呼んでいる。
- 候補 path は `tools/pegasus/policy.json` から読み、probe 内へ候補 2 本を焼き込んではいない。
- `simulated_smoke` は独立再実装であることを field 名と `note` で明示している。
- `probe.json` 書込例外は `ok=false`・rc 4 へ変え、PBS は probe rc を終了値へ伝播する。書込失敗を無視する経路は見つからなかった。ただし部分ファイルの存在だけを成功判定にしてはならない。

## 総括

must-fix は **3 件**。

1. 実コードを測定できなくても `ok=true`・rc 0 になる。
2. 候補 2 本のうち非選択候補の機能を測っていない。
3. probe 前に書く marker を `prepare_toolchain` 実行証拠としている。

**計算ノード投入: NO-GO。** 現状では scheduler 上の正常終了さえ「実コード測定完了」を保証せず、brief が要求する候補 2 本の機能性にも答えない。計算資源を使う前に、少なくともこの 3 件を閉じて再レビューすべきである。

実際に全文を読んだファイル:

- `/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/brief.md`
- `/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s4-adjudication.md`
- `/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s5-impl.md`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/orchestrator/qualification/submission.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/run_probe.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/AGENTS.md`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/CLAUDE.md`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/.agents/skills/dev-wave/SKILL.md`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/.claude/commands/dev-wave.md`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/docs/dev-wave/workers.md`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/docs/dev-wave/core.md`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/docs/dev-wave/mutation.md`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/docs/dev-wave/operations.md`

関連箇所のみ読んだファイル:

- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/policy.json` の `perf_candidates` 周辺

なお consumer 検索時に `s6-review-B.log` の tool-log 断片が検索結果へ混入したが、B の最終レビュー本文・結論は読まず、本所見の根拠にも使用していない。