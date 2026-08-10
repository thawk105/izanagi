# 実装プラン

指定された `brief.md` と `docs/phase3-8b-restart-runbook.md`、ならびに W-1 の正本である D86・D87・T-088 設計 §4 を読了した。HEAD は brief の基準 `118feb6d` と一致している。

以下は静的検査だけに基づく。ファイル編集・pytest 実走・緑判定は行っていない。

## 基本方針

- official の受理集合を広げる変更は W-1 の admission 成功時だけに限定する。
- T-749 は、oracle gate が既に受理している T-080 移行済み v1 bytes と単体 CLI の判定を一致させる。`verify()` 本体は緩めない。
- W-3/W-4 は候補 artifact の producer を追加するだけで、approval・active 化や既存 verifier の受理集合には触れない。
- W-3/W-4 の出力先は必須引数とし、既定の実凍結先を持たせない。書込みは create-only とする。
- docs、approval、active、実 `output/s8b-freeze/` への artifact 作成は実装子の所有外とする。

## W-1 [T-088] — 単一 official admission predicate

### 現行コード

[s8b_floor_campaign.py:207–217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:207) は無条件拒否である。

```python
def _assert_official_permitted(mode: str) -> None:
    ...
    if mode == "official":
        raise FloorCampaignError(
            "official mode は §8 ... core で無条件拒否する ..."
        )
```

同じ判断が [s8b_floor_campaign.py:3562–3569](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:3562) にもある。

```python
if args.mode == "official":
    print(json.dumps({"status": "refused", ...}))
    return 2
```

また、現在の official preflight は [s8b_floor_campaign.py:2983–3007](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:2983) にあり、[同:2970](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:2970) の campaign claim 取得より後である。D86 が問題にした「claim 消費後の admission 失敗」が残っている。

一方、job wrapper は既に次を検査している。

- receipt exact schema: [floor_campaign.sh:405–493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/tools/pegasus/floor_campaign.sh:405)
- 実行中 `$0` の SHA: [同:508–521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/tools/pegasus/floor_campaign.sh:508)
- HEAD と receipt revision: [同:524–537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/tools/pegasus/floor_campaign.sh:524)
- committed blob と receipt: [同:540–555](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/tools/pegasus/floor_campaign.sh:540)

ただし Python driver の起動 [同:961–964](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/tools/pegasus/floor_campaign.sh:961) には、実際の spool bytes を Python が独立再読できる入力がない。

### admission predicate の署名

```python
def _admit_official(
    *,
    protocol: Mapping[str, object],
    freeze: _freeze_io.VerifiedFreeze,
    started_at: dt.datetime | None,
    resume_dir: Path | None,
) -> _OfficialAdmissionSnapshot:
    ...
```

この署名に、次を入れてはならない。

- `permit`、`authorized`、`authorization`、`proof`
- `repo_root`
- `receipt_path`
- `spool_path`、`wrapper_path`
- caller 提供の `script_sha256`、`source_commit`、expected hash
- `environ`
- reader、git runner、preflight callable
- 現行の `_floor_preflight_fn`

`_OfficialAdmissionSnapshot` は predicate の検査結果を同一呼出し内で再利用するだけの非直列化 snapshot とする。これを別関数の入力にして official を許す「permit object」にはしない。

### admission の必要十分条件

`mode == "official"` の分岐から `_admit_official` を厳密に一度だけ呼び、以下をすべて満たす場合にのみ戻る。

1. `protocol` は `_validate_protocol_against_current` 済みで、`freeze` は exact `VerifiedFreeze`。freeze bytes SHA・schema・protocol の freeze pin が一致する。
2. repository root は固定 `ROOT`。環境の nonce から固定規約
   `output/env/pegasus/floor/attempts/submissions/{nonce}/submit-receipt.json`
   を内部導出する。
3. receipt は duplicate key/NaN を拒否して一度だけ読み、exact v1 schema、`dry_run is False`、nonce、normalized PBS job ID、固定 wrapper path、request、preflight capture を検査する。
4. `git rev-parse HEAD == receipt.source_commit`。
5. index と worktree は `output/` 外で clean。さらに loaded repository module の実 bytes を `source_commit:path` の blob と照合し、`assume-unchanged` 等で `git status` から隠れた drift も拒否する。
6. 次の三者の bytes SHA が完全一致する。
   - `source_commit:tools/pegasus/floor_campaign.sh` の committed blob
   - receipt の `job_script_sha256`
   - Python が固定 FD から直接読んだ scheduler spool bytes
