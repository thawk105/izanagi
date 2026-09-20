# K2 loop 原本消失の下流影響 — 3 巡の主張は派生物と sha256 で支えられ、4 巡目の入力は repo 内派生物から組める。checkpoint の択を裁定パッケージへ (2026-09-20)

authority: none / default_effect: no-state-change (照合結果と裁定パッケージの凍結記録。可変状態の正本は worklog 末尾と現行 phase doc)。

一次資料 (wave `dev-wave-k2-loop-originals-lost-downstream`、基準 HEAD = local main `7baf3f375`、2026-09-20 20:52〜 JST、docs-only、実装差分ゼロ)。
段 1 brief は `reviews/s1-brief.md`、段 6 レビューは `reviews/`、実測の逐語は `materials/reconstruction-log.md`。
job dir (repo 外) は `/home/SFC/tanab/.claude/jobs/cc931155/`。起票 = 記録 wave `dev-wave-cleanup-backup-loss-record` (本 wave 着手時点で未 land、
branch tip `f43322f8a`) の worklog fragment の新規 T「K2 loop 原本消失の下流影響」(採番は fold が行う。本 wave は番号を書かない)。

## 0. 一行で・主張すること・しないこと

**2026-09-20 19:25 JST に K2 手動 loop round 2 / round 3 / roundtrip の campaign 原本 (`submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-409e13f8/` の
WAL・`agent_outputs.jsonl`・`loop_state.json`・`s4_loop_digest.txt`・`campaign.lock`・受領証) が消失した** (事故の一次資料 = `output/insights/2026-09-20/cleanup-backup-loss-record/README.md`、
記録 wave の erratum 節 = `2026-09-19/k2-loop-round3`・`2026-09-18/t2746-k2-loop-round2`・`2026-09-16/t2588-k2-loop-roundtrip`)。本 wave は、その前提で
論文ストーリー §8 B-6 / B-9・fig12・[T-2808] fig12b・層 3 材料レポート・[T-2795] 4 巡目の各主張について「要る一次資料 / 残存資料 / 現在確認できる範囲 / 要る限定」を
実測で定め (§2)、4 巡目の入力元の択を裁定パッケージにした (§4)。

主張すること (本 wave の実測、§1・`materials/reconstruction-log.md`):

- **3 巡すべての原本の sha256 と bytes は消失前の同日に 3 巡稿 §5.1 が再計算して記録している。** 記録 wave の README §3 は「roundtrip は原本消失、sha256 も無い (値までしか遡れない)」
  「round 2 の `campaign.lock` は照合不能」と結論しているが、これは roundtrip / round 2 の insight に sha の記載が無いことから導いた結論で、**3 巡稿 §5.1 に記録があるので本 wave はこの
  2 つの結論を補正する**: roundtrip は 5 file とも sha256 (と bytes) まで遡れる (bytes の再検算はできない)、round 2 の `campaign.lock` は t2746 job dir `scratch-campaign/` の写しが記録値
  `fc7acaca…` と **byte 一致**する。記録 wave の file は本 wave の所有外なので書き換えず、差はここに置く。
- round 3 の `loop_state.json` (`917ba3d3…`、255 B) は repo の `materials/run-summary.json` から、round 2 / 3 の本走 `agent_outputs.jsonl` (`804c62c7…` 34,017 B / `66d3e737…` 32,979 B) は
  repo の `layer3_report.json` から、harness の writer と同じ形式で **byte 一致で再構成できる** (round 2 の scratch 写しで手順を検算)。
- round 2 / 3 の WAL 5 record は `layer3_report.json` の `variants[].events` と**内容同一** (canonical ref 5/5 が `materials/wal-refs.json` と一致) だが、
  payload の key 順 (挿入順) が sorted 写しから戻らず **bytes は再構成できない**。digest は repo に逐語が無い。
- [T-2795] pair 走 (campaign `b24749ae`) の原本 5 file は `submit-tree-pair` に無傷 (sha 5/5 一致) だが、その worktree は unlocked で撤去された候補 1 と同型である。
  本 wave は 21:24 JST に同原本 (campaign dir 5 file + claim 1 file) を T-2795 の job dir `originals-copy-20260920/` (repo 外) へ byte 複製した (MANIFEST に sha256、6/6 一致)。
  worktree の lock は未実施 (裁定パッケージ付随項)。
