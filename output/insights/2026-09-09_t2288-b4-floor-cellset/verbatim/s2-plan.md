## 択一の判定

採るのは **(γ): calibration と cell の workload 一致要求だけを外す**案である。ただし受理意味が変わるため、wire 形が同じでも `SPEC_SCHEMA` は `floor-pair-spec/v4` へ上げる。

根拠は次のとおり。

- B10 formal report は一つの top-level calibration を持ち、その束縛 field は `path`、`sha256`、`records`、`threads`、`env_tag`、`clocks_per_us` 等で、`workload` を含まない。[b10 provenance:453](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json:453)
- 同じ report は write-heavy、balanced、read-heavy の各 45 cell を一つの `performance_cell_completeness` にまとめている。[b10 provenance:562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json:562)
- §5 の calibrated `PerfConfig` 欄は単数である。[preregistration:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/phase3-b4-reflux-ablation-preregistration.md:163)
- D1641 はセル集合を 3 workload × contention cell、最終最大をその集合 × 2 window 全部と凍結している。[decisions.md:50331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/decisions.md:50331)
- calibration が採用した `records=1,000,000` は実飽和点ではない。`saturated=false`、`lower_bound_selected=true` であり、選択根拠は maxrss が L3 の 4.9 倍以上になる最小 N である。[calibration artifact:1603](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1603) [同:1634](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1634)
- したがって driver が実際に消費する保証は「この環境・threads で working set/L3 下限を満たす record 数」であり、read/write 混合の同一性ではない。取得時 workload 自体は balanced と記録されているため、他 workload の miss-rate 系列まで実測済みとは主張しない。[calibration artifact:1685](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1685)

却下案:

- **(α) を却下。** 3 spec/3成果物では、単数の floor pin と `artifact_path=...; sha256=...` 一件だけを受ける resolver に渡せない。[preregistration:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/phase3-b4-reflux-ablation-preregistration.md:162) [issuer:1202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:1202) 集約規則の新設は scope 外である。
- **(β) を却下。** `provenance.calibration` と cell の wire 形を拡張し、workload ごとの accepted calibration を必要とする。§5 の calibration 欄が単数であることに反し、D1696 が却下した spec validator の一般拡張にも当たる。[floor_pair_driver.py:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:660) [同:798](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:798) [decisions.md:51700](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/decisions.md:51700)

受理集合の厳密な拡張は、schema v3 から v4 への機械的な版置換を `τ` とすると、

```text
{ τ(s) |
  s は現行の全構文・参照・checkout・binary・calibration 条件を満たし、
  workload 一致条件だけを除けば受理可能であり、
  少なくとも一つの cell c について
  calibration.workload != dict(c.perf_config.workload)
}
```

である。これは複数 workload の spec だけでなく、単一 cell の workload が calibration 取得時 workload と異なる spec、全 cell が異なる spec も含む。workload object の値域は現行 `_parse_perf` が受理する exact 3 key・非空 string の範囲である。文字どおりの JSON bytes では v3 は引き続き拒否されるので、「以前の v3 bytes がそのまま受理される」という意味ではない。

## 前提の独立検証

親の主張は大筋で正しいが、アンカーには次の修正が要る。

- `SPEC_SCHEMA` は確かに line 56。
- `_parse_calibration_reference` は 647-657、`_parse_provenance` は 660-672、`_parse_cells` は 798-816で正しい。
- `_bind_checkout_inputs` の実コードは 1122-1194。1195-1196 は空行である。
- cell loop は 1181 から始まる。1184 は loop 内コメントであり、親の「1184-1196 が loop」は不正確。
- `_derive_identity` は 737-814。親の 737-812 は return まで含まない。
- schema pin test は実質 629-633。628 は空行。
- v2 拒否 test の 636-651 は正しい。
- issuer docstring の `floor_pair_driver.py:759-776, 1136-1147` は既に誤っている。前者は artifact parser と `_parse_perf` 冒頭、後者は binary/build receipt 読取りであり、「nonempty cells with calibration-consistent threads/workloads」の根拠ではない。[issuer:746](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:746)