7. fresh run では `_floor_preflight_freeze_allowlist` と `_official_launch_preflight` の二回 scan が成功する。
8. resume でも receipt/revision/spool admission は毎回必要とする。その後は既存 launch certificate v1 と既存 resume 検査をそのまま使い、schema を変更しない。
9. 失敗は `OfficialAdmissionError(FloorCampaignError)` に正規化し、campaign claim、run directory、certificate、journal の最初の書込みより前に終わる。

固定 spool FD は、例えば `9` とする。wrapper の driver 起動を次の形にし、hash や path を CLI/env で渡さない。

```bash
"$PY" ... s8b_floor_campaign.py --mode official --protocol ... 9<"$0"
```

Python は固定 FD 9 の bytes を読み、receipt/committed blob と独立比較する。既存の `IZANAGI_RESERVATION_SCRIPT_SHA256` は環境自己申告なので admission の根拠に数えない。

### file:line 変更計画

- [s8b_floor_campaign.py:41–48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:41)
  - 「official 無条件拒否」の module docstring を、単一 admission と既知限界へ更新する。
- [同:192–217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:192)
  - `OfficialAdmissionError` を追加し、`_assert_official_permitted` を上記 `_admit_official` へ置換する。
- [同:1392–1396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:1392)
  - dormant/無条件拒否という古いコメントを削除する。
- [同:2805–2830](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:2805)
  - `_run_campaign_core` から `_floor_preflight_fn` seam と旧 guard 呼出しを削除する。
  - official materializer 固定と public 13 seam 拒否は順序ごと維持する。
- [同:2881–3007](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:2881)
  - protocol/freeze/cell 検証後に `started_at` を一度捕捉し、claim 前に `_admit_official` を一度呼ぶ。
  - fresh の certificate と clean digest は snapshot を使い、後段で再評価しない。
- [同:3544–3585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_floor_campaign.py:3544)
  - CLI 固定拒否を削除。
  - `OfficialAdmissionError` だけを `{"status":"refused","reason":...}`、rc=2 に翻訳。
  - その他の `FloorCampaignError` は従来どおり rc=1。
- `orchestrator/campaign/s8b_floor_submission_admission.py:1` 新設
  - strict receipt capture、commit/blob、loaded-module、clean 状態、固定 FD spool の read-only leaf を置く。
  - receipt schema を二重実装しないよう、既存 certified-writer admission と共有する。
- [certified_writer_admission.py:177–215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/certified_writer_admission.py:177)
  - `_admit_floor` の receipt/source 部分を新 leaf へ委譲する。既存 compute-site・calibration 検査は残す。
- [floor_campaign.sh:961–964](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/tools/pegasus/floor_campaign.sh:961)
  - driver に固定 FD で `$0` を渡す。
  - 既存 wrapper 側の receipt/HEAD/spool/clean 拒否は defense-in-depth として削除しない。

## T-749 — 単体 verify CLI の T-080 receipt 対応

### 現行コード

[s8b_holdout_freeze.py:709–712](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_holdout_freeze.py:709) は常に現行 worktree と照合する。

```python
_verify_source(doc, "design_source", root, DESIGN_REL)
_verify_source(doc, "known_axes_freeze", root, KNOWN_AXES_REL)
_verify_source(doc, "generator", root, SCRIPT_REL)
_verify_head(head, root, current_head)
```

CLI も [同:870–872](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_holdout_freeze.py:870) でそのまま `verify(args.path)` を呼ぶ。

一方、T-080 の正規経路は次を提供済みである。

- `verify_receipt`: [t080_freeze_migration.py:1957–2056](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/t080_freeze_migration.py:1957)
- `static_gate_adapter`: [同:2077–2132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/t080_freeze_migration.py:2077)

### file:line 変更計画

- [s8b_holdout_freeze.py:9–25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_holdout_freeze.py:9)
  - direct CLI でも相対 import できる package bootstrap を追加し、`t080_freeze_migration` を import する。
- [同:826–838](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_holdout_freeze.py:826)
  - 既存 `verify()` と `verify_document()` は変更しない。
  - CLI 専用 `verify_cli_with_t080_receipt(path, *, root=ROOT)` を追加する。
