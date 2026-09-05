## 結論

4 件の実装案は起草できますが、実装前に親裁定が必要な実在の衝突が 1 件あります。

`b10_backoff_shape_sweep.py` 自身の bytes が `analysis_code_sha256`、binding SHA、campaign identity に入ります。現行ファイルの SHA は `94d2cb...`、現行 binding は `b63b75...` ですが、残すべき write-heavy 45 セルは analysis SHA `34072f...`、binding `f0f9b2...` です。したがって、この driver を編集しつつ「binding hash / campaign identity を一切変えない」は両立しません。

以下は、この衝突を親が裁定することを前提とした実装プランです。書き込みと pytest 実走は行っていません。

## §6 (1) signal 処理

追加修正は不要です。

[tools/pegasus/b10_backoff_shape_campaign.sh:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/tools/pegasus/b10_backoff_shape_campaign.sh:107) の現行逐語は次です。

```bash
on_signal() {
  local name=$1 number=$2
  local rc=$((128 + number))
```

問題だった複合 `local` は 108–109 行に分離済みです。挙動テストも [test_b10_backoff_shape_sweep.py:1851](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/tests/test_b10_backoff_shape_sweep.py:1851) にあり、TERM から rc 143 と failure 引数を検査しています。本 wave ではこの箇所を触りません。

## 前提衝突: binding hash と campaign identity

現在の [b10_backoff_shape_sweep.py:213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:213) の anchor は次です。

```python
def core(self) -> dict[str, str]:
    return {
        "prereg_commit": self.prereg_commit,
        "prereg_blob_sha": self.prereg_blob_sha,
        "spec_sha256": self.spec_sha256,
        "patch_sha256": self.patch_sha256,
        "formula_sha256": self.formula_sha256,
        "analysis_code_sha256": self.analysis_code_sha256,
    }
```

[b10_backoff_shape_sweep.py:1377-1394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:1377) は現行 driver 全体を読み、SHA を binding に入れます。さらに [同:1476-1519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:1476) がその binding を `search_config` と campaign identity に流します。

実測値は次です。

- 現行 driver: analysis SHA `94d2cb330476...`、binding `b63b75ce1d5d...`
- 保存対象 write-heavy: analysis SHA `34072fb2a5a5...`、binding `f0f9b2a19417...`。根拠は [保存 provenance:14-15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/output/insights/2026-08-31_t1905-b10-formal-run/reports/write-heavy/b10_backoff_shape_provenance.json:14)

この driver に 1 byte でも変更を加えると、さらに別の binding / campaign ID になります。回避案として `analysis_code_sha256` を core から外す、旧 SHA を固定値化する、別 module の変更を hash 対象外にする、のいずれも正しさ束縛を緩めるため採れません。

推奨する親裁定は次です。

- 各既存 campaign の identity は書き換えない。
- 新しい balanced/read-heavy job は実装 commit の新しい binding / campaign ID で走ることを明示承認する。
- 旧 write-heavy `b10-backoff-shape-silo-write-heavy-formal-e3de15eb` だけを D1509 の限定例外として report collector が歴史 binding ごと読む。
- 分母の定義には campaign ID を入れず、完了記録の出所としてのみ ID を記す。

この裁定が得られない場合、今回要求された driver 編集には合法な実装形がありません。

## (2) 壁時計を 1 契約から派生させる

単一定数は JSON の [tools/pegasus/policy.json:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/tools/pegasus/policy.json:11) に置くのが最小です。

**現行 anchor**

```json
"finalize_reserve_s": 600,
```

**置き換え後**

```json
"finalize_reserve_s": 600,
"b10_backoff_shape_walltime_s": 43200,
```

`43200` の数値リテラルはここだけに置きます。

各 consumer の変更は次です。

1. [b10_backoff_shape_campaign.sh:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/tools/pegasus/b10_backoff_shape_campaign.sh:5)

   **現行 anchor**

   ```bash
   #PBS -l elapstim_req=12:00:00
   ```

   **置き換え後**

   Scheduler 指示行なので逐語を維持します。テストが `12:00:00` を秒へ変換し、JSON の `43200` と等しいことを検査します。

