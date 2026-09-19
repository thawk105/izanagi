# B-10 静的 backoff 右 tail — 第 2 cohort (独立再現) を事前登録追記の commit 後に投入し、集団判定まで出した

`authority: none` / `default_effect: no-state-change`

**種別:** 実測 + 記録。**実装面 (D95 決定 2) の差分はゼロ** (事前登録の追記、results 稿、README 表 1 行、本 insight、spool fragment のみ)。

- 日付: 2026-09-19 (JST)
- wave: `dev-wave-b10-tail-cohort2`、branch `worktree-dev-wave-b10-tail-cohort2`
- 起点 local main: `a99425b66258911973785b11fd7d194884aeec64`
- 依頼: 「B-10 静的右 tail の第 2 cohort を投入する。ユーザー決定 (2026-09-19): 第 2 cohort は独立再現とする。cohort 1 の
  verdict を主として保持し、cohort 2 の verdict は再現欄に併記する。合成はしない。この地位の明記を結果を見る前に
  事前登録の追記 (cad6f46d8 の bytes は不変、日付付き append-only 追記) として commit してから投入する」

## 0. この wave が主張すること・しないこと

**主張する。**

1. **地位の明記 (D2050 の充足) を結果より前に commit した。** commit `8737cacb4` (2026-09-19 22:01:23 JST) が
   事前登録 `docs/b10-backoff-static-tail-preregistration.md` の末尾に 51 行の追記を加え、`cad6f46d8` の 71,231 bytes は
   新 file の先頭部分として sha256 一致 (`8084be04…`) のまま残る。§5 spec の SHA-256 は両版で `08f5849b…`。
   投入は同日 22:15:25 JST (commit の 14 分後)。§1。
2. **第 2 cohort は完走し、本番 CLI の集団判定は `not-observed-in-any-workload` だった。** group
   `b10-backoff-grid-20260919T131526Z-2235286`、job `10752` / `10753` / `10754`、3 workload とも `not-observed`、18 区間
   すべて `declining`、`failures` 空、正しさ 120 記録 certified・anomaly 0。§3。
3. **cohort 1 と同じ verdict である。** 事前登録追記のとおり、これを cohort 1 の稿・図の変更、統合 verdict、
   「飽和しない」への読み替えのいずれにもしない。稿は再現欄 (§2.6) に両 cohort を区別して併記した。§4。
4. **最初の投入 (attempt 1) は 3 job とも 5 秒で落ちた。** 原因は T-548 (2026-09-16) 以後の job body が gflags/glog を
   hydrate 済み staging から読むのに、新規 worktree にそれが無かったこと。測定・campaign・WAL は作られていない。§2。

**主張しない。**

- **「飽和しない」「飽和点が存在しない」「再現されたので飽和しない」とは言わない。** 事前登録 §4.5 の固定表現と
  2026-09-19 追記の項 7 に従う。
- **性能を認証していない。** `performance_certified: false` のまま。
- **2 つの cohort を合成していない。** 数値の近さを再現精度として評価しない。
- **fig8 を改変していない。** fig8 は cohort 1 の図のまま。再現欄の追加は生成器の改変 (実装面) を要し別 wave (§5)。
- **B-10 を閉じたとは言わない。** [T-2647] も閉じていない。

## 1. 事前登録の追記 — 何を書き、どう検査したか

- 追記の内容は事前登録末尾の「2026-09-19 追記 — 第 2 cohort の地位 (独立再現) を結果より前に固定する」。
  項 1 地位 (独立再現、置換でない)、項 2 主と併記 (主結果は cohort 1 に固定、既存の稿・図は凍結、第 2 cohort の稿と
  fig8 の再現欄に両 cohort を区別して併記)、項 3 合成しない、項 4 結果にかかわらず 1 本を報告 (未完走・報告失敗も
  §7 で開示、第 3 cohort は定めない)、項 5 同じ規則、項 6 同一機構・別 identity (探索走 campaign の exact path)、
  項 7 主張の範囲を増やさない (verdict ごとに §4.5)。
