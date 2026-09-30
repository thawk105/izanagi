## 所見

**R1 — must-fix — [core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/verifier/core.py:172)**  
D2a は同じ key の外部読みを `external_seen` で最初の一回だけ照合する。`Q` に `R:k:正しい刻印:- R:k:誤った刻印:-` が並び、対応する `R` 行が一つある履歴では、二度目の観測値が検査されない。**影響:** 値を取り違えた取引を certified の受理集合に入れうる。**推奨:** 書き前の外部読みは、同じ key の二度目以降も、その `R` 行が指す版の刻印と照合する。  
受理の含意: 上記の誤った二度目の読みが、他の検査を満たせば通る。拒否の含意: 最初の読みの刻印だけが誤る履歴は現状でも D2a で拒否される。通る正例は、同じ key を二度読み、両方が対応する版の刻印を返す履歴。

**R2 — must-fix — [launch_gate_liveness_v3.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/scripts/launch_gate_liveness_v3.py:22)**  
起動器は `d1_a`・`d2a`・`d5` を読むが、本番の [report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/verifier/report.py:144) は `D1a`・`D2a`・`D5` を出す。現状の `prereg()` は全条件で「missing gate counts」を返し、X の D5 判定にも到達しない。**影響:** 生死確認の実測を、事前登録との一致として読めない。**推奨:** 起動器のキー名を本番投影に揃え、S/X/B/N の保存済み JSON 例で判定関数を確認する。  
受理の含意: 現状では正しい X の結果も `match` にならない。拒否の含意: 誤った結果も期待条件との比較まで進まず、単に判定不能になる。通る正例は、`counts.D1a=0`、`counts.D2a=0`、`D5="pass"` を持つ X の本番 JSON。

**R3 — must-fix — [ycsb.hh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/ccbench/include/ycsb.hh:17)**  
土台 F では空行が 16 行、`gflags` include が 17 行である。追加した `#line 17` は次の空行を 17 行にするため、以後の元コードの行番号が次の `#line` まで一つずれる。TRACE=0 の `__LINE__` 同一性を満たさない。**影響:** D297 が拒否すべき計装を通したと扱うと、性能 build の同一性という一次資料の主張が誤る。**推奨:** この指定を `#line 16` に直し、予定された GCC 11・12 の D297 で確認する。  
受理の含意: 現状の U1 を同一と受理する根拠はない。拒否の含意: D297 がこの差を検出した場合、U1 の受入は止まる。通る正例は、元の空行を 16、include を 17 とする前処理結果。

**R4 — should — [launch_gate_liveness_v3.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u1/output/runs/t2884-u1/scripts/launch_gate_liveness_v3.py:56)**  
`own_write_read_transactions` と `written_transactions` が一つでも 0 なら、S/B/N まで一律 `indeterminate` にする。事前登録でこの発生条件を必須にしたのは X であり、N は commit・abort の記述だけである。**影響:** 有効な S/B の読みや N の記述値を、事前登録にない条件で失う。**推奨:** 発生条件の判定を条件別に置き、X の二条件と B の発火数をそれぞれ確認し、N は記述結果を保持する。  
受理の含意: 現状では N の記述結果さえ `match` として整理できない場合がある。拒否の含意: B1 が発火して D1(b1) と一致しても、別の発生条件が 0 なら判定不能になる。通る正例は、B1 committed が 1、D1(b1) が 1、own-write-read が 0 の B 走行。

**R5 — should — [test_verifier_gate_witness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/tests/test_verifier_gate_witness.py:115)**  
M9 の比較だけを外すと [core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2884-gate-verifier/orchestrator/verifier/core.py:138) の `pending_v[...]` が `KeyError` になる。M10 の集合比較だけを外しても、欠けた `paths[thid]` が `KeyError` になる。両テストは失敗する見込みだが、欠落を計数して拒否する述語の単一理由性は示さない。**影響:** 変異の「kill」を、意図した fail-closed 判定の証拠として過大に主張しうる。**推奨:** 各変異の実走では例外内容も保存し、欠落時に構造化した到達不能へ進む変異・fixture で述語を確認する。  
受理の含意: 現状のテスト失敗をそのまま kill と数えると、例外による失敗も受け入れる。拒否の含意: 期待する `gate_unreachable=1` が返らない変異結果は、意味上の kill として扱えない。通る正例は、V と全 thread の gate file が揃い、到達不能 0 になる fixture。

## 変異 M1〜M15 の kill 見込み

静的な見込みであり、変異本走は未実施。

| 変異 | 見込み | 理由 |
|---|---|---|
| M1 | KILLED | 後続読みのない B2 fixture は D1(a) だけが 1。 |
| M2 | KILLED | B1 fixture は最初の読みの R 欠落だけを D1(b1) に計数。 |
| M3 | KILLED | Q にない R key は D1(b2) だけが 1。 |
| M4 | KILLED | 枠だけ、`Q -`、txid 不一致の三 fixture は D1(c) だけが 1。 |
| M5 | KILLED | 生産版の刻印違いは D1 が整合し、D2a だけが 1。 |
| M6 | KILLED | genesis の期待値 1 に対する観測値 2 を D2a だけで拒否。 |
| M7 | KILLED | 自分の書き後の古い読みは D2b(i) だけが 1。 |
| M8 | KILLED | 二度書きの V が最初の刻印で、D2b(ii) だけが 1。 |
| M9 | KILLED。ただし証拠として弱い | 比較除去後は `KeyError` によるテスト失敗の見込み。R5。 |
| M10 | KILLED。ただし証拠として弱い | 比較除去後は欠けた path の `KeyError` による失敗の見込み。R5。 |
| M11 | KILLED | 要求あり・gate 全欠落の fixture は到達不能だけが 1。 |
| M12 | KILLED | Q/V が整合する fixture で D5 だけが不成立。 |
| M13 | KILLED | 正常な履歴に `gate_x.log` だけを追加している。 |
| M14 | KILLED | legacy に落ちる履歴の gate 到達不能を期待している。 |
| M15 | KILLED | 要求なし・gate ありの B1 fixture は presence 起動で D1(b1) を検出する。 |

## 正しいと確認した点

D1(a)(b1)(b2) の集合の向き、D2b(i)(ii) の最後の書きとの比較、Q/V の書式と parser の十進・16 桁小文字 hex は、裁定と整合する。gate がなく要求もしない場合は追加投影がなく、`Integrity.clean()` の追加項目も既定値では従前の判定を変えない。U1 の pending は retry 時に破棄され、V は YCSB/v2 の UPDATE の `memcpy` 直前に置かれている。B1 patch の計数は commit した取引単位で、stamp-off patch は二つの `id_` 代入だけを除く。

## 総括

**R1〜R3 を修正するまで受入不可。** 特に R1 は certified の受理集合を広げ、R2 は生死確認の判定を全条件で止める。親が報告済みの D5 emitter 名不一致も合わせて修正が必要。親の 189 passed は承知しているが、本レビューでは build・D297・計算ノード実走・変異本走を行っていない。