2. [b10_backoff_shape_campaign.sh:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/tools/pegasus/b10_backoff_shape_campaign.sh:60) の直後

   **現行 anchor**

   ```bash
   [[ -n "$PY" ]] || bootstrap_fail "Python >=3.10 unavailable"
   ```

   **置き換え後**

   `"$REPO_ROOT/tools/pegasus/policy.json"` を strict JSON として読み、exact positive int の `b10_backoff_shape_walltime_s` を `B10_WALLTIME_S` に格納します。

3. [b10_backoff_shape_campaign.sh:168-171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/tools/pegasus/b10_backoff_shape_campaign.sh:168)

   **現行 anchor**

   ```python
   if request != {"project": "SFC", "queue": "gen_S", "nodes": 1,
                  "elapstim_req_s": 43200}:
   ```

   **置き換え後**

   `B10_WALLTIME_S` を embedded Python の引数に追加し、`"elapstim_req_s": int(walltime_s)` と比較します。

4. [b10_backoff_shape_campaign.sh:261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/tools/pegasus/b10_backoff_shape_campaign.sh:261)

   **現行 anchor**

   ```bash
   [[ "$SCHEDULER_ELAPSE_LIMIT_S" -eq 43200 ]]
   ```

   **置き換え後**

   ```bash
   [[ "$SCHEDULER_ELAPSE_LIMIT_S" -eq "$B10_WALLTIME_S" ]]
   ```

5. [submit_b10_backoff_shape.sh:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/tools/pegasus/submit_b10_backoff_shape.sh:85) の後で同じ JSON field を読みます。

   [同:180-200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/tools/pegasus/submit_b10_backoff_shape.sh:180) の embedded Python には `B10_WALLTIME_S` を引数で渡します。

   **現行 anchor**

   ```python
   "request": {"project": "SFC", "queue": "gen_S", "nodes": 1,
               "elapstim_req_s": 43200},
   ```

   **置き換え後**

   ```python
   "request": {"project": "SFC", "queue": "gen_S", "nodes": 1,
               "elapstim_req_s": int(walltime_s)},
   ```

6. [b10_backoff_shape_sweep.py:491-493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:491)

   **現行 anchor**

   ```python
   if request != {
       "project": "SFC", "queue": "gen_S", "nodes": 1, "elapstim_req_s": 43200,
   }:
   ```

   **置き換え後**

   `_b10_walltime_s(root)` で同じ JSON field を strict に読み、期待 request を構築します。

7. [test_b10_backoff_shape_sweep.py:1885-1901](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/tests/test_b10_backoff_shape_sweep.py:1885)

   **現行 anchor**

   ```python
   assert job_text.count("43200") == 2
   assert submit_text.count("43200") == 1
   assert driver_text.count("43200") == 1
   ```

   **置き換え後**

   文字列個数の meta-test を廃止し、次を意味検査します。

   - JSON 値が `12 * 60 * 60`
   - PBS 指示行がちょうど 1 行で、その時分秒を秒換算すると JSON 値と等しい
   - submit dry-run receipt の `elapstim_req_s` が JSON 値と等しい
   - job の receipt validator と scheduler validator が `B10_WALLTIME_S` を参照する
   - driver の receipt validator が `_b10_walltime_s()` を参照する
   - 3 実装ファイルに生の `43200` が残らない

これで 5 箇所は「JSON の 1 定数から派生する 4 consumer + scheduler literal と JSON の意味等価検査」になります。値は変えません。

## (3) ビルドキャッシュをジョブごとに分ける

[b10_backoff_shape_sweep.py:2880](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:2880) を変更します。

**現行 anchor**

```python
cache_root = os.fspath(ccbench_base / "build-variants")
```

**置き換え後**

```python
cache_root = os.fspath(
    ccbench_base / "build-variants" / "b10-jobs" / submission.nonce
)
```

submission nonce は [同:474-476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:474) で 32 桁 hex と検証済みです。1 qsub ごとに異なり、path component として安全です。

**cache_root と同一性 key**

`cache_root` は build cache identity に入りません。

- [buildcache.py:1314-1335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/buildcache.py:1314) の `_v2_identity` preimage に `cache_root` はない
- [同:2527-2548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/buildcache.py:2527) で identity を確定した後、[同:2549-2554](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/buildcache.py:2549) で初めて `root` を物理配置へ使う

一方、source root は外れていません。

