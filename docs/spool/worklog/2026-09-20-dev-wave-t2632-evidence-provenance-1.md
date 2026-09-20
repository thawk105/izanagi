---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2632-evidence-provenance
seq: 1
title: [T-2632] B-4 の proposal・走行・参照点の対応証拠は現存資料では 3 辺とも閉じない — base driver に harness carrier が無く (whiteboard 4 行 ↔ WAL 3 variant)、参照点の object・祖先関係の定義も無い。耐久 carrier と定義の裁定パッケージ 4 項 (D2100 呼び手の lock v2 欠陥を含む) を返す (docs-only、branch worktree-dev-wave-t2632-evidence-provenance)
---

## 本文

- ユーザー依頼 (2026-09-20、dev-wave 引数 = D2120 項 5 (3) の precheck、read-only・実装差分ゼロ) の範囲で 1 wave。一次資料は
  `output/insights/2026-09-20/t2632-b4-evidence-provenance/README.md` (結論表・現物棚卸し・辺ごとの判定・裁定パッケージ・段 6 レビューの反映)、
  逐語は同 `verbatim/` (brief、親の実測 JSON 2 本と probe 手順、review)。専用 handoff は Claude job dir
  (`/home/SFC/tanab/.claude/jobs/385cc37e/handoff-t2632-evidence-provenance.md`)、codex 成果物は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-evidence-provenance/`。起点 local main `482f19b88`、開始 gate `check_wave_startup --mode fresh` rc=0。
- **結論: 3 辺とも現存資料では閉じない。** 辺 A (proposal ↔ 走行): 調査した tracked 3 campaign (base 0b53a387 / sort 3be89e0d / trigger
  3f72ecd5、whiteboard 7 行・WAL 6 variant、全 success) と §5 が選ぶ base driver の precursor 保存経路に、proposal document を bytes で保持する
  harness carrier が無い。base は **whiteboard 4 行 ↔ WAL 3 variant** (重複提案は前 iteration の WAL を再利用、archive 2026-07-09 (3) の散文だけが
  対応を記す。順序で結ぶと誤対応)、sort は iteration 2 の 1 行だけ (iteration 1 は dry-pass が counter を消費)、trigger だけ harness 書きの
  `reports/p3_s8a_trigger_loop_provenance.json` が iteration → variant を結ぶ (proposal は他機体の非耐久 path のみ)。辺 B (走行 ↔ 参照点):
  量は WAL `commit` / `bench_done` record にあり canonical JSON の sha256 (`wal:<sha256>`、layer3 の `source_ref` と現物で同値) で名指せるが、
  snapshot / receipt の object と祖先関係を定める producer・契約が無い (T-2102 と同じ)。現物 6 variant は `linux-baremetal` / `default_perf()` で
  D2150 項 2 の Pegasus `PerfConfig` / `env_tag` と一致し得ない。辺 C: bootstrap 集合が D2120 項 5 (2) で未定義なので定義で閉じない。
  空虚な真 (precursor 0 件) を結論にせず、「現行形式で新規 precursor が出ても harness の記録では結べない」を結論に置いた。
- **付随して見つけた欠陥 (実装せず裁定へ):** D2100 の呼び手 `p3_b4_prerun_caller` は top-level `trial` を読むが、現行 `campaign.lock` は
  `campaign-lock/v2` (`trial` は `identity_preimage` の JSON 文字列の内側) なので、現行形式の campaign は `CampaignInputUnreadable` になり
  不足報告にも空 batch 到達にも至らない。decoder は既存 (`campaign_lock.decode_campaign_lock`)。
- **裁定パッケージ 4 項 (insight §7):** (1) 辺 A の耐久 carrier — 推奨 (α) base driver に trigger 型の harness 書き side channel
  (iteration / variant / build_attempt_id / `canonical_b4_proposal_sha256` / wal_refs / outcome、whiteboard 5 field と D39 決定 3 は不変)。
  (β) D39 決定 3 改訂、(γ) journal 必須化、(δ) trigger 系列先例の移植は劣後。(2) 辺 B の定義 — snapshot / receipt = 祖先 certified の WAL commit /
  bench_done record の canonical sha256 (`agent_outputs.canonical_bytes` を名指す)、祖先は 3 読み (同一 campaign 時間順 / 派生元 snapshot 系譜 /
  campaign 間明示系譜) の択一で推奨 ①、`PerfConfig` は全 field (reps・`ycsb_max_ope` 含む) の一致を出所を名指して確認。(3) 順序 — 新規 base
  campaign の起動前に carrier と定義が要る。(4) 呼び手の lock v2 読取りの局所修正 (Codex author の別 wave)。
- 段 6 read-only review 1 本 (`gpt-6-astra`、2 レンズ、8 分): **NO-GO → must-fix 3・should-fix 3・nit 1、全件 real・採用**、文書訂正で閉じた。
  must-fix = (i) 裁定 2 の一致案が `PerfConfig` 全 field を覆わない、(ii) 見落とし carrier (trigger 系列 supervisor の `proposals/` 保存 +
  completeness 照合、trigger driver の source-preimage) で不在断定が広すぎる、(iii) 「loop_state に `iteration` 出現 0」が誤り (親の probe は WAL
  だけを検索)。レビューは tracked 現物 (3 campaign 14 file、insight 3 file、verbatim JSON 2 本) の sha256・件数・ref を独立再計算し全件一致。
- **事故:** 親が §3.3 の実例に使った K2 3 巡目の repo 外 campaign dir (`dev-wave-jobs/dev-wave-k2-loop-round3/submit-tree/...`) は
  19:11 JST の観測後、19:26 JST に `submit-tree/` ごと消え (別 wave が同 job root を稼働中、主体は特定しない)、レビュー子は独立再確認できなかった。
  観測値は `verbatim/parent-ao-probe.json` に残し、README は観測時刻と限界を明記した。repo 外 campaign 成果物が耐久 carrier でないことの実例。
- 親の実測 probe 3 本 (read-only、job dir) は親が直接書いた ([T-317] 未裁定、軽い側)。逐語は `.md` へ写し `.py` は repo に入れていない。
- 検査: `check_docs` 違反なし、三軸語走査 rc=1 は既存 hit (s8b-floor-official / holdout_freeze.v2.g1) のみで本 wave の file は hit 0、
  `git diff --check` 緑、末尾空白 0。受入: 記録 commit の tip で `dev_wave_wait.py acceptance` を 1 回投入し、結果は受領証と land の記録が持つ。
- 工数: codex 1 本 (review)、計算ノード job = 受入のみ。

## 次の一手差分

### 更新

- [T-2632] **P2・裁定済み (D2120 項 5) → 裁定パッケージ待ち (ユーザー) + 条件待ち**: 対応証拠の出所は 2026-09-20 に現存資料で確かめ、
  **3 辺とも閉じない** (`output/insights/2026-09-20/t2632-b4-evidence-provenance/`)。D2120 項 5 (3) の「別裁定」が発火した — 裁定パッケージ 4 項
  (辺 A の耐久 carrier = 推奨 (α) base driver の harness 書き side channel、辺 B の snapshot / receipt / 祖先の定義、順序、D2100 呼び手の lock v2
  読取り欠陥の局所修正) は同 README §7。§5 の 2 欄は precheck 済み (2026-09-17) で D1483 の順序後、site / PerfConfig / 委任 / 環境契約は
  D2150 項 2 で確定。bootstrap 集合は非空入力が出るまで定義しない (D2120 項 5 (2))。承認済み PerfConfig の base CLI 消費経路は
  `--calibrated-perf --perf-workload` (D2183)、B-4 marker との併用は未検証。通常 base campaign からの自然発生赤の回収は変わらない。
  base: c849abe473225e027676eca10cf75b77cad6ec55a6caad0dbb4c80dfce7dd0fc
