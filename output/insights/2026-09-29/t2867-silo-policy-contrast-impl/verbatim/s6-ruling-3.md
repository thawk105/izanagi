# [T-2867] 段 6 裁定 3 (焦点再レビュー 1 巡目を受けて、親、2026-09-29 16:4x JST)

入力: `codex/s6-focus-1/out.md` (NO-GO、対応表で F1・F3・F5〜F7・F9〜F13・F16・G1〜G3 closed、F2・F4・F8・F14・F15 partial)。

| N | 判定 | 処置 (所有) | 成果物への影響 |
|---|---|---|---|
| N1 report が retry 前後の slot 結果を全部数える | real・must-fix | report は論理 slot ごとに最後の attempt の `slot-result` だけを射影し、その行で件数・identity を検査する (Z)。F2・F8 の partial もこれで閉じる | 許された機械故障 retry が score・floor を欠測にする |
| N2 429 が終端記録の後に起きたときの重複・欠落 | real・must-fix | 親は各起動の前後で台帳を読み、同じ a に `proposed`/`rejected`/`empty`/`role-failure` の終端が既にあれば起動せずその値を返す。round の `check`・`finalize` は同じ a の既存終端があれば新しい event を書かずに既存の結果を返す (冪等)。F4・F14 の partial もこれで閉じる (Z) | A の二重計上、または有効な提案を持つ系列の欠測 |
| N3 proposed/rejected に model ID が載らない | real・nit | 追加しない。各起動の `claude -p` の JSON 出力は attempt dir に全件残り、model はそこから確かめられる。F15 はこれで閉じる (記録だけ) | なし (監査は attempt dir で可能) |
| N4 stock 不成立でも初期点を測る | real・should-fix | job 1 の単位で stock の slot が certified でなければ残りの slot を測らずに単位を終え、`close_series_if_done` で `stock-unestablished` を記録する (X)。台帳側の終了判定が 3 件の結果を要求するなら、stock 不成立の時点で終了できる形に合わせる (Y) | 不成立系列で 2 session 分の計算を使う |
| N5 worktree 内の checkout は job body が拒否 | refuted | 生死確認は AI worktree 容器の外の submit checkout (job dir 下の detach) から投げる計画 (`live/make-submit-trees.sh`) | — |

- DW-O16 の 3 巡上限: これが 1 巡目。fix 3 の後に焦点再レビュー 2 巡目を行う。
