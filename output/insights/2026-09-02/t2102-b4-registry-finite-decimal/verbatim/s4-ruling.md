# 段 4 裁定 — [T-2102] registry の reference_tps 受理値域を有限十進有理数へ狭める

## 1. 配置の択一 (R4) — 択 A 確定

**`p3_b4_analysis_ledgers._validate_attempt` だけに述語を置く。** 段 2 と段 3 の両レーンが
独立に択 A を支持し、択 B を支持する材料は出なかった。

択 B を採らない理由は、`_ratio_payload` / `_ratio_from_payload` が registry と manifest の
**共用**であり、狭めると manifest-only の reader/writer の wire 受理集合まで縮むためである。
事前登録 §5.1.1 の純関数契約は `reference_tps` を「有限の正の exact rational」としており、
`1/3` はその条件を満たす。manifest transport がそれを運べなくなると、§5.1.1 が述べる入力値域と
transport の能力がずれる。D1424 決定 4 の「§5.1.1 の意味を変えない」に触れる。

### 択 A の実効範囲を正直に書く (luna R2 採用)

D1424 決定 4 は「registry の封印時のみ」と説明しながら 4 境界を実装することを禁じている。
本 wave はその対称として、**択 A が実際に何を狭めるかを過小に書かない。**
`_validate_attempt` は 3 箇所から呼ばれる (`:363` `_attempt_payload`、`:436`
`_attempt_from_payload`、`:446` `_normalize_attempts`)。したがって次のすべてが狭まる。

- `scheduled_attempts_sha256` (in-memory batch の hash)
- `seal_scheduled_attempt_registry` (封印)
- `load_scheduled_attempt_registry` (外部 registry JSONL の読取)
- `assert_analysis_manifest_complete` / `generate_analysis_manifest` (先頭で registry を再構成)

**意図的に狭めない面**を明記する。`load_analysis_manifest` 単独と
`assert_manifest_unchanged_before_run` (`:1262-1283`) は manifest だけを読むため、
`[1,3]` を含む単独 manifest は択 A 後も読める。これは残す。完全な registry/manifest 組は
registry を先に読むため成立しない (`p3_b4_analysis_path.py:199-240`、
`p3_b4_prerun_issuer.py:1046-1055,1138-1150`)。

## 2. must-fix

### M-1 (real、luna R1) — `reference_tps=None` を保存する

`reference_tps` は schema 上 optional で、非 `SCHEDULED` row では `None` が現行の**正当な値**である
(`p3_b4_analysis_ledgers.py:139`、`:279-281`、`:341-343`)。段 2 plan は
「`reference.denominator` から 2 と 5 を割り切る」とだけ書いており、`reference` が `None` の場合を
固定していない。そのまま書くと `None` の row を落とす。

**述語は `reference is not None` のときだけ評価する。** `None` を事前登録の正例に含める。
これは D1424 が求める「受理集合を縮めるだけ」に対する、承認外の過剰拒否の正例である
(`DW-M01`)。

### M-2 (real、R5 の実装) — M12 を producer 側の直接検査へ再定義する

ユーザーが名指しした確認点である。**親が実コードで確認し、両レーンが独立に追認した。**

現行 M12 は `_publication(..., reference_override=(1,3))` を作り `publish_b4_attempt_result` の
`DECIMAL_NOT_TERMINATING` を期待する。その `_publication` は
`issue_b4_prerun_publication` → `scheduled_attempts_sha256` → `_normalize_attempts` →
`_validate_attempt` に到達する。**新検査後、`(1,3)` は publication が作られる前 (seal より前の
scheduled hash) で落ちる。** producer の十進 token 化には到達しない。

再定義は node 名 `test_m12_nonterminating_reference_ratio_has_only_named_rejection` を維持し、
本体を次の二段にする。

1. 実物の `_fraction_token((1,3))` が `ArithmeticError("reference_tps has no finite decimal
   expansion")` を送出することを直接検査する。分母判定を消す変異はここで死ぬ
   (消すと `1 // 3 == 0` で整数 `0` が返り、例外期待が落ちる)。
2. 有限十進だけの正常な publication と evidence を作り、`_fraction_token` を
   `ArithmeticError` を送出するものへ差し替えて `publish_b4_attempt_result` を呼ぶ。
   production の catch が artifact `"publication"`、field `"reference_tps"`、
   code `DECIMAL_NOT_TERMINATING`、detail `"reference_tps has no finite decimal JSON
   representation"` を生成することを全項目で固定する。例外から拒否 code への写像を消す変異は
   ここで死ぬ。差し替えが効くこと自体が、`publish` が実際に `_fraction_token` を呼ぶ証拠になる。

**registry 拒否期待への移設は禁止である。**