- CLI helper の判定順:
  1. path が非 symlink regular file で、canonical active path `root / T080.HOLDOUT_REL` と exact 一致するか確認。
  2. holdout raw bytes を一度 capture。
  3. `verify_receipt(root=root)` を一度だけ呼ぶ。
  4. receipt に refusal がある、`invalid`、`issued-but-missing` なら即赤。legacy verifier へ戻さない。
  5. `never-issued` なら既存 `verify()` へ委譲する。
  6. `active-valid` かつ holdout raw SHA・known_axes record が receipt の固定値と exact 一致する場合だけ `static_gate_adapter` を呼ぶ。
  7. adapter refusal が空かつ observation 非 null の場合だけ成功。
  8. 発火条件外は既存 `verify()` へ戻す。したがって receipt にない drift は従来どおり赤。
  9. alternate path に同じ bytes をコピーしても receipt 例外を適用しない。
- [同:856–875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_holdout_freeze.py:856)
  - `verify` subcommand だけ新 helper を呼ぶ。
  - `generate`、`search`、programmatic `verify()` は不変。
- `s8b_oracle_driver.py` と `t080_freeze_migration.py` は編集しない。oracle の受理集合と既存 receipt 検査をそのまま正本とする。

## W-3 [T-750] — freeze v2 candidate producer

### 現行 verifier 契約

- filename: [s8b_ratified_freeze.py:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_ratified_freeze.py:85)
- exact top-level keys: [同:94–104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_ratified_freeze.py:94)
- transition table: [同:127–140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_ratified_freeze.py:127)
- structural parser: [同:846–872](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_ratified_freeze.py:846)
- semantic binding: [同:930–1007](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_ratified_freeze.py:930)
- supersedes chain: [同:1168–1186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_ratified_freeze.py:1168)

現状はテスト helper が手組みしているだけである。例えば [test_s8b_ratified_freeze.py:1145–1166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/tests/test_s8b_ratified_freeze.py:1145) が実質的な test-only producer である。

### 新 module

`orchestrator/campaign/s8b_freeze_candidate.py:1` を新設する。

```python
def build_candidate(
    *,
    generation_number: int,
    floor_protocol_path: str,
    floor_source_path: str,
    budget_path: Path,
    measurement_closure_manifest: Path,
    refreeze_note: str,
    parent_path: Path | None = None,
    root: Path = ROOT,
) -> FreezeCandidate:
    ...

def write_candidate(*, output_path: Path, candidate: FreezeCandidate) -> None:
    ...
```

production CLI は固定 `ROOT` を使い、`--root` を持たせない。

```text
build
  --generation-number N
  --parent PATH             # N>1 のみ必須。N=1 では禁止
  --floor-protocol REL
  --floor-source REL
  --budget PATH
  --measurement-closure PATH
  --refreeze-note TEXT
  --output PATH             # 必須、既定値なし
```

`measurement-closure` 入力は exact `{"canonical_paths":[...]}` とし、hash は producer が repo の実 bytes から計算する。caller 提供 hash は受け取らない。

### build の処理

1. `generation_number` は non-bool integer `>=1`。
2. g1 の親は固定 v1 path・固定 v1 SHA。`--parent` は拒否する。
3. gN、N>1 は `holdout_freeze.v2.g{N-1}.json` の strict parent を要求し、本文番号と raw SHA から `supersedes_sha256` を導く。
4. `frozen_at_head` は producer 実行時の exact HEAD。CLI から指定させない。
5. `design_source`、`generator`、`known_axes_freeze` は `HEAD:path` の committed blob と照合する。
   - g1 では transition が許す design/generator SHA を HEAD blob SHA へ更新。
   - gN では parent 値を維持し、HEAD blob と一致しなければ拒否。
6. protocol/result/closure path は canonical root-relative、非 symlink regular file。
7. result は strict JSON、exact result schema、`mode=="official"`、`eligible_for_refreeze is True`、protocol SHA、freeze/parent SHA、env、holdout/configuration 集合を検査する。
8. `s8b_floor_stats.verify_floor_artifact` で raw sessions から floor を再計算し、空 error の場合だけ採用。
9. candidate の `floor` は result の `floors[h]` から `diagnostics` を除き、exact
   `{by_holdout:{h:{pairs,scale_ref,scalar_alt}}}` へ射影する。
10. budget は入力 JSON の exact
    `{total_bench_s,per_holdout_bench_s,oracle_shared}` を要求する。有限非負、holdout exact、`oracle_shared is True`。
