## 所見

| # | 判定 | 重要度 | 所見・根拠 |
|---|---|---|---|
| F1 | **real** | **must-fix** | B-10 v5 の report collector が、write-heavy / balanced だけ旧 v4 campaign を読みながら、期待する `prereg_commit`・spec・patch・formula を現在の v5 `prereg` から組み立てている。[b10_backoff_shape_sweep.py:2805](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:2805)、[同:2943](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:2943)、[同:3369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:3369)。これは「v4 の 135 cell を v5 へ再ラベルしない」という裁定と両立しない。[preregistration.md:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/docs/b10-backoff-shape-preregistration.md:13) |
|  |  |  | **放置時の成果物影響:** 実在する v4 行は binding/spec 不一致で拒否され、新規 v5 write-heavy / balanced campaign は collector が参照しないため、v5 の3 workload 材料レポート・certified 選択を構成できない。v5 は全 workload を v5 campaign として読むか、旧 adapter を完全な v4 binding に固定して v5 集約から隔離する必要がある。 |
| F2 | **real** | **must-fix** | F1 を覆う既存テストは、synthetic 行を同じ `_legacy_*_binding(prereg)` から作り、期待 digest も注入しているため恒真化している。[test_b10_backoff_shape_sweep.py:393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_b10_backoff_shape_sweep.py:393)、[同:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_b10_backoff_shape_sweep.py:423)、[同:1847](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_b10_backoff_shape_sweep.py:1847)。実在 v4 binding と v5 binding の混在を再現していない。 |
|  |  |  | **放置時の成果物影響:** F1 の誤った受理集合が検査を通り、旧行の拒否または再ラベルを検出できず、B-10 集約レポートの参照集合が誤る。 |
| F3 | **real** | **must-fix** | `test_static_codec_is_bijective_on_its_exact_bounded_domain` の全域検査は、同じ module の encoder と decoder を往復させるだけである。[test_backoff_extended_sweep.py:291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_backoff_extended_sweep.py:291)。境界 pin は有効だが、未 pin の点で encoder/decoder を同じように誤らせれば通る。`_normal_points` も同じ decoder から期待 binding を作る。[test_backoff_extended_sweep_report.py:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_backoff_extended_sweep_report.py:67) |
|  |  |  | **放置時の成果物影響:** 例えば未 pin の物理 560 µs が別 raw に写る共通誤実装では、C++ が別時間を待つ一方、certified 行・材料レポートは `fixed-560us` と記録し、値と選択を変える。既存テスト内で全域の独立式 `raw = µ` / `µ+2000` と C++/`exact_model` を結べばよい。 |
| F4 | **real** | **must-fix** | D1106 の test は seed と base flags は literal pin しているが、肝心の旧 raw grid は production の `M.EXPECTED_FIXED_GRID` を期待値にも使う。[test_backoff_requested_us.py:637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_backoff_requested_us.py:637)。production helper も同じ定数を読む。[backoff_requested_us.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_requested_us.py:96) |
|  |  |  | **放置時の成果物影響:** `EXPECTED_FIXED_GRID` と helper が同時にずれると、`load_reference_binding` が別の historic genome 集合を正本として受理し、D1106 の台帳参照集合が変わる。旧 grid 全体の独立 literal pin が必要。 |
| F5 | **real** | **must-fix** | M11 相当の「実際の prereg 文書と現物 patch/hash の突合」がテストにない。fixture spec は現物から hash を計算し、positive test も同じ値と比較する。[test_b10_backoff_shape_sweep.py:193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_b10_backoff_shape_sweep.py:193)、[同:796](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_b10_backoff_shape_sweep.py:796)。actual Markdown を読む P06 は artifact hash を検査していない。[同:1088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_b10_backoff_shape_sweep.py:1088)。また schema 負例は v3 のままで、直前版 v4 を拒否する検査になっていない。[同:1221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_b10_backoff_shape_sweep.py:1221) |
|  |  |  | **放置時の成果物影響:** stale hash は unit test を通った後、formal preflight の `patch-sha` / `formula-sha` で全 v5 run を拒否し、certified 受理集合と材料レポートを空にする。[b10_backoff_shape_sweep.py:1528](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/b10_backoff_shape_sweep.py:1528) |
| F6 | **real** | **must-fix** | 裁定で明記必須だった三点――`applied_tree_sha256` / `analysis_code_sha256` / `binding_sha256` の変化、非負値 meaning witness が production admission 未接続であること、右側打ち切りが 999→1000 に移るだけであること――が統合差分にも author 報告にもない。[adjudication.md:45](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-backoff-static-ceiling/adjudication.md:45)、[同:47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-backoff-static-ceiling/adjudication.md:47)、[同:50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-backoff-static-ceiling/adjudication.md:50)。さらに親担当とされた spool fragment も差分にない。[同:132](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-backoff-static-ceiling/adjudication.md:132) |
|  |  |  | **放置時の成果物影響:** 台帳・材料レポートから新 binding 参照と既知の admission/右打ち切り境界が欠落し、結果が「意味を production gate 済み」「飽和域まで測定済み」と誤読される。 |
| F7 | **real** | **nit** | 既知の赤の `is not` は正しい実装を落とす期待値不良。[test_backoff_extended_sweep.py:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_backoff_extended_sweep.py:352)。成果物値・受理集合・参照は変えないため、指定された尺度では nit。 |
| F8 | **real** | **nit** | v5 へ更新後も `test_p06_canonical_v4...`、`test_v4_spec...`、`...after_v4_positive_control` という名称が残る。[test_b10_backoff_shape_sweep.py:1088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_b10_backoff_shape_sweep.py:1088)。値への影響はないが、F5 の schema coverage 欠落を見えにくくしている。 |

