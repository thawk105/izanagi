## 実装

新設したのは次の 2 file だけです。commit / add はしていません。

- [p3_b4_floor_artifact_issuer.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-author-a/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:1)
- [test_p3_b4_floor_artifact_issuer.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-author-a/orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:1)

Public API:

- `load_floor_pair_summary(*, repo_root: Path, summary_path: Path) -> B4ValidatedFloorPairSummary`
- `issue_authoritative_floor(*, repo_root: Path, summary_path: Path) -> B4AuthoritativeFloorWrite`
  - `artifact_path: str`
  - `artifact_sha256: str`
- `load_authoritative_floor(*, repo_root: Path, artifact_path: str, expected_sha256: str | None = None) -> B4AuthoritativeFloor`
- `resolve_preregistered_authoritative_floor(*, repo_root: Path, preregistration_path: Path) -> B4AuthoritativeFloor | None`
  - 単位 B 用 resolver。present 時の `.floor` は `Fraction`、逐語 `未記入` なら `None`。
- `main(argv: Sequence[str] | None = None) -> int`

`candidate_floor` は [issuer:756](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-author-a/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:756) で `Fraction(*candidate_floor.as_integer_ratio())` にし、値を変更していません。authority は summary と同じ directory に5要素名で create-only 発行します。

## 実走した検査

- `python3 tools/check_docs.py`: rc=0、`check_docs: 違反なし`
- `python3 -m py_compile`（新設2 file）: rc=0
- `git diff --check`: rc=0
- 実 `floor_pair_driver.finalize_floor()` → `load_floor_pair_summary()` diagnostic: rc=0。`generated` summary のhash一致と、欠落が `protocol` のみであることを確認。ただし pytest node 実走ではありません。

以下は runner がテスト本体を起動する前に `qstat -Q rc=1` となり、dispatch infrastructure rc=16 で停止したため未実走です。

- `orchestrator/tests/test_p3_b4_floor_artifact_issuer.py` 全 node: 未実走、rc=16
- `test_official_perf_closure.py::test_official_perf_surface_inventory_is_exact`: 未実走、rc=16
- `test_official_perf_closure.py::test_outer_perf_file_and_added_guard_inventory_is_exact`: 未実走、rc=16
- `test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`: 未実走、rc=16
- `test_real_repo_serialization.py::test_shard_assignment_preserves_live_xdist_group_components_and_split_control`: 未実走、rc=16

したがってテストを「緑」または作業を `closed` とは申告しません。

## protocol の導出可否

現行 producer からは導出できません。

根拠:

- spec dataclass 群に `protocol` がありません: [floor_pair_driver.py:153](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-author-a/orchestrator/campaign/floor_pair_driver.py:153)
- build receipt の exact top-level / receipt / subject key 集合にもありません: [s8b_binary_admission.py:41](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-author-a/orchestrator/campaign/s8b_binary_admission.py:41)
- receipt validator は未知 top-level key を拒否します: [s8b_binary_admission.py:309](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-author-a/orchestrator/campaign/s8b_binary_admission.py:309)

issuer は推測や既定値を使わず、`B4FloorIdentityError.missing_elements == ("protocol",)` で発行を拒否します。

## 受理集合

変更前:

- 権威 floor issuer / loader / §5 resolver は存在せず、既存 caller の受理・拒否挙動に変更はありません。
- 材料レポートは引き続き floor 不在経路のままです。

変更後の新規面:

- canonicalな単一 pin `floor-pair-summary/v2`、`status == "generated"`、summary-bound spec hash一致、再導出値の `==` 一致、exact `0 <= floor < 1` を受理。
- `upper` の bool、自己矛盾、別schema/status、spec改竄、非canonical JSON、欠落identityを拒否。
- authority loader は canonical `p3-b4-authoritative-floor/v1`、content hash、exact ratio/source float整合、逐語の非保証欄を要求。
- resolver は exact `未記入` のみ不在。指定grammar以外、missing file、hash/schema不一致は fail-closed。
- 現行実 summary は自己整合summaryとして受理しますが、権威成果物の発行は `protocol` 欠落で拒否します。

## 波及可能性

- 現時点の所有外 caller はゼロ。単位 B の `p3_b4_material_report.py` が resolver の最初の production callerになります。
- 新規 integration test は `test_floor_pair_driver._run_production` と `NOW` を共有し、実 `finalize_floor()` を呼びます。
- M1 test は実 `p3_b4_analysis_contract.as_b4_exact_fraction()` に依存します。
- production file scan の波及候補は `test_official_perf_closure.py`、`test_s8b_floor_campaign.py`、`test_campaign.py`、`test_p3_exploration_namespace.py`。
- consumer 配線後は `test_p3_b4_material_report.py` と `test_real_repo_serialization.py` の node golden が波及候補です。

## 総括

D-1/2/3/6/7 と単位 A 対象の M1–M6/M10/M11 を新設2 file内に実装しました。  
丸め・adoption record・caller identity/floor surface はありません。  
現行 `protocol` は導出不能で、欠落名付き拒否になることを実測しました。  
docs・構文・diff検査は rc=0 です。  
pytest は Pegasus dispatch infrastructure rc=16 のため未実走であり、実装済み・未実走です。