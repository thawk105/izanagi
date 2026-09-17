---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2661-rescue-scope-split
seq: 1
title: [T-2661][T-2663] 到達不能監査の用途分離 — 掃除は repo 外走査を明示 off、救出 triage は明示 full にし、rescue gate の子 process 環境から探索根を遮断した — 実 repo off の有効 6 走 max 28.9 秒・fixture off 0.09 秒 (full 1 走 161 秒は A を抑止、off は A を含む 4 path を報告) (コード + テスト + docs、branch worktree-dev-wave-t2661-rescue-scope-split、変異 matrix = baseline PASSED・負例 12/12 KILLED 期待 node 完全一致 (受理集合 kill 5 + 契約 pin 7)・等価 M0 SURVIVED・MISMATCH 0)
---

## 本文

- ユーザー依頼は「[T-2661] 到達不能監査 `tools/check_branch_rescue.py` の第 2 段 = 用途分離 (掃除では repo 外走査 off、救出 triage
  では full)。有効化条件 (第 1 段で 300 秒に入らない) は 2026-09-17 の実測 (走査強制 fixture、有効 6 走 max 335.8 秒) で満たした。
  付ける条件 5 件は 2026-09-16 の一次資料 README §5。着手直前の local main から fresh worktree。/cleanup-branches 稼働中なら変更後の
  経路を掃除に使わない。実装面は Codex author (D95)、変異事前登録要。規律 2 を緩めない。本題の用途分離だけ、追加の gate・台帳は
  scope 外」。wave 中に第 21 回裁定 D2120 項 24 が T-2661 の用途分離を条件 5 件つきで明示採用した (新事実、承認前提を覆さない)。
- **閉じた。** 一次資料は `output/insights/2026-09-17/t2661-rescue-scope-split/README.md`。設計判断は
  {{D:audit-offrepo-scan-mode-split}} (用途分離の契約) と {{D:audit-elapsed-acceptance-cleanup-entry}} (本 wave の所要受理対象)。
  実装 commit `0f7b6b73e` (Codex author、7 file)、段 6 fix `56d53f247`。
- **段 1 の生死確認 (現行 tool、fixture)。** 親 env に探索根があると rescue gate の監査の子 process が走査して抑止し rc 0、無ければ
  rc 3 + `unledgered-audit-finding` 1 件 — 環境の継承だけで掃除の結果が変わる経路 (T-2663 の前提) を現物で確認した。変更後は
  子 argv に `--offrepo-scan off`、子 env に root key なし、子 stdout に off 開示行、env の有無に依らず rc 3 (計測 (d))。
- **段 3 の両レンズが親 brief の 2 点を倒した。** (A1) 「full で全対抑止なら台帳 entry 不要」は台帳 doc の追記契約
  (`unledgered-audit-finding` を出した object も追記対象) と矛盾 → 撤回し、追記候補集合の増加の開示と既存契約への従属に書き換えた。
  (A2 / B1) 所要受理対象を掃除入口 (off) に限定するのは D958 / D2116 の読替えでは導けず、結果を見る前に本 wave の判断として
  段 4 で固定した (D2116 を満たしたとは記録しない、full は再判定しない)。B2 (M1 の killer は API off + 非空 roots) と B3
  (「127 test」の数量根拠を外す) も採用。
- **所要 (login、D958 項 1 の形、掃除入口 = off)。** 実 repo (main `60b4bd13f`、findings 0) は warm-up 19.8 秒を捨て、
  17.7 / 28.9 / 28.3 (max/min 1.63 > 1.5 で +3) / 16.5 / 13.1 / 19.6 秒 → **6 走 max 28.9 秒 ≤ 300 秒**。走査強制 fixture は
  0.079 / 0.086 / 0.083 秒。同 fixture の full 1 走 (161.4 秒、判定に使わない) は A (`s1-brief.md`) を抑止して 3 path、off は A を
  含む 4 path を報告 = `findings(full) ⊂ findings(off)` の実根デモ。28.9 / 28.3 秒の 2 走は本 wave の変異 harness が login 側で
  test 収集を走らせていた窓 (計数 script が test file 名に自己マッチしていたため当初「他の監査 2 本」と誤記録)。
