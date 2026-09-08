# 段 4 裁定 — [T-2409] WAL の正しさ判定を B-10 legacy 受理経路へ束縛する

親が段 2 プランと段 3 敵対相談 2 本を裁定し、プラン v2 を確定する。**実装子はこの文書を正本とする。**
プランと本文書が食い違う場合は本文書が勝つ。

## 確定した実装 (プラン v2)

**候補 A を採る。** `orchestrator/campaign/b10_backoff_shape_sweep.py` の
`_verification_source_disclosure` の `verify_done` ループに、exact 値述語を 1 つ足す。それだけである。

### 置き場所 (起点 commit `cc9bba523` の行番号)

`:3405-3407` の `if record.stage != STAGE_VERIFY_DONE: continue` と、
`:3408` の `raw_verify_done_records` 加算の**直後**。
`:3409` の `workload_payload = record.payload.get("workload")` より**前**。

- **既存の `try/except Exception` (`:3390-3395`) の内側へ入れてはならない。**
  内側だと新しい `PreflightError` まで握り潰されて `wal_read_error` + 空 counts に化ける。
  現行コードでは `for record in records:` ループは既に try の外にあるので、そこへ足せば正しい。
- unknown tag の `continue` (`:3411-3419`) と unmapped variant の `continue` (`:3420-3423`) より
  **前**に置くこと。後ろだと、悪い record の tag を未知値にするだけで検査を回避できる。

### 述語

```
type(record.payload.get("anomalies")) is int
and record.payload.get("anomalies") == 0
and record.payload.get("certified") is True
and record.payload.get("verdict") == "serializable"
```

これを満たさない `verify_done` があれば `PreflightError("legacy-wal-verdict", ...)` を送出する。
message には campaign ID と `record.variant` を含める。

**[段 3 sol 所見 2 = real / must-fix]** 段 2 プランの code block は `payload.get(...)` と書いていたが、
このループに `payload` という名前の変数は無い。**必ず `record.payload` を使うこと。**
そのまま貼ると `verify_done` を含む全 WAL が `NameError` になり、現物 3 系列まで拒否される。

判断の根拠:

- `type(...) is int` は `False == 0` による迂回を塞ぐ (`bool` は `int` の subclass)。
- `certified is True` は `1` や truthy 値を弾く。
- `record.payload` は WAL parse 時に dict であることが保証されている
  (`orchestrator/campaign/wal.py:398-399`。親が確認済み)。

### 触ってはならないもの

- 135 個の `LEGACY_*_RECORD_SHA256S` literal、balanced / read-heavy の `meta_digest` golden。
- 凍結 block record file。`output/` 配下と repository 外の `izanagi-job-evidence` 配下への書き込み。
- `_legacy_*_binding()` / 3 つの `_validate_legacy_*_records()` / `_assert_report_lock_binding()`
  の既存受理述語 (T-2408 担当 session の領域)。
- **`_collect_report_inputs` の関数構造** (module 直下 FunctionDef のまま。helper 切り出し・
  dispatch 表化・デコレータ付与は既存 AST test 4 箇所を直接赤にする)。
- `orchestrator/campaign/wal.py`。

## 裁定した所見

### real / must-fix — 採用して実装または記録を直す

| # | 出所 | 所見 | 裁定 |
|---|---|---|---|
| A1 | sol 2 | プランの述語 code が `payload` 未定義 | **採用。`record.payload` を使う** (上記) |
| A2 | luna 1 | 親 brief の「D1772 の字義は実装不能なので代替」は誤り。**D1772 自身が「追加 exact 条件として重ねられるかを実測せよ」と命じている**ので、値述語は裁定が名指しした第一候補そのもの | **採用。親 brief の (P1) の枠組みを撤回する。**記録には「D1772 の指示どおり実測し、指示された追加 exact 条件を実施した」と書く。「代替」「実装不能」と書かない |
| A3 | luna 2 | 親の「135 file 書換え or 系列別 whole-WAL digest」の二択は偽。`variant` + tag + 3 field に限定した **projection digest** という第三形がある。「read-heavy の `proof_surfaces` があるから系列別 literal が必須」も従って偽 | **採用。二択の記述を撤回する。**第三形の存在を認めたうえで**不採用**とする — 新しい digest producer・期待値・対応規則を要し、D1772 の「新しい gate 機構は作らない」から遠いため (luna も同結論) |
| A4 | sol 親 brief 3 | 親 brief の「現物 verifier 判定へ束縛される」は過大。束縛するのは **WAL に記録された 3 値**であり、その生成主体・verifier の実行・block record との attempt 対応ではない | **採用。**記録では「記録された正しさ判定の値へ束縛する。WAL の真正性は束縛しない (WAL に hash chain は無い)」と書く |
| A5 | sol 親 brief 4 | 完了判定の母集合が未定義 | **採用。**母集合を「`read_records_checked` が例外なく返した**終端済み**で parse 可能な record のうち `stage == "verify_done"` のもの」と定義する |
| A6 | luna 6 | `ANALYSIS_REL` の波及は hash だけでなく binding SHA・将来の campaign identity・将来の block record・report path / provenance にも及ぶ | **採用。**記録の該当箇所を書き直す |
| A7 | luna (副作用節) | 現物に対して full `phase=report` を走らせると、**新しい binding 配下へ新 report を発行してしまう** | **採用。禁止する。**現物確認は `_collect_report_inputs` までに留める。実装子にも禁止として渡す |
| A8 | sol 変異 2 | 変異候補 3 「正数も許す条件」が具体化されていない | **採用。**`== 0` を `>= 0` へ、と具体化する |
| A9 | sol 変異 3 | 変異候補 6 の `[verdict-missing]` は truthy 化 mutant を殺せない (`None` はどちらでも偽) | **採用。**truthy 化の期待 node から `[verdict-missing]` を外す |
| A10 | sol 変異 4 | 変異候補 12 は、3 validator と lock を通過済みの fixture に固定しないと帰属しない。既存 collector test (`:2552-2651`) は disclosure を mock するので証拠にならない | **採用。**専用 fixture を要求する |

