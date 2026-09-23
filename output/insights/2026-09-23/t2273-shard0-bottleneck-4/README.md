# [T-2273] [T-2560] 受入 shard-0 律速の再同定 (第 4 回) — 律速は共有 base 構築の「Lustre からの可視 output 複製」で、複製元を計算ノード局所に置いた対照は同一 node の 1 対で W_0 を 123.9 秒 (27.3 %) 縮めた (2026-09-23)

wave `dev-wave-t2273-acceptance-bottleneck-diag` (branch `worktree-t2273-acceptance-bottleneck-diag`)。依頼の逐語は `verbatim/T-2273-origin.md`。**実装差分ゼロ** (D1936 項 35): probe 3 file は Codex author の子 branch にあり repo 外で実行し、repo には逐語 `verbatim/probe-source.md` だけを置く。
標本の時点 (as-of) = 開始 gate 2026-09-23T07:42:52+09:00 (`verbatim/startup-gate.log`)。計測 tip = `3886a1fd3` (as-of 時点の local main)。記録時に local main `46933e4da` へ ff-only で揃えたが、`git diff 3886a1fd3 46933e4da -- orchestrator tools` は空 (docs・insight のみ)。

## 結論 (最初に読む)

1. **律速 (事前登録 `verbatim/s4-ruling.md` §3.1 を適用):** 現行 main の受入 shard-0 replica (R1、request 18929.nqsv、bnode030) で、最大占有 worker gw2 (O_max 289.0 秒) の最大成分は**依存 builder の完成を待つ flock 206.5 秒**だった (item rank 96 `test_t080_delegated_campaign_start_rechecks_receipt[missing]` 261.7 秒 = 待ち 206.5 + base→test copytree 14.5 + verify 0.7 + 残り 40.0、後続 22.7 + 4.7)。L の worker gw40 (`test_t080_failed_launch_preserves_receipt_refusal` 272.1 秒) も同じ待ち 206.5 + 14.6 + 6.1 + 44.8。待ち先の builder (active_v2 key、gw14) の 206.5 秒は **copy 113.4 (builder 内の複製成分の合計。うち可視 output の copytree 90.1) + 発行 subprocess 79.6 + git 13.5**。
2. **形の説明:** 現行台帳では共有 base の **7 key の builder が全部同時 (JUnit 基準 t≈130 秒) に始まり**、どれも 206〜207 秒 (非発行 key 126.9) かかった。これに加えて、検査用の非共有 builder 1 本 (`test_t080_shared_base_builds_real_builder_once_across_processes`、gw20) も t≈130.3 秒に始まり、同じく実 repo の `output/` を複製する。t=0 に並ぶ active_v2 系 node は共有 builder 1 本を flock で待つので、その所要 + 自分の本体がそのまま node の所要になる。同じ構造を、無効になった R2 の A2 (request 19029.nqsv、最大占有 worker の flock 待ち 230.7 秒) と R2'' の A2 (request 19131.nqsv、同 230.9 秒) でも観測した (両 A2 とも copy 137.6〜138.0、共有発行 key の発行 79.2〜79.6)。
3. **copy は CPU でなく待ちが支配 (§3.2):** builder の可視 output の copytree (Lustre 上の `output/` の git 可視集合 29,885 path を列挙し、receipt・draft・floor 等の所定の除外を引いた残りを計算ノードの /tmp (local nvme xfs) へ複製) は 7 本とも同じ 153〜243 秒の区間で 90.1 秒、**self CPU 時間/壁時間 = 0.11 → 「待ちが支配」**。同区間の node 全体は CPU 使用率 0.24、iowait 0.002、run queue 13、Lustre mdc の close は counter `lustre-MDT0000-mdc-ff2286b3c3d71800/md_stats:close` で 7,362 回/秒 (記録された全 mdc の合計は 7,378 回/秒)。発行 subprocess は子 process 込み 1.0、git は 0.99 で「CPU 実行が支配」。**原因 (Lustre metadata の待ちか、他の何か) は断定しない。**
4. **効果の見込み (事前登録どおりの対照 1 対、R2''):** 同一 node・同一 job で A2 (通常) → staging → X (builder の `_copy_git_visible_output` の複製元だけを、実 repo から作った node-local の git repo に差し替え、実関数を呼ぶ) の順に走らせた。有効性検査は全項目真 (rc 0 両走、outcome 集合一致、全 builder の可視集合 digest と件数が A2・X・staging で一致、clean、others 0、record-error 0)。

   | 量 (秒) | A2 | X | A2 − X |
   |---|---:|---:|---:|
   | W_0 | 454.6 | 330.7 | **123.9 (27.3 %)** |
   | O_max (gw2 → gw2) | 314.7 | 191.1 | 123.6 |
   | L (gw40 → gw40) | 295.6 | 174.2 | 121.4 |
   | pre / post | 129.8 / 10.06 | 129.4 / 10.07 | 0.4 / −0.01 |
   | builder 内の複製成分の合計 (共有 7 key とも) | 138.0 | 11.1 | 126.9 |
   | うち builder 内 copytree の合計 | 117.1 | 8.5 | 108.5 |
   | うち可視 output の copytree 単体 (共有 7 key、生 span) | 111.4〜111.5 | 2.7 | 108.7〜108.8 |
   | builder の構築 (共有発行 key) | 230.8〜230.9 | 104.3〜104.6 | 126.3〜126.7 |
   | 発行 subprocess (共有発行 key) | 79.2〜79.4 | 79.1〜79.4 | ≈ 0 |
   | git (依存 builder = active_v2 key) | 13.5 | 13.9 | −0.3 |
   | staging (X の前、別欄) | — | 43.9 | ΔW_0 − staging = 80.0 |

   X の差し替えは共有 7 key の builder と非共有 builder 1 本 (gw20) の計 8 本に効いた (可視集合の記録は A2・X とも 8 件で digest 一致)。D357 の 1 走比較として 10 % 以上の短縮。**1 対の観測であり有意差判定ではない。** staging (git clone `--no-local --no-checkout` + `output` の checkout + 全 file の bytes 照合) は計測の準備であって実装案の費用ではないが、目安として差し引いた値も併記した。
