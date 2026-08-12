# 段 6 — レビュー所見の裁定と変異再照準 ([T-968])

判定日時: 2026-08-13 03:25 JST / base commit `31b004b7` / 退避 snapshot: `snapshot-pre-fix.patch`

## 1. レビュー所見の裁定

| # | 出所 | 所見 | 判定 | 扱い |
|---|---|---|---|---|
| R1 | **A + B が独立に到達** | 証跡免除 session (pre-probe competing / measure 例外) の `exclusion_class` が意味検証されず、`competing_process` を `rep_integrity_failure` へ偽装できる。generic verifier の `_REQUIRED_SESSION` にも無い | **real / must-fix** | 採用。`exclusion_class` の期待値算出と一致検査を**免除分岐の外へ出し全 session で必須化**する。`_REQUIRED_SESSION` へ追加。competing / launch 各 1 件の改変負例を足す |
| R2 | A | 免除判定が自己申告 (`run_cmd=null` + reason) に依存しており、測定完了 session を「未測定の免除行」に偽装して捨てられる | **real / must-fix** | 採用。**裁定 §3 不変条件 4 が実装で満たされていない。** 免除は構造的事実だけで判定する: pre-probe competing は `probe_before.competing is True` かつ `probe_after is None`、measure 例外は測定段階を表す固定 enum と整合する場合のみ |
| R3 | A | `seq` / `reps_expected` / `exec_failures` / `retry` に `int()` / `bool()` 正規化が残り、`"5"` や `5.9` が丸められて通る | **real / must-fix** | 採用。`SessionRecord` 構築前に非負 exact int / exact bool を要求し、正規化を廃止する |
| R4 | A | `use_perf` call-site meta-test が別用途の keyword まで拾う | real / should-fix | 採用。keyword を削らず**対象関数を限定**する |
| R5 | A + B | M7 (precedence 順序変異) は成果物の値・受理集合・参照を変えない (F86 型) | **real** | 採用。**M7 を受理集合変異から外し、diagnostic sensitivity pin へ降格**する。kill には数えない |
| R6 | B | M1 は median 混入 assert へ到達する前に KeyError / 前段 assert で落ち、主張した帰属が成立しない | **real** | 採用。M1 を**出力 shape を保つ単一変異へ再照準** (下記 §2) |
| R7 | B | M2 は projection 単独では成立せず、後段の reps 本数 gate の変更が要る | **real** | 採用。M2 を再照準 (下記 §2) |
| R8 | B | M4 の anchor (`all` → `any`) が実在しない | **real** | 採用。M4 を**実在する単一条件へ再照準** (下記 §2) |
| R9 | B | M12 の `returncode=True` は fail-open を作らず診断文字列だけの赤 | **real** | 採用。fixture を `returncode=False` にして bool-as-zero の fail-open を直接作る |
| R10 | B | 期待 node 集合が parameter suffix を含んでおらず actual より小さい | **real** | 採用。**parameter suffix を含む完全 node 集合**を登録する |

**規律 2 について:** 両レビューとも「rep 完備判定へ throughput / median / CV の大小を混ぜる経路は
見つからなかった」と報告した。no-touch 列挙対象と `output/` は差分ゼロ、4 理由固定順・protocol
builder・formula / protocol / manifest schema も不変であることを両者が確認している。

## 2. 変異事前登録の再照準 (DW-M01 / F28)

**降格:** M7 は受理集合変異から外す (R5)。診断感度 pin として残すが kill には数えない。

**再定義:**

| ID | 変異位置 (再照準後) | 変異内容 | 期待 node (parameter suffix 込みの完全集合) |
|---|---|---|---|
| M1 | rep 資格付け述語 | **出力 shape を保ったまま**全 rep を資格ありにする (failure count を常に 0、全 tps を qualified へ) | positive control の `[nonzero_rc]` と `[missing_cycles]` |
| M2 | reps 本数 gate | qualified 本数が reps 未満でも median を許す (`assess_session` へ `reps=len(throughputs)` を渡す等) | positive control の `[nonzero_rc]` と `[missing_cycles]` |
| M4 | counter 完備条件 | `incomplete` を資格対象に含める | 専用 4 parametrized node + positive control `[missing_cycles]` |
| M12 | 型検査 | exact-int 検査を `isinstance` へ緩める。fixture は `returncode=False` (bool-as-zero) | 当該 parameter suffix 付き node |

M3 / M5 / M6 / M8 / M9 / M10 / M11 / M13 と positive 層 P1〜P5 は据え置く。
ただし**すべて parameter suffix 込みの完全 node 集合**で登録し直す (R10)。

## 3. 21 件の赤への裁定

- **resume / finalize 系 12 件:** v3 journal は移行処理へ入る前に**早期 return** し、
  測定済み v2 の拒否は維持する (レビュー A が指摘した順序の誤り)。
- **holdout v2 candidate 系 3 件:** 段 5 で親が裁定したとおり
  `s8b_holdout_freeze.py` の当該 1 行へ `expected_use_perf=True` を渡す。
  **既定値の追加で消してはならない** (両レビューが「A3 を再度開く」と警告)。
- **`test_production_use_perf_keyword_call_sites_are_a_closed_set`:** R4 のとおり対象関数を限定。
- **ratified_verify 3 件 / stats 1 件:** 実装側の誤りとして直す。期待値は変えない。
- `test_s8b_approved.py` の ImportError は **file 選択走固有の偽赤** (DW-O18)。修正対象外。

## 4. no-touch の更新

段 4 §2 の no-touch から **`s8b_holdout_freeze.py` の当該 1 行だけ**を外す (段 5 で裁定済み)。
根拠: 同 file の generator bytes 検査はユーザー裁定で保留中 (`s8b-holdout.generator-implementation-bytes`
が `HELD_CHECK_IDS` に在る) で、かつ現物は既に記録値から乖離済み
(実測 `2204ac5e…` ≠ 記録 `1910fff3…`)。触らないことで守れる pin は現存しない。
**それ以外の no-touch は不変。** 特に 4 理由固定順・`_APPROVED_REASONS`・`validate_protocol` の
pin・protocol builder・`FORMULA_ID` / `PROTOCOL_SCHEMA` / `MANIFEST_SCHEMA`・`output/` 配下。