- **§0 への挿入は行わなかった。** 親の初稿は §0 の箇条書きへ 1 項目を挿入していたが、段 3 相当の consult が
  「ユーザー指定の append-only と一致しない」を real 所見として挙げ、親が採用した。§0 が求める「変更理由と時点」の
  記載は追記の冒頭に「§0 への記載 (末尾配置)」として置いた。
- consult (read-only, gpt-6-astra, reasoning medium, 6 model call, 257,763 tokens raw, accepted) の所見 9 件と
  裁定: real 7 (§0 挿入、併記先と「改めない」の区別、未完走時の開示、前向き性の対象を cohort 2 に限定、「3 本目」は
  決定を越える、探索走 path の具体化、brief の §4.5 一般化) を採用、refuted 2 (別 blob 束縛は §4.9/§7-12 に反する、
  test の pin を壊す) に同意。逐語は `verbatim/stage3-consult.md`、prompt は `verbatim/stage3-consult-prompt.md`。
- 検査: `check_docs.py` 緑、provenance 全史監査 11623 件違反なし、`test_b10_backoff_static_tail_formal.py` +
  `test_b10_backoff_grid_submit.py` 166 passed (commit 後、HEAD blob と作業ツリーの一致と spec SHA pin)。
  **login node で 17 件が最初赤になった** — 他ユーザーが `/tmp/.git` (2026-09-07、空 dir) を置いており、pytest の
  `/tmp/pytest-of-tanab/…` が submit script の「repo 祖先」guard に当たる環境要因。`--basetemp` を job dir に移して
  緑。自分の変更に帰属しない (受入は計算ノードで走るので影響しない)。

## 2. 投入 — attempt 1 の失敗と attempt 2 の完走

| attempt | 投入 (JST) | group | job | 結果 |
|---|---|---|---|---|
| 1 | 22:11:18 | `b10-backoff-grid-20260919T131120Z-2159341` | `10743` / `10744` / `10745` | 3 job とも起動 5 秒で `stage=dependency_policy_contract` 「gflags source is not a real directory」rc=2。campaign・WAL・測定なし (`.failure.json` の `campaign_wals: []`) |
| 2 | 22:15:25 | `b10-backoff-grid-20260919T131526Z-2235286` | `10752` / `10753` / `10754` | 22:15:37 開始、22:29:31 前後終了 (Elapse 839 秒)、3 job とも `completion.json` `status: complete` |

- attempt 1 の原因: T-548 (`0165027e0`、2026-09-16) が job body の gflags/glog 供給元を
  `$REPO_ROOT/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src/` (gitignore 対象) へ移した。cohort 1
  (2026-09-15) は T-548 前だったので不要だった。**投入 script `submit_b10_backoff_grid.sh` は login 側で staging の実在を
  検査しない**ので qsub は通り、計算ノードで落ちる。対処: `python3 tools/pegasus/fetch_third_party.py hydrate --repo-root
  <worktree> --cache-root /work/1/SFC/tanab/izanagi-thirdparty-cache --staging-root <worktree>/output/env/pegasus/
  silo_ladder_rung1/job-staging/thirdparty-src` (5 source、rc=0、clean tree 維持)。
- 再投入前に鎖の残りを login で全部実測した (起動時検査は 1 投入 1 欠陥しか出さないため): gflags/glog の HEAD ==
  policy pin かつ `status --porcelain` 空、freeze digest (`output/s1-freeze` + `output/s8b-freeze`) ==
  `c405c742…`、作業ツリーの事前登録 bytes == `8737cacb4` の blob、探索走 campaign 実在、HEAD の job script bytes ==
  投入 script が hash する bytes (clean tree)。
- 投入元は隔離 worktree の repo root (cohort 1 と同じ型)。投入後〜完走まで worktree には 1 byte も書いていない。
- 3 job の `reservation.json` は `source_binding.repository_commit = 8737cacb4…` を記録している。

## 3. 集団報告 — 本番 CLI の出力

