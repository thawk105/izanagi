---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-paper-methods-ja-b8
seq: 1
title: 本体論文 (日本語) の方法節と実装対応メモを 2026-09-21 版に改稿した — B-8 の方法 (発効束・repo 外の runner v5・校正段と本走段・3 値判定の規則) を方法節 §3 に加え、K2 の同 job stock 対照口を D2187 (初投入の不成立) と D2205 (pair mode への修復、実機の再投入は未) に分け、B-5 を D2200 項 1 の段階認可 (本走は未認可) として B-8 と分けた (docs のみ、台帳 ID 未起票、branch worktree-dev-wave-paper-methods-ja-b8)
---

## 本文

- ユーザー依頼 (2026-09-21、dev-wave 引数、台帳 ID 未起票。逐語は `output/insights/2026-09-21/paper-methods-ja/verbatim/request.md`) の範囲で 1 wave。
  成果物は `output/insights/2026-09-21/paper-methods-ja/{methods,implementation,README}.md`、前稿 dir (`output/insights/2026-09-20/paper-methods-ja/`) の
  README 冒頭の前方 pointer、`docs/phase3.md` の [x] 1 項。前稿本文 2 file の sha256 は wave 開始時と記録時で一致。wave の記録 (brief、前稿から変えた点の
  型付け表、段 6 の所見と裁定、検査) は同 README §1〜§6。
- 起点 = 採用時点 local main `36fb14a3d` (fresh worktree、開始 gate rc=0 は 20:46 JST)。軽量版で段 2・3 を省き、実装面 0 なので変異 matrix は `DW-S04` により免除。
- **scope の扱い (brief の (P1)):** 依頼が 09-20 以後の着地全般の総点検を scope 外としたので、三つの対象 (B-8 の方法、K2 の対照口、B-5 の状態) だけを
  `36fb14a3d` と一次資料で照合し、それ以外は前稿の照合 `482f19b88` を継承して再照合しないと本文冒頭と README に明記した。継承部分で「本稿の時点」と
  書いていた箇所は、中身を再照合せず「前稿の照合時点」へ表記だけを直した。作業中に目にした後の着地 (A-1 attempt-0002 の完走 = entry 1755、旧系列の
  再開整合の実測 = entry 1790) は README §5 の限界に例として書き、本文は直していない。
- **段 6 は Codex を起動せず、Claude の独立 context の子で代替した。** Codex は利用上限 (復帰 2026-09-26 19:35 と表示、同日の entry 1801 / 1802 と [T-2833] が実測)。
  `DW-C00` が残せと言う独立 read-only レビュー 1 本 (2 レンズ) と焦点再レビュー 1 本を、Agent (subagent_type = Plan、model = opus) に同じ形式の prompt で渡した。
  同系統モデルなので Codex と同等の独立性は主張しないと README §4 と phase3 の項に書いた。レビューは GO (818 秒・道具 68 回、must 0 / should 4 / nit 9 /
  refuted 24)、焦点再レビューは GO (537 秒・道具 45 回、closed 11 / partial 1 / 不採用が妥当 1 / regressed 0、新規 nit 6)。
- **レビューが捕まえたのは「一次資料の条件・出所の取り違え」だった:** (a) K2 pair の初投入を「pin 前進後の main から」と書いたが、CCBench は driver の
  PIN `511c9538` へ checkout して走っていた (D1777 の手順、superproject だけが前進後)。(b) bench 失敗の規則を本走段にだけ書き、校正の bench 失敗でも pass と
  読める配置だった (D2190 項 3 (b) は校正・本走を問わず pass を妨げると固定。規律 2 の向きで直した)。(c) `pass` という判定値の出所に手順の D2202 を挙げた
  (判定値は結果稿 §3 と発効記録 §5 にある)。(d) 複製した継承段落の `[README](README.md) §5` が新 dir では別の README (§5 = 限界) を指していた —
  **リンクは解決するので相対リンク検査では捕まらない。** 数値 token と件数の帰属 (判定集合 30 枠 = 本走 24 + 校正の完走 6) は初稿から違反 0 だった。
- 検査 (記録 commit 前): `check_docs` 違反なし、相対リンクの解決、三軸語走査は rc=1 で hit は既存の 3 件 (`s8b-floor-official` の journal / manifest / result) だけ、
  全史 provenance 監査は草稿 commit 後に 12,443 件・新規違反なし。受入全走と land の結果は記録 commit の後に確定するので本 entry には書かない
  (受領証は wave の artifact dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-methods-ja-b8/`)。
- 工数: Codex 子 0 本、Claude の独立 context 子 2 本 (review 1、focus 1)、親の login 実走は docs 検査 3 回・provenance 監査 2 回・三軸語走査 1 回。
- 受入 attempt 1 (22:19 JST 投入、tested main `5f25b616b` を post-claim merge) は rc 70 (子 rc 1)。赤は 1 件
  `orchestrator/tests/test_t810_coordinator.py::test_prepare_group_accepts_external_root_with_anchor_union` だけで、他は 26,979 passed / 69 skipped。
  本文は `T810CoordinatorError: cannot read worktree registration: file is absent` (path = `.git/worktrees/rulings-all-20260921d/gitdir`)。
  このテストは実 repo の worktree 登録を読み、登録が他 session の撤去で消える競合に 3 回の再試行 (`_with_live_authority_retry`) を持つ。
  消えたのは別 session の worktree で、判定時点で `.git/worktrees/` に無かった。判定: 非帰属 (`DW-O18` の差分到達不能 — 本 wave は docs と insight だけ)。
  計算ノードの単独再走 (request `15833.nqsv`) は 1 passed で非再現。同じ規則で受入を 1 回だけ再投入する。
- 受入の再投入 (22:39 JST 投入、tested main `caf0f8a1a` = 第 30 回 /rulings の着地を post-claim merge、tip `80dfd3396`) も rc 70 (子 rc 16、
  `dispatch-attestation-missing`)。shard 0 / 2 は赤 0 (4,204 / 12,084 tests)。shard 1 は
  `orchestrator/tests/test_pegasus_floor_tools.py::test_floor_checkpoint_filesystem_hang_has_a_wall_clock_bound[write]` が
  `AssertionError: diagnostic timeout did not interrupt the syscall` (5.1 秒の時間依存テスト) で落ち、続いて xdist の scheduler が
  `KeyError: <WorkerController gw23>` の INTERNALERROR で止まった。判定: 非帰属 (`DW-O18` の差分到達不能)。計算ノードの単独再走
  (request `15897.nqsv`) は parametrize 3 件とも passed で非再現。tip が変わったので、この tip について受入を 1 回だけ再投入する。
- 記録 commit の後に取り込んだ D2211 (第 30 回) の項 1 が K2 の同 job pair の再投入を認可した。採用時点は動かさず、README §5 に「採用時点より後の着地」として書いた。

## 次の一手差分
