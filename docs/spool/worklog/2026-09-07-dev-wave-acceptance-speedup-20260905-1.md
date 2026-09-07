---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-acceptance-speedup-20260905
seq: 1
title: 受入全走の律速を実測で特定し、実 repo output/ snapshot を git 索引経由にした (branch worktree-dev-wave-acceptance-speedup-20260905)
---

## 本文

- ユーザー依頼は「受入全走の高速化。ボトルネックを特定し、リワードハックをせず、
  並列化・効率化・バッチ化などなどあらゆる賢い手段で受入全走の高速化に取り組んでください。
  今のそれは遅いです」。**「リワードハックをせず」を最上位の制約として扱った。**
- **段 6 の敵対レビューが親の数値 4 件を一次資料で反証し、親が全部受け入れた。**
  詳細は `output/insights/2026-09-07_acceptance-git-index-snapshot/README.md` §4。
  特に (a) 呼び出し回数を grep の一致件数から 1.8 倍過大に見積もっていた、
  (b) 対象 test が `xdist_group("real-repo")` に登録されていると仮定していた (1 本も未登録)、
  (c) node 時間を wall 増分として 2 回数え違えた、の 3 つは {{F:node-time-read-as-wall-time}} /
  {{F:call-site-count-read-as-test-count}} / {{F:assumed-registry-membership-without-checking}} に記録した。
- **等価性の実測が緑でも検出力の低下は見えなかった。** 段 6 レビューが挙げた 3 経路
  (`assume-unchanged` で status が黙る / blob sha 単独キーの衝突 / 末尾 NUL 未検査の fail-open) は、
  実 repo で参照オラクルと完全一致していたため実測だけでは検出できなかった。
  {{F:speed-fix-traded-detection-power-silently}} に記録し、索引と設定だけで判定する
  5 つのフォールバックを fail-closed で置いた。変異 5 件で各条件に独立した歯があることを確認した。
- **D1647 (受入 shard report に session timeline の観測 field を足す) は実装しなかった。**
  `DW-S04` に従い不採用にはせず、裁定時の未見事実を添えてユーザー再裁定へ戻す。
  未見事実は (1) D1647 の理由「内訳が分からないと次の一手が決まらない」を本 wave が
  別経路 (テストコードのプロファイル) で満たした、(2) 段 6 の 2 レンズが「裁定された 3 field では
  その目的を達成しない」と示した (wall の両端が閉じず、lock は取得待ちを測らない)、
  (3) closed schema の v1→v2 昇格が「受理集合に触れない」という逐語条件と緊張する、
  (4) v1 を 14 field 完全一致で読む追跡下 consumer
  `output/insights/2026-08-24_t1618-xdist-controller-cost/prepare_inputs.py:501-521` がある、の 4 点。
- **却下した高速化案はすべて実測に基づく。** 特に「チェックを per-test から per-module へ集約する」は
  22 回を 2 回にでき最も効くが、「test A が汚し test B が戻す」経路を検出できなくなる。
  受理集合の拡大にあたるため採らなかった。同 insight §5。
- **変異 13 件のうち 4 件は期待 node が不完全で MISMATCH になった。** いずれも赤にはなり、
  事前登録した期待 node も観測集合に含まれていた。`DW-M03` に従い冗長 gate として記録し、
  単独変異の証拠から外した。**期待を実測に合わせて書き換えての再走は行っていない**
  (新しい事実を何も証明しないため)。初回結果は同 insight §6 に erratum として残した。
  対照 `C1` は事前登録どおり SURVIVED。
- 並行して同主題の wave (`2026-09-07_acceptance-wall-decomposition`) が動いており、
  編集面の競合 1 点について本 wave が裁定した。
  `test_t080_output_snapshot_observes_git_visible_create_and_delete` は
  `test_real_repo_serialization.py:804` と `test_s8b_oracle_driver.py:642` に逐語重複しているが、
  **本 wave が着地すると後者だけが共有実装を呼ぶようになり、両者は独立オラクルの対になる。**
  よってどちらも削除しない。
- 計算ノードは wave 中ずっと他 wave で飽和しており (gen_S で 47 job 実行中、自 job は
  0 RUN / 13 QUE の時間帯があった)、焦点走が `queue-wait-timeout` で rc=16 になった。
  `qdel` は投入停止を誘発するため使わず、D612 の
  `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600` で待ち上限を広げて通した。
- 子の内訳は plan 1・consult 2・author 1・review 2・fix 1 の計 7 セッション、
  すべて `gpt-5.6-sol` / `xhigh`。段 5 と段 6 fix の子はいずれも sandbox から pytest を
  起動できず (`qstat -Q` の `EACCTAUTH`、dispatch rc=16)、実走は親が行った。

## 次の一手差分

### 新規

- {{T:d1647-observation-field-reruling}} **P1・ユーザー裁定待ち**: D1647 の観測 field 集合を
  再裁定する。裁定どおりの 3 field では裁定自身が挙げた目的 (77〜169 秒の未分解区間を閉じる) を
  達成しない。択一は (a) 両端 (session 開始時刻・report 完了時刻) を足す、
  (b) lock を「取得試行から取得完了までの累計待ち」に変える、
  (c) 律速が特定済みである以上、計装そのものを見送る、の 3 つ。
  併せて closed schema v1→v2 と「受理集合に触れない」の射程、
  追跡下 v1 consumer の扱いも裁定されたい。
  根拠は `output/insights/2026-09-07_acceptance-git-index-snapshot/README.md` §4。

- {{T:role-sink-32-wire-split}} **P2・新規**: `test_p3_autonomous_workload_trial::
  test_role_sink_bytes_vary_only_at_declared_declassifications` (受入 63 走で最長残存 node の
  10/63、268〜312 秒) の分割を設計する。32 通りの wire を 1 本の中で回して**横断比較**する
  構造のため、単純な parametrize 分割では assert が成立しない。
  worker を跨ぐ状態共有か、生成と比較の 2 段化が要る。