`load_verified_calibration` が検査するもの:

- repo root、repository-relative path、root 内への解決、artifact bytes、SHA-256。[calibration_verify.py:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/calibration_verify.py:91)
- required mode では calibration/v2 strict parse、`env_tag`、`clocks_per_us`、effective-clock tolerance。[同:116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/calibration_verify.py:116)
- none mode では特定の grandfathered v1 bytes だけを受理し、`calibration=None` を返す。[同:144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/calibration_verify.py:144)

直接は検査しないもの:

- `quality.status == "accepted"`。
- workload と cell workload の対応。
- calibration threads と cell threads の対応。
- `saturation.records` と cell records の対応。

これらは driver の 1170-1194 が追加検査している。

なお、親の「既存 209 node」は陳腐化している。静的に pytest mark を展開すると現 test file は **210 node** で、duration ledger にも同 prefix が210件ある。pytest は実走していない。

## 変更プラン (file:line)

変更対象は次のとおり。

| file:line | 変更 |
|---|---|
| `floor_pair_driver.py:56` | `SPEC_SCHEMA = "floor-pair-spec/v4"` |
| `floor_pair_driver.py:647-672` | wire 形を変えないため完全に据え置く |
| `floor_pair_driver.py:798-816` | cell wire 形を変えないため完全に据え置く |
| `floor_pair_driver.py:1122-1194` | workload 比較2行だけを説明コメントへ置換。他の拒否は維持 |
| `p3_b4_floor_artifact_issuer.py:746-753` | 誤った行番号 pin と workload 保証の説明だけを訂正 |
| `test_floor_pair_driver.py:629-651, 1069-1173` 周辺 | v4 pin、直前版 v3 拒否、混合 workload 正例、各負例 |
| `acceptance_duration_ledger.json:547` 以降 | 廃止・改名・新設 nodeid と実測 duration を更新 |
| `docs/decisions.md:56191` 現 EOF+1 | workload 一致だけを外した受理集合と v4 bump を次の D として記録 |

変更後の parser は以下の完全な形で、現行から変えない。

```python
def _parse_calibration_reference(value: object) -> CalibrationReference:
    label = "provenance.calibration"
    obj = _exact_object(value, {"path", "sha256", "attestation_mode"}, label=label)
    mode = _exact_text(obj["attestation_mode"], label=f"{label}.attestation_mode")
    if mode not in {"required", "none"}:
        raise FloorPairSpecError(f"{label}.attestation_mode が未対応: {mode!r}")
    return CalibrationReference(
        path=_relative_path(obj["path"], label=f"{label}.path"),
        sha256=_sha256_text(obj["sha256"], label=f"{label}.sha256"),
        attestation_mode=mode,
    )


def _parse_provenance(value: object) -> ProvenanceConfig:
    obj = _exact_object(
        value,
        {"calibration", "source_commit"},
        label="provenance",
    )
    source_commit = _exact_text(obj["source_commit"], label="provenance.source_commit")
    if _HEX40_RE.fullmatch(source_commit) is None:
        raise FloorPairSpecError("provenance.source_commit は 40 桁 lowercase hex でなければならない")
    return ProvenanceConfig(
        calibration=_parse_calibration_reference(obj["calibration"]),
        source_commit=source_commit,
    )
```

```python
def _parse_cells(value: object) -> tuple[CellConfig, ...]:
    values = _exact_list(value, label="cells", allow_empty=False)
    result: list[CellConfig] = []
    seen: set[str] = set()
    for index, item in enumerate(values):
        label = f"cells[{index}]"
        obj = _exact_object(item, {"cell_id", "perf_config"}, label=label)
        cell_id = _identifier(obj["cell_id"], label=f"{label}.cell_id")
        if cell_id in seen:
            raise FloorPairSpecError(f"duplicate cell_id: {cell_id}")
        seen.add(cell_id)
        result.append(
            CellConfig(
                cell_id=cell_id,
                perf_config=_parse_perf(obj["perf_config"], label=f"{label}.perf_config"),
            )
        )
    return tuple(result)
```

