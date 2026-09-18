---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-t2724-t080-defer-active-v2
seq: 2
---

## 新規

### {{F:long-reader-registration-starves-real-repo-gate}}. 約 3 分の fixture 構築を持つ新 test 9 node を real-repo reader に登録したら、read lock の長期保持で他 reader が lock deadline を超え xdist worker が落ちた [テスト代表性] [計測汚染]

- 事象: [T-2724] 整合 wave の段 6 で、接続 fixture (T-080 発行済み履歴 + G / A / X を積む、1 node 約 150〜210 秒) を持つ新 test 9 node (接続 8 + draft 負例 1) を conftest の `_REAL_REPO_BOTH_READER_NODES` に登録した (段 6 レビュー RB-6 の「実 root を読む test は登録する」に従った)。chain 有り木の焦点走 (7 file、request 5649、2026-09-18 13:02〜13:11) で xdist worker が `RuntimeError: real-repo lock deadline exceeded; fails-closed: resource=ccbench mode=read` (conftest `_REAL_REPO_LOCK_TIMEOUT_S` = 245 秒) の INTERNALERROR になり、`test_cli_subprocess_returns_rc_2_on_gate_refused` が crashitem として落ちた (1088 passed / 2 failed / 7 skipped で走が中断)。実害なし (land 前)。
- 根本原因: 登録された node は test 全体の間 read lock (LOCK_SH) を保持する。ccbench の writer node が gate を握って全 reader の解放を待つ間、後続の reader は gate で 245 秒を超えて待ち、deadline で fail-closed になる。既存の stub-free T-080 e2e 10 node (各約 200 秒) は `_T080SharedBases` で session に 1 回だけ base を組み、各 test はその copy を使うので登録されておらず、この経路を通らない。「実 root を読む test は登録する」は正しいが、**長時間の test をそのまま登録すると lock の保持時間が gate の deadline を食う**。
- 恒久対応: copy後の親rootへのfallbackをfix-4で除去し、`build_production_emitter_g1`のreceipt接続分岐はcopy内の材料だけを読む。登録簿は既存stub-free e2eと同じ未登録へ戻し、`root=ROOT`を直接渡すseam負例だけ保持する。base構築自体の親root読取りと完全排他の残余は保持する。解消根拠はfix-5後の焦点走（5698: 1211 passed / 12 skipped、5699: 1104 passed / 11 skipped）と回収時の独立静的監査2本 `output/insights/2026-09-18/t2724-t080-defer-active-v2/verbatim/recovery-review-A.md` / `recovery-review-B.md`。旧`s6-rereview.md`のRR-1は修正前NO-GOであり、解消証拠ではない。
- 再発検知: 既存のcopy内材料欠落7条件の負例とreal-repo serialization検査、焦点走のlock deadline/INTERNALERRORを確認する。一般的な所要閾値や新しいgateは設けない。

## 再発

### F106

- **再発: 2026-09-18** — [T-2724] 整合 wave の親が、wave worktree から投入した焦点走 (`focus-nochain-6`、bounded local) の走行中に、同 worktree へ insight の verbatim file 5 本を書いた。bounded local が MemoryMax に達して計算ノードへ再 dispatch する前の tree 状態検査が「local 試行の前後で tree / submodule 状態が変化」で止まり rc=16、走が 1 本無効になった (実害 = 再走 1 本、約 8 分)。恒久対応は F106 のまま。本 wave の親は同日中に前回 (fix-1 の統合前) は守れていたが、fix-4 の統合後に「待ち時間に段 7 を進める」誘因で踏んだ。

### F100

- **再発: 2026-09-18** (同日 3 回目、near miss、実害なし) — [T-2724] 整合 wave の親が `cd <Codex author worktree> && python3 tools/dev_wave_codex.py … --dry-run` (読み取りだけ) を打ち、harness の追跡 cwd が author worktree へ移った。`EnterWorktree --path <自分の wave worktree>` で即復帰。以後の dry-run は `cd` を前置せず絶対 path で打った。書き込みは発生していない。

### F945

- **再発: 2026-09-18** — T-2724/T-2776回収tip `d899c86aa` の受入shard0（6425.nqsv）で、T-1259のmodule fixtureが `git ls-files --others --exclude-standard -z` の30秒TimeoutExpiredとなり12 setup errors。全体は25153 passed / 69 skipped。test本体に入る前で、当該test/probeには今回の差分がない。正規runnerの同tip単独走でも51 setup errors（247.47秒）を再現したため、DW-O18に従い受入2を投入せず停止した。timeout/hold/除外は変更せず、T-2790の既存の設計・検証手番に範囲を残す。一次資料は `output/insights/2026-09-18/t2724-t080-defer-active-v2/README.md` の停止記録と回収jobの生log。
