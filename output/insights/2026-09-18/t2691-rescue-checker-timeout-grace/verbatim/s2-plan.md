## 欠陥の検算

現物と生出力は、子の報告を待つ余裕がないという欠陥と整合する。以下の行番号は変更前を指す。

- `tools/check_branch_rescue.py:1578` は子へ `--timeout-seconds=str(timeout)` を渡し、`:1584` は親の待ち時間を `min(timeout, overall_remaining)` にしている。overall 残時間が十分なら同値、不足なら親の方が短い。
- `tools/check_branch_landed.py:1668–1675` では、Python 起動・引数解析後、`assess()` 内の初期化を済ませてから `time.monotonic() + timeout_seconds` を期限にする。厳密には `assess_started` 自体ではなく、`:1675` が期限起点である。
- 子の `Git.run` は `:215–217` の期限切れ、または `:227–243` の Git 子 timeout を `AssessmentError("assessment-timeout", …)` にする。`:1989–2002` で `indeterminate/assessment-timeout` へ変換し、`:2074–2075` で JSON を改行付き１行で出力して rc=2 を返す。rc 対応は `:26`。
- 親が先に timeout すると、`tools/check_branch_rescue.py:1587–1588` から `_empty_landed` に入り、`:1489–1498` の `checker_rc=None`、`complete=False`、子報告なしになる。

生出力の子単体８走はすべて rc=2。wall−T は **0.103562748〜0.133860497 秒**で、brief の 0.103〜0.134 秒と一致する。親経由は T=1、8 とも `checker-timeout`、rc=None、子 JSON 回収 **0/2**。親の待ち時間に子の起動・終了処理が収まらない説明を支持する。

brief の精度上の補足は次のとおり。

- 「親の timer は Popen 前」は、この呼出コードだけから厳密には確定できない。欠陥の根拠には、親の外側待機と、Python 起動後に始まる子の期限のずれで十分である。
- 生出力は起動時間を独立計測していないため、「Python 起動 0.073〜0.077 秒」という内訳は今回の３ログだけでは検算できない。定数の根拠は検算可能な **wall−T の最大値**に置く。
- 子 CLI の許容値は `check_branch_landed.py:2014–2020` の **0超〜300秒**。1〜60秒は rescue 側の assessment CLI 契約である。
- D498 は `docs/decisions.md:20682–20683` で「形式的には受理集合を広げる」と明記する。本件でも、**JSON 検証述語は不変だが、時間内に回収できる報告は増える**と区別する。

## 修正 (file:line)

変更対象の production code は２箇所だけとする。

1. `tools/check_branch_rescue.py:37` の直後へ追加する。

   ```python
   # Login-node light/moderate-load regime, also used for cleanup: n=8 (T=1 x6, T=8 x2).
   # Max wall-T (startup + deadline overshoot + JSON/exit) 0.134s x ~15 -> 2.0s.
   CHECKER_EXIT_GRACE_SECONDS = 2.0
   ```

   DW-O13 `docs/dev-wave/operations.md:104–107` の母集合・regime・最大値への倍率を示す。共有 FS の重負荷まで測定済みとは書かない。

2. `tools/check_branch_rescue.py:1584` を変更する。

   ```python
   timeout=min(timeout + CHECKER_EXIT_GRACE_SECONDS, overall_remaining),
   ```

   `:1578` の子へ渡す値、`:1592–1632` の JSON 検証・rc↔verdict 対応・結果構築は変更しない。外側 timeout の関数化もしない。

同値問題の周辺確認結果：

| 箇所 | 現物の契約 | 判断 |
|---|---|---|
| rescue `:1790–1805` `_audit` | 外側 timeout のみ。子 argv に deadline はない | 同じ二重期限の同値問題ではない |
| rescue `:2178–2183` `_validate_cli` | `git check-ref-format` を固定時間で打切る | 子が期限 JSON を返す契約はなく、同値問題ではない |
| rescue `:268–297` `Git.run` | command 上限と overall 残時間で Git を打切る | 同上 |
| landed `:227–243` `Git.run` | Git 打切りを子自身の assessment-timeout に変換する | 今回変更しない |

