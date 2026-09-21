---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-t2824-g1-candidate-removal
seq: 1
title: [T-2824] 凍結 v2 g1 の未発効候補文書を削除し、held 真値を削除後の live P3 実測へ追随した — historical reverify は成功、live の policy 拒否は不変 (記録 + テスト、branch worktree-dev-wave-t2824-g1-candidate-removal)
---

## 本文

- ユーザー裁定 D2194 項 5 (択 (a)) の実装手番。削除 commit `58ec3e928` の diff は候補 1 file (`output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`、20,737 bytes、sha256 `7e1114…`、blob `15861416…`) の D だけ。scan 除外・`_active_chain_exempt_exact`・`V2_CANDIDATE_REL` の定数・create-only 拒否・G/A/X・floor_source の bytes・B-10 freeze-tree pin (`92099c87…`、`output/s1-freeze` + `output/s8b-freeze` の固定名 rglob で候補 dir は対象外) はいずれも不変。
- 削除前後の実測 (login、一次資料 `output/insights/2026-09-21/t2824-g1-candidate-removal/README.md` §3): loader は不変 (世代 1、sha `7e1114…`)、**historical `reverify_published_freeze` は `closure-hit-mismatch` (94.2 s) → 成功 (59.7 s)**、live `launch_validate` は `manifest-invalid` / `binary-admission` のまま不変 ([T-2812] 系、本 wave では触らない)、runbook §2 P3 は g1 path が rc=2 / 拒否 2 件・v1 path が rc=2 / 4 件で、**差は走査 hit から候補 path が消えたこと (rr80 / rr20 とも 4→3 件) だけ** (削除前の集合から候補 path を除いた集合が削除後の実測と完全一致)。repo 走査 CLI は rc=1 で hit 3 / 3 (clean scan は設計どおり赤のまま)。
- held 真値 `_ACTIVATED_G1_REFUSALS` を実測へ追随 (`ce84ed8da`、Codex author `gpt-6-astra` / medium、test 1 file +8/−6)。held 6 node は受入全走で走らないため診断焦点走で実走した。**held 解除 env を使った権限根拠は依頼の逐語 (ユーザーの直接指示「held 真値を現在値に更新する」) で、使用範囲は 6 node の診断走と変異走だけ、hold 台帳は不変** (段 6 レビュー A の must-fix への処置、同 README §8)。
- production の受理述語 (コード) は不変で、変わったのは実入力 (repo tree) とその結果の historical 判定である。certified 選択・レポート値・台帳・批准参照・live の受理条件・W-4 / W-5 は不変。historical の成功は live admission の代替ではない。
- 帰結: `generate-v2-candidate` を再実行すれば候補 path は復活し、走査 hit と `closure-hit-mismatch` も復活する (fail-closed の向き。存在拒否が消えたことは生成全体の成功を保証しない)。候補 bytes と来歴は世代文書 (同一 blob) と X2 `4d8fb93b7` の履歴で保持する。削除の根拠は「候補 path の役割が批准済み世代 (D2180) へ移って終了」であり、同 bytes であることではない (D2077 を削除許可として引かない)。
- 段 2・3 は省略 (裁定が択と不変条件を確定済み、実装面は test 定数 1 個)。段 6 は敵対レビュー 2 本 = B が GO / must-fix 0、A が差分 GO・held 実行の権限根拠の記録で NO-GO → 記録で閉じ fix 0。

## 次の一手差分

### 完了

- [T-2824] 候補 file の削除 commit・5 経路の再実測・held 真値の追随・帰結の記録を完了した。
  remaining: none
  base: c172edb9d33a9ff4bd818116f818b4d1fdf37dd3a73a77a624cef77f6e8b7e6e
