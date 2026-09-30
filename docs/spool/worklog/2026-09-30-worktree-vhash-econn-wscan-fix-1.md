---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: worktree-vhash-econn-wscan-fix
seq: 1
title: [T-2952] VHash md_39: 構成 E の書き込み検査の走査中の回収は試作では GC flag の静止条件が塞ぐ (実機の round 計数と一致)。一般の E 向けに公開値の上限 (候補 b) の patch・壊し正例・計器・起動器を置いた。壊し正例は発火せず修理の効果は判定不能、skew 0 で U0 の改善の約 7 割を失う (branch worktree-vhash-econn-wscan-fix)
---

## 本文

- 依頼: `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_39.txt` と `common.txt`。一次資料 `output/insights/2026-09-30/vhash-econn-wscan-fix/README.md`、設計判断 {{D:vhash-e-wscan-cap}}。
- ユーザー指示 (依頼元 manager: vhash と land 調整役 manager: parallel land の中継、2026-09-30 19:5x・20:0x JST): 計算 job は 1 本 5 分目安に分けて多数を並行で投げる、処置とノードを 1 対 1 にしない、1 ノード 1 job・$TMPDIR、2 node 時間超は land 調整役に相談。本 wave は build を 1 変種 1 job、run を shard ごと (各 shard に処置を混ぜる)、trace を cell × 処置の 4 job に分け、計算 job 15 本・各 Elapse 20〜68 秒・合計約 0.2 node 時間 (相談不要)。
- 依頼の成果物「ledger の自分の entry」は作らなかった (`patches/ledger.json` は silo_ladder_rung1 専用、D2288)。食い違いは一次資料 §10。
- 段 1 の親の新事実 (GC flag の静止条件) を段 2 plan・段 3 相談 2 本とも支持した。段 3 の所見 14 件はほぼ real (修理の論証の CAS-max の件だけ refuted)。
- 段 5: Codex 実装子 2 本 (patch / 起動器)。統合時に親が 3 件 (計器が PENDING 待ちの間も mutex を握る deadlock、計数の load が性能 build に残る件、spawn site の在庫の登録漏れ) を見つけ Codex の fix へ。段 6 レビュー 2 本の must-fix 5 件・should 4 件を全件 real として Codex の fix、焦点再レビュー (NO-GO: shard 番号の検証の不足、trace 分割は差分外で未確認) の should を Codex の fix で閉じ、trace 分割は実測 (4 part の結果) で閉じた。
- 変異: 事前登録の MB1 (正例判定から到達の要求を外す) は、段 6 の fix で判定が同じ走査の対 (`detached_reach_both`) を使うようになり、冗長な層として生存した (login 自走 probe)。erratum として残し、両層を同時に外す MB1b に照準し直した。
- 事前登録の外の探索走 (遅延 10 ms の K12) は判定に使わず、一次資料 §5.2 に別記した。

## 次の一手差分

### 完了

- [T-2952] 候補 (b) を overlay patch として試作に入れ、再現走・修理前後の境界の遅れと生存版数・巡回検査を記録した (一次資料、{{D:vhash-e-wscan-cap}})。壊し正例の未発火と利得の減りは新規 item へ送った。
  remaining: none
  base: 2e08702628bf2db5576cc349c11ef9b093c97695da4c19df3af6b96c14aa4161

### 新規

- {{T:vhash-e-wscan-reserve}} **P2・新規**: 構成 E の書き込み検査の走査中の回収を、公開値に上限を掛けずに閉じる「予約」型の規則 (前進の確認で書き込み key の見える確定版の rts も t′ へ上げ、観測し直す) を論証・試作し、md_39 の修理 (候補 b、skew 0 で U0 の改善の約 7 割を失う) と同じ条件で境界の遅れと生存版数を比べる。根拠: `output/insights/2026-09-30/vhash-econn-wscan-fix/README.md` §5.3・§7・§8。
- {{T:vhash-e-wscan-witness}} **P3・新規**: md_39 の壊し正例は K1+K2 でも発火しなかった (T の PENDING 版を待つ書き手も GC flag を立てず round が止まると推定)。一般の E (前進しない thread が無い) の §3.2 の列の witness を、小モデル (`tools/vhash_forwarding_model/`) に GC flag の静止と非原子な書き込み走査を入れて取るか、書き手の静止も外す模擬 schedule で取るかを決める。根拠: 同 §5.1・§5.2。
- {{T:vhash-s2-e-variant}} **P2・新規**: S2 (D2332) の E_sp に md_39 の修理版 (`patches/cicada-forwarding-wscan-cap.patch`) を重ねるか、試作の構成の静止の塞ぎを論文の規則として明記して修理なしで走らせるかを、発効の wave が決める (評価計画 §16.2 の「修理版 E の名前」の欄)。修理版は上限を掛けても公開値を上げた回数が 0 ではない (skew 0 で 704 回、skew 0.9 で 505 回。ただし「その時点の Rts を越えた回数」で、D2332 項 3 の「開始時を越えた回数」とは数え方が違う)。根拠: 同 §7。