- [source_digest.py:114-175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/source_digest.py:114) の `SourceEvidence` と receipt が絶対 `source_root` を保持
- [build_admission.py:662-675](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/build_admission.py:662) がその source receipt を admission に格納
- [buildcache.py:1324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/buildcache.py:1324) が admission 全体を preimage に格納
- [同:654-656](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/buildcache.py:654) も request の source root と evidence の exact 一致を要求

したがって、置き場の分離は D1220 が禁じる source root の除去ではありません。

**実行ファイル bytes への path 混入**

既存コードは既知の経路を次のように正規化しています。

- source `__FILE__`: [buildcache.py:1902-1905](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/buildcache.py:1902) の `-fmacro-prefix-map`
- build/debug path: [同:1906-1915](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/buildcache.py:1906) の staging root 全体への `-fdebug-prefix-map`
- RUNPATH/RPATH: [同:1916-1919](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/buildcache.py:1916) の `-DCMAKE_SKIP_RPATH=ON`
- 実際の fresh build は [同:2661-2667](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/buildcache.py:2661) で exact staging root を渡す

ただし、既存テスト [test_buildcache_v2.py:2488-2542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/tests/test_buildcache_v2.py:2488) が証明するのは異なる source root の `__FILE__` 正規化です。異なる `cache_root` / staging root で生成した実 CCBench executable の full SHA 一致は検査していません。

したがって、現時点では「cache_root の絶対 path が最終 bytes に絶対入らない」とまでは断言できません。上記 split は、次の実バイナリテストが通ることを先行条件にします。

```text
orchestrator/tests/test_buildcache_v2.py::
test_b10_real_binary_sha_is_identical_across_distinct_cache_roots
```

同じ applied source、genome、trace=false、toolchain、admission で `cache-a` と `cache-b` に fresh build し、次を要求します。

- full `bin_sha256` が一致
- 両 cache root と staging root の raw bytes が executable にない
- `readelf -d` に RPATH / RUNPATH がない
- correctness 側 SHA と performance 側 SHA が一致

この nodeid が赤、または実行不能なら cache split は採用しません。`buildcache.py` 本体の変更は不要です。

## (4) 集約入口を job から分離する

同じ driver に `report` phase を追加する案を支持します。ただし `campaign_lock.py` closure を理由にはできません。

**phase surface**

1. [b10_backoff_shape_sweep.py:105-106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:105)

   **現行 anchor**

   ```python
   RUN_PHASES = ("build", "verify", "perf", "probe")
   FORMAL_PHASES = (*RUN_PHASES, "verify-perf")
   ```

   **置き換え後**

   ```python
   RUN_PHASES = ("build", "verify", "perf", "probe")
   FORMAL_PHASES = (*RUN_PHASES, "verify-perf", "report")
   ```

2. [b10_backoff_shape_campaign.sh:24-30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/tools/pegasus/b10_backoff_shape_campaign.sh:24)

   **現行 anchor**

   ```bash
   [[ "${IZANAGI_B10_PHASE:-}" =~ ^(build|verify|perf|probe|verify-perf)$ ]]
   if [[ "$IZANAGI_B10_PHASE" == build || "$IZANAGI_B10_PHASE" == probe ]]; then
   ```

   **置き換え後**

   phase 正規表現へ `report` を加え、`build|probe|report` は workload 無しとします。

3. [b10_backoff_shape_campaign.sh:285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/tools/pegasus/b10_backoff_shape_campaign.sh:285)

   **現行 anchor**

   ```bash
   if [[ "$IZANAGI_B10_PHASE" != probe ]]; then
   ```

   **置き換え後**

   `probe` と `report` の双方で gflags/glog dependency build を省きます。report は集約だけで executable を link しません。

4. [submit_b10_backoff_shape.sh:9-10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/tools/pegasus/submit_b10_backoff_shape.sh:9)、[同:61-70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/tools/pegasus/submit_b10_backoff_shape.sh:61)

   usage、phase 正規表現、workload 規則へ `report` を加えます。`report` は workload を拒否します。

5. submit receipt schema は `pegasus-b10-submit-receipt/v2` のままです。

   [submit_b10_backoff_shape.sh:277-289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/tools/pegasus/submit_b10_backoff_shape.sh:277) は phase を文字列として複製するだけです。[job script:146-170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/tools/pegasus/b10_backoff_shape_campaign.sh:146) と [driver:453-484](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:453) も exact key set と CLI/env との等値を検査し、receipt 自体には phase enum がありません。したがって key shape の版上げは不要です。

