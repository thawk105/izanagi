---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-13
wave: dev-wave-t2515-t2534-backoff-withdraw
seq: 1
title: [T-2534] 供給されていないBACKOFF_FIXED指定を取り下げ、rr95のaccepted較正を得た
---

## 本文

- D1936 項 6 に従い、認定較正経路から `BACKOFF_FIXED=-1` の configure argv と専用条件関門を
  同時に取り下げた。gate だけを消して宣言を残す形にはしていない。
  独立表 (D1863) の期待値、shell を parse する 2 つの helper、README を整合させた。
- 着手前の実測で裁定の前提を確かめた。現行 CCBench pin 511c9538 に `BACKOFF_FIXED` は 0 件。
  registered calibration は 3 件とも rr50 で rr95 / rr5 は 0 件。rratio 許可集合は既に
  `{5,20,50,80,95}` で追加不要。`SPACES['silo'].axes` に当該軸は無い。
- **親 brief の「取得を止めている唯一の原因」は言い過ぎだった。** 段 3 のレンズ 1 が
  「判断不能」と反証し、実測でそのとおりになった。撤去後も build・環境検査・測定品質判定が残る。
  記録では「当時の拒否理由 2 件はどちらもこの宣言に由来する」までに限定した。
- **親の暫定裁定 (P1) も半分外れていた。** 既存の共通検査が捕まえるのは
  「gate だけ消して define を残す」向きだけで、逆向きは捕まえない。裁定が禁じた向きは
  機械で守られているが、非対称は責務の外である。新しい gate は足さず、現物レビューと変異で
  整合を確かめる方針へ限定した。
- 段 3 が見つけた最も重い取り残しは、削除する関門の**中身の 1 行**を別 file が逐語 pin して
  いたもので、識別子検索には掛からなかった。段 5 で当該 assert 1 行だけを削り、
  包含 test の残りに歯があることを変異 M5 で裏取りした。
- 較正 2 条件を同時投入し、**rr95 は accepted** (registered へ自動登録)、
  **rr5 は cache floor による `selection-invalid` で rejected**。後者は絶対規律 4 側の
  正しい拒否であり、`l3_multiple` を後から上げて通すことはしていない。裁定へ返す。
- 変異は probe を全件 SURVIVED 期待で先に流して観測 node を集め、本走の期待 node を機械生成した。
  本走は baseline 緑、6/6 KILLED、期待 node 完全一致。M1 は過剰決定なので冗長 gate と明記し、
  M6 は受理集合を変えないので diagnostic sensitivity pin として別枠に置いた。
- 実装・相談・レビュー・変異・生証拠の所在 =
  `output/insights/2026-09-13/t2515-t2534-backoff-withdraw/README.md`。
- 段 6 の敵対レビュー 2 本は実装 must-fix 0 件。残る 1 件は親担当の所要時間台帳更新だった。
- 非帰属の赤を 1 件観測した。床値 checkpoint の実時間上限 test で、`os.write` を 5 秒眠らせて
  割り込みを見るもの。差分から到達できない面で、単独再走では再現しなかった。
- `tools/run_tests.py` が判定を表示した後の後処理で停止する事象を 2 回観測した。
  pytest の判定自体は出ており、この wave の結果には影響していない。
- 段 8 の自己改善候補は 2 件で、どちらも既存台帳に同型があるため新しい F も docs 編集も作らない。
  (i) `mutation_worktree.py` の共有木事後検査が並行 wave の churn で rc=125 になり、
  harness 直接経路へ落とした。型は F383 と同じ。
  (ii) 変異 harness の preflight が `output/` 配下の untracked も拒否するため、
  較正の実測成果物を先に commit してから走らせた。これも既存 F と同型。
  dev-wave docs は byte 予算が満杯で exact pin が脆いので、本 wave では編集しない。

## 次の一手差分

### 完了

- [T-2534] 供給されていない BACKOFF_FIXED=-1 の指定・configure argv・genome の宣言・
  その専用条件要求を取り下げ、独立表と該当期待値と README を整合させた。
  remaining: none
  base: e61375eee29e9f1d8aec053fa7dee538ccf44b16e43137abc772f6986d990f0d

### 更新

- [T-2515] **P1・rr5 のみ残り・ユーザー裁定待ち**: rr95 の accepted calibration は取得済み
  (registered/calibration-5c836a22eff9ab40.json)。rr5 は cache floor による
  `selection-invalid` で拒否されたままで、取得には {{T:calibration-cache-floor-writeheavy}}
  の裁定が要る。迂回して accepted を作らない。
  base: 50a6c2ae055fad5710569c92cce854af3c90c1744ca30b12f43db90aee28ec7b

### 新規

- {{T:calibration-cache-floor-writeheavy}} **P1・ユーザー裁定待ち**: write-heavy (rr5) では
  D15 の下限基準が選ぶ最小 N と calibrator の cache floor 0.50% が両立しない。実測は
  N=1,000,000 で LLC miss 0.364% (拒否)、N=2,000,000 で 1.392%。選択規則を変えるのは
  正しさゲートの受理集合の変更なので、結果を見た後に AI が決めない。案と実測値を添えて諮る。
