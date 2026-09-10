# [T-2401] 評価器例外の理由を fail-closed のまま構造化して残す — 変異走行が「歯の立たないテスト」を 3 件暴いた

2026-09-08。branch `worktree-dev-wave-t2401-evaluator-reason`。base `cc9bba523`。
裁定の正本は `docs/decisions.md` の {{D:evaluator-diagnostic-outside-report-digest}}。

## 0. この wave が主張すること・しないこと

**主張する:**

1. 8c 判定器が評価器呼び出しの例外を握り潰すとき、捕捉した理由を
   `callsite` / `exception_type` / `preregistration_reason` の 3 field へ構造化して残すようにした。
   判定器 CLI の `check` はこれを stderr へ 1 行の compact JSON で出す。
2. **fail-closed の終端を 1 bit も変えていない。** status、`reason_code`、evidence、`effective`、
   CLI stdout の bytes、report digest はすべて従来どおりである。受理集合は広がっていない。
3. 事前登録した 26 変異が全件 KILLED で、期待 node と完全一致した。
4. 変異走行は「テストを守る道具」ではなく「テストの弱点を暴く道具」として実際に働いた。
   **静的レビュー 3 本が見逃した欠陥を 3 件、走らせて初めて見つけた** (§3)。

**主張しない:**

- **有限個の例外型しか試さないテストは、その型だけを列挙する catch 変異に原理的に勝てない。**
  本 wave はその変異の実装コストを上げただけであり、閉じたとは主張しない。
  repo 内の挙動検査は、gate と検査を同じ主体が変更できる限り、意図的な弱体化への
  完全な防壁ではない (D387)。
- **`PreregistrationError.reason` の由来と機密性は保証していない。** 許可文字
  (`[a-z0-9-]`、128 文字以下) に収まる外部由来の値は、そのまま診断に残る。
  reason 語彙を閉じるのは別の変更である。
- **gate report CLI では F631 が閉じていない。** 同 CLI は診断を持たない旧 API を呼ぶ。
  判定器 CLI の外側 catch が出す `str(exc)` も本 wave の対象外である。どちらも次の一手へ登録した。
- **`--json` の stdout だけを保存する利用者には診断が届かない。** stdout の bytes を
  変えない不変条件を優先した。

## 1. 直した内容

`orchestrator/campaign/s8c_preregistration.py` の `_default_registry_results` は、
評価器呼び出しと結果正規化を 1 つの `try` で囲み、例外 object を捨てて 12 件すべてを
`ERROR / evaluator-exception` に倒していた。F631 で「12 条件すべてが評価不能」という
誤った現在地報告が出た直接の原因である。真因は
`PreregistrationError("predicate-result-type")` だったが、その情報はどこにも残らなかった。

変更後は次のようになる。

- `EvaluatorExceptionReason` を独立した frozen dataclass として足した。
  `ActivationReport` / `PredicateResult` / `EvidenceRef` の field は増減していない。
- `try` を evaluator 呼び出しと `_normalize_predicate_results` 呼び出しの 2 節へ分けた。
  materialize は normalize 側 try の内側に留め、遅延 generator の例外が漏れないようにした。
  捕捉集合 (`except Exception`) は変えていない。
- 診断抽出は total である。例外 object からの値取得を自身で捕捉し、何が起きても診断を返す。
- 3 field はすべて安全な文字列へ正規化する。`callsite` は実装が与える固定 literal のみ。
  `exception_type` と `preregistration_reason` は型・文字種・長さを検査し、外れたら
  受理正規表現に**一致しない** sentinel へ倒す (`<...>` を含む)。
- test-registry 経路も同じ形で診断を返す。
  「診断が空 ⟺ 例外を握り潰していない」を全経路で成立させるためである。
- CLI `check` だけが診断つき sibling API を呼び、診断を stderr へ出す。
  診断出力全体を `except Exception` で囲み、出力に失敗しても stdout と終了値を保つ。

## 2. なぜ report の中に入れなかったか

`_activation_report_digest` は `ActivationReport` の全 field から digest を作る。
その値が `EffectivePreregistration.report_digest_sha256` になり、
`orchestrator/campaign/trial_registry.py` の `activation_report_digest_sha256` として
台帳へ永続化・再照合されている。field を足すと、**非 null の digest を束縛した
registered-effective の成果物**が再導出で不一致になる (規律 7)。
exploratory と formal non-certifying は digest が `None` なのでこの理由では変わらない。

段 1 brief は当初これを「台帳が全件不一致」と書いていた。段 3 の敵対レビューが
過大表現だと指摘し、上記の範囲へ訂正した。

## 3. 変異走行が暴いた 3 件 (静的レビューはいずれも見逃した)

段 3 の敵対相談 2 本と段 6 の焦点再レビュー 1 本は、いずれも次を検出しなかった。
**走らせて初めて出た。**

### 3.1 敵対 fixture が pytest の失敗報告経路を壊す

変異 `m1` (fallback status を `SATISFIED` へ) を当てると、落ちるはずの 3 件は落ちたが、
**pytest 自身が `INTERNALERROR` を出して xdist worker が死に、rc=3 になった。**

pytest は失敗を整形するとき `_pytest/_io/saferepr.py` -> `reprlib.repr1` ->
`typename = type(x).__name__` を通る。本 wave が足した敵対 fixture の metaclass
`__getattribute__` がここで `SystemExit` を送出していた。
3 件の失敗は failure digest に出たが `FAILED` の要約行が出ず、harness は node を抽出できず停止した。

**正常時に緑であることは、失敗時に正しく報告できることを含意しない。**
受入全走でもこれらの node が落ちれば全体が rc=3 になり、赤の帰属が不能になる。