**job 側 report 削除**

[b10_backoff_shape_sweep.py:3044-3072](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:3044) の現行 anchor 全体を削除します。

```python
all_records: list[dict[str, object]] = []
for other_workload in prereg.spec.workload_map:
    ...
json_path, markdown_path = _write_reports(...)
```

perf / verify-perf job の置き換え後は、自 workload の block root を再読し、45 セルの `execution_complete` だけを計算して次を返します。

```python
return None, None, execution_complete
```

`_write_reports` を呼べるのは `phase == "report"` の分岐だけにします。

**report phase**

同じ driver 内へ `_collect_report_inputs(...)` を追加します。

- workload 3 件を固定順に処理
- 各 workload の campaign ID、binding SHA、WAL path、block root を記録
- block record を既存 hash envelope 経由で読む
- report output は trial ごとでなく、binding group 下の固定 `reports/final` とする
- [b10_backoff_shape_sweep.py:2641](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:2641) の `mkdir(..., exist_ok=False)` により、同じ report の二重発行は 1 本だけ成功する

`report` の投入を 3 workload job の終端後に行うのは運用前提です。コード側は次の 135-cell exact gate で、早過ぎる集約を拒否します。

**135 セル exact gate**

期待 key は campaign ID ではなく次です。

```python
{
    (workload, block_id, point)
    for workload in prereg.spec.workload_map
    for block_id in prereg.spec.block_ids
    for point, _genome in named_genomes()
}
```

期待数は `3 * 3 * 15 == 135`。observed key の集合と件数の両方を比較します。

- block record 自体が欠ける、余分、重複、格子外: `_write_reports` 前に `PreflightError("report-completeness", ...)` で拒否し、report directory を作らない
- 135 record は揃っているが row の `missing=True`、uncertified、unstable、underexposed: report は生成し、既存 `judge()` により該当 family を indeterminate として開示

設計文書の「135 セルちょうど」を守るため、構造的な欠落を indeterminate report に薄める案には反対します。

**closure の実体**

[campaign_lock.py:49-74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/campaign_lock.py:49) の exact 24 path に `b10_backoff_shape_sweep.py` は含まれていません。したがって「別 module だけが closure 外になる」は誤りです。

ただし別 module へ切り出すと、[b10_backoff_shape_sweep.py:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:90) と [同:1377-1385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:1377) の単一-file analysis hash にも入らなくなります。結論として同 driver に残すべきですが、根拠は campaign closure ではなく、この analysis-code binding です。

## (4-b) 270 verify 枠の実装

block record は 1 performance cell の要約で、6 verify 反復を持ちません。分母 270 は WAL の `verify_done` から数えます。

根拠は次です。

- `verify_done` の producer: [pipeline.py:1485-1502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/pipeline.py:1485)
- payload は `workload: {"tag": tag}` を持つが repetition field はない
- repetition loop: [pipeline.py:1521-1529](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/pipeline.py:1521)。`_repetition` は payload へ書かれていない
- tag の正本: [pipeline.py:148-155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/pipeline.py:148)
- strict WAL reader: [wal.py:1394-1411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/wal.py:1394)

`_verification_completeness(...)` を `_write_reports` の前に追加し、次の手順にします。

1. 選択した workload campaign ごとに `wal.read_records_checked(layout)` を使う。truncated tail は拒否する。
2. `verify_done` の `variant` を、登録された 15 point の `variant_id` へ exact に対応付ける。
3. `payload.workload.tag` は `legacy` / `performance` だけを受理する。
4. 同じ `(workload, variant, build_attempt_id, tag)` 内の WAL 出現順を 1 始まりの repetition 番号とする。
5. attempt ID を投影から外し、論理 key を `(workload, point, tag, repetition)` とする。
6. campaign ID は key と分母に入れず、record source の内訳にだけ残す。
7. 期待集合は legacy 1 枠、performance 5 枠を各 workload / point に展開した 270 key とする。

report JSON には 135 と 270 を別 object で書きます。

```json
"performance_cell_completeness": {
  "expected_cells": 135,
  "observed_cells": 135,
  "logical_key": ["workload", "block_id", "point"],
  "campaigns": []
},
"verification_slot_completeness": {
  "expected_slots": 270,
  "completed_logical_slots": 270,
  "incomplete_slots": 0,
  "logical_key": ["workload", "point", "verify_tag", "repetition"],
  "observed_verify_done_records_by_campaign": [],
  "missing_slots": []
}
```

