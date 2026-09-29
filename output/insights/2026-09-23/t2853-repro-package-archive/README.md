# [T-2853] 再現パッケージの残り (2)(3) — job dir にだけある論文根拠データの写しと sha256 照合、系列ごとの実行手順と R1 の入力一式 (計算なし)

- 作成: 2026-09-23 JST。wave `worktree-t2853-repro-package-rest` (背景 job)、着手時の基準 = local main `3886a1fd3`。
- 依頼の逐語: `verbatim/request.md`。正本の前段: `output/insights/2026-09-22/t2853-repro-package-estimate/README.md` §7・§8・§11 と
  worklog entry 1822 の [T-2853] 項の残り (2)(3)。残り (1) 標準経路の trace 保全口は同時に走る [T-2849] の wave の担当。
- 計算ノードは使っていない。login での読み取り・写し・sha256 だけである。写しと照合に使った script は repo に入れず
  保存先の `/work/1/SFC/tanab/izanagi-repro-archive/t2853-20260923/tools/` に置いた (sha256 は `verbatim/tools-sha256.log`)。

## 0. 結論

1. **job dir にだけあった論文根拠の実験データ 12 組 (計 9,107 file、78,494,904,269 B) を、cleanup の対象外の repo 外 dir
   `/work/1/SFC/tanab/izanagi-repro-archive/t2853-20260923/` へ写し、原本と写しを別々に読んだ sha256・bytes・種別が全件一致した** (§2)。
   locked submit-tree の中にしかなかった campaign 原本 (B-5 試走 53 campaign、K2 pair 初回・再投入・4 巡目) も、submit-tree を動かさずに読んで写した。
2. 写しは正本ではない。元の path・proof chain・locked submit-tree (HEAD・lock) は動かしていない。保存先の README に「写しであって正本ではない、
   official の入力にしない、書き換えない・消さない」と書いた。official の durable authority (`izanagi-measurements/`) とは別の dir にした。
3. 保存 trace を verifier に掛け直す **R1 の入力一式を今回確認できたのは D2160 検証相と B-8 の 2 系列**である。どちらも各走の `result.json` に
   verifier の起動 argv (期待 commit 数・protocol)・repo の commit・CCBench pin・patch の sha256・genome・verifier 9 module の sha256 が残り、
   記録された commit から取り出した 9 module の sha256 が記録値と全件一致した (= その commit で当時の verifier を再構成できる) (§5)。
   ただし CCBench の source は patch を当てただけでは戻らない走があり (B-8 は gate 条件式の書き込みが要る)、D2160 の 4 走は当時の判定が取れていない (§5.1)。
4. B-5 試走・K2 pair・A-1 attempt は標準経路 (検証後に trace を消す) を通っており、今回の調査では原履歴を確認できず、R1 の手順を示せない
   (他の保存経路・複製の不在までは調べていない)。これらの再現は、保存データからの再解析と、保存候補を LLM なしで動かし直す R2
   (新しい履歴の判定であって原判定の再確認ではない) による (§4)。
5. 追跡下の旧形式 trace 4 file は、現行 parser が拒否する。読める最後の parser は `a70a5acd4` (2026-08-12 11:01)、
   拒否へ切り替えたのは直後の `fb5e74a17` (同日 13:05)。当時の verifier の版は report.py 1 file の sha256 しか記録が無い (§5.3)。

## 1. 範囲と言わないこと

- 本題は (2) 写しと照合、(3) 手順書と R1 の入力一式の整理だけである。gate・検査・台帳の追加、写しの自動化、一般化はしていない。
- 手順書は「当時どう走らせたか」と「今どこから再開できるか」を一次資料から引いたもので、本 wave では再実行も再判定もしていない。
  手順どおりに動くことの実証ではない。R1・R2 の実行は、計算の見積りを示して確認を取ってからの別の作業である (D2212 項 4)。
- 論文根拠かどうかは、結果稿・paper-story・各 insight が引いているかで決めた。どれが論文のどの主張に使われるかの確定は論文側の仕事である。
- 写しは repo 外で hooks の保護外にある (`output/README.md` の proof chain の扱い)。守りは README の運用規則と manifest だけである。

## 2. 写しと照合 (2)

### 2.1 保存先

- `/work/1/SFC/tanab/izanagi-repro-archive/` を新設した。dev-wave-jobs の外で、cleanup の母集合 (git worktree と branch、
  `.claude/commands/cleanup-branches.md` の棚卸し) に入らない plain dir である。job dir そのものも cleanup の母集合には入らないが、
  「job dir は cleanup の対象外」という明文は無く、job dir の中の worktree (submit-tree) は候補になりうる (F1034 はこの型)。
- 配置: `t2853-20260923/data/` の下に `/work/1/SFC/tanab/dev-wave-jobs/` からの相対 path のまま置いた。manifest は
  `t2853-20260923/manifests/<組>.json` (path・bytes・sha256・照合結果) と `<組>.sha256` (sha256sum 形式)。