11. `floor_protocol`、`floor_source`、`measurement_closure` の hash は producer が実 bytes から計算する。
12. parent document を copy し、transition tableで許可された field だけを変更する。
13. `_parse_generation_document`、`_assert_transition`、`_verify_snapshot_layer1`、`_closure_entries`、`_validate_execution_snapshot` を書込み前に通す。
14. approval 系 key は一切追加しない。
15. deterministic JSON bytes を一度だけ組み立て、`output_path.name == holdout_freeze.v2.g{N}.json` を要求する。
16. create-only atomic write。既存 path は bytes が同じでも拒否する。
17. `approvals/`、`active/` へは書かない。candidate の生成後も `load_ratified_freeze` は `no-active` のままとする。

N>1 candidate の構造生成は可能にするが、既存 [s8b_ratified_freeze.py:2874–2877](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_ratified_freeze.py:2874) の `generation_number==1` launch 制限は変更しない。

## W-4 [T-750] — oracle manifest production CLI

### 現行コード

[s8b_oracle_manifest.py:693–769](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_oracle_manifest.py:693) に builder はある。

```python
def build_manifest(
    *, freeze_path, schedule, run_contract, binding_identity, campaign_ids,
    allowed_excluded_reasons, generator_versions, campaign_config_preimages=None,
) -> OfficialManifest:
```

[s8b_oracle_manifest.py:802–807](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_oracle_manifest.py:802) の writer は既に create-only である。一方、[s8b_oracle_driver.py:1552–1556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_oracle_driver.py:1552) は `run-block --manifest` を必須にしている。

### file:line 変更計画

- [s8b_oracle_manifest.py:3–23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_oracle_manifest.py:3)
  - `argparse`、`sys` と direct CLI package bootstrap を追加。
- [同:693–769](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_oracle_manifest.py:693)
  - `build_manifest` の意味論は変更しない。
- [同:802–807](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-integration/orchestrator/campaign/s8b_oracle_manifest.py:802)
  - 既存 `write_manifest` をそのまま CLI writer に使う。
- file 末尾に CLI を追加する。

```text
build
  --freeze PATH
  --spec PATH
  --output PATH
```

3 引数とも必須で、既定 output・`--root`・数値上書き面は作らない。

`--spec` は exact object とする。

```json
{
  "schedule": {},
  "run_contract": {},
  "binding_identity": [],
  "campaign_ids": {},
  "allowed_excluded_reasons": [],
  "generator_versions": {}
}
```

- extra/missing/duplicate key、NaN、非 object を拒否する。
- `campaign_config_preimages` は spec から受け取らず、既存 builder に再導出させる。
- CLI は必ず `build_manifest(...)` → `write_manifest(...)` の順で呼ぶ。
- 成功時は path、`manifest_id`、`manifest_sha256` を JSON 出力して rc=0。
- `ManifestError`、strict JSON error、既存 output は rc=1。
- argparse の構文エラーは rc=2。
- `verify_manifest`、oracle driver、report の受理意味論は変更しない。

## テスト変更一覧

### W-1

- `test_s8b_floor_campaign.py`
  - 正例: exact receipt、HEAD、clean tree、committed wrapper、固定 FD spool、selector preflight が一致すると official fresh core が完走する。
  - 負例: source revision mismatch。
  - 負例: spool bytes と committed blob の不一致。
  - 負例: missing FD、dry-run receipt、nonce/job ID mismatch、duplicate receipt key、dirty/hidden module drift。
  - 全負例で claim/run directory/certificate/journal が作られないことを固定。
  - admission が一回だけ呼ばれ、snapshot が後段で再利用されることを spy で固定。
  - public 13 seam の各拒否が admission より先に発火することを維持。
  - CLI admission failure=rc2、その他 campaign failure=rc1、success=rc0。
- `test_pegasus_floor_tools.py`
  - driver invocation が固定 FD から `$0` を渡すこと。
  - `--permit`、`--authorization`、spool path/hash 引数、spool hash env が存在しないこと。
  - 既存 wrapper の三者照合と source identity テストを維持。
- `test_campaign.py`
  - certified-writer の floor admission が共有 leaf へ移っても、既存 silent/read-only、source-drift、t126 非回帰を固定。
- `test_s8b_ratified_freeze.py`、`test_s8b_ratified_verify.py`
  - `_assert_official_permitted` と `_floor_preflight_fn` monkeypatch を、新 snapshot seam へ機械移行する。
  - ratified/launch/resume の期待値は変えない。

### T-749

- `test_s8b_holdout_freeze.py`
  - active-valid receipt + exact active legacy bytes + adapter successで CLI rc0。
  - programmatic `verify()` は同じ worktree drift を引き続き拒否。
  - never-issued、invalid、issued-but-missing、adapter refusal、raw drift、known_axes drift は rc1。
  - alternate path の同一 bytes は rc1。
  - receipt と adapter の呼出しが各一回であること。
  - direct script CLI で package import が成立すること。