手順書 §4 の argv で 2026-09-19 22:30:18 JST に生成。終了コード 0、stdout・stderr とも空。出力先
`/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/group-report-20260919-cohort2/` (生成前に 3 成果物の不在を確認)。
入力は attempt 2 の 3 campaign
(`…-write-heavy-sweep-45feee64` / `…-balanced-sweep-d7cbfe58` / `…-read-heavy-sweep-ed0b204e`)、探索走 campaign は
追記の項 6 が固定した `…/t2418-backoff-static-explore-v1-silo-balanced-sweep-783ccbe8`。

| 成果物 | SHA-256 |
|---|---|
| `t2500-backoff-static-tail-formal.json` | `932f6cccbf1a4be2ccbd4c11af31fe2a402b26fc352eb05e22b87b14cef504fd` |
| `t2500-backoff-static-tail-formal.dat` | `15b99944b8429c0c2bb0d36d4498c7ab2a57d3f90c97d2430f34838905881fd6` |
| `t2500-backoff-static-tail-formal-complete.json` | `934211874c779c7bfbffd9a596ef9b7094b7bfa2f7a660203065759abf59420c` |

- `verdict` = `not-observed-in-any-workload`、`failures` = `[]`、`performance_certified` = `false`、
  `preregistrations[]` 3 件とも commit `8737cacb4…` / blob `8511d479…` / spec `08f5849b…`。
- 3 workload とも `state` = `not-observed`、18 区間すべて `declining`、`confirmed_nonmonotonicity` / `upward_wiggle`
  とも全区間 `false`、`statistics[].gate_passed` 24 cell とも `true` (変動係数の最大: throughput 0.56%、abort 率 0.58%)。
- 正しさ: 120 記録すべて `certified: true`、anomaly 0、`verdict: serializable`、`source_measurement: trace_enabled`、
  `correctness_mode: legacy`。`perf_bin_sha256` は各 workload 8 個が相異なる。
- 所要: `sweep_elapsed_s` 822.14 / 820.43 / 822.64 秒 (cohort 1 は 823.31 / 820.90 / 825.31)。
- 抽出は親の job dir の補助 script で機械的に行い (`verbatim/extract-cohort2.md`)、同 script を cohort 1 の集団報告に
  当てると cohort 1 の稿の全表を byte 一致で再現した (自己検算)。稿の数値表 66 行 (区間 18 + 平均/変動係数 24 +
  生標本 24) は抽出出力と 66/66 一致。

## 4. 成果物 — results 稿と README

- `docs/paper-story/results/2026-09-19-b10-static-tail-cohort2.md` (file 名は結果前に中立名で固定): cohort 1 の稿と同型。
  §1.1 に両 cohort の束縛の差 (commit・blob は別、spec は同一)、§1.5 に失敗 attempt の開示、§2.6 に再現欄
  (主結果 cohort 1 と独立再現 cohort 2 を区別して併記、合成しない)、限定 16 件。
- `docs/paper-story/README.md` の results 系列表に 1 行。
- fig8 への再現欄の材料は稿の §2.6 と §4.1 (group id、3 成果物の SHA-256、verdict、束縛) に揃えた。

## 4a. 段 6 独立レビュー (read-only) と fix

review 1 本 (gpt-6-astra、7 レンズ、`verbatim/stage6-review.md`) は cohort 2 の数値・識別子・hash に転記誤りを見つけず
(§2.2 の推定値 108 個、§2.3 の平均 48 + 変動係数 48、§2.5 の 360 値、§4.1 の hash を JSON / DAT と直接照合)、
総括は yes-with-fixes。所見 5 件の裁定と対応:

