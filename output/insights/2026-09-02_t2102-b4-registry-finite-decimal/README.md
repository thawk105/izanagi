# [T-2102] B-4 registry の reference_tps 受理値域を有限十進有理数へ狭める (実装 wave)

- 日付: 2026-09-02
- branch: `worktree-dev-wave-t2102-b4-reference-tps-domain`
- 取り込んだ main の固定 SHA: `7233afa81`
- 前段の測定 wave: `output/insights/2026-09-02_t2102-b4-reference-tps-domain/`
- ユーザー裁定: 択 α を採る (worklog エントリ 1184)。**根拠は D1344 充足ではなく周辺実測に
  基づく上書き裁定**であり、D1424 決定 4 の拘束はすべて効く。

## 何をしたか

封印前 registry admission (`p3_b4_analysis_ledgers._validate_attempt`) に、
`reference_tps` が**有限十進有理数**であることの述語を 1 つ足した。述語は
「既約分母から 2 と 5 を除いた残りが 1」で、`p3_b4_raw_record_producer._fraction_token` の
有限十進判定と同じ手順を独立に書いたものである。

これにより、publication 段階で必ず落ちる非有限十進の比を封印段階で落とす。
受理集合を**縮めるだけ**の変更なので絶対規律 2 と整合する。

## 配置の択一 (D1424 決定 4 の R4) — 択 A

D1424 決定 4 は「registry の封印時のみ」と「registry と manifest の codec も含む」の
二択を示し、**前者と説明しながら後者を実装することを禁じた**。本 wave は前者 (択 A) を採る。

択 B を採らない理由は、`_ratio_payload` / `_ratio_from_payload` が registry と manifest の
**共用**であることにある。狭めると manifest 単独の reader/writer の wire 受理集合まで縮む。
事前登録 §5.1.1 の純関数契約は `reference_tps` を「有限の正の exact rational」としており、
`1/3` はその条件を満たす。manifest transport がそれを運べなくなると、§5.1.1 が述べる
入力値域と transport の能力がずれる。段 2 と段 3 luna が独立に同じ切り分けを支持した。

### 択 A の実効範囲を過小に書かない

D1424 の禁止の対称として、択 A が実際に何を狭めるかも正直に書く。
`_validate_attempt` は 3 箇所から呼ばれる (`_attempt_payload`、`_attempt_from_payload`、
`_normalize_attempts`)。したがって次のすべてが狭まる。

- `scheduled_attempts_sha256` (in-memory batch の hash)
- `seal_scheduled_attempt_registry` (封印)
- `load_scheduled_attempt_registry` (外部 registry JSONL の読取)
- `assert_analysis_manifest_complete` / `generate_analysis_manifest` (先頭で registry を再構成)
- 段 6 レビュー luna が追加で指摘した `append_registry_violation`、
  `derive_registry_violation_count`、`build_contract_binding` (いずれも registry 再構成を通る)

**意図的に狭めない面**は `load_analysis_manifest` 単独と
`assert_manifest_unchanged_before_run` である。`[1,3]` を含む単独 manifest は択 A 後も読める。
完全な registry/manifest 組は registry を先に読むため成立しない。この残置は裁定どおりであり、
段 6 レビュー luna が実測で「manifest 単独の `[1,3]` 受理は維持されている」ことを確認した。

## M12 の再定義 (D1424 決定 4 の must-fix R5)

D1424 は「既存の変異検査 M12 を registry 拒否期待へ単純に移設してはならない」と縛った。
**この必要性を実コードで確認した。**

- 現行 M12 (`test_m12_nonterminating_reference_ratio_has_only_named_rejection`) は
  `_publication(..., reference_override=(1, 3))` で publication を作り、
  `publish_b4_attempt_result` が `DECIMAL_NOT_TERMINATING` を返すことを期待していた。
- その `_publication` は `issue_b4_prerun_publication` を呼び、そこから
  `scheduled_attempts_sha256` → `_normalize_attempts` → `_validate_attempt` に到達する。
- したがって新検査後、`(1, 3)` は **publication が作られる前** (封印より前の scheduled hash) で
  落ちる。producer の十進 token 化には到達しない。registry 拒否期待へ移すと
  `_fraction_token` の丸め禁止分岐が一切検査されなくなり、恒真な保証になる。

再定義は node 名を変えず、本体を二段にした。

1. 実物の `_fraction_token((1, 3))` が
   `ArithmeticError("reference_tps has no finite decimal expansion")` を送出することの直接検査。
2. 有限十進だけの正常な publication と有効な evidence を用意し、`_fraction_token` を
   `ArithmeticError` を送出するものへ差し替えて `publish_b4_attempt_result` を呼び、
   production の catch が artifact `"publication"` / field `"reference_tps"` /
   code `DECIMAL_NOT_TERMINATING` / detail `"reference_tps has no finite decimal JSON
   representation"` を生成することを**全項目**で固定する。

### 差し替え (monkeypatch) を最後の手段と判断した根拠 (DW-O14)

