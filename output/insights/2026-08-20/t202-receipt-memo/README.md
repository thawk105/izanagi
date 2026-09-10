# [T-202] real_repo_receipt_memo の2欠陥修正 — 一次資料索引

- `brief.md`: 段1 brief 〜 段4 親裁定 (plan v2) の全文 (handoff から確定した範囲を転記)。
- `mutation-spec.json`: 段6 変異matrix の最終 registered spec (baseline PASSED・
  M1/M2/M4 とも matches_expectation=true、SURVIVED/MISMATCH 0)。probe
  (`expected_status=SURVIVED`) で観測した failed_nodes と本走の failed_nodes は完全一致。

## 概要

commit `2fc7655e` ([T-202] real_repo_receipt_memo の2欠陥を閉じる) が正本。本ディレクトリは
段1-6 の設計根拠・敵対相談/レビューの所見・変異matrix の一次資料を保全する。

- 欠陥(a): `--testrunuid` replay で実 receipt payer が0回になる → controller nonce
  (`pytest_configure_node`/`workerinput` 経由 xdist 伝播) を cache path に混ぜて解消。
- 欠陥(b): `pickle.loads` が `isinstance` 判定より先に実行される → pickle 除去、
  closed-schema JSON (`object_pairs_hook`/`parse_constant` 必須) へ置換。
- 段2 plan の worker nonce 配線 file:line 主張 (誤り) を段3 敵対相談レンズAが検出、
  段4 で訂正。段6 敵対レビューが `import pytest` 漏れ (焦点走で実測) と、変異 M2/M4 の
  positive control 単一理由性問題を検出、fix で解消。M3 (`parse_constant`除去) は
  `_is_json_tree` の finite 検査と常に冗長になり独立登録不能と判定 (defense-in-depth
  として維持)。
- 設計判断: {{D:receipt-memo-nonce-json}} (`docs/spool/decisions/` fragment、fold後は
  `docs/decisions.md` の D 番号を参照)。

段2/3/6 の codex 生出力 (s2-plan.md, s3-lensA/B-v2.md, s6-reviewA/B.md, s6-fix.md) は
job tmp (`/home/SFC/tanab/.claude/jobs/bcb81cc4/tmp/dev-wave-t202-receipt-memo/logs/`) に
あり、セッション終了後は非保証。要点は `brief.md` と commit message に転記済み。
