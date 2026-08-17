---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-17
wave: t1283-waiter-runner-main-blob
seq: 2
---

## 新規

### {{F:acceptance-authority-self-certified}}. 受入証拠の主経路が wave tip の自己証明のままである [恒真ゲート]

- 事象: 受入の合否を書く待ち手 `tools/dev_wave_wait.py` と実行器 `tools/run_tests.py` は
  wave tip 側の版が使われる。land が待ち手について照合するのは
  `receipt["waiter_blob_sha"] == tested_tip:tools/dev_wave_wait.py` だけで、
  発行側も land 側も同じ tip の tree から算出するため実行体の検査としては恒真である
  (D403 本文が自ら明記)。したがって wave は待ち手を書き換えるだけで、実際の子 rc が 1 でも
  `child_rc=0 / verdict=child-green` の受領証を作れる。2026-08-17 の実測では受領証 25 本のうち
  24 本が `child-green` であり、**これが受入の主経路**である。
- 根本原因: 権威の検査を、権威を疑われている当人 (wave tip 側の待ち手) の中に置いている。
  実行 bytes を main 側 blob へ束縛して自己再実行する案も、検査と再実行の双方が同じ待ち手の中に
  あるため、書き換えた側が再実行を削除して main 側の hash を自己申告すれば land を通る
  (2026-08-17 の敵対レビューが実証)。Git 由来の値だけで閉じる形 (main==tip 等値) は、
  待ち手・実行器を編集した wave をどの経路でも land 不能にする。
- 恒久対応: **部分のみ。閉じていない。** 実在する fails-closed 検査は
  `tools/dev_wave_wait.py` の `_verify_red_check_receipt` と `tools/dev_wave_land.py` の
  受領証検証が **`verdict == "non-attributable-only"` の経路でだけ** checker と runner を
  tested main の blob へ束縛する部分だけである (D487 決定 4、[T-1131])。受入の約 96% を占める
  `child-green` 経路は未閉鎖であり、閉じ方は [T-1283] のユーザー再裁定に係属する。
  [T-696] が「審査される側が審査する道具を書き換えられる」構造を協調境界として受容した残余と
  同じ所有に置く ([T-1195] が課した記録条件の執行)。
- 再発検知: 受入受領証の `verdict` 分布を集計し、`child-green` が主経路である限り本欠落は
  生きていると読む (集計 predicate は 2026-08-17 の worklog エントリに記録)。
  非帰属経路の束縛が発火した割合が、既存の部分対応が実際に効いた割合の上限である。