### W-3

新設 `test_s8b_freeze_candidate.py`。

- g1 正例が exact key 集合、v1 supersedes、HEAD source blobs、floor projection、budget、closure、filename 規約を満たす。
- g2 正例は直前世代 raw hash を supersedes に持つ。ただし `launch_validate` の generation 1 制限は残る。
- pilot/`eligible_for_refreeze=False`/wrong protocol/wrong freeze/env/floor 再計算不一致を拒否。
- budget extra key、NaN、holdout 不足、`oracle_shared!=True` を拒否。
- closure 重複、path traversal、symlink、専用 role との衝突を拒否。
- parent gap・番号不一致・不正 supersedes を拒否。
- wrong output basename、既存 output を書込み前に拒否。
- candidate 単体では `load_ratified_freeze` が `no-active` を返す。
- `approvals/`・`active/` に書込みが無いことを filesystem snapshot で固定。

### W-4

- `test_s8b_oracle_manifest.py`
  - CLI 正例が builder と同一 document を create-only で書き、`verify_manifest` を通る。
  - spec missing/extra/duplicate key、NaN、null floor/budget を拒否。
  - existing output は非上書き。
  - generator SHA drift、binding/schedule/campaign ID 不整合が builder と同じ理由で赤。
- `test_s8b_oracle_driver.py`
  - CLI 生成 manifest を既存 `run-block --manifest` fixture が消費できること。
  - driver の gate、launch、budget 意味論には変更がないこと。

## ファイル所有の分割

| 子 | 編集ファイル |
|---|---|
| A — W-1 | `orchestrator/campaign/s8b_floor_campaign.py`、新 `s8b_floor_submission_admission.py`、`certified_writer_admission.py`、`tools/pegasus/floor_campaign.sh`、`test_s8b_floor_campaign.py`、`test_pegasus_floor_tools.py`、`test_campaign.py`、`test_s8b_ratified_freeze.py`、`test_s8b_ratified_verify.py` |
| B — T-749 + W-4 | `s8b_holdout_freeze.py`、`s8b_oracle_manifest.py`、`test_s8b_holdout_freeze.py`、`test_s8b_oracle_manifest.py`、`test_s8b_oracle_driver.py` |
| C — W-3 | 新 `s8b_freeze_candidate.py`、新 `test_s8b_freeze_candidate.py` |
| 親のみ | docs、worklog、phase check、commit |

この分割なら編集ファイル集合は素集合である。

共有 helper の取り合いは次のように閉じる。

- `certified_writer_admission._admit_floor` の receipt/source logic は A が新 leaf へ移す。B/C は触れない。
- T-080 の `verify_receipt` / `static_gate_adapter` は B が利用するだけで編集しない。oracle driver から helper を移動しない。
- C は `s8b_ratified_freeze` の structural validator と `s8b_oracle_manifest._validate_execution_snapshot` を read-only 利用する。B は manifest の validator 本文を変更せず CLI だけを末尾追加する。
- `orchestrator/tests/s8b_v2_freeze_fixture.py` は B/C 共用だが、どちらも編集しない。

## 波及の静的列挙

### W-1

- `_assert_official_permitted` の production callerは `_run_campaign_core` 一箇所。
- production CLI callerは `main`、外側の実 caller は `tools/pegasus/floor_campaign.sh`。
- 旧 monkeypatch consumer:
  - `test_s8b_floor_campaign.py:314,677,781,3209,3593,3856,4092,4232`
  - `test_s8b_ratified_freeze.py:748`
- `_floor_preflight_fn` consumer:
  - `test_s8b_floor_campaign.py:300,795,3220,3603,3863,4102,4191,4221`
  - `test_s8b_ratified_freeze.py:816`
  - `test_s8b_ratified_verify.py:1641`
- wrapper/receipt consumer:
  - `certified_writer_preflight.py`
  - `certified_writer_admission.py`
  - `test_campaign.py`
  - `test_pegasus_floor_tools.py`
- `submit_floor.sh` の receipt schema は変更不要。

### T-749

- `verify_document()` の caller は `verify()`。
- `verify()` の production caller は `s8b_oracle_driver.py:390` と CLI main。
- 今回変更するのは CLI main だけ。oracle driver は旧 `verify()` を fallback として保持する。
- shared fixture は `test_s8b_holdout_freeze.py` の synthetic freeze helpers と T-080 module。