変更後の binder の完全な形は次のとおり。行数を動かさないよう、削除する workload 拒否2行を2行の説明へ置換する。

```python
def _bind_checkout_inputs(
    *,
    root: Path,
    loaded_head: str,
    provenance: ProvenanceConfig,
    environment: EnvironmentConfig,
    artifacts: tuple[ArtifactConfig, ...],
    cells: tuple[CellConfig, ...],
) -> None:
    _read_tracked_bound(
        root, loaded_head, provenance.calibration, label="calibration artifact"
    )
    receipt_raw_by_reference: dict[BoundReference, bytes] = {}
    for artifact in artifacts:
        binary = _resolve_regular(root, artifact.binary_relpath, label=f"binary {artifact.artifact_id}")
        try:
            buildcache.assert_binary_sha256(str(binary), artifact.binary_sha256)
        except Exception as exc:
            raise FloorPairBindingError(
                f"binary {artifact.artifact_id} sha256 を検証できない: {exc}"
            ) from exc
        if artifact.build_receipt not in receipt_raw_by_reference:
            receipt_raw_by_reference[artifact.build_receipt] = _read_tracked_bound(
                root,
                loaded_head,
                artifact.build_receipt,
                label=f"build receipt {artifact.artifact_id}",
            )
        _validate_build_receipt(
            receipt_raw_by_reference[artifact.build_receipt], artifact
        )
    try:
        verified = calibration_verify.load_verified_calibration(
            env_tag=environment.env_tag,
            clocks_per_us=environment.clocks_per_us,
            attestation_mode=provenance.calibration.attestation_mode,
            calibration_path=provenance.calibration.path,
            calibration_sha256=provenance.calibration.sha256,
            repo_root=root,
        )
    except Exception as exc:
        raise FloorPairBindingError(f"calibration admission に失敗: {exc}") from exc
    calibration = verified.calibration
    if calibration is None:
        raise FloorPairBindingError(
            "この driver は校正済み動作点だけを測るため、"
            "calibration=None の attestation mode は意図的に受理しない"
        )
    quality = getattr(calibration, "quality", None)
    if getattr(quality, "status", None) != "accepted":
        raise FloorPairBindingError("calibration quality.status が accepted でない")
    saturation = getattr(calibration, "saturation", None)
    if type(saturation) is not dict:
        raise FloorPairBindingError("accepted calibration の saturation が非 null object でない")
    if "records" not in saturation:
        raise FloorPairBindingError("calibration saturation.records が欠落")
    saturation_records = saturation["records"]
    if type(saturation_records) is not int or saturation_records < 1:
        raise FloorPairBindingError("calibration saturation.records が exact 正 int でない")
    for cell in cells:
        perf = cell.perf_config
        # verifier が production 入力で同値を既に要求するため env/clocks は冗長 gate。
        # 防御的な再照合として残すが、単独変異の証拠には数えない。
        if calibration.env_tag != environment.env_tag:
            raise FloorPairBindingError(f"cell {cell.cell_id}: calibration env_tag 不一致")
        if calibration.threads != perf.threads:
            raise FloorPairBindingError(f"cell {cell.cell_id}: calibration threads 不一致")
        if calibration.clocks_per_us != environment.clocks_per_us:
            raise FloorPairBindingError(f"cell {cell.cell_id}: calibration clocks_per_us 不一致")
        # workload は cell 側の凍結値を用いる。calibration の取得時 workload ではなく
        # saturation.records の working-set/L3 下限を各 cell へ束縛する。
        if perf.records != saturation_records:
            raise FloorPairBindingError(f"cell {cell.cell_id}: calibration records 不一致")
```

calibration artifact は一 spec load につき:

1. `_read_tracked_bound` が working-tree bytes を1回読み、別に loaded HEAD blob を `git show` で1回読む。
2. `load_verified_calibration` が strict parse 用に working-tree bytes をもう1回読む。
3. verifier 呼出しは cell loop 外なので、cell 数にかかわらず1回だけ。

