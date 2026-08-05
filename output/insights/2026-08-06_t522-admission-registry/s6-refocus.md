結論は **NO-GO**。静的再レビューのみで、テストは実行していない。親提示の実測結果は前提として扱うが、「緑」とは主張しない。

主な理由は、A1 に偽陽性退行があり、`check_docs` 側に stale pyc 経路が残り、さらに実際の mutation spec が課題文と不一致かつ exact failure-set を満たさないためである。

## 1. 所見ごとの対応表

番号は `stage6-reviewA.md` / `stage6-reviewB.md` の番号である。

### レビュー A

| # | 判定 | コード確認と根拠 |
|---:|---|---|
| A1 | **regressed** | 任意 path sanction は plain `dict`、canonical path、4 field、非空 plain `str`、class 閉集合で遮断され、lookup も subtree 限定になった（[guard_bash.py:228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/hooks/guard_bash.py:228)、[guard_bash.py:528](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/hooks/guard_bash.py:528)）。一方、`main()` の raw mention は command の役割を見ず、内部例外時に `rg tools/pegasus/README.md` や `echo tools.pegasus` まで rc=2 にする（[guard_bash.py:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/hooks/guard_bash.py:185)、[guard_bash.py:1567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/hooks/guard_bash.py:1567)）。元の穴は閉じたが偽陽性退行を導入した。また loader の空 `{}` は「正常・diagnostic なし」として受理される。 |
| A2 | **partial** | FIFO は `O_NONBLOCK`、regular 判定、bounded read、cleanup 正規化で閉じた（[pegasus_admission_registry.py:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/pegasus_admission_registry.py:37)、同:59）。しかし loader source と関数は依然 hook process 内で直接実行され、無限ループ、shared builtins・`sys.modules` 内容破壊に deadline はない（[guard_bash.py:215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/hooks/guard_bash.py:215)、同:227）。子プロセス監督は **not-done (親裁定)**（[stage6-fixA.md:23](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/out/stage6-fixA.md:23)）。 |
| A3 | **closed** | import machinery を通さず exact source bytes を `compile/exec` している（[guard_bash.py:213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/hooks/guard_bash.py:213)）。unchecked stale pyc の回帰 fixture も source 側の class を要求する（[test_hooks.py:1962](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_hooks.py:1962)）。ただしこれは hook consumer だけの閉鎖で、`check_docs` は別途後述の pyc 穴を持つ。 |
| A4 | **closed** | `None`、list、scalar、raising mapping、top-level/function の `SystemExit`・`KeyboardInterrupt`、entry lookup、sanctioned 導出を実 subprocess exact rc=2 で検査する（[test_hooks.py:1768](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_hooks.py:1768)、[test_hooks.py:1790](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_hooks.py:1790)）。 |
| A5 | **closed** | final symlink、directory、oversize、FIFO、permission error の実 hook fixtureと、regular/stat cap/bounded read の独立 detector がある（[test_hooks.py:1844](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_hooks.py:1844)、[test_hooks.py:1884](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_hooks.py:1884)）。 |
| A6 | **closed** | canonical bytes、順序、indent、改行、空 entries、不正 path、field 欠落・余分・空を loader と実 hook の両側で検査する（[test_hooks.py:1468](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_hooks.py:1468)、[test_hooks.py:1822](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_hooks.py:1822)）。 |
| A7 | **closed** | loader と wrapper の双方で Unicode category `Cc` を拒否する（[pegasus_admission_registry.py:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/pegasus_admission_registry.py:88)、[guard_bash.py:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/hooks/guard_bash.py:197)）。NUL/control fixture もある（[test_hooks.py:1453](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_hooks.py:1453)）。 |
| A8 | **not-done (親裁定)** | `fstat` は read 前の1回だけで、同一 inode の read 中書換えを照合する post-`fstat` はない（[pegasus_admission_registry.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/pegasus_admission_registry.py:41)、同:47）。 |
| A9 | **closed** | measured-table の missing/extra は path 集合、classification は「非 local-ok」という case 別 exact finding になった（[test_check_docs.py:1167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_check_docs.py:1167)）。旧誤 oracle は残っていない。 |

### レビュー B