- 4 巡目は harness が round 3 の tree を `load_loop_state` で再開する設計ではない (round 3 自身が round 2 の tree を「`start_wall` 超過で入口停止」として fresh tree + 新 WAL で走り、
  前巡の状態は親の射影で運んだ)。射影に要る入力 (whiteboard・current_perf・critic-3 逐語・knowledge-input・受領証 bytes・identity の lock) は**すべて repo 内派生物か無傷の写しにある**。

主張しないこと: 3 巡の値・判定・結論の変更、再走の必要、稿の書換え、過去結果の無効化 (規律 7)。再構成物を「原本」とは呼ばない (派生物から作った、記録 sha256 と一致する複製)。
digest の再描画可能性は未実測。4 巡目の認可・予算 (D2172 項 3 (iv)、ユーザー) と pair 修復 (D2187、別 wave) は本 wave の外。

## 1. 前提 — 何が消え、何が残っているか (記録 wave の損失表を本 wave の実測で補正)

記録の出所: 原本 sha256 / bytes = 3 巡稿 §5.1 (2026-09-20 に再計算、消失前)。残存の実測 = 本 wave (`materials/reconstruction-log.md`)。
「bytes 一致」= sha256 が記録値と一致する file が今ある。「内容同一」= canonical 化した内容が一致するが bytes は戻らない。「値のみ」= 転記された数値だけ。

| 巡 (campaign `409e13f8`) | file | 原本 sha256 (bytes) | 現況 | 残存資料と本 wave の照合 |
|---|---|---|---|---|
| 1 roundtrip (t2588) | `runs/wal.jsonl` (5 record) | `ac12b80f…` (7,053) | 消失 | **値のみ** (sha 一致 file は走査 (a) で 0 件): 3 巡稿 §2.1 の terminal record、insight README、`evidence/attempt-0001/job.stdout` の要約行、roundtrip の `materials/planner-input-2.json` の `current_perf` (719,324.5 tps / 7.75 %) |
| 1 | `loop_state.json` | `e6b819f3…` (256) | 消失 | **内容の一部** (sha 一致 file は走査 (a) で 0 件): whiteboard 1 entry (`iteration 1 / decrease / medium / success / delta_pct null`) が roundtrip の `materials/planner-input-2.json` の `whiteboard` (親の射影) に残る。`start_wall` / `reverse_recommendations` の値は走査 (a) の全 file に無い (語 `start_wall` を含む file は round 3 / pair の `run-summary*.json`、round 2 scratch の `loop_state.json`、設計議論の codex event log・diff だけで、roundtrip の値ではない) |
| 1 | `s4_loop_digest.txt` | `1d834279…` (1,893) | 消失 | **無し** (sha 一致 file は走査 (a) で 0 件。critic-1 逐語 `verbatim/critic-1.md` は digest を引用するが逐語複製ではない) |
| 1 | `campaign.lock` | `48520c2b…` (8,307) | 消失 | **無し** (sha 一致 file は走査 (a) で 0 件)。同 identity `409e13f8` の lock は round 2 の写し (`fc7acaca…`、別 bytes) が残るだけで、round 1 の bytes は無い |
| 1 | 受領証 | `c42dc712…` (1,317) | 消失 | **bytes 一致**: 3 巡と pair 走で同一 bytes。scratch (round 2) と `submit-tree-pair` に現物 |
| 2 round2 (t2746) | `runs/wal.jsonl` | `03ac8508…` (7,057) | 消失 | **bytes 一致**: `dev-wave-jobs/dev-wave-t2746-k2-loop-round2/scratch-campaign/runs/wal.jsonl` (mtime 09-18 08:00)。加えて `layer3_report.json` の events と内容同一 (canonical ref 5/5) |
| 2 | `runs/agent_outputs.jsonl` (4 行) | `804c62c7…` (34,017) | 消失 | **bytes 一致で再構成可**: `layer3_report.json` の `agent_outputs` 4 event を `ts` 昇順に canonical 行で並べると sha 一致。scratch の AO (`1866ebc8…`) は 08:00 の別走で ts だけが違う |
| 2 | `loop_state.json` | `03ebaf94…` (255) | 消失 | **bytes 一致**: scratch |
| 2 | `s4_loop_digest.txt` | `a0a4c204…` (1,938) | 消失 | **bytes 一致**: scratch |
| 2 | `campaign.lock` | `fc7acaca…` (8,307) | 消失 | **bytes 一致**: scratch (記録 wave は「照合不能」と書いたが、3 巡稿 §5.1 の値と一致) |
| 2 | 受領証 | `c42dc712…` | 消失 | **bytes 一致**: scratch |
| 3 round3 | `runs/wal.jsonl` | `eb8927b7…` (7,057) | 消失 | **内容同一**: `layer3_report.json` の `variants[0].events` 5 record の canonical ref が `materials/wal-refs.json` と 5/5 一致。bytes は payload key 順が戻らず不一致 (再構成 7,057 B、sha `2e97f644…`) |
| 3 | `runs/agent_outputs.jsonl` (3 行) | `66d3e737…` (32,979) | 消失 | **bytes 一致で再構成可**: `layer3_report.json` の `agent_outputs` 3 event から |
| 3 | `loop_state.json` | `917ba3d3…` (255) | 消失 | **bytes 一致で再構成可**: `materials/run-summary.json` の `loop_state` を writer の key 順 + `indent=2` で直列化 |
| 3 | `s4_loop_digest.txt` | `f993251d…` (1,939) | 消失 | **無し** (sha 一致 file は走査 (a) で 0 件、round 2 digest の先頭 200 B を含む file も走査 (b) で 0 件)。critic-3 逐語と `run-summary.json` に `digest_sha256` の記録。固定 checkout での再描画は未実測 |
| 3 | `campaign.lock` | `f1ab4966…` (8,307) | 消失 | **無し** (sha 一致 file は走査 (a) で 0 件)。同 identity `409e13f8` の lock は round 2 の写し (`fc7acaca…`、別 bytes) が残るだけ。`layer3_report.json` の `artifact_refs` に sha 記録 |
| 3 | 受領証 | `c42dc712…` | 消失 | **bytes 一致**: scratch / `submit-tree-pair` |
| pair (T-2795、campaign `b24749ae`) | WAL / lock / loop_state / digest / 受領証 | `b5754f98…` / `962ef7d7…` / `a8c6a8b6…` / `8bde66fa…` / `c42dc712…` | **現存** | `dev-wave-jobs/dev-wave-t2795-k2-pair/submit-tree-pair/…/p3-s4-loop-s4-autonomous-b24749ae/` で 5/5 一致 (21:00 JST)。worktree は unlocked・未追跡 `output/exploration/` あり |

