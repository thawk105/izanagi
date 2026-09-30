# [T-2867] 本走 wave 段 6 裁定 2 (親、2026-09-30 12:5x JST) — 焦点再レビュー 1 の裁定と段 6 の終了

対象: `codex/s6-focus-1/out.md` (NO-GO、新 must-fix 2)。fix 後の loop = `runner/contrast_runner.py` (sha256 bfc099a1…051d)、自己試験 12/12 (計算ノード bnode064、request 37781)。

| 所見 | 裁定 | 根拠 |
|---|---|---|
| 裁定 1 の 1 (排他) | closed | 焦点再レビューの判定どおり |
| 裁定 1 の 4 (qstat 遅延) | closed | 同上 |
| 裁定 1 の 2・3・6 | fail-closed として採る (残りは下の 2 件) | 二重起動・二重投入は attention で止まる |
| 新 A: 不明な親・job が残っても done.json | refuted as must-fix → nit | 起動成功から state 保存までの窓は 1 回の `persist` のみ。起きてもその系列は attention に載り done.json に列挙される。親は done の後に attention を全件分類してから report へ進む (handoff の運用規則)。結果の値・受理集合は変わらない |
| 新 B: 周の途中の STOP | refuted as must-fix → nit | 停止は親の運用操作で登録規則ではない。停止後に投げた job も state に記録され、再起動した loop が追う。結果の値は変わらない |

DW-O16 に従い fix を重ねず、ここで段 6 を閉じる。実行環境依存 (signal・lock・旧 state の読込・走行中 job の引き継ぎ) は、前走の loop を SIGTERM で止めて修正版で再起動する実走で確かめる。