### real だが scope 外 — 実装せず、ユーザーへ返す

| # | 出所 | 所見 | 裁定理由 |
|---|---|---|---|
| B1 | sol 3 | 3 field を正常値で**自己申告した偽 WAL** は述語を通る。`build_attempt_id` / `commits` / `aborts` / timestamp も偽造できる | WAL に真正性の仕組みが無いことは `wal.py:14-15` が自ら明記している既存の性質。閉じるには暗号学的束縛 = **新しい gate 機構**が要り、D1772 が明示的に却下し、ユーザーも「仮想リスク向けの gate 追加は scope 外」と指示している。**記録に限界として明記し、裁定へ返す** |
| B2 | sol 4 | WAL 欠落 / 読取例外 / 未終端 tail は述語へ到達しない | **親が実測して scope 外と裁定する。**`read_records_checked` は WAL 不在で `([], False)` を返し (`wal.py:1651-1652`)、`_verification_completeness` は一度も raise せず `incomplete_slots` を開示するだけである (`:3441-3513`、親が確認)。よってこれらの経路では **`incomplete_slots > 0` または `wal_read_error` が立った、見て分かる別物の report** になる。T-2409 が名指しした穴は「件数と tag が揃って**同じ判定の** report が出る」ことであり、この経路はそれに当たらない。fail-closed 化は受理集合をさらに狭める別の裁定事項。**裁定へ返す** |

### refuted — 対応しない

- sol 1 (攻撃は止まる)、sol 5 (別 stage への悪い値。攻撃者は正常な `verify_done` 90 件を別途
  用意する必要があり、利得が無い)、sol 所見 1 / 3 / 5 / 6。
- sol 所見 4 のうち `_write_reports` の直接呼出しは **test 専用 surface** であり production の
  consumer 取り残しではない。`--phase trial-cell` は schema が別 (`b10-backoff-shape-trial-report/v1`)
  で legacy 3 系列 report ではない。**対応しない。**
- luna 3 / 4 / 7 / 8。
- luna 5 と sol 親 brief 5 (「のみ」「将来も」の一般化) は **nit として採用** — 記録では
  「指定 3 campaign の現時点の bytes について」と範囲を明記する。

## A10 の訂正 (段 6 の再レビュー後、親が実測して裁定)

**A10 が要求した「3 validator と lock を通過済みの collector fixture」のうち、validator 部分は
repository 内では構造的に達成不能である。裁定を訂正し、要求を lock 部分だけへ狭める。**

実測した理由:

- `_validate_legacy_*_records` は各 record の `submission_receipt` を **filesystem の path として開き、
  bytes の sha256 を照合する** (`b10_backoff_shape_sweep.py:2651-2659`)。現物 record の receipt は
  repository 外 (`izanagi-job-evidence` 配下) にあり、repo 内の fixture では開けない。
- receipt path を tmp へ書き換えれば通せるが、**record の内容が変われば `record_sha256` が変わり、
  45 個の凍結 literal と一致しなくなる**ので validator は別の理由で落ちる。逃げ道が無い。
- `expected_record_digests` を注入すれば回避できるが、`_collect_report_inputs` が
  validator を keyword 無しで呼ぶことを既存 AST test が固定しているため、注入点が無い。
- これは本 wave が作った制約ではない。先行 wave (worklog 1324) が同じことを実測して
  「repo 内では validator の全経路を本物の証拠に通せない」と記録済みである。

したがって:

- **lock は実物を通す (達成済み)。** 段 6 再レビューが経路を追って「素通りしていない」ことを確認した。
- **3 validator の stub は残す。** 限界を test の docstring に明記し、隠さない。
- **validator 側の本物の証拠は、専用の既存 test が別に担っている** —
  `test_e3de15eb_legacy_adapter_enforces_injected_exact_digest_set` (`:1898`)、
  `test_143a3f74_balanced_adapter_accepts_only_pinned_series` (`:1982`)、
  `test_acf840c8_read_heavy_adapter_accepts_only_pinned_series` (`:2116`)、
  `test_acf840c8_frozen_read_heavy_records_match_production_contract` (`:2182`)。
  collector test が validator を stub することで、**変異 M12 の赤理由が 1 つに絞れる**という
  副次的な利点もある。
