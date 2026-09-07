# [T-583] qsub の scheduler 出力を repo 外へ向けた — 封じ込め gate は作らず、argv を実走検査する負例で守る

2026-09-08。branch `worktree-dev-wave-t583-qsub-oe`。base `0e02169b0`。実装 commit `461d44f2e`。
裁定の正本は `docs/decisions.md` の D1291。

## 0. この wave が主張すること・しないこと

**主張する:**

1. `tools/pegasus/submit_certify.sh` が `qsub` へ渡す引数へ `-o` / `-e` を足し、返り先を
   **repo 外の file path** にした (D1291 の実装)。
2. 返り先が repo の内側でないことを、**script を実走して qsub argv を解析する**テストで
   検査する。source 文字列の一致ではない。
3. 事前登録した 6 変異が全件 KILLED で、期待 node と完全一致した。**冗長 gate は無い** —
   `orchestrator/tests/test_pegasus_tools.py` も走らせたが 1 件も落ちておらず、これらの変異を
   捕まえているのは今回足した 2 本だけである。

**主張しない:**

- **NQSV がこの exact path を受理し、実際に leaf へ書くことを実証していない。** テストは
  `--dry-run` でしか走らず、qsub は起動されない。言えるのは argv 契約までである。
  repo 外 `/work` 配下への `-o` / `-e` がこの機体で動く証拠は §4 の既存実績に留める。
- **「qsub を実行しなかった」ことの因果を実証していない。** `--dry-run` 分岐は返り先の
  正しさとは独立で、何もしない qsub stub でも同じ観測になる。
- **任意の Git 配置に対する物理的な repo 外性を保証していない。** テストが確かめるのは
  現 fixture に対する字句的な配置である (§5 の残余)。

## 1. 直した内容

変更前 (`tools/pegasus/submit_certify.sh:176`):

```bash
qsub_cmd=(qsub -v "$export_spec" "$JOB_SCRIPT")
```

`-o` / `-e` を一つも渡していなかったため、scheduler 出力は呼出し元の cwd へ返っていた。

変更後 (追加は 6 行だけ):

```bash
GIT_COMMON_DIR=$(git -C "$REPO_ROOT" rev-parse --path-format=absolute --git-common-dir) || exit 2
SCHEDULER_OUTPUT_ROOT="$(dirname "$(dirname "$GIT_COMMON_DIR")")/izanagi-job-evidence/calibration-certify"
mkdir -p "$SCHEDULER_OUTPUT_ROOT"
...
SCHEDULER_STDOUT="$SCHEDULER_OUTPUT_ROOT/$NONCE.scheduler.stdout"
SCHEDULER_STDERR="$SCHEDULER_OUTPUT_ROOT/$NONCE.scheduler.stderr"
qsub_cmd=(qsub -o "$SCHEDULER_STDOUT" -e "$SCHEDULER_STDERR" -v "$export_spec" "$JOB_SCRIPT")
```

導出式は `tools/pegasus/submit_b10_backoff_shape.sh:136`、`tools/pegasus/submit_floor.sh:564`、
`tools/pegasus/floor_campaign.sh:56` と同形で、共有 git dir 起点なので worktree からでも同じ
root を指し、機体固有の絶対 path を repo へ持ち込まない。

同 script の他の挙動は変えていない — `usage()`、引数解析、`--rratio` 検査、dirty gate の
`':(exclude)output'`、preflight 4 capture の順序と qsub 前停止、`pre-submit.json` /
`submit-receipt.json` の payload と schema、`--dry-run` 分岐、export 変数。

## 2. 事故型の裏取り (実測)

D1291 の記述を現物で確かめた。

- scheduler 出力の実ファイル名は `certify_calibration.sh.o<ID>` / `.e<ID>` である。
  `output/env/pegasus/calibration/job-staging/0:892707.nqsv/` などに、手で移された現物が残っている。
- `.gitignore:11` の `*.o` は `certify_calibration.sh.o892707` に**一致しない** (末尾が `.o` ではなく
  `.o<数字列>` であるため)。`*.out` も、`.e<ID>` を拾う行も無い。
- したがって投入のたびに repo 直下へ untracked が 2 つ増え、受入の prerun-clean と変異 harness の
  clean tree 検査を落としていた。これは仮想リスクではなく記録された実運用の負担である。