`_derive_b4_attempt_data` は module 直下の `_fraction_token` を直接呼んでおり、
正規の注入 seam が無い。差し替えずに実物へ非有限十進を届ける経路も閉じている。
`publish_b4_attempt_result` は `_validated_publication` で publication を**disk から再読込して
bytes 一致を要求**し、publication loader は manifest を registry から再生成して比較する。
したがって manifest row だけに `(1,3)` を仕込む構成は `ARTIFACT_MISMATCH` で落ち、
`_fraction_token` に届かない。

### 段 6 が見つけた穴 (must-fix、fix 済み)

敵対レビュー sol が、第 2 段が**差し替えたものが実際に呼ばれたことを固定していない**ことを
指摘した。production 側の `_fraction_token(row.reference_tps)` という呼出しそのものを
例外送出へ置き換える変異が素通りする。加えて再定義前にあった正例対照
(差し替えが無ければ publication が正常に書き込まれる) が失われていた。

fix で、独立 root への正常 publication と `_assert_write` による正例対照を戻し、
差し替えを名前で受けて `assert_called_once_with(publication.manifest.rows[0].reference_tps)`
を足した。実体を名指しし、依存先を stub していない。

## 述語の射程 — 完全一致とは主張しない

段 3 sol が real 所見を出した。`_fraction_token` は token 化の最終段で `str(abs(scaled))` を
呼ぶため、Python の int から str への桁数上限に掛かる。`(1, 2**6200)` のような
**巨大な有限十進**は新述語を通って registry を封印できる一方、producer では `ValueError` になり、
`DECIMAL_NOT_TERMINATING` ではなく `EVIDENCE_SCHEMA` に写る。

**本 wave ではこの残差を埋めない。** 理由は 3 つある。

1. D1424 決定 4 は述語を「既約分母から 2 と 5 を除いた残りが 1」と**名指しで**指定している。
   桁数上限を足すのは、裁定が名指ししていない第 2 の述語の追加になる。
2. 該当する値を生む producer は存在しない。`reference_tps` は certified snapshot の
   session-level throughput 比であり、記録された値域にも該当値は無い。
   要求外の仮想リスクであり、`DW-G05` の成果物影響を 1 行で示せない。
3. ユーザーが「仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」と明示した。

したがって本 wave が主張するのは「述語は `_fraction_token` の**有限十進性の判定と**一致する」
までであり、「操作上の受理集合と完全に一致する」ではない。

## 段 6 レビューが refuted にしたもの

- M12 再定義が恒真化する — 実物の `_fraction_token` 分岐を名指しで刺しており、分岐削除で落ちる。
- repo 内の既存正例が新検査で落ちる — registry を通る値の既約分母は 1 と 10 だけで、
  `None` は guard で除外される。落ちる正例は 0 件。
- `(1,30)` が既存の `wire reference_tps is not reduced` で落ちる — `[1,30]` は既約かつ
  canonical なので通過し、新検査だけが発火する。
- 新検査または既存検査が恒真化した — `(1,3)`・`0`・wire `[2,6]` がそれぞれ新検査・既存 invalid・
  既存 not-reduced へ別々に到達する。
- 裁定 scope を超えて contract / adapter / manifest codec を狭めた — production 差分は
  `_validate_attempt` の 8 行だけ。
- `bool` による registry / producer の不一致 — 両側とも exact-type 検査で拒否する。

## DW-O09 pin 閉包

`p3_b4_analysis_ledgers.py` は B-4 の source closure member
(`p3_b4_analysis_path.py`、`p3_b4_analysis_prereg_consumer.py`) なので、
member digest と closure receipt digest は**動く**。段 3 luna が変更前の現行 2 値
(`7476c812...c152`、`57e84eeb...384c`) を repository 全域で検索し、literal hit **0 件**を確認した。
段 6 luna が変更後の値でも同じ結論を出した。repin 対象は無い。
`preregistration_section_sha256` / `semantic_section_sha256` は文書 bytes だけを pin するので
動かない。凍結成果物の bytes を変える producer は無く、`DW-O10` は成立しない。

## 変異台帳

spec と結果は同ディレクトリの
`mutation-spec-probe.json` / `mutation-probe-result.json` /
`mutation-spec-final.json` / `mutation-final-result.json` が正本。

本走の結果は **baseline PASSED、KILLED 6、SURVIVED 0、MISMATCH 0**。

| ID | 変異 | 期待赤 |
|---|---|---|
| MUT-T2102-01 | registry の新述語を恒真化 | `(1,3)` と `(1,30)` の負例 2 件 |
| MUT-T2102-02 | `reference is not None` guard を削除 | `None` 正例 1 件 |
| MUT-T2102-03 | 分母から 2 を除くループを削除 | `(1,10)` 正例と M12 |
| MUT-T2102-04 | 分母から 5 を除くループを削除 | `(1,10)` 正例と M12 |
| MUT-T2102-05 | producer `_fraction_token` の `ArithmeticError` 分岐を削除 | M12 |
| MUT-T2102-06 | producer の例外から `DECIMAL_NOT_TERMINATING` への写像を削除 | M12 |

### erratum — probe が期待 node を 2 件訂正した

