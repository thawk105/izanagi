---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-t2632-b4-evidence-carrier
seq: 1
title: [T-2632] B-4 の対応証拠 — base driver に harness 書きの provenance side channel (reports/p3_s4_loop_provenance.json、iteration ごとの 6 field) を足し、prerun caller の lock 読取りを既存 codec 経由にした。参照点の定義は docstring と記録で確定、中断時の保証は「公開できない iteration を checkpoint に確定しない」だけ (コード + テスト + insight、branch worktree-dev-wave-t2632-b4-evidence-carrier、変異 21 件すべて期待どおり)
---

## 本文

- 一次資料 = `output/insights/2026-09-21/t2632-b4-evidence-carrier/README.md`。設計判断は {{D:b4-base-provenance-carrier}}。
- **着手条件の待ち:** [T-2795] と [T-2830] の land を 08:20〜17:34 JST 待った (land はそれぞれ 13:35 `d99c556df`、17:33 `5f48a298a`、local main の ref で検算)。
  17:34 に `5f48a298a` から fresh worktree を作った。
- **Codex の利用上限で中断:** 段 2 の plan 子が 17:46 に 9 秒で `You've hit your usage limit` (14:33 以降の全 wave の codex 9 件が同じ)。D582 に従い通知して停止し、
  ユーザーの「codex今なら使えると思う」で 20:1x に再開 (local main `36fb14a3d` へ ff-only、取り込みは docs のみ)。
- **依頼文と裁定の食い違い:** 依頼は先例を `_write_source_preimage_artifact` と名指すが、裁定の `reports/<driver>_provenance.json` の先例は
  `_append_provenance_entry` 系。裁定優先 (F31) で、file の意味は後者、書き込みの堅さは前者に合わせた。段 3 の過剰・削除レンズが妥当と判定。
- **実装 (Codex author 2 本 + fix 4 巡):** side channel (`ec6459863`)、caller (`ec6459863`)、段 6 must-fix (`eee7e4ba3`: 非 canonical proposal は hash=null で続行、
  docstring 2 件の限定、新設 test の fixture、launcher positive test の stub 出力の実物化)、test のみの fix 3 巡 (`f5049bf6d` / `3bfbecfca` / `92f501c28`)。
  production は 1 巡目の fix 以降変えていない。本番の attempt 検査は緩めていない。
- **親の誤診断と訂正:** 焦点走 f2 の赤 1 件 (duplicate の attempt 選択 test) を「採用 commit の後の abort」と誤診断し fix を 1 巡空費した。
  `_resolve_duplicate` は拒否理由を握りつぶすので、親の読み取り probe (job dir、repo に入れない) で理由 (`anomalies` 欠落、次に受領証の `tags` 不一致) を特定し、
  修正案を probe で確かめてから fix させた。段 6 裁定 §4.1・§4.2 に訂正を追記で残した。
- **検査:** 焦点走 5 本 (f1 33 file 12 failed / 4689 passed → f2 同 1 failed / 4701 passed / 15 skipped (skip は全件既存理由) → f5 test_p3_s4_loop.py 655 passed)。
  全史 provenance 監査は `92f501c28` 後 12,447 件で新規違反なし。
- **変異 (21 件、final は全件期待どおり):** `p3_s4_loop.py` は contract loader closure に入り、等価変異 E1 の注入だけで 150 node が drift で落ちると実測した。
  drift を受ける test でしか検出できない変異 (S1・S2・S10〜S15) は、変異を独立 clone の commit に焼く自作 harness (段 6 裁定 §5 で走行前に登録) で KILLED 8/8。
  drift を受けない test で検出する S3〜S9 は注入で KILLED 7/7、E1 は SURVIVED (等価対照)。caller の C1〜C5 は注入で KILLED 5/5。
  焦点再レビューが指摘した「S13・S8 の注入は入口停止を外して drift に届く」は割り振りの訂正 (S13 を commit 群へ、S8 は loader の直接 test だけ) で閉じた。
- **scope 外 (起票しない):** base provenance の admission 検査、中断後に B-4 認可を再利用可能にする変更、side channel の `reference` 欄、caller に side channel を読ませること、
  sort / trigger への展開。caller の不足報告は赤候補 1 件につき 12 件のまま (適格行はまだ作れない)。bootstrap 集合は定義していない (D2120 項 5 (2))。
- **工数:** Codex 子 13 本 (plan 2 (うち上限で即死 1)・consult 2・author 2・review 2・fix 4・focus 1、model call 計 146)、焦点走 5 本、変異 dispatch
  (drift probe 1・注入 probe 2・注入 final 2・commit 群 probe 2・final 1)。
- B-4 本走・床値 w2 は投入していない (計算ノードへ投げたのはテスト job だけ)。受入全走は本記録を含む tip に対して land の前に投入する。

## 次の一手差分

### 完了

- [T-2632] B-4 の対応証拠 4 項 (D2194 項 3) を実装・記録した — base driver の harness 書き side channel、参照点の定義の確定 (docstring と {{D:b4-base-provenance-carrier}})、
  新規 base campaign 起動前の発効 (本 land)、prerun caller の codec 経由化。変異 21 件は期待どおり。適格行の生成・bootstrap 集合・B-4 本走は本項の外。
  remaining: none
  base: d3dd431f127f7f63cd61110b0dba043c33c65fd9cd6e0ffe0199ca17f9d385a9