`observed_verify_done_records_by_campaign` には full campaign ID、workload、raw `verify_done` 件数、tag 内訳を必ず記します。過去の参考値を書く場合も `e3de15eb=90 + balanced=85 + read-heavy=22` のように campaign を名指しします。

[b10_backoff_shape_sweep.py:2591](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:2591) の provenance schema は、新しい完全性 object を追加するため `b10-backoff-shape-provenance/v2` へ上げます。既存 v1 report は書き換えません。

Markdown は [同:2647-2658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:2647) の cell 表より前に、別々の節として 135 と 270 を出します。

**出現順の既知限界**

出現順以外に repetition 番号を得る field はありません。壊れる入力例は次です。

- 同一 attempt の performance #1 frame が重複し、5 frame あると出現順だけでは #1〜#5 が完了したように見える
- retry attempt が performance 3 回で停止し、次 attempt も 3 回で停止すると、attempt を無視した単純出現順では 5 枠完了と誤認する
- WAL frame の並べ替えで repetition の順序が変わる

このため attempt ごとに ordinal をリセットしてから論理 key へ射影します。それでも「重複した frame」と「別 repetition」を完全には区別できません。明示 repetition field を producer に足す変更は `pipeline.py` と正しさ WAL 契約へ及ぶため、本 wave には入れません。この occurrence-order 規則を採るかは親裁定へ返します。

## (5) 実行ノード名

block schema は v3 に上げず、既存 v2 の additive field とします。

[b10_backoff_shape_sweep.py:3001-3004](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:3001) の anchor は次です。

```python
row = {
    "schema_version": "b10-backoff-shape-block/v2",
    "official_certification": False,
    "workload": workload,
```

置き換え後は同じ v2 のまま、次を加えます。

```python
"execution_host": reservation.read_binding(os.environ).host,
```

取得元は既存のものだけです。

- job export: [b10_backoff_shape_campaign.sh:269-276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/tools/pegasus/b10_backoff_shape_campaign.sh:269)
- env mapping: [reservation.py:120-129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/reservation.py:120)
- binding 構築と host field: [reservation.py:159-175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/reservation.py:159)

新しい環境変数は作りません。

[b10_backoff_shape_sweep.py:2360-2398](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:2360) では、`execution_host` が存在する場合だけ non-empty exact str を要求します。既存 v2 は field 無しで受理し、report では `not-recorded-legacy-v2` と表示します。

envelope は変更不要です。[同:2287-2294](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:2287) が record 全体を hash し、[同:2316-2325](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py:2316) が envelope/hash を検証するため、追加 field も既に hash 対象です。

**v3 案の評価**

`_validate_prior_block_records` の version 条件を `{v2, v3}` に変えると、旧実装で version mismatch により拒否されていた v3 document が新たに通ります。従って、形式的には明らかな受理集合の拡大です。v3 に host を必須化しても「より強い形の新しい document」を追加受理する事実は変わりません。しかも block record は `correctness_certified` を通じて `judge()` に入るため、規律 2 と無関係とは扱えません。

v2 のままなら、現 validator は既に unknown additive field を拒否していません。optional host の型検査を追加する変更は受理集合を広げず、むしろ malformed な present-host record を狭めます。このため v2 継続を推奨します。

ただし、旧 write-heavy が現在拒否される主因は v2 ではなく、前述の歴史 binding と現行 binding の不一致です。schema を v2/v3 union にしても解決しません。

## 旧 write-heavy 45 セルの限定受理

通常の `_validate_prior_block_records` を広く緩めず、report phase だけに D1509 専用 adapter を置きます。

対象は full campaign ID `b10-backoff-shape-silo-write-heavy-formal-e3de15eb` に固定します。根拠は [missing-iterations-scope:68,82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/output/insights/2026-09-02_b10-missing-iterations-scope/README.md:68) です。

adapter は次を要求します。

- campaign ID、workload、45 個の `(block_id, point)` が exact
- envelope hash、submission receipt hash、point metadata は現 validator と同じ
- 歴史 `preregistration_binding` が campaign.lock の binding と exact 一致
- prereg commit/blob、spec、patch、formula は現 prereg と一致
- 歴史 analysis commit/code SHA は記録として保持し、現行値へ書き換えない
- `official_certification` は引き続き false
- host 無しは `not-recorded-legacy-v2`

