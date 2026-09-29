# 段 4 裁定 — prune-tools-batch1 (2026-09-29 JST)

入力: brief.md、s2/plan.md (Codex plan、check_codex_output rc=0)。段 3 は省略 (下記)。

## 段 2 所見の裁定

| 所見 | 判定 | 親の裏取り |
|---|---|---|
| (P2) 予算承認 preflight の専用 test は live freeze を検査する | real、採用 → 対ごと残す | `orchestrator/tests/test_s8b_budget_approval_preflight.py` の `test_verify_and_loader_accept_same_canonical_candidate` (L296) と `test_design_asymmetry_loader_uses_caller_holdout_ids` (L415) が `FREEZE._load_budget_approval` (live `orchestrator.campaign.s8b_holdout_freeze`) を直接呼んで assert することを本文で確認。D2179「専用 test に live code の性質を検査する関数が含まれる場合は module ごと残す」 |
| (P4) 台帳が走査器の再実行を手順として要求する | real、採用 → 走査器・test・台帳とも残す | `docs/test-environment-coincidence-ledger.md` の「再走査は走査器を当て直して行う」「走査述語は commit 済みのコードになった。`tools/scan_env_coincidence.py` が P1 / P2 を AST で実装する」を本文で確認。D1989 の現役の拘束的 consumer (現行 docs が対象を手順として要求) |
| (P1) 署名対は残す | 支持 | D1399 が実装を名指し、D1829 は主体の実効層の保留で部品撤去の指定ではない (逐語確認済み) |
| (P3) 環境契約 activation 発行器は残す | 支持 | test 93 関数のうち 525〜2492 行が live `env_contract_activation` 等を検査 (段 2 の関数名列挙、test 本体行数 3175 は親実測) |
| (P5) A-1 balanced sizing 対は残す | 支持 | 凍結事前登録 README:290-291 が現行 sha256 を名指し (親の hash 全文検索で 3 hit、すべてこの事前登録 dir) |
| (P6) strip script は削除 | 支持、採用 | 専用 test 無し、名前参照は runbook の `unknown` 表 1 行と自身のみ。hooks・.claude・.codex・registry に 0 件。2026-07-17 commit `1c5a72d68` で実行済み |
| 付随: 前提表 A6 の `BUDGET_APPROVAL_SHA256` を `None` とする記述が古い | real だが scope 外 | 修正は docs の現状更新で削除 wave の目的外。一次資料に記録のみ |

## 段 3 の省略

DW-C00 の再評価: 変更面は「専用 test を持たない script 1 本の削除 + runbook 1 行の置換」に確定し、正しさ防壁・受理集合・設計択一の
いずれにも触れない (削除する script を実行・検査する test は 0 件で、受入の検査集合は変わらない)。軽量版の省略条件に当たるので
段 3 を省く。残す 5 候補は「残す」側の判断なので、誤っても現状が保たれる。

## plan v2 (確定)

1. 段 5 実装子 (Codex author、1 単位): `tools/strip_claude_session_trailers.sh` を削除する (所有 = この 1 path だけ)。
2. 親 (docs): `docs/pegasus-runbook.md` の `unknown` 表から当該行を削り、表の直後に削除済みの注記 1 文を置く。
   docs/README.md の地図・docs/archive/README.md の墓標・orchestrator/tests/README.md・nodeid 台帳は変更なし (docs 削除 0 件、test 削除 0 件)。
3. commit 題 `prune(tools): remove completed session-trailer rewrite script`、本文に path・理由・関連 D を 1 行ずつ。
4. 一次資料 `output/insights/2026-09-29/prune-tools-batch1/README.md` に 6 候補の判定と残した理由、受理集合への影響を書く。
5. spool worklog fragment 1 本。

## 変異の事前登録

- kill 型の変異: **0 件**。削除する script を読む test・gate が repo に存在せず、DW-M01 の「同じ入力を拒否する単一理由の層」を
  置けない (F28 の再照準先も無い)。実装面差分はゼロではないので「免除」ではなく「登録可能な実効 gate が無い」と記録する。
- 診断 probe D1 (kill に数えない): 「script を削除し runbook 行を残したまま」の木で `python3 tools/check_docs.py` を走らせ、
  削除済み path への dangling 参照を拾う gate が在るかを観測する。期待 = 生存 (段 2 の静的判定: check_docs の `unknown` 表検査は
  `tools/pegasus/` の path だけを照合)。結果は一次資料へ記録する。

## 受入

`tools/dev_wave_wait.py acceptance` による全走 1 回。変更後の tip で行う。