したがって filesystem 上は2読、git blob は1読である。build receipt のような複数参照は存在せず、verifier API も raw bytes を受け取らないため、`receipt_raw_by_reference` 型の新しい cache は足さない。これを畳むには `calibration_verify.py` のAPI変更が必要になり、本件の最小差分を越える。

## (P1) 判定

| P1 | 判定 | 根拠 |
|---|---|---|
| P1-a | **real、(γ) を採用** | B10 の単一 calibration と3 workload、§5の単数欄、working-set/L3 による records 選択が整合する |
| P1-b | **記述どおりなら refuted** | issuer の実行ロジックは無変更で足りるが、docstring の「calibration-consistent workloads」は (γ) 後に偽になるため文言変更が必要 |
| P1-c | **real。ただし bump 不要説は refuted** | wire 形は同じでも受理集合が変わるので SPEC v4。PLAN v2、WINDOW v3、SUMMARY v3は据え置く |
| P1-d | **real、ただし test fixture として** | 同じ accepted calibration を rr50 cell と rr95 cell が共有する spec が最小 witness。現 repo の実 artifactだけでは end-to-end spec を構成できない |
| P1-e | **real** | 発行、§5記入、preregistration改訂、測定投入はいずれも scope 外 |

## 受理集合の不変性

(γ) 後も以下の経路は閉じたままである。

- `quality.status != "accepted"`: `floor_pair_driver.py:1170-1172` が拒否。
- `saturation.records` の欠落・型違反: `:1173-1180` が拒否。
- cell records 不一致: `:1193-1194` が cell ごとに拒否。
- `env_tag` 不一致: production verifier の `calibration_verify.py:121-124` が先に拒否し、driver `:1185-1186` も冗長に拒否。
- `clocks_per_us` 不一致: verifier `:125-129`、driver `:1189-1190` の両方が拒否。
- `calibration=None`: driver `:1165-1169` が意図的に拒否。
- cell 間 threads 不一致: 全 cell が一つの `calibration.threads` と `:1187-1188` で比較されるため、全 cell の threads は同一値になる。issuer の `next(iter(threads_values))` は引き続き安全。
- path、SHA、loaded HEAD blob の不一致: `_read_tracked_bound` の `:621-635` が維持される。
- (β) は採らないため、cell calibration ref の欠落・空・重複という新しい wire 状態自体が存在しない。

外すのは `:1191-1192` の workload 比較だけである。

## schema bump の閉包

`SPEC_SCHEMA` は v4へ上げる。理由は wire field の追加ではなく、同じ field に対する受理意味の変更である。

他の schema は据え置く。

- `PLAN_SCHEMA`: plan の形と HMAC algorithm は不変。plan は `spec.schema` と `spec_sha256` を入力に含むため新 spec では自然に別 plan hashになるが、plan algorithm の意味は変わらない。[floor_pair_driver.py:1338](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:1338)
- `WINDOW_SCHEMA`: header は `spec_relpath`、`spec_sha256`、`plan_sha256` と planned sessions を既に記録する。workload/calibration field の追加はない。[同:2241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:2241)
- `SUMMARY_SCHEMA`: summary 生成側は spec の path/hash、plan hash、window/campaign、導出値を記録し、spec schema や calibration/workload を複製しない。[同:3055](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:3055)
- issuer `_validate_summary_document` も同じ exact top-level 形と、再導出した `upper/candidate_floor` の一致を検査するだけである。[issuer:666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:666)
- その後 `load_floor_pair_summary` が summary-bound spec を現在の `load_frozen_spec` へ通すので、v3 spec を参照する旧 summary は fail-closed になる。[issuer:848](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:848)

candidate floor の計算、field、値域の意味は変わらないため、`SUMMARY_SCHEMA` と `ACCEPTED_FLOOR_PAIR_SUMMARY_SCHEMA_VERSION` はともに v3のままにする。D1759の単一値 pin に変更はない。[decisions.md:53416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/decisions.md:53416)