不在の断定の範囲 (`materials/reconstruction-log.md` §6・§8、生 stdout は `materials/reconstruction-stdout.txt`):
走査 (a) = 2026-09-20 21:23 JST、repo の K2 insight dir 4 つ (`2026-09-16/t2588-k2-loop-roundtrip`、`2026-09-18/t2746-k2-loop-round2`、`2026-09-19/k2-loop-round3`、
`2026-09-20/t2795-k2-pair-attempt`) と repo 外 job dir 2 つ (`dev-wave-jobs/dev-wave-t2588-k2-loop-roundtrip/`、`dev-wave-jobs/dev-wave-t2746-k2-loop-round2/`、
submit-tree は撤去済み) の全 615 file について、roundtrip 5 file + round 3 の lock / digest / WAL の sha256 一致と、語 `start_wall` / `reverse_recommendations` の有無を見た
(sha 一致は round 2 scratch の受領証 1 件だけ)。走査 (b) = 同日 21:0x JST、repo の insight dir 3 つ (round3 / t2746 / t2795) の全 file について round 2 / 3 digest の sha 一致と
round 2 digest 先頭 200 B の包含を見た (0 件)。他の job dir・他ユーザー領域・Lustre snapshot (無い、記録 wave) は走査していない。

## 2. 主張ごとの対応表 (成果物 1)

「要る限定」は、各主張を今後書くときに添える文であり、稿・図の既存 bytes は変えない (規律 7、凍結物)。