- login の上限 (2026-09-23 07:43 JST 実測): user の cgroup メモリ 16 GiB、CPU 時間・file size・process 数は無制限、/work の空き 81 TiB、
  負荷平均 17 前後 (96 core)。写しは I/O 主体の 1 process を直列に、`nice -n 10`・`ionice -c3` で流した。runbook は大量データの転送に
  rsync を推奨するが、写しと照合を同じ script で行うため Python の `shutil.copy2` を使った。

### 2.2 照合の方法

原本と写しを**別々に**読み、各 entry の種別・bytes・sha256 (symlink なら link 先の文字列) が一致することを確かめた。
写し先に既存 file があれば上書きしない。全組の後に保存先 `data/` 全体を歩き、manifest の和と path 集合が一致すること (余計な file も欠けも無いこと) を確かめた。
`archive_copy.py` は不一致や余計・欠けを記録・表示するだけで異常終了しない。**script の rc=0 は照合成功を意味しない**ので、合否は各 manifest の
`verify.ok`・`verify.mismatch` と全体走査の行 (`extra`・`missing`) で判定した (今回はすべて `ok=True`・空)。同じ script を再利用するときも同じ読み方をする。
symlink・hardlink・`.git` の混入は、写す前の数え上げで全組 0 件だった。

### 2.3 組ごとの結果

2026-09-23 08:25:37〜08:43:24 JST に 1 process で直列に行った (log は `verbatim/copy.log`、事前の数え上げは `verbatim/dryrun.log`)。
「写し」「照合」は秒。照合は原本と写しの両方を読んだ時間である。

| 組 | 系列 | 元 (dev-wave-jobs/ 相対) | file | bytes | 照合 | 写し / 照合 |
|---|---|---|---:|---:|---|---:|
| d2160-verify-phase | D2160 検証相 | `dev-wave-verify-phase-adopted-backoff/` (`thirdparty-src/` を除く) | 3,991 | 48,939,853,127 | 一致 | 550.6 / 66.8 |
| b8-effective | B-8 | `dev-wave-t2807-b8-effective/` | 2,003 | 29,497,936,741 | 一致 | 242.8 / 36.4 |
| b8-prerun-runner | B-8 (runner v3〜v5) | `dev-wave-t2807-b8-prerun/` | 364 | 5,677,309 | 一致 | 23.2 / 0.6 |
| b5-pilot-jobdir | B-5 試走 | `dev-wave-t2797-b5-contrast/` (`submit-tree/`・`mutation-source/` を除く) | 1,683 | 27,358,224 | 一致 | 85.1 / 2.4 |
| b5-pilot-originals | B-5 試走 (campaign 原本) | `dev-wave-t2797-b5-contrast/submit-tree/output/` の campaign 53・claim 53・`namespace.json` | 274 | 1,161,686 | 一致 | 17.4 / 0.4 |
| k2-resubmit-jobdir | K2 再投入・4 巡目 | `dev-wave-t2795-k2-pair-resubmit/` (submit-tree 2 本を除く、`originals-copy-20260922/` を含む) | 163 | 1,538,269 | 一致 | 4.2 / 0.2 |
| k2-resubmit-pair2-originals | K2 再投入 (campaign 原本) | `…/submit-tree-pair2/output/` の campaign・claim・`namespace.json` | 8 | 31,597 | 一致 | 0.4 / 0.0 |
| k2-resubmit-r4-originals | K2 4 巡目 (campaign 原本) | `…/submit-tree-r4/output/` の同上 | 8 | 31,584 | 一致 | 0.4 / 0.0 |
| k2-pair-first-jobdir | K2 pair 初回 (不成立) | `dev-wave-t2795-k2-pair/` (`submit-tree-pair/` を除く) | 130 | 2,322,714 | 一致 | 6.9 / 0.4 |
| k2-pair-first-originals | K2 pair 初回 (campaign 原本) | `…/submit-tree-pair/output/` の同上 | 7 | 19,231 | 一致 | 0.6 / 0.0 |
| a1-durable-authority | A-1 attempt-0001・0002 | `dev-wave-paper-story-a1-balanced5-sized-20260913/` (中身は `measurement/` だけ) | 353 | 18,774,872 | 一致 | 17.1 / 1.3 |
| a1-attempt2-jobdir | A-1 attempt-0002 の wave 記録 | `dev-wave-t2792-a1-sized-attempt2/` (`submit-tree/`・`third-party-hydrated/` を除く) | 123 | 198,915 | 一致 | 4.7 / 0.3 |
| **計** | | | **9,107** | **78,494,904,269** | 不一致 0 | |

- 全組の後の保存先全体の走査: 9,107 path で manifest の和と一致 (余計 0、欠け 0)。
- 別実装での再確認: 写しの直後の照合とは別の実装 `sha256sum -c` で、写し側だけを全 manifest に対して読み直した。08:43:43〜08:51:45 JST、
  12 組 9,107 行すべて rc=0 (`verbatim/recheck.log`)。これは manifest との一致を別実装で確かめたもので、同じ filesystem の cache を読んだ可能性まで排除する証拠ではない。
- 各組の manifest (`manifests/<組>.json`・`<組>.sha256`) の sha256 は `verbatim/manifest-sha256.log`。

