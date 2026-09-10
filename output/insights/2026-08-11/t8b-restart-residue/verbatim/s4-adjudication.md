# 段 4 裁定 — dev-wave 8b 再開の残余

親が段 3 の全所見を real / refuted、採用 / 不採用、scope 内 / 外に裁定する。
`DW-S04` に従い、scope 外の real 所見は実装せず裁定パッケージでユーザーへ返す。

## 裁定の骨子

**scope A (toolchain 束縛 = [T-747] (B) + [T-783]) は実装しない。**
`DW-S04` に従い親は不採用にせず、**新事実つきでユーザー再裁定へ戻す**。
B (分類訂正) と C (手順書更新) は実装する。よって本 wave は **docs-only**、遷移は `4→7→8→9`。

## 決め手 — A-1 単独は fail-closed 障壁を緩めるだけである

段 4 で気づいた非対称性であり、段 3 の 2 レンズも段 2 のプランも指摘していない。

- **現状**: 床値 build は `buildcache.DEFAULT_CC/CXX` = `gcc-13`/`g++-13` を固定要求する。
  Pegasus には無いので `_tool_version` が `toolchain cxx が PATH に存在しない: 'g++-13'
  (fails-closed)` で倒れる。**これは事故ではなく、現に効いている障壁である。**
- **A-1 を入れると**: `compilers_for_current_site()` が Pegasus compute で `("gcc","g++")` を返し、
  実測 11.4.0 で **build が通るようになる**。
- **A-2 (束縛検査) が無ければ**、A-1 は「認可されていない compiler で床値を測れるようにする」
  変更でしかない。手順書 §1.2 が「既定 compiler へ黙って倒すのは選択肢にしない」と
  명記した当のものになる。

したがって **A-1 と A-2 は不可分**であり、A-2 を完全形で出せない本 wave では
**A-1 も出せない**。[T-783] の起票文自身が「[T-747] の択が (B) に決まった場合の実装単位」と
条件付けており、単独実装を意図していない。

## A-2 を完全形で出せない理由 (blocker 4 件、いずれも裁定時点で未見)

| # | レンズ | 所見 | 判定 |
|---|---|---|---|
| B-1 | B | 裁定文が指定する三者照合のうち **attempt 実測値の脚が配線されていない**。`tools/pegasus/floor_campaign.sh:769-778` が `$ATTEMPT_DIR/{compiler,cxx,cmake}.{path,version}` へ書くが、driver へ渡らず `job-result.json` (`:970-1005`) にも入らない | **real・採用・scope 外** |
| A-1 | A | 現行 calibration に **cmake の path と cxx の version が無い**。`cmake.realpath` 非束縛のため PATH 先頭の cmake wrapper が通り、`cxx.version_first_line` 非束縛のため同 path の別版 g++ が通る。閉じるには executable SHA-256 を持つ新 calibration 世代が要り、**事前登録に触る** | **real・採用・scope 外** |
| A-2 | A | floor 限定の gate では、同じ contract を使う `pipeline` / `loop` / `oracle` / `screening` / silo ladder が無防備のまま。レンズ A は「裁定なしの floor-only 実装は不可」と判定 | **real・採用・scope 外** |
| B-2 | B | gate に**本番の発火経路が無い** (`DW-G04`)。official は W-1 が拒否、投入 script は official 固定、pilot 投入経路なし。発火条件を満たす既存 artifact path も計測 ID も書けない | **real・採用。`DW-G04` により設計メモへ** |

`DW-G04` は「発火条件を満たす既存 artifact path か計測 ID を brief に書ける場合だけ実装する。
書けなければ設計メモに留める」と定める。B-2 はこの条項に正面から当たる。

## 親の実測による追加の real 所見 (レンズより先に親が測った)

- **P1 / プランの「version 先頭行の逐語一致」は Pegasus で恒常赤になる。**
  calibration の `compiler_version` 先頭行 = `gcc (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0`、
  `buildcache._tool_version('gcc','cc')` の実測 `version_first_line` =
  `x86_64-linux-gnu-gcc-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0`。
  gcc は argv0 を先頭 token に出すため同一 compiler でも一致しない。
  `silo_ladder_rung1.tool_version_body()` が argv0 token を捨てているのはこのためである。
  **realpath 同士は完全一致する** (`/usr/bin/x86_64-linux-gnu-gcc-11` /
  `/usr/bin/x86_64-linux-gnu-g++-11` = build_argv の値)。
- **shell の attempt 記録は calibration と同形式である。** shell は `command -v gcc` を叩くので
  `gcc (…)` 形になり、`build_v2` だけが argv0 の違う形になる。三者照合を実装するなら
  正規化は `build_v2` の脚にだけ要る。

## 親 brief の訂正 (レンズが正した親の主張)

