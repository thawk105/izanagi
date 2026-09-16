## 判定

静的検査では、**現実装が帯外 post を publish する経路や、帯内 post を無条件に拒否する不具合は確認できませんでした**。ただし、M02・M04 は変異の具体的な置換方法によって、意図した理由とは別の理由で赤になります。pytest・変異テストは実行していません。

## 変異の帰属

**real / nit — M02・M04 の「赤」を、そのまま供給源の検証成功と数えてはいけません。**

根拠：`orchestrator/calibrator/cli.py:1018`、`orchestrator/campaign/execution_guard.py:370`、`orchestrator/tests/test_calibrator_certify.py:271`。

| ID | 静的に予測される結果と帰属 |
|---|---|
| M01 | 主要高側負例が accepted・publish に進む。pre 自己照合は通り、static 比較は clock を除外するため、新 gate に帰属する。 |
| M02 | **dict を丸ごと逆転すると shape 違反で常時拒否**。高側負例の拒否自体は維持され、spy・sidecar の入力一致 assertion または正例で赤になる。帯方向の検証には帰属しない。**key 形を維持して標本列だけ逆転**すれば、両中央値が 2101 なので主要負例が通り、意図どおり検出できる。 |
| M03 | observed を profile 標本にすると主要負例が通る。新 gate に帰属する。 |
| M04 | **expected の両参照を static_pre に置換すると `tolerance_pct` がなく `KeyError`**。2300 正例だけでなく 2095 正例も拒否され、中央値取り違えへの帰属が成立しない。標本の供給源だけ替え、凍結 tolerance を維持すれば、2300 正例で意図どおり検出できる。 |
| M05 | policy-change で帯判定は True となり、新 reason・sidecar が消える。既存 self reason により拒否は維持されるが、**reason 完全一致 assertion** がこの変異を検出する。 |
| M06 | 主要負例は sidecar を残して accepted・publish に進む。reason 追加の欠落に帰属する。 |
| M07 | policy-change で expected tolerance が 3 となり、新 gate は通る。既存 self reason は残るが、新 reason の欠落を完全一致 assertion が検出する。 |
| M08 | `status` の直後へ移すと accepted のまま reason が追加される。schema は accepted＋非空 reasons を禁止しておらず、主要負例が publish に進む。順序変異に帰属する。 |
| M09 | 帯内正例も rejected になる。過剰拒否の検出に帰属する。 |

M05・M07 は「publish 阻止を新 gate 単独で証明するテスト」ではありませんが、**新 reason の有無を検証するテストとして帰属は成立**しています。先行する self gate は reason を追加するだけで、新 gate の実行を止めません。

根拠：`orchestrator/tests/test_calibrator_certify.py:1780`、`orchestrator/calibrator/schema_v2.py:477`、`orchestrator/calibrator/cli.py:1063`。

## 恒真・恒偽と欠落 key

**real / nit（確認事項）— 正常到達時の shape は正しく、恒真・恒偽への退化はありません。**

新 gate は expected をちょうど 2 key、observed をちょうど 1 key に組み直します。policy が一致する正常入力なら、post 全要素が pre 中央値の帯内にある族は通り、1 要素でも帯外の族は落ちます。policy 不一致なら標本値に関係なく落ちるのは canonical の仕様です。

根拠：`orchestrator/calibrator/cli.py:1018`、`orchestrator/campaign/execution_guard.py:368`。

`profile["effective_clock"]` の key 欠落には、到達時点を区別する必要があります。

- 通常取得時の tolerance 欠落は正常です。CLI が `:883` で追加します。samples 欠落が変換を通過したとしても、`:886` の schema preflight が拒否します。
- **新 gate 到達時点で** samples または tolerance が欠落していれば、`:1019`／`:1020` が `KeyError` を送出します。直前の self 検査は `.get()` を使うため False を返します。
- `:1131` の `except (Exception, SystemExit)` が捕捉し、`attempt-fatal: KeyError` を追加して終了コード 1。壊れた profile のため拒否 artifact の再組立ても失敗すれば、`:1166` で捕捉して stderr に記録します。**拒否ファイルが残らない可能性はありますが、publish には進みません。**

根拠：`orchestrator/calibrator/cli.py:587`、`:883`、`:1131`、`:1155`、`orchestrator/calibrator/schema_v2.py:600`。

## 既存 gate の到達性と数値検算

**real / nit（確認事項）— 指定された既存 reason は、いずれも到達不能になっていません。**

`within-run-cv-invalid` と `post-attestation-mismatch` は新 gate より前に追加され、self reason も維持されます。`effective-clock-policy-changed` は、新 gate 通過後から publish 直前までに policy が変われば到達します。既存テストは `token_hex` 呼び出しでそのタイミングを作っています。

根拠：`orchestrator/calibrator/report.py:121`、`orchestrator/calibrator/cli.py:1015`、`:1073`、`orchestrator/tests/test_calibrator_certify.py:995`。

数値を独立に検算すると、次のとおりです。