test は次のように更新する。

- `test_all_four_semantic_schema_identifiers_are_bumped`: SPECだけ v4、PLAN v2、WINDOW v3、SUMMARY v3を同時 pin。
- `test_loader_rejects_v2_schema_on_v3_shaped_spec` を `test_loader_rejects_v3_schema_on_v4_shaped_spec` へ改名し、直前版 v3 が calibration verifier 到達前に拒否されることを固定。
- `REQUIRED_FIELD_PATHS` は wire 形不変なので変更しない。

仮に SUMMARY を上げる案を採るなら、D1759により issuer の accepted constant も同じ変更単位で進める必要があるが、本件ではその条件は成立しない。

## issuer への波及

実行ロジックは変更しない。

- cells の workload は set 化され、canonical sort 後に `_aggregate_identifier("set", workload_wire)` へ入る。[issuer:758](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:758) [同:797](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:797)
- threads は `next(iter(threads_values))` だが、driver の全-cell thread 比較により set は singleton のまま。[同:807](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:807)
- summary loader は line 858 で current spec loader を呼ぶため、SPEC v4へ自動追従する。

docstring だけを次の内容へ直す。

```python
    ``floor_pair_driver.py:798-816, 1181-1194`` guarantees nonempty cells with
    calibration-consistent threads/records; cell workloads may differ and are aggregated.
    The issuer summary validator at ``p3_b4_floor_artifact_issuer.py:412-413`` guarantees nonempty campaigns.
```

これにより誤った `759-776, 1136-1147` pin と、(γ) 後に偽になる workload 一致保証を同時に除く。identity要素、命名、protocol導出、accepted summary schema constantは変えない。

## test 設計

追加・変更する node は以下。

1. `test_shared_calibration_accepts_two_cells_with_distinct_workloads_and_is_verified_once`

   `_document_only` から開始し、`cell-a` を複製して `cell-b` を作る。records、threads、extime、reps、ycsb_max_ope は同一、workload だけ rr50 と rr95 に分ける。`pair-b` を `cell-b` に結び、window `pair_ids` と `closed_strata` に追加する。mock calibration は rr50・accepted・records 1000・threads 1・env/clocks 一致とする。loader 成功、workload set が2件、verifier 呼出しが exact 1回、calibration の HEAD blob query が1回であることを確認する。

2. `test_mutation_04_calibration_projection_gates_have_single_reason_inputs`

   workload case は削除し、IDsを `env-tag`、`clocks`、`threads`、`records` の4件にする。各々ほかの field を一致させ、名指しの拒否だけが出るようにする。

3. `test_cells_with_distinct_threads_are_rejected_even_when_workloads_differ`

   上の二 workload document の `cell-b.threads` だけ2へ変え、calibration threads=1とする。`cell-a` 通過後に `cell-b` が `calibration threads 不一致` で拒否されることを固定する。

4. 既存負例を維持する。

   - quality: `test_mutation_14_rejected_calibration_is_rejected_for_quality_only`
   - records: `test_mutation_15_calibration_records_mismatch_is_rejected_for_records_only`
   - none mode: `test_calibration_none_mode_rejection_is_explicit_and_intentional`
   - env/clocks/threads/records: 更新後の mutation 04

登録済み実 calibration artifact は判断資料には使えるが、現 checkout の end-to-end loader test には直接使えない。`load_frozen_spec` は同じ repo root 内の tracked spec、binary、build receipt、calibration を全て要求する一方、handoff が示すとおり実 `floor-pair-spec/v3` instance と tracked `s8b-binary-admission/v2` receipt は0件である。artifact を tmp repo へ複製するだけでは「実 checkout の凍結 spec」を構成したことにならない。対象ループの単独検査には既存 `_verified_calibration` mock を使う。

