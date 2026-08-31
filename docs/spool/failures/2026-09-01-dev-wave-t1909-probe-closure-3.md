---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t1909-probe-closure
seq: 3
---

## 新規

### {{F:symmetric-looking-negative-controls-missed-one}}. 同型に並んだ 3 本の負例のうち 1 本だけ拘束が欠けていた [テスト代表性] [恒真ゲート]

- 事象: 非標本 probe の遮断目録は 3 つの権威点からの逆到達閉包で導く。権威点ごとに
  「その権威点を種から外すと対象が目録から落ちる」負例が 1 本ずつ並んでいたが、
  第一権威点の 1 本だけが**権威点自身の在籍を検査せず**、下流の 1 関数だけを見ていた。
  第一権威点を目録から落とす変異は、この 3 本にも実 producer 直接呼出しの 9 本にも
  証拠 schema 検査にも掛からず生存する。3 本が同型に見えるため、目視では欠落が分からない。
  同じ file で、構成上必ず成立する一致を runtime import 閉包の被覆と称する検査名も見つかった
  ({{D:probe-generation-scope-matches-derivation}} と同じ wave の敵対レビューが検出)。
- 根本原因: 同型に並ぶ検査群を、名前と並びの対称性で「同じ拘束が掛かっている」と読んだ。
  中身の assert を 1 本ずつ照合していない。恒真な検査名の側も、名前が主張する内容と
  assert が実際に測る内容を照合していない。
- 恒久対応: 第一権威点の負例へ、権威点自身が baseline 目録に在ること・種を外すと落ちることの
  assert を足した (`orchestrator/tests/test_p3_b4_wiring_probe.py` の
  `test_anchor_seed_alone_load_bears_pipeline_evaluate`)。恒真な検査は名前と docstring を
  実際に検査している内容へ狭めた。
- 再発検知: 変異事前登録 MWA (`_build_inventory` で第一権威点だけを目録から落とす) を
  KILLED 期待で登録し、修正前 HEAD では SURVIVED になることを同じ wave で実測した。

### {{F:pinned-historical-rollout-vanished-from-shared-sessions}}. repo が pin する過去の codex rollout が共有 sessions ディレクトリから消え、受入が 26 件赤になった [計測汚染] [テスト代表性]

- 事象: [T-1909] wave の受入全走が `19033 passed` の一方で
  `5 failed, 21 errors` を返した。赤 26 件はすべて
  `orchestrator/tests/test_codex_reasoning_ab.py` に集中し、本 wave が 1 度も触っていない
  file である。junit の first line は **3 種**で、内訳は次のとおり (全 26 件を数えた)。
  - 21 件 (error): `failed on setup with "ValidationError: session 019fac6b-4f74-7a03-aa4d-8a9de22b352c rollout count is 0, expected 1"`。`benchmark_snapshots` fixture の setup。
  - 1 件 (failed): 同じ `ValidationError` 本文。`test_m2_production_golden_requires_both_routes`。
  - 4 件 (failed): `FileNotFoundError: [Errno 2] No such file or directory: '/home/SFC/tanab/.codex/sessions/2026/07/29/rollout-2026-07-29T15-49-14-019faca2-6e1f-7601-bfc7-be27edcfb4ba.jsonl'`。
    `test_prompt_replacement_count_zero_expected_and_excess[0]` `[9]` `[10]` と
    `test_real_rollout_collector_golden_is_source_bound`。**POS session を固定の絶対 path で
    直接読む経路**であり、fixture 経由ではない。
  **消えたのは author 1 本ではない。** 現存 7169 rollout を 5 つの期待 SHA すべてで
  全件 hash 照合した結果、POS / NEG / fix2 / author / fix1 のいずれも 0 件だった。
- 根本原因: `tools/codex_reasoning_ab.py` の `_find_rollout` は
  `/home/SFC/tanab/.codex/sessions` を `rollout-*.jsonl` で全走査し、repo が pin した
  session id にちょうど 1 件一致することを要求する。当該 id は `_LEGACY_SESSION_IDS` の
  `author` で、machine 上の rollout 7120 件のどれとも一致しない。
  **repo の pin が、repo の外にある共有ディレクトリの実体に依存している。**
  同ディレクトリは 2026-08-01 以降しか持たず、pin された session はそれより古い。
