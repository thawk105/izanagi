# 段 1 brief — prune-tools-batch1 (speedup md_3)

- wave: dev-wave-prune-tools-batch1、worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-prune-tools-batch1`、基準 = local main `4ac4f8dfd517b668130bede7811abb07c25e63a8` (開始 gate rc=0)
- 研究前進: 論文の主張・図表は動かさない。ユーザー依頼 (2026-09-29 逐語「不要なテスト、ツール、ファイルは削除して記録しておき、後でgit参照しやすいように」) に基づく整理。速度効果は小さい見込み (D1990 の結論が再び当てはまる)。完了判定 = 各候補の削除/残置が D1989・D2179 の現物照合つきで一次資料に書かれ、削除分が `prune(tools)` commit と墓標で git から引けること
- 確定済みユーザー裁定・依頼: 依頼文 `task-md_3.txt`、共通指示 `task-common.txt` (同 dir)。関連裁定の逐語は `rulings-verbatim.md` (D1174, D1385, D1398, D1399, D1829, D1989, D2179)
- 不変条件: (1) 削除は D1989 の「現役の拘束的 consumer 無し」と D2179 の 3 連言 + 専用 test の専用性が**現物で確認できた対象だけ**。1 つでも未確認なら残す (2) 凍結 bytes・hash・path に束縛された文書・成果物は動かさない (規律 7) (3) 残る test の期待値を変えない、被覆を移す test 分割をしない (D2179 却下欄) (4) 所要台帳 `orchestrator/tests/acceptance_duration_ledger.json`・`tools/check_docs.py`・`hooks/`・`orchestrator/tests/test_hooks.py`・`orchestrator/tests/test_check_docs.py` に触れない (5) check_docs が削除 path を pin して赤になる候補は残す
- 成果物: `prune(tools): ...` commit (本文に path・理由・関連 D を 1 行ずつ)、`docs/archive/README.md` 墓標 (docs 削除時)、一次資料 `output/insights/2026-09-29/prune-tools-batch1/README.md`、spool fragment (worklog)

## 親の実測 (2026-09-29 22:4x-23:1x JST、main 4ac4f8d / 8fe87f8 の tracked tree)

| 候補 | 名前参照 (insights・archive・worklog 以外) | sha256/blob の束縛 | 権威 D |
|---|---|---|---|
| tools/acceptance_issuer_reference.py + tools/acceptance_receipt_signature.py + orchestrator/tests/test_external_acceptance_signing.py (22 test) | 互いと test のみ。duration ledger に test 名 | なし | D1399 が「署名検証 library と reference issuer を実装」と名指し。D1829 (ユーザー裁定) が外部署名主体を「当面実装しない、第二 OS principal が使えたら再訪」。部品の撤去を命じた裁定は未発見 |
| tools/s8b_budget_approval_preflight.py + orchestrator/tests/test_s8b_budget_approval_preflight.py (17 test、`s8b_holdout_freeze` を import し L289/L562 で `BUDGET_APPROVAL_SHA256` 行を生成) + docs/s8b-budget-approval-user-turn.md | orchestrator/tests/README.md、duration ledger、decisions D1385 (歴史) | なし | D1174「発行せず検証だけ機械化」、D1385、D1398。`s8b_holdout_freeze.py:53` の `BUDGET_APPROVAL_SHA256` は設定済み (= 承認は発行済み) |
| tools/issue_env_contract_activation.py (+ test_env_contract_activation 93 test / 3175 行) | docs/calibration-freeze-authority-bundle-design.md、docs/env-contract-activation-prerequisites.md、docs/failures.md。`env_contract_activation` は live module 群 (campaign/env_contract.py 他) と共有名 | なし | decisions に tool 名 0 件 |
| tools/scan_env_coincidence.py + orchestrator/tests/test_scan_env_coincidence.py (8 test) + docs/test-environment-coincidence-ledger.md | ledger doc (自称「分類と処置の正本」)、docs/README.md:113、docs/failures.md (F641 周辺 2 か所) | なし | decisions 0 件 |
| tools/size_paper_story_a1_balanced.py + tools/verify_paper_story_a1_balanced_sizing.py + orchestrator/tests/test_paper_story_a1_balanced_sizing.py | test のみ | **凍結事前登録 `output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md:290-291` が両 tool の現行 sha256 を名指し**。live `orchestrator/campaign/paper_story_a1_paired.py:223` と `.v3-sized.json` がその prereg を参照 | D2179 条件 3 (凍結事前登録が実装として名指し) |
| tools/strip_claude_session_trailers.sh | docs/pegasus-runbook.md:678 (`unknown` 経路表の 1 行) | なし | decisions 0 件。2026-07-17 に実行済み (commit 1c5a72d68) |

- nodeid 台帳: 候補 test 名は README と duration ledger 以外の tracked file (conftest の REAL_REPO_SERIAL_NODES 等) に 0 件 (名前 git grep、実行 import 経由・glob は未確認)
- 模擬/実の差: 上表は静的 git grep のみ。import graph・glob・動的ロード・admission registry・check_docs の pin は未実測

## 親の provisional 裁定 (攻撃対象)

- (P1) 署名対は**残す** — D1399 が現行機構の部品として名指しし、D1829 は再訪条件つきの保留であって撤去ではない
- (P2) 予算承認 preflight 対 + doc は、専用 test が live code (`s8b_holdout_freeze`) の性質を検査する関数を含まず、承認の再発行予定 (g2 等) が無いことが確認できれば**削除**、1 つでも崩れれば残す
- (P3) `issue_env_contract_activation` は**残す** — test が専用でない見込み (93 test、live module を検査)
- (P4) 走査器 + test は削除候補、ledger doc は F641 の処置の正本として**残す** (doc が走査器を再実行手順として要求していれば走査器も残す)
- (P5) A-1 balanced sizing 対は**残す** — 凍結事前登録が sha256 で名指し
- (P6) strip script は**削除**し、runbook の行を「削除済み、`git log --grep='^prune'` で引ける」へ置き換える (check_docs が表を JSON と照合していないことを確認できた場合だけ)

## 分割方針

削除だけなので実装子 1 本 (所有 = 削除対象 file と orchestrator/tests/README.md の該当行)。docs 側 (runbook 行・docs/README.md 地図・墓標・一次資料・fragment) は親が書く。
受入: `tools/dev_wave_wait.py acceptance` の全走 (login 所在は worklog に従う)。削除 wave なので変異 matrix の対象は段 4 で決める (実装面差分がゼロでないため免除しない)。
