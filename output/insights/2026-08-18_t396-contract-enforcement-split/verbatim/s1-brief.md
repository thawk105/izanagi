# 段 1 brief — [T-396] 裁定 A/B の実装

wave = `dev-wave-t396-contract-alignment` / 基準 main = `a160f4aa` / 2026-08-18

## scope

裁定 4 件のうち **A と B だけ**を実装する。

- **C は実装しない** — 既に実行済み。`docs/archive/worklog-phase3-0816-568.md:474` が
  [T-1148]「verifier の予定操作数検査を設計・実装する」として起票し、現 worklog (642〜646) でも
  active に carry されている。再起票は二重在籍になる。
- **D は実装しない** — 見送り確定 (commit `4dd87752`)。D344 も覆さない。

## 確定済みユーザー裁定 (攻撃対象ではない)

- A = 契約側を実態へ合わせる。ただし契約文だけが実態より広い状態は放置しない。
- B = テストで恒久化された bounded loop の固定を外して未定義へ戻す。
- 規律 2 を緩める方向の変更は採らない。実装面は Codex author (D95)。
- 正本 = `output/insights/2026-08-15_t396-hole-allowlist-refuted/README.md`。

## 不変条件

1. **受理集合を 1 bit も変えない。** `coder_effect_gate.py` / `sort_swo_oracle.py` /
   `diff_quarantine.py` の production 実装は編集面外。
2. **契約文の禁止を 1 つも撤回しない。** 二分は「誰が執行するか」の注記であり、禁止の緩和ではない。
3. agent md は coder への live prompt である。「機械は見ていない」とだけ書けば許可と読まれる。
   残余項には必ず「auditor が拒否する / 禁止は不変」を同じ場所に書く。
4. typed IR / AST allowlist を作らない (D344)。
5. `DESCRIPTION_SHA256` / `ROLE_MANIFEST_SHA256` / `SCHEMA_SHA256` を不変に保つ
   (frontmatter description・`manifest.json`・schema を触らない)。
6. 対象は sort role 1 枚。`coder-v4-autonomous-trigger-gating` / `coder` へ一般化しない
   (DW-G03 — 同型欠陥の独立 2 例が無い)。

## 成果物影響 (DW-G05)

- **A を実装しない場合**: certified 選択の値・proof chain は変わらないが、closed-region 5 項目が
  「機械執行済み」と誤読され、sort 軸 variant の受理経路で auditor の人手検査が省かれうる。
  gate 説明の誤りが材料レポートへそのまま引用される。
- **B を実装しない場合**: 受理集合は今は変わらないが、機械執行を強める後続 wave
  ([T-1148] 系) が既存テストの反転を強いられ、D96 手続なしには着手できない構造が残る。

## 変更面 (実アンカー)

| # | file | anchor | 変更 |
|---|---|---|---|
| 1 | `.claude/agents/coder-v4-autonomous-sort.md` | 「**Closed-region 制約 (D23 道Y、hook が機械執行する部分と auditor が目視する部分の併用):**」節の 5 bullet | 「機械執行される項目」/「auditor が拒否する残余 (機械は見ていない)」へ二分。禁止は全て残す |
| 2 | `orchestrator/codex_roles/review_ledger.py:21` | `SOURCE_FILE_SHA256["coder-v4-autonomous-sort"]` = `577af0d4…` | 新 sha256 + レビュー日付コメント |
| 3 | `.codex/role-adapters/coder-v4-autonomous-sort.json` | `developer_instructions` の `<<<CLAUDE_ROLE_BODY_BEGIN>>>`〜`<<<CLAUDE_ROLE_BODY_END>>>` | renderer 出力で再生成 (`tools/check_codex_agents.py:234` が byte parity を要求) |
| 4 | `orchestrator/tests/test_coder_effect_gate.py:150-163` | `test_ordinary_for_range_for_and_data_dependent_loops_pass` (5 param) | bounded / data-dependent loop の「通る」固定を外して未定義へ戻す |

## 段 0 で実測した gate 閉包 (「gate が無い」と書かないための表)

sort hole text が通る production 列 = `load_proposal_file` (`p3_s4_loop_sort.py:359`) →
`drive_iteration` (`:415`) → `_quarantine_and_audit` (`:145`) →
`L.quarantine` (`p3_s4_loop.py:229-246`, ここで `DiffQuarantine.validate()` →
`coder_effect_gate.scan_host_effects`) → auditor gate → `check_materialized_sort_swo`
(`:180`, UNAVAILABLE は fail-closed) → `run_campaign` → `evaluate` → build。
**`scan_host_effects` は sort 軸にも適用される** (backoff 軸専用ではない、実測)。

## 攻撃対象の provisional 前提

- **(P1)** insight §7 (2026-08-15) の「5 項目の機械執行状況」は現行 main `a160f4aa` でも成立する。
  段 2 が現行 main で file:line から再導出し、どの bullet がどの gate のどの規則で執行されるかの
  対応表を作る。段 3 が攻撃する。
- **(P2)** B の正しい形は `test_ordinary_for_range_for_and_data_dependent_loops_pass` を
  **丸ごと削除**することである。過剰拒否の回帰検出力を失うが、「未定義へ戻す」以上、
  受理方向を固定するどの assert も残せない。部分削除・意図コメント追記は裁定の履行にならない。
- **(P3)** adapter JSON は codex sandbox が `.codex/` 書込を拒むため、実装子でなく親が
  renderer 出力を review して適用する (D149 / T-428 前例)。まず実装子に試させ、
  拒否を実測してから親が代行する。

## 分割方針

編集 4 枚が md → sha256 → adapter bytes → test の連鎖で相互依存するため素集合に割れない。
**単一の Codex `role=author` 実装単位**とする。段 6 の敵対レビューは 2 本。
