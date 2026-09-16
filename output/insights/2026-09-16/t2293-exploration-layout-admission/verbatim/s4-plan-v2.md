# [T-2293] Q1 段 4 裁定 — plan v2 (親の確定版)

基底: plan-v1 (段 2) + consult-A / consult-B (段 3)。裁定 = 親。日時 = 2026-09-16 20:20 JST。

## 所見の裁定

| 出所 | 所見 | 判定 | 採否 |
|---|---|---|---|
| A M1 | `type(layout) not in (A, B)` は tuple 所属 = `is` または `==` なので、metaclass の `__eq__` を持つ別型が通る | **real** (親が最小再現で検算: tuple 所属は impostor を True、identity gate は False) | **採用 (must-fix)**。両 gate を `type(layout) is not CampaignLayout and type(layout) is not ExplorationCampaignLayout` に統一し、impostor 負例を発行入口・projection 入口の両方へ加える。変異 M5 (tuple 所属へ戻す) を登録 |
| A nit | D123 (4) は継承禁止を決めたのではなく型分離を別裁定へ送った記録 | real | brief の表現を訂正 (現物では両 class に継承関係が無く、本 wave はそれを変えない) |
| A nit | 「record bytes 不変」は無限定にできない (root が変われば ref path・projection・record bytes は変わる) | real | 記録では「既存入力に対する生成規則と schema (`result-evidence/v1`、`execution-provenance/v2`) は不変、use class は record に書かない」と限定する |
| A nit | pin 閉包 hit 無しは probe の帰結ではなく grep の申告 | real | 記録で根拠を分ける (DW-O09 の path 検索 + module 名検索、間接参照の全否定ではない) |
| A nit | brief (P4) の「subclass 負例が単独で kill」は外側 gate だけの照準では不成立 | real | plan-v1 の再照準 (内側 L447 + projection 直呼び負例) を採用 |
| B | root 外負例は `_producer_context` が directory を作らないので evidence root を明示 mkdir する必要 | real | author prompt へ明記 |
| B | M4 の観測集合に root 外負例が漏れている (型エラーが root エラーより先に出て match 不一致で赤) | real | M4 の expected_nodes に加え、意味 (拒否地点の前移動であって受理拡大ではない) を insight に書く |
| B | WAL 内部に型拒否が無いことは射影外 | unverified → 親が現物で確認: `wal.ordered_attempt_frames` は `layout.wal_file` の存在検査と `_iter_binary_frames(path)` だけで layout の型を見ない | M1/M2 の単一理由性は静的に成立。実走で確かめる |
| B | 実 runner の tmp 配置が worktree container 外か未確認 | unverified | `tools/run_tests.py` は `--basetemp` を既定で渡さず、conftest は TMPDIR を設定しない → pytest 既定 `/tmp/pytest-of-<user>/`。焦点走で resolved path を 1 回確認する |
| B | probe は `run_campaign` の統合到達性を証明しない。WAL 5 frame は helper の作成であって producer 内の消費ではない | real | 記録の表現を訂正。統合正例で担保し、skip を成功扱いしない (compiler helper の skip を焦点走で検出する) |
| A/B | 全面作り直しは不要 | — | plan-v1 を M1 と M4 の局所改訂で確定 |

scope 外の real 所見: なし。裁定パッケージ: なし。

## 確定した変更面

production: `orchestrator/campaign/reflux_result_evidence.py` のみ。
1. L34: `from .layout import CampaignLayout, ExplorationCampaignLayout, validate_campaign_id`
2. L447-448 (`_ordered_attempt_materials`):
   ```python
   if (
       type(layout) is not CampaignLayout
       and type(layout) is not ExplorationCampaignLayout
   ):
       raise ResultEvidenceError(
           "layout must be an exact CampaignLayout or ExplorationCampaignLayout"
       )
   ```
3. L1090: `_context_roots(*, layout: CampaignLayout | ExplorationCampaignLayout, ...)` (注釈のみ)
4. L1213-1214 (`issue_campaign_result_evidence`): 2 と同じ述語・同じ message。

**gate の署名と含意:** `issue_campaign_result_evidence(*, layout: object, ...)` と `produce_ordered_wal_projection(*, layout: object, ...)` は、`type(layout)` が `CampaignLayout` または `ExplorationCampaignLayout` と**同一** (identity) のときだけ型 gate を通す。受理の含意: 型 gate 通過は発行を意味せず、context・capability・contract・receipt・root 包含・WAL・record の既存検査をすべて通る必要がある。拒否の含意: 両型の subclass、metaclass 等価比較の別型、`root`/`wal_file` を持つ duck typed object、`str`/`Path`/`None` は型 gate で拒否し、exact 探索 layout でも physical root が evidence root 外なら `_context_roots` の既存包含検査で拒否する。
**通る正例:** `exploration_campaign_layout("fixture-physical-run", os.fspath(evidence_root)).ensure()` に有効な attempt の WAL を記録し、`issue_campaign_result_evidence(layout=<それ>, context=_producer_context(evidence_root), ...)` → `evidence_root / context.expected_record_path` に record が create-only で書かれ、resolve できる。