### 2.4 写さなかったものと理由

| 対象 | 理由 |
|---|---|
| job dir 内の `submit-tree*` 本体 (locked worktree 5 本) | repo の写し。中の未追跡の原本 (campaign・claim・`namespace.json`) だけを写した。未追跡の判定は submit-tree の HEAD の `git ls-tree` と実 file の差で取った |
| submit-tree 内の `output/campaign-locks/*.flock` | 56 個すべて 0 B の lock file (実測) |
| submit-tree 内の `output/env/pegasus/silo_ladder_rung1/` 配下の未追跡 971 file (各 tree) | `.gitignore` 対象。job-staging 全体 (追跡済みの旧 raw・trace を含む) は 5 本とも 1,389 file・169,493,326 B で、pair2 と r4 の差は依存 clone の `.git/index` と reflog の 12 file だけ (時刻の差、実測)。未追跡分は tree ごとに展開した依存物のソースであって実験原本ではない。追跡済みの分は repo にある |
| A-1 の submit-tree の未追跡 `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/` の 4 file | 4 file とも現行 repo の追跡下の同じ path の file と sha256 が一致した (実測、段 6 レビュー S2 の裏取り)。原本は repo にあり保全漏れではない |
| `mutation-source/`・`thirdparty-src/`・`third-party-hydrated/` | 独立 clone (変異検査用の repo 写し、CCBench の依存物のソース) |
| `dev-wave-t2795-k2-pair-repair` | driver 修復の実装 wave で、実機の pair 投入をしていない (`output/insights/2026-09-21/t2795-pair-repair/README.md` §0)。実験データが無い |
| `dev-wave-a1-sized-attempt2` (2026-09-19) | 投入前に拒否されて測定値が無い (`output/insights/2026-09-19/a1-sized-attempt2/README.md`) |
| A-1 の pilot / sizing 段 (`dev-wave-a1-pilot-*`・`dev-wave-a1-sizing-certificate`・`dev-wave-a1-fanout`) | 現行の結果稿がこれらの job dir を引いていることを確認できなかった。論文根拠と言えないので本 wave では写していない (後で必要なら同じ script で足せる) |
| B-5 試走の trace | 今回の調査では確認できなかった (標準経路は検証後に削除する、前段 insight §4.1・§4.3。他の保存経路・複製の不在までは調べていない) |

### 2.5 K2 原本の二重照合

K2 再投入の原本 14 file は、前日の wave が作った写し `dev-wave-t2795-k2-pair-resubmit/originals-copy-20260922/MANIFEST.sha256` と、
今回 submit-tree (pair2・r4) から写した manifest が全件一致した。r4 の原本は 2026-09-22 の写し以後変わっていない
(同時に走る [T-2860] の wave は同じ原本を読むだけで、本 wave も読むだけにした)。`namespace.json` は前日の写しに無く、今回が初めての写しである。

## 3. 保存先の運用

- 写しは正本ではない。元の path が残っている間は元の path を参照する。元の path が失われたときに限り、manifest の sha256 で
  「原本と同一だった」ことを示す控えとして使う。写しを official の入力 (certified 経路・durable authority) に使わない。
- 書き換えない・消さない。追加の写しは新しい日付の dir に置く。新しく論文根拠になった job dir は、実験と並行で同じ手順で写す (前段 insight §11 の推奨)。

## 4. 系列ごとの実行手順 (3)

各系列について、当時の走らせ方 (一次資料から)、写しの位置、成り立つ再実行の経路 (前段 insight §8.1 の R1 再判定 / R2 再実行 / G 再生成) を示す。
計算の見積りは前段 insight §9 の単価で出し、2 node 時間以上なら確認を取る (D2212 項 4、D2219 項 1)。

共通の前提:

- R2 の入口は `pipeline.evaluate` (LLM を呼ばない) で、保存済みの提案 JSON は `orchestrator/campaign/p3_s4_loop.py --run-iteration PROPOSAL.json` に渡す
  (前段 insight §8.3)。R2 は新しい有限履歴の判定であり、anomaly が出れば即 reject して理由を構造化して返す (規律 2・3)。
- 当時の checkout は記録された repo の commit を `git worktree add --detach <新しい dir> <commit>` で取り出し、CCBench は記録された pin を checkout する。
  現行 checkout に一律に限定もしないし、当時の checkout との同一性を新しい測定の条件にもしない (規律 7、前段 insight §8.2)。
- 旧書式 (exact-63) の campaign.lock は現行の厳密 decoder では読めず、歴史閲覧 (`HISTORICAL_RAW`) か JSON の直読で読む。

### 4.1 D2160 検証相 (採用候補 fixed-5 / fixed-10 の追加検証)

