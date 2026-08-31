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
  file である。junit の本文はいずれも
  `ValidationError: session 019fac6b-4f74-7a03-aa4d-8a9de22b352c rollout count is 0, expected 1`
  で、`benchmark_snapshots` fixture の setup で落ちる。
- 根本原因: `tools/codex_reasoning_ab.py` の `_find_rollout` は
  `/home/SFC/tanab/.codex/sessions` を `rollout-*.jsonl` で全走査し、repo が pin した
  session id にちょうど 1 件一致することを要求する。当該 id は `_LEGACY_SESSION_IDS` の
  `author` で、machine 上の rollout 7120 件のどれとも一致しない。
  **repo の pin が、repo の外にある共有ディレクトリの実体に依存している。**
  同ディレクトリは 2026-08-01 以降しか持たず、pin された session はそれより古い。
- 恒久対応: 未実施。**この wave では修理していない。** 直し方は repo の外にある実体の復元か
  pin の張り替えのいずれかで、どちらも本 wave の scope の外にある。
  `DW-O18` は「main 既存 F を証拠に hold 登録」を求めるが本件の F は存在しなかったため、
  同節に従い hold を登録せず裁定へ送って停止した。本エントリはその F を残すためのものである。
- 再発検知: 赤の本文が `rollout count is 0, expected 1` を含むなら本件型である。
  `find /home/SFC/tanab/.codex/sessions -name 'rollout-*.jsonl' | wc -l` で母集合を数え、
  `tools/codex_reasoning_ab.py` の `_LEGACY_SESSION_IDS` と `SESSION_IDS` の各 id が
  何件一致するかを個別に数える。0 件の id が本件の対象である。
- 補足: 決定的な赤である。単独再走 (`test_codex_reasoning_ab.py` だけ) でも同じ 26 件が
  同じ本文で再現し、**独立 clone 上の local main 単独でも同一の 26 件が同一本文で再現した**
  (5 failed / 598 passed / 2 skipped / 21 errors)。F189 のとおり複製 checkout の走行は
  環境差で赤くなりうるが、本件は本文が worktree 走行と完全に一致するため checkout 依存ではない。
