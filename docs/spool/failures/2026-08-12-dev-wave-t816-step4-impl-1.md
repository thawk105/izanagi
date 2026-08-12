---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t816-step4-impl
seq: 1
---

## 新規

### {{F:consumer-liveness-misjudged}}. 「生きた consumer が居る」だけで凍結 artifact を現用と裁定し、逆向きに壊す再 pin を通した [手順漏れ]

- 事象: [T-816] 手順 4 の段 4 で、親が `output/s1-freeze/*.json` と
  `output/env/linux-baremetal/calibration/s8a_trigger_freq_t48.json` を「生きた driver が
  verify するので現用」と裁定し、新 gitlink へ機械再 pin させた。段 6 の敵対レビューが実測で覆した。
  `s8b_oracle_driver.py` は `known_axes_freeze.json` の**生バイトが移行 receipt の旧 SHA と
  一致すること**を要求しており、再 pin は 8b oracle を即座に拒否させる。さらに同じ bytes は
  `output/s8b-freeze/holdout_freeze.json` と `measurement_freeze.json` の
  `implementation_hashes` にも束縛されていて、閉包を追うと凍結 holdout / seal の書き換えに波及する。
  s8a 側は TRACE=1 で採った値であり、親が根拠にした TRACE=0 同一性証拠が適用できないうえ、
  現物は `build_admissions` field を欠くため wave 以前から読み込み不能 (= 未使用) だった。
- 根本原因: 現用性を **consumer の存在**で判定し、**consumer が何を要求しているか**を読まなかった。
  `grep` で呼び手を見つけた時点で「現用」と結論し、その呼び手の比較対象 (新しい pin なのか、
  旧 bytes なのか) を確認していない。
- 恒久対応: {{D:frozen-evidence-historical-binding}} の判定規則 (「consumer の存在」ではなく
  「consumer が何を要求しているか」で現用性を決める) と、memory
  `frozen-artifact-liveness-by-what-consumer-demands`。
- 再発検知: 凍結・校正 artifact を書き換える wave では、段 6 の敵対レビュー 1 本を
  「その artifact の bytes を hash で束縛している箇所の全列挙」に必ず割り当てる
  (本件はレンズ B がこの列挙で検出した)。

## 再発

### F240

- **再発: 2026-08-12** ([T-816] 手順 4 wave が [T-917] の保留執行を担った際)。
  `orchestrator/tests/test_frozen_artifacts.py` の `_frozen_artifact_check_result()` が、
  保留中に `FROZEN_MANIFEST` **23 件を一括 skip** する実装になっていた。この 23 件には
  selector prediction / journal / payload / envelope / raw response の**盲検封印 14 件**が含まれ、
  oracle の結果を見た後に予測を整合的に書き換えることを防ぐ実験妥当性である。
  静的レビューが「23 件一括 node の保留は禁止」と警告した所見が、実装に現れた実例である。
  修正: held (凍結チェーン 4 件) / keep (残り 19 件) を定数で明示分割し、積が空・和が全 key と
  一致することを検査する positive control を追加した。

### F230

- **再発: 2026-08-12** ([T-816] 手順 4 実装 wave)。変異 8 件のうち 2 件が MISMATCH。
  期待 node を**波及の完全集合として導出せず**、直接の対象テストだけを登録した。実測では
  missing-end の記録を落とす変異が cycle 優先テスト (framing 件数に依存) も落とし、
  `0 0` frame を過剰拒否させる正例は 1 本でなく 10 本を落とした。いずれも SURVIVED ではなく
  検出はされているので検出力の欠落ではないが、台帳の期待値としては誤りだった。
  初回結果を消さず `mutation-ledger-a.json` に残し、実測の完全集合で再登録した確認走を
  `mutation-ledger-b.json` に置いて 2 件とも KILLED を確認した。