## 既知の赤 1 件

保護しようとしていた性質は、T-2266 成果物が「要求した点」と「実際に測れた点」を別フィールドとして保持し、F718 のような未実現点を隠さないことです。Python tuple のオブジェクト同一性ではありません。

現在は両方の値列が同じ tuple literal になったため、CPython が定数を共有し、`is not` が偽になります。[backoff_extended_sweep.py:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep.py:85)。一方、実成果物では別々に `list(...)` を生成して別キーへ格納しており、フィールド分離は保たれています。[同:513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep.py:513)、[同:779](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/backoff_extended_sweep.py:779)。

したがって、誤りは実装ではなく `is not` という期待値です。弱めない修正は次です。

- requested / realized の exact literal 値を引き続き固定する。
- config と report document に両キーが存在することを固定する。
- そこで生成された二つの list が別インスタンスであり、片方を変更しても他方が変化しないことを検査する。

tuple 定数をわざと別オブジェクトに構築する修正は、成果物上意味のない CPython 実装詳細を固定するため不適切です。

## 申告と実物の照合

| author の受理・拒否行 | 実物判定 | 差分根拠 |
|---|---|---|
| 静的物理値 `0..999` → exact integer `0..9999` | **一致** | `STATIC_BACKOFF_MAX_US = 9999` と exact-type check。`backoff_extended_sweep.py:60-68` |
| encode: `0..999` 同値、`1000..9999` は `µ+2000` | **一致** | `backoff_extended_sweep.py:64-68` |
| static decode: raw `0..999`, `3000..11999` のみ受理 | **一致** | `backoff_extended_sweep.py:71-79` |
| `exact_model`: raw `0..11999`、負値/12000+/非整数を拒否 | **一致** | `b10_backoff_shape_sweep.py:722-734` |
| raw `0..999` 数値不変 | **一致** | C++ の code 0 枝は不変、Python は `Fraction(encoded)`。`b10_backoff_shape_sweep.py:730-734` |
| raw `1000..1999` symmetric-modulo 不変 | **一致** | C++ の code 1 枝に差分なし。独立閉形式検査は `test_b10_backoff_shape_sweep.py:2570-2580` |
| raw `2000..2999` binary 不変 | **一致** | C++ の code 2 枝に差分なし。独立閉形式検査は `test_b10_backoff_shape_sweep.py:2581-2587` |
| raw `3000..11999`: `%1000` → `raw-2000` | **一致** | `patches/silo-backoff-fixed.patch:70`、`b10_backoff_shape_sweep.py:733-734` |
| `BACKOFF_FIXED=-1` stock 枝不変 | **一致** | 変更は `#if >=0` 内の hole 1行のみ。stock は `patches/silo-backoff-fixed.patch:71-73` |

