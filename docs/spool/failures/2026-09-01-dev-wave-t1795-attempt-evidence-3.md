---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t1795-attempt-evidence
seq: 3
---

## 再発

### F20

- **再発: 2026-09-01** — 揮発領域に唯一コピーがある成果物を、今度は**恒久の検査入力として
  設計に組み込んだ**。`tools/codex_reasoning_ab.py:196-209` が `~/.codex/sessions` 配下の
  過去 session 5 件を ID と SHA-256 で pin し、`orchestrator/tests/test_codex_reasoning_ab.py` が
  後日それを読む。pin 先は全て 2026-07-29 のもので、実測時点で `~/.codex/sessions/2026/07/` が
  丸ごと存在しない (現存は `2026/08/01` 以降、同 root に rollout は 7138 件)。`~/.codex` 配下に
  退避も無く復元不能で、並行する 4 セッションが独立に全探索して 0 件だった。結果、受入全走が
  同 file の 26 node (5 failed + 21 error) で赤になり、現行 main
  (`24014bdb259d971571f22b54a8f10a49352b825f`) 単独でも同じ内訳が再現した。受入が緑にならない
  間は `tools/dev_wave_land.py` が受領証を発行せず、**この機体の全 wave が land できなかった**。
  **本エントリの事象本文は 2026-07-16 時点で既に `~/.codex/sessions` を「探したが不在だった」
  領域として挙げている。** 非永続だと分かっていた領域を、2 週間後に恒久の gate 入力として pin
  したことになる。**深刻度は本体より上がっている** — 本体は永続化の判断を次セッションへ
  繰り延べたものだが、今回は繰り延べですらなく、揮発領域への依存を設計として固定した。
  **被覆の喪失はこの機体では恒久である。** 会話ログはストレージ上限のため定期的に削除される
  運用であり (2026-09-01 に中継されたユーザー指示)、同じ pin は今後も落ちる。消えた 26 node は
  「緑になった」のではなく「実行されていない」。受入 receipt は skip node ID を保持せず red と
  flake だけを持つため (`tools/dev_wave_land.py:102-130`、`tools/task_runs/pytest_stats.py:18-20`)、
  総数だけを見ると通ったように読める。独立相談が file:line で確認したとおり失われる検出力は
  実在し、2026-07-29 の実 corpus そのもの、独立 golden 二経路の実 patch 合成、実 prompt の
  置換数、実 snapshot から完全 replay までの結合被覆に完全な代替は無く、登録済みの
  M1 / M2 / M3 mutation killer も止まる。合成 fixture 側
  (`orchestrator/tests/test_codex_reasoning_ab.py:7154-8010`、`:8366-8491`) に部分的な代替はある。
  当座の対応は別の単独 wave が担い、同 file の可用性判定を実依存の粒度へ直す。述語は
  「`rollout-*-<escaped session id>.jsonl` の候補が 0 件のときだけ skip」に限定し、候補が存在するのに
  SHA 不一致・malformed・session 所有不一致・重複・読取不能なものは従来どおり赤のままにする。
  既存 guard は root directory の有無という粗い粒度
  (`orchestrator/tests/test_codex_reasoning_ab.py:788-790`) で、実際の依存である特定 5 session を
  捉えられなかった。**本エントリの `再発検知` 欄は「再発時に機械化を再検討」と事前に登録して
  おり、今回がその再発である。** 結果を見てから条件を作ったのではなく、条件が先に書かれていた。
  本体が機械 lint を見送った理由は「唯一コピーか」の意味判定が要り恒真化するというものだったが、
  **今回の型はもっと狭く意味判定を要さない** — 「同一性 (ID や SHA-256) を pin する対象の root が
  非永続領域か」は静的に判定でき、現行の `_LEGACY_ROLLOUT_SHA256` の pin がそのまま正例として
  発火するので恒真にもならない。ただし単純な「非永続 path の禁止」へ広げると
  `tools/codex_worker_ledger.py:153-168` のような正当な走査経路まで拾うので pin との連結が要る。
  **この機械化は本再発の時点では未実装であり、対応済みとして数えない。** 射程の棚卸しでは、
  tracked な実行コードと test を `git grep` で走査した範囲に同型の経路は当該 2 file 以外に無く、
  repo 外・untracked・ignored file は未検査である。
