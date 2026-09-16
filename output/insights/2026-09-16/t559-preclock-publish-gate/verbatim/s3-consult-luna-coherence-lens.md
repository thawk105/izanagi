## 1. publish 前照合は実効があるが、T-559 全体の閉鎖は名乗れない

**real / scope 内（名乗りの修正）。根拠：brief:7–10,59–67、plan:30–36、`cli.py:1006,1017,1033,1067`、`certify_calibration.sh:955–963`。**

新 gate が失敗すると registered の作成前に return するため、CLI 内で取得した post 標本について「publish 前照合を課す」は実効を持つ。名乗りだけの gate ではない。

ただし、外側の `attestation-post.json` は CLI 成功後に取得され、その標本を照合する処理は wrapper にない。T-559 原文の「外側の post probe は publish より後に走り、publish を取り消さない」（`verbatim-T559-entry250.md:2–4`）という窓は残る。裁定済み逐語（`verbatim-T559-entry944.md:1`）は観測源を限定していないので、外側まで充足したとの断定も、CLI 内照合では裁定を全く満たさないとの断定も強すぎる。

成果物には次の **1 文**が正確：

> CLI 内で benchmark 後に取得した post clock と凍結 pre profile の canonical 照合を publish 前に実装したが、benchmark 中および CLI 終了後の外側 `attestation-post.json` の clock は本 gate の検査対象外である。

さらに brief の下流効果の説明は広すぎる。D155 は「この gate が守る範囲は CLI publish 経路だけ」「『登録済み較正を守る』とは書けない」と明記する（`verbatim-D155.md:16–18`）。新規 publish が登録済み契約へ自動的に選択される構造でもない（`env_contract.py:253–279,601–624`）。

## 2. published bytes 不変は条件付きで成立する

**real / scope 内。根拠：plan:93–100、`cli.py:752–771,1039–1067`、`schema_v2.py:553–569,585–600,776–790`。**

成立条件は次のとおり。

- 比較前後で、凍結 `profile` の標本・順序・型・tolerance を変更しない。
- `result_to_dict(result)` の全出力、receipt、genome、schema version を同一に保つ。
- 合格時の `status="accepted"` と空の `reasons` を維持する。
- JSON serialization の設定と末尾改行を維持する。
- post 情報や診断を artifact の既存 field にも混入させない。

exact keys 検証は新 field を拒否するが、既存 `notes` 等への情報追加による bytes 変更まで防ぐものではない（`report.py:72–83`、`schema_v2.py:798`）。また、保証できるのは **同じ既存入力に対する bytes** であり、別の実測 attempt 同士の一致ではない。

提案 sidecar は公開 bytes の外にある。CLI は `attempts/<safe-job-id>` を staging とし（`cli.py:831–834`）、registered へ渡すのは `_assemble_v2` が返した `artifact` のみである。ディレクトリ全体を publish する処理ではない。

**attempt staging の consumer は実在する。** 例えばテストが `rejection.json` を読む（`test_calibrator_certify.py:836,907`）、公開後 receipt を読む（同 `:1178–1180`）、staging と published の bytes を比較する（同 `:1624`）。一方、確認した契約 consumer は registered の明示 path/hash を読む（`env_contract.py:606–624`）。wrapper の `ATTEMPT_DIR` は別の `job-staging` namespace である（`certify_calibration.sh:50–54`）。

登録済み Pegasus 2 件は `env_contract.py:263–266` と `:276–279` の固定参照であり、この変更が既存 artifact・参照・loader を変更しない限り、その束縛への直接波及はない。ただし事前登録文書と pin 対象 bytes は射影外なので、**pin 自体の整合を検証済みとは言えない**。新規コード差分から更新必須になる経路が見当たらない、という判断までである。

## 3. D191・D218・D155 との衝突は確認できない

**疑わしい（衝突の主張は支持されない） / scope 内。根拠：plan:11,34,68–89、以下の裁定逐語。**

| 裁定の逐語 | 判定 |
|---|---|
| D191 決定2「benchmark 後の既存 gate は削除しない」（`verbatim-D191.md:7`） | plan は既存 late self を残すため整合する。 |
| D191 決定3「publish の直前に…policy 定数と一致する…独立に検査」（同 `:8–9`） | `cli.py:1044` の検査を残すため整合する。新 gate の policy 判定で代替してはならない。 |
| D191 決定5「early 拒否の成果物には…評価されなかった検査の一覧」（同 `:13–15`） | 新 gate を未評価一覧へ追加する方針は整合する。逐語から late sidecar の義務までは導けない。 |
| D218「別 process の verifier と、その判定を最終 receipt へ束縛する完全形は実装しない」（`verbatim-D218.md:8`） | 同一 process の失敗診断 sidecar はこの完全形に当たらない。ただし独立検証の証拠とは名乗れない。 |
| D155「probe の観測者効果の是正は実装せず、ユーザー再裁定へ返す」（`verbatim-D155.md:23`） | 既存標本を加工せず、追加 probe・除外・許容緩和を行わない plan は是正を先取りしていない。 |

F108 の「計算ノードでの因果は未立証」（`verbatim-F108.md:21`）も維持すべきである。brief の外側 post の合格例は、CLI 内 post の実測到達性や observer effect の解消を証明しない（brief:54–61）。

## 4. 指定された行番号はほぼ正確

**real / scope 内（参照精度）。根拠：plan:5,7,104,146–149 と実ファイル。**

