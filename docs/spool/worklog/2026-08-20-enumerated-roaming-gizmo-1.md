---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: enumerated-roaming-gizmo
seq: 1
title: 受入全走のボトルネックを調査し、per-test snapshot コピーの hardlink 化を実測して不採用と結論した (docs のみ、branch worktree-enumerated-roaming-gizmo)
---

## 本文

- command 引数「受入全走のボトルネック改善。リワードハック禁止」を受け、直前 wave
  `dev-wave-accept-bottleneck` (2026-08-18、実装差分ゼロ) の継続として着手した。
  D531/D532 (`output/insights/2026-08-18_acceptance-wall-cost-structure/README.md` が正本)
  を前提に、real-repo 鎖上位3件のうち2件 (`test_codex_reasoning_ab.py` 側) の per-test
  `shutil.copytree` 8箇所を hardlink 化する案を段2 codex プラン→段3 敵対相談 2 レンズ
  (所見計16件、BLOCKER 3件) で精査した。
- D315 (docs/decisions.md:14373、2026-08-12) が `--no-hardlinks`/`_seal_git_object_closure`
  系の変更を「検証している安全性質そのもの」として既に禁じていることを段1 brief で発見し、
  対象を D315 範囲外の per-test copytree だけに絞った。段3 で submodule `.git` marker
  (通常ファイル) の取りこぼし・symlinks 引数の意味論差・8箇所以外への波及リスクを検出、
  実装前に測定ゲートを課す判断をした ({{D:accept-chain-copytree-hardlink-no-gain}})。
- 段5 実装子 (workspace-write) に測定ゲートを持たせたが、Codex 子は scheduler 呼出しが
  sandbox で拒まれ測定できず (`qstat -Q` rc=1)、530秒・32 model call を空費した
  ({{F:author-child-cannot-dispatch-measurement}})。親が `tools/run_tests.py` 経由の
  bounded local 実行 (24.89秒、pegasus02 ログインノード) で対象テストを単独実走し、
  実際に構築された snapshot (82.67MB) を pytest basetemp と同じ filesystem 上で計測した。
  `.git` (root+submodule marker) が全体の 43.2%、copy2 相当のコピーは 0.158秒、hardlink相当は
  0.043秒で、削減幅は高々1秒 (鎖長77.5〜94.9秒に対し無視できる) と判明し、実装を見送った。
- `test_s8b_floor_campaign.py` 側 (top-3 の残り1件) は、D315 保護対象の clone 2 箇所以外の
  checkout/add/commit・consumer replay も実質的な検査であると段3 レンズAが特定し、対象外と
  確定した。`test_supervisor_launches_pair_and_scrubs_git_environment` (19.38秒) は copytree を
  伴わずUnit A の対象になり得ないと段3 レンズBが確認した。
- Unit B (T-870、dispatch queue-wait/overall-grace 既定値の引き上げ) は、段3 レンズAが
  「受入 lease TTL (既定2400秒) との衝突を検討していない」ことを BLOCKER として検出したため
  本 wave では実装せず、次の一手として更新した (下記)。
- 実装差分ゼロのため変異matrixは免除 (DW-S04)。受入全走は本 fragment 群の commit 後に
  親が投入する。

## 次の一手差分

### 更新

- [T-870] **P2・受入 queue-wait/overall-grace 既定値の是正 (再訪、2026-08-20 wave が blocker を追加発見)**:
  `tools/run_tests.py` の `_default_dispatch` が `dispatch_compute.dispatch(...)` を
  `overall_grace_s`/`queue_wait_timeout_s` 指定なしで呼び、既定 300秒/900秒に固定される
  (`tools/pegasus/dispatch_compute.py:47-48`)。queue 滞留時に焦点走・受入が rc=16 で落ちる。
  単純に両値を引き上げる案 (queue_wait=10800秒/overall_grace=7200秒) を検討したが、
  2026-08-20 wave の段3 敵対相談が次の blocker を検出し、次回試行はこれを設計に含めること:
  (a) overall_grace を数千秒級に延ばすと、受入 lease の TTL (既定2400秒) が dispatch の
  queue 待ち中に先に切れ、lease 失効後に受理される経路が生まれうる (renew/recheck/cancel が
  未設計)。(b) dispatch 親が SIGTERM された場合の孤児 job 占有 (既知型) への影響が未検討。
  (c) queue-wait (pre-RUN) と overall-grace (post-RUN 超過猶予) は別々の根拠で設計すべきで、
  同じ実測値 (過去の55分・2.5時間滞留) から両方を導出しない。(d) 変更は `_default_dispatch`
  経由 (受入・テスト dispatch 限定) にとどめ、`dispatch_compute.py` 汎用既定値は変えない
  スコープにする。実装案の詳細は `/work/1/SFC/tanab/dev-wave-jobs/accept-bottleneck-chain/`
  (`stage2-plan.md` 175-249行、`stage3-lensA.md` 所見7・8・9・10、`stage3-lensB.md` 所見3) に
  保全済み。
  base: a29a40db24c90e3c6a37d0bddc34fb9d05a2af9c9395b2dd404fabde1b6857f7

### 新規

- {{T:accept-chain-fixed-cost}} **P2・新規**: 受入全走の固定費 (約26秒、48 worker が各自
  12951件を collection する費用、wall の22〜25%、D532 (c)) の削減を、worker数変更以外の
  技法 (collection manifest の共有、controller-only collection 等) で検討する。
  2026-08-20 wave (段3 レンズB 所見4) が「worker数変更以外は未検討」「controller-only
  collection は xdist protocol を変える大きな変更で低risk実装とは言えない」と指摘済み。
  低risk案が無ければ「無い」と結論してよい。関連: {{D:accept-chain-copytree-hardlink-no-gain}}。
