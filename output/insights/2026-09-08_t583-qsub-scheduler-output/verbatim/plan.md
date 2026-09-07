## 結論

推奨は、`--scheduler-output-root` を追加せず、既存の `--repo-root` と実在する Git common-dir 配置で負例を作る最小案である。これなら公開 CLI、usage、receipt schema を変えず、実変更を repo 外 root の導出、封じ込め、`qsub_cmd` の `-o` / `-e` 追加に限定できる。

書き込み、commit、テスト実行は行っていない。確定済み裁定を覆す新事実も見つからなかった。

## `submit_certify.sh` の変更計画

行番号は現状基準。

1. `tools/pegasus/submit_certify.sh:5-10`

   `usage()` は一切変更しない。特に現行 8 行目の次の行を空白も含め逐語保存する。

   ```text
                            [--job-script PATH] [--rratio 20|50|80]
   ```

   `--scheduler-output-root` は追加しないため、引数解析 `tools/pegasus/submit_certify.sh:24-34` も変更しない。

2. `tools/pegasus/submit_certify.sh:84-88` の dirty gate 直後、`JOB_SCRIPT_SHA256` の前へ root 導出と封じ込めを挿入する。

   骨格は次のとおり。

   ```bash
   GIT_COMMON_DIR=$(
     git -C "$REPO_ROOT" rev-parse --path-format=absolute --git-common-dir
   ) || exit 2
   [[ "$GIT_COMMON_DIR" == /* ]] || {
     echo "git common dir is not absolute" >&2
     exit 2
   }

   GIT_COMMON_REPO=${GIT_COMMON_DIR%/.git}
   GIT_COMMON_REPO=$(realpath -e -- "$GIT_COMMON_REPO") || exit 2

   DEFAULT_SCHEDULER_OUTPUT_ROOT="$(
     dirname "$(dirname "$GIT_COMMON_DIR")"
   )/izanagi-job-evidence/calibration-certify"

   scheduler_root_is_outside_repositories() {
     local root=$1
     [[ "$root" != "$REPO_ROOT" && "$root" != "$REPO_ROOT/"* \
         && "$root" != "$GIT_COMMON_REPO" \
         && "$root" != "$GIT_COMMON_REPO/"* ]]
   }

   [[ "$DEFAULT_SCHEDULER_OUTPUT_ROOT" == /* ]] || {
     echo "scheduler output root is not absolute" >&2
     exit 2
   }

   SCHEDULER_OUTPUT_ROOT=$(
     realpath -m -- "$DEFAULT_SCHEDULER_OUTPUT_ROOT"
   ) || exit 2

   scheduler_root_is_outside_repositories "$SCHEDULER_OUTPUT_ROOT" || {
     echo "scheduler output root must be outside repository roots" >&2
     exit 2
   }

   mkdir -p -m 0700 -- "$SCHEDULER_OUTPUT_ROOT" || {
     echo "scheduler output root is unavailable" >&2
     exit 2
   }

   SCHEDULER_OUTPUT_ROOT=$(
     realpath -e -- "$SCHEDULER_OUTPUT_ROOT"
   ) || exit 2

   scheduler_root_is_outside_repositories "$SCHEDULER_OUTPUT_ROOT" || {
     echo "scheduler output root must be outside repository roots" >&2
     exit 2
   }
   ```

   既定 root の式は `tools/pegasus/submit_b10_backoff_shape.sh:133-137` および `tools/pegasus/submit_floor.sh:562-565` と同形である。Git common dir を基準にするため、通常 checkout と linked worktree のどちらからでも共有 repo の兄弟にある `izanagi-job-evidence` を指す。

   `realpath -m` による正規化と最初の封じ込め判定を `mkdir` より前に置く。これにより、`..` や既存 symlink を経由して repo 内へ解決される候補を、repo 内へ directory を作る前に拒否できる。作成後にも `realpath -e` と同じ封じ込め判定を行い、実際に `qsub` へ渡すのは正規化済み絶対 path とする。

3. `tools/pegasus/submit_certify.sh:175-179` の `qsub_cmd` 構築箇所を変更する。

   ```bash
   SCHEDULER_STDOUT="$SCHEDULER_OUTPUT_ROOT/$NONCE.scheduler.stdout"
   SCHEDULER_STDERR="$SCHEDULER_OUTPUT_ROOT/$NONCE.scheduler.stderr"
   qsub_cmd=(
     qsub
     -o "$SCHEDULER_STDOUT"
     -e "$SCHEDULER_STDERR"
     -v "$export_spec"
     "$JOB_SCRIPT"
   )
   ```

   `-o` / `-e` の値は directory 自体ではなく、32 桁 nonce を basename に含む二つの file path になる。これは `tools/pegasus/submit_b10_backoff_shape.sh:232-234` の `scheduler.stdout` / `scheduler.stderr` と同じ qsub argv 形であり、`docs/pegasus-runbook.md:1585-1590` の規範を満たす。

