# 不要ツールの整理 第 1 束 — 8b 正式系列の部品と一回限りツール (2026-09-29)

- authority: none
- default_effect: `tools/strip_claude_session_trailers.sh` 1 file を削除した (履歴は書き換えない)。他の 5 候補は残す
- 依頼: `verbatim/request-md_3.txt` (並行 wave 共通指示 speedup-2026-09-29 の md_3。ユーザー依頼「不要なテスト、ツール、ファイルは削除して記録しておき、後でgit参照しやすいように」)
- 基準: 判定は local main `4ac4f8dfd517b668130bede7811abb07c25e63a8` の tracked tree。判定の基準は D1989 (参照 4 分類) と D2179 (一回限り・結果凍結済み・現行機構の実装でない の 3 連言、専用 test の専用性)
- 経過: 段 1 brief (`verbatim/s1-brief.md`) → 段 2 Codex plan (`verbatim/s2-plan-codex.md`、read-only・静的) → 段 4 裁定 (`verbatim/s4-ruling.md`)。段 3 は変更面確定後の再評価で省略 (理由は s4-ruling) → 段 5 Codex author (削除) → 段 6 read-only 監査 1 本 (`verbatim/s6-review-codex.md`、GO・must-fix 0、記録上の誤り 2 件を commit 前に修正)

## 1. 結論

- 依頼 md の候補 6 束 (tool・test・doc の計 15 file) のうち、D1989・D2179 を現物で満たしたのは **`tools/strip_claude_session_trailers.sh` の 1 file だけ**だった。
- 残る 5 束は「使われていない」のではなく、現行の裁定・凍結事前登録・現行 docs の手順・live code を検査する test のいずれかに拘束されている (§2)。
- 速度への効果は無い (削除 file を実行・検査する test は 0 件)。整理の効果も 1 file に留まる。md の候補一覧 (調査役の機械集計) は、
  名前参照の件数で「8b 専用」「一回限り」と分類していたが、test の中身・凍結 hash・docs の手順文までは見ていなかった。

## 2. 候補別の判定

| 候補 | 判定 | 拘束 (D1989 分類) | D2179 で崩れた項 |
|---|---|---|---|
| `tools/acceptance_issuer_reference.py`、`tools/acceptance_receipt_signature.py`、`orchestrator/tests/test_external_acceptance_signing.py` | 残す | D1399 が「署名検証 library と repository 内の reference issuer を実装する」と名指し (現役の拘束的 consumer = 有効な決定)。D1829 (ユーザー裁定) は外部署名主体の**実効層**を「当面実装しない、第二の OS principal が使えたら再訪」とした保留で、部品の撤去指定ではない | 一回限りでない・現行機構の実装 |
| `tools/s8b_budget_approval_preflight.py`、`orchestrator/tests/test_s8b_budget_approval_preflight.py`、`docs/s8b-budget-approval-user-turn.md` | 残す | D1174「発行せず検証だけ機械化する」、D1385 が手順書を名指し。手順書が skeleton / verify の CLI 呼出しを手順として持つ | **専用 test が専用でない**: `test_verify_and_loader_accept_same_canonical_candidate` と `test_design_asymmetry_loader_uses_caller_holdout_ids` 他 (段 2 列挙で計 6 関数) が live の `orchestrator.campaign.s8b_holdout_freeze._load_budget_approval` を直接呼んで assert する (親が本文で確認) |
| `tools/issue_env_contract_activation.py` (test: `orchestrator/tests/test_env_contract_activation.py`) | 残す | `docs/calibration-freeze-authority-bundle-design.md` と `docs/env-contract-activation-prerequisites.md` が発行 CLI を手順として指定。test は `spec_from_file_location` で動的ロード | **専用 test が専用でない**: 93 関数・3,175 行のうち前半の大半が live の `env_contract_activation`・`env_contract` 等を検査し、発行器自身の test は後半だけ |
| `tools/scan_env_coincidence.py`、`orchestrator/tests/test_scan_env_coincidence.py`、`docs/test-environment-coincidence-ledger.md` | 残す (3 file とも) | 台帳 (F641 の分類と処置の正本、`docs/README.md` の地図と `docs/failures.md` から引かれる) が「走査述語は commit 済みのコードになった。`tools/scan_env_coincidence.py` が P1 / P2 を AST で実装する」「再走査は走査器を当て直して行う」と手順として要求する | 一回限りでない・現行手順の実装 |
| `tools/size_paper_story_a1_balanced.py`、`tools/verify_paper_story_a1_balanced_sizing.py`、`orchestrator/tests/test_paper_story_a1_balanced_sizing.py` | 残す | 凍結事前登録 `output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md` の tool 表が両 tool の**現行 sha256** を名指しし、同 dir の `sizing-replay-receipt.json` も束縛する (候補 14 file の sha256・blob で tracked 全 file を検索し、hit 3 件はすべてこの dir、`verbatim/candidate-hash-hits.txt`)。live の `orchestrator/campaign/paper_story_a1_paired.py` と `.v3-sized.json` がこの事前登録を参照する | 現行機構の実装でない、が不成立 (凍結事前登録の名指し) |
| `tools/strip_claude_session_trailers.sh` | **削除** | 名前参照は `docs/pegasus-runbook.md` の login `unknown` 経路表 1 行 (実在を要求しない一覧 = 非拘束) と歴史的言及 (archive worklog 2 行、`output/insights/2026-08-09/t139-f37-land-gate/` 3 行) だけ。hooks・`.claude`・`.codex`・`tools/pegasus/` の registry・run_tests の固定表に 0 件。専用 test 無し | 3 連言とも成立: 2026-07-17 に実行済み (commit `1c5a72d68` 「除去の実行」)、結果は履歴の書き換えとして確定、有効な決定・事前登録の名指し無し (decisions 0 件) |