| 項目 | 内容 |
|---|---|
| 論文での役割 | A-2 / A-6 の 5 限定に対する正しさ側の追加事実。B-8 の要件は満たさない (`docs/paper-story/2026-09-22.md` の該当節) |
| 一次資料 | `output/insights/2026-09-20/verify-phase-adopted-backoff/README.md` (§4 条件・§5 結果)、裁定 `rulings-inbox/2026-09-19-verify-phase-adopted-backoff-authorization.md` |
| 当時の構成 | repo `657e1e5a7`、CCBench pin `511c9538`、build `-DCCBENCH_TRACE=1 -DCCBENCH_BACK_OFF=1 -DCCBENCH_BACKOFF_FIXED=<5\|10> -DCCBENCH_BACKOFF_NOINLINE=0 -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1 -DCCBENCH_NO_WAIT_OF_TICTOC=0 -DCCBENCH_WAL=0`、Silo・YCSB 3 workload・1,000,000 records・48 thread・skew 0.9・extime 3 s (校正は 3/6/10 s) |
| 当時の投入 | repo 外 runner `probe/verify_phase_runner.v1-run.py` (走行)、集計は `probe/verify_phase_runner.py` (v2) の `summarize`。校正 `10868〜10873.nqsv`、本走 `11268〜11279.nqsv` (gen_S、2026-09-19 22:46〜09-20 00:43 JST) |
| 写し | `data/dev-wave-verify-phase-adopted-backoff/` (run/ の保全 trace 3,072 file と各走の記録、probe/ の runner) |
| 再現の経路 | **R1 の入力一式あり** (§5)。ただし 10 s 校正 4 走は当時の判定が無く追加評価になる。R2 は LLM を使わない固定 genome なので、同じ runner と構成で新しい履歴を取り直せる (原判定の再確認ではない)。G は該当しない |
| 費用 (記録) | 校正 + 本走 25,251 s = 7.01 node 時間 (前段 insight §9)。R1 だけなら 3 s trace 1 本 84〜433 s (改修後 verifier) × 走数 |

### 4.2 B-8 (S-1 最終候補の長時間実行による検証)

| 項目 | 内容 |
|---|---|
| 論文での役割 | B-8「種を変えた長時間実行による最終候補の検証」そのもの、判定 `pass` (D2194 項 1、D2202) |
| 一次資料 | `output/insights/2026-09-21/t2807-b8-effective/README.md`、前段 `output/insights/2026-09-21/t2807-b8-prerun/README.md`、事前登録 `docs/b8-final-candidate-longrun-verify-preregistration.md` |
| 当時の構成 | 発効 commit `624c84986`、CCBench pin `e9e477ca`、genome `silo\|BACKOFF_TRIGGER_GATING=1,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` (記録 `result.json` の `bindings.genome`、3 workload で同じ。系側の gate 構成 g_rl / g_rt は `bindings.gate`)、extime 10 s、各 workload 2 job × 4 反復 |
| 当時の投入 | job dir `dev-wave-t2807-b8-effective/launch-calib*.sh`・`launch-verify*.sh` (workload・job ごと) が runner v5 (`dev-wave-t2807-b8-prerun/probe/verify_phase_runner.py`、sha256 `4ff6652a…`) と事前登録・発効束の sha256 を `identity.txt` に書いて照合し、`dispatch_compute.py --task generic --walltime 03:30:00 ... -- python3.10 -B <runner v5> calibrate\|verify --workload <w> --repo-root <submit-tree> --scratch-root /scr --output-dir ... --ruling ... --bundle ...` で投入。校正 `14640〜14642`、本走 `14686〜14691` |
| 写し | `data/dev-wave-t2807-b8-effective/` (run/ の保全 trace 1,440 file と記録、launcher)、`data/dev-wave-t2807-b8-prerun/` (runner v3〜v5) |
| 再現の経路 | **R1 の入力一式あり** (§5)。source の再構成には gate 条件式の書き込みが要る (§5.1)。runner v5 の `reverify` は本走の未完了走だけを受け付ける運用上のやり直しで、汎用の R1 入口ではない (B-8 本走では発生 0 件)。R2 は固定 genome の再実行。G は該当しない |
| 費用 (記録) | 3.11 node 時間。R1 だけなら 10 s trace 1 本 219〜496 s (workload 別平均) × 走数 |

### 4.3 B-5 試走 (LLM・random・sweep・block stock の生成器対照の試走)

| 項目 | 内容 |
|---|---|
| 論文での役割 | B-5 (LLM の因果的必要性の対照) の試走。n = 1、`purpose="pilot"`、主標本には入れない (`output/insights/2026-09-20/t2797-b5-contrast/README.md` §6)。既知結果台帳の参考値 |
| 一次資料 | 同 insight §6.1 (条件)・§6.3 (所要)・§8、事前登録 `docs/b5-generator-contrast-preregistration.md` |
| 当時の構成 | submit-tree = 統合 commit `11d46a74a`、CCBench pin `511c9538`、write-heavy・1,000,000 records・48 thread・extime 3 s・5 反復、verify は legacy 1 回 + trace 5 回 |
| 当時の投入 | job dir の `submit_pilot.py` (launcher API を import) で 4 job (random `13636` / sweep `13637` / llm `13638` / block-stock `13639`、gen_S) |
| 写し | `data/dev-wave-t2797-b5-contrast/` (台帳 `ledgers/`、入力素材 `materials/`、LLM 入出力、`pilot/` の報告と所要、codex の段記録)、submit-tree 内の campaign 原本 53 と claim 53 (`data/dev-wave-t2797-b5-contrast/submit-tree/output/...`) |
| 再現の経路 | R1 の手順を示せない (標準経路は検証後に trace を消し、今回の調査では原履歴を確認できなかった。他の保存経路・複製の不在までは調べていない)。**R2 可**: random・sweep は凍結した生成規則、LLM arm は各巡の提案 JSON (`materials/`・台帳 `proposals`) から LLM なしで評価し直せる。**G 可**: prompt・知識 manifest・leakproof context・model 設定が逐語で残る。campaign.lock は旧書式 (exact-63) |
| 費用 (記録) | job Elapse 17.0 node 時間 (lock 待ちと LLM 待ちを含む)、固有費 22,230 s。R2 で 53 session を測り直すと固有費だけで 3.19〜7.49 h (前段 insight §9) で確認対象 |

