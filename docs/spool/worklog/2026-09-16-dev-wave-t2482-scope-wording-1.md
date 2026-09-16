---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2482-scope-wording
seq: 1
title: [T-2482] campaign verifier epoch の保証文言を現物の被覆 (収載 63 / 発見集合 162 / 未収載 99) へ合わせた — 63 本目は import 先でなく subprocess 委譲先で、旧文言の除外欄はそれと矛盾していた (コード + docs、branch worktree-dev-wave-t2482-scope-wording、変異 9 本 = drift 対照 1 SURVIVED + 診断感度 pin 8 KILLED、うち 1 本は erratum の補走)
---

## 本文

- 一次資料は `output/insights/2026-09-16/t2482-scope-wording/`。閉包寸法の実測 JSON 3 本、
  変異 spec と台帳 (probe / final)、子の逐語 7 本 (plan・敵対 2・実装・レビュー 2・fix・焦点)、
  親 brief・裁定・追補を置いた。設計判断は {{D:scope-wording-dated-snapshot}}。
- **起票時の「現行 63 / 140 / 77」は着手時点で既に古かった。** T-2344 の probe 原本
  (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-reachability/probe_closure_v2.py`、
  repo の逐語 md のコード部と sha256 一致) を書き直さずに実行し、着手時 main `e667c8c13` と
  取り込み後の base `a1b40608c` の両方で 収載 63 / 発見 162 / 未収載 99 を得た (発見集合は両 commit で
  完全一致)。正例対照 `2143a49c0` は T-2344 の記録 63 / 140 / 77 を再現した。収載が不変でも
  発見集合は 1 週間で 22 module 増えており、食い違いの源は収載の段階実装だけではない。
- **親 brief の (P3) は撤回した。** 63 本目 `verify_fanout_worker.py` を静的 import する module は
  発見集合に 0 本で、`pipeline.py` が ssh 経由で起動する subprocess 委譲先を T-2429 が明示収載した
  ものだった (段 2 投入後の親の追加実測)。旧文言の「subprocess を含む非 import 委譲は本 map の外」は
  この 1 本について事実と食い違っていた。段 3 の 2 レンズは独立に同じ must-fix を出した。
- **親 brief の実測の一般化を子が 2 件訂正した。** (a) 「E1 値不変」は記録済み map から再導出する
  値に限る (`artifact_admission.py` 自身が収載 path なので新規 lock の E1 は変わる)。
  (b) 「受理に効く経路は scope の直接照合だけ」は誤りで、同 file 全 bytes の sha256 が admission
  receipt の validator と B-4 projection hash に入る。いずれも D170 (d) と B-4 事前登録本文が既に
  限界として記す既知の性質で、本 wave 固有ではない (記録のみ、コード変更なし)。
- 段 6 レビュー A は所見ゼロ、B は should-fix 1 件 (除外句の「除く」の係り先が一意でない) を出し
  採用した。fix 子 1 本で例外を括弧書きへ移し、親が逐語一致を独立検算 (6/6) した。
- **変異は kill でなく診断感度 pin として記録した (DW-M03)。** 差分は説明文字列だけで受理集合を
  変えない。comment だけを変える対照 M0 が SURVIVED・赤 0 で、この焦点集合 (3 file) には
  F358 の drift 核が無いことと harness の SURVIVED 検出が生きていることを同時に示した。
  M1〜M5 (production の数値・句の改変) は各 4 node、M6 (test literal) は 1 node、M7 (test literal) は
  3 node で、静的予測と完全一致。赤の理由は独立 literal との不一致だけ。
- 受入全走は本記録 commit を含む最終 tip へ land 前に 1 回投入し、受領証を
  `dev-wave-jobs/dev-wave-t2482-scope-wording/` に残す。件数は本文へ書かない
  (書けば tip が変わり取り直しになる)。
- 工数: codex 子 8 本 (plan 1・consult 2・author 1・review 2・fix 1・focus 1、全て gpt-6-astra /
  medium)、計算ノード job = 焦点走 1 + 変異 probe 9 + final 9 + 補走 2。

## 次の一手差分

### 完了

- [T-2482] 2 定数を現物の被覆へ合わせ、test の独立 literal 2 か所を追随させた。
  remaining: none
  base: 7b719ad82d9e00dd66dc48f800321d0f72ab44743e993c7fbaf00685ecab428b
