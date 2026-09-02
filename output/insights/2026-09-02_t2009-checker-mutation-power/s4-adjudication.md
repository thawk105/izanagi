# 段 4 裁定 — [T-2009]

親が段 2 プランと段 3 の 2 レンズを real / refuted、採用 / 不採用、scope 内 / 外で裁定する。
親が自分で実測して裏取りした事実には「(親実測)」を付す。

## 所見の裁定

| # | 出所 | 判定 | 採否 |
|---|---|---|---|
| A-1 | M5 の digest が 63 桁で分岐非到達 | **real** (親実測: 実値は `...ee511a2a` の 64 桁) | 採用。ただし M5 自体を差し替えるので消滅 |
| A-2 | P1 を殺す node が推奨分母の外にある (`test_campaign.py::test_pipeline_extra_correctness_second_pass_red_aborts_with_workload_tag`) | **real** (親実測: `_mock_pipeline_multipass` は r1 を実 verifier に通し `_red_vr()` で差し替えない) | 採用。分母に `test_campaign.py` を**丸ごと**入れる |
| A-3 | 分母に inert な raw-bytes 同一性 node が 2 件残る | **real** | 採用。deselect はせず「観測 node に一度も現れないこと」を inert の証拠として記録する |
| A-4 | F-new1 は過大一般化だが同一性 pin 自体は正当 | **real** (親実測: 発火は `capture_/verify_live_contract_loader_binding` 経由のみ) | 採用。brief の F-new1 を訂正し、規律 7 の但し書きと矛盾しない書き方にする |
| A-5 | 「穴」と呼べる条件を限定すべき | **real** | 採用。matrix を 機械結果 / semantic 遷移 / 主張可能範囲 の 3 層で書く |
| A-6 | README は prior claim、実測が current behavior | **real** | 採用 |
| A-7 | 塞ぐ実装は scope 外 | **real** | 採用 (元から scope 外) |
| B-1 | M1 は診断 pin であって semantic kill ではない | **real** | 採用 |
| B-2 | M2 は有効 | **real** | 採用、変更なし |
| B-3 | **M3 は生存しない。`r5_nonlatest_transitive` に長さ 4 の witness がある** | **real** (親実測: `T2 → T3 → T4 → T50 → T2`、len 4、G2) | 採用。事前登録は probe の観測 node で確定する |
| B-4 | M4 は単一理由性を満たさない | **real** | 採用。`Integrity.clean()` の framing 項へ再照準 (M4') |
| B-5 | M5 は照準ミスで結論を支えない | **real** | 採用。ただし差し替え先はレンズ B 案ではなく親案 (下記 M5') |
| B-6 | P1 は有効な正例対照 | **real** | 採用 |
| B-7 | E1 は正しい等価対照 | **real** | 採用 |
| B-8 | bytes node の分離は保たれている | **real** | 採用 |
| B-9 | harness の KILLED は意味論を表さない | **real** | 採用。台帳を 4 欄で書く |
| B-10/11 | 親 brief の訂正 | **real** | 採用 (下記) |

## 差し替えの確定

**M4'。** `orchestrator/verifier/core.py:65` の counter ではなく、
`orchestrator/verifier/model.py:170` の実効 gate から framing 項だけを外す。

- old: `                and self.malformed_keys == 0 and self.framing_violations == 0\n`
- new: `                and self.malformed_keys == 0\n`

counter・details・notes は無傷なので、診断を assert する node は緑のまま残り、赤は
「framing 違反があるのに clean と判定された」一因に絞れる。

**M5'。** レンズ B は「未知入力で誤答する mutant と killer input を事前登録せよ」と勧めた。
親はこれを採るが、実装形は**入力の出所で答える**形にする (D799 が挙げた「fixture の hash や
dir 名で結果を返す」の後者)。hash 表を持たずに同じ問いを測れ、単一理由性も保てる。

- old: `    """1 run (= 1 trace ディレクトリ) を検証する。"""\n    txns, issues = parse_trace_dir(trace_dir)\n`
- new: 入口で `os.path.abspath(trace_dir)` が `/orchestrator/tests/fixtures/` を含まなければ
  `VerifyResult(trace_dir=trace_dir, serializable=True, n_txns=1)` を返す。含む場合は通常経路。

これが測る問いは「**既存スイートは corpus の外の入力を与えているか。与えているなら、
corpus 引き当て型の verifier は既存テストを通らない**」である。`n_txns=1` は必須で、
`n_txns == 0` だと `VerifyResult.verdict` が indeterminate に倒れて fail-open にならない
(親実測: `model.py:211`)。killer input は事前登録できる — `test_verifier.py:206` の
`_tmp_trace` が `/tmp/izanagi_trace_*` に作る合成 trace 群である (親実測: 用例 4 箇所)。

**M3 は差し替えない。** 事前登録の期待だけを probe で確定する。r5 の変異前 verdict は
`non-serializable`、M3 適用後は cycle が消えて `indeterminate` (integrity は
`missing_txids=46` で unclean のまま) になる (親実測)。**certified 側へは倒れない**ので、
これは fail-open ではなく verdict 遷移である。台帳ではそう書く。

## 分母 (estimand)

**挙動分母 = 次の 5 file 全体。** 709 passed / 3 skipped / 27.73 秒 (親実測、login node)。

```
orchestrator/tests/test_verifier.py
orchestrator/tests/test_t1286_commit_receipt.py
orchestrator/tests/test_campaign.py
orchestrator/tests/test_s1_direct_comparison.py
orchestrator/tests/test_silo_ladder_rung1_driver.py
```

exact node selector ではなく file 単位にする理由は 2 つ。(a) A-2 の見落としが示すとおり、
「実 verifier を呼ぶ node」の静的列挙は取りこぼす。(b) 費用が安く、file を丸ごと走らせても
28 秒である。**contract-loader の live-binding node はこの 5 file に 1 件も無い** (親実測:
発火点は `ident.py` / `artifact_admission.py` / `p3_b4_wiring_probe.py` と
`test_t671_source_binding.py`)。よって `--deselect` は使わない。

**同一性対照 = `orchestrator/tests/test_t671_source_binding.py` 単独。** 113 passed / 7.15 秒
(親実測)。ここへ E1 (意味を一切変えない等価変異) と P1 (正しさを壊す変異) を同じように当てる。
**両方が同じように赤くなるなら、同一性層は「変わったか」しか言えず「効いたか」を言えない**という
規律 7 の主張が、この repo の現物で実証される。これは新しい gate ではなく、既存 2 層の
検出力を同じ変異で比較するだけの対照である。

## 事前登録 (`DW-M01`)

3 段で回す。**probe → 期待確定 → 本走**。

1. **probe (挙動分母)**: 7 変異を全件 `SURVIVED` 期待で走らせ、観測 node を集める。
2. **probe (同一性分母)**: E1・P1 を全件 `SURVIVED` 期待で走らせ、観測 node を集める。
3. **本走**: probe の観測 node を完全集合として `expected_status` / `expected_nodes` を
   登録し直して走らせる (`DW-M08`)。

**期待の事前宣言 (結果を見る前に書く。外れた向きが所見である)。**

| id | 機械期待 | semantic 期待 | 根拠 |
|---|---|---|---|
| M1 | KILLED | 遷移なし (診断のみ) | `_classify` は verdict 不関与 |
| M2 | KILLED | non-serializable → certified (fail-open) | r6/r7 の cycle が消える |
| M3 | KILLED | non-serializable → indeterminate (fail-open ではない) | r5 の len 4 witness |
| M4' | KILLED | indeterminate → certified (fail-open) | framing 項が gate から消える |
| M5' | KILLED | corpus 外入力が certified (fail-open) | `_tmp_trace` の合成 trace |
| P1 | KILLED | non-serializable → certified、receipt 発行可へ (fail-open) | rw 辺消失 |
| E1 | SURVIVED | 遷移なし | 等価変異 |
| E1 (同一性分母) | **KILLED** | 遷移なし | 意味不変でも blob が変わる |
| P1 (同一性分母) | KILLED | — | 同上 |

**この事前登録の要点は「M1〜M5 のうち生存するものは無い」という予測である。** D799 決定 (2) の
5 件は g6/r8 の**対**の射程であって既存スイート全体の射程ではない、というのが親の判断であり、
実測がこれを支持すれば「規律 7 が開けた穴」は本測定の範囲では 0 件になる。
**外れた場合 (どれかが生存した場合) は、そこが穴として特定される。**

## 台帳の書式 (`DW-M09` ではなく B-9 の採用)

各変異について 4 欄で書く。

`machine_status` (harness の KILLED/SURVIVED) / `failed_nodes` (完全集合) /
`semantic_transition` (受理集合の遷移。無ければ「なし」) / `first_failure_layer`
(semantic / graph-only / golden / diagnostic / identity)。

## 親 brief の訂正 (段 7 の記録に反映する)

- **F-new1 を訂正**: 「verifier を触る変異はすべて数百件の drift 赤を引く」は誤り。
  同一性 pin は live-binding を通ったときだけ発火し、挙動分母の 5 file は通らない。
  同一性検査そのものは規律 7 が明示的に許す (束縛の検査)。本 wave はそれを禁じず、
  **今回の estimand から別層化するだけ**である。
- **F-new2 を訂正**: `fixtures/README.md` の「長さ 4 以上の巡回はどの fixture も担っていない」は
  **事実として誤り**。`r5_nonlatest_transitive` が長さ 4 の G2 witness を持つ (親実測)。
  README の「規模で買えない限界」の測定 (実 Silo prefix では witness が 2 か 3) 自体は
  否定しない — 対象が実 emitter 由来 fixture に限られていただけである。
- **穴の数の上限を 5 とした点を訂正**: M1 は受理集合を変えないので穴の候補ではない。
- 変異アンカー表を M4' / M5' で置き換える。

## scope

- 塞ぐ実装 (長さ 4 の clean fixture、metamorphic test、第二 checker) は**行わない**。
  裁定パッケージとしてユーザーへ返す。
- 新しい gate・検査・台帳・一般化を足さない。既存テストの期待値を 1 行も変えない。
- repo の tracked file は 1 byte も変えない (変異は固定 commit の使い捨て worktree のみ)。

## 実装面

repo へ入る実装面は**ゼロ**。変異 spec は repo 外の JSON、走行は既存 `tools/` の harness。
よって段 5 の Codex 実装子は立てない (`DW-S04`: 実装面差分ゼロ)。ただし
**変異 matrix は免除しない** — 本 wave の成果物そのものが変異 matrix である。