tests:
- `orchestrator/tests/test_reflux_result_evidence.py`: `_producer_layout(evidence_root, *, kind="official")` (kind ∈ {"official","exploration"})、`_log_producer_attempt` / `_issue_producer_record` の layout 注釈を緩める。正例 L1123 を `@pytest.mark.parametrize("kind", ["official", "exploration"])` で両 layout 化 (探索側は exact 型と namespace marker の存在も assert)。負例 (id は下の nodeid 表のとおり): 発行入口 = subclass[official|exploration]、duck[frozen|namespace]、non_layout[str|path|none]、type_equality_impostor[official|exploration]、exploration_root_outside_evidence_root (evidence root は明示 mkdir、探索 layout は `tmp_path/"outside-output"` を base に作る、`match="^physical campaign root is outside the result evidence root$"`)。projection 入口 = 同じ subclass / duck / non_layout / impostor を `produce_ordered_wal_projection` に直接渡す (有効な build attempt と実 WAL の terminal prefix digest を持つ `source_wal_ref` を渡し、型 gate を緩めたとき digest 不一致などで代わりに落ちない fixture にする)。発行入口の負例は前後の `_file_snapshot` 同一と `expected_record_path` 不在も assert。型負例の match は `^layout must be an exact CampaignLayout or ExplorationCampaignLayout$`。
- `orchestrator/tests/test_reflux_campaign_issuer.py`: `_drive_campaign(..., declared_use_class="official")` 引数化 (L433 の固定文字列を置換、既定は official)。新規 `test_real_run_campaign_exploration_issues_rejected_record`: `_drive_required_campaign(..., declared_use_class="exploration", context=context)` で `context.evidence_root` = `output_root`、assert = aborted 1 / committed 0、`issued.layout_root == exploration_campaign_layout(issued.campaign_id, output_root).root`、導出 record が存在し parse/resolve でき outcome が rejected、`ExplorationCampaignLayout` で読んだ WAL interval と resolver の source bytes 一致、source-WAL / projection / provenance が探索 physical root 配下。

触らない: `acceptance_duration_ledger.json`、`p3_autonomous_workload_trial.py`、`reflux_formal_consumer.py`、他 module の exact gate、Q2〜Q4、record schema。

## 変異事前登録 (DW-M01、実装前に登録)

runner = `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_reflux_result_evidence.py orchestrator/tests/test_reflux_campaign_issuer.py -q -rf`。spec は `wave/mutation-spec.v1.json` (job dir、checkout 外)。expected_nodes の nodeid は実装後の収集 (probe 走) で綴りを固定し、集合は下記から変えない (変えるときは理由を記録)。

| id | 位置 | 変異 | category | 期待 | 単一理由性 |
|---|---|---|---|---|---|
| M1 | 内側 L447 | 述語を `not isinstance(layout, (CampaignLayout, ExplorationCampaignLayout))` へ | negative | KILLED: projection subclass[official], [exploration] | 内側は外側 L1213 を通らず WAL reader に型拒否なし。duck/impostor/non-layout は isinstance でも拒否されるので観測に入らない |
| M2 | 内側 L447 | 述語を `not hasattr(layout, "wal_file")` へ | negative | KILLED: projection subclass ×2、duck ×2、impostor ×2 | `wal_file` を持つ 6 負例が全て同じ gate の緩和で受理される。str/Path/None は属性が無く拒否されたまま |
| M5 | 内側 L447 | 述語を `type(layout) not in (CampaignLayout, ExplorationCampaignLayout)` へ | negative | KILLED: projection impostor[official], [exploration] | tuple 所属の `==` だけが impostor を通す。subclass/duck は tuple 所属でも拒否 |
| M3 | 内側 L447 | 述語を `type(layout) is not CampaignLayout` へ (旧 gate) | positive | KILLED: unit 正例[exploration]、統合 exploration 正例 | 外側は探索型を通し、root 包含 (E:1278) は内側 (E:1285) より先に評価されるので root 外負例は緑のまま |
| M4 | 外側 L1213 | 述語を `type(layout) is not CampaignLayout` へ (旧 gate) | positive | KILLED: unit 正例[exploration]、統合 exploration 正例、発行入口 root 外負例 | root 外負例は型エラーが先に出て match 不一致 = 拒否地点の前移動 (受理拡大ではない)。insight に明記 |
| M6 | 内側 L447 | 2 つの `is not` 節の順序を入替え (等価変異) | positive | SURVIVED (expected_nodes 空) | harness の SURVIVED 検出の正例 |

登録しない: 外側 L1213 だけの isinstance/hasattr/tuple 緩和 (内側が同じ入力を拒否、観測 0 件)、両 gate 一括緩和 (単一箇所で測れる)、`_context_roots` の root 包含除去 (loop L303 / E:1173 が重複拒否、別文言の赤は実効 gate の kill ではない)。

## 段 5 の分割

author 1 本 (Codex `role=author`、workspace-write、別 worktree `.codex/worktrees/t2293-explayout-impl`、branch `impl-dev-wave-t2293-explayout`)。所有 = 上記 3 file。docs 編集・commit・ledger 編集は禁止。

## 段 6 追記 (20:47 JST) — 変異登録の改訂 (実走前)

review B の must-fix (real・採用): 負例 helper `_assert_layout_projection_rejected` が正例を同居させていたため、M3 で負例 node 2 件が正例過剰拒否という別理由で赤化する。fix 1 で正例を `test_ordered_wal_projection_accepts_exact_layouts[official|exploration]` へ分離した。これに伴い **M3 の期待集合を 3 件へ改訂** (unit 発行正例[exploration] + 新設 projection 正例[exploration] + 統合 exploration 正例)。M1/M2/M4/M5/M6 の期待集合は不変 (projection 正例は real layout を渡すので M1/M2/M5 の緩和では緑のまま、M4 は projection 入口を通らない)。spec = `mutation-spec.v2.json` (sha256 1450ebb8…)。probe spec = `mutation-spec.probe.json` (全件 SURVIVED 期待、sha256 c33ca90b…)。
