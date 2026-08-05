---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-06
wave: dev-wave-t503-liveness
seq: 3
---

## 新規

### {{F:t503-probe-realmachine-mismatch}}. 実機の外部書式と防壁を机上で仮定し、実験 leg を 3 度空振りさせた [手順漏れ] [テスト代表性]

- 事象: 生死確認 probe の実走で、机上レビューを通過した実装が実機で 3 回止まった。
  (1) 検査・修復を login ノードで走らせる段 1 の前提が `hooks/guard_bash.py` に拒否され、
  修復側 PBS を追加実装するまで leg が 1 本も完走しなかった。
  (2) NQSV accounting の見出しを `PBS request ID` と仮定したが実際は `Request ID:` であり、
  `PBS_JOBID` も `0:` 接頭辞付きで accounting 側と文字列一致せず、walltime leg が
  `scheduler terminal accounting is invalid` で隔離された。
  (3) 修復 job が writer より先に起動すると、`ready` を 300 秒待つ設計でありながら
  その手前の `realpath -e` で即死し、2 job が成果物ゼロで終わった。
- 根本原因: 外部権威 (scheduler の出力書式、機械防壁の許可集合) に依存する述語と手順を、
  **実データを 1 件も採らずに**書いた。3 件とも fail-closed 側に倒れたため被害は空振りに
  留まったが、いずれも実走するまで検出できなかった。
- 恒久対応: {{D:liveness-probe-single-commit}} と併せ、`docs/dev-wave/core.md` の
  `DW-S01` が既に要求する「別 program を起動する成果物では build・環境変数・外部 command と
  注入 seam の実在を棚卸しする」を、**外部出力の書式そのもの**まで及ぶものとして適用する。
  実データ 1 件を採取してから述語を書く。
- 再発検知: 外部書式に依存する述語は、その書式の**実採取物**を逐語で pin する負例テストを
  同じ commit に置く (本 wave では `test_scheduler_evidence_accepts_nqsv_accounting_format` と
  拒否 8 種)。逐語 pin の無い外部書式述語をレビューの must-fix 対象にする。
