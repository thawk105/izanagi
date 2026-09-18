---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2288-floor-pair-job-body
seq: 1
title: [T-2288] (a) B-4 床値 (floor-pair) の窓 job と finalize job を計算ノードで起動する Pegasus job body と submitter を着地させた — 凍結 spec 3 本を floor_pair_driver の --execute-window / --finalize で走らせる資材、登録簿 2 entry、契約 test 22 本、runbook §7.8。実投入は次の測定 wave (F660) (コード + テスト + docs、branch worktree-dev-wave-t2288-floor-pair-job-body、変異 matrix = baseline PASSED・M0 SURVIVED・M1〜M5/M7〜M10 KILLED 期待 node 完全一致・M6 は check_docs 直接で KILLED・MISMATCH 0)
---

## 本文

- ユーザー依頼は「[T-2288] (a) B-4 床値 (floor-pair) の run_window / finalize を計算ノードで起動する Pegasus job body を着地させる wave —
  凍結済み 3 spec (commit 0b4fbd7a6 の output/env/pegasus/floor-pair/t2288-f1/、窓 w1 2026-09-19〜09-27 / w2 09-29〜10-07 UTC、各 62 標本) を
  orchestrator/campaign/floor_pair_driver.py の run_window / --finalize CLI で走らせる job body と submit script を、既存の
  tools/pegasus/floor_campaign.sh + submit_floor.sh の型で足し、admission_registry.json (必要なら spawn sites / materializer 登録簿) の閉包を通す。
  run_window は site_policy.current_site(require_evidence=True) の証拠を要求する。申し送りは output/insights/2026-09-18/t2288-a5-freeze/README.md
  「後続の測定 wave への申し送り」1〜7 (3 段を同じ実行 HEAD で、place は checkout ごと (D2069)、窓の末端に投入しない、create-only)。F660 により
  実測 (w1 は 09-19T00Z 以降の session 開始) は含めず、job body の起動確認までとする。Codex author (D95) + 変異事前登録。稼働 t2772 が
  orchestrator/tests/test_ccbench_spawn_sites.py / orchestrator/campaign/materializer_admission.py を編集中なので、起動時に編集面を照合し、
  重なるなら t2772 の land 後に着手する (重ならない file だけで閉じられる場合に限り先行可)。着手直前の local main から fresh worktree を作る。
  規律 2 を緩めない。本題の job body だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **着地させた (実投入は含まない)。** 一次資料は `output/insights/2026-09-18/t2288-floor-pair-job-body/README.md`。設計判断は
  {{D:floor-pair-job-body-contract}} (1 job = 1 spec × (1 窓 | finalize)、submitter の早期拒否 = 窓の時刻・create-only・同 spec の他窓 header の
  `loaded_head` == HEAD・finalize の terminal、walltime window 24 h / finalize 30 分、証拠は repo 外)。failures fragment は再発 2 件 (F1012、F100)。
- 成果物: 新規 `tools/pegasus/floor_pair_campaign.sh` (job body、236 行、mode = window | finalize) と `tools/pegasus/submit_floor_pair.sh`
  (login 側、287 行)、`tools/pegasus/admission_registry.json` に 2 entry (74 → 76)、`orchestrator/tests/test_hooks.py` の golden 3 箇所、新規
  `orchestrator/tests/test_floor_pair_job_contract.py` (22 test、490 行、自走 harness、実関数の抽出実行)、`docs/pegasus-runbook.md` §7.0 投影表 2 行 +
  §7.8 投入手順。driver・spec・issuer・`tools/pegasus/README.md` は 0 byte。編集面は t2772 (orchestrator/campaign 4 本 + tests 5 本) と
  重ならず先行した。
- **段 3 が親 brief を 3 点で覆した (採用)。** (1) 3 段同一 HEAD は投入時に機械保証されず w1=H1・w2=H2 が finalize まで通る → submitter が他窓
  header の `loaded_head` を照合。(2) finalize は `incomplete` terminal の窓からも `not_generated_*` summary を create-only で作る (失敗 summary も
  1 回限り) → runbook に明記 + finalize 前段。(3) walltime 10 h の根拠 (44.4 h の regime は 5% 判定で不採用) は不成立 → window 24 h
  (gen_S 上限、回復不能な窓の喪失と queue 待ちの非対称)。レンズ B は `test_hooks.py` golden 3 集合・scratch の `0:` 正規化・必須 command の
  `nm` (driver は session 内で `nm -C`)・python3 shim 不要・契約 test の実行観測を要求し、すべて採用。