| 主張 | 要る一次資料 | 残存資料 (t2746 scratch の sha 一致分を含む) | 現在確認できる範囲 | 要る限定 |
|---|---|---|---|---|
| **B-6 (a)** 3 巡が閉じた: 各巡 `serializable` / certified / anomaly 0 / `continue` (20 → 25 → 10) | 各巡 WAL の `verify_done` / `bench_done` / `commit` record | round 2: WAL bytes 一致 (scratch)。round 3: WAL 内容同一 (`layer3_report.json` events、canonical ref 5/5) + `run-summary.json` の `verify` / `bench` / `records`。round 1: 値のみ (3 巡稿 §2.1、`evidence/job.stdout`、`compute-result.json`) | round 2 は原本 bytes まで、round 3 は canonical 内容まで、round 1 は転記値と job 出力まで再検算できる | 「round 3 / roundtrip の WAL 原本 bytes は消失 (2026-09-20)。round 3 は材料レポートの record と canonical ref で、roundtrip は転記値と job 出力で裏づける」 |
| **B-6 (b)** 診断が「届いた」: planner-4 / coder-4 入力に `k2_critic_diagnosis` の exact 6 field が実在し critic-2 逐語 (`d2b2ab77…`) から作られた | `materials/diagnosis-4.json`・`planner-input-4.json`・`coder-input-4.json`・round 2 `verbatim/critic-2.md` (全部 repo tracked) | 全部残存 (sha 実測: diagnosis `7b742268…`) | 消失前と同じ範囲で再検算できる (原本に依存しない) | 追加の限定は不要。既存の限定 (届いた ≠ 効いた、同 job stock 未達) のまま |
| **B-6 (c)** 規律 6 の検査: 各巡 role の `instruction_like_content_detected=false`、critic の「指示めいた文字列は無い」 | role 逐語 (`verbatim/`) と、critic が読んだ digest / WAL / `loop_state.json` / 受領証 / `campaign.lock` (critic-3 の読取対象は 3 巡稿 §2.4 表の 5 種) | 逐語は全部 repo。critic-3 の読取対象のうち bytes で残るのは受領証 (同一 bytes) と `loop_state.json` (再構成、sha 一致) だけ。digest (`f993251d…`) は無く、WAL は内容同一まで (bytes 不一致)、round 3 の lock (`f1ab4966…`) は無い (同 identity の round 2 写し `fc7acaca…` は別 bytes で代用にならない)。critic-2 (round 2) の読取対象 (digest + WAL + lock) は scratch に bytes 一致で残る | role 側の自己申告は全部再読できる。critic-3 の読取対象を bytes で再現できるのは受領証と `loop_state.json` だけで、digest・lock は不可、WAL は canonical 内容まで。critic-2 の読取対象は bytes まで再現できる | 「critic-3 の読取対象のうち digest と `campaign.lock` の bytes は消失 (sha256 の記録のみ)、WAL は材料レポートの record で内容同一まで」を書く。判定は当時の記録による (元々「自己申告」の限定つき) |
| **B-6 (d)** 同 job stock 対照は未達 (3 巡とも、pair 初投入でも) | 3 巡: 各巡の記録 (未達の理由 = 既存 S4 口に stock 結線なし、各巡 README と 3 巡稿 §2.2 表) と各巡 WAL (stock record 不在)。pair: pair 走の WAL (stock record 不在) と `evidence/`、T-2795 insight | 3 巡: 記録は repo。WAL は round 2 = bytes 一致 (scratch)、round 3 = 内容同一 (材料レポート)、round 1 = 値のみ (§1)。pair: 原本は現存 (5/5 一致) + 21:24 JST の byte 複製 (T-2795 job dir `originals-copy-20260920/`) | pair 試行の未達は原本で完全に再検算できる。3 巡の未達は「stock record が無い」ことを round 2 は bytes、round 3 は canonical 内容、round 1 は転記値で確認でき、理由は各巡の記録による | 「3 巡の未達は各巡の記録と残存 WAL (round 1 は転記値) による。pair 走の原本は `submit-tree-pair` (unlocked) と job dir の写しにあり、lock は付随項 (P2)」 |
| **B-9 (c)** 機序仮説層 v3 が K2 2・3 巡目に同型適用、`certifying_input=false`、`source_refs` 10 / 9、双射通過 | `layer3_report.json` (round 2 `f6dca3b9…`、round 3 `c37fda1f…`) と、その入力 (WAL・AO・loop_state) | レポートは repo。入力: round 2 は WAL / loop_state bytes 一致 (scratch) + AO 再構成可、round 3 は WAL 内容同一 + AO / loop_state 再構成可 | レポートの記載 (件数・refs・certifying_input) はそのまま読める。**「verifier 経由の fresh rebuild 深い一致」(story §8 B-9 (b) が「実装済み」と書く経路) は、原本 root が無いので round 2 / 3 とも現物に対しては再実行できない。** round 2 は scratch + 再構成 AO で root を復元すれば可能 (未実測) | 「材料レポートの fresh rebuild は原本 root の消失により再実行不能 (round 2 は写しから復元すれば可能、未実測)。レポートは非 certifying の二次 view であり結論に影響しない」 |
| **fig12** (3 巡のデータフロー説明図) | 稿 `results/2026-09-20-k2-manual-loop-three-rounds.md` (`caption_source` sha `1b0f6f56…`)、流れ JSON、role frontmatter 3 file | 全部 repo。provenance の入力に campaign 原本は無い | 生成器を再実行して同 bytes を得られる (稿と JSON が不変なら) | 追加の限定は不要。図の caption 固定文 8 つのまま。「図の入力は稿と JSON であり原本 bytes に依存しない」を figures/README 側に書く必要も無い |
| **[T-2808] fig12b** (4 巡目 = 同 job stock 対照ありの巡を描く後継図、裁定前は起動しない) | 4 巡目の稿 (未存在) と流れ JSON | 未着手 | 影響なし。4 巡目が走れば、その巡の原本は新 tree にできる | 4 巡目の稿を書くとき「round 3 からの入力は派生物由来」(§4 の択に従う文) を 1 行入れる |
| **層 3 材料レポート** (`layer3_report.json` そのもの、round 2 / 3) | 自身 (repo tracked) | 残存、sha 一致 | 中身の読取・引用は影響なし。`admission_decision.attempt_receipt_sha256s` 等が指す repo 外 file は round 3 について無い | 「レポートが指す campaign root は消失、レポート自身は不変」 |
| **[T-2795] 4 巡目** (round 3 からの再開、D2172 項 3 (iv)) | 親の射影入力: round 3 の whiteboard・`current_perf`・critic-3 逐語・knowledge-input・受領証 bytes・identity の lock (§3) | whiteboard / current_perf = `run-summary.json`、critic-3 = `verbatim/critic-3.md`、knowledge-input = `materials/`、受領証 = scratch / `submit-tree-pair`、lock = `submit-tree-pair` (`b24749ae`) と scratch (`409e13f8`) | **必要な入力は全部ある。** harness の checkpoint 再開は元々使っていない (§3) | 入力元は §4 の裁定に従う。択 A なら 4 巡目の記録に「入力は round 3 の派生物 (repo tracked、sha 照合済み) から組んだ。round 3 の原本 bytes は消失」を、択 B / C なら実際に選んだ入力元とその原本の所在を書く |

