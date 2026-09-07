## 総括

条件付きで `t2364-20260907b` の投入は可です。Lustre で失敗した `RENAME_NOREPLACE` は、同一 directory 内の create-only hard link へ正しく退避されています。  
最も重い所見は、失敗・indeterminate の attempt に対しても `collect` が最終 leaf を公開し、再取得と図生成を妨げる点です。`finish-group` 後に full・plot-compatible であることを確認してから `collect` してください。  
submit tree は投入から collect 完了まで HEAD・policy・job body を固定する必要があります。wave worktree の編集は、新しい tracked destination を作成・変更しない範囲なら成立します。  
policy SHA-256 は実物でも `67dce5a785dfc52d5df9b773f7a65905a030b7bd61ab7706704e2ed8e85a0487` と一致しました。追加処理は syscall 数回で、6 時間 walltime への影響は無視できます。  
pytest は指示どおり未実行です。また、実行される job-body 本体と `run_campaign` 以下は射影外なので、その内部 primitive まで含む完全保証はできません。

## 所見

1. **失敗した attempt を無条件に collect すると、図にできない成果物が最終 leaf を占有する**

   - **主張:** 段 4 §5 の「終端後 finish-group、次いで collect」は条件分岐が必要です。1 workload 失敗なら partial、両方失敗または収集時検証失敗なら indeterminate になりますが、collector はいずれも `materialize` を呼びます。その後は同じ tracked destination を再利用できません。
   - **file:line の根拠:** [`paper_story_a2_certification.py:2007`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:2007) で partial/full completion を分岐し、[`paper_story_a2_certification.py:4654`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4654)–4694 はどの report でも materialize します。materialize は [`paper_story_a2_certification.py:4461`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4461) で既存 leaf を拒否します。plotter は [`plot_a2_certification.py:143`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:143) の full schema pair と、[`plot_a2_certification.py:485`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:485) 以下の全 cell を要求します。
   - **放置したときの成果物への影響:** partial/indeterminate certification が新 leaf を占有し、予定した四セル図を生成できず、次 attempt も同じ公開先へ collect できません。
   - **自己申告:** **must-fix（実行手順）**

2. **`finish-group` は raw manifest 公開後の失敗から同じ command では再開できない**

   - **主張:** terminal 確認や事前検証までの失敗は同 ID で再試行できますが、`raw-manifest.json` を書いた後、completion を書く前に失敗すると、再度の `finish-group` は manifest の `O_EXCL` で止まります。
   - **file:line の根拠:** manifest は [`paper_story_a2_certification.py:2013`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:2013)–2021 で completion より先に生成され、[`paper_story_a2_certification.py:3738`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:3738)–3740 から create-only writer を使います。completion/acquisition はその後の [`paper_story_a2_certification.py:2037`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:2037)–2039 です。
   - **放置したときの成果物への影響:** manifest だけ残った attempt は acquisition receipt を作れず、collect・図生成へ進めません。
   - **自己申告:** **must-fix（復旧手順）**

3. **「wave worktree は編集してよい」は destination 非接触という条件付き**

   - **主張:** provenance は同じ固定 submit tree の Python/policy を最後まで使えば成立します。ただし receipt chain は policy bytes SHA を照合せず、materialize は収集時 policy の bytes と destination を採用します。また wave 側で新 destination を先に作れば collect は失敗します。
   - **file:line の根拠:** submission receipt の必須項目には policy SHA がなく [`paper_story_a2_certification.py:1207`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:1207)、job body bytes だけは再照合されます（同:1229–1238）。materialize は収集時 policy bytes と destination を使います（[`paper_story_a2_certification.py:4458`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4458)–4474）。`--repo-root` は [`paper_story_a2_certification.py:4692`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4692) で materialize にだけ渡ります。
   - **放置したときの成果物への影響:** submit tree の policy を途中変更すると、認証結果の embedded policy・公開先が投入時契約と異なり、wave 側で destination を作ると成果物自体が公開されません。
   - **自己申告:** **must-fix（固定範囲の明文化）**

4. **射影だけでは job の後半にある全 filesystem primitive を列挙できない**

   - **主張:** 実際に qsub される `tools/pegasus/paper_story_a2_certification.sh` と、receipt 公開後に呼ばれる `run_campaign` 等の実装は射影されていません。先行 attempt は receipt 公開までしか到達していないため、特にその後半は今回の実走で未確認です。
   - **file:line の根拠:** policy の job body 指定は [`paper_story_a2_certification.v2.json:123`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.v2.json:123)、qsub 実行は [`submit_paper_story_a2_certification.sh:258`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/pegasus/submit_paper_story_a2_certification.sh:258)、`run_campaign` は condition receipt の後の [`paper_story_a2_certification.py:3473`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:3473) です。
   - **放置したときの成果物への影響:** 射影外の後半に Lustre 非対応 primitive があれば raw results が完成せず、図・results 節・認証結果はいずれも作れません。
   - **自己申告:** **must-fix（レビュー証拠の不足。実装欠陥を発見したという主張ではない）**

