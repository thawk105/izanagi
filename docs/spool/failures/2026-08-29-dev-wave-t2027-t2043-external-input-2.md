---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-29
wave: dev-wave-t2027-t2043-external-input
seq: 2
---

## 新規

### {{F:hold-evidence-circularity}}. 非帰属赤の hold 登録が「exact 関数名を含む F」要求で循環し wave を止めた [手順漏れ] [テスト代表性]

- 事象: T-2027/T-2043 の wave が受入全走を 2 回投入し、いずれも
  18319 passed / 62 skipped / 1 failed で戻った。唯一の赤は
  `orchestrator/tests/test_growth_test_holds_contract.py::test_regular_pytest_path_keeps_single_hold_skip`
  で、本 wave の差分から到達しない node だった。`DW-O18` に従って
  `orchestrator/tests/flaky_test_holds.py` へ hold を登録しようとしたが登録できず、
  wave は受入の手前で中断した (2026-08-28)。翌日の回収 wave が原因を特定した。
- 根本原因: 二つが重なっていた。**(1) 証拠 F の選び違い** — 中断した wave は同型の
  既存 F として F273 (`test_codex_worker_launch.py` が並行 launcher の負荷で落ちる) だけを見て
  「exact 関数名を含む F が無い」と結論した。実際の族の正本は F480 (絶対 wall-clock 上界が
  受入の並列負荷で壊れる) であり、`Thread.join(<秒>)` の上界も順序 assert も同族として
  既に追記されていた。台帳を主題ではなくファイル名で引いたため、正しい族に当たらなかった。
  **(2) 構造的な循環** — `flaky_test_holds.py` の field 契約は、`evidence_id` の指す F 節が
  当該 node の **exact な test 関数名を言及していること**を検査する (`_evidence_section` 照合)。
  新しい node の再発を F へ land するには受入全走を通す必要があり、その受入を通すには
  hold が要る。`DW-S07` は 3 台帳の直接編集を禁じ、fragment は land の fold でしか
  `docs/failures.md` に入らないため、wave の中でこの輪を切ることはできない。
- 恒久対応: 本件では上界が検査対象の性質ではなく `subprocess.run` の anti-hang guard だったため、
  hold を登録せず当該 1 呼び出しの予算を広げて閉じた (実体は
  `orchestrator/tests/test_growth_test_holds_contract.py` の
  `test_regular_pytest_path_keeps_single_hold_skip` に渡した明示 `timeout=120.0` と、
  その根拠を書いた同行のコメント)。**この抜け道は上界が性質そのものである node には無い。**
  契約側の境界をどう変えるかは受理集合に関わるため本 wave では決めず、
  {{T:hold-evidence-circularity}} としてユーザー裁定へ返す。
- 再発検知: 受入の非帰属赤を hold 登録しようとして「evidence_id が test 関数名を言及していない」で
  止まったら、まず `docs/failures.md` を**ファイル名でなく破れた assert の主題**
  (実時間の上界か、イベント順序か、負荷依存か) で引き直し、族エントリが別 F に無いか確かめる。
  族が正しく当たってもなお exact 関数名が無いなら、それは本エントリの循環に入っている。

## 再発

### F480

- **再発: 2026-08-28** — 受入全走 2 回 (同一 tip、attempt 1 = 04:07、attempt 2 = 04:21) が
  いずれも `orchestrator/tests/test_growth_test_holds_contract.py::test_regular_pytest_path_keeps_single_hold_skip`
  1 件だけで赤になった (どちらも 1 failed / 18319 passed / 62 skipped)。破れたのは
  同 file の helper `_run_subprocess` の既定 `timeout: float = 10.0` で、
  `subprocess.run` の budget 切れである。当該 node は実 conftest を読み込む pytest session を
  subprocess で起動する、同 file で唯一の呼び出しであり、他の 11 呼び出しは `--noconftest` か
  小さな合成 file を走らせるので桁が違う。**同 node の単独走は緑** — 中断時 4.15 秒、
  翌日の回収 wave が local main を取り込んだ tip でも `1 passed in 4.25s` / rc=0 で再現しなかった。
  受入全走は compute job へ shard され約 48 並列の xdist で走るため、4.25 秒の子 session が
  10 秒を超えるのは容易であり、余裕は 2.35 倍しかなかった。本 wave の差分 (compiler input の
  根分類と再束縛、4 module) は当該 node の実行経路に入らない — 起動される内側 node が import
  するのは `s8b_holdout_freeze` だけで、しかも growth hold により skip する。
- **この再発が族に足す区別: 破れた上界が「検査対象の性質」か「hang 防止の guard」か。**
  F480 の既存事例 (deadline の絶対性、hook の相対順序) では assert 自身が守りたい性質だったので、
  上界の設計は所有者の判断として据え置かれた。本件の 10 秒はそうではない — この node の assert は
  subprocess の終了コードと 3 つの出力 marker だけで、経過時間を一切見ていない。よって
  当該 1 呼び出しにだけ `timeout=120.0` (実測 4.25 秒の約 28 倍) を渡し、helper 既定の 10.0 秒は
  他 11 呼び出しのために据え置いた。**受理集合は不変**で、真の hang には従来どおり fail-closed する。
  上界が性質そのものである node では、この処置は使えない。
- なお、この赤の hold 登録が構造的に不可能だったことは {{F:hold-evidence-circularity}} に別記した。