| # | 判定 | コード確認と根拠 |
|---:|---|---|
| B1 | **closed** | A9 と同じく case 別 exact finding へ修正済み（[test_check_docs.py:1186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_check_docs.py:1186)）。 |
| B2 | **partial** | qsub 引数集合、site tag、宣言 site の一致により現行5 entryの `qsub-job-body` / `compute-only` swap は検出する（[check_docs.py:2810](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/check_docs.py:2810)、[test_check_docs.py:1275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_check_docs.py:1275)）。ただし独立 site golden はなく、宣言と command/tag を同時変更すれば意味上の site drift は通る。 |
| B3 | **partial** | 認識された fenced command は tag と宣言へ exact 結合される（[check_docs.py:2841](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/check_docs.py:2841)）。一方、`env qsub`、`python3.10`、shell prompt、wrapper 経由、平文手順は認識外で、README 自身も保証外と明記する（[README.md:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/pegasus/README.md:47)）。 |
| B4 | **partial** | 宣言表非空と大小文字・重複 slash・全角 slash は検出する（[check_docs.py:2970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/check_docs.py:2970)、同:3008）。しかし `P=tools/pegasus` と `python3 "$P/collect_receipt.py"` の行分割は今も lexical coverage を失わせる（[check_docs.py:2843](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/check_docs.py:2843)）。 |
| B5 | **partial** | `submit_silo_ladder_rung1.sh` の警告は独立 golden になり、削除・空表・非 canonical 化を検出する（[check_docs.py:2290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/check_docs.py:2290)、[test_check_docs.py:1098](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_check_docs.py:1098)）。ただし golden はこの1本だけで、unknown inventory 全体の完全性は保証しない。 |
| B6 | **closed** | registry class/evidence 変異について、projection・unknown・README・measured の巻き添え finding 集合を exact assert する（[test_check_docs.py:1019](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_check_docs.py:1019)）。 |
| B7 | **closed** | 診断は型名だけを使い、formatter と admission checker 全体が `BaseException` を捕捉する（[check_docs.py:2317](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/check_docs.py:2317)、[check_docs.py:3047](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/check_docs.py:3047)）。poisoned `__str__` control もある（[test_check_docs.py:900](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_check_docs.py:900)）。 |
| B8 | **partial** | URL・否定文・diff・code span control は追加された（[test_check_docs.py:1404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_check_docs.py:1404)）。しかし §7.0 内の全 pipe table に admission 用の `\|` 禁止を適用し、README 全文の禁止例まで非 canonical path finding にするため、偽陽性面が残る（[check_docs.py:2490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/check_docs.py:2490)、[check_docs.py:3008](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/check_docs.py:3008)）。 |
| B9 | **closed** | `local-ok` の grandfather 例外を明記し、README 冒頭も「job body の重い処理」に限定して login clone を開示した（[pegasus-runbook.md:358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/docs/pegasus-runbook.md:358)、[README.md:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/pegasus/README.md:4)）。 |
| B10 | **closed** | 拒否保証は LOGIN/SUSPECT と parser 認識綴りへ限定され、projection・配線・parser 非認識面も保証外と明記された（[pegasus-runbook.md:377](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/docs/pegasus-runbook.md:377)、同:420）。 |
| B11 | **partial** | `tools/README.md` 本文は registry、generic command gate、self site gate を正しく分離した（[tools/README.md:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/README.md:28)）。ただし分類 claim を書ける living docs の閉集合化は **not-done (親裁定)**（[stage4-ruling.md:164](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/stage4-ruling.md:164)）。 |
| B12 | **closed** | 3段目は blocked・未実証と冒頭から明記し、collector の compute 経路も実 artifact 未確認としている（[README.md:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/pegasus/README.md:9)、同:161）。 |
| B13 | **not-done (親裁定)** | registry は依然「compute work stays in job body」と書く一方、実 script は login で clone する（[admission_registry.json:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/pegasus/admission_registry.json:124)、[submit_silo_ladder_rung1.sh:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/pegasus/submit_silo_ladder_rung1.sh:150)）。`reason` / `primary_gate` 同期は明示的 scope 外（[stage4-ruling.md:161](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/stage4-ruling.md:161)）。 |

### 親裁定項目の確認

| 項目 | 判定 |
|---|---|
| loader の deadline 付き子プロセス監督 | **not-done (親裁定)** |
| A8 同一 inode の read 前後照合 | **not-done (親裁定)** |
| `reason` / `primary_gate` 同期 | **not-done (親裁定)** |
| hook 配線欠落を skip でなく失敗にする検査 | **not-done (親裁定)**。現在も `hooks` 欠落時は skip（[test_hooks.py:2558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_hooks.py:2558)）。 |
| 分類 claim を持つ living docs の閉集合化 | **not-done (親裁定)**。admission checker が直接読むのは runbook と Pegasus README だけ（[check_docs.py:3031](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/check_docs.py:3031)）。 |

## 2. fix が作った／残した穴

### `compile()` / `exec()` loader

現行 loader に限れば、`__file__` と `__name__` は正しく設定され、`__package__=""` でも相対 import を使わない。`exec` は `__builtins__` を自動挿入し、repo root も事前に `sys.path` へ追加されているため、正常 loader に対する即時退行は見つからない（[guard_bash.py:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/hooks/guard_bash.py:64)、[guard_bash.py:217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/hooks/guard_bash.py:217)）。