### W-3

candidate の直接 caller は新 CLI のみ。人間が commit/approval/active 手順を行った後の consumer は次である。

- `s8b_ratified_freeze.resolve_active_generation`
- `load_ratified_freeze`
- `_verify_generation_semantics`
- `launch_validate` / `reverify_published_freeze`
- `s8b_oracle_driver` の gate/run-block
- `s8b_oracle_report`
- `s8b_oracle_manifest.build_manifest`

主要 consumer tests は `test_s8b_ratified_freeze.py`、`test_s8b_ratified_verify.py`、`test_s8b_oracle_driver.py`、`test_s8b_oracle_report.py`。

### W-4

現行 `build_manifest` caller はテストだけである。

- `test_s8b_oracle_manifest.py`
- `test_s8b_oracle_driver.py:1462`
- `test_s8b_oracle_report.py:201,298`

生成物の production consumer は次である。

- `s8b_oracle_driver.verify_manifest`: `:450`, `:1124`
- `s8b_oracle_driver run-block --manifest`: `:1553`
- `s8b_oracle_report.verify_manifest`: `:1757`

共有 fixture は `s8b_v2_freeze_fixture.py`。manifest・driver・report の三群が利用しているため変更しない。

## brief と現行コードの食い違い

- W-1 の A 所有を `s8b_floor_campaign.py` だけとする案では D87 を満たせない。Python driver には実 spool bytes を独立取得する経路がないため、最低でも `floor_campaign.sh` とそのテストが必要。
- wrapper、submission receipt、static certified-writer admission は既に存在する。W-1 は新しい認可 artifact を作る仕事ではなく、既存証拠を sole unlock predicate へ結ぶ仕事である。
- T-749 の恒常赤は `design_source` / `generator` だけではない。`frozen_at_head=2e20d441…` も dangling であり、receipt が受領済みである。
- T-749 で `verify()` 自体を緩めると、oracle driver の legacy fallback まで変わる。brief の「単体 CLI」を守るには CLI adapter を分離する必要がある。
- W-3 は production producer が無い点は正しいが、テスト内には既に複数の手組み producer がある。これらを正本に昇格せず、production module を単一源にする必要がある。
- `s8b_ratified_freeze.py` 冒頭は「semantic 検証は次段 W3」と書くが、現コードには `_verify_generation_semantics` が実装済みである。docstring が stale。
- W-3 の新 producer 自身を `generator.path` に記録することは現 transition table上できない。g1 でも変えられるのは `/generator/sha256` だけで、path は v1 の `s8b_holdout_freeze.py` のままになる。
- W-3 の budget 値をどこから導くかは brief に正本がない。現 repo にある `100/50` は test fixture の便宜値だけで、production 値として使えない。
- verifier は世代連鎖 N≥1 を扱うが、launch は `generation_number==1` に限定されている。producer が gN を組めても g2 以降は実走不能である。
- W-4 は CLI だけでなく、`schedule`、`binding_identity`、`campaign_ids` 等を作る production sourceも存在しない。今回の最小 scopeでは reviewed spec を明示入力とする必要がある。

## 総括

- A/B/C の編集ファイルは、A に wrapper と admission leaf の所有を追加し、C を新 module に閉じれば素集合にできる。
- W-1 は固定 FD による実 spool bytes、receipt、committed blob、HEAD/clean を一つの predicate で照合し、claim 前に一度だけ評価する。CLI はその失敗だけを rc=2 に翻訳する。
- T-749 は CLI 専用 adapter とし、active-valid T-080 receipt が exact legacy artifact を受領している場合だけ既知 drift を許す。`verify()` と oracle gate は緩めない。
- W-3 は explicit input・explicit output・create-only の candidate producerとし、approval/active は作らない。
- W-4 は exact reviewed spec を `build_manifest` へ渡す production CLI とし、builder/verifier の意味論は変えない。
- 実装前のユーザー裁定を推奨する点:
  - W-1 の spool bytes handoff を「固定 inherited FD」とし、A の所有を wrapper/helper まで広げてよいか。
  - W-3 の budget は既定値を持たず、明示された strict budget JSON を人間レビュー済み入力とするか。
  - W-3 は構造上 gN を生成可能にする一方、g2 以降の launch 拒否は現状維持でよいか。
  - W-4 は reviewed spec の明示入力を production source とみなすか。自動的な schedule/binding producerまで求めるなら別 scope が必要。