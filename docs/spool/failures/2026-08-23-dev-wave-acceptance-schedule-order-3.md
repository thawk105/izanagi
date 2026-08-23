---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-23
wave: dev-wave-acceptance-schedule-order
seq: 3
---

## 新規

### {{F:silent-key-mismatch-noop}}. 生産側と消費側の key がずれても赤にならず機構が静かに無効化される [恒真ゲート] [自己整合]

- 事象: 受入の投入順を決める所要台帳で、生成側 (junit の `classname` から nodeid を復元) と
  消費側 (`item.path` から nodeid を復元) が**別々の規則で同じ key を作っていた**。
  規則がずれると台帳の全 key が未知になり、並べ替えが no-op へ落ちる。
  **これは例外も赤も出さない。** 段 6 の敵対レビューが指摘するまで誰も気づかなかった。
- 根本原因: 新設した 26 個の gate のうち、消費側を検査するものが
  **期待値を消費側の関数そのもので生成していた**。自己整合なので両側がずれても全部緑になる。
  生成側 -> 実 collection -> 消費側 の round-trip を通す gate が 1 つも無かった。
- 恒久対応: **実台帳と実 collection の被覆率を測る gate** を置いた。
  repo にある実台帳を読み、実 collection の nodeid を消費側の規則で key へ変換し、
  被覆率が 90% 未満なら赤にする。期待値を消費側の関数から導かない。
  閾値の根拠は 14457 / 14663 = 98.6% (実測) と、欠落 10% でも makespan が
  111.9 対 111.8 秒で実質同等という頑健性実測。
- 再発検知: 消費側の key 生成を壊す変異 (`@group` suffix を落とさない) がこの gate で落ちること。
  この gate は**台帳の陳腐化を検知する運用 gate も兼ねる**。
- 一般化: **producer と consumer が独立に同じ識別子を組み立てる設計では、
  consumer 側の gate を consumer 側の関数で書くと必ず自己整合になる。**
  片側の実データを固定して round-trip を通す gate が要る。

### {{F:lpt-sync-window}}. 未知要素を先頭へ寄せると LPT の利得が消える [性能] [模型の誤り]

- 事象: 所要降順の並べ替えで、台帳に無い unit を「安全側」として先頭へ寄せたところ、
  欠落 1.3% で makespan が 111.8 秒から 166.2 秒へ悪化した。実既定の 155.3 秒より遅い。
- 根本原因: xdist の `LoadScopeScheduling.schedule()` は各 node へ 1 unit を配り、
  続けて `_reschedule()` でもう 1 unit を配る。**先頭 96 unit (= 48 x 2) だけが
  同期して 1 台 1 本ずつ配られる。** それ以降は worker が非同期に取りに来るため、
  重い unit が窓の外に押し出されると 1 台が連続で抱え込む。
  実測では 1 worker が 81.66 + 60.17 + 60.17 = 202 秒を直列に抱え、
  最速 worker は 109.5 秒で遊んだ。
- 恒久対応: 未知 unit の擬似 cost を「既知の cost 降順の第 96 位」にした
  ({{D:acceptance-duration-order}})。欠落 30% まで実既定より速い。
- 再発検知: 未知既定を先頭 (`inf`) や 0 (末尾) へ戻す変異が gate で落ちること。
- 一般化: **greedy list scheduling の利得は「重い job が同期配布窓に入る」ことに依存する。**
  「未知は安全側へ」という直感は、窓の位置を無視すると逆効果になる。

### {{F:invariant-overclaimed-as-outcome}}. fail-soft の不変条件を outcome 不変まで広げて書いてしまった [裁定] [過大主張]

- 事象: 段 1 の brief で不変条件を「台帳の障害は順序の質だけを落とし、
  選択・skip・受理判定・receipt を 1 件も変えない」と書いた。この文は
  「順序を変えても outcome は変わらない」まで含むように読める。
  段 6 の敵対レビューが、module scope fixture の finalizer や `tmp_path_factory` の連番で
  **順序差だけで緑と赤が入れ替わる**具体構成を示した。
- 根本原因: 「台帳の障害に対する不変性」と「順序変更に対する不変性」は別の主張なのに、
  1 文へまとめた。後者は順序依存のテストがある限り一般には成立しない。
- 恒久対応: 不変条件を 2 つに分けた。(2a) 台帳の障害は順序の質だけを変える (成立・gate 済み)。
  (2b) 順序非依存は本 repo の受入が既に要求している前提であり、
  本 wave が持ち込んだものではない (`-n 48` で 48 worker へ任意に散らされ、
  xdist 自身も既定で件数降順に並べ替えている)。
- 再発検知: 受入全走を決定的な検査とする。赤が出たら順序依存の実在として停止し、
  テストを緩めて緑にしない。
- 一般化: **「X の障害に対する不変性」を「X が変える対象に対する不変性」と混ぜて書かない。**
  gate は前者しか pin できない。