| plan の参照 | 実際の内容 | 照合結果 |
|---|---|---|
| `cli.py:1006` | `static_post` 取得 | 一致 |
| `cli.py:1017` | status 決定 | 一致 |
| `cli.py:1044` | publish 前 policy 検査 | 一致 |
| `cli.py:1079` | 公開 bytes 再読 receipt 呼出し | 一致 |
| `cli.py:81` | early 未評価一覧の late self 項目 | 「付近」として一致 |
| `test_calibrator_certify.py:40` | 同一覧の期待値 | 一致 |
| 同 `:253` | `_pegasus_shaped_probe` 定義 | 一致 |
| 同 `:1153` | 空行 | 挿入位置の「付近」としては妥当。既存テスト定義の参照なら `:1155` |
| 同 `:1570` | `"2.0", "100.0"` の parametrization | 一致 |

指定 9 箇所に重大な行ずれはない。なお brief の `env_contract.py:263–277` は 2 件目の hash がある `:279` を含まない。

## 5. 主要負例の帰属は妥当だが、spy は判定への依存を証明しない

**real / scope 内。根拠：plan:106–136、`cli.py:515–519,735–746,1014–1017`、`test_calibrator_certify.py:253–287,367–375`。**

主要負例は pre 全標本が帯内で、post だけを帯外にする。48 cores の receipt 修正と正常 benchmark stub を使用すれば、既存 self・static・品質 gate による別理由の拒否は静的には見当たらない。未変更実装には新 reason を生成する経路がないため、plan:122 の **reason 完全一致**は未変更実装で通らない。

6 行の変異対策の評価は次のとおり。

| plan の対策 | 静的評価 |
|---|---|
| 帯内正例・probe 回数 | 恒偽化と追加 probe を検出できる設計 |
| post 全体を 2300 にする負例 | post 自己照合・expected の post 化を検出できる設計 |
| static pre のみ 2300 にする正例 | static pre の取り違えを検出できる設計 |
| 低側帯外値 | 上側だけの検査を検出できる設計 |
| 帯外 post ＋ bad CV | 両 reason を要求すれば上書きを検出できる設計 |
| canonical へ委譲する spy | 呼出しと入力は検査できるが、**戻り値が受理判断を支配することは証明しない** |

最後の行には、canonical を正しい入力で呼びながら戻り値を捨て、別途 `diagnostics["band_pass"]` 等で判定する変異が生き残り得る。通常入力では同じ結果になるため、入力記録だけでは区別できない。canonical の実体は `cli.py:47–50` の import と `execution_guard.py:324–337` にあり、単なる性質検査より強い配線検査ではあるが、**呼ばれることと判断に使われることは別**である。

既存の診断偽装テスト（`test_calibrator_certify.py:924–965`）は early 拒否で終了し、新 cross gate に到達しない。新 gate の canonical 戻り値への依存を判別するテスト条件が必要である。変異の実走結果ではなく、静的な検出力評価である。

## 6. early 未評価一覧の変更は 4 箇所の既存 assertion に届く

**real / scope 内。根拠：指定コード 7 ファイルへの `rg`、`cli.py:898,789–793,1123,1134`。**

production 定数だけを変更すると、次の完全一致 assertion が不一致になる。

- `test_calibrator_certify.py:841`
- `test_calibrator_certify.py:959`
- `test_calibrator_certify.py:1237`
- `test_calibrator_certify.py:1454`

いずれも同ファイル `:34–45` の `_EARLY_CLOCK_NOT_EVALUATED` を共有するため、plan の期待値定数 1 箇所の更新で追随できる。`:40` は唯一の consumer ではなく、共通期待値の定義位置である。

射影内には別の独立期待値や production consumer は見つからなかった。**射影外を読むことは禁止されているため、リポジトリ全体で他にないとの網羅保証はできない。**

## 7. 不変条件 2 は保守的な制約であり、監査性の欠落とは分けるべき

**real / scope 内（brief の論拠と成果物説明）。根拠：brief:37–38、plan:70–83,98–100,138、`cli.py:765–770,1079–1096`。**

既存登録 bytes と pin を保全することは必要だが、そこから「将来の同一入力の accepted artifact も必ず旧 bytes と一致しなければならない」は導けない。後者は schema 改訂を避けるための、今回の保守的な自己制約である。今回の実装条件としては守れるが、pin 保全に不可欠だという説明は強すぎる。

監査性の欠落は実在する。plan は失敗時にしか post 入力を保存しないため、成功 artifact と既存公開後 self receipt から **成功時の pre→post 判定を再計算できない**。同じ published bytes は gate 導入前にも生成され得る。

ただし、これは bytes 不変条件だけの必然ではない。**「成功時には比較証拠を残さない」という plan の追加選択**による。既存の公開後 self receipt 自体も staging に置かれている。

成功時の証拠保存・束縛まで保証対象にするかは、現 plan の失敗時診断を超える **裁定パッケージ候補（scope 外だが real）**。本レビューでは実装拡張を提案しない。

## 総括

- **real / scope 内：名乗りが広い。** CLI 内 post の publish 前照合は実効を持つが、外側 post と登録済み契約全体の保護は保証しない。
- **real / scope 内：spy の変異検出力が不足。** canonical 呼出しを残して戻り値を無視する変異を区別できない。
- **real / scope 内：成功時の監査証拠がない。** bytes 不変は条件付きで成立するが、成功した cross 判定は成果物から再計算できない。

**plan を実装してよいか：条件付き。** 名乗りを CLI 内 post に限定し、canonical 戻り値への依存を検証条件に加え、成功時の証拠と射影外 consumer／pin が未検証であることを明記すること。静的検査のみ実施し、ファイル変更・テスト実走は行っていない。