---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t1140-t330-claim-authority
seq: 3
---

## 新規

### {{F:glob-swallows-permission-error}}. `Path.glob()` が列挙拒否を空集合へ変え、走査型の防壁を恒真化する [恒真ゲート]

- 事象: (2026-08-16、段 3 敵対相談の指摘を親が実測) claim root を走査して競合を探す防壁の設計案が
  `Path.glob("*.claim")` を使っていた。Python 3.10.12 の `pathlib.py:459-460` は
  `except PermissionError: return` であり、**列挙が権限拒否されると例外を上げずに空を返す**。
  親が実測したところ、`chmod 000` した directory に対し `Path.glob()` は `[]` を返し、
  `os.scandir()` は `PermissionError` を送出した。設計文が書いていた
  「列挙失敗は operational error にする」は `glob` では実装できない。
- 根本原因: 「走査して見つからなかった」と「走査できなかった」を、標準ライブラリの
  例外抑制によって同一の戻り値へ潰していた。走査型の防壁は、空集合を「競合なし」と読むため、
  列挙拒否がそのまま通過へ倒れる。実装前に発見したので成果物への影響はない。
- 恒久対応: {{D:claim-liveness-exclusion-scope}} が列挙を `os.scandir()` で明示的に包み、
  `OSError` を error へ翻訳することを要求する。書込み可能な root の初回 `os.scandir` だけへ
  `PermissionError` を注入する変異 (本 wave の M06) が、この分岐を戻すと赤くなる。
- 再発検知: 防壁が directory / 集合を走査して「見つからなければ通す」構造を持つとき、
  その列挙 API が権限・I-O 失敗を例外として伝えるかを実測すること。
  `Path.glob` / `Path.rglob` / `Path.iterdir` の失敗時の戻り値を仕様で確認せずに使わない。

### {{F:postscan-both-reject-overclaim}}. 新設テストが production の保証しない「双方拒否」を要求し、変異走行でだけ露見した [事前登録の不完全]

- 事象: (2026-08-16、変異本走) claim の post-scan を検証する新設 node が
  `assert [result["ok"] for result in results] == [False, False]` と書かれていた。
  変異走行の 1 巡でこの node が赤くなり、親が stdout を実測すると
  `assert [False, True] == [False, False]` だった。待ち時間の上限を引き上げても再現した。
- 根本原因: post-scan の**双方拒否は production が保証する性質ではない**。先に競合を検出した側は
  error を送出してプロセスが終了するため、後から post-scan する側からはその PID が存在せず、
  DEAD として正当に通過する。設計判断は「双方拒否は受容する」であって
  「必ず双方拒否になる」ではなかったのに、テストが後者を固定していた。
  親が最初にこれを「高負荷フレーク」と誤診し、待ち時間の引き上げを 1 巡余分に費やした。
- 影響: 実装は正しく、成果物への影響はない。ただしこの node をそのまま land すれば、
  他の wave の受入全走が確率的に赤くなり、緑 1 回で 1 回分の land 窓を消費する運用を汚染していた。
- 恒久対応: 判定を production が実際に保証する 2 点 (成功数は高々 1 / 全 owner 死亡後に次が通る)
  へ訂正した。二重成功の検出力は `sum(...) <= 1` で維持している。
- 再発検知: 競合する複数 process の**特定の結果の組合せ**を等値で固定するテストを疑う。
  固定してよいのは不変条件 (上限・下限・到達可能性) であって、レースの決着そのものではない。
  「赤が高負荷でだけ出る」と見えたら、待ち時間を疑う前に**失敗した assert の実文**を読むこと。