- **M-6 は refuted。** 同型の束縛は `silo_ladder_rung1.py:3554-3588` に**既に実装済み**
  (build_argv からの compiler 抽出、`toolchain.compiler_path` との交差検証、
  `tool_version_body()` による version 比較)。正しい主張は
  「**floor / `build_v2` 経路に consumer が無い**」という狭い形だけである。
- **M-1 の言い方を訂正 (レンズ A 所見 7)。** 「投入できない」は逐語には誤り。
  `submit_floor.sh` に mode の分岐は無く `qsub` は実行される。正しくは
  「**enqueue はできるが、official run は計算ノードで rc=2 になり、
  再凍結適格な artifact を完遂できない**」。キュー資源は消費されうる。
- **M-4 の言い方を訂正 (レンズ A 所見 8)。** 「driver source の pin が無い」は広すぎる。
  直接の frozen / 事前登録 pin は無いが、`submit_floor.sh` の submission receipt が
  `source_commit` を pin し、`floor_campaign.sh:524` と `certified_writer_preflight.py:85` が
  実行時に imported module bytes を照合する。**submission→execution の commit pin は在る。**
- **M-3 の一般化を撤回 (レンズ B 所見 6)。** 「計算ノードの既定は 11.4.0」は
  登録済み g1/g2 の 2 標本の観測であって `gen_S` 全ノードの現在値ではない。
  手順書 C-1 は「**登録済み g1/g2 calibration は 11.4.0 を記録している**」へ限定する。

## 採用しない所見 (scope 内で閉じないが blocker でもない)

- **A-3 (build 副作用)**: 拒否が build 後なので認可外の cache entry が残る。**real**。
  実装するなら `_toolchain_manifest()` 直後・cache 作成前へ置く。A を実装しない以上 moot。
  **裁定パッケージへ設計制約として同送する。**
- **A-4 (世代誤配線)**: authority に `contract_sha256` / calibration path・SHA / generation を
  含めるべき。**real**。同上、設計制約として同送。
- **A-5 / B-5 (proof chain へ残らない)**: 照合結果が portable artifact に残らず
  ratified verifier が再検算できない。**real**。同上。
- **A-6 / B-8 (silo ladder との二重実装)**: **real**。`DW-G03` の「独立 2 例」に相当するが、
  silo ladder は所有外である。共通 helper 化は裁定パッケージの択一に含める。
- **B-3 (package.md の superseded 表示)**: **real・採用・本 wave で実施**。
  実装子が旧裁定 (a) を読んで誤実装する導線であり、docs で閉じられる。
- **B-4 (pilot の意味の二義性)**: **real**。floor pilot と full-pipeline pilot が別物である点は
  裁定パッケージへ。(P3) の可否はこの二義性の解消後でないと決まらない。
- **B-6 (runbook の過度な一般化)**: **real・採用・本 wave で実施** (上記 M-3 の訂正)。
- **A-7 / B-7 (build 中の compiler 差し替え窓)**: **real だが should**。A を実装しないので moot。

## (P1)〜(P4) の最終判定

- **(P1) refuted** — version は逐語一致では成立しない (親実測)。`tool_version_body()` 同型の
  argv0 除去が必須。cmake は path 非束縛のままでは wrapper を止められない (A-1)。
- **(P2) real** — build_argv 第一 + `compiler_path` との交差検証は妥当。ただし
  attempt 実測値の脚が加わる (B-1)。
- **(P3) 判定保留** — pilot の二義性 (B-4) が解けるまで決まらない。
- **(P4) refuted** — `BuildResult` に toolchain manifest が無いため `buildcache` 無変更は不可能
  (段 2 プランが file:line で反証)。

## 変異事前登録 (`DW-M01`)

**実装差分ゼロの「実装しない」裁定であり、`DW-S04` により変異 matrix は免除。**
B / C は docs のみで受理集合を変えない。**受入全走は免除しない** — 段 7 の記録前に走らせ、
結果を worklog へ書く。実 repo を読むテストの有無は証拠つきで判定する。

## 本 wave が実装するもの (docs のみ)

1. **B**: `orchestrator/tests/README.md` へ「条件付き未実走」節を新設し、
   `output/insights/2026-08-11_known-red-exceptions/README.md` の分類語を訂正 + erratum。
2. **B-3**: `output/insights/2026-08-11_t8b-restart-integration/package.md` の R-4 節へ
   「(a) は superseded、正本は [T-747] (B)」の追記。
3. **C**: `docs/phase3-8b-restart-runbook.md` の §1.2 / §3 W-1 / §3 W-2 / §5 を実測値で更新。
   M-3 は限定表現、M-1 は「enqueue 可・official run は rc=2」へ。
4. **裁定パッケージ**: `output/insights/2026-08-11_t8b-restart-residue/package.md`。