### 4.4 K2 pair 再投入と 4 巡目

| 項目 | 内容 |
|---|---|
| 論文での役割 | B-6 (リーク制御を完備した実走) の同 job stock 対照。`docs/paper-story/README.md` の stale 注記が次版で取り込む根拠として指名 |
| 一次資料 | `output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md` §1 (pair)・§2 (4 巡目)・§9 (原本の所在) |
| 当時の構成 | submit-tree `8fd2a2f5c` (pair2・r4 とも)、CCBench は `p3_s4_loop.PIN` = `511c9538` へ checkout (gitlink は `e9e477ca` のまま)、4 thread・100,000 records・rr50・skew 0.9・extime 1・2 反復 |
| 当時の投入 | pair: env `IZANAGI_S4_STOCK_CONTROL=1`、round 3 の `materials/proposal-4.json` (value 10)、K2 manifest wal-only、`CODER_ROLE=coder-v4-autonomous-k2`、job `16269.nqsv`。4 巡目: 入力を job dir の `build_round4_inputs.py` で組み、job `16312.nqsv` |
| 写し | `data/dev-wave-t2795-k2-pair-resubmit/` (`materials/`・`verbatim/`・`originals-copy-20260922/`・集計 script)、submit-tree 2 本の campaign 原本と claim。初回 pair (不成立) の `data/dev-wave-t2795-k2-pair/` と campaign 原本も写した |
| 再現の経路 | R1 の手順を示せない (標準経路で trace は残らないと判断した。本系列の trace の不在を名指しで確かめた記録は無く、同じ経路であることからの判断)。**R2 可**: 候補 10・候補 5・stock の genome と提案 JSON が残る。**G 可**: critic 診断・knowledge input・whiteboard・leakproof context が bytes と sha256 で残る |
| 費用 (記録) | 2 job 207 s (≈ 0.06 node 時間)、LLM の role 呼び出し 2 回 |

### 4.5 A-1 sized attempt-0002 (同一配置の反復観察)

| 項目 | 内容 |
|---|---|
| 論文での役割 | A-1 (headline estimand と一致する対測定) の非認証観察 2 本のうち 2 本目 (`formal=false`)。3 本目は今は走らせない (D2211 項 10、D2212 項 5) |
| 一次資料 | 結果稿 `docs/paper-story/results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md` (§1 条件、§5.2 durable authority)、`output/insights/2026-09-20/t2792-a1-sized-attempt2/README.md` |
| 当時の構成 | submit-tree = `fec4a8187`、CCBench pin `511c9538`、Silo・1,000,000 records・48 thread・skew 0.9・extime 3 s、arm は write-heavy `fixed10` / balanced `fixed5` / read-heavy `fixed2` 対 `no-backoff` (BACK_OFF=0) |
| 当時の投入 | `python3 -B -m orchestrator.campaign.paper_story_a1_paired authorize-rerun --study-id paper-story-a1-20260901-balanced5-sized-v1 --attempt-root <durable base>/measurement/attempt-0002 --expected-head fec4a818741e5464fffcd11e4b094c125dfe5280 --decision D2172 --decision-item 2 --decided-on 2026-09-20` → `submit` → `complete` → `materialize`。job `13220`〜`13222` |
| 写し | `data/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/` (attempt-0001・0002 の durable authority、結果稿 §5.2 が sha256 を列挙する一次資料)、`data/dev-wave-t2792-a1-sized-attempt2/` (brief・裁定・抽出・検算 script) |
| 再現の経路 | R1 の手順を示せない (測定は標準経路の `loop.run_campaign` を再利用する (`orchestrator/campaign/paper_story_a1_paired.py` 冒頭) ので trace は残らないと判断した。本系列の trace の不在を名指しで確かめた記録は無い)。R2 は事前登録が固定した genome の再実行そのものだが、新しい attempt の投入には改めて認可が要る。G は該当しない。保存データからの再解析 (結果稿の数値・図) は写しからも行える |
| 費用 (記録) | 3 job の elapsed 合計 2,218.79 s ≈ 0.62 node 時間 |

## 5. R1 (再判定) の入力一式