後方互換については `_valid_document` が `F.SPEC_SCHEMA` を参照するため全既存 fixture が自動的に v4になる。`_document_only`、`_prepare_spec`、`_prepare_configured_spec`、`_multiple_pair_sample_document` の引数・返値・既存 shape は変えない。特に既存 HMAC golden を変えないため、二 workload 専用 helper は別に追加する。

現状は209でなく210 node。上の設計では mutation 04が3から4 nodeへ増え、新規2 nodeを加えるので **213 node** になる。duration ledgerでは以下を行う。

- 旧 `[workload]` nodeidを除去。
- v2拒否 nodeidをv3拒否名へ置換。
- `env-tag`、`clocks`、二つの新 nodeidを登録。
- 段6の sanctioned run で得た実 duration を記録し、`nodeid_count` を同時更新する。現 worktreeだけなら全体は22155から22158だが、並行着地があれば再生成値を採る。

これは既存台帳の通常更新であり、新しい台帳や gate の新設ではない。

## 変異点候補

登録する候補:

1. `floor_pair_driver.py:1191-1192` 相当へ workload equality を戻す変異。

   新しい二 workload 正例だけが `calibration workload 不一致` で赤になる。他の calibration 条件は一致するため帰属が一意。

2. `floor_pair_driver.py:1170-1172` の accepted quality gate を削除。

   `test_mutation_14_rejected_calibration_is_rejected_for_quality_only` が、他条件一致の rejected calibration を通して赤になる。

3. `floor_pair_driver.py:1193-1194` の records gate を削除。

   `test_mutation_15_calibration_records_mismatch_is_rejected_for_records_only` が、recordsだけ異なる入力を通して赤になる。

4. `floor_pair_driver.py:1187-1188` の threads gateを削除。

   二 cell threads 負例が loader を通して赤になる。workloadは意図的に異なるが、その比較は廃止済みなので先行拒否しない。

5. `floor_pair_driver.py:56` を v3へ戻す変異。

   4 schema pin と直前版 v3拒否 test が殺す。calibration verifier 到達前なので帰属が一意。

登録しない候補:

- driver 内の env_tag/clocks 冗長 gate `:1185-1190` の削除。production では `calibration_verify.py:121-129` が先に拒否し、mock verifierだけで殺しても production surface への帰属にならない。
- calibration artifact の workload bytes を改変する変異。SHA/HEAD blob gateが workload論点より先に拒否する。
- workload object の key欠落・未知key変異。`_parse_perf` の exact-object検査が binderより先に拒否する。
- (β) 型の空・欠落・重複 calibration reference。採らない wire 形であり、本変更の変異点ではない。

## 触らない面

- `docs/phase3-b4-reflux-ablation-preregistration.md`: §5を埋めず、本文・erratumとも変更しない。
- calibration registered artifact と B10 provenance: 一次証拠であり改変しない。
- `calibration_verify.py`: verifier APIや検査範囲を変えない。raw bytes cache対応も足さない。
- issuer の `_derive_identity`、命名、artifact schema、accepted summary schema constant: 既に集合 workload と単一threadsに対応しているため変更しない。変更はdocstringだけ。
- `PLAN_SCHEMA`、`WINDOW_SCHEMA`、`SUMMARY_SCHEMA`: 出力形・計算意味が変わらないため据え置く。
- `p3_b4_launcher.py`: 並行wave T-2316所有。
- `p3_s4_loop*`、`between_run_floor.py`、`s8b_floor_*`: 本欠陥の経路外。
- floor発行、calibrator実行、Pegasus投入、§5 pin記入: 本waveの土台変更には含めない。
- 一般化したmulti-calibration機構、新gate、新validator、新台帳: D1696と依頼のscope境界に反するため追加しない。

## 総括

実装は「workload一致2行の除去」だけでは足りない。正しい閉包は、`SPEC_SCHEMA` v4、issuer docstring訂正、境界test、既存duration ledger更新、受理集合を明記するDの同一変更単位である。runtime issuer、summary schema、事前登録、測定・発行経路は変えない。

本段ではファイル編集、pytest、commitはいずれも実施していない。上記は指定資料の静的読解に基づくプランである。