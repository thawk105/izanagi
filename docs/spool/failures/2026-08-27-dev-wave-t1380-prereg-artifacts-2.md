---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-t1380-prereg-artifacts
seq: 2
---

## 新規

### {{F:pinned-suites-freeze-part-of-a-living-ledger}}. 生きた台帳の一部を exact pin で凍結し、全体更新をできなくした [恒真ゲート] [自己整合]

- 事象: 受入全走が 17700 件中 1 件だけ赤で戻った。落ちたのは
  `orchestrator/tests/test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`
  で、`orchestrator/tests/acceptance_duration_ledger.json` の被覆率が
  **15912 / 17700 = 89.898305%** となり閾値 0.90 を 18 node 分だけ割った。
  7 時間前の別 wave の受入では同 gate は緑で、suite の成長が閾値を跨いだ初回である。
- 根本原因: 台帳は「90% 被覆契約の非網羅台帳」として運用され、被覆率 gate が
  **現在の collection への追随**を要求する (F515 が同 gate を陳腐化検知も兼ねると明記)。
  一方 `orchestrator/tests/test_update_acceptance_duration_ledger.py::test_t1574_changed_suite_ledger_node_delta_is_exact`
  は、**8 suite 分の node 集合 identity (件数 + sorted UTF-8 の SHA-256) と 12 個の所要値を
  exact に固定**している。**同じ台帳の一部だけが凍結され、残りは追随を要求される。**
- 実測 1 (全体再生成は通らない): 受入走行の JUnit から台帳全体を再生成すると被覆率は
  99.994350% (17699 / 17700) へ回復するが、pin が 121 / 42 / 69 node と定める
  `test_critic.py` / `test_real_repo_serialization.py` / `test_sort_swo_oracle.py` の実体は
  現在 **138 / 46 / 81 node** であり node 集合 hash が一致しない。pin 済み 12 値も
  5.89 対 8.6 のように全て食い違う。**全体再生成は T-1574 を壊す。**
- 実測 2 (部分更新なら通る): 現 collection にあって台帳に無い node は 1787 件で、
  そのうち **1725 件は凍結対象の 8 suite の外**にある。この 1725 件だけを実測所要つきで
  足すと被覆率は 17637 / 17700 = 99.64% となり、凍結された 8 suite の node 集合も
  12 個の所要値も 1 byte も動かない。**両 gate は同時に緑にできる。**
  「両立不能」と結論するのは誤りである — 本 wave も一度そう判断しかけ、実測で覆した。
- 恒久対応: 部分更新で被覆率を回復させた。**着地したのは main の 50b36435 で、
  本 wave とは独立に同じ手を採っている** — 凍結 pin の 8 prefix には触れず、その外側の
  1725 nodeid だけを受入全走の実測値で足す、という手も理由も同一である。本 wave も
  同じ結論に独立到達して同じ変更を作ったが、land 再試行の merge で main 側を採り、
  重複した変更は落とした。**同一の欠陥に対し 2 つの wave が独立に同一解へ到達した。**
  ただし**根本原因は残る** — 凍結された 8 suite の台帳 entry は今後も更新できず、
  その部分の陳腐化は被覆率 gate の分母が大きいうちは検出されない。凍結 pin の対象を
  所要値と node 集合から「delta の向き」だけへ絞るかどうかはユーザー裁定へ送った。
- 再発検知: **同じ artifact を対象にする gate を新設するとき、既存 gate と要求の向きが
  逆でないかを機械検査する仕組みが無い。** 本件は受入が赤になって初めて表面化した。
  向きの衝突を機械検出する gate は未実装で、次の一手として起票した。