### {{F:background-job-waiter-reaped}}. 背景 job では待ち手も監視も「完了した」と嘘をつく [待ち手] [通知]

- 事象: 背景 job で回した dev-wave で、子の完了待ちが**成果物なしで成功を返す**事象を
  4 回踏んだ。内訳は `tools/dev_wave_wait.py producer` が 2 回 (どちらも出力ゼロ・rc=0・約 7 分)、
  Claude harness の Monitor が 2 回 (`.done` が存在しないのに `DONE rc=0` を通知)。
  いずれも producer (launcher bash / `dev_wave_codex.py` / `codex exec`) は 3 段とも生きていた。
- 根本原因: `wait_for_producer` は pid 状態を poll し `.done` と artifact が揃うまで
  `RC_OK` を返さない構造なので、**tool の欠陥ではなく外側が待ち手 process を回収している**。
  背景 job の harness が turn を跨ぐ background 実行を reap するのが最有力だが未確定。
  Monitor の誤報は原因未特定で、こちらは通知経路そのものが信用できない。
- 恒久対応: **なし (既存契約で足りている)。** `DW-O01` の
  「完了は `.done` と exit code だけで判定し、grep も通知も判定にしない」に従っていたので
  4 回とも現物照合で救えた。**この規律は「通知が先行しうる」だけでなく
  「通知が偽でありうる」場合にも効く**ことが実地で確かめられた。
- 再発検知: 完了通知を受けたら必ず `.done` の実在と内容、artifact の bytes を現物で確認する。
  確認せずに次段へ進むと、走行中の子の tree を壊す。
- 一般化: **背景 job では「待ち手の rc」も「完了通知」も完了の証拠にならない。**
  producer が書く成果物だけが証拠である。長い待ちは前景 block を分割して張るのが最も確実。

### {{F:pytester-usersite-home}}. `pytester` の `HOME` 差し替えが user site の pytest を見えなくする [環境] [偽赤]

- 事象: 新設した live gate 11 件が全滅した。内側 subprocess が
  `/usr/bin/python3: No module named pytest` で即死していた。
- 根本原因: `pytester` は inner run のために `HOME` を tmp directory へ差し替える。
  この機体の pytest は **user site** (`$HOME/.local/lib/python3.10/site-packages`) にあるため、
  `HOME` が変わると解決できなくなる。修正して pytest が入るようになると、今度は
  repo root が `sys.path` に無く `No module named 'orchestrator'` になった。
- 恒久対応: `pytester` の subprocess を起動する前に、`PYTHONPATH` へ
  **user site と repo root の両方**を前置する (既存値は保つ)。
  `runpytest_inprocess` へ逃げると production の hook chain と worker 側 wiring を通せない。
- 再発検知: live gate が緑であること自体。**静的レビューでは検出できない**ので、
  `DW-O16` の「実行環境に依存する実装は実機で動かすまで closed にしない」に従う。
- 一般化: **user site へ導入した interpreter 資材は、`HOME` を差し替える test harness から見えない。**
  `pytester`・`tmp_path` を使う subprocess test は、この機体では `PYTHONPATH` の明示が要る。

### {{F:mutation-runner-mode-coupling}}. 変異 harness の `--runner-mode dispatch` は login node の余裕で壊れる [変異] [argv]

- 事象: 変異 probe は `--runner-mode dispatch` で 12/12 走完走したが、直後の本走は
  `baseline が緑でないため production write を開始しない: status=PARSE_ERROR` で止まった。
  attempt sidecar には `artifact_error: receipt 表示行が exactly one でない: 0` と rc=0 が残っていた。
  **テストは通っているのに、dispatch receipt が 1 行も無い**ため harness が parse できなかった。
- 根本原因: `tools/run_tests.py` は §7.0.0 の自動判定で local と dispatch を選ぶ。
  login node に余裕があると local を選び、dispatch receipt 行を出さない。
  一方 `--runner-mode dispatch` は毎走に receipt 行が exactly one あることを要求する。
  **同じ argv・同じ tip でも、login node の空きメモリ次第で走行形が変わる。**
- 恒久対応: `--runner-mode local` へ切り替える。harness は runner を黒箱として扱い、
  `run_tests.py` が内部で必要なら dispatch する。
  ただし `--attempt-out` / `--wrapper-attempt` は **`dispatch` 専用**なので同時に外す
  (`attempt sidecar は --runner-mode dispatch でのみ使用できる`)。
- 再発検知: probe が dispatch mode で通っても本走が同じ mode で通るとは限らない。
  **probe と本走は同じ mode でも別の走行形になりうる。**
- 一般化: 走行形 (local / dispatch) を自動判定する runner を、走行形を要求する harness へ
  渡すと、環境の空き次第で間欠的に落ちる。**判定するのは runner か harness のどちらか一方にする。**
