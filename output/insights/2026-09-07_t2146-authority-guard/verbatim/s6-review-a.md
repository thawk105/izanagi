## 判定 (GO / NO-GO)

**NO-GO**。

静的検査のみ実施し、pytest は実行していない。親の `deny → allow = 0` corpus に無い、既存防護対象に対する具体的な `deny → allow` を 1 件確認した。また、親報告の既存テスト赤は実装欠陥ではないが、期待値を設計に合わせて更新するまで test gate は緑にならない。

## must-fix

| # | 判定 | 内容 | file:line | 成果物影響 |
|---|---|---|---|---|
| 1 | real | `perf -o FILE` 処理が出力 option/value の index を記録し、後段の既存 `_tree_violation()` からその値だけを除外している。直接検査は `_LEAF_RE` と authority しか見ないため、非-leaf の既存防護 tree が退化した。例: `perf stat -o output/exploration/namespace.json true`、`perf stat -o hooks/guard_bash.py true` は旧版では output value を `_tree_violation()` に通して deny、新版では allow。防護追加と無関係な既存拒否の弱化である。 | [guard_bash.py:2781](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2781)、[a1-vs-current.diff:679](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2146-authority-guard/a1-vs-current.diff:679) | Bash の受理集合に namespace marker・hooks・ccbench file を `perf` 出力で上書きする入力が加わり、exploration/official の参照、評価入力、以後の防壁が変化する。 |

## should-fix / nit

差分と呼び出し網羅については、上記 `perf` 退化を除き、無関係な allowlist・拒否条件・境界の削除は見つからなかった。`guard_write.py` の差分は authority 判定、引数伝播、説明文だけである。

呼び出し漏れの懸念は **refuted**。

- `guard_bash.py` の `_argument_hits_protected()` は 15 呼び出しすべてで `authority_cwd` と `authority_index` を渡している。[guard_bash.py:1436](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:1436)、[guard_bash.py:2829](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2829)
- `_tree_violation()` は 7 呼び出しすべて、`_read_only_check()` は 2 呼び出しすべて、redirect/tree 判定は各 1 呼び出しで authority 引数を伝播している。[guard_bash.py:2622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2622)、[guard_bash.py:2753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2753)
- `guard_write.py` は production の `classify_path()` 3 呼び出しすべてと `_decide_apply_patch()` に共有 index を渡す。[guard_write.py:336](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:336)、[guard_write.py:384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:384)
- `_is_read_only()` は検査対象内に caller がなく、互換 wrapper 自身は追加引数を完全伝播する。[guard_bash.py:2245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2245)

S1〜S7 の実装状況は次のとおり。

| 裁定 | 判定 | 静的確認 |
|---|---|---|
| S1 祖先破壊 | refuted（漏れなし） | `include_ancestors` 時に `_inside(root, candidate)` を評価し、破壊系へ渡している。[guard_bash.py:2375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2375)、[guard_bash.py:2622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2622) |
| S2 部分 glob | refuted（漏れなし） | glob 前の literal prefix と `root.startswith(prefix)` が実際に発火する。[guard_bash.py:2254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2254)、[guard_bash.py:2363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2363) |
| S3 inode alias | refuted（漏れなし） | 両 guard が regular-file inode index を持ち、各 `decide()` で共有 instance を生成する。[guard_bash.py:2288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2288)、[guard_bash.py:2724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2724)、[guard_write.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:83)、[guard_write.py:391](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:391) |
| S4 final symlink | refuted（裁定範囲内） | Delete/Move/rm/mv の source は authority 判定だけ final を解決せず、通常形は allow になる。[guard_bash.py:2563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2563)、[guard_write.py:356](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:356) |
| S5 全挿入点 | refuted（authority gate は存在） | fast path、redirect、tree、argument/read-only、perf、builder 分離、fallback の全箇所に authority 判定がある。ただし `perf` 変更が既存側を弱めた点は must-fix #1。[guard_bash.py:2723](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2723)、[guard_bash.py:2763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2763)、[guard_bash.py:2883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2883) |
| S6 path 境界 | refuted（漏れなし） | lexical/canonical とも component 境界付き `_inside()`。fallback regex も前後境界付き。[guard_bash.py:2284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2284)、[guard_write.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:47) |
| S7 固定定数 | refuted（漏れなし） | 両 guard が同じ固定 absolute module constant を直接使用し、argv/env/repo root から導出しない。[guard_bash.py:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:108)、[guard_write.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:47) |

M1〜M15 は、**M1、M3〜M15 の 14 個は静的に kill 可能**。M2 だけは事前登録時の独立した変異位置が実装上存在せず、15/15 という主張は支持できない。