- 恒久対応: 本 wave では未実施。修理は並行セッションへ一本化された。本 wave は編集面の衝突を
  避けるため `tools/codex_reasoning_ab.py`・`orchestrator/tests/test_codex_reasoning_ab.py`・
  `orchestrator/tests/flaky_test_holds.py` に触れない。
  **hold 登録は構造的に不可能である** — `orchestrator/tests/flaky_test_holds.py` は
  `green_observation` の非空 (115 行) と `green_run_count >= 1` (135-139 行) を必須とし、
  この 26 件は素材消失後に一度も緑になっていない。
  **復元も不成立である** — rollout の bytes は `~/.codex/sessions`、
  `~/.codex/thread_history_1.sqlite` (当該 thread の行は全テーブル 0)、repo、job dir、
  home のいずれにも存在しない。
  D1144 に従い wave は停止せず、land 以外を完了して修正の着地を待つ。
  本エントリは恒久対応を持つ主体へ一次資料を渡すためのものである。
- 再発検知: 赤の本文が `rollout count is 0, expected 1` または
  `~/.codex/sessions` 配下への `FileNotFoundError` を含むなら本件型である。
  **2 経路あることに注意する** — fixture 経由の閉包解決と、POS session を固定の絶対 path で
  直接読む経路で、後者は fixture を直しても掛からない。
  **後者の path 束縛は 2026-09-01 の修理でも解けていない** — 固定の絶対 path のまま
  `is_file()` で条件化されただけで、corpus が別の場所に在る環境では依然として成立しない。
  hermetic 化 (`CODEX_HOME` の引数化) は恒久対応へ持ち越された。
  `find /home/SFC/tanab/.codex/sessions -name 'rollout-*.jsonl' | wc -l` で母集合を数え、
  `tools/codex_reasoning_ab.py` の `_LEGACY_SESSION_IDS` と `SESSION_IDS` の各 id が
  何件一致するかを個別に数える。0 件の id が本件の対象である。
- 補足: 決定的な赤である。単独再走 (`test_codex_reasoning_ab.py` だけ) でも同じ 26 件が
  同じ本文で再現し、**独立 clone 上の local main 単独でも同一の 26 件が同一本文で再現した**
  (5 failed / 598 passed / 2 skipped / 21 errors)。F189 のとおり複製 checkout の走行は
  環境差で赤くなりうるが、本件は本文が worktree 走行と完全に一致するため checkout 依存ではない。
- 補足: **壊れた時刻を挟み込めた。** 緑だった直近の受入受領証は 2026-09-01 00:49:31
  (`verdict=child-green` / `red_nodeids=[]` / argv `['python3','tools/run_tests.py']`)。
  `/home/SFC/tanab/.codex/sessions/2026` の mtime は同日 00:54:20 で、`2026/09` は
  00:00:13 に作成済みなので、00:54 の更新は entry の削除を指す。本件の赤は 01:30 頃である。
- 補足: **これは事故ではなく運用である。** home の会話ログは容量制限のため定期的に削除される。
  剪定窓は実測で約 32-34 日 (pin は 5 件とも 2026-07-29、現存の最古は 2026-08-01)。
  **次の境界では `2026/08/01` の 173 件が落ちる。** 同型の pin が他にあれば同じ壊れ方をする。
  復元も、消える場所への pin 張り替えも、同じ窓に繰り返し轢かれる。
- 補足: **hold の循環は既知である。** wave の fragment が land まで canonical F にならない
  構造的循環は F766 に記録済みで、D1160 が placeholder 契約を裁定しているが、
  `orchestrator/tests/flaky_test_holds.py` の現行 regex は未実装である。
  したがって本件で循環を断てるのは、exact node 名と各 failure signature を持つ F を
  別の先行 wave が canonical main へ先に land する経路だけである。