5. **次の一手 (1 つ、§3.3 と追補 1 の採否基準を満たした):** **「t080 共有 base の可視 output 複製元を計算ノード局所に置く」** (共有 7 本 + 非共有 1 本の builder が開始直後に同時に Lustre から可視 output を複製するのをやめる)。複製する集合・object store・index は変えないので D2068 の却下 3 案 (whitelist / alternates / 独立 index) には当たらない。ただし**実装の形 (いつ・誰が局所の写しを作るか、未 commit の可視 file をどう扱うか、session 間の再利用をするか) は未設計**で、X の staging は計測用の手段にすぎない。実装 wave は隣接対の実受入で効果を測ってから land する形になる (D357 / D1936 項 35)。
6. **その次の律速:** X でも最大占有 worker gw2 の最大成分は flock 待ち (104.6 秒) で、その依存 builder (active_v2 key) は copy 11.1 + git 13.9 + **発行 79.4 (CPU 支配)**。copy を除くと発行 subprocess が構築の 3/4 を占める。発行の内訳 (draft / validate / finalize / verify / gate_check) は測っていない。
7. **過去 A の 189.98〜208.09 秒 (§3.4):** 再走していない。T-2817 Job B (旧台帳) では t≈116 秒・181 秒に始まった builder の copy が 64.2・33.0 秒で、t≈62 秒に 5 本同時に始まった builder の copy (100.4 秒) より短かった。「A の同系 node は、builder が開始直後の同時構築と重ならなかった分だけ短かった」と整合するところまでで、原因は未同定のままとする。
8. **外れの明記 (§3.5):** 今回の 4 走 (R1 / R2 の A2 / R2'' の A2 / X) はどれも **pre が 128.8〜130.2 秒**で、T-2825 の実受入 (62.6〜64.4 秒) の約 2 倍だった。W_0 の絶対値 (A 系 429.4〜454.6) も T-2825 B の上端 344.9 を 24.5〜31.8 % 上回る。pre 倍増の原因は分解していない (probe の plugin・資源標本の負荷、node や Lustre の状態のいずれも候補)。**対比較の差 (ΔW_0) は同 job 内で pre がほぼ同じ (差 0.4 秒) なので pre の影響を受けにくいが、X の W_0 330.7 秒を「受入が 5 分を切る」の根拠には使わない。**