- **段 6 は両レビュー NO-GO → fix 1 巡で GO 相当。** must-fix = (a) 契約 test の TERM 経路が計算ノードで赤 (SIGTERM SIG_IGN 継承、F1012 再発)
  → test の子で SIG_DFL + unblock、(b) signal 観測時に driver rc=0 を signal rc で上書きする分岐 (裁定外) → 削除、(c) 環境消去が名指し 5 個
  → `PYTHON*`/`LD_*`/`GIT_*` prefix 全件。should = top-level の `main()` 化 + stub 到達 test 2 本、`bash -n` test、X_OK 負例の訂正、finalize の
  header 不一致負例、runbook の同一 HEAD 単位 (各 spec の 3 段) と初回投入の順序と SIG_IGN の帰結。不採用 (記録) = finalize では `nm`/`pgrep`
  不要 (loader は sha だけ) だが集合を分けない、spec 名の再列挙、`driver_stdout_sha256`/`qsub.rc`、hostname lowercase と `--help` alias。
- **login 起動確認は live hook が拒否した (F660 の型、迂回せず)。** Bash tool の `bash -n` 2 本とも「未登録 Pegasus 実行体」。到達 gate なし。
  代わりに契約 test (`tools/run_tests.py`、計算ノード) が `bash -n` と実関数の抽出実行 (窓 gate 全 6 窓 × 5 境界、hostname、gate 到達順、
  main の呼出し列、driver argv、dry-run 分岐、child rc 回収、`clean_environment`、A1/A2 正負例、pin の三者一致) を担う。実 qsub・env 配送・
  実効 walltime・signal 配送・計算ノードでの実行は未観測。
- 実走: 焦点走 1 (統合 commit 20aca3006、request 5523.nqsv) 503 passed / 1 failed (TERM) / 1 skipped → 焦点走 2 (fix commit cbcb4bf95、
  request 5553.nqsv、82 秒) 579 passed / 3 skipped / rc=0 (spawn_sites 含む)。login 自走 harness 18/18 → 22/22 (1.5 秒)。check_docs rc=0
  (統合 commit 後)。変異: probe 走で観測 node を採り本走 (container worktree、cbcb4bf95): baseline PASSED (508 passed、32 秒)、M0 SURVIVED、
  M1〜M5・M7〜M10 KILLED (matching 10/10、MISMATCH 0)、M6 は check_docs 直接で rc=1・違反 1 件だけ (`registry_only=[floor_pair_campaign.sh]`)。
- 工数: codex 子 6 本 (plan 1、consult 2、author 1、review 2、fix 1、全段 `gpt-6-astra` / medium)。author と fix は dispatch 障害 (`qstat -Q
  preflight rc=1`) でテスト未実走、親が焦点走を担った。段 5 前に main を ff-only で取り込み (24ede1d11 → 4e3d1df97、編集面に差分なし)。
  隔離 session の `cd <他 worktree>` で cwd が移る罠を 1 度踏んだ (F100 再発、実害なし、EnterWorktree(path) で復帰)。
- 受入調停 (peer manager thread、12:09): 受入の門番を leaders ≤ 1 (自 slug 除外) ∧ load ≤ 60、2 分周期、F945 型 / postcheck / child log 無し
  rc=70 は自動再投入で連結する運用に従った。

## 次の一手差分

### 更新

- [T-2288] **P1・(a) job body と submitter を着地させた (D は本 wave の fragment)。残るのは (b) 実測 wave**: 資材は
  `tools/pegasus/submit_floor_pair.sh` (login) + `tools/pegasus/floor_pair_campaign.sh` (計算ノード)、手順は `docs/pegasus-runbook.md` §7.8。
  **(b) 実測 wave — 実行 HEAD `H` を本 wave 着地後の main から 1 つ決め、detached checkout で `place` (D2069 項 7)、w1 (2026-09-19T00:00Z 以降、
  `now + 24h <= 09-27T00:00Z`) → w2 (09-29T00:00Z 以降) → finalize (両窓の terminal の後) を各 spec で同じ `H` から投げ、初回実行で実配送
  (8 変数・walltime・signal・到達段・receipt) を確認して記録する。** 証拠確認 (24 h 分離・n = 62・欠測率) の後に集約発行と採用裁定
  (D1641 決定 2)、§5 floor 欄の記入へ。窓を使えずに終わったら延長・差替えをせず新しい凍結を別 commit で行う。
  base: 4a58067a1f9bddae3a07900658801400f49dec7e84da2bd1368238f43988ff2d
