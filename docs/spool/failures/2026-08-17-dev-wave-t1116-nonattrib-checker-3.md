---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-17
wave: dev-wave-t1116-nonattrib-checker
seq: 3
---

## 新規

### {{F:consumer-partial-predicate-check}}. 呼び手を確認したと書きながら入れ子の exact 検査を見落とし、修正が end-to-end で 1 度も発効しなかった [恒真ゲート] [手順漏れ]

- 事象: 2026-08-16 の commit `8a2b735b` が受入赤の分類へ第 3 分類 `flake` を足した。
  commit body は「既存の呼び手 `tools/dev_wave_wait.py` は既に同 flag を渡しており、
  receipt でも `wave_tip == tested_tip` を照合しているので壊れない」と述べた。
  しかし同 file には**受領証の node ごとの exact 検査**が別にあり
  (`set(node) == {"classification","nodeid","rerun_rc"}` かつ
  `classification == "non-attributable"`)、5 field の `flake` node はそこで落ちる。
  結果、修正は checker 層で正しく動きながら **end-to-end では 1 度も発効せず**、
  「確率的なフレークで受入全走を何度も無駄にする構造は許さない」というユーザー裁定が
  丸 1 日「実装済み」と誤認されたまま運用された。文字列 `flake` の出現数は
  `tools/dev_wave_wait.py` / `tools/dev_wave_land.py` とその test の 4 file すべてで 0 だった。
- 根本原因: 「呼び手を確認した」を **root field と CLI flag の照合だけ**で閉じた。
  exact 述語は root / 配列要素 / 入れ子 object のそれぞれに独立して置かれるため、
  1 段の通過を全体の通過と読むと修正が黙って無効化される。
  テストが producer 側 (`orchestrator/tests/test_check_acceptance_reds.py`) にしか無く、
  consumer 側へ新しい形を渡すテストが 1 件も無かったので、全部緑のまま通った。
- 恒久対応: memory `consumer-exact-predicates-must-all-be-checked` —
  出力形を変えたら consumer file を `set(` と `==` で grep して**全述語**を新しい形へ当て、
  実際の producer 出力を 1 件作って consumer の述語へ通し accept/reject を実測する。
  **機械化 (受領証 schema と消費側述語の相互 pin) は本件の受理集合裁定に従属する**ため、
  裁定パッケージ #2 の採択後に同 wave で行う。
  裁定パッケージ = `output/insights/2026-08-17_t1116-nonattrib-checker/ruling-package.md`。
- 再発検知: 実 producer 出力を consumer 述語へ通す実測を、出力形を変える wave の完了条件に置く。
  本件は `output/insights/2026-08-17_t1116-nonattrib-checker/probe2-receipt.json` を
  消費側述語へかけて REJECT を得ることで検出した。
