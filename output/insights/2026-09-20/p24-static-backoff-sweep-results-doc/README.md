# 旧 `linux-baremetal` 環境の P2-4 静的 backoff sweep 3 campaign (論文 §8 exact claim (性能) の出所) の単独 results 稿 — 1 campaign 群の一次資料全体 (campaign.lock・WAL・.dat・材料レポート・fig2b provenance・較正記録・裁定) から書き、README の results 表へ 1 行足した (docs のみ、台帳 ID 未起票)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)

- wave: `worktree-dev-wave-p24-static-backoff-sweep-results` (背景 job 43f9108b、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-p24-static-backoff-sweep-results/`)
- 起点 local main: `947fd160ab44e6ae82b6eab56ee8d70813fda31d` (着手直前の local main、fresh worktree)。**実装面 (repo 内) の差分 0**
  (results 稿 1 本・paper-story README 表 1 行・本 insight・worklog fragment のみ)。変異 matrix は `DW-S04` により免除、受入全走は免除しない
- **新規の測定は 0 件。** 凍結物 (3 campaign の成果物・fig2b・A-3 insight・版・claim-evidence) の bytes は 1 byte も変えていない
- ユーザー依頼の確定事項: 一次資料 = fig2b provenance の inputs が指す 3 campaign の WAL・較正記録と A-3 一本化 (D20)、限定として
  但し書き 1 (D496 以前、A-1 の配置・推定対象ではない)・但し書き 3 (別 boot 未取得、D1100 / D1525)・「正しさは機序論証による外挿で
  certification は遡らない」・現行環境の 3 走行と pool しない (D1993 項 6) を番号で列挙、+38.5% を headline に使わない理由 (D20) を書く、
  値は WAL と provenance の facts から逐語で取り推定しない、README の results 表へ 1 行、段 6 は read-only レビュー 1 本 + 焦点再レビュー、
  scope 外 = 図の作り直し・再測定・英語稿

---

## 1. 一行で

`docs/paper-story/results/2026-09-20-p24-static-backoff-sweep-linux-baremetal.md` (results 系列の凍結物、限定 15 件、成果物に無い /
束縛の範囲 / 未照合の項目を §4 に区別、図は無い) を書き、`docs/paper-story/README.md` の results 表へ 1 行足した。数値・識別子・時刻の
出所は 3 campaign の `campaign.lock` / `runs/wal.jsonl` / `reports/*.dat` / `reports/*_report.md`、fig2b の provenance JSON、同環境の較正記録
4 本、profile JSON (headline でない +38.5% の出所) だけで、A-3 insight・figures README・版・claim-evidence を数値の出所にしていない。

---

## 2. 段 1 の一次資料の実測 (親、2026-09-20 13:3x〜13:5x JST、login node、読み取りだけ)

| 項目 | 実測 | 稿での扱い |
|---|---|---|
| fig2b provenance の inputs | write-heavy `493813a7` / balanced `484c663e` / read-heavy `610004b9`。WAL / lock / dat の sha256 は現物と byte 一致 (3 × 3 件) | §0.1、§5.1 |
| WAL の構造 | 各 40 行 = 8 variant × `build_start` / `build_done` / `verify_done` / `bench_done` / `commit`、`abort` 段階なし。variant ID 8 個は 3 campaign で同一 | §0.1、§1.3、§2.5 |
| `bench_done.median_tps` (逐語) | write 無 backoff 1,882,125 / fixed 10 = 2,603,521; balanced 2,791,760 / fixed 5 = 3,106,342; read 8,450,806 / fixed 2 = 7,889,420。式 `100×(v/b−1)` で 38.32880387859468 / 11.268232226265873 / −6.642987662951915% (A-3 の再計算表と一致) | §2.1 |
| median = 5 反復の 3 番目 | 24 件とも `(tps|sort)[2] == median_tps` が true | §2.2 |
| provenance `facts` | 標本平均 `best_M` / `none_M` / `adapt_M`、平均比 38.11118512885447 / 11.422593027550953 / −6.852026348109752% (figures README のキャプション正文 +38.1 / +11.4 / −6.9% と一致) | §2.3 |
| `verify_done` | 24 件とも `serializable` / `certified: true` / `anomalies: 0`。`commits` は campaign ごとに異なる。provenance の epoch は `E0` / `v1-authority-absent` | §2.4 |
| 時刻 (epoch → JST) | write 2026-06-22 22:58:59–23:09:04、balanced 23:09:04–23:14:19、read 2026-06-28 14:34:11–14:39:04 (A-3 の表と一致) | §2.5 |
| configure / build / run command | directory 名と指定 flag (`-DCCBENCH_BACKOFF_FIXED` / `-DCCBENCH_BACK_OFF`、`-ycsb_rratio`) 以外は 24 件同一。`-DCMAKE_BUILD_TYPE=Release`、gcc-13 / g++-13、`-DCCBENCH_TRACE=0`、`numactl --interleave=all perf stat -e LLC-load-misses,LLC-loads,instructions,cycles` | §1.4、§1.5 |
| binary hash | `trace_bin` / `perf_bin` の 16 hex × 8 genome が 3 campaign で同一。write-heavy は fixed 50 だけ cache 再利用、balanced / read-heavy は 8 件とも再利用 | §1.4 |
| `campaign.lock` | key = `ccbench_commit` / `search_config` / `search_tag` / `spec_content` / `trial`。`search_config` に `screening` 無し。`ccbench_commit` は短縮 `6656e93` → submodule の `git log` で `6656e9319566e602113edf46588de9a612d166a1` (2026-06-20 07:38:09 +0900) に解決。profile 側 `dff0f1e` は `dff0f1ef2a4b84746f6463839e85b24301f4b16d` (2026-06-28 15:52:52 +0900、`Fix ODR violation…`) | §1.2、§3 限定 5 |
| 非正典 read-heavy 2 本 | `6f169f90` / `8ff95955` は lock に `screening` / `screening_fixed_us` key、`ccbench_commit` `d706650` / `dff0f1e`、WAL に `abort` (`screen-slower-than-floor` / `build-error`)。`6f169f90/reports/` には `layer3_report.json` (2026-09-16 commit `f47876014`、A-3 の「reports/ 無」より後の追加) だけ | §0.1、§4.3 |
| 較正記録 | `calibration_t48_skew0p9_rr50_rmw0.json` (records 1,000,000 下限基準、`working_set_ratio` 6.637…、within-run cv 0.0228…、host `cygnus` / kernel `5.15.0-117-generic`)、`between_run_noise_t48_skew0p9_rr{5,50,95}_rmw0.json` (8 セッション × 5 rep、cv 0.00666… / 0.01067… / 0.00110…、genome に `BACKOFF_FIXED` key 無し)。`p2_2.py` の `BETWEEN_RUN_CV = 0.030` 実在 | §1.6 |
| profile (+38.5%) | `rows[]` の `tps_median` 1,867,747 (`backoff_us` 0) / 2,586,112 (10)、各 3 反復、genome に `BACKOFF_NOINLINE=1`。式で 38.46157964649388% | §3 限定 5 |
| 既裁定 | D19 / D20 / D496 / D497 / D1100 / D1506 / D1525 / D1631 / D1993 項 4・6 / D2120 項 15。論文ストーリー 2026-09-20 版 §8 の exact claim (性能) と但し書き 1・3 の逐語。rulings-inbox に本主題の新規裁定なし | §3、§5.3 |
| 既存被覆 | results 系列 16 稿に旧 sweep を単位とする稿なし (`grep 38.3` は A-1 稿と claim-evidence だけ)。凍結閉包に `docs/paper-story` を参照する module なし、test の pin は fig2b の bytes のみ (`test_backoff_figure_provenance.py`) | brief の条件 08/09/10 |

---

## 3. 一次資料の sha256 (稿 §5.1 / §5.2 の全 24 件。親が現物から `sha256sum` で計算し、稿の 64 桁 hex 全件と集合比較して一致)

稿 §5.1 (18 件) と §5.2 (6 件) に全桁を載せた。初稿では profile md の 1 桁 (`…904edf…`) が誤っており、集合比較 (`comm`) で検出して
`…904adf…` へ是正した (§4)。

---

## 4. 親の機械照合 (稿 v1、job dir `tmp/`、grep -F による逐語存在検査)

| 検査 | 件数 | 結果 |
|---|---:|---|
| 稿の 64 桁 hex ⊆ 実 file の sha256sum (集合比較) | 24 | 初稿 1 件不一致 (profile md) → 是正後 24/24 一致 |
| WAL の 5 反復リスト (`tps` を `, ` 連結) の逐語存在 | 24 | 24/24 |
| WAL の `abort_rate` (`\| x \|` セル形) の逐語存在 | 24 | 24/24 |
| WAL の `verify_done.commits` の逐語存在 | 24 | 24/24 |
| WAL の `median_tps` (桁区切り) のセル存在 | 24 | 24/24 |
| cv (小数 4 桁) / IPC (小数 3 桁) の丸めが jq の `round` と一致 | 24 + 24 | 全件一致 (`.dat` の `ipc` 列 18 件とも一致) |
| `trace_bin` / `perf_bin` 16 件、provenance `baselines` の `value_tps` / `ci95_half_tps` 6 件、`facts` 9 件、`generated_utc` | 32 | 全件逐語存在 |
| configure / build / run command と lock の `spec_content` / `base` / `scale`、較正記録の 11 値 | 17 | 初稿は build command を `<同 directory>` の placeholder で書いており逐語でなかった → 逐語へ是正、17/17 |
| `tools/check_docs.py` | — | 違反なし (rc=0) |
| `git diff --check` | — | rc=0 |
| 三軸語走査 `s8b_holdout_freeze search` | — | rc=1 は既存 hit (official 床値 journal と holdout 台帳自身) のみ。本 wave の 2 file は hit 0 |

実測で稿を直した点 (段 5 の自己点検): (1) `6f169f90` の `reports/` に `layer3_report.json` があり A-3 の「reports/ 無」は当時の事実 →
§0.1 / §4.3 を実測どおりに書き直した。(2) §1.4 の「verify は trace 側、bench は perf 側で行う設計」は WAL が言っていない推論 →
「2 binary の hash を持つ (規律 1 の分離に対応)」「`verify_done` がどちらの binary を使ったかは WAL に無い」へ弱め、§4.1 へ移した。
(3) §1.1 の「driver が判定境界・反復数・集約を持っていた」→ 「反復数と集約は WAL から読める、driver の当時の版は読んでいない (§4.3)」。

---

## 5. 段 6 — 独立 read-only レビュー 1 本と焦点再レビュー

### 5.1 レビュー 1 巡目 (review-1、gpt-6-astra / medium、read-only、15 call、349 秒、14:05〜14:11 JST、`outcome: accepted`)

prompt は job dir `prompt-review.md` (2 レンズ = A 一次資料との照合・母集合・件数 / B 主張の強さ・限定の完全性・禁止句・先取り、brief の
(P1)〜(P4) 攻撃を含む)、逐語出力は `review-out.md`。**NO-GO、所見 5 件。親の裁定: 所見 1〜4 = real・採用、所見 5 = refuted (現状維持)。**

| # | 区分 | 所見 (要旨) | 裁定 | fix |
|---|---|---|---|---|
| 1 | must-fix | §3 限定 11 が別図 (`t2187_stage2_thread_axis`) の `not_certified` field / `NOT CERTIFIED` 表示を fig2b に誤帰属。fig2b の provenance に同 key は無く、PNG にも表示は無い | real (親も段 5 の自己点検で同一件を検出済み) | 限定 11 を fig2b の provenance の実 field (`read_purpose: HISTORICAL_RAW` / epoch `E0`) を根拠に書き直し、別図の表示は fig2b のものでないと明記 |
| 2 | should-fix | §5.1 冒頭「いずれも provenance と A-3 台帳の記載と byte 一致」は過大 — 較正 4 件はどちらにも収載が無い | real | 「収載のある 14 件 (重複を除く) はその記載とも一致、較正 4 件は再計算値だけ」へ狭めた |
| 3 | should-fix | 「導出索引を数値の出所にしない」の総称が、参考値 (+39.0 / +12.9 / −7.1、+42.2 / +11.7、0.133 pp、既定 adaptive 3 定数、D20 の +0.76%) の引用と一致しない。§5.4 に対応行が無い | real | 冒頭を「論文値と測定数値」に限定し参考値の引用元と再計算していない範囲を明記、§5.2 見出し・§5.4 (新規 4 行)・README 行を揃えた |
| 4 | nit | §0.3「+147.4% も再計算していない」と限定 7 / §5.4 の再計算値が矛盾 | real | §0.3 を「adaptive 分母だけは限定 7 で再計算、他は再計算していない」へ |
| 5 | nit | (P1)〜(P4) を理由に追加測定・図変更・承認を要求する必要はない | refuted (現状維持) | なし |

照合して一致した範囲 (レビューの記録): 論文値 3 と採用点、標本表 24 行 (median・反復 120 値・cv・abort・IPC)、WAL 母集合 (40 行 × 3、
5 段階 × 8、abort 無し、env tag 120 行)、build / 実行 (binary hash 16、cache、command の逐語)、`verify_done` 24 件、provenance (facts 9・
baselines 6・平均比 3・生成日時・条件・epoch)、時刻 6、較正・profile、hash 24 件 (§5.1 18 + §5.2 6)、CCBench 完全 SHA 2 件と 1 commit の
前後関係、D 番号 15 件 + D2120 項 15、非正典 2 本、限定 15 件と要求 4 限定、参照の実在、`947fd160a..1a9096453` が 2 file だけ。
fix commit は `0228673fa` (稿 +21/−10、README 行 1 箇所)。

### 5.2 焦点再レビュー (focus-1、gpt-6-astra / medium、read-only、8 call、153 秒、14:15〜14:18 JST、`outcome: accepted`)

prompt は `prompt-focus.md` (射影 = 1 巡目の所見・fix の `git show`・fix 後の稿・README 行・fig2b provenance・A-3 insight)、逐語出力は
`focus-out.md`。**GO。所見 1〜4 は全件 closed、新規所見なし。** 検算の記録: fig2b provenance の 3 入力とも `read_purpose=HISTORICAL_RAW` /
`campaign_verifier_epoch=E0`、`not_certified` key 無し、figures README に `t2187_stage2_thread_axis` の記述が実在。§5.1 の 14 件 =
provenance 9 + A-3 ledger 11 − 重複 6、較正 4 件は両台帳に無し、18 file の sha256 再計算が稿と一致。参考値の帰属 (A-3 / D20 / figures README) と
submodule log の 1 commit (`dff0f1ef`)、上流 message の `ADD_ANALYSIS=0` unaffected を確認。adaptive 分母 147.35883510937478% を WAL から再計算。
`git diff --stat 1a9096453 0228673fa` は 2 file (+21 / −10) のみ。件数補足: A-3 ledger の artifact 行は 17 (親の prompt の「18 行」は誤り)、
§5.4 の追加は 4 行 (同「5 行」は誤り) — いずれも prompt 側の記述で、稿の集計に欠落は無い。

DW-O16 の 3 巡上限に対し 2 巡 (review 1 + focus 1) で閉じた。

---

## 6. 段 7 以降の記録と運用の気づき

- 記録 = 本 README、worklog fragment `docs/spool/worklog/2026-09-20-dev-wave-p24-static-backoff-sweep-results-1.md` (次の一手差分は空。
  台帳 ID は未起票のまま、新規 T は立てない — 作業は本 wave で閉じ、後続の手番は無い)。decisions / failures の fragment は無し
  (設計判断も新しい失敗型も無い)。受入結果と land は専用 handoff (job dir `HANDOFF.md`) へ集約する。
- 費用: 親の一次資料読み込み (A-3 insight 287 行、figures README fig2b 節、§8 exact claim、D 8 本、WAL 3 × 40 行、較正 JSON 4 本、profile JSON)、
  codex 2 本 (review 15 call / 349 秒、focus 8 call / 153 秒、いずれも gpt-6-astra / medium)、計算ノード job は受入のみ (新規計測 0)。
  wave 全体 13:31 JST 起動 → 段 6 GO 14:18 JST (47 分)。受入・land の所要は handoff。
- 運用の気づき (段 8 候補にはしない — 既知の型): (1) 隔離 session の Bash guard は `sed -i 'Nr file'`・awk の program・`$()` と防護 path の
  同居を拒否する → README への行挿入は Edit tool、集合比較は `sort -u` + `comm` を別 command に分ける。(2) 転記した SHA-256 は目視でなく
  `grep -o '[0-9a-f]\{64\}'` と `sha256sum` の集合比較で検査する (初稿で 1 桁の写し間違いを検出)。(3) figures/README の fig2b 節の直前に
  別図 (t2187) の節があり、「この図は認証されていない … `not_certified`」の段落は t2187 のもの — 節境界を `grep -n "^# "` で切ってから引用する
  (段 5 の自己点検と段 6 レビューの両方が同じ誤帰属を検出した)。