#### 差し替え (monkeypatch) を使う根拠 — DW-O14

`_derive_b4_attempt_data` は module 直下の `_fraction_token` を直接呼んでおり、
**正規の注入 seam は無い** (`p3_b4_raw_record_producer.py:1541`)。
差し替えずに実物の `_fraction_token` へ非有限十進を届ける経路も閉じている。
`publish_b4_attempt_result` は `_validated_publication` で publication を**disk から再読込して
bytes 一致を要求**し (`:561-585`)、publication loader は manifest を registry から再生成して
比較する (`p3_b4_prerun_issuer.py:1138-1150`)。したがって manifest row だけに `(1,3)` を
仕込む構成は `ARTIFACT_MISMATCH` で落ち、`_fraction_token` に届かない。
**差し替えは最後の手段として正当である。** 実物の述語は第 1 段が名指しで検査するので、
両層 stub で緑になる形にはならない。

## 3. real だが scope 外

### sol R1 — 巨大な有限十進 `(1, 2**6200)` の操作上の不一致

`_fraction_token` は token 化の最終段で `str(abs(scaled))` を呼ぶため、Python の int→str
桁数上限に掛かって `ValueError` を送出し、publication では `DECIMAL_NOT_TERMINATING` ではなく
`EVIDENCE_SCHEMA` に写る (`p3_b4_raw_record_producer.py:366`、`:1542-1551`)。
一方この値は分母が 2 の冪なので新述語を通り、registry を封印できる。

**本 wave では埋めない。** 理由は 3 つある。

1. D1424 決定 4 は述語を「既約分母から 2 と 5 を除いた残りが 1」と**名指しで**指定している。
   桁数上限を足すのは、裁定が名指ししていない第 2 の述語の追加である。
2. 該当する値を生む producer は存在しない。`reference_tps` は certified snapshot の
   session-level throughput 比であり、記録された値域 (443,911 観測) にも該当値は無い。
   これは要求外の仮想リスクであり、`DW-G05` の「成果物の値・受理集合・参照がどう変わるか」を
   1 行で示せない。
3. ユーザーは「仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」と明示した。

**ただし主張の射程は正直に書く。** 記録には「述語は `_fraction_token` の**有限十進性の判定と**
一致する」と書き、「受理集合と完全に一致する」とは書かない。残差
(有限十進でも桁数上限を超える値は registry を通り publication で `EVIDENCE_SCHEMA` として
落ちる) を insight に明記する。

### sol R2 — final assembly 側の `DECIMAL_NOT_TERMINATING` は未検査のまま

`assemble_b4_raw_analysis` 側の catch (`:1967-1974`) には、再定義後の M12 も到達しない。
ただし**現行 M12 も到達していない**ので回帰ではない。決定的な `_fraction_token` に対して、
同じ値の 1 回目が成功して 2 回目だけ失敗することは自然入力では起こらないため、
この catch は自然入力では到達不能である。成果物影響を 1 行で示せないので `DW-G05` により
nit/backlog とし、追加 review も起動しない。insight に所見として残す。

## 4. 親 brief の訂正 (採用)

| # | 誤り | 訂正 |
|---|---|---|
| C1 | 「`seal_scheduled_attempt_registry` は ledgers `:446`」 | `:662`。`:446` は `_normalize_attempts` 内の `_validate_attempt` 呼出し (sol R5) |
| C2 | 「201 試行を実走した後に `EVIDENCE_SCHEMA` で失う」 | 非有限十進は `DECIMAL_NOT_TERMINATING` に写る。`EVIDENCE_SCHEMA` は `ValueError` 側。また「必ず 201 件実走後」は推論であり、publisher は attempt 単位 API である (luna R3、sol) |
| C3 | 「新検査は production の既存 artifact では発火しない」 | production の封印済み registry は 0 件なので、この主張は registry については恒真である。正しくは「非有限十進を生む producer が不在で、記録された throughput 値域にも該当値が無い」(sol R3、luna) |
| C4 | 「共有 helper へ切り出すと `as_b4_exact_fraction` 側と結合しうる」 | refuted。配置次第であり必然ではない。独立実装を選ぶ実際の根拠は、producer 側防壁との故障独立性、producer を source closure の外に保つこと、変更 scope を増やさないこと (luna F4) |
| C5 | 「択 A は封印時だけを狭める」 | hash・外部 registry load・completeness・manifest generation にも効く。§1 の実効範囲表が正本 (luna R2) |

## 5. refuted (不採用)