## 3. 4 巡目の入力元 — 事実

- **各巡は fresh tree + 新 campaign dir + 新 WAL (iteration 1) で走っている。** round 3 の記録: 「round 2 の tree (`d2ebef7a4`) は続行不能 (checkpoint の `start_wall` が 39 時間前で
  `MAX_WALLTIME_S=3600` を超え入口 `check_stop` が `budget-walltime` を返す) なので、round 2 と同型に fresh tree + 新 WAL とした」。round 3 の `start_wall` (1789824041 = 2026-09-19)
  も同じ理由で入口停止する。したがって「round 3 の `loop_state.json` を harness に load させて再開する」形は消失の有無にかかわらず取れない。
- **前巡の状態は親の射影で運ぶ。** round 3 の planner-4 / coder-4 入力 (`materials/planner-input-4.json` / `coder-input-4.json`) は round 2 の whiteboard
  (`iteration 1 / decrease / small / success`) と `current_perf` (687,508.5 tps / 7.40 %) に critic-2 の診断を足したもので、round 2 の `loop_state.json` そのものは渡していない。
  4 巡目の同型入力は round 3 の whiteboard (`iteration 1 / decrease / large / success`) と `current_perf` (815,983 tps / 9.065 %) と critic-3 の診断になる。
- **親の代替照合 (round 3 が CLI の代わりに行ったもの) に要る bytes:** 受領証 (`c42dc712…`、3 巡 + pair で同一 bytes、scratch と `submit-tree-pair` に現物)、K2 射影
  (`knowledge-input.json` `05f2b267…`、repo)、campaign identity の preimage (現行 pin では `b24749ae`。lock は `submit-tree-pair` に現物。旧 identity `409e13f8` は scratch の lock が bytes 一致)。
