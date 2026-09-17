# [T-2445] [T-2680] next-tasks の Codex skill を repo 内 adapter へ移設し、共通自己改善契約と checker へ登録した (2026-09-17)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。

wave: `dev-wave-t2445-next-tasks-skill-relocation` (branch `worktree-dev-wave-t2445-next-tasks-skill-relocation`)。
起点 main `b4631a92e`。commit 列: docs `835a2dc33` (親、D744) → checker `e9a4efeae` (Codex author) → decisions
fragment `e6e620c40` → docs fix `3183ec132` (親) → checker fix `988905881` (Codex author) → 記録 commit (本 README)。

## 何を閉じたか

- **D2104 項 37**: `~/.agents/skills/next-tasks/` (SKILL.md 13,255 bytes、sha256
  `39d3247e816437c5c33d85a29ff3a7313c06610028339948b39844351dc982d2`、2026-09-10 版) を repo 内
  `.agents/skills/next-tasks/` へ移設。形は既存 3 skill と同型の薄い adapter (5,730 bytes) で、
  `.claude/commands/next-tasks.md` を共通 dispatcher として全文読む。`agents/openai.yaml` は原本 (208 bytes、sha256
  `22dac38bf55a6e9c0e2efcb87f95511de6547fe896bc995de10344a7801bffbb`) と bytes 同一。byte 予算は
  `tools/check_docs.py` の `_check_codex_skill_guard("next-tasks", ...)` に登録 (SKILL.md 5,732 = ceil(5730 × 3000 / 2999)、
  yaml 300、23 literal の存在、yaml exact、2 file 閉包)。
- **D1890 (1)** (= T-2680): `docs/skill-self-improvement.md` に next-tasks の発火 gate と `### next-tasks` 終端を登録し、
  checker の終端 pin `REQUIRED_SELF_HEADINGS[3]` に `next-tasks` を足した。契約文書は 5,999 → 5,997 bytes (上限 6,000
  不変、`## routing` は byte 同一、縮約は重複・接続句のみ)。D782 の上限引き上げは発火しない。
- **D1890 (2)**: command の「本ファイル (repo 外)」を消し、`/work/1/SFC/tanab/scripts/` の 7 箇所を `<tools>` へ間接化
  (定義は手順節冒頭、所在は `docs/pegasus-runbook.md` §7.2 に追記)。26,903 → 26,950 bytes (上限 27,100 不変、最長行 83、
  `$ARGUMENTS` 0 件、契約への到達性 1 件)。

## 引数の前提を覆した新事実 (段 1 実測、段 3 レンズ A が 3 事実を追認)

「checker 側は登録済み」は command の予算・interface pin (entry 1352) のことで、D1890 (1) / T-2680 が言う終端 pin
`REQUIRED_SELF_HEADINGS[3]` は `{dev-wave, cleanup-branches, rulings}` のままだった。docs だけを当てた状態の
`check_docs.py` は「孤児 H3 `next-tasks`」の 1 件で赤 (`verbatim/parent-check-docs-docs-only.txt`)、checker commit で
rc=0 になった。「docs / skill 文書のみ」では裁定 2 件の中身を満たせないため、checker/test への最小登録を Codex author
で行った (段 4 裁定 P3、`verbatim/s4-adjudication.md`)。

## 設計判断 (新 D、fragment `docs/spool/decisions/2026-09-17-dev-wave-t2445-next-tasks-skill-relocation-1.md`)

1. 薄い adapter (逐語複製しない)。委譲を基本とし Codex 固有の対応と義務だけを重ねる。
2. D2051 の Codex 起動時の対応付け: 事実も選定判断も起動主体 (Codex)、Claude の見解は独立検査、Claude が挙げた/未確認
   の候補は実測せずに外さない、2 巡目 1 回、3 巡目なし、件数合わせ禁止、文責は起動主体。plan の「事実は Claude」案は
   段 3 レンズ B が反証 (相談先は read-only・15 分・裏取り 3 件の制約下で事実の権威になれない)。
3. 旧 Codex 版だけにあった出力の義務 5 件を Codex overlay として保持 (投げ文の自己改善終端、CC 不採用の理由、既存
   patch・OID・handoff の束ね、補助 artifact・検証済み単独行・handoff 記録、半角番号)。Claude 側 command は拡張しない。
4. 契約の next-tasks 終端: 昇格と起動手順は rulings と同じ、短い手順是正は command の該当節 (入口の編集条件)、道具は
   runbook の道具置き場、`docs/` は裁定パッケージ。

## 段 3 / 段 6 の所見

- 段 3 レンズ A (受理集合、`verbatim/s3-lensA.md`): must-fix 0。nit: D744 の射程は SKILL.md と yaml に限定、LF 計数規約。
- 段 3 レンズ B (意味保存、`verbatim/s3-lensB.md`): must-fix 4 (D2051 主体対応、旧版だけの義務、道具追加の裁定境界、
  brief の一般化) → すべて段 4 で採用し adapter v2 / 契約 / 裁定文へ反映。
- 段 6 レビュー A (`verbatim/s6-reviewA.md`): 実装本体 must-fix 0。変異 M5 の anchor が単行だと rulings にも一致する
  指摘 → spec は 3 行 anchor で count=1 (閉じている)。nit: 負例 needle が汎用文言、M1/M6 の広範な赤と専属検出の区別。