## test 設計 (file:line)

`orchestrator/tests/test_check_branch_rescue.py:143` の直後に、時間境界専用の別 helper `_make_timed_fake_landed(path, *, silent=False)` を追加する。既存 `_make_fake_landed` (`:89–142`) は据え置く。

これにより既存３ test (`:515–581`) に加え、既存 helper の payload を完全一致で確認する `:1859–1868`、`:1892–1901` も影響を受けない。

helper が生成する子スクリプトは `json`、`sys`、`time` を使用し、次の動作だけを持つ。

- `T = float(sys.argv[sys.argv.index("--timeout-seconds") + 1])`
- `oid = sys.argv[-1]`
- 沈黙モードは `time.sleep(60)` の後、出力せず終了。
- 正例モードは `time.sleep(T + 0.3)` の後、次の JSON を１行出力して rc=2。

```python
{
    "schema": "izanagi-branch-landed-v1",
    "branch": {"input": oid, "tip": oid},
    "branch_delete_authorized": False,
    "manual_review_required": True,
    "decision": {
        "verdict": "indeterminate",
        "reason": "assessment-timeout",
        "conclusive": False,
    },
    "observations": {"ledger_corpus": {"bytes_read": 0}},
}
```

新規３ test は現 EOF `:1914` の後へ追加する。fake は Git を呼ばないので、`repo=tmp_path`、`oid="a"*40` とし、不要な repo 初期化を省く。親の subprocess・時計は差し替えない。

| test | 呼出・検査 | 追加所要の見積り |
|---|---|---|
| (a) 子の期限報告を回収 | `_landed_assessment(tmp_path, checker, oid, 1.0, 100.0)`。reason=`assessment-timeout`、checker_rc=2、verdict=`indeterminate`、conclusive/complete=False、manual_review_required=True、corpus_bytes_read=0 | 約1.32〜1.40秒 |
| (b) 沈黙する子を打切り | 同じ引数、沈黙モード。reason=`checker-timeout`、checker_rc=None、complete=False。`1.0 + GRACE - 0.2 <= elapsed_seconds < 10.0` | 約3.0〜3.03秒 |
| (c) overall 残時間が優先 | 沈黙モードで `_landed_assessment(tmp_path, checker, oid, 5.0, 0.5)`。reason=`checker-timeout`、checker_rc=None、complete=False、`elapsed_seconds < 1.5` | 約0.5〜0.53秒 |

(a) では `unproven_unit_details.missing_reason == "proof-units-unavailable"` も確認する。`:1502–1516` により、上の最小 payload ならこの値になる。`child-report-unavailable` ではないことを示せるが、**具体的な未証明 unit を回収した証拠とはしない**。

(d) 自己検査は (b)(c) に統合する。(b) が T+GRACE の待機下限、(c) が overall cap を実 subprocess で検査するため、専用関数・４本目の test は不要。ただし elapsed の許容幅は数式の厳密一致を証明するものではなく、今回登録する変異の識別を担う。

公称待機合計は **1.3+3.0+0.5=4.8秒**、通常の起動等を含め約4.82〜4.96秒を見込む。+5秒以内は余裕が小さく、後段で実測確認が必要。ここでは未実行である。

既存実 checker test (`:1758`、`:1789`) の `(30, 30)` は overall cap が優先する既存条件として維持する。monkeypatch 型 timeout test (`:1823–1843`) も維持する。

## 変異事前登録の検算

推奨する (a)〜(c) に対する予測は次のとおり。KILLED は未実測であり、表は事前登録である。

| 変異 | 赤にする test | 理由 |
|---|---|---|
| M1：GRACE→0 | (a) | 外側1秒で、子の T+0.3=1.3秒後の報告を回収できない |
| M2：overall cap を除去 | (c) | 0.5秒で終わらず約7秒待ち、`elapsed < 1.5` に違反 |
| M3：子にも T+GRACE を渡す | (a) | fake が argv の3秒を読み3.3秒眠るため、外側3秒で打切られる |
| M4：外側を `max(T, GRACE)` に変更 | (b) | 約2秒で打切り、下限2.8秒に違反する |