- M12 の再定義が恒真化する (sol F1) — 実物の `_fraction_token` 分岐を名指しで刺している。
- tracked の既存正例が新検査で落ちる (sol F2) — registry を通る値の既約分母は 1、2、10 だけ。
- `(1,30)` が既存の `wire reference_tps is not reduced` で落ちる (sol F3) — `[1,30]` は既約かつ
  canonical なので通過し、新検査だけが発火する。
- `bool` による registry / producer の不一致 (sol F5) — 両側とも exact-type 検査で拒否する。
- 択 A で完全 artifact が manifest codec を迂回して受理される (luna F1) — registry-first load と
  exact regeneration で閉じている。
- §5.1.1 の判定順序・literal・section digest が動く (luna F2) — 文書 bytes を変えない。
- closure digest を literal pin する live consumer がある (luna F3) — 現行 2 hash
  (`7476c812...c152`、`57e84eeb...384c`) の全域検索がともに 0 件。

## 6. DW-O09 / DW-O10 の確定

`p3_b4_analysis_ledgers.py` の member digest と closure receipt digest は**動く**。
literal pin する consumer は repository 内に 0 件で、repin 対象は無い。
`preregistration_section_sha256` / `semantic_section_sha256` は文書 bytes だけを pin するので
動かない。凍結成果物の bytes を変える producer は無いので `DW-O10` は成立しない。

## 7. 変異事前登録 (DW-M01)

実装前に登録する。各変異は位置に加え、同じ入力を拒否する層が前後に無く、無効化時の赤理由が
一つに絞れることを確認済みである。受理集合を縮める wave なので、承認外の過剰拒否の正例
(M-mut-02、M-mut-05) を含める。

| ID | 変異 | 期待赤 | 単一理由性の根拠 |
|---|---|---|---|
| M-mut-01 | registry の新述語を恒真化 (常に受理) | 負例 `(1,3)` の `scheduled_attempts_sha256` が例外を出さず赤 | registry admission に `(1,3)` を拒否する層は前後に無い |
| M-mut-02 | registry の新述語を恒偽化 (常に拒否) | 正例 `(1,10)` の seal が失敗して赤 | `(1,10)` は他のどの検査にも掛からない |
| M-mut-03 | 分母から 2 を除く while を削除 | 正例 `(1,10)` が拒否されて赤 | 残分母が 2 になるのは新述語だけの判定 |
| M-mut-04 | 分母から 5 を除く while を削除 | 正例 `(1,10)` が拒否されて赤 | 残分母が 5 になるのは新述語だけの判定 |
| M-mut-05 | `reference is not None` の guard を削除 | `reference_tps=None` の正例が赤 | `None` を拒否する層は他に無い (過剰拒否の正例) |
| M-mut-06 | producer `_fraction_token` の `if denominator != 1: raise ArithmeticError` を削除 | 再定義後 M12 の第 1 段が赤 | 直接呼出しなので registry は介在しない |
| M-mut-07 | producer の `except ArithmeticError` → `DECIMAL_NOT_TERMINATING` の写像を削除 | 再定義後 M12 の第 2 段が赤 | assembly 側の catch は別関数で到達しない |

## 8. プラン v2 (確定変更面)

1. `orchestrator/campaign/p3_b4_analysis_ledgers.py` — `_validate_attempt` の既存
   exact-rational / 正値検査 (`:341-343`) の**直後**に、`reference is not None` を条件として
   既約分母から 2 と 5 を割り切り、残りが 1 でなければ
   `_fail("reference_tps has no finite decimal expansion")` を呼ぶ。
   共有 helper へ切り出さず独立に書く。既存検査の順序は変えない。
2. `orchestrator/tests/test_p3_b4_analysis_ledgers.py` — 正例 `(1,10)`、正例 `None`、
   負例 `(1,3)`、負例 `(1,30)` を追加する。`(1,30)` は `_ratio_from_payload([1,30]) == (1,30)`
   を先に固定し、既存の not-reduced 検査を通過することを示してから新検査の発火を確かめる。
   拒否署名は `B4LedgerError` と exact message。
3. `orchestrator/tests/test_p3_b4_raw_record_producer.py:1138` — M12 を §2 M-2 の二段検査へ
   再定義する。node 名と `MUTATION_NODE_IDS` は変更しない。
4. 変更しない: `p3_b4_analysis_contract.py`、`p3_b4_analysis_adapter.py`、
   `_attempt_is_eligible`、`generate_analysis_manifest` 本体、manifest codec
   (`_ratio_payload` / `_ratio_from_payload` / `_manifest_row_payload`)、事前登録 §5.1.1、
   `acceptance_duration_ledger.json`。

## 9. 段 5・6 の分割

実装面があるので `D95` の Codex author 1 本を立てる。所有は上記 3 file だけ。
段 6 は敵対レビュー 2 本、fix、変異 matrix、受入全走。
