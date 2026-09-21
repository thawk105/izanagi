---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-21
wave: dev-wave-t2795-k2-pair-repair
seq: 1
---

## 再発

### F1019

- **恒久対応の一部を実施 (2026-09-21)** — K2 同 job pair launcher と one-shot claim の整合を driver 設計で直し ({{D:k2-pair-authorization-session}})、
  **認可 / claim 結合の再発検査**を追加した: site `PEGASUS_COMPUTE`・`ec.lookup("pegasus")` (`single_process=True`)・実 reservation・実 `campaign_claim.acquire_claim`・
  実 layout / campaign lock / WAL / `pipeline.evaluate` を `p3_s4_loop.main()` から通し、候補 `certified` → stock `certified-stock`・rc 0・同一 WAL に両 variant の
  BUILD_START / BUILD_DONE / VERIFY_DONE / BENCH_DONE / COMMIT・`acquire_claim` 1 回・claim record 不変・候補 checkpoint 不変を固定する。
  負例は「session 無しの 2 回目が `ClaimError`」「pair × B-5 / B-4 / value / emit / no-build の rc=2」「候補の検疫 reject 後も stock が初回 claim を取り測定へ到達」
  「候補の認可後例外でも stock 測定・claim 取得 1 回・候補例外の再送出」「job body は driver 1 起動」「fixture + stock は rc=2」。
  **未実施の範囲を明記する: 実 compiler による STOCK 成立、実 checkout / patch と実 build の統合、Pegasus production の pair 1 走。**
  代用しているのは build・trace 実行・bench・attestation の観測・condition gate・patch 適用・checkout・compiler 依存の SourceEvidence・perf preflight であり、
  この結合検査の緑は「stock 対照が成立した」ことを意味しない。production 1 走はユーザーの予算再提示 (D2172 項 3) が前提で本 wave では投入していない。
- **併せて判明した検査条件 (2026-09-21 実測)** — `orchestrator/campaign/loop.py` と `orchestrator/campaign/p3_s4_loop.py` は `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS`
  (85 path) に含まれ、環境契約付きの v2 campaign lock を作る経路は `contract_loader_binding.capture_contract_loader_binding()` で **live bytes = HEAD blob** を要求する。
  変異 harness は固定 HEAD へ bytes を注入するため、この 2 file を変異させると「変異の内容と無関係に」lock を作る test が `contract-loader-drift` で落ちる。
  等価変異 (comment 1 行) の probe で該当 node を実測し (114 node: `test_p3_s4_loop.py` 81 / `test_campaign.py` 33)、変異走行ではこれを `--deselect` して帰属を保った。
  同 file 群を変異させる後続 wave は、同じ手順 (等価変異で drift 集合を実測 → 除外) を取るか、commit 済み状態で走らせる probe に切り替える必要がある。
