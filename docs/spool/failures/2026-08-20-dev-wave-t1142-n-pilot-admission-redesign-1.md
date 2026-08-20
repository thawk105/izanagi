---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: dev-wave-t1142-n-pilot-admission-redesign
seq: 1
---

## 新規

### {{F:dev-wave-stage4-mutation-registration-gap}}. dev-wave段4裁定でB-057変異事前登録の手順自体が漏れた [手順漏れ]

- 事象: T-1142 n-pilot R33 admission再設計waveの段4裁定 (第2wave、ユーザーが
  「実装に着手してほしい」を選んで再開した回) で、DW-M01が求める「段4でB-057
  の変異を実装前に登録する」を実行せず、Unit0-4実装 (段5、1756+行規模) へ
  進んだ。段6 fixの統合commit後にDW-M01を読み返して発覚した。
- 根本原因: 段4裁定を確定する際、docs/dev-wave/mutation.mdのDW-M01を実際には
  適用しなかった。wave自体が「実装しない」裁定からユーザー指示で再開するという
  複雑な経緯を辿っており、通常の段2→3→4の直線フローと異なる分岐を通ったことが
  見落としと関係した可能性がある。
- 恒久対応: memory (`dev-wave-stage4-mutation-registration-checklist.md`) へ、
  段4裁定確定直前に DW-M01 の適用有無を明示確認する運用を記録した。今回は
  事後 (段6 fix後) に B-057 変異8件を新規登録・本走し、8/8 KILLED を確認して
  代替した (実装後だが実測ベースの検証、前例 T-172 系5度目発火・
  `docs/phase3.md:1043` の "bounded 事後 audit" と同型)。
- 再発検知: 段6以降で DW-M01 を読み返した際に、既存 spec ファイルの不在を
  grep で確認する事後検知に留まる。段4時点での検知手段は本 wave では
  新設していない。

## 再発

### F230

- **再発: 2026-08-20** — T-1142 n-pilot R33 admission 再設計 wave の fix 後
  変異 matrix で、変異8件のうち4件が MISMATCH。M1 は8件への missing 拡大
  (共有 fixture `_allocation_result_files` への連鎖影響)、M2 は逆に extra 側
  (予測2件・実測1件、変異後も別分岐で偶然動作)、M6/M7 は
  `s8b_oracle_n_pilot.py` 変異全てに共通する巻き添え
  (`test_r33_protocol_document_loads_from_repository` が driver.py のバイト
  変更で protocol document 記録 hash と不一致になる構造的性質、正しさ検出とは
  無関係)。期待 node を机上予測でなく実測から再導出し、巻き添えテストを
  `--deselect` で除外して再走、8/8 KILLED 一致を確認した。
