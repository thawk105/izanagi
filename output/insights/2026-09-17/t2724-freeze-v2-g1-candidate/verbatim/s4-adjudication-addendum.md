# 段 4 追補 — 実測で出た must-fix C-1 と plan v3 (2026-09-17 01:35 JST)

## C-1 (must-fix、実装面あり): producer が固定 protocol の literal read で official result を拒否する

- **実測:** chain 木 (HEAD = X1 `0287c26d0`) で `generate-v2-candidate` は rc=1
  `fails-closed: floor result.protocol_sha256 が固定 protocol hash と不一致`。
  固定 `output/s8b-freeze/floor_protocol.json` (raw sha `261cec1c…`、ccbench_pin `d706650c…`) と
  official 走行が解決した版付き `output/s8b-freeze/floor-protocols/e576e9cd…--511c9538….json`
  (raw = canonical sha `2c8cf9be…`、pin `511c9538…`) は ccbench_pin だけが違う (diff で 1 行)。
  result は `protocol_sha256 = 2c8cf9be…`、path の proto8 も `2c8cf9be`。
- **原因:** `s8b_holdout_freeze._validate_floor_inputs` (HF:1389〜1414) が `FLOOR_PROTOCOL_REL` を
  literal で読み、その canonical hash を result に要求する。campaign 側 (`floor_campaign.sh` /
  `s8b_holdout_admission._authority`) は D460 型の index authority `resolve_current_floor_protocol`
  で版付き protocol を解決する。producer は 2026-08-11 実装で、2026-08-12 の pin 前進 ([T-816]) に
  追随していない。admission 側 `_authority` は解決 record と producer が渡す `protocol` 文書の一致も
  要求する (HA:851〜856) ので、hash 比較だけ直しても通らない。
- **既裁定:** D589 (2026-08-20) がこの箇所を名指しし「current の literal read で D460 型変換の
  対象になり得るが、承認 artifact・pin ratify・official result の 3 条件が揃わず到達不能なので
  本 wave では実装しない (DW-G04)」と deferred。3 条件は今日すべて揃った (承認 09-05、pin 済み、
  official result 09-16) ので発火条件成立。D460 (caller に選ばせず index authority で解決) の
  設計方向は裁定済み。
- **裁定:** 本題 (候補生成) に必要な実在欠陥の局所修正として scope に入れる (DW-G05)。
  実装面 → Codex author (D95)、段 6 敵対レビュー 2 本 + 変異 matrix + 焦点走。受理集合の変化:
  「固定 protocol と一致する result だけ受理」→「index authority が解決した現行 protocol と一致する
  result だけ受理」。方向は D460 と同じで、走査・admission・批准側は変えない。
- **却下:** (a) 固定 `floor_protocol.json` の pin を書き換える — `output/s8b-freeze/` の凍結 bytes
  (guard 拒否、historical anchor、`test_floor_protocol_historical_anchors_remain_legacy` が literal を
  pin) → 規律 2。(b) result 側を書き換える — 測定成果物の改変。(c) 停止して裁定へ返す — 設計方向は
  D460 / D589 で裁定済み、ユーザー常設指示 (裁定へ返さず決める)。

## 変更面 (Codex author の所有)

| file | 変更 |
|---|---|
| `orchestrator/campaign/s8b_holdout_freeze.py` | `_validate_floor_inputs`: 固定 path の literal read を `s8b_floor_campaign.resolve_current_floor_protocol(root=root)` の record へ置換 (record.path / raw_bytes / document)。record の commit_oid == captured HEAD、worktree bytes == HEAD blob の検査は残す。`validate_protocol` / canonical sha / `protocol.freeze` 固定検査 / header field 比較は不変。返り値に protocol path を足し、`build_v2_g1_candidate` の `document["floor_protocol"]` は解決 path + raw sha を記録。`_measurement_closure` の専用 path に解決 path を足す (FLOOR_PROTOCOL_REL は残す)。`FLOOR_PROTOCOL_REL = "…"` の代入 1 件は削らない (historical anchor test の pin)。新しい subprocess spawn 点を作らない (`test_ccbench_spawn_sites` の台帳)。`use_perf_from_receipt` / `result_keys_for_mode` / `validate_manifest_v3` の呼出しは残す (`test_official_perf_closure` の AST 述語) |
| `orchestrator/tests/s8b_v2_freeze_fixture.py` | `candidate_repository` に「版付き protocol (pin = fixture ccbench HEAD) を index に足し、result はそれで作る」option |
| `orchestrator/tests/test_s8b_holdout_freeze.py` | 正例 (版付き解決で生成成功、`floor_protocol` が解決 path と raw sha)、負例 (固定 protocol のまま result が版付き hash → `protocol_sha256 不一致` で拒否 = 現行挙動の保持、worktree 改変 → HEAD 不一致拒否) |

## 変異事前登録 (DW-M01、実装前)

| ID | 変異 (位置) | 期待 | 殺す test (期待 node) |
|---|---|---|---|
| M0 | `_validate_floor_inputs` に comment 1 行追加 (等価対照) | SURVIVED | — |
| M1 | 解決 record を捨て `FLOOR_PROTOCOL_REL` の literal read へ戻す | KILLED | 新正例 (版付き解決で生成成功) |
| M2 | `document["floor_protocol"]["path"]` を `FLOOR_PROTOCOL_REL` に固定 | KILLED | 新正例の `floor_protocol` 一致 assert |
| M3 | 解決 path の worktree bytes == HEAD blob 検査を削除 | KILLED | 既存 `test_v2_candidate_rejects_worktree_only_floor_protocol_master_seed_mutation` (fixture が固定 path 1 件のとき解決 = 固定 path) または新負例 |
| M4 | `result.protocol_sha256 == protocol_sha256` の比較を削除 | KILLED | 新負例 (hash 不一致の拒否) |
| M5 | `protocol.get("freeze") == {FREEZE_REL, HOLDOUT_RAW_SHA256}` 検査を削除 | KILLED | 既存 freeze 不一致 test (author が nodeid を名指し) |

単一理由性は実装後に author が確認し、殺せない登録は再照準する (F28)。

## plan v3

1. 段 5: author (workspace-write、`.codex/worktrees/t2724-impl`、base X0) → 段 6: review 2 本 + fix + 変異 matrix (container 木) + 焦点走 (`test_s8b_holdout_freeze.py`、`test_s8b_protocol_builder.py`、`test_official_perf_closure.py`、`test_ccbench_spawn_sites.py`、`test_s8b_floor_stats.py`、`test_s8b_ratified_freeze.py` の consumer 部分)。
2. 親が所有 path 限定 patch を wave 木へ展開し commit P (AI-Agent role=author は Codex 子、integrator は親)。
3. chain 木: X1 を捨て `P` から作り直す (bundle は固定退避先に残るので restore 再実行可) → X1' (入力 6 file) → generate (HEAD = X1') → X2 → 静的検証・走査。chain = X0 → P → X1' → X2 で P は wave と共有。
4. 以降は段 4 本文の plan v2 §3 と同じ (docs、insight、fragment、段 7〜9)。
