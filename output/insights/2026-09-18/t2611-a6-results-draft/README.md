# [T-2611] A-6 read-heavy 認証 (attempt `a6-20260908b`) の単独 results 稿 — 一次資料 (2026-09-18)

`authority: none` / `default_effect: no-state-change` — これは wave の記録である。可変状態の正本 (worklog 末尾・現行 phase doc)
ではなく、成果物 (results 稿) の値・判定を変えるものでもない。

- wave: branch `worktree-dev-wave-t2611-a6-results-draft`、worktree `.claude/worktrees/dev-wave-t2611-a6-results-draft`
- 起点 main: `302b94796` (commit 時刻 11:01:14 JST、着手直前の local main。worktree 作成は 11:06:31 JST、`.git` の mtime)。
  開始 gate `tools/check_wave_startup.py --mode fresh` は乖離 0 commit で緑
- 種別: docs のみ。成果物は `docs/paper-story/results/2026-09-18-a6-certification-reject.md` (新規) と
  `docs/paper-story/README.md` の results 表 1 行。新しい測定は 0、凍結物の bytes 不変、図は作っていない (A-6 の凍結図は無い)
- 段構成: 軽量版 (`DW-C00`)。段 2・3 は省略、段 5 は親編集、段 6 は read-only codex の敵対レビュー 2 本 + 焦点再レビュー 1 本。
  変異 matrix は実装面差分ゼロで免除 (`DW-S04`)