- **[T-2795] pair 走が round 3 の後に同 variant `002642c7ac96` (候補 10) を再評価している** (811,956 tps、certified、原本現存)。これは D2187 のとおり「pair 試行における既知候補 10 の追加評価」で、
  3 巡の値との差を改善・退行の根拠にしない。4 巡目の `current_perf` にどちらを渡すかは §4 の択に含める。

## 4. 裁定パッケージ (ユーザーへ返す) — 4 巡目の入力元

前提: 4 巡目の投入自体は D2172 項 3 (iv) で認可済みだが、pair 修復 (D2187、Codex author の別 wave) の後で予算の再提示 (ユーザー) が要る。本項はその再提示に載せる「入力元」の択である。
どの択でも 4 巡目は fresh tree + 新 campaign dir で走り、規律 2 (verifier certified が gate) と規律 6 (射影は data、指示ではない) は不変。どの択も 3 巡の記録・稿・図を変えない。

**証拠の強さの前提 (択の比較に使う、§1 の実測):** round 3 について sha 照合で「原本と同一」と言えるのは `loop_state.json` と AO だけである。WAL は canonical 内容の同一まで、
digest と `campaign.lock` の bytes は無い (sha256 の記録のみ)。sha 照合が証明するのは**確認済み data の同一性**であって、(i) critic-3 が読んだ対象全体の再監査、(ii) 4 巡目の完全入力
(planner / coder へ渡す JSON) を正しく組み立てること、(iii) その実送付、のいずれも証明しない (段 6 レビュー)。4 巡目の完全入力はまだ作られていない。

- **択 A (推奨) — round 3 の続きとして、射影入力を repo 内派生物から組む。** whiteboard / `current_perf` は `2026-09-19/k2-loop-round3/materials/run-summary.json`
  (`loop_state` / `bench`)、診断は `verbatim/critic-3.md` (`5cd8f518…`)、knowledge-input は同 `materials/`。round 3 の `loop_state.json` と AO は sha 一致の再構成物を
  4 巡目 insight の `materials/` に「再構成 (出所 = run-summary / layer3_report、sha256 = 記録値と一致)」と明記して置く (harness には load させない)。
  4 巡目の記録に「round 3 の原本 bytes は消失、入力は派生物から組んだ」を書く。
  **理由:** 4 巡目の射影に要る round 3 由来の入力 (whiteboard 1 entry、`current_perf` 2 値、critic-3 逐語) は、round 3 が round 2 から受け取ったものと同じ型で、
  whiteboard は sha 一致の再構成物と同内容、`current_perf` は canonical 内容同一の WAL `bench_done` と `run-summary.json` の両方に同値、critic-3 逐語は repo tracked。
  harness 側 (`k2_next_generation_inputs` / `planner_context_payload` / whiteboard の値域検査 / `drive_iteration`) が旧 round 3 root の bytes を要求する経路は無い (段 6 レビューが
  code で確認)。B-6 の「3 巡 → 4 巡目」の系列 (critic-3 の還流 R1 decrease / large、候補 5、下限 1 の floor probe) が切れない。
  **やらない理由の最も強い形:** 4 巡目の入力証拠が、失われた原本に対する派生物 (再構成物と canonical 内容) に依存する範囲が残る。sha 一致は上の前提のとおり「確認済み data の同一性」
  までで、消失前より弱い provenance の上に次巡を積むことになる。これは択 B が回避できる不利益である。
- **択 B — 別走 (新系列の 1 巡目として始める)。** round 3 の状態を引き継がず、whiteboard を空、`current_perf` を新しい stock 対照 (pair 修復後の同 job stock) から始める。
  **理由:** 次系列の入力証拠を新しい stock 測定から原本まで辿れる。過去 3 巡の証拠が強くなるわけではないが、次系列が失われた過去証拠に依存する範囲は減る (択 A との差はここにある)。
  harness は診断なしの入力も受ける (`k2_next_generation_inputs`) ので、code 上 B を拒む理由は無い。研究目的次第で B を選ぶ合理性はある。
  **やらない理由の最も強い形:** 予定していた critic-3 診断の還流 (3 巡連続で最優先だった R0 = 同 job stock に、pair 修復で初めて答えられる巡) を観測する系列を中断する。
  「別走にすれば消失が無かったことになる」わけではない (3 巡の記録は変わらない)。