ただし次が残る。

- loader は shared builtins・`sys.modules`・`sys.path` と同じ process を使う。loader が builtins 内容を破壊したり停止した場合、finally の参照復元だけでは隔離できない。
- `sys.dont_write_bytecode` は保存・復元するだけで、source 実行前に `True` にしていない。現行 loader 自身の pyc は生成されないが、将来 sibling module を import すると pyc 面が再び生じ得る。
- `check_docs` consumer は今も `spec.loader.exec_module()` で loader を読むため、unchecked stale pyc が source より優先され得る（[check_docs.py:2338](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/check_docs.py:2338)）。hook の A3 fix と非対称で、これを攻撃する test もない。これは **must-fix**。

### wrapper と正常24 entry

現行24 entry はすべて canonical plain `str` path、plain `dict`、exact 4 field、閉集合 class なので、追加 postcondition により正常系が拒否される経路は見つからない。親の独立24×4比較とも整合する。

ただし wrapper は `loaded == {}` を拒否しない。全件検証が誤って空 mapping を返した場合、全 Pegasus を拒否する点は安全側だが、diagnostic が空の「正常 load」として扱われる（[guard_bash.py:227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/hooks/guard_bash.py:227)）。

### `O_NONBLOCK`

通常の regular file では `O_NONBLOCK` は read の blocking semantics を変えず、部分 read は既存 loop が EOF まで吸収する（[pegasus_admission_registry.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/pegasus_admission_registry.py:47)）。regular 判定後に通常ファイルが `EAGAIN` になる現実的経路は見つからない。ここは退行なし。

### `main()` の偽陽性

内部例外時の raw regex は「実行 target」ではなく単なる文字列 mention を拒否する。例えば `rg tools/pegasus/README.md` は通常許可だが、`decide()` や site 判定が `SystemExit` / `KeyboardInterrupt` を投げると rc=2 になる。現テストは `git status` と実行形 Pegasus command しか比較せず、benign mention control がない（[test_hooks.py:2273](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_hooks.py:2273)）。

### docs の正当編集を赤にする経路

- §7.0 に unrelated な CommonMark 表を追加し、cell 内の正当な escaped pipe `\|` を使うだけで admission finding になる。
- README に「`tools//pegasus/foo.py` は不正な綴り」と説明する禁止例を追加しても、全文の非 canonical scan により赤になる。
- `qsub ...` を正当な `env VAR=x qsub ...` や absolute qsub path に変えると command parser が qsub 引数と認識せず、宣言集合不一致になる（[check_docs.py:2468](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/check_docs.py:2468)、同:2891）。

### 新テストの検出力

全体が恒真な test function は見つからないが、弱い case はある。

- `test_bash_pegasus_wrapper_postcondition_fails_closed_in_subprocess[loader-unknown-class]` は class 閉集合検査を削っても、未知 class が local-ok でないため command が別理由で rc=2 となり通る。class 検査の一次 detector ではない（[test_hooks.py:1790](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_hooks.py:1790)）。
- projection mutation test は admission finding の件数だけを要求し、detail を固定しない（[test_check_docs.py:948](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/orchestrator/tests/test_check_docs.py:948)）。
- benign raw mention、`check_docs` stale pyc、split-variable target の detector はない。

## 3. 変異の帰属

以下では `H` を `orchestrator/tests/test_hooks.py`、`D` を `orchestrator/tests/test_check_docs.py` と略す。各 `H::...` / `D::...` は完全な pytest nodeid である。