## filesystem 依存 primitive の全列挙

以下は射影された production code に直接現れる全件です。射影外 helper は別行で明示しています。

| 段階 | primitive | file:line | Lustre での扱い |
|---|---|---|---|
| submit 前 | `mktemp -d`、通常の shell redirection | [`submit…sh:207`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/pegasus/submit_paper_story_a2_certification.sh:207)–211 | 通常は `/tmp`。`O_TMPFILE` は不使用 |
| preregister | `mkdir(..., exist_ok=False)` | [`paper_story…py:821`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:821)–872 | 可。attempt ID の create-only 点 |
| submit | Bash `noclobber` による qsub 診断 file の排他的作成 | [`submit…sh:248`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/pegasus/submit_paper_story_a2_certification.sh:248)–256 | 可。実質 `O_EXCL` |
| 全 create-only file | `os.open(O_CREAT|O_EXCL)` | [`paper_story…py:914`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:914)–924 | 可。preregistration、request-id、raw、manifest、receipt、stage 内 file に使用 |
| durability | file `fsync`、directory `fsync` | [`paper_story…py:914`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:914)–936 | 可。先行 attempt もこの面は通過済み |
| condition receipt | `renameat2(RENAME_NOREPLACE)` | [`paper_story…py:947`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:947)–953、実体 4141–4159 | **不可。EINVAL**。今回の hard-link fallback が覆う |
| condition fallback | `os.link(staging, destination)` → `unlink(staging)` | [`paper_story…py:949`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:949)–959 | 可。親の Lustre 実測で既存名は EEXIST |
| raw root | create-only `mkdir` | [`paper_story…py:4594`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4594)–4610 | 可。同 ID の job 再実行を拒否 |
| condition gate 作業域 | `TemporaryDirectory` | [`paper_story…py:586`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:586)–605 | 通常は一時 FS。`O_TMPFILE` は不使用 |
| campaign 本体 | `patchharness.checkout/applied`、`run_campaign` | [`paper_story…py:596`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:596)、3473 | **射影外のため不明** |
| finish-group | raw manifest の `O_EXCL` 公開 | [`paper_story…py:3694`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:3694)–3740 | 可。ただし公開後は同 command で再開不能 |
| materialize | stage directory + stage 内 `O_EXCL` file | [`paper_story…py:4454`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4454)–4526 | 可 |
| materialize 初回公開 | `renameat2(RENAME_NOREPLACE)` | [`paper_story…py:4527`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4527)–4532 | **不可。EINVAL**。既存 fallback あり |
| materialize fallback | `O_EXCL` claim + `renameat2(flags=0)` | [`paper_story…py:4200`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:4200)–4236 | 可。Lustre で flags=0 は実測成功 |
| cleanup | `unlink`、`shutil.rmtree` | [`paper_story…py:956`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/orchestrator/campaign/paper_story_a2_certification.py:956)、4536–4538 | 可。未公開 staging は例外経路でも除去 |
| plot policy decode | `tempfile.mkstemp` + `unlink` | [`plot_a2_certification.py:157`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:157)–190 | 通常は `/tmp`。`O_TMPFILE` は不使用 |
| plot publish | same-directory `mkstemp` + `os.replace` | [`plot_a2_certification.py:755`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema/tools/plotting/plot_a2_certification.py:755)–780 | 可。通常 rename semantics。3 ファイル一括 atomic ではないが再実行可能 |
| 明示的不在 | `O_TMPFILE`、production の `os.rename` | 射影全体を検索 | 使用箇所なし |

新しい file fallback は、非 EINVAL をそのまま再送出し、`os.link` の例外も握り潰しません。staging と destination は `path.parent` から構成されるため同一 directory です。`os.link` 成功後の unlink/fsync 失敗では destination が残り得ますが、これは上記の「attempt 消費点」として扱う必要があります。

増えた job-side 処理は workload ごとに「失敗する renameat2 1 回、hard link 1 回、unlink 1 回」です。walltime への実質的影響はありません。

## 投入手順の検算

射影から埋められない値は次の3つです。

- `<SUBMIT_TREE_ABS>`: 親が固定する submit tree の絶対 path
- `<CCBENCH_ROOT_ABS>`、`<DEPENDENCY_PREFIX_SOURCE_ABS>`: 今回使う canonical source/prefix
- `<FIGURE_PREFIX_ABS>`: 段 4 には新図 prefix の実名がない

