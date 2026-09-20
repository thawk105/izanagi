# ユーザー裁定 2026-09-20 13:2x — /dev-wave の引数 (逐語)

[T-2724] ユーザー裁定 2026-09-20 13:2x: 凍結 v2 g1 の承認 A → active pointer X は AI が作る (D2120 項 2 (b) の「人間 commit」と D2174 項 4 を supersede)。着手直前の local main から fresh worktree。(1) この委任を decisions fragment (placeholder) に記録し、attestation を「AI-Agent: none 逐語」から「記録済みの委任裁定 + 構造化 AI trailer」へ改めると明記する。(2) Codex author (D95) が orchestrator/campaign/s8b_ratified_freeze.py の _assert_user_commit (approval / pointer / revocation / cancellation の導入 commit 検査) を「非 merge・AI-Agent trailer がちょうど 1 行 (逐語 none または provenance 規約に適合する構造化 trailer)・H ancestry」に改める。G の generation-commit-none 拒否、diff 1 file、X^ == A は不変。orchestrator/tests/test_s8b_ratified_freeze.py に正例 (構造化 trailer の A/X) と負例 (trailer 無し / 2 行 / merge / X^ ≠ A / diff 1 file 超) を足し、変異 matrix (DW-M08) で負例が KILLED であることを示す。(3) 同 author が output/insights/2026-09-18/t2724-freeze-g1-gen/README.md §5 手順 2〜5 の形で approval record (keys 4 つちょうど、approver にユーザー委任と裁定日を書く) を commit A、pointer record を commit X として作る (いずれも非 merge・diff 1 file・構造化 trailer、A と X の間に他 commit を挟まない)。(4) 検証: 同 README §5 手順 6 の批准 loader (JSON 1 行、generation 1、sha 7e1114…)、docs/phase3-8b-restart-runbook.md §2 P1〜P4 (P3 gate-check は active 世代 holdout_freeze.v2.g1.json で受理)、全史 provenance 監査。docs: 同 README §5、runbook W-3、hooks/README.md 150 行付近の「人間 commit」記述を委任後の形へ。scope 外: W-4 / W-5、hook の変更、鍵署名、床値・certification。規律 2 を緩めない。

## 先行する裁定控え (10:2x、`rulings-inbox/2026-09-20-t2724-ax-approval-by-ai.md`) との差

- 10:2x: 「AI が AI-Agent trailer 付きで A/X を commit (approver は AI の識別子)、hooks の Write 拒否は正規経路に限って解除」。
- 13:2x (本引数): hook の変更は scope 外、正規 CLI 無し、trailer は「ちょうど 1 行」、approver は「ユーザー委任と裁定日」、Codex author が README §5 手順 2〜5 の形で書く。
- 13:2x が後の裁定であり本 wave はこれに従う。10:2x の控えを引数にした先行 job 9f2d502a は 13:37 に「譲る・停止・撤去」と返信した。