対応: 危険な挙動を診断抽出を呼ぶ瞬間だけ有効にする arm / disarm 構造にし、
armed でない状態で `repr()` しても例外が出ないことを assertion で固定した。

### 3.2 `KeyboardInterrupt` を負例に使うと pytest が session 中断と解釈する

診断 helper の guard (`except BaseException`) を狭める変異で **rc=2** が返った。
rc=2 は「session が中断された」であり、テストの失敗 (rc=1) ではない。
guard を外すと `KeyboardInterrupt` が helper の外へ出て、pytest が利用者による中断と解釈する。

対応: 負例を、この test file 内で定義した `BaseException` の直接 subclass へ置き換えた。
`Exception` を継承すると「`except Exception` では捕まらない例外」という命題が検査できなくなる。

### 3.3 CLI guard のテストが guard の有無を区別できていなかった

CLI 診断出力の guard を `except ZeroDivisionError` / `except OSError` へ狭める変異が
**2 件とも生存した。**

対応する 2 つの test は、子 process で `sys.stderr` を「write すると例外を出す object」へ
差し替え、`raise SystemExit(P.main([...]))` を実行し、
stdout の完全一致・`returncode == 1`・`stderr == b""` を検査していた。
**guard が捕まえなくても、この 3 つはすべて成立する。**

- 例外が `main()` の外へ出ると未処理例外になるが、**その終了コードも 1 である。**
- traceback は差し替えた `sys.stderr` object へ書かれるので、**実 fd 2 は空のままである。**
- stdout は診断 loop より前に出力済みなので変わらない。

つまり「guard が効いて `main()` が値を返した」ことを 1 つも観測していなかった。
機構を守っているつもりのテストが、実際には何も守っていなかった。

対応: `main()` の返り値を受け取れたこと自体を壊れていない出力先へ記録し、
その実在と値を assertion で固定した。既存の 3 つの assertion は純増で残した。
production の guard を 2 通りに狭めて、両方で該当 test が落ちることを実測した。

## 4. 変異 matrix (26 件、全件 KILLED)

`tools/mutation_harness.py`、`--runner-mode dispatch`、baseline は `PASSED / rc=0`。
spec は `mutation-spec.json`、結果は `mutation-out.json`、
probe の要約は `evidence/mutation-probe4-summary.json`。

```
{"KILLED": 26, "MISMATCH": 0, "PARSE_ERROR": 0, "SURVIVED": 0, "TIMEOUT": 0,
 "completed": 26, "matching": 26, "recorded": 26, "registered": 26}
```

`repo_head` は `9989d360501e951c8cd4d187f84183e40eb9f8a4`。
anchor はすべて source 内で一意であることを、spec 生成時に機械で確認した (`DW-M04`)。

**枠 1 — 受理集合と捕捉集合 (10 件)**

| id | 変異 |
|---|---|
| m1 | evaluator 側 fallback を `ERROR` から `SATISFIED` へ |
| m2 | normalize 側 fallback の `reason_code` を別の値へ |
| m3 | `_normalize_predicate_results` を外して raw を返す |
| m4 | evaluator 側 catch を `except RuntimeError` へ狭める |
| m5 | normalize 側 catch を `except RuntimeError` へ狭める |
| m6 | test-registry evaluator 側 catch を狭める |
| m7 | test-registry normalize 側 catch を狭める |
| m8 | 診断 helper の type 抽出 guard を `except SystemExit` へ狭める |
| m9 | 診断 helper の reason 抽出 guard を狭める |
| m10 | CLI 診断出力の guard を `except OSError` へ狭める |

**枠 2 — 診断感度 pin (16 件、`DW-M08` の別枠)**

| id | 変異 |
|---|---|
| d1 | normalize 側の診断を空にする |
| d2 | `exception_type` を定数にする |
| d3 | `exc.reason` の代わりに `str(exc)` を入れる |
| d4 | 2 つの callsite を同じ literal に潰す |
| d5 | 例外が無くても診断を 1 件返す |
| d6 | test-registry の診断を空にする |
| d7 | 診断を stdout へ出す |
| d8 | reason 抽出の totality guard を外す |
| d9 | CLI が evaluator 側 callsite の診断を捨てる |
| d10 | reason の長さ判定を `<=` から `<` へ |
| d11 | type の長さ判定を `<=` から `<` へ |
| d12 | reason の受理 charset に `_` を足す |
| d13 | CLI 診断出力の guard を外す |
| d14 | sentinel を受理正規表現に一致する値へ戻す |
| d15 | `_DIAGNOSTIC_TEXT_MAX_LENGTH` を 128 から 129 へ |
| d16 | CLI が `ValueError` の診断を捨てる |

**この結果に至るまでに 4 回の走行が要った。** 1 回目と 2 回目は §3.1 と §3.2 の欠陥で
harness が停止し、3 回目で 2 件が生存して §3.3 を暴いた。4 回目で全件が検出に転じ、
その観測 node を完全集合として登録した本走で 26 件全件 KILLED・完全一致になった。

## 5. 親が実行した検査

- 焦点走 (15 file、計算ノード): **2378 passed / 8 skipped / 赤 0**。
  対象は変更 file の consumer test を参照関係で引いた集合 (`DW-O26`)。
- 変異 matrix: 上記のとおり 26 件全件 KILLED。
- `python3 tools/check_ai_provenance.py`: 各 commit の作成前に message 検査 rc=0、
  作成後に full 監査 rc=0。

## 6. 残余

- 有限個の例外型しか試さないテストは、その型だけを列挙する catch 変異に原理的に勝てない
  (§0 の「主張しない」)。
- `PreregistrationError.reason` の由来と機密性は保証していない。
- gate report CLI と、判定器 CLI の外側 catch が出す `str(exc)` は本 wave の対象外。次の一手へ登録した。