前段 insight §8.1 の R1 の入力 (保存 trace、当時の判定に使った関連入力 = 期待 commit 数・protocol・CCBench の source context、当時の verifier の版) が、
系列ごとにどこにあるかを示す。値は 1 走ずつ実測した (D2160 `run/verify/fixed-10-balanced-1/rep-1/attempt-1`、B-8 `run/verify/write-heavy-j1/rep-1/attempt-1`)。

### 5.1 D2160 と B-8 (1 走 = 1 dir)

| 入力 | 所在 (各走の dir) | 実測 (D2160 / B-8 の上の 1 走) |
|---|---|---|
| 保存 trace | `trace/trace_<N>.log.zst` × 48 | 48 / 48 file |
| 復元の照合 | `preservation.json` の `files[]` = `name`・`sha256`・`bytes`・`lines`・`stored_name`・`stored_sha256`・`stored_bytes` ほか | runner の `restore` は圧縮 file の sha256 と bytes を照合 → `zstd -d` → 復元 file の sha256 と bytes を照合 (2 段) |
| 期待 commit 数・protocol | `result.json` の `verify.argv` | `--expected-commits 4332864 --protocol silo` / `--expected-commits 8342453 --protocol silo` |
| CCBench の source context | `result.json` の `bindings.ccbench_pin`・`patch_sha256`・`genome`・`configure_defines`・`source_before`/`source_after` (B-8 は加えて `template_patch_sha256`・`gate_predicate`) | pin `511c9538…` / `e9e477ca…`。patch の実体は記録 commit 内の `patches/silo-backoff-fixed.patch` (`a5e0710c…`) / `patches/silo-backoff-trigger-gating-variant.patch` (`31316713…`、template)。sha256 が記録値と一致することを確かめた (段 6 レビュー M1 の裏取り)。B-8 の runner v5 は template を当てた後に `gate_predicate` を `quarantine(..., write=True)` で source へ書き込む (runner 634〜642 行付近) ので、patch だけでは当時の source にならない。当時の source は `source_before`/`source_after` の `src_token`・`tracked_diff_sha256` で照合できる |
| verifier の版 | `result.json` の `bindings.repo_head` と `bindings.verifier_module_sha256` (9 module) | `657e1e5a7` / `624c84986`。**記録された commit から取り出した `orchestrator/verifier/*.py` 9 file の sha256 が記録値と全件一致した** (§7 の script) |
| 当時の判定 | `verifier.json` (`certified_serializable`・`non_serializable`・`indeterminate`・`results`・`runs`) | 集計は系列の `run/summary-*.json`。**D2160 の 10 s 校正 4 走 (`run/calib/fixed-{5,10}-{write-heavy,balanced}/extime-10/`) は `verifier.json` が 0 B** (旧 verifier が timeout / kill で完走しなかった、前段 insight §4.2、実測) で、比べる旧判定が無い |

- 版の関係: D2160 の `657e1e5a7` は verifier 改修 D2181 (`11f0f1972`、2026-09-20 14:28) より前、B-8 の `624c84986` は改修後で、
  9 module のうち `dsg.py` と `parse.py` の sha256 が違う (実測、`git merge-base --is-ancestor` でも確認)。
- **argv はそのままは再生できない。** `verify.argv` の trace dir と `--ccbench-root` は計算ノードの一時領域 (`/scr/verify-phase-*/...`) の path で、
  job 終了後は残っていない。R1 では trace を復元した dir と、記録の pin・patch・genome から作り直した CCBench checkout に読み替える。
- 入口: 現行 repo の `python -m orchestrator.verifier TRACE_DIR --json --expected-commits N --protocol NAME --ccbench-root PATH`
  (`orchestrator/verifier/cli.py`) が同じ形の CLI である。当時の版で掛けるなら記録された commit を detached worktree で取り出して同じ CLI を使う。
- 新しい版で掛けた結果は「保存履歴に対する新しい版での再評価」として別に記録し、旧判定は保持する。新しい版が通ったことを理由に遡って certified へ昇格させない (規律 7)。
  先例は `output/insights/2026-09-20/verifier-capacity/README.md` §4 (旧版 `947fd160a` と改修版を同じ trace に掛けて 14 本一致、repo 外 probe)。
- 対象の分け方: 保全 94 走 (D2160 64・B-8 30) のうち、当時の判定が取れている 90 走は「旧判定との比較」、D2160 の 10 s 校正 4 走は
  「当時は完走しなかった履歴の追加評価」として分けて記録する (4 走の `result.json` の timeout / kill の記録は保持する)。
- 所要: 前段 insight §9 の単価 (10 s trace 1 本 219〜496 s、3 s trace 1 本 84〜433 s) は**改修後 verifier** の値である。当時の版 (D2160 の `657e1e5a7`) で
  10 s の trace を掛けると、D2160 の校正では balanced が SIGKILL (wall 約 300 s、主 process maxrss 約 21 GiB)、write-heavy が hard timeout (3,600 s) で
完走しなかった (`output/insights/2026-09-20/verify-phase-adopted-backoff/README.md` §5.3)。
  当時の版での 10 s 走の所要と資源は未知なので、当時の版で掛けるのは 3 s の走に限るか、別に見積もる。全部を掛け直すなら見積りを出して 2 node 時間の線で確認を取る。

