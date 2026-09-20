## 段 1 brief (07:28 JST)

- 研究前進: 論文の limitations 節・results の執筆用作業表 (claim-evidence matrix) を、2026-09-19 版以後に着地した測定
  (A-2 observed-positive / A-6 reject / T-1998 accepted / A-1 attempt-0001 descriptive / B-10 cohort 1・2 / 採用候補の検証相 /
  B-7 fixed5 材料 / official 床値案 / mocc 観測 4 件) まで一次資料で引き直し、限定レジストリを L29〜 で拡張する。
  完了判定 = `docs/paper-story/claim-evidence/2026-09-20.md` が 3 表 + 限定レジストリ + limitations 統制稿を持ち、段 6 read-only レビュー通過、受入緑、land。
- scope: docs-only。新規 file 1 (`claim-evidence/2026-09-20.md`)、README の claim-evidence 系列表へ 1 行、spool fragment (worklog)、insight README。
  scope 外 = 新規計測・gate・台帳追加・版の履歴表・既存版/前稿/results/figures の変更・英語化。
- 確定済み裁定: append-only (2026-08-26 稿不変)、入力 5 節 = 2026-09-19 版 §3/§6/§7/§8/§9 (blob bde3c0c66)、出所は一次資料だけ、
  版の履歴表に登録しない (README 規則)、段 6 独立 read-only レビュー 1 本 (D2148 項 11)、README は受入 owned-path に入れない。
  未着地物 (fig10・cohort 2 後継図・T-2792 A-1 attempt-0002 経路・T-2795 K2 同 job stock 対照・T-2797 B-5 本走認可) は裁定待ち/未完として書き、完成扱いしない。
- 不変条件: 規律 2 (verifier 判定・certified 記録を上げも下げもしない、規律 7)、規律 1 (検証相の走行から性能値を引かない)、
  版の文を数値の出所にしない、(c) 欄は 6 値の閉語彙、(d) は ✗ 禁止推論付き、(e) は 外せる/後続別主張 の 2 行。
- 実測した前提: ストーリー 09-20 版は main に無い (README 最新 = 09-19)。claim-evidence / README に byte pin する test は無し (grep 0 件)。
  fig10 / fig8b は figures/ に無い。T-2792/2795/2797 は archive 1687/1691/1692 で「ユーザー裁定待ち」起票、裁定 D は無い。裁定 inbox に本件の新裁定なし。
  DW-O08/O09/O10/O11/O13 は不成立 (freeze/oracle/proof chain/削除/gate 新設に触れない)。
- (P1) 前稿 C12 (単回 4 cell) は A-2 attempt で上位互換の観測が取れたため行として残さず C2/C18 へ吸収し、対応表で明示する。
  (P2) 検証相 (2026-09-20) は B-8 の要件本文に対する仕分けを本稿で行わず「次版で仕分ける」を継承し、L で限定を採番する。
  (P3) results/ 稿は `[導出索引]`、certification.json / result.json / WAL / prereg が `[権威 bytes]`。
- 成果物の形: 前稿と同じ §1〜§6 + §7 前稿との行対応。ID は前稿 C1〜C17 を継承し新規は C18〜。L は L01〜L28 継承 + L29〜。
- 分割方針: 軽量版 (DW-C00)。段 2・3 省略、段 5 = 親の docs 編集 (実装面ゼロ、変異 matrix 免除 DW-S04)、段 6 = Codex read-only レビュー 1 本 + 親 fix + 必要なら焦点再レビュー 1 本、受入全走は免除しない。
- 受入・実測環境: Pegasus login (docs 検査) + 受入は `tools/dev_wave_wait.py acceptance` (計算ノード dispatch)。計測ゼロ。

## 段 4 裁定 (段 2・3 省略につき brief をプラン v2 とする)
- (P1)〜(P3) は親の provisional のまま採用し、段 6 レビューの攻撃対象に明示する。変異登録: 実装面差分ゼロにつき免除 (DW-S04)。

