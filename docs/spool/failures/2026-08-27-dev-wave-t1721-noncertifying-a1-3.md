---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-t1721-noncertifying-a1
seq: 3
---

## 新規

### {{F:promotion-prohibited-marker-was-vacuous}}. 昇格禁止 marker と use class が 1 つも発火しておらず、恒真な保証だった [恒真ゲート] [誤前提]

- 事象: A-1 の campaign config は `promotion_prohibited=True` を持ち、`declared_use_class` も
  複数 module で使われている。裁定要約と作業依頼はこれらを「非認証であることの表明」として
  扱っていた。ところが read-only probe で、**この 2 つの値を保ったまま certified 受入の
  gate を E1 で通せた**。marker は 1 箇所も判定に効いていない。
- 根本原因: `declared_use_class` は保存先 root と build 材料の選択にしか使われず、
  campaign 同一性にも consumer 境界にも入っていない。official と exploration で campaign id が
  同一になることを固定した既存テストがある。`promotion_prohibited` は campaign config の
  `search_config` に載るが、lock の identity 検査は exact 5 key と型しか見ず中身を読まない。
  どちらも「宣言はあるが読む者がいない」型である。
- 恒久対応: {{D:noncertifying-type-blocked-by-lock-only-gate}} が、宣言を同一性へ入れるだけでは
  不十分であることを決定として固定した。実効化は
  {{D:noncertifying-scope-is-one-land-unit-through-final-reader}} が定める再開 wave の
  1 land 単位に含める。恒真な marker を据え置かない。
- 再発検知: 「この値は昇格を防ぐ」と要約された field を見たら、その値を**保ったまま**
  certified 経路を通せるかを read-only probe で 1 回試す。通るなら marker は恒真である。

### {{F:lock-only-epoch-gate-bypasses-ratification}}. 批准 gate の適用範囲を producer 側の 1 呼び出しだけと測り、lock だけで epoch を決める consumer 経路を見落とした [誤前提] [手順漏れ]

- 事象: 段 1 の前提実測で、批准検査の production 呼び手を
  `ident.py` の `_capture_current_loader_binding` 1 箇所と数え、そこを分岐させれば非認証型の
  座は足りると provisional に裁定した (親 brief の P2)。実際には、campaign lock だけを読んで
  certified epoch を出す consumer 経路が別にあり、**そこは批准台帳を 1 度も参照しない**。
  未批准の closure から作った lock がその経路を E1 で通る。
- 根本原因: 「gate を課す側の呼び手」を全数で数えたが、「gate を課さずに同じ判定を出す側」を
  数えていなかった。producer 側の座と consumer 側の座は別の集合であり、前者の全数は
  後者の不在を含意しない。
- 恒久対応: {{D:noncertifying-type-blocked-by-lock-only-gate}} が lock-only 経路を
  閉じるべき対象として名指しした。段 1 の実測表はこの見落としを含んだまま insight へ保全し、
  訂正を同 insight の訂正節に書いた。
- 再発検知: 受理集合を広げる wave で「gate の呼び手は N 箇所」と測ったら、**同じ判定結果を
  gate 抜きで出す経路**を別に探す。呼び手の全数検索はそれを見つけない。

## 再発

### F634

- **再発: 2026-08-27** — [T-1721] の実装 wave が段 1 で投入器の実在を再検査し、
  `tools/pegasus/submit_*.sh` が 8 本あるのに A-1 用は 0 本、
  `paper-story-a1-paired-submission/v1` を書く実装が tracked file に 0 件であることを再確認した。
  F634 の恒久対応 (段 1 の前提実測で実行器の tracked file を全数検索する) は**発火し、
  着手前に検出した**。本 wave は別の理由 (非認証成果物型が作れない) で停止したため
  投入器は実装していないが、契約の全数調査は完了して insight へ保全した。