- **段 6 レビュー 2 本 (U1 正しさ境界・test の殺傷力、U2 契約整合・pin 閉包・報告と実体) は must-fix 0。** nit 4 件 (開示行の
  全角記号 → 半角、M3 の帰属 → `_checked_git` にも trap (反実仮想 2 failed "off must not touch offrepo I/O")、計測 (d) は spawn
  記録、焦点走は計算ノード完走と記録) を fix 子 1 本で閉じ、追加のレビュー子は起動していない。author の TD 22 関数の直呼び
  (growth-hold 解除 token 使用) は親の権威に数えず、親の焦点走 (計算ノード 4076.nqsv、872 passed / 3 skipped = 既存 hold 3 node)
  と fix 後の焦点走 (login、289 passed) を証拠にした。
- **誤投入 1 件。** 段 6 review の launcher に `--reasoning` を付け、dry-run rc 2 を見ずに detach した (2 本とも即死 rc 2)。
  `--reasoning` 無しの第 2 版で投げ直した。段 8 (自己改善) で契約どおり裁定: `DW-C01` (他段指定は rc=2) と `DW-O01` (`--dry-run` を
  先に検査) が既に義務を持ち、実害は即死 2 本 (再投入で回復) のみ。dev-wave docs 3 層は予算満杯で意味等価の縮約先が無く、
  正本は変えず記録のみ (D782)。
- **変異 matrix (container worktree `56d53f247`、`run_tests.py` 3 file、probe と本走で各 14 run = baseline + 13 変異、計算ノード dispatch)。**
  probe 走 (全件 SURVIVED 登録) で観測 node を集めてから本走。本走は baseline PASSED、負例 12 件すべて KILLED で期待 node と観測
  node が完全一致 (matching 13/13)、等価変異 M0 (docstring) は SURVIVED、MISMATCH 0、TIMEOUT 0、全 anchor 一意。DW-M03 / M08 に従い
  受理集合か fail-closed 挙動が変わる本物の kill (M1 off が走査を続ける、M3 full+root 無しの拒否除去、M7 off+CLI root の usage 拒否
  除去、M9 command digest の旧値、両層 M45 = argv off 落とし + env 復元で子が走査) と、出力・I/O の契約 pin (M2 env を読む、M4 argv、
  M5 env、M6 開示行、M8 JSON field、M10 blob metadata、M11 root 検証) を分けて記録した。M4 / M5 単独は二重防壁の片方が残り
  findings 不変 — 受理集合の kill は両層 M45 が担う。M9 は check_docs の合成 repo 検査 321 node が一斉に赤 (digest 不一致)。
- 残存 (scope 外、記録のみ): flag 省略 + 環境変数の探索根は full 相当のまま (第 3 の入口、掃除の規範入口 2 箇所だけを固定)。
  off で通知された object は従来どおり `pending` の追記対象で、掃除 1 回あたりの追記候補は増えうる。T-2662 / T-2664 / T-2749
  は触っていない。D2120 項 25 (T-2707) が台帳 doc の別段落 (運用契約) を触る予定で、本 wave は「dangling audit の分岐」だけを変えた。
- 工数: codex 子 8 本 (plan 1、consult 2、author 1、review 2、fix 1、誤投入 2 は即死で不使用、全段 `gpt-6-astra` / `medium`)。
  親の実測: 生死確認 1、計測 (a) 7 走 + (b) 4 走 + (c) 1 走 + (d) 1 走、焦点走 2 (計算ノード 1・login 1)、変異 2 走 (probe + 本走)、
  check_docs 2 回、provenance preflight 3 回。

## 次の一手差分

### 完了

- [T-2661] 第 2 段 (用途分離) を実装した。掃除の規範入口 2 箇所 (`/cleanup-branches` §1 の単独実行、rescue gate の子 process) を
  `--offrepo-scan off` に固定し、救出 triage は明示 full を単独実行 (探索根が無ければ rc 2)。条件 5 件の対応は一次資料の表。
  実 repo off の有効 6 走 max 28.9 秒 ≤ 300 秒。
  remaining: none
  base: 3e1bb3b69f8883f4effc7e52529b29a44ef4440a9108cae0850c0d8b4aec3822

- [T-2663] 実測で確かめた: 現行 tool は `check_branch_rescue.py --ledger-check` が親 env の `IZANAGI_DEV_WAVE_JOBS_DIR` を子へ継承し、
  fixture で子が走査して抑止 (rc 0) / 無ければ rc 3 に分かれた。子 argv の `--offrepo-scan off` と allowlist からの除外の二重防壁で
  閉じ、変更後は env の有無に依らず rc 3。
  remaining: none
  base: 95e445aa3bb6119bf4baa5686b89f809ee94221deff24b9ff953e10fea509bf1