4. repo 内判定は既存 staging 作成 `tools/pegasus/submit_certify.sh:96-104` より前へ置く。

   負例では判定用 root が repo 内へ正規化された時点で rc=2 とし、scheduler root の `mkdir`、attempt staging、preflight、`pre-submit.json` 作成、`qsub command:` 出力、qsub 実行のすべてへ進ませない。

## 正例テストの計画

`orchestrator/tests/test_pegasus_calibration_workload.py:5-7` に fixture 作成と argv 解析用の `os`、`shlex`、`shutil` を追加する。必要なら nonce の形を見るため `re` も追加する。

`orchestrator/tests/test_pegasus_calibration_workload.py:15` の定数群直後へ、既存 `test_pegasus_tools.py:1564-1578` と同型の clean Git fixture helper を追加する。

- `tools/pegasus/` を一時 repo へ copyする。
- `git init`、local user config、`git add`、`git commit` で dirty gate を通る fixture にする。
- 実行環境から `PEGASUS_EFFECTIVE_CLOCK_TOLERANCE_PCT` と外部の `GIT_DIR` / `GIT_WORK_TREE` を除く。
- scheduler command は `--dry-run` により起動しない。

`orchestrator/tests/test_pegasus_calibration_workload.py:138` 付近、既存 submitter 負例の前へ、例えば次を追加する。

```python
def test_submitter_dry_run_routes_scheduler_files_outside_repo(
    tmp_path: Path,
) -> None:
    ...
```

実行 argv は次の形にする。

```text
submit_certify.sh
  --repo-root <通常の一時 Git repo>
  --attempts-root <一時 repo 外の attempts>
  --dry-run
```

主張は次のとおり。

- rc=0 であり、`qsub command:` 行がちょうど一つある。
- `shlex.split()` でその行を argv に戻し、`-o` と `-e` の直後の値を取得する。
- 両方が絶対 path で、fixture repo およびその Git common repo の配下でない。
- parent は、実際の `git rev-parse --path-format=absolute --git-common-dir` に precedent の式を適用した `<common-dir の二つ上>/izanagi-job-evidence/calibration-certify` と一致する。
- `-o` は `<同じ32桁nonce>.scheduler.stdout`、`-e` は `<同じnonce>.scheduler.stderr` であり、root directory そのものとは一致しない。
- source 文字列の存在ではなく、script 実走で組み立てられた qsub argv を検査する。
- dry-run なので scheduler の二つの leaf file は作成されず、qsub も実行されない。

## 負例テストの計画

同じ位置へ、例えば次を追加する。

```python
def test_submitter_rejects_repo_internal_derived_scheduler_root_before_side_effects(
    tmp_path: Path,
) -> None:
    ...
```

fixture は有効な Git repo を次の配置で作る。

```text
<fixture-repo>/
  .git                         # separate git dir を指す管理 file
  .git-store/.git/             # 実際の git common dir
  .gitignore                   # /.git-store/ を除外
  tools/pegasus/...
```

`git init --separate-git-dir <fixture-repo>/.git-store/.git <fixture-repo>` を使う。このとき precedent の式は `<fixture-repo>/izanagi-job-evidence/calibration-certify` となり、実在する通常の Git command が repo 内 root を導出する。

実行 argv は次の形とする。

```text
submit_certify.sh
  --repo-root <上記 fixture repo>
  --attempts-root <repo 外の negative-attempts>
  --dry-run
```

特別な `GIT_DIR` 環境変数や判定関数の mock は使わない。主張は次のとおり。

- 事前条件として、Git common dir から計算した候補が fixture repo 内にあることをテスト自身でも確認する。
- rc=2 で、stderr が scheduler output root の repo containment 拒否を名指しする。
- stdout に `qsub command:` がない。
- `negative-attempts` と候補の `izanagi-job-evidence` が作成されていない。

受理の含意: 通常の Git common-dir 配置から repo 外へ導出された root は同じ判定を通り、dry-run の qsub argv まで到達する。  
拒否の含意: repo 内へ導出された root だけが rc=2 で止まり、qsub command と staging のどちらにも到達しない。

通る正例は直前の `test_submitter_dry_run_routes_scheduler_files_outside_repo` である。この対照があるため、負例の述語は恒真ではない。

## 負例入力の到達可能性

この負例は shell 断片や固定文字列への単体 assert ではなく、Git が正式に提供する `--separate-git-dir` で作った clean repository に対する script 全体の実走である。

`submit_certify.sh` は既に `--repo-root` を受理するため、追加 CLI なしでこの経路へ到達できる。repo 内 root は現在まで scheduler の既定出力が submit directory に返っていた型でもあり、brief の `DW-O13` にある到達可能性とも整合する。

## 不変条件ごとの保全理由

