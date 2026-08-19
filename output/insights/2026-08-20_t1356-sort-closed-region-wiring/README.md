# [T-1356] sort closed-region 残余を auditor の gallery/checklist/入力へ結線した

2026-08-19〜20、dev-wave `wave-t1356-sort-closed-region-wiring`、基準 main = `050b0648`。
2026-08-18 /rulings 全件 第8回の裁定 (`docs/archive/worklog-phase3-0819-671.md:551-554`)
「sort の closed-region 残余を auditor の入力と checklist へ結線する」の実装。

**受入投入前に local main (25+ commit 先行) を `git rebase main` で取り込んだ。**
別 wave が `orchestrator/codex_roles/review_ledger.py` の別キー (`planner-v4`、本 wave が
触ったのは `auditor` キー) を編集済みで、merge commit にすると
`check_ai_provenance.py` (D95) が「3方向結合の結果が両親のどちらとも異なる」として
Codex role=author trailer を要求し、待ち手の自動 merge 手順 (`stage=merge-message-provenance`)
が進めない状態だった。rebase で線形履歴にすることでこの検査を回避した (5 commit とも
無競合で自動適用、`check_ai_provenance.py` 再監査 rc=0)。下記の commit hash は
**rebase 後の値**。verbatim/ 以下の逐語ファイルと変異 matrix の JSON は生成時点の
(rebase 前の) hash を保持したままの凍結記録であり、書き換えていない。

逐語は `verbatim/` (段2 plan、段3 両レンズ、段6 両レビュー・焦点レビュー)。

## 1. 背景 — 何が未結線だったか

T-396 (2026-08-18、commit `dc87fff7`) が `coder-v4-autonomous-sort.md` の closed-region 契約へ
「機械執行の範囲」表 (完全/部分的/なし の3分類) を後置した。5項目 (新しい型/関数の追加・
非決定ビルトイン・副作用のある呼び出し・ループ・例外送出) のうち「部分的」「なし」に
分類された残余は、auditor の checklist/gallery に一切結線されておらず、「謳うだけで発火しない」
契約項目のままだった (T-396 自身がこれを real 所見として明記、実装は sort role 1枚だけを
触る裁定だったため見送っていた)。

## 2. 段2-3: プラン・敵対相談で見つかった構造

- **共有 gate の実測**: `orchestrator/campaign/auditor_gate.py:29` の
  `_AUDITOR_VIOLATION_TYPES = frozenset(range(1, 17))` が、auditor が引用できる violation type
  の唯一の実 gate である。`orchestrator/codex_roles/manifest.json` の output schema にも
  独立に `"maximum": 16` があり、両方を同時に広げないと新しい gallery 型を auditor が
  引用した瞬間 `AuditorGateFailure` で reject される (型5「consumer 取り残し」の自己再演)。
- **pin 閉包**: `orchestrator/codex_roles/review_ledger.py` の3 pin
  (`SOURCE_FILE_SHA256`/`ROLE_MANIFEST_SHA256`/`SCHEMA_SHA256["output"]`、いずれも `"auditor"`
  キー) と `.codex/role-adapters/auditor.json` (Codex sandbox が `.codex/` を read-only
  mount するため親が D105 waiver で再生成) が閉包に入る。
- **[段3 レンズB, real, 採用] 入力側の未結線**: `docs/phase3-s5-sort-runbook.md` の auditor
  spawn 手順は `designated_sources` に coder-v4-autonomous-sort.md の API 宣言を含めることを
  明示していなかった。裁定文言「auditor の**入力**と checklist へ」の入力半分が手つかずだった。
  親が直接 (docs-only) 追記して解消した。
- **[段3 レンズB, real, 採用] 型番号は5個 (17-21) に分割**、1個への集約 (段2案) は採用しなかった。
  型8-12 (5個の独立 lock 系統) を前例とし、1個集約は将来「5項目のうちどれを検査したか」の
  集計を不能にするため (規律3 の構造化シグナル要求)。

## 3. 段5-6: 実装・敵対レビュー・fix

- 実装 (commit `a5b676c7`、rebase 前は `10f6d4f6`): auditor.md へ型17-21・checklist14、manifest.json の
  `maximum: 16→21`、review_ledger.py の3 pin、auditor_gate.py の `range(1,22)`、境界テスト2本、
  `p3_autonomous_workload_trial.py` の表示数値更新 (trigger-gating 専用 driver、型を実際には
  使わないが共有 gate の実際の上限と数値を一致させる)。
- adapter 再生成 (commit `dd9df29d`、rebase 前は `66e50e4b`、D105 waiver `reason=codex-sandbox-readonly-dotcodex;
  ratified=2026-08-18` の再利用。段3 両レンズが独立に「reason の鮮度検査は無い」と裏取り済み)。
