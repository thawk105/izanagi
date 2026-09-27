---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-27
wave: dev-wave-t2104-flock-scope
seq: 1
title: [T-2104] campaign の advisory flock を B-4 認可から checkpoint 完了まで広げた (D1346)。base driver と main の B-4 経路が外側で lock を取り、run_campaign へ保持 handle を渡す。旧 driver では新しい負例 7 件すべてで producer が実行中の arm の lock を取れる誤判定を再現し、新 driver で緑 (コード + test、branch dev-wave-t2104-flock-scope)
---

## 本文

- 依頼どおり base driver (`p3_s4_loop.py`) の並行実行契約だけを変えた。sort / trigger / policy driver・tools/pegasus/・producer は触っていない。
  対象を base に限った根拠は B-4 事前登録 §5「対象 driver と軸」= base。受け渡しの設計は {{D:held-campaign-lock-handoff}}。
- 実測: 焦点走 f1 (39 file) 2 failed / 5080 passed → fix 1 巡 (各 1 行) → 再走 f2 1146 passed / 赤 0。
  旧 driver (p3_s4_loop.py だけ ad114fba0 版) で新しい負例 7 件すべてが「DID NOT RAISE CampaignBusy」で赤 = 誤判定の再現。
  変異 harness 本走 10/10 KILLED (drift 核 148 node を対照 M0a/M0b で分離)。drift に隠れる M1/M2/M3/M5 は commit 済み変異の個別走で狙いの負例だけが赤。
  単独走は M1 (fix 後の再走 f2 を変更 test file 2 本 + signature test の file に置き換え)。
- 棄却・見送り: 段 3 の「path 不一致を B-4 消費前に拒否する追加照合」は本番経路で起きない仮想リスク向け gate として不採用。
  sort / trigger の同型の窓と producer の非保証文の陳腐化は insight に記録し起票しない。
- セッション異常: 親が DW-O13 (検証の新設時の入力実在) を段 2 前に読まず、段 4 直前に段 2・3 を無効化して再実行した (codex 3 本分)。
  実装子 worktree の作成が EINTR で 1 回失敗、submodule 初期化が 1 回 runtime-io-failure (いずれも再実行で回復)。
- 工数: codex 11 本 (plan 2・consult 4・author 1・review 2・fix 1・focus 1)、計算ノード job は焦点走 2・旧 driver 確認 1・変異 probe/本走 各 11 run・commit 済み変異 4・受入。
- 詳細: output/insights/2026-09-27/t2104-campaign-flock-scope/README.md

## 次の一手差分

### 完了

- [T-2104] campaign の advisory flock を base driver の B-4 認可・preflight・実行・checkpoint 完了までと main の B-4 事前認可から driver 復帰までへ広げ、誤判定の再現 test と既存の並行実行契約 test を同じ単位で置いた。
  remaining: none
  base: da13d9d00594a73d19e0e9def8e13f44c2c54032d95177e98aaa7c831d2bf5dd
