---
authority: none
default_effect: no-state-change
---

# t080 fixture の config.h 取り込み漏れ — 取り込んだ場合の忠実性の増分と所要の増加 (2026-09-17)

依頼は「t080 fixture が実 repo の tracked file `orchestrator/tests/fixtures/sort_swo_masstree/config.h` を
取り込めていない件の影響を測り、採否を裁定パッケージで返す。実装差分は原則ゼロ」。
結論は **本 wave では実装しない**。計算ノードで実測した結果を §3 に、採否の裁定パッケージを §4 に置く。
親の推奨は「path を名指しした `add -f` 1 行 + membership 検査 1 本を別 wave で入れる」だが、
放置しても certified 選択・レポート・台帳は変わらないので、採否はユーザー裁定に返す。

## 一次資料

| 段 | file | 内容 |
|---|---|---|
| 1 | `stage1-brief.md` | 親の brief (P1〜P4 は provisional。§6 の訂正を受けた) |
| 2 | `stage2-plan.md` | Codex plan (read-only) — probe 設計、13 scan の静的内訳、一般解の反証 |
| 3 | `stage3-lensA.md` / `stage3-lensB.md` | 敵対相談 2 レンズ (正しさ境界 / 整合・実効性)、計 23 所見 |
| 4 | `stage4-ruling.md` | 親の裁定 (所見表、プラン v2、判定基準を結果を見る前に固定) |
| 5 | `stage5-author-report.md` | Codex author の報告 (probe 361 行、selftest 緑) |
| 6 | `stage6-fix-report.md` | Codex fix 子の報告 (growth hold 対応、415 行、hold-only 緑) |
| — | `probe-source.md` | probe 本体の逐語 (`.py` は repo に残さない。保全先と sha256 を記載) |
| — | `run1-result.json` | 本走 1 回目 (bnode028、6 秒 rc=1、growth hold の import 拒否) の原本 |
| — | `run2-result.projected.json` | 本走 2 回目 (bnode028、1,105 秒 rc=0) の射影。原本 661,637 bytes (sha256 `22369458a9ced013…`) から `add.general[*].paths` (419 path × 10 回の重複) を件数へ置換した以外は同一 |

起票元は `output/insights/2026-09-16/t2559-acceptance-floor-t080/README.md` §4-2 と D2068。

## 1. 機序 — なぜ 1 件ずれるか

`_build_t080_stub_free_e2e_repo` (`orchestrator/tests/test_s8b_oracle_driver.py:1364-1455`) は
`orchestrator/` を `shutil.copytree` で丸ごと複製し (1380 行)、git 可視の `output/` を複製し (827〜874 行)、
`git init` した fixture で `git add -A` する (1451 行)。複製された
`orchestrator/tests/fixtures/sort_swo_masstree/.gitignore` の 8 行目 `/config.h` は、実 repo では tracked に負けて
効かないが、fixture では新規 index への `add -A` に効く。結果、実 repo で scan される `config.h` (10,448 bytes、
sha256 `e9a4ecd3dfb9aef9…`) が fixture では ignored untracked になり、production scanner
(`s8b_holdout_freeze.enumerate_repository_files`、tracked regular + 非 ignored untracked + ccbench) の対象から外れる。

## 2. 静的閉包 — 同型の穴は config.h の 1 件だけ

- 実 repo (main `38353207f`) で tracked かつ ignore 規則に一致する file は **419 件**。由来は root
  `.gitignore:25` (`output/env/pegasus/silo_ladder_rung1/job-staging/`) が 418 件、
  `sort_swo_masstree/.gitignore:8` が 1 件。fixture は root `.gitignore` を複製しないので、418 件は fixture で
  `add -A` に拾われ一致側に落ちる。fixture へ複製される `.gitignore` は `sort_swo_masstree/` の 2 本だけで、
  `doc/.gitignore` は tracked file に当たらない。
- `orchestrator/` 配下の非 ignored untracked は 0 件。ignored untracked は 9 件で全部 `__pycache__/*.pyc`
  (copytree の除外対象)。逆向きのずれ (fixture が実 repo より多い) の候補は無い。