受理・拒否表そのものに虚偽はありません。

ただし author の最終文「Markdown/RST に触れていない」は、実装子単独の所有範囲としては `author.md:61-64` と整合しますが、統合 snapshot 全体の説明としては使えません。統合差分では preregistration、`patches/README.md`、`src/coder-spec.md` の3 Markdown が変更されています。

## 裁定 9 項目との照合

裁定の実装可能な指示を重複なく9群に整理した結果です。

| # | 必須面 | 判定 | 対応差分 |
|---|---|---|---|
| 1 | 有限 9999 µs の codec と定義域 | **充足** | `backoff_extended_sweep.py:60-79` |
| 2 | hole 最終項、逐語 pin、`exact_model` の一致 | **充足** | `silo-backoff-fixed.patch:70`、`b10_backoff_shape_sweep.py:263-264,722-734` |
| 3 | extended/T-2266 の raw 3000・物理1000分離と新 identity | **充足** | `backoff_extended_sweep.py:85-88,384-417,474-532,646-660` |
| 4 | normal report / overthrottle の物理 label・row・resume・schema | **充足** | `backoff_extended_sweep_report.py:257-290,462-504`、`backoff_overthrottle.py:50-51,81-95,316-339,475-531` |
| 5 | D1106 historic genome の現行 `genomes()` からの分離 | **実装は充足、検査は F4** | `backoff_requested_us.py:73-107,659-674` |
| 6 | B-10 v5、patch/formula hash、space/trial 次版 | **機械 spec は充足** | `preregistration.md:312-315`、`b10_backoff_shape_sweep.py:88-89,294` |
| 7 | raw 3000/3001/3999 の独立 oracle、F718 負例 | **指定3点は充足** | `test_b10_backoff_shape_sweep.py:2590-2597,2899-2904`、`test_condition_meaning_gate.py:302-310,414-428` |
| 8 | 新入力言語・cache/binding・meaning witness・右打ち切りの正直な記録 | **一部欠落: F6** | 入力言語と cache miss は `author.md:34,65`。残る3点と spool がない |
| 9 | 旧 v4 成果物を旧 binding に残し、禁止範囲へ触れない | **ファイル非改変は充足、consumer 境界は F1** | 旧 digest 定数は不変だが `b10_backoff_shape_sweep.py:2805-2814,3369-3388` が v4/v5 を混在 |

## 差分ハンク対応

統合 snapshot の SHA-256 は、worktree の staged diff と完全一致しました。17変更ファイルの全ハンクは次へ対応します。

| ファイル（ハンク数） | 裁定項目 |
|---|---|
| `docs/b10-backoff-shape-preregistration.md` (2) | #6、v4保存説明 |
| `orchestrator/campaign/b10_backoff_shape_sweep.py` (4) | #2、#6 |
| `orchestrator/campaign/backoff_extended_sweep.py` (8) | #1、#3 |
| `orchestrator/campaign/backoff_extended_sweep_report.py` (4) | #3、#4 |
| `orchestrator/campaign/backoff_overthrottle.py` (5) | #4 |
| `orchestrator/campaign/backoff_requested_us.py` (6) | #5 |
| condition-meaning fixture 2ファイル (各1) | #2、#7 |
| `test_b10_backoff_shape_sweep.py` (8) | #2、#6、#7。ただし F2/F5 |
| `test_backoff_extended_sweep.py` (7) | #1、#3、#7。ただし F3/F7 |
| `test_backoff_extended_sweep_report.py` (1) | #4。ただし F3 の自己参照 |
| `test_backoff_overthrottle.py` (2) | #4、#7 |
| `test_backoff_requested_us.py` (3) | #5、#7。ただし F4 |
| `test_condition_meaning_gate.py` (1) | #7 |
| `patches/README.md` (2) | #8 |
| `patches/silo-backoff-fixed.patch` (1) | #2 |
| `src/coder-spec.md` (1) | #8 |