- 段 6 レビュー B (`verbatim/s6-reviewB.md`): NO-GO must-fix 2 (adapter の編集禁止条件が非発火時と発火時の command 是正・
  道具追加まで禁じる読み、旧版 L59 の handoff 記録義務の欠落) + nit (新 D 決定 (1) の「委譲だけ」)。段 3 must-fix は
  2 closed / 2 partial → 親が adapter v3 (`3183ec132`) で閉じ、予算 5,460 → 5,732 の追従を fix 子 (`988905881`)。
- 段 6 焦点再レビュー (`verbatim/s6-focus.md`): GO。B の must-fix 2 件・A の M5・M3 追従・fix 子の数値は closed。nit:
  needle の対象明記、`docs-fix.diff` (job dir 内の参考 diff) の比較基点の説明ずれ (成果物には含めていない)。

## 実走

- `python3 tools/check_docs.py`: docs のみ → rc=1 (孤児 H3 1 件) / checker 登録後 → rc=0 / adapter v3 のみ → rc=1
  (予算超過 1 件) / fix 後 → rc=0。
- 焦点走 7 file (`test_check_docs` + importer 3 (`test_check_ai_provenance` / `test_s8b_selector_output` /
  `test_s8c_preregistration_invariant`) + `test_dev_waves_checker` + `test_growth_test_holds_contract` +
  `test_hold_inventory`): fix 前 (`e6e620c40`) 1245 passed / 8 skipped (計算ノード 2805.nqsv、39.6 s)、fix 後 (`988905881`)
  1245 passed / 8 skipped (2868.nqsv、39.9 s)。skipped は growth hold (D753)。
- 全史 provenance (docs commit 後): 10,910 件・新規違反なし。
- 三軸語・placeholder 走査 (`s8b_holdout_freeze search`): rc=0、hit 0。
- **変異 matrix** (container worktree `t2445-mutcontainer`、`run_tests.py orchestrator/tests/test_check_docs.py`、対象は
  `tools/check_docs.py` のみ、probe 8 request + 本走 8 request): probe (`e6e620c40`、`mutation-ledger-probe.json`) で
  観測 node を集め、本走 (`988905881`、`mutation-ledger-final.json`、spec sha256 `f35b2b82…`) は baseline PASSED
  (580 passed / 3 skipped)、M0 (comment) SURVIVED、M1〜M6 KILLED で期待 node 完全一致、MISMATCH 0。

  | ID | 変異 | 観測 node | 専属性 |
  |---|---|---|---|
  | M0 | 新規定数直前の comment のみ | 0 (SURVIVED) | 等価対照 |
  | M1 | `REQUIRED_SELF_HEADINGS[3]` から `next-tasks` を除去 | 337 | 過剰決定 (合成 fixture の孤児 H3 で全 positive control が baseline 失敗)。PIN と `self_next_tasks_h3_deleted` を含む |
  | M2 | guard 呼出しを除去 | 4 | skill 負例 4 case の専属 kill (PIN は呼出しを検査しない) |
  | M3 | SKILL.md 予算を 5_732 → 573_200 | 2 | PIN + `codex_next_tasks_skill_byte_over` |
  | M4 | yaml 定数の `Next Tasks` → `Next Taskx` | 2 | PIN + `codex_next_tasks_skill_openai_changed` |
  | M5 | literals から `AGENTS.md` を除去 (3 行 anchor) | 2 | PIN + `codex_next_tasks_skill_adapter_deleted` |
  | M6 | FILES から yaml path を除去 | 337 | 過剰決定 (合成 repo の未登録実体で全 case が baseline 失敗)。PIN を含む |

  M1 / M6 の 337 は job stdout の `failures=337` と一致する完全集合 (中継上限の欠落なし)。
- 受入全走: 記録 commit 後の tip で単独に投げ、結果は land の受領証が持つ (本 README 記録時点では未実施)。

## 残存 (scope 外、記録のみ)

- Codex の skill 探索順 (repo `.agents/skills/` と `~/.agents/skills/` の優先) は未実測。land 成功後に親が home 側を
  `~/.agents/skills-retired/next-tasks-2026-09-17/` へ退避して二重化を解く (本 README 記録時点では未実施。退避時の
  sha256 は wave の最終報告と job dir handoff に残す)。現存 session が新定義へ切り替わるかは主張しない。
- 旧 Codex 版だけにあった義務 5 件を Claude 側 command にも入れるかは候補生成ロジックの拡張に当たるため scope 外。
- `next_tasks_consult.sh claude` の CLI 疎通は未実測 (静的に `codex)` / `claude)` 両分岐の存在を確認)。
- 負例 needle 3 件 (`_openai_changed` / `_adapter_deleted` / byte) は既存 case と同じ汎用文言 (nit、単一理由性は
  個別 fixture で保たれる)。

## 逐語

`verbatim/` に brief、plan、レンズ 2 本、裁定、author 報告、レビュー 2 本、fix、焦点再レビュー、移設元 SKILL.md の
複製、docs のみ時点の checker 出力。`originals.json` に原文 bytes・sha256・行末空白の正規化行数 (可逆。`s1-brief.md` は末尾の空行 1 行も除いた)。
`mutation-spec-{probe,final}.json` / `mutation-ledger-{probe,final}.json` は harness の入力と出力そのまま。