- `config.h` に三軸 key (`ycsb_` 接頭の 3 語) は 0 件。known-axes 側の glob は `output/campaigns/` 配下限定。
  `_live_scan_sha256` (`t080_freeze_migration.py:1741`) は `search` を含まず、`search.file_count` は
  「受理集合に直結しない」と production が注記する (同 1735 行)。t080 e2e は `file_count` を pin していない。
- §3-1 の実測がこの静的閉包を動的に裏づけた (期待集合との差がちょうど 1 件、取り込むと差 0)。

## 3. 実測 (計算ノード bnode028、run2、request 4055.nqsv、Elapse 1,105 秒)

probe は同一 fixture を 1 回組み、`.git/index` を A (現行) / B (取り込み後) として保存し、復元で切り替えて
測る (D2068 の作法: 同一 tree 内の交互対比較)。builder (`issue_receipt=False`) の所要は 163.8 秒 (参考値)。
growth hold を通す pytest session (collect-only、`-k` 不一致) は 2.19 秒、rc=5。

### 3-1. 集合 — 忠実性の増分

期待集合 E = source の `orchestrator/` 実体 regular file (`__pycache__`/`*.pyc` 除く) ∪ git 可視 `output/`
− receipt/draft 2 path ∪ basis 上書き 30 path ∪ operational 6 path ∪ `.gitmodules`。

| 集合 | 件数 | E − 集合 | 集合 − E |
|---|---|---|---|
| E (期待) | 25,182 | — | — |
| A index (現行) | 25,181 | **{config.h}** | ∅ |
| A `enumerate_repository_files` | 25,585 | {config.h} | ccbench 404 件 (E に submodule を入れていないため) |
| A scan 対象 (`output/s8b-freeze/` 17 件を除外後) | 25,568 = `search.file_count` | {config.h} + 除外 17 件 | ccbench 404 件 |
| B index (取り込み後) | 25,182 | **∅** | ∅ |

B − A = {config.h}、A − B = ∅。**取り込むと fixture の index は期待集合 E と完全一致する** (25,182 / 25,182)。
scan の `skipped_binary_count` は 1,810。

### 3-2. 取り込み操作の所要 (各 10 回、毎回 A index を復元してから計測、復元は timed 外)

| 方式 | 内訳 | 初回 | 反復 (n=9) 中央値 [min, max] |
|---|---|---|---|
| 一般解 | source で `git ls-files -z -ci --exclude-standard -- orchestrator output` (419 path) | 5,306.9 ms | **4,821.9 ms** [4,796.6, 4,951.1] |
| 一般解 | fixture で `git add -f --pathspec-from-file=- --pathspec-file-nul` (419 path、missing 0) | 126.7 ms | 128.3 ms [126.9, 130.5] |
| 一般解 | 一連 (列挙 + 検証 + add) | 5,508.3 ms | **5,028.4 ms** [4,999.9, 5,157.7] |
| hard-code | fixture で `git add -f -- orchestrator/tests/fixtures/sort_swo_masstree/config.h` | 29.1 ms | **28.7 ms** [28.2, 28.9] |

**一般解は実 repo 側の列挙が 4.8 秒**で、fixture 側の add (128 ms) の 38 倍である。原因は `ls-files -ci` が
tracked 27,022 件全部に ignore 規則を照合すること (Lustre 上の実 repo)。hard-code は 29 ms。
限界: A index は commit 後の状態で、採用位置 (`add -A` 直後・commit 前) と index の cache 状態が違う。

### 3-3. scan の対比較 (warm-up 2 対を除く N=20 対、AB / BA 交互、timed は `search_repository(root)` だけ)

| 量 | 中央値 | Q1 | Q3 | IQR | min | max |
|---|---|---|---|---|---|---|
| A (現行) 1 scan | 18,485.5 ms | 18,362.7 | 19,513.7 | 1,151.1 | 18,064.3 | 28,382.9 |
| B (取り込み後) 1 scan | 18,398.8 ms | 18,319.1 | 18,769.1 | 450.0 | 17,929.8 | 28,694.3 |
| 対差 B − A | **−70.1 ms** | −418.4 | +139.4 | 557.9 | −2,823.2 | +2,809.4 |

