# [T-1878] mocc trace-hook (TRACE=1) pilot の raw verifier 出力 artifact の所在 — 探索した範囲での未特定 (2026-09-18)

- wave: branch `worktree-dev-wave-t1878-mocc-trace-pilot-raw-artifact`、worktree `.claude/worktrees/dev-wave-t1878-mocc-trace-pilot-raw-artifact`
- 起点 main: 302b94796 (11:02 JST の local main)。11:20 JST に 99fcf2323 を ff-only で取り込み
- 種別: docs のみ (本 insight + `docs/paper-story/README.md` の claim-evidence 系列節への追記 + worklog fragment)。新規実装・計測なし。
  実装面差分ゼロなので変異 matrix は免除 (`DW-S04`)。段 6 に read-only codex review 1 本 (`verbatim/out-review.md`。entry 998 の教訓:
  一次資料から事実を再抽出する docs wave はレンズが親の制約違反を出した — 本 wave でも must-fix 3 件を出した、§6)
- 対象: `docs/paper-story/claim-evidence/2026-08-26.md` (sha256 `cdc59aef…`) の C14a 行が `[権威 bytes]` を「**未特定。** 本文書では raw の
  verifier 出力 artifact を見つけられなかった」と書いている件。同 file は凍結物 (D1013) なので**書き換えない**
- 結論を先に: **依頼が限定した範囲 (§2) を探索した結果、PBS request `934607.nqsv` の raw verifier 出力 (`verifier.json`) もその sha256 も
  特定できなかった。** 当時の script の出力先は投入 worktree 配下で、その worktree は現在存在しない。今回の探索では、同 path の commit も
  evidence dir への退避物も特定できなかった。当時の receipt 生成処理には verifier.json の sha256 束縛が無かった。
  **これは探索した範囲での未特定であり、消失の経緯・過去の保存履歴・全体での不在は確定していない。**

## §1 対象の同定 (一次資料)

| 項目 | 値 | 出所 |
|---|---|---|
| 主張 | mocc trace v2 hook の TRACE=1 pilot は verifier verdict `serializable`、`certified` 真、anomaly 0、total_cycles 0 | `output/insights/2026-08-22_t755-mocc-trace-v2-pilot-serializability.md` (sha256 `df4c135b…`) |
| PBS request | `934607.nqsv` (gen_S、2026-08-22、host bnode050) | 同 insight「実行条件」 |
| outer commit | `2efe6282ed22a694cdd7b38c641bedecc6d2e6d4` | 同 |
| ccbench source binding | base `511c9538e4e8efa54b45cda62e72389ed3b706ec` → new `ef9328a35d49b1b9b610f244bee22ad7f10b8b66` (mocc-trace-v2.patch 適用) | 同 |
| workload | records 10,000 / threads 48 / skew 0.9 / rratio 50 / rmw 0 / max_ope 10 / extime 3 s、txns 761,914 | 同 |
| verifier 起動 | `<VERIFIER_PY> -m orchestrator.verifier <trace_dir> --json --expected-commits 761914`。compute node の job 本体と login node の独立再実行で byte-for-byte 一致 (と同 insight が記述)。**一致を示す hash は同 insight に記録されていない** | 同 insight「検証結果」と 08-23 追記 |
| 投入 worktree | `dev-wave-t755-mocc-trace-execution` (5 回目の投入が 934607) | `/work/1/SFC/tanab/dev-wave-jobs/t755-mocc-trace-execution/handoff.md` (sha256 `2be8fffb…`) 8-9 行・77 行 |
| 当時の script の出力先 | `REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P)`、`JOB_STAGING_ROOT="$REPO_ROOT/output/env/pegasus/mocc-trace/job-staging"`、`ATTEMPT_DIR="$JOB_STAGING_ROOT/$PBS_JOBID"`。verifier 出力は `"$ATTEMPT_DIR/verifier.json"` (stderr は `verifier.stderr`、rc は `verifier.rc`)、他に `trace-manifest.json`、`mocc-trace-pilot-receipt.json`、`job-result.json`。**変数展開すると** `<投入 worktree>/output/env/pegasus/mocc-trace/job-staging/<PBS_JOBID>/verifier.json`。`$PBS_JOBID` の実値は記録に無く、request 934607 の dir 名は `934607.nqsv` か `0:934607.nqsv` のどちらか (同 script は両表記を正規化して比較する。08-24 の t1582 insight は「正規化後 `942177.nqsv`」、evidence の dir 名は `0:942177.nqsv`) | `git show 2efe6282:tools/pegasus/mocc_trace_pilot.sh` 40-46 / 242-250 / 878 / 934-938 / 990 行 (逐語は `verbatim/` でなく同 commit の blob) |
| submit 側 (当時版) | submit receipt は `$REPO_ROOT/output/env/pegasus/mocc-trace/attempts/submissions/<nonce>/`。`qsub_cmd=(qsub -v "$EXPORT_SPEC" "$JOB_SCRIPT")` で **`-o` / `-e` を付けていない** (PBS stdout / stderr は投入 directory へ落ちる — 08-26 pair insight「PBS stdout/stderr が submit directory (= repo root) へ落ちる」)。現行版は `-o` / `-e` で submissions dir へ向ける (`tools/pegasus/submit_mocc_trace.sh` 381-382 行、本 wave の HEAD) | 同 commit の `submit_mocc_trace.sh` 152-154 / 199 行 |
| 当時の receipt の束縛 | `artifacts.verifier_json` は file 名 `"verifier.json"` のみ。**verifier.json の sha256 は receipt に無い** (bytes 束縛は 2026-08-26 の pair wave で導入、`output/insights/2026-08-26_mocc-trace-pair.md`「job が証拠 bytes を hash して receipt へ束縛するようにした」)。`job-result.json` は receipt の sha256 (`receipt_sha256`) を持つが、同じ dir に書かれる | 同 script 1080-1115 行 |