```bash
SUBMIT_TREE=<SUBMIT_TREE_ABS>
WAVE_ROOT=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2365-a2-plot-schema
ATTEMPT_ID=t2364-20260907b
ATTEMPT_ROOT=/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907b
CCBENCH_ROOT=<CCBENCH_ROOT_ABS>
DEPENDENCY_PREFIX_SOURCE=<DEPENDENCY_PREFIX_SOURCE_ABS>

cd "$SUBMIT_TREE"
PYTHON=python3.10 tools/pegasus/submit_paper_story_a2_certification.sh \
  --attempt-id "$ATTEMPT_ID" \
  --ccbench-root "$CCBENCH_ROOT" \
  --dependency-prefix-source "$DEPENDENCY_PREFIX_SOURCE"
```

終端後:

```bash
cd "$SUBMIT_TREE"
PYTHON=python3.10 tools/pegasus/submit_paper_story_a2_certification.sh \
  finish-group \
  --attempt-id "$ATTEMPT_ID"
```

`collect` 前に、既知の leaf 消費問題を避けるため同じ固定 tree で read-only に full result を導出します。

```bash
CURRENT_PIN=$(
  cd "$SUBMIT_TREE" &&
  python3.10 -B -c 'from orchestrator.campaign.pin import CURRENT_PIN; print(CURRENT_PIN)'
)

cd "$SUBMIT_TREE"
python3.10 -B - "$ATTEMPT_ROOT" "$CURRENT_PIN" <<'PY'
import pathlib
import sys
from orchestrator.campaign import paper_story_a2_certification as a2

root = pathlib.Path(sys.argv[1])
current_pin = sys.argv[2]
policy = a2.load_policy()
evidence = a2.validate_acquisition_bundle(
    policy, root / "receipts/acquisition.json", current_pin=current_pin
)
if evidence["acquisition_schema"] != a2.ACQUISITION_SCHEMA:
    raise SystemExit("not a full acquisition; do not collect into the canonical leaf")
if any(rc != 0 for rc in evidence["driver_rcs"].values()):
    raise SystemExit("driver failure; do not collect into the canonical leaf")
if (not evidence["raw_manifest_valid"]
        or evidence["raw_manifest_schema"] != a2.RAW_MANIFEST_SCHEMA):
    raise SystemExit("full current raw manifest unavailable; do not collect")
report = a2.collect_results(
    policy,
    evidence["raw_results"],
    attempt_id=evidence["attempt_id"],
    current_pin=current_pin,
    request_ids=evidence["request_ids"],
    frozen_files=evidence["raw_files"],
    attempt_root=root,
)
if report["status"] not in {"observed-positive", "reject"}:
    raise SystemExit(f"not plot-compatible: {report['status']}")
print(report["status"])
PY
```

上が成功した場合だけ collect:

```bash
cd "$SUBMIT_TREE"
python3.10 -B -m orchestrator.campaign.paper_story_a2_certification \
  collect \
  --attempt-root "$ATTEMPT_ROOT" \
  --current-pin "$CURRENT_PIN" \
  --acquisition-receipt "$ATTEMPT_ROOT/receipts/acquisition.json" \
  --repo-root "$WAVE_ROOT"
```

その後、次の2ファイルの実 SHA-256 を wave 側の `CANONICAL_SHA256` に追加して commit します。

```bash
CERT="$WAVE_ROOT/output/insights/2026-09-07_t2364-paper-story-a2-certification/certification.json"
RAW_MANIFEST="$WAVE_ROOT/output/insights/2026-09-07_t2364-paper-story-a2-certification/raw-manifest.json"
sha256sum "$CERT" "$RAW_MANIFEST"
```

図は pin entry を含む **wave tree の plotter** から、旧 default を使わず明示引数で生成します。

```bash
FIGURE_PREFIX=<FIGURE_PREFIX_ABS>

cd "$WAVE_ROOT"
python3.10 -B tools/plotting/plot_a2_certification.py \
  --measurement-root "$ATTEMPT_ROOT" \
  --certification "$CERT" \
  --raw-manifest "$RAW_MANIFEST" \
  "$FIGURE_PREFIX"
```

復旧区分は次のとおりです。

| 失敗点 | 同じ attempt ID |
|---|---|
| submitter の preregister 前（queue、clean tree、source pin 等） | 再利用可 |
| preregister 後の qsub、visibility、submission receipt 失敗 | 再利用不可。新 ID |
| compute-preflight または job body/run-workload 失敗 | full rerun は新 ID。旧 attempt は finish-group で閉じても canonical leaf へ collect しない |
| finish-group の terminal 判定・manifest 作成前 | 同 ID で finish-group 再試行可 |
| `raw-manifest.json` 作成後、completion 作成前 | 同じ finish-group では再開不可。新 ID が安全 |
| completion 作成済み、acquisition 未作成 | 同 ID で `record-acquisition` を直接実行可 |
| acquisition 作成後、materialize 公開前 | destination が無ければ同 ID で collect 再試行可 |
| destination 公開後（collect rc=2 や最終 fsync 失敗を含む） | 同じ destination では再試行不可。新 IDと新 destination、または明示的な旧 leaf 処置が必要 |
| plot の途中公開失敗 | `os.replace` なので同じ prefix で再実行可 |