対差の正負は 7 / 13。順序別の対差中央値は AB (B が後) で −324.9 ms (正 1 / 負 9)、BA (A が後) で
+149.7 ms (正 6 / 負 4) — **2 走目が速い順序効果 (±数百 ms) が支配的**で、config.h 1 件の増分は
その中に埋もれて分離できなかった。順序効果を相殺した推定 (両順序の中央値の平均) は −88 ms、
レンズ B の近似 (s_d ≈ IQR / 1.349 ≈ 414 ms、N=20 の中央値 95% 半幅 ≈ 2.46 s_d / √N ≈ 227 ms) で
対差の区間はおよそ [−297, +157] ms/scan。**統計上限は +157 ms/scan、13 scan 換算で約 2.0 秒。**
一方 per-file 換算 (18,485.5 ms / 25,568 file = 0.723 ms/file) の期待増分は **≈ 0.72 ms/scan、13 scan で ≈ 9.4 ms**。
末尾の 5 対 (pair 15〜20) は A/B とも 20〜28 秒に膨らんでおり、同居 job か I/O の外乱を含む。

### 3-4. 判定不変 (動的)

全 22 対で、A/B の report の `match_convention` / `holdouts` / `positive_control` が等しく、
`_live_scan_sha256` が等しく、`search.file_count` は 25,568 → 25,569 (+1) だった (`statistics_valid=true`、
`failures=[]`)。現在の `config.h` bytes を basis commit 前に取り込んで新規発行する限り、受理・拒否は変わらない
(静的根拠は §2、束縛経路の表は `stage2-plan.md` §1 と `stage3-lensA.md`)。

## 4. 採否の裁定パッケージ (ユーザー裁定)

費用許容値は既存裁定に無い。レンズ B の提案「critical path への追加 1 秒以内 (e2e 200〜222 秒の約 0.5%、
13 scan 換算で 77 ms/scan)」を親が提案値として採る。D2086 の「−10% なら採らない」は高速化の採用基準であり、
忠実性向上の費用許容値には転用しない。

| 案 | 変更 | 費用 (fixture 構築 1 回あたり) | 効果 | 裁定 |
|---|---|---|---|---|
| (a) hard-code | `test_s8b_oracle_driver.py:1451` の `add -A` 直後に `_run_git(root, "add", "-f", "--", <config.h の path>)` 1 行 + 実 builder の未発行 fixture で config.h が index と `enumerate_repository_files` の双方に含まれ source と bytes 一致する新規 test 1 本 | 29 ms + scan 増分 (期待 9 ms、統計上限 2.0 秒) | fixture 可視集合が E と完全一致 (差 1 → 0) | **親の推奨**。ユーザー裁定へ |
| (b) 現状維持 | なし | 0 | fixture が E より 1 件狭い。判定・成果物は不変 | ユーザー裁定へ |
| (c) 一般解 | 実 repo の `ls-files -ci` 集合を `add -f` | **5.0 秒** (列挙 4.8 秒) × key 数 (現行 5 key なら shard あたり約 25 秒) | (a) と同じ集合。将来の同型 path も救うが、非コピー対象 (receipt/draft、`*.pyc`) を force-add しうる成立条件の欠落あり | **不採用 (親裁定、decisions に記録)** |

(a) の変異事前登録 (採用 wave 用): 取り込み行を削除する変異 → 新規 membership test が赤。**既存 test は
この削除を殺さない** (レンズ A 所見 7: 可視性検査群 `T:1633-1705` は output 複製までで再 index 化後を見ない)。
等価変異 = comment 行追加で SURVIVED。(a) は D2086 (proto 化、branch 保存) と独立で、snapshot 集合を要しない。
(a) の推奨理由: 費用 29 ms は e2e 200 秒の 0.015%、効果は E との完全一致。ただし成果物影響ゼロ (§5) なので
優先度は P3 相当であり、採らない判断も妥当である。