段 4 で事前登録したとき、親は MUT-03 と MUT-04 の期待赤を「`(1,10)` の正例 1 件だけ」と
**解析で**導いた。probe 走 (全件 SURVIVED 期待で観測 node を集める形) の実測では、
両者とも M12 も赤になった。M12 の fixture が作る publication の `reference_tps` は
`(100_001 + 10*index, 10)` で既約分母が 10 であり、2 か 5 の除去を消すと registry admission が
それらも落とすためである。**解析だけでは取り逃していた依存であり、probe を挟んだことで
捕まった。** 本走の spec は probe の観測 node から機械的に再構成した。

### 事前登録から外した変異 1 件

段 4 では 7 件を事前登録したが、そのうち「述語を恒偽化する (常に拒否)」変異は、実装後に
**過剰決定**であることが分かった。恒偽化すると `reference_tps` を持つ registry test が
ほぼ全件赤になり、単独変異の証拠にならない。`DW-M03` が定める扱い
(冗長 gate と明記して単独変異の証拠から外す) に従って spec から外した。
同じ保証 (正例が生きていること) は、単一理由の MUT-03 と MUT-04 が担う。

## 親 brief の訂正

段 3・段 6 が親の段 1 brief と段 4 裁定の誤りを 7 件指摘し、すべて採用した。

| # | 誤り | 訂正 |
|---|---|---|
| C1 | `seal_scheduled_attempt_registry` の行番号 | `_normalize_attempts` 内の `_validate_attempt` 呼出しと取り違えていた |
| C2 | 「201 試行を実走した後に `EVIDENCE_SCHEMA` で失う」 | 非有限十進は `DECIMAL_NOT_TERMINATING` に写る。`EVIDENCE_SCHEMA` は `ValueError` 側。「必ず 201 件実走後」も推論で、publisher は attempt 単位 API である |
| C3 | 「新検査は production の既存 artifact では発火しない」 | production の封印済み registry は 0 件なので、この主張は registry については恒真。正しくは「非有限十進を生む producer が不在で、記録された throughput 値域にも該当値が無い」 |
| C4 | 「共有 helper へ切り出すと `as_b4_exact_fraction` 側と結合しうる」 | 配置次第であり必然ではない。独立実装の実際の根拠は、producer 側防壁との故障独立性、producer を source closure の外に保つこと、変更 scope を増やさないこと |
| C5 | 「択 A は封印時だけを狭める」 | hash・外部 registry load・完全性検査・manifest 生成にも効く |
| C6 | 択 A の実効範囲の列挙が非網羅 | `append_registry_violation` / `derive_registry_violation_count` / `build_contract_binding` も registry 再構成を通る |
| C7 | fixture の既約分母を `{1,2,10}` と記録 | 現物は `{1,10}` |

## 検査

- 焦点走 (対象 2 file): 64 passed。
- 焦点走 (`DW-O26` の参照関係で引いた consumer test 4 file: analysis_path / prereg_consumer /
  material_report / prerun_issuer): 121 passed。
- fix 後の焦点走 (対象 2 file): 64 passed。
- 変異本走: baseline PASSED、KILLED 6、SURVIVED 0、MISMATCH 0。
- `python3 tools/check_ai_provenance.py`: 実装 commit 後に full 監査 rc=0 (7806 件、新規違反なし)。
- `python3 tools/check_docs.py`: rc=0 (違反なし)。
- `python3 tools/spool_fold.py --dry-run`: rc=0 (`status=planned`)。
- `git diff --cached --check`: rc=0。逐語 5 file の行末空白は `verbatim/ERRATUM.md` に
  原文 hash と byte 数を記録したうえで可逆最小正規化した (可視文字は不変)。
- **三軸語走査:** 権威実装は `orchestrator/campaign/s8b_holdout_freeze.search_repository`。
  これを repository 全域へ当てる `test_s8b_repo_scan_invariant.py` は growth hold
  (`release_condition: explicit-user-command-only`、2026-08-12 rulings 第 3 束) の下にあり、
  既定では skip される。**hold は迂回していない。** 代わりに同じ権威実装の `files` 注入 API で、
  本 wave が変更した 17 file に positive control が発火する既存 169 file を足した 186 file を
  走査した。結果は rr80 / rr20 とも conjunction hit **0 件**、positive control **14 hit** で、
  走査の感度が発火していることも同時に確かめた。
- 受入全走の結果はこの節へ実測後に追記する。

## 逐語

子の出力は `verbatim/` に置く。

- `verbatim/s2-plan.md` — 段 2 プラン起草
- `verbatim/s3-sol.md` — 段 3 敵対相談 (正しさ防壁の恒真化レンズ)
- `verbatim/s3-luna.md` — 段 3 敵対相談 (配置の択一と波及レンズ)
- `verbatim/s4-ruling.md` — 段 4 親裁定
- `verbatim/s5-author.md` — 段 5 実装子
- `verbatim/s6-review-sol.md` — 段 6 敵対レビュー (実効性レンズ)
- `verbatim/s6-review-luna.md` — 段 6 敵対レビュー (波及レンズ)
- `verbatim/s6-fix1.md` — 段 6 fix 子