これは arbitrary な旧 record を受理する一般互換層ではありません。それでも既存 consumer より受理範囲が増えるため、前提衝突の親裁定後にだけ実装します。

## 新規テスト nodeid 候補

すべて未実走です。

| nodeid 候補 | 赤になる条件 |
|---|---|
| `test_b10_walltime_contract_semantically_drives_all_five_sites` | JSON、PBS、job receipt、qstat、submit receipt、driver receipt のいずれかが不一致 |
| `test_sanctioned_dry_run_report_phase_has_no_workload_and_uses_contract_walltime` | report が拒否される、workload を受理する、receipt walltime が JSON と違う |
| `test_b10_real_binary_sha_is_identical_across_distinct_cache_roots` | cache/staging path が bytes に入る、SHA が不一致、RPATH/RUNPATH が残る |
| `test_b10_cache_root_is_submission_nonce_scoped_but_source_identity_is_unchanged` | job 間で cache root が共有される、または source root/admission identity が落ちる |
| `test_report_phase_is_the_only_caller_of_write_reports` | perf/verify-perf job が `_write_reports` を呼ぶ、report phase が呼ばない |
| `test_report_input_requires_exact_135_registered_cells` | 134、136、重複、格子外の入力を report が受理する |
| `test_present_missing_cell_is_reported_indeterminate_not_structurally_absent` | 135 row 中の `missing=True` を構造欠落扱いする、または成功扱いする |
| `test_report_publish_is_create_only_for_one_binding_group` | 二度目の report が上書きまたは別 trial directory へ発行できる |
| `test_verification_completeness_uses_270_registered_logical_slots` | 分母が started attempts や campaign 数から派生する |
| `test_verification_completeness_names_each_source_campaign_without_keying_slots_by_it` | campaign ID が論理 key に入る、または完了内訳に campaign ID がない |
| `test_verification_repetition_ordinals_reset_per_attempt` | retry の 3+3 record を単純に 5 完了へ数える |
| `test_verification_unknown_tag_or_rep_overrun_is_rejected` | legacy/performance 外、legacy 2 件、performance 6 件を受理する |
| `test_legacy_v2_block_without_execution_host_remains_reportable` | 完走済み v2 row が host 欠落だけで落ちる |
| `test_new_v2_block_records_reservation_binding_host` | 新規 row が `IZANAGI_RESERVATION_HOST` 以外を記録する、または空 host を受理する |
| `test_preserved_write_heavy_campaign_is_exactly_scoped` | `e3de15eb` 以外や異なる spec/patch/formula の歴史 binding を legacy 例外が通す |

既存の次のテストも更新対象です。

- `test_run_phase_closed_set_is_build_verify_perf_probe`
- `test_verify_perf_phase_is_additive_to_the_legacy_phase_set`
- `test_pegasus_submit_and_job_scripts_are_syntax_valid_and_use_pbs_contract`
- `test_verify_perf_launcher_contract_and_walltime_are_consistent`
- `test_formal_campaign_layout_and_writer_share_resolved_root_and_policy`
- `test_sanctioned_dry_run_stages_outside_worktree_and_preserves_clean_surface`

driver の行追加で spawn-site 行番号が動くため、[test_ccbench_spawn_sites.py:825-840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/tests/test_ccbench_spawn_sites.py:825) と [同:2589-2604](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/tests/test_ccbench_spawn_sites.py:2589) の `2515` / `2911` は、最終 AST 上の実行位置へ更新します。

## 変更順と依存関係

1. 親裁定で analysis binding / campaign identity の衝突と、歴史 `e3de15eb` 限定受理を確定する。
2. `policy.json` に壁時計の単一契約を置き、submit/job/driver をそこへ接続する。
3. 異なる cache root で実 executable の SHA 一致テストを追加して実走する。
4. 3 が通った場合だけ `cache_root` を submission nonce ごとに分ける。
5. `execution_host` を v2 additive field として writer と report 表示へ追加する。
6. `report` phase を driver、job script、submitter へ通す。receipt schema は維持する。
7. perf job から集約を除去し、自 workload 45 セルの completion 判定だけ残す。
8. report phase に exact 135-cell collector と create-only final report を追加する。
9. WAL から 270 verify 枠を数える helper と、135/270 を分けた provenance v2 / Markdown を追加する。
10. D1509 の歴史 write-heavy adapter を report phase だけへ接続する。
11. B10 テスト、buildcache 実バイナリテスト、spawn-site 行番号台帳を更新する。
12. 親が指定の test runner で実走する。今回の段では緑とは報告しない。