- **[段6 レンズB, must-fix, real] D48/D511 違反を検出・是正**: 実装時の型17-21記述が、
  機械 gate が検査しない/部分的な**具体的識別子・検出/未検出のループ形・corpus 発火条件**を
  file:line 付きで開示しており、これは合成側 LLM が読める回避手順の開示だった
  (T-396 が一度是正した同型の誤りの再演。親の段5 prompt 自体が「機序を file:line 付きで書け」と
  指示したことが D511 と緊張関係にあった)。fix (commit `9edb7449`、rebase 前は `e55c3a9a`) で
  `.claude/agents/coder-v4-autonomous-sort.md` の「機械執行の範囲」表と同じ抽象度 (完全/部分的/
  なしの分類だけ) へ後退させ、機序説明は auditor 自身の構造化出力 `verifier_blind_spot`
  (発見時の事後報告) に委ねる設計にした。adapter 再々生成 (commit `068532c4`、
  rebase 前は `2ec1d382`)。
- fix commit の trailer で scope 値に大文字 (`s6-revA`/`s6-revB`) を使い、`docs/ai-provenance.md`
  の `IDENT` 正規表現 (小文字のみ) 違反で全史監査が rc=1 になった。`git reset --soft HEAD~1`
  (非破壊、ファイル内容は完全温存) で trailer だけを訂正し再commit (`amend` は使わない既定規律)。
- 焦点再レビュー (`DW-S06-C`): 全所見 closed、GO を確認。

## 4. 変異 matrix

| ID | 対象 | 手法 | 結果 |
|---|---|---|---|
| M1 | `auditor_gate.py:29` range(1,22)→(1,17) | 標準harness (node直接指定) | KILLED, matches_expectation=True |
| M2 | `manifest.json` maximum 21→16 | 手動 (collection error 単一原因) | `RoleSpecError: manifest.json:roles.auditor: reviewed full manifest role SHA256 drift` |
| M3 | `review_ledger.py` auditor pin stale | 手動 (collection error 単一原因) | `RoleSpecError: auditor.md: reviewed SOURCE_FILE_SHA256 drift` |
| M4 | `.codex/role-adapters/auditor.json` source_file_sha256 破壊 | 標準harness (node直接指定) | KILLED, matches_expectation=True |

M2/M3 は `tools/mutation_harness.py` の canonical node 抽出器が pytest collection ERROR
(`test_codex_agents.py` が module import 時に全13 role の pin を即時評価するため、1件でも
drift すると個別 `::test_name` でなくファイル全体 1件の collection error になる) を扱えず
fail-closed abort したため、Edit→`tools/run_tests.py`実走→`git checkout --`復元の手動検証に
切り替えた (T-1411 前例と同型)。M1/M4 も当初は3ファイル合計166テストの collection 出力が
dispatch capture のバイト上限で切り詰められ誤 abort したため、`file::test_name` の直接指定へ
retarget して解消した。詳細は memory
`mutation-harness-collection-error-needs-manual-verify`/`mutation-harness-collection-output-byte-cap`。
4件とも baseline PASSED・単一原因の赤を確認し、pin 閉包 (schema/gate/ledger/adapter の
4箇所すべて) が実効的に機能していることを実証した。

## 5. 不変条件の確認

CC variant 側の raw 受理集合 (`coder_effect_gate.py` の DENY_TABLE、`sort_swo_oracle.py` の
判定ロジック) は本 wave を通じて1 byte も変更していない。`coder-v4-autonomous-sort.md` の
禁止5 bulletも1 byte も変更していない (T-396/D511 の禁止文不変原則を維持、契約文への
反映は本waveのscope外と明記)。変更したのは auditor の指摘語彙 (violation type 受理範囲
16→21) と gallery/checklist 本文のみ。auditor gate の reject 経路の粒度は変わる
(意図した効果) が、trigger-gating とも共有する gate のため型番号の受理範囲自体は波及する
(trigger 側 driver は型17-21を実際には引用しない、`p3_s4_loop_trigger_gating.py`/
`auditor_gate.py` の reject 判定ロジック自体は型番号で分岐しないため実害なし、段6レンズBが
実測確認)。

## 6. 環境と実測

性能計測は行っていない。焦点走 (adapter再生成後、fix後の最終状態) =
`test_auditor_gate.py`+`test_p3_s4_loop_trigger_gating.py`+`test_codex_agents.py`+
`test_check_docs.py`+`test_critic.py`+`test_p3_build_authority_cli.py`+`test_p3_s4_loop_sort.py`+
`test_p3_autonomous_workload_trial.py` = **1030 passed / 3 skipped / 0 failed** (親が直接実走、
Codex子はPegasus dispatch制約でpytest実走不能のため代替せず)。`check_codex_agents.py` rc=0、
`check_docs.py` rc=0、全史 provenance 監査 (`check_ai_provenance.py`) 4件のcommitすべて
rc=0・新規違反なし。受入全走の結果は worklog エントリへ記録する (本README執筆時点で未実施)。

エージェント工数: codex 子 6本 (plan 1 [researcher]・consult 2 [reviewer, lane sol/luna]・
author 1・review 2 [reviewer]・fix 1 [author])。全 job で `model=gpt-5.6-luna` 実測
(`--lane` は consult 専用でモデル選択とは別軸)。plan/consult は明示 `--reasoning max`、
author/review/fix は docs-authority 由来の自動導出 (T-1362 相当の拘束が main へ着地済みと
本wave中に実測、`--reasoning` 明示指定は rc=2)。
