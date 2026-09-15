---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-15
wave: dev-wave-t2595-floor-query-legacy-symmetry
seq: 1
---

## {{D:floor-query-counts-recovery-before-legacy}}. 床値 retry の query は legacy 認可を返す前に同じ trigger の recovery 候補を数える

`floor_retry_trigger_for_round` は、round の各 session-start について完了行を集めて legacy 候補を作り、
別のループで registry recovery 候補を集める。後者だけが「既に retry へ使われた trigger」を除外していた。
その結果、使用済み trigger が canonical な失敗 planned 完了行と recovery 候補を併せ持つとき、query は
recovery 候補を数えずに多重性検査を通し、legacy 認可を返した。同じ履歴を消費側
`_assert_retry_start_authorized_locked` は「完了数 + recovery 候補数 != 1」で拒否する。公開 query と
消費ゲートが同じ journal に別の判定を返していた。

**決定:** query は legacy 候補を認可として返す前に、選んだ trigger の recovery 候補を
**使用済み除外なしで**数え、非空なら消費側と同じ文言
`retry trigger has both completion and recovery evidence` で `HoldoutAdmissionError` を上げる。
逆向き (recovery を選んだ trigger に完了行がある場合) には既に同じ検査があり、その対称形である。

**採らなかった案と理由:**

- 使用済み trigger を legacy 候補からも一律除外する — legacy 経路は同じ trigger で retry 枠を
  使い切るまで複数回 retry するのが設計 (`s8b_floor_campaign.py` の `_retry_round` の while ループ)
  であり、正当な resume を壊す。
- 黙って `None` を返す — 呼び手 `_retry_authorization` は `None` を「この cell は retry 不要」と読む。
  消費側が拒否する履歴を検出しておきながら、試行不足のまま先へ進める。
- recovery 側の使用済み除外を外す — recovery の一回限定設計を変える。

**この決定が変えないもの:** 消費側と最終 inspection の受理集合。certified な成果物の値・受理集合・参照。
現時点の production では registry recovery 行を書く呼び手が無く、混在履歴を置いても通常 resume は
`_replay_cut6_start` の cut-6 検査で query より先に拒否する。閉じたのは API 境界の判定不一致であり、
scheduler collector が接続された時点で live になる。

段 1 brief はこの影響を「測定を 1 本空費して `artifact-invalid` で終わる」と書いたが、段 3 の敵対 2 本が
現物で否定した。消費は測定 callback より前に行われる。この訂正は
F591 の再発として failures へ記録した。
