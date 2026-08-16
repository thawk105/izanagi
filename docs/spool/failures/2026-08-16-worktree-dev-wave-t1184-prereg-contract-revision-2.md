---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: worktree-dev-wave-t1184-prereg-contract-revision
seq: 2
---

## 新規

### {{F:live-derived-hash-pins-invisible-to-search}}. 生きた成果物から導出した hash の literal pin が path 検索にも値検索にも掛からず、実走でだけ露見した [手順漏れ]

- 事象: 8c 事前登録の証拠契約を改訂する wave で、親は着手前に pin 閉包を取った。成果物 path で
  `grep -rn` し、契約 hash の現在値で `grep -rln` し、生きた pin は
  `orchestrator/tests/test_s8c_preregistration_core.py` の 2 箇所 (現行値の凍結テストと
  第 1 世代の歴史値) だけだと結論して brief へ書いた。段 5 実装子はその 2 箇所を更新し、
  段 6 の敵対レビュー 2 本も pin 閉包を攻撃面に含めたうえで「追加の trust root は
  見つからなかった」と報告した。**計算ノードでの実走が 3 件の赤を出した** —
  `test_evidence_contract_hash_accepts_non_path_controls` の `[cr]` / `[nul]` / `[lf]` である。
  生きた pin は 2 箇所ではなく 5 箇所だった。
- 根本原因: この 3 param は、**生きた証拠契約ファイルを読み込み、その JSON を改変してから
  hash した値**を literal で持っていた。したがって literal は成果物の現在値と一致せず、
  値による検索に当たらない。path による検索は当該テストファイルを挙げるが、同ファイルには
  pin でない参照も多数あるため path hit だけでは pin の所在を特定できない。
  **pin には「成果物 path を含む」でも「成果物の現在値を含む」でもない第 3 の型がある** —
  成果物を入力にして計算した派生値の pin である。既存の pin 閉包手順はこの型を名指ししていない。
- 恒久対応: memory `derived-hash-pins-need-separate-search` — 凍結成果物の bytes を変える wave の
  pin 閉包では、**成果物を読み込んで加工してから hash / digest を取る箇所**を別途探す。
  具体的には、成果物 path を含むテストファイル内で、hash / digest 関数の呼び出しと
  64 文字 hex literal が同一テスト関数内に共起する箇所を列挙する。値検索と path 検索の
  どちらにも当たらないため、この形は別の探し方を明示しないと必ず落ちる。
  **`DW-O09` への追記は取れなかった** — 同節は 996 / 1000 bytes で余白が 4 bytes しかなく、
  既存行の圧縮は dev-wave docs の exact pin を壊す。lint 化は
  {{T:derived-hash-pin-closure-lint}} へ起票した。
- 再発検知: 凍結成果物の bytes を変える wave は、静的レビューを pin 閉包の完了根拠にしない。
  **本件は静的レビュー 3 者 (実装子・敵対レンズ 2 本) が全員見落とし、実走だけが検出した。**
  統合 commit の前に、当該成果物を消費するテストファイル全体を計算ノードで 1 度実走させる。
  実走で出た赤の件数が brief の pin 閉包と食い違ったら、閉包を取り直してから先へ進む。
