# stock mocc の G2 観測条件の分離 ([T-2779]) の単独 results 稿 — 1 試行の一次資料全体 (job dir の 4 block・360 走・G2 7 走の生 trace・事前登録) から書き、README の results 表へ 1 行足した (docs のみ、台帳 ID 未起票)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)

- wave: `worktree-dev-wave-mocc-g2-observation-results` (背景 job ca6c2863、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-g2-observation-results/`)
- 起点 local main: `b7f970dfa507558f7fb669a5ab38958d6c76b57c` (着手直前の local main、fresh worktree)。**実装面 (repo 内) の差分 0**
  (results 稿 1 本・paper-story README 表 1 行・本 insight・worklog fragment のみ)。変異 matrix は `DW-S04` により免除、受入全走は免除しない
- **新規の測定は 0 件。** 凍結物 ([T-2779] insight・job dir・段 4 裁定) の bytes は 1 byte も変えていない
- ユーザー依頼の確定事項: 限定を最初に置く (非 certifying・TRACE=1 観測専用・pin 前進なし D2159・頻度差から backoff の抑制効果や正しさを結論しない・
  G2 signal の再現を根因確定としない = D2148 項 13 / [T-2791] の限定)、[T-2611] / [T-2674] の型 (1 試行の一次資料全体から、横断稿・版を出所にしない)、
  README の results 表へ 1 行 (README は owned-path に入れない)、段 6 は独立 read-only レビュー 1 本 (D2148 項 11)、規律 2 を緩めない、本題の稿だけ

---

## 1. 一行で

`docs/paper-story/results/2026-09-20-mocc-g2-observation-conditions.md` (results 系列の凍結物、限定 18 件 = §0.1 の 10 + §5 の 8、
成果物に無い / 束縛の範囲 / 未照合の 13 項目を §4 に区別、図は無い) を書き、`docs/paper-story/README.md` の results 表へ 1 行足した。
数値・識別子・時刻の出所は job dir の原本 (4 block の `result.json`、360 走の run / verifier JSON、G2 7 走の `trace-manifest.json` と生 trace、
`s4-ruling.md`、dispatch log の NQSV 要約) と insight の `summary.json` だけで、版・横断稿を出所にしていない。

---

## 2. 段 1 の一次資料の実測 (親、2026-09-20 07:0x〜07:2x JST、login node、読み取りだけ)

| 項目 | 実測 | 稿での扱い |
|---|---|---|
| 4 block の `result.json` | `status=completed`、`not_started=0`、`rounds=30`、`runs` 90 件ずつ、run dir 90 個ずつ、ordinal 1〜90 重複なし。sha256 は `summary.json.inputs` と一致 | §1.5、§3.1、§6.2 |
| arm 別 k / m (独立再集計) | 通常 5/120、診断 0/120、backoff 2/120 (`runs[].verifier.status` の `g2` を数えた)。全 360 走 bench rc=0・timeout=false | §3.1、§3.5 |
| verifier の出力 | 353 走 `no-g2` / `serializable` / certified true / rc 0、7 走 `g2` / `non-serializable` / certified false / rc 1。`integrity.clean` 360/360、timeout 0 | §3.5 |
| discriminator | 360 走 `not-run` (reason `witness-off`) | §0.1 項 7、§3.5 |
| G2 7 走の anomaly | 全件 `phenomenon=G2`・`length=2`・両辺 `rw`・`total_cycles=1`・`anomaly_count=1`。txid・key・`[epoch, tid]` を表に書写 | §3.4 |
| G2 7 走の生 trace | 各 48 file、計 336 file、1,981,789,619 byte。`trace-manifest.json` の name / size_bytes / sha256 と **336/336 一致** (親が再 hash) | §3.4、§4 項 17 |
| 非 G2 353 走 | run dir に `trace/` 無し (find で trace dir は 7 個だけ) → 「成果物に無い」 | §4 項 1 |
| CP 区間・Fisher p | `summary.json` の値と、二項 cdf の二分探索 / 超幾何和の独立再計算が全桁一致 | §3.2、§3.3 |
| bindings (4 block + smoke) | runner sha・repo_head・workload argv・arm の pin / patch sha / witness / observational_only / define / source sha・arms JSON sha・policy sha・toolchain が全部一致。binary sha は block ごとに異なる。backoff arm の source sha は通常と同一 | §1.4 |
| dispatch log | request 5894 / 5895 / 5897 / 5898 (B1〜B4)、smoke 5875。Created / Started / Ended / Elapse は insight §5 の表と一致 | §1.5 |
| `s4-ruling.md` | sha256 `14dbfd6c…` (job dir 原本 = insight verbatim)、mtime 2026-09-18 15:26:11 JST (smoke 投入 15:36:29 より前)。見出しの自己記載「15:30 起草」と 4 分ずれ | §2 |
| verbatim の `.patch.txt` | 末尾空白の正規化で原本と sha が異なる (`whitespace-errata.json` に原本 sha)。job dir `verbatim/*.patch` の sha は insight の記載と一致 | §4 項 9、§6.1 |
| 既裁定 | D2148 項 11 / 項 13、D2150 項 1、D2159、D1686、D1373、D12。phase3.md の [T-2779] は済。rulings-inbox に T-2779 の新規裁定なし | §0.1、§6.4 |

---

## 3. 一次資料の sha256 照合表 (稿 §6.2 が全桁を委ねる表。親が現物から計算、手打ちなし)

job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2779-mocc-g2-observation-conditions/`:

| file | sha256 | byte |
|---|---|---|
| `arm-B/B1/runs/082-e9-instr-nowit/run.json` | `93c5720bb6169ef3a008ad98c3bac5fe57afa0ea36bc88ce4c73d8d3a8e11778` | 2,539 |
| `arm-B/B1/runs/082-e9-instr-nowit/verifier.json` | `15df9bfd83f65cdd6f957680a116d17770af436d7257af49b44f80fa875010b6` | 2,504 |
| `arm-B/B1/runs/082-e9-instr-nowit/trace-manifest.json` | `396b21f4ac247e867ab74864399b7629642c4b5d0d5cc7eaa39132c1b3ce2a80` | 7,991 |
| `arm-B/B2/runs/030-e9-instr-nowit-bo1/run.json` | `426f61cdbfe3533a40ea39a1acd84ceaa1b60063470938f853267479e5643b1b` | 2,518 |
| `arm-B/B2/runs/030-e9-instr-nowit-bo1/verifier.json` | `a5897657e7c94c1268dd02d899ab503aa8d84c168e783dbe2f3e00c3d39432b9` | 2,513 |
| `arm-B/B2/runs/030-e9-instr-nowit-bo1/trace-manifest.json` | `2711e34686c800d90848cfb1d08a99e9148b3739ea8a5f356f66b768a52bda35` | 7,998 |
| `arm-B/B2/runs/033-e9-instr-nowit/run.json` | `60dd6615fe88a01f0fb08d76a1122a9660fb8f57959265c8e8f56718c8e6789a` | 2,504 |
| `arm-B/B2/runs/033-e9-instr-nowit/verifier.json` | `6bff0611ea1bbfc4d376880bae993a83fbbe8974ecad2d3376e993d60475dedb` | 2,499 |
| `arm-B/B2/runs/033-e9-instr-nowit/trace-manifest.json` | `f784a70f8591d791cbd9d146c0af6234f43c9fd6a5d91a9d1eca92b62ca1c23a` | 8,003 |
| `arm-B/B2/runs/069-e9-instr-nowit/run.json` | `ba96a940f1e99c4abed865b43e799653020491ba6b1c4023e5da55f61f3ff164` | 2,504 |
| `arm-B/B2/runs/069-e9-instr-nowit/verifier.json` | `71cb8ce72c02f960ca855ff852bc3609aeef0c669799714f3c052420151f016c` | 2,508 |
| `arm-B/B2/runs/069-e9-instr-nowit/trace-manifest.json` | `7313e9be42da4c856315fb32412b1154303c5b188d2664f43b9e801832e4c45b` | 7,996 |
| `arm-B/B2/runs/077-e9-instr-nowit-bo1/run.json` | `9b4876850f1ec7e3f904ca8d8372a3806ae9d903b6c64d1896de5027966a1b82` | 2,516 |
| `arm-B/B2/runs/077-e9-instr-nowit-bo1/verifier.json` | `604cb14d732953a28018acd482c3d9db125ae4138cf8f28e48ce521be8bc7324` | 2,509 |
| `arm-B/B2/runs/077-e9-instr-nowit-bo1/trace-manifest.json` | `38de16962b37df25bfb161cb396c494baa6d005b1f4c371a8035fc30d7063368` | 7,998 |
| `arm-B/B3/runs/006-e9-instr-nowit/run.json` | `22987d198f5616d0f8ecb3fffd77715256c11e4943a64b4545e70b06365f9f98` | 2,500 |
| `arm-B/B3/runs/006-e9-instr-nowit/verifier.json` | `bb8c86ed1e113fa8b2fa0ab4315d92ffe4af64f42aba634862aabc30aa63029c` | 2,504 |
| `arm-B/B3/runs/006-e9-instr-nowit/trace-manifest.json` | `7f3680d42c8187c2f37e79e54f7820722f0f85d8579c42b83f3d05796c28f616` | 7,999 |
| `arm-B/B4/runs/080-e9-instr-nowit/run.json` | `9211fc0e2ffbff01a8a66ad8d2b78f21de709db30cad3a673249809135bcf530` | 2,502 |
| `arm-B/B4/runs/080-e9-instr-nowit/verifier.json` | `c4b936cc23d3d5ff10c6895e009068fcb9d55bfe054df1d5a9c80b197ba2fd54` | 2,508 |
| `arm-B/B4/runs/080-e9-instr-nowit/trace-manifest.json` | `e6cf802b55d7bc37fd47ab0f6dd9cf11b56f2f08d90e289d2dd08e107e95151c` | 8,000 |
| `dispatch-B1.log` | `14a6b8ed39a5ad25f8a61a81e22af3b73c640b6a63dcbd997c0d1178597010cd` | 4,249 |
| `dispatch-B2.log` | `d297be267774a6028639b4ce025643098f7e0598340d60977042c36d1284cce3` | 4,145 |
| `dispatch-B3.log` | `e1cb1b06505c18bf81d32f350afe634f756f900098729ddc87b8b9b068a111e1` | 4,144 |
| `dispatch-B4.log` | `2bf96c2d08abff4cc2508b3918c3ba59321f44d97f0d97ce0ccc15f0009d3857` | 4,145 |
| `dispatch-smoke.log` | `3b108bc42e59491cb277e4e755df751aa8b31e06883c3557d1b7fc56ab9e9bd2` | 4,230 |
| `arm-B/smoke/result.json` | `7a45a4f257dfe6772044bf163a9b6728b6a572cc3d19a8ec305ff9876ea4f381` | 23,256 |
| `arm-B/B1/result.json` | `db26afc7fcab7772c672cf5b112f05f58d9c3e72d77a20fd176840aacd60e427` | 277,951 |
| `arm-B/B2/result.json` | `f5cdf50fda33162039107480d0646e05d736883b83471f2a7c3da0f9200ccdb7` | 274,819 |
| `arm-B/B3/result.json` | `c883caa298584ebb0d20609618ddd8de413d6cab14e2ed45109c3b9f5643075d` | 274,669 |
| `arm-B/B4/result.json` | `7e43392f4af7fc64c86ce6b86fa9d79b020187b3ed712c3561b8f0f26667ea25` | 274,679 |
| `s4-ruling.md` | `14dbfd6c2f6b101888948c0505c903d78b35e9903f60ec42b3f1c7ed68eb8d6a` | 12,366 |
| `probe/t2779_probe.py` | `7907a545b719845d69b36590cc90cff6b28c242d3b7140d9c52b4a838798df99` | 40,315 |
| `probe/arms-t2779.json` | `4f6aaf5a172eb8eb737bd0ec6e2fcc52e92b5dce2691803f65d8f34e327ebb56` | 1,124 |
| `probe/v4-to-v5.diff` | `e6979b719766013495f5e485228dcfc64c1c723bb4ec76e46092f322aaa4a547` | 9,956 |
| `verbatim/instr-mocc-lock-coverage.patch` | `e9e65b7876050865ee1cbc4d3a05516b09a8fe0b18149e0c063632162fd7bb48` | 4,080 |
| `verbatim/mocc-close-version-counter-gap.patch` | `8a25bd0a5687437269c720cb34a4b26024a6f1f119adf1c16281d455b9ecaa1d` | 1,168 |

repo 内 (wave worktree = local main `b7f970dfa`):

| file | sha256 | byte |
|---|---|---|
| `tools/pegasus/mocc_trace_v1_policy.json` | `66ea7135c6d84cfd09013f33da23d8ca8015dcb547e34db7c802644f4986acd6` | 1,241 |
| `patches/instr-mocc-lock-coverage.patch` | `e9e65b7876050865ee1cbc4d3a05516b09a8fe0b18149e0c063632162fd7bb48` | 4,080 |
| `output/insights/2026-09-18/t2779-mocc-g2-observation-conditions/README.md` | `559d8e68ee9d875bd9580ef08e70a9c3641019d225c6d7579a8958a0767a9724` | 18,497 |
| `output/insights/2026-09-18/t2779-mocc-g2-observation-conditions/summary.json` | `fee7803f27bbdf2637b4d4f667430e379e1a89f09d47b4056a1892b14a765459` | 3,612 |
| `output/insights/2026-09-18/t2779-mocc-g2-observation-conditions/verbatim/s4-ruling.md` | `14dbfd6c2f6b101888948c0505c903d78b35e9903f60ec42b3f1c7ed68eb8d6a` | 12,366 |
| `output/insights/2026-09-18/t2779-mocc-g2-observation-conditions/verbatim/whitespace-errata.json` | `8edb281d528f4ab1767d9563abb14dc4b7338ab0f1f7eecb94f7886ae0c45a3b` | 3,666 |
| `output/insights/2026-09-18/t2779-mocc-g2-observation-conditions/verbatim/recovery-raw-hashes.log` | `9619542305050feb38545ccaa8ed926c5e64cea4c58df5220baa3db6f76f30cc` | 218 |

bindings の値 (B1 `result.json.bindings`、4 block で一致): pin `e9e477ca1b55348ab4530de0b1cf663ce4555290`、`repo_head` `c8e8dc06f33891aa2fd6345063b30ca11b52fe6d`、
source sha256 通常 / backoff `bd0add59890a60150b9c650155943ddd0c1e91eeccc0121a6b674c834b3ed04c`、診断 `1c5da7c8439144d02621071622e5eba31f1ff583c4fbda5efdfe7483c2c3168a`、
B1 の binary sha256 通常 `4317ea39c69a7589ef27d8ed5ad2e36438cf27b52ef3e259fbad36fd46bd61d0`、診断 `077fabf8403f540ff425bbf572c0cf7953abdc08f10518c0fdcad1589ea9432b`、backoff `3bf14e5604f4b78e0955f243cc0058bfafbc0fea39593e93f58409c39d62c663` (B2〜B4 は別値)、
toolchain version 本文 sha256 `b713e6ab62b67126b772f6b0a8d9751070f0d0315c7017291cb5dde67747b9c0`。

---

## 4. 親の機械照合 (稿 v1、job dir `scratch/check_doc.py`、出力 `scratch/check_doc-v1.log`)

稿の hex 識別子 (7〜64 桁の前置 59 token) を上表 + bindings の値の集合と前置一致で照合し、不一致 0。block 表・合算 k / m・CP 区間 (小数 4 桁と生値)・Fisher p・
G2 7 走の表 (cycle・key 下 4 桁・`[epoch, tid]`・round / 位置・commit 数)・dispatch 表 (request・node・Created / Started / Ended・Elapse)・
Elapse の和 8,911 S・commit 数の範囲・`result.json` の started / finished を現物から再抽出して全部一致 (`ALL OK`)。
**照合で 1 件捕まえた:** B2〜B4 の `result.json` の `started_at` / `finished_at` を最初は B1 の値から推定して書いており、実値 (B2 06:50:16 / 07:27:12、
B3 06:55:37 / 07:32:38、B4 06:50:29 / 07:27:33 UTC) へ直した。稿への数値は現物から貼る (T-2674 の 1 桁誤りと同型の near miss、F1 型)。
稿 v1 の照合 log は `verbatim/check-doc-v1.log`、fix 後の最終版は `verbatim/check-doc-final.log` (いずれも `ALL OK`)。

---

## 5. 段 6 — 独立 read-only レビュー 1 本 (D2148 項 11) と焦点再レビュー 1 本

- レビュー (`verbatim/s6-review.md`、prompt `verbatim/s6-review.prompt.md`、codex `gpt-6-astra` / `medium`、read-only、2 レンズを 1 本で: 数値・逐語・識別子の照合 +
  過剰・限定・裁定整合・出所): **must-fix 1 / should-fix 4 / nit 1、「着地は止める」**。親の裁定は全件 real・採用。
  1. (must) 稿が「thread id は成果物に無い」と書いたが、生 trace の C 行 (`C <txid> <thid> <epoch> <tid> <read_set 数> <write_set 数>`、source
     `writePhase()` の `#if TRACE` 内) にある。B1/082 の `trace_33.log` に `C 406139 33 42 176 4 6`、`trace_0.log` に `C 406140 0 42 177 6 4`
     (親が現物で確認)。→ §0.4・§3.4・§4 項 3 を「verifier 出力には無いが生 trace にある、7 走の対応表は未作成」へ直し、§4 に項 12 を新設 (13 項目)。
  2. (should) 検出力の追加値 (0.30 / 約 0.70) と基準率の由来 (7/120・2/40) は `s4-ruling.md` 項 6 の本文になく記録 insight §4 にある。「本稿の値は全部
     runner の JSON の書写」も時刻・検出力・再計算には成立しない。→ §2 項 5 で逐語と親の設計説明と本稿の再計算を分け、§5 項 17 を転記範囲へ限定、
     §6.3 の出所表を 3 行に分けた。検出力 4 値は親も独立再計算して 0.831467 / 0.721809 / 0.302390 / 0.701730 (レビュー子・焦点子と一致)。
  3. (should) §5 項 16 の「現行 pin の checkout では D1373 の関門で拒否される状態のまま」は本観測が確かめていない現況の断定。→ 「between-run floor の
     生成可否 (D1373 の関門) を検査したものでも変えたものでもない」へ。
  4. (should) (P1) A-1 descriptive 稿の「非認証」という共通点だけでは results 系列への配置根拠にならない。→ §0.2 を「段 4 裁定が結果を見る前に固定した
     単一の観測 protocol (標本・主比較・主表示・欠測規則) を 4 block で完走した 1 結果」と書き換え、A-1 類推を外した。README 行にも同じ 1 句。
  5. (should) §3.6 の例文「同一 block の 3 arm × 各 120 走」は 1 block・1 binary の 120 反復に読める。→ 「各 block 内に 3 arm を回転配置した 4 block
     (別 node、各 arm 合計 120 走)」へ。
  6. (nit) `observational_only: true` の意味 → §1.2 に 1 文 (診断介入の観測専用という位置づけを記録へ写す runner の field、verifier 判定を書き換えない)。
  - 所見なしの観点: 数値・hex の転記 (4 block + smoke、7 走の JSON、patch、runner、arms、diff、dispatch log、insight・summary・errata の sha / byte)、
    block 別 k の再集計 1/2/1/1・0/0/0/0・0/2/0/0、CP・Fisher の独立再計算、7 走の cycle / key / 版 / 位置 1/3/3/3/2/3/2、時刻・Elapse 8,911 S、
    bindings、§4 の「無い」の裏取り (非 G2 353 dir に `trace/` 無し、verifier file digest 無し、seed 記録無し、witness on arm 無し)、件数 (限定 18・360 走・
    336 file・1,981,789,619 byte)、規律 1 / 2 / 7 と D2148 項 13 / D2150 項 1 / D2159 との整合、(P2) commit 数の掲載は規律 1 と両立、(P3) 方針妥当。
  - 親の brief への異議: (P1) 論拠に異議 (上記 4 で採用)、(P2) 異議なし、(P3) 方針は妥当だが出所の混同を直す (上記 2)。「機械照合 ALL OK は散文の正確さまで
    保証しない」— そのとおりで、所見 1・3 は機械照合の射程外だった。
- fix は親が docs-only で当てた (job dir `scratch/apply_fix1.py`、置換 11 箇所、各 1 回一致を assert)。fix 後に機械照合 `ALL OK`、`check_docs.py` 違反なし。
- 焦点再レビュー (`verbatim/s6-focus.md`、prompt `verbatim/s6-focus.prompt.md`、`DW-O16` の対応表): **closed 5 / partial 1 / regressed 0、新規所見 2 (nit)、
  「着地は止めない」**。partial は所見 2 で、新規 nit 2 件 = (a) §2 項 5 の「逐語」が `α=.05` を `α = .05` に整形していた、(b) `0.058 = 7/120` は等式でない
  (7/120 = 0.058333…)。→ 親が両方反映 (逐語を原文表記に戻し「空白整形なし」と明記、「7/120 = 0.058333… を丸めた値」)。反映後に逐語の一致を grep で確認、
  機械照合 `ALL OK`、`check_docs.py` 違反なし。焦点子の検出力独立再計算 (0.831467371927 / 0.721808728928 / 0.302389858606 / 0.701729548189) は親の値と一致。
- 費用: codex 2 本 (review 1、focus 1)、いずれも read-only、rc 0。

---

## 6. 段 7 以降の記録と運用の気づき

- 変異 matrix は実装面差分ゼロで免除 (`DW-S04`)。三軸語走査 (`s8b_holdout_freeze search`) は holdout の conjunction hit 0 (positive control の rr50 は本稿を含め設計どおり hit)。
  `check_docs.py` 違反なし。fold `--dry-run` planned (failures fragment 1 = F1 の near-miss 再発、worklog fragment 1)。受入全走は免除せず、結果は worklog fragment に書く。
- (F1 型 near-miss、自分で捕捉) 稿 §1.5 の B2〜B4 の `result.json` 時刻を推定で書き、commit 前の機械照合で実値に直した (§4)。専用 handoff の節見出しの時刻も
  2 回推定で書き `date` で訂正した。failures fragment に F1 の再発として追記。
- (作法) 隔離 session の Bash guard は `output/insights/...` の path と heredoc の同居を「分類不能」で拒否する。検査 script は Write で job dir に置き
  `python3 <script> <path>` で呼ぶ (DW-O03 の射程が `output/` root にも掛かる実測)。
- 本 wave の scope 外 (起票しない): 7 走 14 txid の thread id 対応表の作成 (生 trace から機械抽出できる。次に mocc の観測を稿へ載せるときに同じ runner の
  出力へ含めるのが安い)。