| 変異 | 期待して赤になる nodeid | 一次／巻き添え判定 |
|---:|---|---|
| 1. 全件検証→部分成功 | `H::test_bash_pegasus_registry_failures_close_all_direct_entries[json-unknown-class]` | 課題文どおりなら単一一次 detector。invalid な `dispatch_compute` より前の2 entry が公開され、registry `{}` assertion が壊れる。 |
| 2. `BaseException`→`Exception` | `H::test_bash_pegasus_registry_failures_close_all_direct_entries[loader-system-exit]`、`H::test_bash_pegasus_loader_failures_are_denied_by_real_subprocess[loader-top-level-system-exit]`、同 `[loader-top-level-keyboard-interrupt]`、`[loader-system-exit]`、`[loader-keyboard-interrupt]`、`[loader-cleanup-system-exit]` | 複数。実 subprocess 群が一次で、in-process state test と cleanup caseが巻き添え。 |
| 3. wrapper の path/4 field/class 検査削除 | state test の `[loader-outside-local-ok]`、`[loader-extra-field]`、`[loader-unknown-class]`、subprocess test の `[loader-outside-local-ok]`、`[loader-extra-field]` | 複数。missing/empty は残る非空値検査で fail-closed、unknown-class の subprocess case は別理由 rc=2 のため赤にならない。 |
| 4. `O_NONBLOCK` 削除 | `H::test_pegasus_registry_file_boundary_closes_real_hook[fifo-no-writer]` | 単一一次 detector。subprocess の3秒 timeout が test failure になる。 |
| 5. runbook class 書換え | `D::test_real_repo_clean` | 単一。合成 projection mutation test は tracked runbook を読まないため赤にならない。 |
| 6. runbook evidence 書換え | `D::test_real_repo_clean` | 単一。projection 不一致が一次。 |
| 7. README 宣言行削除 | `D::test_real_repo_clean` | 単一。本文 mention ⊄ 宣言表が一次。 |
| 8. README site tag 書換え | `D::test_real_repo_clean` | 単一。現 spec の `qsub-job-body`→`login-direct` は tag/declaration 不一致。 |
| 9. main から checker 呼出し削除 | 後掲14 node | 多数。構造 detector だけでなく全 admission negative test が finding 蒸発で赤になる。単一帰属ではない。 |
| 10. JSON 1 entry class 書換え | `H::test_bash_pegasus_registry_schema_and_fixed_classes`、`H::test_bash_pegasus_registry_login_and_suspect_bits_are_pinned`、`H::test_bash_sanctioned_pegasus_paths_are_derived_from_registry`、`D::test_real_repo_clean` | hook golden・受理 bit・sanction 集合・docs projection の4層。明示的な冗長 gate。 |

変異9で赤になる14 nodeは次のとおり。

- `D::test_admission_registry_load_failures_are_one_fail_closed_finding`
- `D::test_admission_loader_system_exit_never_evaporates_checker`
- `D::test_admission_poisoned_exception_string_never_evaporates_checker`
- `D::test_admission_outer_wrapper_fail_closed_on_poisoned_subchecker`
- `D::test_admission_projection_mutations_each_have_one_primary_finding`
- `D::test_admission_registry_mutations_have_exact_attributed_finding_sets`
- `D::test_admission_unknown_table_rejects_non_unknown_and_incomplete_legacy_rows`
- `D::test_admission_unknown_table_requires_grandfather_warning_golden`
- `D::test_admission_measured_table_requires_exact_registry_path_set`
- `D::test_admission_runbook_orphan_pipe_row_is_rejected`
- `D::test_admission_readme_declaration_and_fenced_target_mutations_are_rejected`
- `D::test_admission_readme_site_tags_and_three_site_values_are_exact`
- `D::test_admission_readme_rejects_empty_and_noncanonical_path_surfaces`
- `D::test_admission_main_call_cannot_be_removed_without_evaporation_control_failing`

### 実 mutation spec の blocker

実際の [mutation-spec.json](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t522-admission-registry/mutation-spec.json:1) は課題文と一致していない。

- M1 は「部分成功」ではなく canonical byte 比較の無効化である（同:12）。したがって課題文の変異1は、現 matrix では実際には注入されず、**matrix 上の検出力はゼロ**。
- M3 は path 検査だけを外し、4 field/class 検査を外さない（同:57）。課題文の変異3を試していない。
- M2 の登録 expected nodes は `[loader-cleanup-system-exit]` を欠く（同:44）。
- M3 の登録 expected nodes は state test `[loader-outside-local-ok]` を欠く（同:64）。
- M9 は1 nodeだけを登録しているが、実際には上記14 nodeが失敗する（同:160）。

harness は失敗 node 集合の **exact equality** のときだけ `KILLED` とする（[mutation_harness.py:1177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t522-admission-registry/tools/mutation_harness.py:1177)）。従って現 spec を受入2ファイル全走で使うと、静的予測は次になる。

- M1: `KILLED` だが、課題文とは別変異
- M2: **MISMATCH**
- M3: **MISMATCH**
- M4〜M8: `KILLED`
- M9: **MISMATCH**
- M10: `KILLED`

## 総括

- **NO-GO**。A1 は安全穴を閉じたが、benign Pegasus mention を内部例外時に拒否する退行を作った。
- regressed 判定は A1。B 側は closed と partial が混在し、新しい明確な安全側 fail-open は見つからない。
- must-fix は `check_docs` の stale/unchecked pyc 経路と、raw mention 偽陽性。
- mutation spec の M1/M3 は課題文と別変異で、意図した検査を実走しない。
- M2/M3/M9 は expected failure-set が不正で、現 harness では `MISMATCH` 見込み。
- 正常24 entry の受理集合を縮める静的経路、および regular file に対する `O_NONBLOCK` 退行は見つからない。
- 子プロセス監督、同一 inode、配線欠落、散文同期、living-doc 閉集合は親裁定どおり未実装。
- 親提示の実測結果は覆さないが、本レビューではテストを実行しておらず、緑は主張しない。