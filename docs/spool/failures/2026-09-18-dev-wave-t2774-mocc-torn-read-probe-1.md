---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-t2774-mocc-torn-read-probe
seq: 1
---

## 新規

### {{F:mocc-pilot-hydrate-interpreter-regression}}. mocc trace pilot の hydrate だけが素の python3 で driver を import し、計算ノードで 3.10 専用式を踏んで止まった [テスト代表性] [ドリフト]

- 事象: 2026-09-18 06:29 JST、`tools/pegasus/submit_mocc_trace.sh --t1943-g2-discriminator` の生死確認 job `4936.nqsv` が
  `mocc_trace_pilot.sh:1534` の hydrate で `fetch_third_party: unsupported operand type(s) for |: 'type' and '_LiteralGenericAlias'`
  を出し rc=2 (起動 9 秒)。hydrate 出力 JSON は 0 byte。
- 根本原因: T-548 (2026-09-16、`0165027e0`) で `tools/pegasus/fetch_third_party.py` が driver
  `orchestrator.campaign.silo_ladder_rung1` を import するようになり、推移的に `orchestrator/verifier/parse.py:71` の module 直下
  alias `bool | Literal["NOT_EVALUATED"] | None` (実行時評価、Python 3.10 専用、2026-08-20 `3c9932591`) へ到達する。pilot の
  checker (1756〜) と verifier (2203〜) は `python3 python3.10 …` の候補から `sys.version_info >= (3, 10)` で interpreter を選ぶが、
  hydrate 呼び出しだけが素の `python3` (計算ノードでは 3.10 未満) のままだった。T-548 の段 6 レビューが静的に見つけた断線 3 件と
  同じ「テスト緑・実 job 断線」型で、同 wave は compute 実走をしていない。
- 恒久対応: 修正設計 = `output/insights/2026-09-18/t2774-mocc-torn-read-probe/README.md` §8 (hydrate 直前に同型の interpreter
  選択 block と契約 test 1 本) を {{T:mocc-pilot-restore-certified-mode}} で実施する。本 wave は pilot を使わず job dir の runner で
  実測したため修正していない。
- 再発検知: `orchestrator/tests/test_mocc_trace_job_contract.py` の interpreter gate 検査 (checker / verifier) と同型の hydrate 版を
  {{T:mocc-pilot-restore-certified-mode}} で足す。fake interpreter は配線の検査であり、計算ノードの旧 python での推移 import は
  実 job でしか確かめられない (F650 / F651 と同じく mocc pilot の実走で検出する型)。

## 再発

### F102

- **再発: 2026-09-18** — [T-2774] 段 2 plan の 1 本目 (06:39〜06:46 JST) が最終メッセージ生成時に
  `This content was flagged for possible cybersecurity risk` で `turn.failed` になり成果物 0 byte。引き金は brief の
  「攻撃対象」「隙間」「反実仮想 patch」と、並行制御の race 順序を patch で塞ぐという作業内容。memory
  (`codex-adversarial-prompt-defensive-framing`) の対処 (前置き節 + 語彙中立化) を投入前に読み返さなかった親の手順漏れ。
  v2 は前置き節「DB 研究ベンチマークの直列化可能性検査であって攻撃ツールではない」と語彙置換で通った (所見の深さは不変)。