- 依頼 §4 の台帳 (`orchestrator/tests/README.md` の allowlist、`test_plain_runner_coverage`、`REAL_REPO_SERIAL_NODES`、growth / flaky の hold、shard 表) は、
  test を 1 本も削除しないので**変更なし**。docs の削除も 0 件なので `docs/archive/README.md` の墓標と `docs/README.md` の地図も変更なし。
- runbook の表行は削除し、表の直後に「削除済み、`git log --grep='^prune' -- tools/strip_claude_session_trailers.sh` で引ける」を置いた。

## 3. 受理集合への影響

- 削除した script を実行・import・検査する test は repo に 0 件であり、消えた検査性質は無い。受入の検査集合は変わらない。
- 残した 5 束の test を消していれば、署名 receipt の schema 検査、予算承認と freeze loader の受理の一致、環境契約 activation の live 経路、
  P1/P2 走査述語の再現性、A-1 sizing の再現性の検査がそれぞれ失われていた (段 2 の被覆説明、親は予算承認と環境契約の 2 件を本文で確認)。

## 4. 変異と診断 probe

- kill 型の変異は 0 件。削除した script を読む test・gate が repo に無く、DW-M01 の「同じ入力を拒否する単一理由の層」を置けない
  (実装面差分はゼロではないので「免除」ではなく「登録できる実効 gate が無い」)。
- 診断 probe D1 (kill に数えない): script を削除し runbook の表行を**残したまま**の木 (実装子の worktree、commit `199c8a67a`) で
  `python3 tools/check_docs.py` を走らせた → rc=0「違反なし」。事前の期待 (生存) どおりで、docs に残った削除済み tool path を拾う
  lint は無い。したがって本 wave の runbook 置換の正しさは check_docs では担保されず、親の `git grep` (削除後の tracked 参照は
  歴史的言及 5 行だけ) が担う。

## 5. 確かめたこと・確かめていないこと

- 確かめた (親の実測): 候補名の tracked 全文検索 (insights・archive・worklog を別計数)、候補 15 file のうち `orchestrator/tests/test_env_contract_activation.py` を除く 14 file の sha256 / blob id の tracked 全文検索 (除いた 1 本は親が検索対象に入れ漏らした。対の tool は test が専用でないことで残すので、判定には影響しない)、
  D1174・D1385・D1398・D1399・D1829・D1989・D2179 の逐語、予算承認 test 2 関数と台帳の再走査手順の本文、`BUDGET_APPROVAL_SHA256` が設定済みであること。
- 段 2 Codex の静的判定に依拠 (親は再走査していない): 残り 4 関数の live 検査、env_contract_activation test の関数ごとの対象、
  check_docs の `unknown` 表検査が `tools/pegasus/` の path だけを照合すること、`tools/pegasus/` の registry に候補名が無いこと。
- 未確認のまま残した事項は無い (未確認が 1 つでもあれば残す規則で、残した 5 束は拘束が確認できている)。

## 6. 付随して見つけたこと (scope 外、記録のみ)

- `docs/env-contract-activation-prerequisites.md` の前提表 A6 は `BUDGET_APPROVAL_SHA256` が `None` と書く。これは同文書の基準 commit
  `3c1156056b9f7d9606a6af1ebac6f386eea642ac` 時点の観測で、現物 (`orchestrator/campaign/s8b_holdout_freeze.py`) はその後に設定済みになっている (段 2 所見、親が両方の本文で確認)。
  観測時点の記録としては事実のままで、現況を読むときの注意として残す。
- md の候補一覧の「8b official 専用」は調査役の分類語であって、8b 正式系列を退役させるユーザー裁定は見当たらない
  (2026-09-29 の裁定控えは 8c の達成条件を維持し、8b/8c module の切り離しを見送りとしている)。
