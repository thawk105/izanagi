---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-8b-b2-precheck
seq: 3
---

## 新規

### {{F:cli-double-module-diagnostics}}. 同じ判定を CLI 経由と library 経由で呼ぶと答えが変わる道具を、現在地の一次資料に使った [テスト代表性] [手順漏れ]

- 事象: 8c 事前登録の発効判定 `s8c_preregistration.py` を CLI として起動すると、12 条件
  すべてが `ERROR / evaluator-exception` になる。同じ引数で package として import して
  `main()` を呼ぶと本当の内訳 (C03 のみ UNSATISFIED、他は EVIDENCE_UNDEFINED、
  C05 は `schedule-schema-absent`、C08 は `prereg-binding-proof-undefined`) が出る。
  親は precheck の最初の実測でこの CLI 出力を採り、「12 条件すべてが評価不能」と読んで
  ユーザーへ報告した。直後の追加調査で library 経由との食い違いに気づき、訂正した。
- 根本原因: 判定器を `__main__` として実行すると core module が二重に実体化し、
  結果正規化の `isinstance` 判定が偽になって `PreregistrationError` が送出される。
  その例外を `except Exception` が握り潰し、全条件を一律 ERROR へ倒す。
  検査が通らなかった事実は残るが、**なぜ通らなかったかが消える。**
  同型の欠陥がもう 1 件あり、`s8c_gate_report.py` はファイルパス直接起動では
  相対 import で ImportError になる (`python3 -m` 形式なら正しく動く)。
- なぜテストで捕まらなかったか: CLI の既存テストは imported module の `main()` を呼ぶ。
  実プロセスとして `__main__` を起動する経路を一度も通らないため、二重実体化が起きない。
  **テストが通す経路と、人間が打つコマンドが別物だった。**
- 恒久対応: memory `check-rc-not-through-pipe` と同じ系統の作法として、
  **道具の出力を現在地の一次資料に使う前に、別の起動形 (library 呼び出し、または別の
  権威ある入口) で 1 回突き合わせる**。本件では `python3 -m
  orchestrator.campaign.s8c_gate_report` が正しい内訳を返す独立入口として実在した。
  コード側の修正は次の一手へ登録した (CLI を実プロセスとして起動する検査の新設を含む)。
- 再発検知: 同じ判定を返すはずの 2 経路が異なる答えを返さないことを、CLI を subprocess として
  起動する検査で固定する (未実装。次の一手で追跡)。
