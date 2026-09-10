結論は **NO-GO** です。実コード側の 3 理由は閉じていますが、変異証拠 `new-3` が partial のままです。

## 再判定表

| 理由 | 判定 | 独立照合結果 |
|---|---|---|
| new-1 official 過剰拒否 | **closed** | official policy は no-op（[layout.py:201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:201)）、exploration は container gate（[layout.py:467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:467)）。append・repair・write_lock・acquire_lock_atomic の全4経路が policy を呼ぶ（[wal.py:310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/wal.py:310)、[wal.py:471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/wal.py:471)、[wal.py:783](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/wal.py:783)、[wal.py:808](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/wal.py:808)）。official 正例は4経路とも実際の file/receipt bytes を検査する（[test_campaign.py:3993](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_campaign.py:3993)）。 |
| new-2 8c pin 迂回 | **closed** | 8c の env 存在判定は消え、省略時は常に resolver を呼ぶ（[p3_autonomous_workload_trial.py:1758](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:1758)）。env 読取・pin 照合・legacy 返却は同じ lock 内（[layout.py:298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:298)）。env 未設定＋pinなしは `legacy_base`、pinありは `ValueError`（[layout.py:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:301)）。reset なし env 削除負例も実在する（[test_campaign.py:3774](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_campaign.py:3774)）。 |
| A-5 残存 materializer | **closed** | repair は WAL open/receipt/truncate より前（[wal.py:469](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/wal.py:469)）、namespace は mkdir/marker より前（[layout.py:375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:375)）に gate。負例はそれぞれ [test_campaign.py:4031](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_campaign.py:4031)、[test_campaign.py:4048](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_campaign.py:4048)。grep 棚卸し上、exploration の直接 digest writer も `ensure()` または先行 `run_campaign` 後にしか到達しない。8c も最初の mkdir 前に gate 済み（[p3_autonomous_workload_trial.py:1587](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:1587)）。 |
| new-3 変異証拠 | **partial** | 8 spec の SHA-256 は manifest と一致し、13 anchor はすべて現コードに逐語 1 件。登録済み13変異はすべて期待 node 単独で静的 KILL 見込み、明白な等価変異もない。しかし、初回 NO-GO が指摘した post-resolve walk と複数 WAL call-site の独立証明が manifest から落ちている。 |

`getattr(..., default no-op)` について、実 `ExplorationCampaignLayout` は必ず method を持ちます。production の `CampaignLayout` 再包装箇所は、8c の先行 run-root gate や各 loop の先行 `ensure()` 後です。現行 production caller に、実 exploration object が fallback no-op へ落ちる経路は見つかりませんでした。

## 13変異の静的判定

全 spec の `old` anchor は現コードで **1/1**、manifest の各 runner node と spec の `expected_nodes` も一致します。

| 変異 | 単一 node での判定 |
|---|---|
| M01 | **KILLED 見込み** — env root が repo 既定へ変わり precedence assertion が赤。非等価。 |
| M02 | **KILLED 見込み** — env=`""` 時の明示 root 優先が失われる。非等価。 |
| M03 | **KILLED 見込み** — 空文字が拒否されず最初の不正値 case が赤。非等価。 |
| M04 | **KILLED 見込み** — repo ancestor が受理される。非等価。 |
| M05 | **KILLED 見込み** — lstat helper 全体を無効化し、既存 symlink fixture が赤。非等価。ただし post-resolve 単独の検出力は証明しない。 |
| M06 | **KILLED 見込み** — container detector 全体が無効化され、wave-local output が作成される。非等価。 |
| M07 | **KILLED 見込み** — 8c env root が無視され、捕捉 run_root が不一致。非等価。 |
| M08 | **KILLED 見込み** — `..` 入力が受理される。非等価。ただし初回レビュー時の「post-resolve walk 除去」とは別変異へ差し替わっている。 |
| M09 | **KILLED 見込み** — write_lock が最初の materializer case で作成に成功する。非等価。ただし append/acquire は未変異。 |
| M10 | **KILLED 見込み** — 8c legacy base が空になり旧既定文字列と不一致。非等価。 |
| M11 | **KILLED 見込み** — repair が container を拒否せず `missing` を返す。非等価。 |
| M12 | **KILLED 見込み** — namespace directory/marker が作成される。非等価。 |
| M13 | **KILLED 見込み** — pin が保存されず drift が受理される。非等価。env削除時の既存-pin guard 自体は未変異。 |

## 残存所見

### MF-1 — 変異 matrix が初回 NO-GO の対象防壁を取りこぼす

- 深刻度: **統合前 blocker**
- post-resolve walk は [layout.py:327](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:327) に残る一方、M05 は helper 全体、M08 は `..` guard を変異するだけです（[mutation-spec-g2-admission.json:40](/work/1/SFC/tanab/dev-wave-jobs/t422-campaign-external-root/mutation-spec-g2-admission.json:40)、[同:56](/work/1/SFC/tanab/dev-wave-jobs/t422-campaign-external-root/mutation-spec-g2-admission.json:56)）。post-resolve loop だけを除去しても、現 symlink fixture は pre-resolve walk で拒否されるため **SURVIVED 見込み**です。
- M09 は write_lock だけを変異します（[mutation-spec-g4-wal-lock.json:13](/work/1/SFC/tanab/dev-wave-jobs/t422-campaign-external-root/mutation-spec-g4-wal-lock.json:13)）。append と acquire の独立 call-site は実コード上存在しますが変異証拠外です。
- M13 は pin 保存を変異するだけで、fix2 の核心である env 未設定時の既存-pin guard（[layout.py:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:301)）を直接変異していません。
- 壊れ方: ledger が13/13 KILLEDでも、post-resolve race 防壁や一部 materializer call-site、env削除 guard の欠落を検出した証拠になりません。
- 修正方向: post-resolve loop 単独を除く変異＋pre/post間を制御できる fixture、append/write_lock/acquire の各 call-site 独立変異、configured-none の pin guard 除去変異を追加する。

fix2 起因の新しい実コード回帰は静的には見つかりませんでした。pytest・変異は指示どおり未実走で、動的な緑は主張しません。

## 総括

**NO-GO — new-1・new-2・A-5 は closed だが、post-resolve walk と独立 materializer/pin guard を証明しない new-3 が partial のため統合不可。**