| case | 中央値・帯・判定 |
|---|---|
| 主要高側負例 | pre 中央値 2101、2% 幅 42.02、帯 **2058.98–2143.02**。2110 は帯内、3079.456 は帯外。 |
| post-self-pass | post 自己照合は中央値 2300、帯 **2254–2346** で通る。pre→post は 2300 > 2143.02 で落ちる。 |
| policy-change | pre/post とも中央値 2101、凍結 2% の帯内。diagnostics は `band_pass=True`。しかし **2.0 != 3.0** のため `policy_matches=False`、canonical は False。 |

static 比較は effective clock 全体を除外するため、post-self-pass の 2300 は `post-attestation-mismatch` を起こしません。policy-change では旧 self gate も同じ policy 不一致で落ち、期待された 2 reason が成立します。

根拠：`orchestrator/calibrator/cli.py:516`、`orchestrator/campaign/execution_guard.py:381`、`:405`。

## sidecar の書込みと再計算

**real / nit（確認事項）— sidecar 書込み失敗から publish に進む経路はありません。**

`_write_exclusive` の open・write・flush・fsync 例外は外側の `:1131` に移り、拒否処理後に 1 を返します。部分ファイルは残り得ます。

staging は `os.mkdir` で新規確保し、既存 attempt は開始前に拒否します。同一フローに同名 sidecar の先行 writer はありません。外部から同名ファイルを作られた場合も `O_EXCL` が拒否し、同じ例外経路になります。

根拠：`orchestrator/calibrator/cli.py:303`、`:835`、`:1027`、`:1131`。

判定に必要な **expected・observed・照合時 policy** は全部あります。指定 canonical 実装を用いる限り、再計算に不足する値はありません。`json`・`effective_clock_policy`・canonical 関数を読み込んだ環境で、手順は次の 3 行です。

```python
s = json.loads(sidecar_bytes)
effective_clock_policy.EFFECTIVE_CLOCK_TOLERANCE_PCT = s["policy_at_comparison"]
assert effective_clock_comparison_passes(s["expected"], s["observed"]) is s["passed"]
```

根拠：`orchestrator/calibrator/cli.py:1037`、`orchestrator/campaign/execution_guard.py:324`。

## 合格時の published bytes

**real / nit（確認事項）— 同じ既存入力について、合格時の bytes 不変はコード経路から成立します。**

新 gate は profile・result・receipt・genome を変更せず、合格時は reasons にも追加しません。`_assemble_v2` の入力、`indent=2 / ensure_ascii=False / sort_keys=True`、末尾改行は変更されていません。post 情報は失敗 sidecar にだけ入り、`notes` を含む artifact field に混入しません。

根拠：`orchestrator/calibrator/cli.py:753`、`:1018`、`:1047`、`orchestrator/calibrator/report.py:72`。

ただし正例の bytes assertion は「公開先＝同 attempt の calibration.json」を検証するだけで、変更前との比較ではありません。不変性の根拠は上記のコード経路です。

根拠：`orchestrator/tests/test_calibrator_certify.py:1738`。

## gate 削除後にも成立する assertion

**real / nit — 個々の assertion には非識別的なものがありますが、新設負例テスト全体は gate 削除を検出します。**

以下は先行 assertion の失敗による実行打切りを除き、各 assertion を個別評価した場合です。sidecar 読込み以降は、削除後にファイルが存在しないため評価できません。

| 新設 test | gate 削除後も成立する assertion |
|---|---|
| `rejects_high_outlier` | `calls == [0,1,2]`（`:1674`）。さらに `candidate.json` 不在（`:1680`）は、成功 publish 後に calibration.json へ rename されるため成立する。 |
| `accepts_using_dynamic_pre` | **全 assertion**（`:1733`–`:1745`）。これは M09 などの過剰拒否を検出する正例。 |
| `rejection_mechanisms` 全 case | `calls == [0,1,2]`（`:1774`）と `candidate.json` 不在（`:1786`）。 |
| 同 `post-self-pass` | 上記に加え、post 自己照合の True（`:1755`）。 |
| 同 `bad-cv`・`policy-change` | 上記に加え、`rc != 0`、status rejected、registered 不在、publish.json／published-self-comparison.json 不在（`:1773`、`:1783`–`:1786`）。既存 gate だけでも拒否するため。 |

`bad-cv`・`policy-change` でも、新 reason を含む **reasons 完全一致**（`:1780`）は削除後に失敗します。したがって「既存 gate が落とすから新テストも緑のまま」という結論にはなりません。

## 総括

- must-fix：**なし**。指定 scope の現実装について、受理集合・公開 bytes・参照を誤らせる不具合は確認できませんでした。
- 帰属不成立：**M02 の dict 丸ごと逆転、M04 の expected 全参照置換**。shape／欠落 key による拒否です。標本供給源だけの置換なら成立します。
- land：**条件付き**。M02・M04 の具体的な変異定義と検出理由を区別して記録すること。実走結果は未確認です。