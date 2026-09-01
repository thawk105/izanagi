---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t1946-t2107-registry-proof-wiring
seq: 2
---

## 新規

### {{F:dispatching-check-orphaned-by-foreground-timeout}}. 親が走らせた検査が計算ノードへ投入するものだと知らず、既定 timeout で殺して worktree の全投入を止めた [手順漏れ]

- 事象: `DW-O17` に従い ff-only merge の後で `python3 tools/check_ai_provenance.py` を実行した。
  この検査は内部で計算ノードへ job を投入する。Bash tool の既定 timeout (2 分) で
  ラッパーだけが SIGTERM され、投入した job (`964324.nqsv`) が終端証拠なしのまま残った。
  dispatch 層は `output/pegasus-dispatch/orphan-hold.json` と
  `output/pegasus-dispatch/orphan-holds/964324.nqsv.json` を作り、
  **以後この worktree からの全投入が `rc=16` / `reason=orphan-hold` で拒否**されるようになった。
  受入全走も同じ経路を使うため、気づかなければ wave 全体が止まる。
- 根本原因: (a) 親が「自分で走らせる検査は local 実行」と仮定し、
  投入を伴う検査を短い timeout つきで前面実行した。既存の memory
  `never-wrap-detached-launch-in-timeout` は背景投入だけを対象にしており、
  **親が前面で走らせる検査も投入経路でありうる**ことは既存のどの節にも書かれていなかった。
  (b) 復旧手順が不十分。hold file 自身の `recovery.final-step` は
  「source の clean/HEAD を確認した後だけ hold を手動削除する」と書き、
  エラー文も aggregate marker (`orphan-hold.json`) の path だけを名指しする。
  しかし gate は `orphan-holds/` に entry が 1 件でもあれば成立する
  (`tools/pegasus/dispatch_compute.py` の `_orphan_hold_*`)。
  aggregate marker だけを消しても解けず、消したつもりで再投入して同じ `rc=16` を見ることになる。
- 恒久対応: memory `never-wrap-detached-launch-in-timeout` に前面実行の節を追記した
  (呼び出し側の規律 — 投入を伴いうる検査は背景で走らせ、短い timeout で包まない)。
  復旧手順は本エントリの「再発検知」に置く。検査側の是正
  (エラー文が両方の path を名指しする、または gate と marker の対応を 1 つにする) は
  本 wave の編集面の外なので裁定へ返す。
- 再発検知: 投入が `IZANAGI_DISPATCH_OUTCOME_V1 {"kind":"infra","reason":"orphan-hold"}` を返したら、
  (1) `qstat -J -f <request_id>` で対象 job の不在または終端を確認し、
  (2) `git status --porcelain` で作業ツリーの clean を確認し、
  (3) `orphan-hold.json` **と** `orphan-holds/<request_id>.json` の**両方**を削除する。
  削除前に hold の内容を repo 外へ退避して証拠を残す。
  job が生存中なら削除せず終端を待つ。手動 `qdel` は F47 の submission-disabled を武装させるので使わない。

## 再発

### F606

- **再発: 2026-09-01** — 段 1 の編集面重複走査を、(i) 大分類の名前 pattern と
  (ii) `git diff --name-only main...HEAD` + `git status --porcelain` だけで組み、
  45 worktree に対して **0 件**と結論して brief に書いた。段 3 の両レンズが独立に
  「走査面と証跡が無く再現不能」と指摘した。exact path 集合 + staged + untracked で
  走査し直したところ**実際は 3 件**あり
  (`worktree-dev-wave-t2027-root-class2` が `orchestrator/campaign/s8b_floor_campaign.py`、
  `worktree-dev-wave-t2074-a1-estimand-realign` と `impl-dev-wave-t2074-fix2` が
  `orchestrator/tests/test_s8b_floor_campaign.py`)、brief を訂正した。
  型は F606 と同じ「走査の網が実際の編集予約より狭い」だが、本件が足す軸は 2 つある。
  1 つ目は **snapshot の陳腐化** — 初回走査から裁定までの間に local main が 2 回進み、
  worktree が 43 本から 45 本へ入れ替わったため、走査時点の 0 件が裁定時点の 0 件ではなくなった。
  2 つ目は **証跡の不在** — 件数だけを brief に書き、走査時刻・main head・各 worktree の
  head/base・exact path 集合を残さなかったため、第三者が再現できなかった。
  恒久対応は F606 既存の「落ちた面は『無い』と書かず、走査面を明示して限定した結論を書く」で
  変わらない。運用としては、走査結果を固定 artifact
  (`output/insights/2026-09-01_t1946-t2107-registry-wiring-design/overlap-scan.txt`) として残し、
  実装子 dispatch の直前に走査し直す。