## 5. 本 wave が主張しないこと

- 「発行経路 (draft → validate → finalize → verify → gate、13 scan) の e2e wall の増分」は測っていない。
  probe の B index は staged addition で発行の clean 条件 (`M:1833`) を満たさないため、発行 A/B は別の検証になる。
- 「scan 増分が 9 ms である」とは主張しない。統計的には分離できず、上限 2.0 秒 (13 scan) まで否定できない。
- 「fixture が実 repo 全体と一致した」とは主張しない。E は構築規則 (copytree の除外、basis 上書き、submodule の
  known pin、receipt/draft の除外) で射影した期待集合であり、実 repo の現 scan 集合との差 (レンズ A 所見 2〜4) は
  本件の scope 外として残る。
- 「config.h に将来三軸 conjunction が入る」現実性は判定不能 (masstree の configure 生成物)。
- login node の値は使っていない (runbook §7.0.0: 性能測定は常に計算ノード)。

## 6. 段 3 所見と親の訂正 (要約)

23 所見の裁定表は `stage4-ruling.md`。親 brief の訂正: (i) 実測環境 login node → 計算ノード、
(ii) 「所要増分は ms 級」→ 未測定 (実測後: hard-code 29 ms、一般解 5.0 秒)、(iii) 「一般解は 1 手・件数非依存」→
419 path を処理し 1 行ではない、(iv) DW-G05 の「レポート・台帳は変わらない」は実 repo の既存成果物に限る
(fixture の `file_count`、basis OID、receipt bytes は変わる)、(v) 「untracked 0 件」は非 ignored に限る。
棄却した所見は無い (refuted は plan の妥当性を確認する向きの 5 件)。

## 7. run1 の失敗 — growth hold の import 拒否 (F351 と同型)

本走 1 回目 (request 4025.nqsv) は `from orchestrator.tests import test_s8b_oracle_driver` が
`GrowthTestHoldBypassRefused` で落ちた (6 秒、rc=1)。held module は末尾の `enforce_held_functions(...,
plain_runner="none")` が enforcing な pytest session 内でしか import を通さない。解除 env はユーザー明示専用なので
使わず、probe の内側で `pytest.main([held module, "--collect-only", "-q", "-p", "no:cacheprovider",
"-k", <不一致名>])` を呼び、`pytest_sessionstart` hook で完全修飾名を import して `sys.modules` に残す形に
直した (`-k` で items を空にし `pytest_collection_finish` の receipt memo prewarm を避ける)。段 2 plan と段 3 の
2 レンズはいずれも held module の import 制約を見落とした (plan §3 は「静的には直接呼べる」と判定)。
計算ノード dispatch 1 本 (6 秒) を空費した。

## 8. 工数・環境

- codex 子 5 本 (plan 1、consult 2、author 1、fix 1、全段 `gpt-6-astra`)。親の実走: selftest 1 (login)、
  hold-only は fix 子が login で 1 回、本走 2 回 (計算ノード generic dispatch、bnode028、4025.nqsv 6 秒 / 4055.nqsv 1,105 秒)。
- 実装差分ゼロ (probe は repo に残さず `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2708-fixture-config-h-gap/` へ保全)。
  変異 matrix は免除。受入全走は記録 commit 後の最終 tip に対して緑の受領証 1 本を得るまで再投入した
  (attempt 1 は wrapper の post-claim merge 後に main がさらに進んだ postcheck 競走でテスト未走行、attempt 2 は
  24,749 passed / 10 failed で赤は全部負荷由来 — `git archive` / `git log` の 30 秒 timeout 5 件 (F945 型)、codex launcher の
  timing 系 4 件、`run_tests_preflight` の dispatch 判定 1 件、load average 59 — 自分の差分 (docs + insight) から到達不能。
  attempt ごとの waiter log と shard junit の抜粋は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2708-fixture-config-h-gap/acceptance/`
  に保全)。
- fixture の実体 (`run2/build`、978 MB) は同 dir に残っている。保全対象は `result.json` と `index-A` / `index-B` だけ。