### 5.2 D2160 と B-8 の R1 の手順 (実行していない)

1. 写しまたは元の run dir から 1 走の dir を選ぶ。`preservation.json` の `stored_sha256` で `trace/*.zst` を照合し、`zstd -d` で復元、`sha256` で照合する
   (runner の `restore` と同じ処理)。B-8 の runner v5 の `reverify` は汎用の R1 入口ではない — 本走で verifier が運用上未完了 (`indeterminate`) だった走だけを受け付け、
   完走済みの走と校正の走は拒否する (runner の `reserve_output`、829 行付近)。
2. `result.json` の `bindings.repo_head` を `git worktree add --detach <新しい dir> <commit>` で取り出し、`orchestrator/verifier/*.py` の sha256 を
   `bindings.verifier_module_sha256` と照合する。
3. `bindings.ccbench_pin` の CCBench に、手順 2 の checkout 内の patch (§5.1 の表の path、sha256 が記録値と一致するもの) を当てる。B-8 は続けて
   `bindings.gate_predicate` を runner v5 と同じ方法で書き込む。できた source を `source_before` の `src_token`・`tracked_diff_sha256` と照合してから `--ccbench-root` に使う。
4. 計算ノードで `python3.10 -B -m orchestrator.verifier <復元 dir> --json --expected-commits <argv の値> --protocol silo --ccbench-root <3 の checkout>` を実行し、
   当時の判定がある走は `verifier.json` と比べ、D2160 の 10 s 校正 4 走は追加評価として別に記録する。資源: 改修後 verifier は balanced 10 s で node peak 32.4 GiB
   (`verifier-capacity/README.md` §4)。当時の版の 10 s 走は完走した記録が無い (上の所要の項)。

### 5.3 追跡下の旧形式 trace 4 file (2026-07-29 劣化梯子 rung 1)

- trace: `output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/correctness/traces/trace_{0..3}.log` (非圧縮、追跡下)。
  preservation.json に当たる manifest は無い。
- 関連入力: `raw-manifest.json` などの `bindings` に `ccbench_pin_full` = `d706650c…`・`patch_sha256`・`policy_sha256`・`third_party_heads` がある。
  **期待 commit 数と protocol は記録に見当たらない** (調査子の報告、`correctness/verifier.json` と `run.command.json` に無い)。
- verifier の版: `verifier_module_sha256` は `orchestrator/verifier/report.py` 1 file の sha256 (`e604cef0…`) だけで、`afa732573` (2026-07-29 11:46) の
  report.py と一致した (実測)。他の module の版は記録から特定できない。
- parser: 5 項目の C 行 (v1) を読める最後の commit は `a70a5acd4` (2026-08-12 11:01)、直後の `fb5e74a17` (同日 13:05、「trace を v2 専用にし ccbench pin を 511c953 へ前進」)
  が v1 を拒否した (実測)。R1 には `a70a5acd4` 以前の checkout の verifier が要る。report.py 以外の module が当時と同じだったかは確かめられない。

### 5.4 R1 の入力を確認できなかった系列

B-5 試走・K2 pair・A-1 attempt・S-1a などの標準経路の系列は、今回の調査では原履歴 (trace) を確認できず、現時点で R1 の手順を示せない
(標準経路の削除処理からの判断で、他の保存経路・複製の不在までは調べていない、前段 insight §4.3)。今後の実験で R1 を成り立たせるには
[T-2849] の wave が担う保全口 (残り (1)) で、D2160・B-8 の runner と同じ組 (trace・`preservation.json`・verifier の argv・repo commit・pin・patch・
verifier module の sha256) を残すことになる。本 wave は保全口の設計に立ち入らない。

## 6. 段 6 レビュー

軽量版の dev-wave として段 2・3 は省いた (実装面の差分ゼロ、設計の択一なし)。一次資料から事実を再抽出した docs なので、段 6 の read-only レビューを 1 本残した。
review (Codex、read-only、08:52〜08:57 JST、rc=0、`tools/check_codex_output.py` 受理 rc=0、逐語 `verbatim/s6-review.md`) は NO-GO (must-fix 3・should 3・nit 1)。
親が各所見を現物で裏取りし (`verbatim/review-checks.log`、runner の該当行の読解)、7 件すべて real・scope 内と裁定して本文を直した。