**訂正:** 「submit directory = qsub 実行時の cwd = repo root」という一般化は**誤り**である。
`submit_certify.sh` は qsub の前に `REPO_ROOT` へ `cd` しない (script 内の `cd` は path 解決用の
サブシェルだけ)。対して `tools/pegasus/submit_floor.sh:664` は `cd "$REPO_ROOT"` の subshell で
qsub を実行する。正しくは「返り先は呼出し元の cwd であり、記録済み運用が repo root から投げていた
ので repo root だった」。段 3 の両レンズが独立に指摘し、親が両 script を直接読んで確認した。

## 3. 封じ込め gate を作らなかった理由

段 2 のプランと段 3 のレンズ B は、返り先が repo 内を指したら rc=2 で拒否する封じ込め判定と、
それを撃つ負例を提案した。**採らなかった。**理由は 3 つで、いずれも実測に基づく。

1. **裁定の文面。** D1291 は「直すのは投入時の引数 1 箇所である」、依頼引数は「仮想リスク向けの
   gate・検査・台帳・一般化の追加は scope 外」。rc=2 で拒否する判定は script の受理集合を変える
   新しい gate であり、両方に抵触する。
2. **循環。** レンズ B が「負例は恒真でない」と示した根拠は、変異 (m3) 判定を常に true にする・
   (m5) 判定を qsub 後へ動かす、で赤になることだった。しかし **その 2 つは gate が在って初めて
   存在する変異**である。gate を足し、gate を撃つ負例を足し、その負例が gate を守るから gate が
   要る、という循環になっていた。gate 無しで残る変異は、argv を実走で検査する側が捕捉する。
3. **守る先が実環境で到達不能。** gate が拒否する状態は「導出式が repo 内を指す repo 配置」で
   ある。段 3 レンズ A はその経路として submodule を挙げたが、**親が実測して否定した**:

   ```
   $ bash tools/pegasus/submit_certify.sh --repo-root <worktree>/external/ccbench --dry-run
   policy not found: <worktree>/external/ccbench/tools/pegasus/policy.json
   RC=2
   ```

   policy 検査 (script 45-48 行) が導出より前にあり、submodule を `--repo-root` に指す経路は
   そこで死ぬ。走行後の `git status --porcelain --untracked-files=all` は空で、副作用も無かった。
   残る経路は `git init --separate-git-dir` の repo だけで、izanagi はその配置を採っていない。

## 4. repo 外 root がこの機体で動く証拠 (既存実績)

`submit_b10_backoff_shape.sh` が使う同じ root には、NQSV が実際に書いた非空の出力が残っている。

```
10395 /work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/7af18e12b58328c1fd9145c7d0588791/scheduler.stdout
  550 /work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/7af18e12b58328c1fd9145c7d0588791/scheduler.stderr
```

同型が複数 submission にある。**ただしこれは既存 campaign の実績であって、本 wave が
新しい exact path で投入した証拠ではない** (§0 の「主張しない」)。

## 5. テストと、その検出力の限界

`orchestrator/tests/test_pegasus_calibration_workload.py` へ 2 本足した。いずれも `tmp_path` 配下に
clean な fixture repo を作り、複製した script を `--dry-run` で実走し、stdout の `qsub command:` 行を
`shlex.split` で argv へ戻して**実際の値**を検査する。fixture が `tmp_path` 配下にあるので、
実運用の `/work/1/SFC/tanab/izanagi-job-evidence/` は汚さない。

- 正例 `test_submit_dry_run_passes_scheduler_file_paths_to_qsub`:
  `-o` / `-e` の存在、絶対 path、`<32桁 nonce>.scheduler.stdout` / `.stderr` という leaf 名、
  両者の nonce 一致、root directory 自身と一致しないこと、親が期待 root と一致すること、
  期待 root が実際に directory として存在すること。
- 負例 `test_submit_dry_run_keeps_scheduler_output_outside_the_repository`:
  両 path が fixture repo とその git common repo に等しくなく、その配下でもないこと。

**期待 root はテスト側が `git rev-parse --path-format=absolute --git-common-dir` の結果へ
独立に `parent.parent` を当てて組み立てる。** 実装の式を読んでいないので、実装の導出だけを
壊す変異 (m5) で期待値が追随せず赤になる。

**残余 (段 3・段 6 のレビューが指摘し、親が real として受け入れたもの):**