- **択 C — pair 走 (`b24749ae`、原本現存) を直前巡として使う。** whiteboard / `current_perf` を pair 走の `loop_state.json` (`a8c6a8b6…`) と WAL (811,956 tps) から取り、
  診断は critic-3 (round 3 の digest に対するもの) を使う。**理由:** 直前評価の原本が現物 (+ 21:24 JST の写し) で残り、現行 identity と一致する。混在を明示すれば A より劣ると一律には言えない。
  **やらない理由の最も強い形:** critic-3 が診断した実測 (815,983 tps) と `current_perf` の実測 (811,956 tps、別走) の対応が変わり、harness (`k2_next_generation_inputs`) は
  両者の走行同一性を照合しないので、型が通ることは整合性の証明にならない。fig12b に描く還流も「round 3 の診断 + pair 走の実測 → 4 巡目」になる。
- **付随 1 項 (P2) — `dev-wave-jobs/dev-wave-t2795-k2-pair/submit-tree-pair` を `git worktree lock` する。** pair 走の原本 5 file + claim の現物で、worktree は unlocked・
  未追跡 `output/exploration/` あり = 撤去された候補 1 と同型。本 wave (隔離 session、他 worktree への git 操作は guard が拒否) では打てないので、次に触る非隔離 session
  (T-2795 修復 wave の段 1、または次の `/cleanup-branches` の前) が 1 command で打つ。**本 wave が 21:24 JST に行ったこと:** 同原本 6 file を T-2795 job dir
  `originals-copy-20260920/` (repo 外) へ byte 複製し、MANIFEST に sha256 を記録した (6/6 一致)。lock は写しではなく、写しは lock の代わりではない (両方要る)。
  既存の `git worktree lock` の適用であり、新しい gate・検査・台帳ではない (段 6 レビューも scope 外に当たらないと判定)。
  同型の `dev-wave-t2698-official-floor-resubmit` は wave 自身の `run-backup/` bundle で実害なし (記録 wave)。
- **付随 2 項 — round 3 の digest 再描画は要らない。** 4 巡目の入力に digest は入らない (critic-3 が読んだ digest は critic-3 逐語に消化済み)。B-6 (c) の限定 1 文で足りる。

推奨 = **択 A + 付随 1 項**。段 6 レビュー (read-only、`reviews/s6-review-1.md`) は「択 A 自体を棄却する技術的根拠は無い」とし、A / B / C の説明の過大を must-fix にした
(本節はその fix 後の文)。

## 5. `docs/paper-story/README.md` の stale 注記に積む文面 (本 wave では README を編集しない)

story 20260920b wave (`dev-wave-paper-story-20260920b`) が同じ節を編集中 (README mtime 20:57 JST、「5 件」へ書き換え済み) なので、衝突を避けて本 wave は README に触れず、
文面をここに置く。積む先は 20260920b 版の land 後の stale 注記 (または同版が吸収)。

> - **K2 手動 loop 3 巡の campaign 原本 (WAL・AO・loop_state・digest・lock・受領証) は 2026-09-20 19:25 JST の cleanup 事故で消失した (F 番号は記録 wave の fold が採番、記録 wave の insight
>   `output/insights/2026-09-20/cleanup-backup-loss-record/README.md`)。** 同版 §8 の B-6 / B-9 と B-6 稿 §5.1 が「権威 bytes (repo 外) … job root」と書く箇所は執筆時点では真であった。
>   3 巡稿 §5.1 は消失前に全原本の sha256 と bytes を再計算しており、round 2 は job dir の写しが bytes 一致、round 3 の `loop_state.json` と round 2 / 3 の AO は repo の派生物から
>   bytes 一致で再構成でき、round 2 / 3 の WAL は材料レポートの record と内容同一 (canonical ref 5/5)、roundtrip は転記値と job 出力のみ。**変わらないこと:** 3 巡の値・判定・
>   結論、稿・図 12 の bytes、同 job stock 対照の未達。変わるのは「原本 bytes を後から再検算できる」強さで、B-6 (a)・(c)・B-9 (c) に限定 1 文が付く。一次資料 =
>   `output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md` §2。

