## 総括

既裁定と絶対規律2を守ったまま、現在の入力で凍結できる spec は**示せなかった**。  
rr5 の較正 artifact は見つかったが `rejected`。accepted 較正を省く合法な mode も無い。  
利用可能な v3 receipt／凍結 spec の実 instance は、下記の内容・gzip・base64 検索では発見できなかった。  
ただし、親の検索方法だけでは不存在の閉包にならず、実 binary の不存在も未証明である。  
**3 spec の同時凍結は不要**。必要入力が揃った1〜2件の先行凍結は両立するが、その具体的な充足例までは示せなかった。

## 反証の試行と結果

以下、repo 内の行番号は HEAD `0600887d92538b3f34d894f9674d202d0a29a578` のもの。

### 1. registered 外に accepted rr5 較正がある

**仮説**

登録 directory の4件だけを調べたため、別 directory の accepted rr5 を見落としている。

**調べた現物**

- `output/env/pegasus/calibration/registered/` の全4 fileを JSON として読み、SHA-256を計算。
- repo 全域の `calibration/v2`、`attestation_profile` 内容検索。
- `calibration/v2` を含む tracked `*.json` を解析し、top-level の較正 artifact を抽出。
- `output/env/pegasus/calibration/attempts/0_995806.nqsv/calibration.json:1604`、`:1696`。

**結果**

通常の tracked JSON では較正 artifact は13 path。内訳は次のとおり。

| 対象範囲 | accepted rr50 | accepted rr95 | accepted rr5 |
|---|---:|---:|---:|
| registered 全4 file | 3 | 1 | 0 |
| 抽出した通常 JSON 全13 path | 9 | 2 | 0 |
| 上段の accepted をSHAで重複排除 | 5 | 1 | 0 |

**rr5 artifact 自体は1件発見した**。ただし `quality.status="rejected"`、理由は `selection-invalid`。accepted への読み替えはできない。

registered 外には `attempts/`、`output/insights/2026-09-10/t2535-certify-offline-fetch/measurement/`、`2026-09-11/t2563-calibration-runtime/{before,after}/` の較正がある。登録 directory が較正全体の閉包ではないことは確認したが、凍結可能性の反証にはならなかった。

### 2. 任意の名前・埋め込み・圧縮・base64 に receipt／spec がある

**仮説**

ファイル名検索や通常の literal 検索から漏れる実 instance が存在する。

**調べた現物・検索語**

母集合は `git ls-files` の24,983 entry。

- 全 tracked 内容を `git grep -a` で検索：
  - `floor-pair-spec/v3`
  - `s8b-binary-admission/v3`
  - `admission_receipt`
  - `closed_strata`
  - `attestation_profile`
- 通常の JSON／JSONL／YAML に対する schema 宣言検索。
- `admission_receipt` にヒットした JSON の object／array を再帰確認。
- tracked `.gz` **1,767件すべて**を展開し、v3 literal と主要キーを検索。
- 上記 schema／キーを連続 base64 化した場合の、3通りのバイト境界に対応する断片を検索。通常の tracked 内容と、gzip展開後の1,767件の両方を対象とした。

**結果**

- `admission_receipt`：178 file。内訳はコード・テスト66、docs 6、insights 105、受入所要台帳1。該当 JSON の再帰確認では **`admission_receipt` をキーに持つ object は0件**。
- `closed_strata`：32 file。コード・テスト4、docs 1、insights 26、受入所要台帳1。
- v3 literal の通常内容ヒットは実装、fixture生成コード、説明文、変異ログ等。利用可能な実 instance は発見できなかった。
- gzip展開後の v3 literal／主要キー検索は0件。
- 通常内容・gzip展開後とも、上記 base64 断片は0件。

したがって、**親の「0件」に対する実 instance の反例は得られなかった**。ただし任意の符号化まで解いた完全な不存在証明ではない。未完了範囲は後述する。

### 3. `attestation_mode` に較正不要の合法経路がある

**仮説**

`none` や legacy mode を使えば、accepted rr5 が無くても凍結できる。

**調べた現物**

- `orchestrator/campaign/calibration_verify.py:80` の `load_verified_calibration` 全分岐。
- `orchestrator/campaign/floor_pair_driver.py:647` の mode parser。
- 同 `:1154` の verifier 呼出し、`:1165` 以降の admission・cell照合。

**結果**

全値域は次のとおり。

| mode | verifier | floor driver |
|---|---|---|
| `required` | v2 schema、env、clocks、clock toleranceを検証し較正を返す | accepted、正整数records、各cellとの署名一致を要求 |
| `none` | 固定SHAの grandfathered v1 bytesのみ受理。`calibration=None` | **明示的に拒否** |
| その他 | 拒否 | parserでも拒否 |

`calibration=None` の拒否は「校正済み動作点だけを測るため」と明記されている。D15（`docs/decisions.md:222`、`:241`）と workload 完全一致（F:1191）も残る。反証不成立。

### 4. 空の artifacts・最小 record・既存 campaign の再利用で閉じる

**仮説**

binary入力を省くか、既存 campaign の receipt を流用すれば rr50／rr95 を凍結できる。

**調べた現物**

- `floor_pair_driver.py:739`、`:818`、`:856`、`:1091`、`:1131`。
- `s8b_binary_admission.py:46`、`:343` 以降。
- `s8b_floor_campaign.py:4587` の発行、`:4855` の受理、`:4921` 付近の portable record 射影。
- `test_floor_pair_driver.py:54` の最小 fixture、`:173` のbinary内容、`:442` のverifier差替え。

**結果**