- job dir (prompt・log・receipt・解析 script): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2611-a6-results-draft/`
- 裁定の出所: D1693 / D1870 / D1993 (項 2・3・4・6) / D2108 / D2120 項 7・15 / [T-2430] の裁定 (反復 attempt を行わない)、
  results 系列の規則 (`docs/paper-story/README.md`)、絶対規律 1・2・7、D12

## §1 着手前実測 (段 1)

一次資料の全件を現物で読み、稿に載せる値をすべて自分で再計算した。

| 項目 | 実測 | 出所 |
|---|---|---|
| tracked 6 file の SHA-256 | `artifact-manifest.json` の列挙と全件一致。`COMPLETE.json` の certification / manifest / protocol 束縛も一致 | `output/insights/2026-09-08_t2411-paper-story-a6-certification/` |
| durable authority の SHA-256 | raw manifest が束縛する 6 file (raw 2・WAL・lock・claim・admissions) と受領証が束縛する 5 file (raw manifest・reservation・compute-result・job.stdout 589,570 bytes・job.stderr 547 bytes) が全件一致 | `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b/` |
| 派生統計 | stock median 10,088,796 / mean 10,132,250.6 / 標本 sd 133,406.6 / cv 0.0132 / 95% CI 半幅 165,646.2。adopted median 9,505,248 / mean 9,565,649.4 / sd 112,221.9 / cv 0.0117 / CI 半幅 139,341.9。効果 −5.7841% (権威値 `-0.057841193339621455` と一致)。cv は WAL `bench_done.cv` と 4 桁一致 | job dir `wal_extract2.py` |
| policy bytes の差 | 走行時 (`8969a7e4…`、commit `ae8a767eb` の file bytes) と公開 (`96ed47d0…`) の JSON 差は `tracked_destination` 1 key、`protocol_sha256` は同一。現行 policy (main `302b94796`) との差は `scheduler.nodes` 1 → 5 で preimage 外、protocol hash 同一 (`_protocol_preimage` の実関数で計算) | job dir `policy_diff.py`、`protocol_hash.py` |
| B-10 3 block | record の `throughputs` から median と効果 (−6.609 / −5.377 / −5.317%) を再計算し [T-2430] insight と一致。6 record とも `official_certification = false`、`correctness_certified = true`、`bnode088`、`977647.nqsv`、source `2a338449b` | job dir `b10_blocks.py` |
| WAL | 20 行 (`build_start` 2・`build_done` 2・`verify_done` 12・`bench_done` 2・`commit` 2)。`verify_done` は全件 `serializable` / `certified` / `anomalies` 0 / `proof_surfaces` X・P present、I absent。abort 率 0.1547 / 0.145 は `bench_done.leading_indicators` | 同 WAL |
| abort 率の規則 | 走行時 source `ae8a767eb` の `orchestrator/calibrator/runner.py` は throughput の中央値に最も近い rep の CCBench `abort_rate` (aborts / (commits + aborts)) を採る (5 標本では median の rep) | `git show ae8a767eb:…` |
| request の時刻 | Created 01:28:55 / Started 01:29:06 / Ended 02:42:03 JST (2026-09-08)、Elapse 4382 秒 | `jobs/rr95/scheduler/job.stderr` の会計出力 |
| 条件関門 | admissions 2 件 (`admitted = true`、`use_class = paper`、`unestablished_meaning_macros = []`)、record_ids 8 件。scheduler stdout に 8 ID が各 1 回現れる (record 本文の出力。schema 化された保存ではないので限定 (iv) は維持) | `condition-gate-rr95.admissions.jsonl`、job.stdout の `grep -c` |
| 限定 (v) の現況 | [T-2630] 実測 (2026-09-16) → D2108 (2026-09-17) が `-dD` + 環境 prefix 除去を main に着地、既存 identity は 8/8 byte 一致。残余 (相対位置・push/pop_macro) は D2120 項 7 で「現状維持 + 限界明記」 | decisions.md、`source_digest.py` の現物 |
| 既存被覆 | results 系列に A-6 単独稿なし (横断稿 2 本が rr95 を併記するだけ)。D2120 項 15 が「単独 results 稿 (T-2611 の型) を使う」と支持。A-6 稿を扱う他 branch・spool fragment なし | `ls docs/paper-story/results/`、`git branch`、`docs/spool/` |

段 1 の brief で親が置いた provisional 裁定: (P1) file 名は A-2 稿に倣い `2026-09-18-a6-certification-reject.md`、(P2) 図の provenance が
無いので派生統計は執筆者が raw 5 標本から計算し式を書く、(P3) 限定 (iv) は tracked 成果物の記述として維持し stdout の出力は補足、
(P4) policy 1 key 差と protocol hash 同一を検算どおり書く。

## §2 稿を書きながら親が直した誤り (段 5、レビュー前)

1. §3.4「判定式も違う」→ A-2 と A-6 は同じ合成規則 (`logical conjunction in policy workload order`) で、違うのは論理積を取る
   workload の集合。
2. §3.5 で D1506 の根拠を「旧環境の較正」と書いた → D1506 (2026-09-02) の根拠は Pegasus 上の非認証較正
   (`2026-09-02_cicada-adaptive-three-constants.md`) で、同決定の「限界」節が「variant 採用の根拠には使えない」と明記。
   旧 `linux-baremetal` の 3 値 (D1993 項 4) とは別物として書き分けた。
3. §4 (v) で「A-6 の `src_token` は新旧どちらの実装でも同じ」と断定していた → 親は再計算していないので「再計算して照合して
   いない」と明記。[T-2752] を「起票されたまま」と書いていたが D2120 項 7 で裁定済み。

## §3 段 6 敵対レビュー 2 本の所見と裁定

read-only codex 2 本 (`gpt-6-astra`、いずれも `outcome = accepted` / `stop_reason = completed`、model_calls 13 / 10)。
逐語は `verbatim/s6-review-A.md`、`verbatim/s6-review-B.md`。**両本とも NO-GO を返し、親は全所見を real と裁定して採用した。**

| 所見 | 内容 | 裁定 | fix |
|---|---|---|---|
| A MF-1 | `high_variance` / `rounds` を raw JSON の出所に帰属させていたが、raw JSON の `performance` に両 field は無く WAL の `bench_done` にある | real | §2.1 の文を出所ごとに分け、§5.3 の 2 行を置換 |
| A MF-2 | §3.4 の A-2 の status / adopted genome を支える一次資料が §5 に無い (「出所は §5 だけ」の宣言に反する) | real | A-2 `certification.json` (SHA-256 `e74d0f87…`) の行を §5.3 に追加。親が同 file の `status` / `cells[].genome` / 復号 policy の `certification_composition` を現物で確認 |
| A N-1 | WAL 行数内訳の「build 2」は event 行数 (build_start 2 + build_done 2) と混在 | real | 内訳を stage 別 5 項に |
| A N-2 | 埋込み policy bytes を「canonical」と呼ぶと producer の `_canonical_json` (別 hash `500b329f…`) と紛れる | real | 「復号した policy file bytes の SHA-256 (canonical JSON 直列化の hash ではない)」に |
| B MF-1 | §2.2 の「退行した adopted cell も certified である — 書けるのは『検査された範囲で正しさを保ち、観測された median で stock を下回った』まで」が、性能と別走行の正しさを引用可能な 1 文に畳んでいる (results 系列の規則違反) | real | レビュー B の是正案 (性能と正しさを別文の 2 段落) に置換 |
| B MF-2 | §5.4 の裁定一覧が D1506 を「旧環境での read-heavy の較正」と書いたまま (§3.5 の修正が §5.4 に及んでいなかった) | real | 「2026-09-02 の非認証較正に基づく、無 backoff と調整済み adaptive の基準線の裁定」に |
| B SH-1 | §3.1 の「一致するのは protocol / …」が認証 protocol と B-10 の測定契約の同一性に読める | real | 「共通するのは CC protocol の Silo、read-heavy、2 genome、5 標本、pin と patch。測定契約が同一という意味ではない。argv の一致は spec による」に |
| B SH-2 | §2.3 の trace 側 aborts / commits の範囲は performance 条件各 5 回だけで、legacy (別 workload) を含まないことが未明記 | real | 範囲を performance 条件に限定し、legacy 各 1 回は別 workload (rratio 50・4 thread・200 tuple・rmw true) で範囲外と明記 |
| B N-1 | 性能表の sd / CI / min–max 列に単位が無い | real | 列名に `(tps)` |
| B 総括 | §0 の主判定文案 (3 文に分けた引用形) | 採用 | §0 に「主判定文 (結果節へ落とすときの形。文を分けたまま使う)」として追加 |

レビュー A は掲載した全数値・hash・識別子・policy 比較を現物から再計算して「一致」を列挙した (派生統計 8 値、正しさ検査 24 整数、
SHA-256 18 件、B-10 6 record、時刻 4 点、argv、perf 観測、限定 (v) の表現)。レビュー B は論点 11 件を「所見なし」と列挙した
(規律 7 の判定保持、表題・§0・README 行の分離、D12、限定 (i)〜(v)、D1993 項 4・6、[T-2430]、D1870、results 系列の規則、追加限定の
不要、用語と scope)。

## §4 焦点再レビュー (段 6、fix 後)

read-only codex 1 本 (`gpt-6-astra`、`outcome = accepted` / `stop_reason = completed`、model_calls 8)。逐語は `verbatim/s6-focus.md`。
**GO。所見 10 行すべて closed、partial / regressed なし、新規所見なし。** fix の検算として、A-2 権威 bytes の SHA-256・`status`・
genome・合成規則、raw JSON と WAL の field 実在、復号 policy の `legacy_correctness`、README 行の「限定 12 件」と §4 の項数、
派生統計 (mean・標本 sd・cv・CI 半幅・min–max・効果) を現物から再計算して一致を確認した。

## §5 検査 (段 6・7)

- `python3 tools/check_docs.py`: 違反なし (段 5 後、fix 後の各 1 回、commit 後に再走)。
- 三軸語走査 `python3 -m orchestrator.campaign.s8b_holdout_freeze search`: rc=0、`conjunction_hits` 空 (新稿は hit_paths に無い)。
- `git diff --check`: rc=0。
- 変異 matrix: 実装面差分ゼロで免除。受入全走は land 経路で 1 走 (結果は land の受領証)。
- 全史 provenance 監査 (`python3 tools/check_ai_provenance.py`、commit `582cf60c0` 後): 11,315 件、新規違反なし、rc=0。
  本 README と spool fragment を含む後続 commit は preflight (`--message-file`) を通し、全史監査は land (`DW-O25`) が再走する。
- spool fragment `docs/spool/worklog/2026-09-18-dev-wave-t2611-a6-results-draft-1.md`: `spool_fold.py --dry-run` rc=0。

## §6 稿が言うこと・言わないこと (要約。正本は稿自身)

- 言うこと: attempt `a6-20260908b` の outer status は `reject`、効果 −5.7841% (1 attempt・各 5 標本の中央値比較)、2 cell とも
  `source_binding_status = bound`、別 trace-enabled 走行で 2 cell とも `certified` (legacy 1 + performance 条件 5、anomalies 0)。
  B-10 read-heavy 3 block (−6.609 / −5.377 / −5.317%) と同符号・同程度 = 近接条件の別実行による履歴的照合。
- 言わないこと: 再現、有意差、floor 超の退行、機序の同定、研究の失敗、read-heavy で stock が最良の証明、A-2 とのプール、
  旧環境・D1506 較正・−4.876% (D1870) との前後比較、反復 attempt の予定。限定は 12 項 (D1993 の (i)〜(iv) + identity 層の (v))。
