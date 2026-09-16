# 台帳 entry の保持 field — 実測と導出 (2026-09-16 JST)

すべて `/work/1/SFC/tanab/izanagi` の主 checkout で実測した。導出規則は
`tools/check_branch_rescue.py` の `_retention()` / `_gc_observation()` の逐語に従う。

## repo 全体 (30 entry 共通)

| field | 値 | 出所 |
|---|---|---|
| `gc_auto_threshold` | 6700 | `git config --get gc.auto` は未設定。実装 `_config_value(git, "gc.auto", "6700")` の既定 |
| `gc_auto_sample_fanout` | `17` | schema 固定値 |
| `gc_auto_sample_count` | 18 | `.git/objects/17/` の実測 entry 数 (`sum(1 for _ in sample_path.iterdir())`) |
| `gc_auto_sample_threshold` | 27 | `(6700 + 255) // 256 = 27`。実装の `math.ceil(6700/256) = 27` と一致 |
| `gc_auto_heuristic_version` | `git-2.34.1-fanout-17-sample` | schema 固定値。実測 `git version 2.34.1` と一致 |
| `loose_count_at_loss` | 4616 | `git count-objects -v` の `count:` (実装の `total_loose_count_observation`) |

`gc.pruneExpire` は未設定なので実効値は git 既定の `2.weeks.ago`。
pack は 18 本、`in-pack: 171779`、`prune-packable: 0`、`garbage: 0`。

## object ごと

`git verify-pack -v` を 18 本すべての `.idx` に掛けて 30 OID を索いた (実装 `_pack_index` と同じ方法)。

- **pack に在る 26 件** → `storage_kind = "packed"`、`object_mtime = null`、
  `lower_bound_basis = "assessment-time-conservative-floor"`、
  `loss_possible_not_before` = 評価時刻 (実装は `lower_bound = now`、理由は
  「pack mtime is not an object-specific unreachable time」)。
- **pack に無い 4 件** (loose のみ) → `storage_kind = "loose"`、
  `lower_bound_basis = "loose-object-mtime-plus-prune-expire"`、
  `loss_possible_not_before = max(now, loose_mtime + 14 日)`。

loose 4 件の実測 mtime (UTC):

| oid | loose mtime | mtime + 14 日 |
|---|---|---|
| `1d41c41714b66ecb54eb23d52602fb7f8170602a` | 2026-09-09T04:23:58Z | 2026-09-23T04:23:58Z |
| `f181f703d1d68ab2bbd03ad2d6f594dfe039f030` | 2026-09-09T04:24:06Z | 2026-09-23T04:24:06Z |
| `c656d831e30ee0c261538889991af6c30bb45e89` | 2026-09-09T04:28:53Z | 2026-09-23T04:28:53Z |
| `54d4dd9b3eb270307e6294b9ac9b1484f7ba868f` | 2026-09-09T04:28:58Z | 2026-09-23T04:28:58Z |

この 4 件は評価時刻 (2026-09-16) から 7 日以内に期限が来る。`pending` で残すと
`pending-ledger-entry` が `urgent` で発火する。

## assessment 系

- `assessment_schema` = `izanagi-branch-landed-v1` (schema 固定値)。
- `assessment_verdict` = `indeterminate` (全 30 件)。`check_branch_landed.py` は本 repo で
  `COMMAND_TIMEOUT_SECONDS = 5.0` に阻まれて必ず `assessment-timeout` で倒れる。
- `assessment_reason` = `assessment-timeout`。
- `assessment_report_sha256` = 当該 OID に対する `check_branch_landed.py` の **stdout の sha256**
  (実装 `_landed_assessment` の `hashlib.sha256(result.stdout).hexdigest()` と同じ定義)。
  30 件それぞれについて実走して採る。

## source 系

- `source_refs` = `[]`、`source_tips` = `{}`。本 entry 群は branch 削除の事前 report 由来ではなく、
  `--ledger-check` の `unledgered-audit-finding` 由来である。削除起点の ref は存在しない。
  実装 `_validate_ledger_entry` は空 list / 空 dict を受理する (`all()` が空で真)。