## 1. 依頼と不変条件

依頼 (逐語 `verbatim/T-2273-origin.md`): T-2825 の refresh 後も shard-0 の W_0 は 310.7〜344.9 秒で 5 分上限を超えている。最大占有 worker の形 (t=0 から並ぶ active_v2 系 8 node の後に 20〜31 秒の item) から律速を特定し、効果の見込みを実測で示して次の一手を 1 つ選ぶ。標本の時点を固定する。T-2845 (Path.resolve 縮約) は D2219 項 4 で起こさない。未実測の prewarm・共有 cache は先行実装しない。既存の検査は削らない。診断 job は計算ノード。2 node 時間以上なら確認。

守ったこと: production・test・conftest・台帳・既存検査は 1 byte も変えていない。観測 wrapper は実物へ同じ引数を 1 回渡す (DW-O14)。X の差し替えは「対照用の差し替えであり観測 wrapper ではない」と span と docstring に明記し、builder が実 repo root で呼ぶ 1 箇所 (`test_s8b_oracle_driver.py` の `_build_t080_stub_free_e2e_repo` 内) だけに効く (他の 2 箇所の呼出しは fixture 側の root を渡すので差し替わらない)。prewarm・共有 cache は実装していない (X は計測の対照)。

## 2. 段 3 相談と段 4 裁定 (逐語 `verbatim/s3-consult-*.md`、`verbatim/s4-ruling.md`)

段 1 brief (`verbatim/s1-brief.md`) の仮説 P1 「同時構築本数に応じて copy が伸びる IO 競合」は、段 3 相談 (修正後 GO、所見 7 件) の C1 が T-2786 §4 (5 本同時の copy は collection 中なら 30〜35 秒) を反例に挙げ、撤回した。他に C2 copy 計器の分割、C3 対象を最大占有 worker とその依存 builder へ、C4 無負荷 node の k 曲線 (Job C) の削除、C5 過去 A は再走しない、C6 R を 3 本同時にしない、C7 TMPDIR を継承し費用を実測で再見積り — を全件採用した。

段 6 は一次資料から再抽出して照合する独立 read-only レビュー 1 本 (`verbatim/s6-review-{prompt,out}.md`、修正後 GO)。must-fix 1 (R1 の可視 output copytree と R2'' の builder 内 copytree 合計を同じ量として並べていた)、should 4 (超過率の流用、R2 と R2'' の待ち・key の取り違え、非共有 builder の記載漏れ、可視集合件数と実複製件数の区別)、nit 2 (test 件数、mdc counter の範囲) を全件 real として本 README と worklog fragment に反映した。

## 3. 計測

| job | request | node | Elapse | 内容 | 結果 |
|---|---|---|---:|---|---|
| R1 | 18929.nqsv | bnode030 | 514 秒 | smoke → A (観測のみ) | 有効 |
| R2 | 19029.nqsv | bnode025 | 954 秒 | smoke → A2 → staging (/tmp) → X | A2 有効、**X 無効** (計算ノード /tmp のユーザー quota 超過 `Errno 122` で test の一時 dir が作れず failed 21 / errors 25) |
| R2' | 19108.nqsv | bnode005 | 84 秒 | 同 (staging を /scr へ) | smoke 後の clean 検査で停止 (**親が走行中に wave 木へ insight の下書きを書いた**。probe の欠陥ではない) |
| R2'' | 19131.nqsv | bnode081 | 1,046 秒 | 同 (/scr/<user> を作って staging) | **有効** (結論 4) |