| ID | 所見 | 判定 | 処置 |
|---|---|---|---|
| M1 | B-8 は template patch の後に gate 条件式を source へ書き込むので、patch を当てるだけでは当時の source にならない | real | §5.1 の表に patch の path・sha256 の一致と gate 条件式の書き込みを追記、§5.2 手順 3 に書き込みと `source_before` での照合を追加 |
| M2 | D2160 の 10 s 校正 4 走は `verifier.json` が 0 B で旧判定が無い。32.4 GiB は改修版の値。`reverify` は汎用入口でない | real | §5.1 に 90 走 / 4 走の分け方、当時の版の 10 s 走が完走しなかった記録、§5.2 手順 1・4 と §4.1・§4.2 を修正 |
| M3 | trace の不在を調査範囲を超えて断定 | real | §0 項 3・4、§2.4、§4.3〜§4.5、§5.4 を「今回確認できた / できなかった」に揃えた |
| S1 | 別の道具での再読は cache の排除の証拠ではない | real | §2.3 を「別実装で manifest との一致を再確認」に弱めた |
| S2 | A-1 の submit-tree の未追跡 4 file の扱いと、job-staging の未追跡分と全体の区別 | real | 4 file が追跡下と同一であることを実測して §2.4 に行を追加、job-staging の行を未追跡分に限定 |
| S3 | copy script の rc=0 は照合成功を意味しない | real | §2.2 に合否の読み方を追記 |
| N1 | `git worktree add --detach` の引数不足 | real | §4 共通前提と §5.2 を `<新しい dir> <commit>` に直した |

焦点再レビュー 1 巡目 (Codex、read-only、09:00 JST 起動、rc=0、受理 rc=0、逐語 `verbatim/s6-focus-1.md`) は **GO** — 7 所見すべて closed、新規所見なし
(must-fix・should・nit とも 0)。再レビュー子は現物で、D2160 の判定取得 60 / 64 走と B-8 の 30 / 30 走 (合わせて 90 走、残る 4 走は 0 B)、
balanced 10 s の SIGKILL と write-heavy 10 s の timeout、patch と verifier の hash、A-1 の 4 file の同一性を確かめた。

## 7. 出所

- `verbatim/request.md` — 依頼の逐語。`verbatim/startup-gate.log` — 開始 gate (rc=0)。
- `verbatim/dryrun.log`・`verbatim/copy.log`・`verbatim/recheck.log` — 写す前の数え上げ、写しと照合、写し側の独立再検算。
- `verbatim/manifest-sha256.log`・`verbatim/tools-sha256.log` — 保存先の manifest 24 file と script・計画の sha256。
- `verbatim/submit-tree-untracked.log` — submit-tree 5 本の未追跡 output の一覧 (HEAD の `git ls-tree` と実 file の差)。
- `verbatim/check-excluded.log`・`verbatim/job-staging-diff.log` — 対象外にした flock と依存物展開の実測。
- `verbatim/k2-crosscheck.log` — K2 原本の二重照合。
- `verbatim/r1-facts.log`・`verbatim/verifier-blob-check.log` — R1 の入力の実測と、記録 commit の verifier sha256 の照合。
- `verbatim/s6-review.md`・`verbatim/s6-focus-1.md` — 段 6 レビューと焦点再レビューの逐語。`git diff --check` に抵触する行末の半角空白 2 個
  (Markdown の改行指定) だけを除く可逆の正規化をした (可視文字は不変)。原文: `s6-review.md` sha256 `a9b2fc98f48301c3d389b47f3aaa77036e44419f6c23095793f2bd6c3b4ff97c`
  (codex receipt の `output_sha256` と一致)・5,578 B、対象 8・9・12・13・16・17・22・25・28・33 行。`s6-focus-1.md` sha256
  `d880d34300263b925b051d275e07fcc8c7a6b1e37fdbf2536e24d545d2e33188`・2,094 B、対象 3 行。復元法: 対象行の行末に半角空白 2 個を足す。`verbatim/review-checks.log` — 所見の裏取り (patch の sha256、A-1 の 4 file、0 B の verifier.json)。
- 保存先の script (repo 外、`tools/`): `make_plan.py` (計画)、`dryrun.py` (数え上げ)、`archive_copy.py` (写しと照合)、`run_copy.sh` (起動)、
  `recheck.sh` (再検算)、`review_checks.sh` (段 6 所見の裏取り)、`inventory.py`・`untracked.py`・`check_excluded.py`・`diff_staging.py`・`k2_crosscheck.py`・`r1_facts.py`・`verifier_blob_check.sh` (読み取りの実測)。
- 調査子 (Claude Explore、sonnet) 4 本 (cleanup の範囲と保存先の慣行、5 系列の所在と量、系列ごとの手順の一次資料、R1 の入力) の報告は会話内のみ。
  本文に使った値は親が一次資料・実測で照合した。調査子の報告にあった `a70a5acd4` の日時 (2026-07-29 とあった) は誤りで、実測は 2026-08-12 11:01 である。

## 所在の移動・撤去 (2026-09-30 追記)

本 insight が写しの元として記録した locked submit-tree (K2 pair・pair2・r4、B-5 試走、A-1 attempt2 ほか) は、2026-09-30 の掃除 wave で回収せずに撤去する。以後、これらの campaign 原本の控えは `/work/1/SFC/tanab/izanagi-repro-archive/t2853-20260923/` の写しと、各 job dir に残る複製 (K2 の `originals-copy-*` 等) になる。写しを official の入力へ昇格させるものではない。
判定の根拠・木ごとの退避の所在・残る写しの一覧は `output/insights/2026-09-30/cleanup-originals-migration/README.md` を正本とする。上の本文は当時の事実として書き換えない (記録された測定・判定は撤去を理由に無効にならない、規律 7)。撤去は同 wave の land の後に行う。