裁定外の production 機構、1000 µs 超の測定格子、新 gate、cache admission preimage、T-2216、一般整数 gate への変更はありません。

## 正しさ境界

| 境界 | 判定 | 根拠 |
|---|---|---|
| stock 枝・marker・`#if/#else/#endif`・待機ループの byte 不変 | **refuted / nit**（違反なし） | patch の唯一の production hunkは hole line 1行。stock 行は `patches/silo-backoff-fixed.patch:71-73`、frame/wait-loop pin は `b10_backoff_shape_sweep.py:265-288` のまま |
| raw `0..2999` の C++ 数値 | **refuted / nit**（違反なし） | 変更されたのは q≥3 の最終項だけ。q=0/1/2 の式は逐語不変 |
| raw `0..2999` の Python 数値 | **refuted / nit**（違反なし） | `exact_model` は q≥3 だけ変更。`b10_backoff_shape_sweep.py:730-742` |
| verifier / certified / R1〜R5 / shape 閉集合 / μ 格子 | **refuted / nit**（違反なし） | `MEANS_US=(2,5,10,25,50,100)`、shape は2種のまま。`b10_backoff_shape_sweep.py:98-106`。prereg の既存規則本文・machine fields に該当差分なし |
| prereg v5 の規範フィールド変更 | **refuted / nit**（違反なし） | machine JSON は schema と patch/formula hash の3 scalar だけ変更。`preregistration.md:312-315`。追加された改訂履歴 prose は規範フィールドではない |
| 旧成果物の byte/digest 非改変 | **refuted / nit**（違反なし） | 旧 campaign/artifact/digest ファイルに差分なし。ただし消費時の v4/v5 分離は F1 で破れている |

確認した現物 hash は patch `a5e0710c…`、formula `1205b1ff…` で prereg の値と一致します。

## 恒真化と負例

独立 oracle として成立しているものは次です。

- raw 3000/3001/3999 の Python期待値は literal 1000/1001/1999。[test_b10_backoff_shape_sweep.py:2590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_b10_backoff_shape_sweep.py:2590)
- 同じ3点を実 C++ 式へ直接当てる期待値も literal。[同:2899](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/tests/test_b10_backoff_shape_sweep.py:2899)
- raw 3000 meaning test は `_case(3000, 1000)` の独立値を compiler 観測と比較する。
- F718 raw1000 負例は、観測 0 と期待1000の bit 不一致が [condition_meaning_gate.py:4291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-backoff-static-ceiling/orchestrator/campaign/condition_meaning_gate.py:4291) で `decoded-meaning-mismatch` になる。
- codec の invalid 値は外側範囲条件または static-domain hole で落ちる。`backoff_extended_sweep.py:66,73,79`
- D1106 の `without_1000` は `_grid_projection` の exact-grid 比較で落ちる。`backoff_requested_us.py:471-488`

恒真または不十分なのは F2〜F5 のテストと、正しいコードを落とす F7 です。

pytest は実行しておらず、緑とは判定していません。

## 総括

production codec・C++復号・物理 label の実装自体は裁定どおりで、stock、raw `0..2999`、R1〜R5、shape/μ格子も保持されています。

ただし受理可能状態ではありません。最大の must-fix は、B-10 v5 reporter が旧 v4 write-heavy/balanced campaign と現在の v5 binding を混在させ、新 v5 campaign も読めない F1 です。加えて、その不具合を隠す legacy fixture、codec/D1106/prereg の自己参照検査、裁定済み spool・境界説明の欠落を直す必要があります。既知の `is not` 赤は期待値側の誤りであり、成果物への影響がないため指定尺度では nit です。