- **負例に独自の検出力は無い。** この fixture では git common repo == fixture repo なので、
  正例の「親が期待 root と一致」が成り立てば負例の containment は論理的に導ける。実測でも、
  負例だけが赤になる変異は 1 件も無い。負例は依頼の要求 (返り先が repo 外であることの検査) を
  直接表現する可読性のために残す。**独自に守っているとは主張しない。**
- `Path.parents` は字句的な包含判定で `resolve()` を行わない。相対 path・`..`・symlink を含む
  入力では誤判定しうる。現 fixture では script が `pwd -P` 済み repo から絶対 common dir を取り、
  固定 suffix を連結するので、そうした値は生じない。
- 特殊文字 (空白・`,`・`:`) を含む root の fixture が無い。現実装は二重引用と Bash array で
  壊れないが、将来 quoting を退行させても文字種によっては緑のまま通りうる。
- fixture は `tools/pegasus` 全体を `copytree` するので、無関係な file の追加で遅くなる・
  壊れる余地がある。
- `mkdir -p` は preflight より前かつ `--dry-run` 分岐より前にあるので、後続が失敗した投入でも
  空の `calibration-certify` directory が残る。裁定した位置での `mkdir -p` そのものの帰結である。

## 6. 変異走 (6/6 KILLED、完全一致)

台帳は `mutation-spec.json` / `mutation-main-report.json`、probe は `mutation-probe-spec.json` /
`mutation-probe-report.json`。HEAD `461d44f2e`、baseline `PASSED` (rc=0、失敗 node ゼロ)。

runner argv には `orchestrator/tests/test_pegasus_tools.py` も入れた。そこに submit script を
dry-run する既存テストがあるので、それも赤くなるなら「赤理由が一つに絞れる」という主張が崩れる。
**実測では 1 件も落ちなかった** — 冗長 gate は無い。

| # | 変異 | 結果 | 期待 node (完全集合) |
|---|---|---|---|
| m1 | `-o "$SCHEDULER_STDOUT"` を qsub argv から削る | KILLED | 正例 + 負例 |
| m2 | `-e "$SCHEDULER_STDERR"` を qsub argv から削る | KILLED | 正例 + 負例 |
| m3 | `SCHEDULER_STDOUT` を `"$REPO_ROOT/$NONCE.scheduler.stdout"` へ差し替える | KILLED | 正例 + 負例 |
| m4 | `-o` の値を leaf でなく root directory にする | KILLED | 正例のみ |
| m5 | 導出の `dirname` を 2 段から 1 段へ減らす | KILLED | 正例 + 負例 |
| m6 | `mkdir -p "$SCHEDULER_OUTPUT_ROOT"` を削る | KILLED | 正例のみ |

**段 4 の事前登録の訂正:** 段 4 では「m3/m5 は負例が捕まえる」と書いたが、probe の実測でも
段 6 レンズ B の静的解析でも、正例・負例の**両方**が落ちる。期待 node は probe の観測値から
完全集合として登録し直した。

**`DW-M08` の新旧両走について:** m1〜m6 の変異対象行は変更前 HEAD に存在しないため、旧走は空である。
新テストだけが検出する差分を示す走行としては、旧 HEAD 側に当てる変異が定義できない。

## 7. 段 6 の must-fix 2 件

- **レンズ B 所見 1:** m1/m2 が `qsub_argv.index("-o")` の `ValueError` で落ちており、
  「argv に option が存在する」という契約を assert で検査していなかった。抽出の前に
  明示的な存在 assert を置いた。
- **レンズ A 所見 9 (親が nit から昇格):** テストが `mkdir -p` の存在を検査しておらず、
  その行を消しても dry-run では両テストが緑のまま通った。実投入では出力先が開けず job が
  落ちるので、`expected_root.is_dir()` を足した。これが m6 を KILLED にしている。

レンズ A の must-fix は 0 件だった。既存テストの弱体化 (反転・緩和・skip・削除) は無い。

## 8. 一次資料

`verbatim/` に段 1〜6 の子出力と親の brief・追補・裁定を逐語で置いた。
`brief.md` には §2 で訂正した誤った一般化がそのまま残っている (訂正の経緯を追えるようにするため)。
`ruling.md` §5 の変異事前登録は §6 のとおり訂正されている。