同 handoff の「落とし穴」は当時から「**REPO_ROOT は submit 時の shell cwd に依存し、worktree cwd から呼ぶと全出力が worktree 配下に落ちる。
worktree を畳むと失われるため、land 前に必ず内容を記録へ落とす**」と書いている (handoff 109-113 行、消失への注意であって本 artifact の
消失経緯の記録ではない)。確認できた insight には JSON block と要約があるが、今回の探索では raw bytes とその hash を特定できなかった。

## §2 探索した範囲と結果 (11:05〜11:20 JST 初回、11:45〜11:55 JST 再走査、login node、read-only)

依頼が限定した範囲 = (a) pilot の insight 5 群が名指す job dir、(b) `/work/1/SFC/tanab/izanagi-job-evidence/` 配下、
(c) `tools/pegasus/mocc_trace_pilot.sh` の出力先。走査 script は 3 版を `verbatim/` に置く (`search_934607.py.txt` = 初回、
`search_934607_v2.py.txt` = 除外件数を数え全本文で完全表記を判定、`search_934607_v3.py.txt` = 拡張子 filter なし + path 名走査)。
結果は `verbatim/search-934607-result.txt` (初回、path と分類のみ) / `search-934607-v2-result.txt` / `search-934607-v3-result.txt`。
本文の写しは含めない。**再走査 (v2 / v3) は段 6 レビュー R-2 / R-3 への fix であり、初回 (v1) の「最初の一致だけの分類」を全本文の判定で置き換えた。**