## 6. 検査手順の記録

- 実測の抜粋・要約 = `materials/reconstruction-log.md`、生 stdout の逐語 = `materials/reconstruction-stdout.txt`。使い捨て script は job dir (repo 外) に置き、repo へ入れない
  (probe は Codex author 無しで repo に入れない)。
- 手順の正例: round 2 の scratch 写し (原本 sha と一致済み) に同じ再構成手順を当てて byte 一致 (loop_state / AO の直列化形式)。負例に相当するもの: WAL の再構成は
  同じ手順で不一致 (payload の挿入順) — 「内容同一」と「bytes 一致」を分けて書く根拠。
- 段 6: read-only レビュー 1 本 (`reviews/s6-review-1.md`、NO-GO、must-fix 7 + nit 2、全件採用) → 親が docs を fix (`reviews/s6-adjudication.md`、追加実測 = 走査 (a) と pair 原本の
  複製) → 焦点再レビュー 1 本 (`reviews/s6-focus-1.md`)。
- ListAgents (20:55 JST): 稼働 17 session に [T-2795] の session は無い (entry 1754 で着地済み、`submit-tree-pair` だけ残存)。編集面の重複: `docs/paper-story/README.md` は
  20260920b wave が編集中 → 本 wave は触らない。`docs/phase3.md` は 20260920b wave の版が main より古い (未編集) → 項 4 の [T-2795] 項の直後に 1 行足す。
  記録 wave の編集面 (4 insight の erratum 節 + 新 insight + spool) とは重ならない。

## 7. 言わないこと

- 「原本は復元した」とは言わない。再構成物は派生物から作った複製で、sha256 が記録値と一致することだけを言う。
- 「WAL は再構成できる」とは言わない (内容同一まで)。「digest は再描画できる」とも言わない (未実測)。
- 「3 巡の provenance は消失前と同じ強さ」とは言わない。roundtrip の WAL / digest / lock は値と sha のみで、bytes の再検算はできない。
- 4 巡目の認可・予算・投入時期、pair 修復の設計、cleanup command の改訂 (別 T) は本 wave で決めない。

## 8. 一次資料・工数

- 記録 wave: `output/insights/2026-09-20/cleanup-backup-loss-record/README.md` (未 land、branch `worktree-dev-wave-cleanup-backup-loss-record` tip `f43322f8a`)、
  同 wave の spool fragment (worklog seq 1、failures seq 1)。
- 3 巡稿 `docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md` §2.1・§4・§5.1・§5.2、story `docs/paper-story/2026-09-20.md` §8 B-6・B-9、
  `docs/paper-story/README.md` stale 注記 (4 件)、fig12 `output/insights/2026-09-20/k2-loop-fig12/README.md` + `figures/fig12_k2_manual_loop_dataflow.provenance.json`。
- 3 巡の insight: `2026-09-16/t2588-k2-loop-roundtrip`、`2026-09-18/t2746-k2-loop-round2`、`2026-09-19/k2-loop-round3` (各 `materials/` / `layer3_report.json` / `verbatim/`)。
  pair: `2026-09-20/t2795-k2-pair-attempt`。裁定: D2172 項 3、D2183、D2187、D2155、D2148 項 3。harness: `orchestrator/campaign/p3_s4_loop.py` (`state_to_dict` /
  `save_loop_state` / `drive_iteration`)、`orchestrator/campaign/agent_outputs.py` (`canonical_bytes`)、`orchestrator/campaign/model.py` (`WalRecord`)。
- repo 外: t2746 job dir `scratch-campaign/`、`dev-wave-t2795-k2-pair/submit-tree-pair/`、`cleanup-20260920/candidates-*.txt`。
- repo 外 (本 wave が書いたもの): T-2795 job dir `originals-copy-20260920/` (pair 原本の byte 複製 + MANIFEST)、`dev-wave-jobs/rulings-inbox/2026-09-20-k2-loop-originals-lost-downstream.md`
  (裁定パッケージの控え)。
- 工数: codex 2 本 (段 6 read-only レビュー gpt-6-astra 12 call 180 秒、焦点再レビュー = `reviews/s6-focus-1.md` 冒頭に実測値)、計算ノード job 0、login node の読み取り検査のみ。