| # | 格付け | 所見 | 裁定 | 対応 |
|---|---|---|---|---|
| 1 | must-fix | §2.6 の cohort 1 欄の出所が旧稿 (二次資料) で、系列規則「数値の出所は一次資料だけ」に反する | real | closed — cohort 1 の集団報告 3 file と job root へ同じ抽出手順を当て直接照合 (`verbatim/extract-cohort1-crosscheck.md`、hash は JSON `5f426ecb…` / DAT `758b3121…` / 完了記録 `7192d1da…` を実計算)。§4.2 の出所行を一次資料へ置換 |
| 2 | should | §2.2 と限定 2 が `qhat` の単調な変化を暗示 (write-heavy 1768→2500 は −0.5445 で左隣 −0.5475 より小さい負、read-heavy 3535→5000 も同様) | real | closed — 「最右区間は最左区間より負側」に改め、非単調の実例を併記。限定 2 の文言を置換 |
| 3 | should | cohort 1 稿 §1.1 が開示した 2026-09-10 追補の §0 未記載の留保が脱落 | real | closed — §1.1 に留保と「遡及的に正当化しない」「§7-12 / invalid へ読み替えない」を追加 |
| 4 | should | 失敗 attempt に機械生成 verdict が無いことを明示していない (追記の項 4) | real | closed — §1.5 に 1 文追加 |
| 5 | nit | insight の hash を省く理由づけが不正確 (同一 commit と循環の混同) | real | closed — 理由を「commit 前に bytes が確定しない」に改め、循環しないことを明記 |

fix 後に稿の数値表 66 行を抽出と再照合 (66/66 一致)。fix は親が docs 本文に直接施した散文の追加・置換で、数値の
変更は無い (所見 2 の実例の数値は §2.2 の表の値そのもの)。焦点再レビューの codex 再投は行わず、この表と再照合を
DW-O16 の closed 判定の根拠とする。

## 4b. 逐語の可逆最小正規化 (DW-S07)

codex の出力 2 本は markdown の行末 2 空白 (改行指示) を含み `git diff --check` に抵触したので、**行末の 2 空白だけを除去**した
(可視文字は不変)。復元は列挙した行の末尾へ 2 空白 (U+0020 ×2) を戻す。

| file | 原文 SHA-256 | 原文 bytes | 正規化後 bytes | 除去した行 (原文の行番号) |
|---|---|---|---|---|
| `verbatim/stage3-consult.md` | `bb8d0c97bb877221aaf8b95b4d5b61b6145a77f5d2913007a6de384780ec194e` | 9,654 | 9,628 | 5, 8, 11, 14, 17, 20, 23, 26, 29, 36, 66, 67, 68 (13 行 × 2 bytes) |
| `verbatim/stage6-review.md` | `a82fa55f45fa4c2eef31e20d549ebdb490a518c7a23990e5adc0195c9bc45c7b` | 6,587 | 6,579 | 15, 60, 61, 62 (4 行 × 2 bytes) |

## 5. 本 wave が閉じないもの・裁定へ返すもの

- **fig8 への再現欄の実装。** `tools/plotting/plot_b10_static_tail_formal.py` は cohort 1 の group id と 3 成果物の SHA-256 を
  定数で持つ。再現欄を描くには生成器・provenance・検査の改変 (実装面) が要り、Codex author の別 wave になる。
- **D2104 項 7 / D2120 項 16 の保留。** 両項は「走らせる場合は D2050 の地位明記を満たす別 wave として新規に起票する」と
  書き、本 wave はユーザー決定 (2026-09-19) に基づくその別 wave である。本 cohort 1 本についてのみ保留を解いたのであり、
  第 3 cohort 以後の扱いは定めない (追記の項 4)。
- **投入手順書 `docs/b10-backoff-static-tail-submission.md` §1 に hydrate 済み staging の前提が無い。** attempt 1 が
  1 投入 (3 ノード) を無駄にした実測欠陥。docs の是正候補として段 8 へ送る (本 wave では手順書を変えていない)。
- **cohort 1 の稿 §1.3 / 限定 5 の「izanagi 側の source commit は成果物に記録されていない」は不完全である。** 同 job root の
  `reservation.json` (`source_binding.repository_commit`) に `0600887d9…` が記録されている (本 wave の実測)。同稿は
  凍結物なので書き換えない。cohort 2 の稿では reservation.json を出所として明記した。
- **性能の認証、機序、901〜998 µs 帯 (D2044 項 14)、v2 consumer 移行 (D1936 項 36)。** いずれも対象外のまま。