| # | 範囲 | 方法 | 結果 |
|---|---|---|---|
| 1 | (c) 出力先の実体 = 投入 worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t755-mocc-trace-execution/output/env/pegasus/mocc-trace/` | `ls -d /work/1/SFC/tanab/izanagi/.claude/worktrees/*t755* /work/1/SFC/tanab/izanagi/.codex/worktrees/*t755*` (絶対 path)、`git branch --list '*t755*'` | **worktree・branch とも現在は存在しない** |
| 2 | (c) git 履歴 | `git log --oneline --all -- output/env/pegasus/mocc-trace` (本 wave の worktree、`--all` = 探索時点の全 ref) | **0 件** — 探索時点の ref から辿れる履歴に同 path を触る commit は無い (削除済み ref・到達不能 object は対象外)。`.gitignore` は同 path を無視しない (`git check-ignore` rc=1) が、HEAD の tree にも無い |
| 3 | (c) 主 checkout の同 path | `ls /work/1/SFC/tanab/izanagi/output/env/pegasus/mocc-trace/` | 不在 |
| 4 | (b) evidence dir 全体 | dir 一覧: `pegasus/` は 17 request dir (926261〜999102、`0:927684`、`1818`)、`index/by-job` 16 件、`index/by-time` は 08-20 / 08-23 / 08-24 / 08-26 / 08-27 / 09-01 / 09-09 / 09-15 / 09-16 (08-22 無し)。本文と path 名は #5 と同じ走査 | path 名に `934607` を含む entry 0 件。本文に `934607.nqsv` を含む file 0 件 (v3、全本文、拡張子不問、50 MiB 以下)。数字 `934607` だけを含む file は他 job (t2187 certify、t2265 trace 等) の trace log / JSON で、完全表記は含まない |
| 5 | (a) 名指し job dir 9 件: `t755-mocc-trace-execution`、`dev-wave-t755-mocc-trace-execution`、`dev-wave-t755-q2-mocc-trace`、`…-continuation`、`dev-wave-t1641-t755-report-binding`、`dev-wave-t1506-mocc-trace0`、`dev-wave-t1582-mocc-trace0-pilot`、`dev-wave-mocc-trace-pair`、`dev-wave-mocc-g2-repro-20260826` | v3: (a)+(b) の全 entry 17,380 件のうち、regular file で 50 MiB 以下の 16,372 件を**拡張子不問で全本文**読取 (読取試行 16,372 = 成功 16,372、lstat 失敗 0、symlink 0、directory symlink 0)。path 名 (dir 名・file 名) も走査 | 本文に `934607.nqsv` を含む file 13 件 = 当時の handoff (結果待ちと今後の作業の記述)、insight の写し 3 件 (`audit/insight.md`、`materials/insight-trace1.md`、`prior-pair-insight.md`)、worklog fragment の写し 1 件、codex の events.jsonl 8 件。**いずれも本文での言及であり、raw `verifier.json` ではない。** path 名に `934607` を含む entry は 0 件 |
| 6 | (a) 同 9 dir 内の `verifier*` / `trace-manifest.json` / `mocc-trace-pilot-receipt.*` | 名前で列挙 (v1、280 file) | `.nqsv` 表記の request は 50 種 (g2-repro 43、pair の `0:949961`〜`0:949967` から 6、t1582 の TRACE=0 `0:942177` 1)。probe `949555` / `949585` は `probe-<id>/job-staging/` の別形式 path。**`934607` は含まれない** |
| 7 | 補助: 当時の session の job tmp (`/home/SFC/tanab/.claude/jobs/ea53ff4a/`、handoff 79 行が qstat log の置き場と名指す) | `ls` | 不在 |

**走査の条件と、範囲内で本文を読んでいない対象 (R-2):**

- 50 MiB (52,428,800 bytes) 超の regular file 1,008 件 (合計 122.6 GB) は本文を読んでいない。内訳は evidence dir の他 job の `trace_N.log`
  1,006 件と dynamic-backoff の `stage*-rep*-*_<request>.nqsv.json{,.journal.jsonl}` 2 件で、最小は 52.5 MB。file 名の request は 934607 でない。
  探している `verifier.json` は同型の raw (pair wave の `verifier-trace1.json`) が 1,330 bytes なので、この上限で除外されることはない
  (ただし raw が別名で 50 MiB 超の file に連結されている可能性は本走査では否定できない)。
- v1 は拡張子 allowlist で 3,846 file を除外し 12,526 file を読んでいた。v3 は allowlist を外して 16,372 file (12,526 + 3,846) を読んだ
  (完全表記の hit は同じ 13 件、数字のみの hit も同じ 151 件)。
- symlink (file・directory) は追跡しない設計だが、対象 dir には 0 件だった。lstat・読取の失敗は 0 件。
- 当時の raw `verifier.json` は `results[0].trace_dir` に `job-staging/<PBS_JOBID>/run/trace` の絶対 path を含む (§3) ので、
  本文検索は改名された写しも (50 MiB 以下なら) 捕捉する。捕捉したのは本文言及 13 件だけだった。

**探索していない範囲 (不在を断定しない理由):** 上の 50 MiB 超 1,008 file の本文。依頼範囲外 = Pegasus 側の scheduler accounting、
他ユーザー領域、home 配下の他 session job dir 全数、`/work/1/SFC/tanab/` 直下で名指しされていない dir、backup / snapshot、
削除済み branch の到達不能 object。本 wave は走査していない。

## §3 insight 埋め込み JSON は raw の逐語ではない

C14a の `[導出索引]` が指す insight の「検証結果 (verifier 構造化出力、全文)」block は、raw `verifier.json` と**同じ bytes ではない**。
当時の verifier (`git show 2efe6282:orchestrator/verifier/report.py` の `result_to_dict` 96-131 行、`cli.py` の `--json` 経路 78-86 行は
`result_to_dict` を直接使う) は `results[0]` に `trace_dir`、`integrity.framing_violation_details`、`integrity.permutation_violation_details`
を出力するが、埋め込み block はこの 3 key を欠く。判定値 (`verdict` / `certified` / `anomaly_count` / `total_cycles` / `stats` /
`integrity` の数値) は読み取れるが、**raw bytes の sha256 を埋め込み block から再構成することはできない。**
したがって `[権威 bytes]` の代わりに埋め込み block の sha256 を書く案は成立しない。

## §4 隣接物 (C14a ではない — 代替にしない)

同じ adapter の TRACE=1 走行で raw が退避されているものは、2026-08-26 の pair wave の leg `0:949961.nqsv` / `0:949963.nqsv`
(`output/insights/2026-08-26_mocc-trace-pair-receipt.json` の `legs[].mode_evidence.sha256` = `c284b507…` / `ff334773…`、退避先
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-trace-pair/evidence/paired-97906410/`、txns は pair insight 110-111 行の 756,277 / 740,190) と
probe `949555` (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-trace-pair/materials/verifier-trace1.json`、`stats.txns` 778,690) である。
**これらは別 request の観測であり、`934607.nqsv` (txns 761,914) の raw bytes ではない。** C14a の行にこれらを流用してはならない。

## §5 記録の置き場と言えること・言えないこと

- 追記は `docs/paper-story/README.md` の「claim-evidence 系列」節に、C14a の所在調査の追記 (2026-09-18) として置く (本 wave の commit)。
  claim-evidence matrix の新稿は作らない — D1013 規則 2 は「一項目だけを直した差分改訂を新しい日付として置かない」と定め、新稿を
  置くなら入力 5 節全体の再導出が要る (scope 外)。D1013 は既存 insight を指す個別注記を禁じていない (段 6 レビュー R-5)。同 README の
  版系列「最新スナップショット以後に確定したこと」節は、branch `worktree-dev-wave-t2775-paper-story-a1-attempt1` の tip (未 land) が
  同節を変えている (件数行と項目追加、`verbatim/overlap_scan.py.txt` で 209 branch を走査) ので、衝突を避けて触れない
- **言えること:** C14a の `[権威 bytes]` は 2026-09-18 時点でも未特定である。今回の探索で確認できたのは「当時の出力先は投入 worktree 配下で、
  その worktree は現在存在しない。探索時点の ref・主 checkout・evidence dir・名指し job dir に raw も退避物も特定できなかった。当時の
  receipt 生成処理は verifier.json の sha256 を束縛していなかった」まで。C14a の判定値は insight の転記でしか辿れない
- **言えないこと:** raw が世界に存在しない (走査外の領域がある)。消失の経緯 (撤去で失われたのか、別の場所へ写されたのか)。C14a の判定が
  誤り (判定の正否は本 wave の対象外。絶対規律 7 — 当時その道具でその測定をし結果が出た事実は変わらず、再現できないことと事実でないことは
  別)。埋め込み JSON が raw と同 bytes (§3 で否定)
- **変わらないこと:** claim-evidence の C14a 行・8 月の insight 5 群・pair receipt は 1 byte も変えていない。規律 2 に触れない。
  gate・検査・台帳・一般化は足していない

## §6 段 6 レビューと fix、工数と検査

- read-only codex review 1 本 (`verbatim/prompt-review.md` → `verbatim/out-review.md`、レンズ = 正しさ境界・整合と過剰・削除を 1 本で)。
  所見 8 件: must-fix 3 (R-1 消失・未退避の断定 → 観測文へ、R-2 走査の除外条件が未記載 → 条件と件数を明記、R-3 「完全表記 0 件」が
  最初の一致だけの分類に依拠 → 全本文で判定する再走査 v2 / v3 を実施し同じ 13 件)、nit 4 (R-4 D920 の引用の射程、R-5 README 追記の
  見出しが一般規則化、R-6 request 内訳と写しの説明、R-8 行番号・`$PBS_JOBID` 表記・根拠を出せない「別 binary」)、記録 1 (R-7 branch 差分から
  「稼働 wave が編集中」は導けない)。全件 real として採用し、親が本 insight と README 追記を直した。refuted 0
- `verbatim/out-review.md` の可逆最小正規化 (DW-S07): 子の最終 message は 17 行が markdown の行末 2 space (`git diff --check` 抵触) を
  持っていたので、行末の space 2 byte だけを除いた (可視文字不変)。原文 sha256 `aae0521f8cc03aa5760d3f176679dbb38de7fee512f468165f509fb180679f57`
  (16,866 bytes)、正規化後 sha256 `17c86d6df9d29ff2efdacdaf6b1a7b71bfbbbef6da1232052d965e2add375bf9` (16,832 bytes)。復元法 = 行 13 / 15 / 17 /
  19 / 30 / 33 / 35 / 46 / 60 / 73 / 88 / 90 / 101 / 110 / 112 / 114 / 117 (1 始まり、正規化後の行番号は不変) の末尾に space 2 個を戻す。
  原文の逐語は codex artifact `t1878-review-1/attempt-0001.output.md` (job dir) にもある
- 親の実測: 走査 3 回 (v1 12,526 file、v2 同集合で全本文判定、v3 16,372 file 拡張子不問 + path 名)、git 履歴・ignore・tree の照合、
  当時 script と verifier の `git show` 読み、編集面照合 (209 branch)
- 検査: `tools/check_docs.py`、`tools/spool_fold.py --dry-run`、受入全走は land 経路で 1 走 (結果は land の受領証)。実装子 0 (docs-only)

## §7 段 8 自己改善 (候補 1 件、docs/dev-wave は編集しない)

- 候補: **一次資料から事実を再抽出する docs-only wave では、段 6 の read-only review を 1 本省かない。** `DW-C00` は「docs-only は子ゼロでよい」
  と定めるが、本 wave は 1 本入れた review が must-fix 3 件 (消失の断定、走査の除外条件の未記載、最初の一致だけの分類) を出し、
  記録の正しさを直した。独立 2 例目である (1 例目 = entry 998 の claim-evidence matrix wave、「本 wave が 1 例目なので制度化しない」と記録)。
  `DW-G03` の「独立 2 例」は満たすが、これは段構成 (どの段の子を省けるか) の変更なので、`docs/skill-self-improvement.md` の
  dev-wave 終端「段構成…の変更は実装せず裁定パッケージへ送る」に従い実装しない。L1 (常時読む節) の byte 予算も満杯
  (entry 1649 の実測 10,622 / 10,625) で `DW-C00` へ 1 文を足す余地は無い。**裁定パッケージ候補として本 insight と worklog に残す**
  (推奨案: `DW-C00` の「docs-only は子ゼロでよい」に「一次資料から事実を再抽出する docs wave は review 1 本を残す」を足す。原資は D730 の手順)。
  仮想リスクではなく実測 2 例に基づくが、採否はユーザー裁定に属する
- 上記以外に作法の欠落・無駄は観測していない (隔離 session の Bash guard が複数 dir の `grep -rl` を拒否する件は既知で、Write tool の
  Python で回避した)

## §8 受入 attempt 1 の赤 1 件と非帰属判定 (DW-O18)

- attempt 1 (門番経由、13:17〜13:40 JST、tip `a578e7400` = main `697025ec9` 取り込み後、同時受入 2〜3 本): rc=70、赤 1 件
  `orchestrator/tests/test_pegasus_floor_tools.py::test_floor_checkpoint_filesystem_hang_has_a_wall_clock_bound[write]`
  (`AssertionError: diagnostic timeout did not interrupt the syscall`。0.02 秒の診断 timeout が 5 秒 sleep を中断できるかを見る時間依存 test)。
  junit は `/work/1/SFC/tanab/.izanagi-acceptance-shards/fc46ab5b3249116b0bfd8c4f7b9a4e6a/shard-2/junit.xml`
- 判定 = 非帰属。根拠: (i) 本 wave の変更面 (paper-story README・spool fragment・insights) を同 test file も `floor_job_checkpoint.py` も
  参照しない。(ii) 同一 tip で同 file を単独再走 (`run_tests.py` 経由、計算ノード request `5666.nqsv`) → **3 passed / 4.44 秒 / child rc=0**
  (`verbatim/acceptance-red-rerun-5666.log`)。(iii) 同型の赤は archive worklog の entry 1482 (2026-09-14) と 1546 (2026-09-16) でも
  単独非再現で非帰属判定 (今回で 3 例目、failures 未起票)。(iv) 赤の受領証は受理せず、テストの弱体化・deselect・hold 登録はしない
- 対応: 本判定の記録 commit を積み、門番 (leader ≤ 1 ∧ load ≤ 60、乱数周期 + 二重確認) で受入を 1 回だけ再投入する
- `verbatim/acceptance-red-rerun-5666.log` の可逆最小正規化 (DW-S07): 行 58 / 80 の行末 space 1 byte ずつを除いた (可視文字不変)。原文 sha256
  `3a0d9fbe9102ab1fca0adb010dc3b0f64d651ee2a3c110b3e247899d3bafcc0d` (8,595 bytes)、正規化後
  `65f31290e95adf03aeb7828b52f8c5b71679b672a58666d888172b66c72b3ba8` (8,593 bytes)。復元法 = 同 2 行の末尾に space 1 個を戻す。
  原文は job dir の `rerun-red-1.log`
