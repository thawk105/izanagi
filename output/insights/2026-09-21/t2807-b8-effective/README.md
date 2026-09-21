# [T-2807] B-8 事前登録 v1 の発効 (D2194 項 1) と、校正 → 本走 → 3 値判定の記録

- wave: `worktree-dev-wave-t2807-b8-effective` (背景 job、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2807-b8-effective/`)
- 起点 local main: `5efd69367` (開始 gate rc=0) → 段 3 前に `21641fee7` へ ff-only (差分は dev-wave 手順書・worklog の docs と fold だけ。事前登録・patch・verifier・pin は不変)
- 依頼: D2194 項 1 (第 27 回 /rulings、ユーザー「推奨通り」2026-09-21 00:5x JST) — 事前登録 v1 を案 A の発効束で発効し、校正 3 job → 規則が決める extime で本走 6 job → 3 値判定 → results 稿と論文ストーリーへ
- 前段: 発効前試走と発効束 draft は `output/insights/2026-09-20/t2807-b8-prerun/README.md` (§7.1 = 発効束の全項目の表)
- 実装面 (repo 内) の差分 0。runner v5 は repo へ入れない (D95、前 wave の job dir に保全、sha256 で同定)

---

## 1. 発効の記録

**事前登録 v1 (`docs/b8-final-candidate-longrun-verify-preregistration.md`、raw sha256
`6ccb18c73b80ba42031f1373d48baa2e3fe441e0370a208836a6d75a9504f7c5`、51,974 bytes) は、本 README と
`verbatim/b8-effective-bundle.json` を追加した commit (以下「発効 commit」) で発効した。** 発効 commit の hash は
自己参照を避けて本 README 初版には書かず、後続の記録 commit で本節末尾に追記する (事前登録 §0)。

| 項目 | 値 |
|---|---|
| 決定 | D2194 項 1 (択 (a) 承認)。関連 = D2186 項 1 (段階認可)、D2190 (runner v5 と発効束 draft) |
| 承認の日付 | 2026-09-21 (ユーザー発話「推奨通り」00:5x JST、第 27 回 /rulings の索引 14 項への一括回答) |
| 承認の対象 | 承認時に提示された snapshot = main `285477c0052819e272e390d798f6442658075866` 内の試走 insight §7.1・発効束 draft・事前登録 v1 と、それらの実値 |
| 承認を記録した commit | rulings commit `3016f22eec17ac839fd4db0a0798f7e441f99bff` (2026-09-21 01:03:47 JST、裁定の記録)。D 番号 D2194 を振った fold = `2afb3976822dc0e3d8591c139f6ab607278b9276` |
| 対象の択 | 案 A (S-1 最終候補の系側 gate 構成。g_rl = balanced / read-heavy、g_rt = write-heavy、24 verify) |
| 発効束 JSON (runner の `--bundle`) | `verbatim/b8-effective-bundle.json`。draft (`output/insights/2026-09-20/t2807-b8-prerun/verbatim/b8-effective-bundle.draft.json`、sha256 `6063d5d8b45c0bcd405296f9f99ca2989f894a7054bf91ef0248e45f4a5d7ae6`) の実験構成の値を不変で写し、`status` だけを `effective` に置換し、`effective` 節 (決定・日付・承認の対象と記録 commit・draft の出所・校正 walltime・verifier hard timeout) を足した。sha256 `059536a7359406182c622172354207e147ad2811ba0b4d9286982778b3807c1b` |
| 発効束の他の項目 (JSON 外) | 前 wave insight §7.1 の表のとおり — 環境 (Pegasus gen_S、1 job 1 node、単独性検査は runner が bench・verifier 直前)、configure argv 全文 (試走 record `bindings.configure_argv`)、校正 walltime 03:30:00 の根拠 (上限式 ≈ 10,347 s ≤ 12,600 s、D2160 校正最大 Elapse 4063 S × 3 = 12,189 s。上限式は setup+hydrate+build の事後検査 2400 s を含む見積式で、厳密な上限保証ではない)、既知結果台帳の差分 (試走 6 record)。値は変えていない。**保全先と空き容量は本 wave の現在値を §3 に書く** (前 wave の「81 TB」は転記しない) |
| runner | v5 `4ff6652a365b952cba4deb23e2ae910ba863dabba4a107503c641c7a36863430` (2103 行)、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2807-b8-prerun/probe/verify_phase_runner.py` (repo 外) |

### 1.1 発効直前の検算 (親、login、HEAD `21641fee7`)

`probe/check_bundle_at_head.py` (job dir、読むだけ) で、draft の値と HEAD の実体を照合した。全 15 項目一致 (NG 0):
submodule gitlink = pin `e9e477ca1b55348ab4530de0b1cf663ce4555290`、`pin.CURRENT_PIN` = `e9e477c`、patch sha256 `31316713…`、
事前登録 sha256 `6ccb18c7…`、verifier module 9 file の sha256 (余分な `*.py` 無し)、`pipeline.py` sha256 `472cc7a2…`。
発効版 JSON (sha256 `059536a7…807c1b`) は runner v5 の `load_bundle` に受理され、同 JSON に対しても同じ 15 項目が一致した。runner の `validate_bundle` は `status` と承認情報を検査しないので、校正・本走の launcher は固定 checkout 内のこの tracked path を `--bundle` に固定し、`summarize` には `--accept-ruling-sha` と `--accept-bundle-sha` を各 1 値で渡す (段 3 相談の注意、新しい gate は足さない)。

## 2. 論文ストーリー §8 B-8 の仕分け (2) の限定 (D2186 項 1 (2))

D2186 項 1 (2) は、事前登録 §3.2 の定義 (「種を変えた N 反復」= N 個の独立な bench process をそれぞれ新しい OS process
として起動し、各 process の各 worker thread が `std::random_device` から自己シードすること。seed 値は記録しない) を
B-8 の「種を変えた」の要件として認め、論文ストーリー §8 の仕分け (2) 「数値 seed・乱数列の独立性は記録できない」とは
不一致なので、発効時に仕分けを「独立 process の自己シード」へ改める限定を明記すると定めた。

**発効後の B-8 の仕分け (2):「種を変えた」は独立 process の自己シードで満たす。** 各 verify が記録するのは rep-id・bench の
PID・開始時刻 (wall clock と monotonic)・argv 全文・node 名・binary の sha256・source identity・trace の byte 数 / 行数 /
commit witness であり、seed 値は記録しない (CCBench に seed の flag は無く、seed 注入は要件にしない — 候補の identity が
変わり、検証対象が headline の候補でなくなる)。**限定:** 独立性は操作的仮定で、`std::random_device` の実装は測っていない。
同じ 32 bit 値の再出現は検査できない。「異なる乱数列であることを検証した」とは書かない (事前登録 §3.4)。

- 論文ストーリーの日付版は凍結物 (「書いた後は更新しない」) なので、2026-09-21 版以前の §8 の文は書き換えない。
  限定は腐らない入口 `docs/paper-story/README.md` の「最新スナップショット以後に確定したこと」へ積み、次に作られる版が
  本文へ取り込む。
- この限定は D2160 の検証相 (採用候補 2 genome、extime 3 s) の仕分けを変えない。検証相は対象 (1) と長さ (3) が要件と
  違うので、仕分け (2) が改まっても B-8 には数えない。
- **発効は、校正・本走・判定が済んだことを意味しない。**

## 3. 校正 (段 A) — 2026-09-21 08:45〜09:11 JST、Pegasus gen_S 3 job

投入形: 発効 commit の detached submit-tree (`submit-tree-c1/c2/c3`、HEAD = 発効 commit、clean、submodule = pin `e9e477ca`) から
`dispatch_compute.py --task generic --walltime 03:30:00 --queue-wait-timeout 21600 --overall-grace 21600 -- python3.10 -B <runner v5> calibrate
--workload <w> --repo-root <tree> --third-party-cache /work/1/SFC/tanab/izanagi-thirdparty-cache --scratch-root /scr --output-dir <J>/run/calib/<w>
--ruling <tree>/docs/b8-…preregistration.md --bundle <tree>/output/insights/2026-09-21/t2807-b8-effective/verbatim/b8-effective-bundle.json`。
`--extimes` は既定 (= {6, 10})。launcher は投入直前に runner v5 / 事前登録 / 発効束の sha256 を照合し、不一致なら投入しない
(`run/calib-<w>.identity.txt`)。3 job は独立なので並行投入した (runbook §7.5)。

| workload | gate | request | node | job 所要 (runner) | dispatch Elapse | F_s (setup / hydrate / build) |
|---|---|---|---|---:|---:|---|
| write-heavy | g_rt | 14640.nqsv | bnode019 | 553.1 s | 558 S | 30.6 |
| balanced | g_rl | 14641.nqsv | bnode020 | 430.9 s | 436 S | 30.5 |
| read-heavy | g_rl | 14642.nqsv | bnode023 | 920.7 s | 926 S | 42.1 (setup 3.2 / hydrate 22.8 / build 16.1) |

**6 行すべてが bench 完走・trace 保全済み・verifier 完走・`serializable`・certified・`anomaly_count` = 0・identity 一致で、
verifier wall は最大 491.4 s (適格の上限 1800 s の内側)。打ち切り 0 件、未完走 (indeterminate) 0 件、bench 失敗 0 件、規約不適合 0 件。**

| workload | extime | commit witness (= C 行数え直し) | bench s | count s | preserve s | verifier wall s | verdict / certified / anomaly |
|---|---:|---:|---:|---:|---:|---:|---|
| write-heavy | 6 | 5,031,651 | 6.36 | 5.01 | 8.61 | 173.5 | serializable / true / 0 |
| write-heavy | 10 | 8,386,125 | 10.38 | 8.38 | 12.91 | 296.7 | serializable / true / 0 |
| balanced | 6 | 4,365,476 | 6.35 | 4.32 | 8.33 | 129.8 | serializable / true / 0 |
| balanced | 10 | 7,291,602 | 10.35 | 7.18 | 12.30 | 221.0 | serializable / true / 0 |
| read-heavy | 6 | 11,820,251 | 6.34 | 11.74 | 18.68 | 290.5 | serializable / true / 0 |
| read-heavy | 10 | 19,605,018 | 10.34 | 19.39 | 29.24 | 491.4 | serializable / true / 0 |

- 校正の完走 verdict は判定集合に入る (§6.1)。6 件とも certified なので「certified でない校正 verdict」の開示は 0 件。
- D2160 の校正 (案 B、fixed-5 / fixed-10) では balanced 10 s が SIGKILL、write-heavy 10 s が hard timeout で未完走だったが、
  **案 A の 3 workload は 10 s まで完走した** (対象も verifier の版も違うので比較はしない。事実として併記する、§8 の既知結果台帳)。

### 3.1 規則が機械的に決めた extime と予算 (発効の後・本走の前に記録する値、§12)

`summarize` (runner v5、`--accept-ruling-sha 6ccb18c7…` / `--accept-bundle-sha 059536a7…`) の出力
(`run/summary-calib.json`):

- 適格集合 = write-heavy {6, 10}、balanced {6, 10}、read-heavy {6, 10}。**共通部分 {6, 10}、その最大 = extime 10 s。**
- B(10) = **9,289.3 s** (T_s 8,601.2 + A_s 435.6 + F_hat 42.09 × 6 = 252.5) ≤ 14,400 s → 段下げ無し (`stepdown_history` = 10 s「within budget」)。B(6) = 5,608.6 s (参考)。
- **`stage_B_allowed` = true。** この時点の `decision` は `undetermined` (本走 24 枠が未実施なので当然。理由 = 「missing/out-of-range rep」「not all 24 slots satisfy pass conditions」)。
- 本走の構成: extime 10 s、3 workload × job-index {1, 2} (rep 1–4 / 5–8) = 6 job、24 verify。
- **本走 job の walltime = 03:30:00 (12,600 s)。** 根拠 (2 つとも満たす): (a) 校正実測の最大 job 所要 920.7 s から 4 反復へ換算した見込み
  = read-heavy 42.1 + 4 × (10.34 + 19.39 + 29.24 + 491.43) ≈ 2,243 s の 5.6 倍。(b) 上限式 = setup+hydrate+build の事後検査 2,400 +
  4 × (bench 120 + count 19.4 + preserve 29.2 + verifier hard 1,800) + 終了余裕 300 ≈ 10,574 s ≤ 12,600 s。
  **この上限式は見積りであって強制される上限ではない** — 2,400 s は setup 完了後の事後検査で、count / preserve に個別 deadline は無い
  (段 3 相談の指摘を採用)。
- **保全先と空き容量 (本 wave の実測、2026-09-21 09:1x JST):** 保全先 = job dir `run/` (`/work` lustre)。校正の 10 s の保全は
  write-heavy 510 MB / balanced 613 MB / read-heavy 1.8 GB = 2.85 GiB。本走 24 枠 (各 8 反復) への外挿 ≈ **22.8 GiB**。
  `df` の空き = **81 TB** (使用 5%)。校正全体 (6 行) の実消費は 4.6 GB。
- 費用の照合は dispatch の Elapse の和で行う (runner の `consumed_job_wall_s` は内部 monotonic の暫定値として別記する)。
  校正の実消費 (別欄、§7) = 558 + 436 + 926 = **1,920 S**。

## 4. 本走 (段 B)

(校正の summarize が `stage_B_allowed` を返した場合に追記する)

## 5. 3 値判定

(未)

## 6. 限定

(判定後に書く)