依存関係は `binding 裁定 → report collector`、`cross-root SHA 証明 → cache split`、`report phase 配線 → job 側集約削除`、`135 collector → _write_reports`、`WAL collector → 270 report field` です。

## 触る file

- [tools/pegasus/policy.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/tools/pegasus/policy.json)
- [tools/pegasus/b10_backoff_shape_campaign.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/tools/pegasus/b10_backoff_shape_campaign.sh)
- [tools/pegasus/submit_b10_backoff_shape.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/tools/pegasus/submit_b10_backoff_shape.sh)
- [orchestrator/campaign/b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/campaign/b10_backoff_shape_sweep.py)
- [orchestrator/tests/test_b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/tests/test_b10_backoff_shape_sweep.py)
- [orchestrator/tests/test_buildcache_v2.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/tests/test_buildcache_v2.py)
- [orchestrator/tests/test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-preflight-fixes/orchestrator/tests/test_ccbench_spawn_sites.py)

## 触らない file

- `orchestrator/campaign/buildcache.py`。既存 prefix-map / no-RPATH を利用し、今回は本体を変えない
- `orchestrator/campaign/campaign_lock.py` と exact 24-path closure
- `orchestrator/campaign/reservation.py`
- `orchestrator/campaign/pipeline.py`、`wal.py`、`model.py`
- verifier、correctness receipt、commit receipt の発行・消費経路
- `docs/b10-backoff-shape-preregistration.md`
- `patches/silo-backoff-fixed.patch`
- prereg spec、binding field 定義、正しさ反復数、規模、厳しさ
- `docs/b10-multinode-formal-run-design.md`。本依頼は実装プランであり、signal の現状確認だけ行う
- 既存の write-heavy 45-cell record、既存 provenance v1、過去の測定値
- §8 の検査多重化に関わる file

## 総括

実装順の file:line は次です。

1. `tools/pegasus/policy.json:11` — 壁時計の単一定数
2. `b10_backoff_shape_campaign.sh:60,127-170,261` — 契約読込と 2 consumer
3. `submit_b10_backoff_shape.sh:85,180-200` — submit receipt
4. `b10_backoff_shape_sweep.py:491-493` — driver receipt
5. `test_buildcache_v2.py:2488` 付近 — cross-cache-root executable SHA 証明
6. `b10_backoff_shape_sweep.py:2880` — nonce ごとの cache root
7. `b10_backoff_shape_sweep.py:3001-3030` — v2 additive execution host
8. `b10_backoff_shape_sweep.py:105-106,2822-2848` — report phase
9. `b10_backoff_shape_sweep.py:3044-3072` — job 側集約削除
10. `b10_backoff_shape_sweep.py:2580-2719` — exact 135、WAL 270、provenance v2
11. `test_b10_backoff_shape_sweep.py:1066-1072,1784-1960` — phase、report、壁時計、host、完全性
12. `test_ccbench_spawn_sites.py:825-840,2589-2604` — shifted sink 行番号

親 provisional への評価は次です。

- P1: 支持。JSON の単一定数と scheduler literal の意味等価テストが最小の実現形。
- P2: 結論は支持、理由は一部反対。driver は closure 外だが、別 module は単一-file analysis hash からも外れるため同 driver に残す。
- P3: 反対。v2/v3 union は受理集合拡大なので、v2 additive optional host で既存 45 セルを維持する。
- P4: 支持。135 performance cell と 270 verify slot は別 object、別 key、別分母で出す。
- P5: 支持。`reservation.read_binding(os.environ).host` を使い、新しい環境変数は作らない。

親裁定へ返す未決択一は 3 件です。

- driver bytes を変えることで新しい binding / campaign ID が生じることを承認し、旧 `e3de15eb` だけを歴史 binding 付きで限定集約するか。
- repetition field がないため、attempt 内 WAL 出現順を repetition 番号とする規則と、その既知限界を受け入れるか。
- 135 record の構造欠落は report 拒否、row は存在するが測定不能なら indeterminate 開示、という区別を確定するか。