| 変異 | 判定 | テストの歯 |
|---|---|---|
| M1 | real: kill | 全 Write 系で root・既存・未存在 path を実 `decide()` に通す。[test_hooks.py:1298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1298) |
| M2 | real: 非独立 | apply_patch も共通 `classify_path()` の authority unionを使う。`_decide_apply_patch()` から `authority_index=` だけを消しても、default が index を再生成するため等価変異になる。M1 と別の gate として再照準が必要。[guard_write.py:248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:248)、[guard_write.py:336](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:336)、[test_hooks.py:1320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1320) |
| M3/M7/M8 | real: kill | root・祖先・partial glob の三入力が tree detector を個別に要求する。[test_hooks.py:1364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1364) |
| M4 | real: kill | `cp`、`tee`、`truncate` が argument union を必要とする。ただし `mv` と `install` は tree 層でも拒否されるため、この二入力だけは M4 の歯ではない。[test_hooks.py:1380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1380)、[guard_bash.py:2586](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2586) |
| M5 | real: kill | redirect target は後段 args に残らないため、redirect OR を外すと四形すべて allow になる。[test_hooks.py:1346](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1346) |
| M6 | real: kill | fixed literal を含まない canonical/hardlink alias が fast-path authority trigger を要求する。[test_hooks.py:1404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1404)、[test_hooks.py:1480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1480) |
| M9 | real: kill | canonical 外の同一 inode を両 guard の本物の `decide()` に通す。[test_hooks.py:1404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1404) |
| M10 | real: kill | 未存在 child を持つ外部 symlink alias なので inode/lexical には相乗りしない。[test_hooks.py:1480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1480) |
| M11 | real: kill | authority 内の symlink から外へ escape する未存在 path で、canonical 側から独立している。[test_hooks.py:1496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1496) |
| M12 | real: kill | `decide()` を意図的に例外化し、実 `main()` fallback を通す。stub は対象機構を迂回せず、入口を強制している。[test_hooks.py:1578](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1578) |
| M13 | real: kill | `-copy`、`2`、job、worktree の正例が substring 境界変異を検出する。[test_hooks.py:1521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1521) |
| M14 | real: kill | apply_patch Delete/Move と Bash rm/mv の実 source 判定を通す。[test_hooks.py:1563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1563) |
| M15 | real: kill | four pure readers の allow を直接固定する。[test_hooks.py:1548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1548) |

追加テストの弱点は以下。

- real: T-2146 の 13 テストには authority 用 `perf -o` と builder exception 分離の固定がない。S5 の実装子報告には含まれるが、永続テストになっておらず、今回の `perf` 回帰も捕捉できなかった。[test_hooks.py:1283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1283)、[guard_bash.py:2779](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2779)、[guard_bash.py:2853](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2853)
- real: fallback の sibling 正例が永続テストにない。通常系の component boundary は検査するが、内部例外時に regex を substring 化する変異は捕捉しない。[test_hooks.py:1521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1521)、[test_hooks.py:1578](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1578)
- refuted: hardlink テストが性質だけを見て実体を名指ししない、という懸念は当たらない。固定定数の一致、実 public key、実 authority index を先に確認し、managed mount で link 作成不能な場合だけ detector を synthetic root へ切り替える。[test_hooks.py:1301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1301)、[test_hooks.py:1404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1404)

性能上は、index object は常に 2 本作るが、tree walk は lazy で各 instance 最大 1 回である。

- authority root が巨大な場合、既存 regular file を候補に含む各 `decide()` が authority 全体を走査し、時間・メモリとも authority 内 file 数に比例する。cross-decision cache はない。[guard_bash.py:2302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2302)、[guard_write.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:97)
- root 不在は空 index と扱い、walk しない。固定 root 配下への lexical 書込みは root 不在でも拒否する。
- root の `stat`・walk・entry stat が不能なら `_scan_failed=True` となり、既存 regular target を局所的に alias 扱いして fail-closed にする。無関係な既存 file への writer も拒否し得るが、未存在 target は index を load せず、この理由では拒否しない。[guard_bash.py:2307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2307)、[guard_write.py:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:102)

## 既存テストの赤の帰属

**(a) 期待値が新しい設計を反映していない。実装は per-candidate 再走査していない。**

`guard_bash.decide()` は hooks root と authority root 用の別 index を各 1 個生成する。[guard_bash.py:2724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2724) 各 index は `_loaded` を最初に立てるため、同一 instance の二度目以降は walk しない。[guard_bash.py:2302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2302)

赤いテストの command は同じ hooks hardlink を複数箇所に含む。fast phase で、

1. hooks alias 判定が hooks root を 1 回走査し、
2. authority alias でないことの判定が authority root を 1 回走査する。

したがって合計 2 は設計どおりである。[test_hooks.py:1195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1195) `guard_write` は hooks 判定で即 deny して authority 判定まで到達しないため 1 のままである。[guard_write.py:271](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:271)

単に `walk.call_count == 2` へ変更する案は不採用。hooks root を 2 回、authority root を 0 回でも緑になるため、元テストが守った「per-candidate 再走査禁止」を十分保持しない。

推奨は `walk.call_args_list` の第 1 引数を canonicalize し、次を個別に assert すること。

- `guard_write`: `{fixture/hooks: 1}`
- `guard_bash`: `{fixture/hooks: 1, fixed authority root: 1}`
- 総数もそれぞれ 1 / 2

これなら、同一 root の再走査、authority index の未使用、余分な第 3 index のすべてを検出できる。

## 裁定パッケージ候補

- authority root が将来巨大化する場合の上限・manifest・cross-decision cache 方針。cache は stale inode を保護対象から落とす危険があるため、本 wave で安易に導入せず別裁定とする。
- 既裁定どおり、秘密鍵と signer を別 OS principal / host / hardware signer に置く D906 実効境界、`pushd`・`env --chdir`・条件実行を扱う shell 状態模型、密着 `perf -oFILE`、copy-out 非対称は別 package のままとする。[s4-adjudication.md:131](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2146-authority-guard/s4-adjudication.md:131)

## 総括

authority 防護自体は S1〜S7 の採用機構を概ね忠実に実装し、全 production caller に引数が伝播している。しかし `perf -o FILE` の編集で既存 tree 防護を弱め、具体的な `deny → allow` を作っているため NO-GO である。

併せて、M2 は M1 から独立した変異になっておらず再照準が必要で、`perf`・builder・fallback sibling の永続テストが不足している。親報告の `count=2` は索引 2 本を各 1 回走査した結果であり、実装欠陥ではない。