`artifacts=[]` は拒否。非空pairsとcandidate／referenceの別ID要求により、**少なくとも2 artifact ID** が必要。ただし異なるbinary／receipt fileが2件必要とは限らず、receipt共有も F:1143 が扱っている。

非`sort_best`の最小recordのトップキーは次の12個。

```text
cell_id, holdout_id, configuration_id, binary, binary_sha256,
bin_hash_short, binding, configure_argv, build_argv, cached,
store_path, admission_receipt
```

receipt本体だけでは通らない。内包receiptにはv3 schema、admission、subject、proof、canonical SHAが必要で、binding、compiler manifest、source protectionとの整合も検証する。`sort_best`にはさらに `sort_swo_oracle` が必要。

**再利用経路そのものは存在する。** campaignが作るportable recordは同じvalidatorを使い、floor側は `expected_policy=None` で歴史的recordを検証する。現行policy一致やfloor cell IDへの再束縛を追加要求してはいない。したがって「既存campaign由来だから流用不可」とは言えない。

しかし再利用する実recordを検索で発見できなかった。fixtureは文字列binaryと自己構成証拠を使い、較正verifierも差し替えるため、実入力の代わりにならない。反証不成立。

### 5. 「3 spec」を1件・2件へ減らせる

**仮説**

3件は親の過剰解釈で、少数specだけで要求を満たせる。

**調べた現物**

- D1936 項7：`docs/decisions.md:58154` 以降。
- 事前登録 `:281` の3結果、`:287` の集合閉包、`:291` の窓条件、`:297` 以降の非保証。
- `p3_b4_floor_artifact_issuer.py:1032`、`:1058`、`:1143`。

**結果**

D1936は明文で **workload別3spec** を要求する。issuer自身は非空の期待列を受け取り、件数を3に固定しない。検査するのは各specの2窓と、期待列・summaryの完全一致である。

したがって以下を区別する必要がある。

- **1〜2件を先に凍結し、残りを後から足す**：同時commitの要求はなく、両立し得る。
- **1〜2件の集約をB-4全体の完成とする**：3 workload の対象集合を欠き、不成立。
- **先行結果を見てから残りや期待列を選ぶ**：§5(b)の事前閉包に反する。

先行凍結の余地はあるが、今回それを実現できる完全な入力組は見つからなかった。

### 6. 「凍結 → 較正取得 → 測定」に並べ替える

**仮説**

較正取得を凍結後へ送り、今はspecだけ確定できる。

**調べた現物**

- 事前登録 `:1081`〜`:1085` の手順4〜7。
- `floor_pair_driver.py:647` のcalibration pin、`:614` のtracked bytes照合、`:1131`、`:1154`。
- D1641 決定3：`docs/decisions.md:50335` 付近。

**結果**

手順は **env決定 → PerfConfig校正・成果物化 → 凍結 → campaign**。§11.1全体を無条件に発効済み規範とは扱わないが、現行loaderも独立して較正の実在・SHA・HEAD blob一致・内容の受理を要求する。

較正を後取得にするには、必須pinを仮値や未取得入力への参照にする必要がある。これは今回の凍結定義と規律2に反する。出力pathのleaf未作成許容を、入力calibrationへ転用できない。反証不成立。

## 親 brief と plan の誤り

1. **brief:40〜42 の件数は、registeredを母集合とすれば正しい。**  
   全repoのaccepted較正数としては閉じていない。通常JSONではrr50=9 path、rr95=2 pathを確認した。ただしaccepted rr5の反例は無い。

2. **brief:44 のspec不在の根拠は不十分。**  
   `git ls-files | grep -i floor.pair` は任意の名前を除外できない。今回の内容・圧縮・base64検索でも実instanceは見つからなかったが、元の方法が十分だったことにはならない。

3. **brief:43、:59〜60 のreceiptとbinaryの扱いは限定が必要。**  
   receipt実instanceの反例は発見できなかった。一方、**receipt不在からbinary不在は導けない**。F:1136はbinaryのtracked要件を持たず、本調査も全untracked／ignored binaryの不存在を証明していない。

4. **brief:61〜62 は「完成したspecの凍結」に限定して維持できる。**  
   較正と独立したrecord準備や、充足したworkloadの先行凍結まで不可能と一般化してはいけない。

5. **planに、今回確認した範囲で重大な誤りは無し。**  
   plan:152〜160の母集合・binary要件・先行凍結に関する限定は実コードと一致する。planの登録4件のSHAも独立計算と一致した。§5 floorの`未記入`は事前登録:162で確認した。全行番号の悉皆監査はしていない。

## 数え落としの残余

- 全tracked fileを読み、JSON再帰探索・汎用base64デコードまで行う一括探索は**中断した**。完了件数を出していないため、その走査を閉包の証拠には数えていない。
- Unicode escapeでschema／キーを全面的に隠したJSON、改行・分割されたbase64、二重以上の符号化、gzip以外の任意形式は完全には解いていない。
- tracked archive拡張子の列挙ではgzip 1,767件のみだったが、別拡張子に偽装されたarchiveの全magic検査は完了していない。
- untracked／ignored内容、別branch・過去commitの全blob、submodule内部、repo外のbuild cache・job成果物は探索閉包に含めない。
- 記録されたreceiptを新規作成できるだけの真正な証拠一式が、断片として既存資料に揃っているかまでは完全に再構成していない。

## 本報告が保証しないこと

- 「将来も凍結不能」「正当な新規record準備も不能」という結論ではない。
- accepted表記の確認は、現行verifierによる完全受理の実測ではない。
- loader、pytest、build、較正取得、床値測定は実行していない。
- ファイル作成・変更・commitは行っていない。