M1 で test 側も変更後の定数を参照すると、(b) の下限は0.8秒へ下がるため、**M1 の検出担当は (a)** と明記する。

M4 に対する２案：

- **T+0.3=1.3秒を維持する案を推奨。** (a) 単体では M4 が生き残るが、(b) の下限で検出できる。正例の終了余裕は約1.7秒あり、実測 overshoot にも比較的近く、合計4.8秒を維持できる。
- **T+GRACE−0.5=2.5秒へ延ばす案。** (a) 単体でも M4 を検出するが、正例の余裕が約0.5秒へ減り、公称合計が6.0秒となって+5秒制約に反する。採用しない。

この条件なら、４変異すべてに検出担当があり、M4 用の追加 sleep や自己検査 test は不要である。

## docs 逐語案

親が `docs/unreachable-object-ledger.md:91–93` を次の３行へ置換する。既存 `:94` 冒頭の「そちらも上げる。」へ接続する。

```text
landed 判定の子予算は既定 8 秒で、期限超過の JSON を回収できれば `assessment-timeout` となり rc `2` になる。
親は子予算 + 終了余裕 2 秒まで待つが、全体の残時間で打ち切る。そこで応答がなければ `checker-timeout` となる。必要なら `--assessment-timeout-seconds` (上限 60) を上げ、
判定件数 × (子予算 + 2 秒) に inventory 等の時間を足した見積りが全体の `--timeout-seconds` (既定 300、上限 900) に迫るなら
```

## scope 外

- **T-2686 の律速改善**：判定処理の高速化は、親子の期限差を直す今回の目的と独立している。
- **`_audit` へ子 deadline を追加**：現状は同値問題ではなく、新たな子の期限契約を設ける変更になる。
- **GRACE の CLI 化**：実測に基づく定数１つで足り、公開設定面を増やす必要がない。
- **既存 monkeypatch 型 test の置換**：子報告欠落時の不完全性を検査する役割があり、実時間境界の新規 test と併存できる。
- **landed checker、gate、検査器、台帳の新設・改修**：今回の修正に不要。JSON 形・schema・rc↔verdict の受理規則も変更しない。

## リスクと未確定点

- **共有 FS 重負荷**：Python 起動等が2秒の余裕を使い切れば、従来どおり `checker-timeout` となる。`:1486–1498` により indeterminate、complete=False を保ち、JSON 検証述語を緩めない。ただし2秒は８走の観測に基づく値で、重負荷時の回収を保証しない。
- **時間依存 flake**：(a) は約1.7秒、(c) は0.5秒の打切りに対して上限1.5秒の余裕がある。(b) は ε=0.2秒にし、M4 の2秒と下限2.8秒を分離する。ただし親が大幅に停止・遅延すれば、elapsed による M4 検出が隠れる可能性は残る。
- **+5秒制約**：公称4.8秒には約0.2秒しか余裕がない。repo 初期化と４本目の実時間 test を省くが、実行環境での増分確認は後段に残る。
- **総時間**：子待機の総量は最大で `max_assessments × (T+GRACE)` 相当へ増える。ただし rescue `:1985` の全体 deadline、`:262–263` の残時間、`:2065–2067` の受渡し、変更後も残す `min` が制限する。既定値なら無制限時の640秒に対して全体予算は300秒。
- **overall cap の精度**：渡される残時間は呼出時点の値であり、環境準備・終了処理・後処理もあるため、wall time が overall 値を一切超えない厳密 watchdog ではない。この既存性質の改修は含めない。
- **実 repo の回収確認**：親の後段実測で T=1、8 の2/2回収を確認する。今回の静的検算から成功済みとは扱わない。

## 総括

推奨は **GRACE=2.0秒の定数追加と外側 timeout １行の変更、専用 fake helper と実時間 test ３本、親による docs 修正**。正例は T+0.3秒を維持し、M4 は沈黙 test の待機下限で検出する。

実装・編集・pytest・変異実行は行っていない。未確定なのは実行環境での追加所要+5秒以内、４変異の実測結果、実 repo の子報告2/2回収である。