- **記録では「統合を通した」と書かない。**「collector と WAL 述語の結線は通した。validator は
  repo 外 file を要するため別 test が担う」と書く。

段 6 の再レビューはこの 1 点で NO-GO を出したが、**要求自体が達成不能であることを親が実測したので、
要求を訂正して GO とする。**他の所見 (F1 / F2 / F3 と luna の must-fix) はすべて closed で、
fix による新規 regression は無いことを再レビューが確認済みである。

## 変異事前登録 (DW-M01)

**anchor の逐語 (`old`) と期待 node は、段 6 の fix 後の最終 commit で再検証してから本走する
(DW-M07)。** 以下は登録内容であり、行番号は実装後に確定する。

| id | category | 変異 | 期待 status | 期待 node の骨子 |
|---|---|---|---|---|
| M1 | negative | 述語ブロックを丸ごと削除 | KILLED | field mutation 8 case 全部 |
| M2 | negative | `type(x) is int` を `isinstance(x, int)` へ | KILLED | `[anomalies-bool-false]` |
| M3 | negative | `anomalies == 0` を `anomalies >= 0` へ (**A8 で具体化**) | KILLED | `[anomalies-nonzero]` |
| M4 | negative | `certified is True` を `certified == True` へ | KILLED | `[certified-int-one]` |
| M5 | negative | `certified` 条件を削除 | KILLED | `[certified-false]`, `[certified-missing]` |
| M6 | negative | `verdict == "serializable"` を truthy 判定へ (**A9: `[verdict-missing]` は期待から外す**) | KILLED | `[verdict-other]` のみ |
| M7 | negative | 3 条件の連言を `or` へ | KILLED | 単独 field mutation 各 case |
| M8 | negative | 述語を unknown tag の `continue` より後へ移す | KILLED | `[unknown-tag]` |
| M9 | negative | 述語を unmapped variant の `continue` より後へ移す | KILLED | `[unmapped-variant]` |
| M10 | negative | ループ全体を broad `try/except` の内側へ移す | KILLED | field mutation 全 case |
| M11 | **positive (過剰拒否の正例、DW-M01 必須)** | stage filter を削除し `build_start` 等にも 3 field を要求 | KILLED | 正例 test (3 field を持たない非 `verify_done` frame を含む) |
| M12 | negative | collector から disclosure 呼出しを迂回し空 counts を直接設定 (**A10: 3 validator と lock を通過済みの専用 fixture に固定すること**) | KILLED | collector 経由の差し替え検出 test |

`--runner-mode dispatch` を既定とし runner argv へ `--force-dispatch` を入れる。
`--attempt-out` と `--wrapper-attempt` は同時指定。実走は `--detached`。

## テスト (確定)

**配置:** 新 test は **2850 行付近以降** (既存 `test_verification_completeness_counts_records_and_discloses_wal_anomalies`
(`:2752`) の直後)。**2463〜2670 行は T-2408 担当 session の領域なので使わない。**

- 正例 1: exact な 3 field を持つ `verify_done` と、3 field を持たない非 `verify_done` frame を
  同じ WAL に置き、production の `_verification_source_disclosure` を通して期待 counts が返ること。
  **read-heavy を模した `proof_surfaces` 入り payload も正例に含める** (余分な key で壊れないこと)。
- 正例 2: 3 campaign layout を組み、`_collect_report_inputs` が返ること。disclosure を mock しない。
- 負例 8 case (parameterized): `anomalies-nonzero` / `anomalies-bool-false` / `anomalies-missing` /
  `certified-false` / `certified-int-one` / `certified-missing` / `verdict-other` / `verdict-missing`。
  **各 case は record 数・variant・`workload.tag` を不変にする** (件数と tag を揃えた差し替えの再現)。
- 順序 case 2 件: `unknown-tag` / `unmapped-variant` — 悪い 3 field と未知 tag / 未対応 variant を
  同じ record に置き、`continue` より先に赤になること。
- 既存 `test_verification_completeness_counts_records_and_discloses_wal_anomalies` (`:2752`) の
  **fixture** に 3 field を足す。**同 test の assertion と期待値は変えない。**

現物 WAL は repository 外なので、標準 suite の唯一の正例にはしない。決定的 fixture を正とする。

## 記録に書くこと (段 7)

- **A2 / A3 / A4 / A5 / A6 の訂正を反映する。**「字義が実装不能」「二択」「verifier 判定へ束縛」
  「全 verify_done」とは書かない。
- **B1 / B2 を限界と未裁定事項として明記し、ユーザーへ返す。**
- 範囲は「指定 3 campaign の現時点の bytes について」と明記する。