- `usage()` の `[--job-script PATH] [--rratio 20|50|80]`: `tools/pegasus/submit_certify.sh:5-10` を編集しないため逐語保存される。
- dirty gate、RRATIO、export、schema: `tools/pegasus/submit_certify.sh:36-39`、`:84-87`、`:130-168`、`:175`、`:213-242` は変更せず、特に `':(exclude)output'` と `IZANAGI_CALIBRATION_RRATIO` を維持する。
- preflight 4 capture: `tools/pegasus/submit_certify.sh:115-128` の順序と `:170-173` の qsub 前停止を変更しない。
- `-o` / `-e` は file path: root の下へ nonce 付き `.scheduler.stdout` / `.scheduler.stderr` leaf を組み立て、root directory 自体は渡さない。
- 絶対かつ repo 外: Git common dir の絶対性を確認し、正規化前後の候補を repo root と Git common repo の双方に対して封じ込め検査する。
- `--dry-run`: 現行 `tools/pegasus/submit_certify.sh:181-185` を変更せず、qsub array の表示だけ行って実行しない。
- 正しさ gate: dirty、ratio、policy、preflight の既存 gateを緩めず、scheduler path に拒否条件を一つ追加するだけである。
- `pre-submit.json` / `submit-receipt.json`: Python へ渡す argv、payload field、schema version、書式を変更せず、scheduler path も追加しない。
- `':(exclude)output'`: 現行 `tools/pegasus/submit_certify.sh:84` を byte 単位で変更対象から外す。

## P1 から P4 の推奨

| 項目 | 推奨 | 理由 |
|---|---|---|
| P1 | 採る | common dir の二つ上から `izanagi-job-evidence` を導く形は `submit_b10_backoff_shape.sh:133-137` と同じで、worktree 固有 path を焼かない。`calibration-certify` と nonce 名により既存 attempts とは nonce で対応づけられる。 |
| P2 | 削る | 公開 CLI `--scheduler-output-root` の追加は、文字どおりには「投入時の引数 1 箇所」より広く、既存 CLI の受理集合も変える。既存 `--repo-root` と有効な separate-git-dir fixture で実判定の正負を撃てるため、override は不要である。 |
| P3 | 変える | `provision_durable_root` 全体の path 文字 whitelist、全 symlink 成分拒否、directory mode 再検査までは今回の狭い修正に対して厚い。最小形は、作成前の `realpath -m`、repo/common-repo containment、`mkdir -p -m 0700`、作成後の `realpath -e` と containment 再確認である。 |
| P4 | 採る | scheduler path を receipt へ足すと `pre-submit.json` / `submit-receipt.json` の schema と field が変わる。追跡は qsub command 行と共有 nonce で可能なので、今回は記録しない。 |

P2 の削除は、brief の成果物案にある override 部分を provisional 裁定として変更する提案である。確定済み D1291 の repo 外 file path、同一 commit の負例、他挙動不変は維持する。

## 影響を受ける既存テスト

焦点走の対象は参照関係から次の二つに限定できる。

- `orchestrator/tests/test_pegasus_calibration_workload.py`: `:10-12` で変更 script を直接束縛し、`:27-38` で usage、RRATIO、dirty gate、export を逐語検査し、`:58-67` で shell parse、`:139-156` で submitter を実走している。ここへ正例と負例を追加する。
- `orchestrator/tests/test_pegasus_tools.py`: `:124-131` の shell syntax、`:176-184` と `:692-700` の直接 source 参照、`:1564-1619` の clean fixture を使った dry-run 実走が変更 script を消費する。

`brief.md:52-54` が挙げる `orchestrator/tests/test_hooks.py` と `orchestrator/tests/test_check_docs.py` は、変更しない `admission_registry.json` の path/class consumer である。admission class を変えないため焦点走には含めず、実装段の通常 docs 完了検査で確認する。

実装後の焦点走は、この二つの test file を `tools/run_tests.py` 経由でまとめて実行する。今回は plan-only のため実行しない。

## dry-run と実投入の差

新しい root 導出、正規化、封じ込め、directory provision、`SCHEDULER_STDOUT` / `SCHEDULER_STDERR` の構築、qsub argv の表示は両経路で共通にする。

既存の分岐は維持する。

- dry-run は `tools/pegasus/submit_certify.sh:115-121` で preflight command を起動せず、`:181-185` で qsub を起動せず synthetic request ID を作る。scheduler leaf file は作成されない。
- 実投入は `:122-128` で preflight 4 command を実行し、`:186-195` で新しい `-o` / `-e` を含む qsub argv を実行する。scheduler が指定 leaf fileへ出力する。
- repo 内 root の拒否はこの分岐より前なので、dry-run と実投入の双方が同じ rc=2 判定で止まる。
- preflight 失敗後に qsub へ進まない既存順序は変えない。

## 裁定を覆す新事実

該当なし。

`submit_floor.sh` は repo 外 evidence root を `:562-565` で導く一方、scheduler 出力は repo 内 submission directory を `:639-649` で使っている。これは brief `:42-44` に既に記録済みの precedent の割れであり、D1291 の「repo 外」を変更する根拠にはならない。

## 総括

- common-dir precedent から repo 外 root を導き、nonce 付き stdout/stderr file path を `qsub_cmd` 一箇所へ追加する。
- 公開 override は追加せず、separate-git-dir fixture で repo 内候補への実判定を負例として通す。
- receipt、usage、dirty gate、RRATIO、export、preflight は変更しない。
- 最大の risk は root 正規化と directory 作成の順序であり、作成前 containment と正負の script 実走で固定する。