- 合計 Elapse 2,598 秒 ≈ 0.72 node 時間 (受入を除く)。2 node 時間未満。
- 共通条件: 受入 shard-0 と同じ argv (`tools/run_tests.py orchestrator/tests -n 48 --dist loadgroup --junitxml=<session>/shard-0/junit.xml -p tools.acceptance_shards -p no:cacheprovider` + 観測 plugin)、`acceptance_shards.create_session(repo, 3)` の shard 0/3、TMPDIR は dispatch 環境から継承 (未設定 → /tmp、`/` の nvme xfs、user quota 100G)、`PYTHONDONTWRITEBYTECODE=1`。**replica であり受入ではない** (session は受入共有 root に作られる。受入成果物の読み取りでは除外する)。
- 計器: 共有 base の builder・copy (列挙 `copy.list` / 実 copytree `copy.copytree` / その他)・git・発行・flock・base→test copytree・verify の span、span ごとの self / children CPU 時間、1 Hz の資源標本 (`/proc/stat`、`/proc/loadavg`、Lustre mdc md_stats。llite stats は読めず欠測)。analyzer の rc=1 はこの資源欠測だけによる。
- R2 の X 無効後の参考値 (判定に使っていない): quota 超過の前に走った X の builder は copy 4.2 秒・構築 104.1 秒だった。

## 4. 限界・言わないこと

- R2'' は 1 対。X は A2 の後に走るので後走の warm を受けうる (pre・post・残りの成分は A2 と X でほぼ同じだった)。隣接対の実受入 (D357 の形、複数対) は実装 wave が行う。
- 絶対値は結論 8 の外れを含む。X の W_0 から「5 分を切る」とは言わない。
- copy の待ちの原因 (Lustre metadata・client lock・他 worker の Lustre 操作との干渉のどれか) は計器の分解能より細かく、断定しない。
- staging の方法 (clone + checkout) と所要 43.9 秒は計測用で、実装の費用ではない。実 tree が dirty (未 commit の可視 file あり) のとき X は止まる作りで、実装側の扱いは未設計。
- 発行 subprocess (79 秒) の内訳は未測定。
- 受入全走ではなく shard-0 の replica だけを測った。shard-1 / 2 の wall は測っていない (T-2825 では 190〜219 秒)。

## 5. この dir の中身

- `verbatim/T-2273-origin.md` 依頼、`verbatim/s1-brief.md` 段 1、`verbatim/s3-consult-{prompt,out}.md` 段 3、`verbatim/s4-ruling.md` 段 4 (追補 1 = R1 の読みと R2 の事前登録)、`verbatim/s5-*` 実装子の prompt と報告 (author / author-r2 / fix1 / fix2)、`verbatim/s6-review-*` 段 6 レビュー、`verbatim/NORMALIZATION.md` 逐語の行末空白の可逆正規化、`verbatim/probe-source.md` probe の逐語、`verbatim/startup-gate.log` 開始 gate。
- `analysis/` 機械集計の抜粋 (`r1-summary.json`、`r2c-pair-summary.json`)。全文と生 span・資源標本は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-acceptance-bottleneck-diag/` (`job-out-r1/`、`job-out-r2c/`、`analysis/`) にある (repo 外、大きいので写さない)。

## 6. 再現手順

1. probe を Codex author の branch (`author-t2273-probe-fix2` の終端 `7f38ac7fd`) から repo 外の dir へ取り出す (逐語は `verbatim/probe-source.md`、R2'' で走った版と同一)。
2. `python3 tools/pegasus/dispatch_compute.py --task generic --walltime 00:50:00 -- python3.10 <probe>/t2273_replica_runner.py pair --repo-root <clean な wave 木> --probe-dir <probe> --out-root <out> --job-tag <tag>`。
3. `python3.10 <probe>/t2273_replica_analyze.py --pair-dir <out> --markdown <md> --json <json>` (単走は `--run-dir <out>/A`)。
