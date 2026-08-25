## 所見

### 1. `real` / must-fix — v2/v3 verifier が無関係な実行層を import し、正しい receipt を環境依存で赤くする

新 import 自体は関数ローカルだが、`s8c_acceptance_receipt.py:703-704` から読み込む `s8b_ratified_freeze` は `s8b_ratified_freeze.py:40-50` で floor、環境契約、build admission まで eager import する。

具体的な副作用は次のとおり。

- `freeze_verification_hold.py:43-52`: check-id hash の再計算と `threading.Lock` 生成
- `env_contract.py:375-400`: registry と contract hash の import 時再構築
- `env_contract.py:553-575`: process-local lock 2 本の生成
- `env_contract.py:732,745`: fork callback 2 本の登録
- `s8b_binary_admission.py:32-35` → `s8b_sort_swo_receipt.py:17-25` → `sort_swo_oracle.py:1631-1680,2513-2555`: `inspect.getsource` による別 oracle の source 読取りと hash 再計算
- `s8c_arm_inputs.py:21-22` → `s8b_descriptor.py:16`: 第三者 package `jsonschema` の import
- resolver 実行中はさらに `s8b_descriptor.py:46-51` で schema source を反復読取りする

`_require_ratified_legacy_arm_authority` が捕捉するのは `RatifiedFreezeError` だけ (`s8c_acceptance_receipt.py:706-711`)、resolver 側も `ArmInputError` だけ (`s8c_acceptance_receipt.py:813-823`) である。したがって `jsonschema` 不在、source-less 配布での `inspect.getsource` 失敗、無関係な env/oracle import-time invariant の破れは、正しい v2/v3 receipt に対して `ModuleNotFoundError` や `OSError` をそのまま漏らす。

`layer3_report` は `AcceptanceReceiptError` だけを変換する (`layer3_report.py:617-622`) ため、再検証 API の例外契約も破れる。

成果物影響: 現在の receipt は非 certifying なので既存成果物値は変わらないが、v2/v3 の受理集合が verifier 環境と無関係な oracle source に依存し、将来の accepted Layer 3 report と certified 選択が正しい receipt を参照できなくなる。

修正方向は gate を緩めず、legacy loader と arm 再導出に必要な最小 authority を副作用のない leaf へ分離すること。指定 2 file を超えるため、編集面の再裁定が必要になる。

### 2. `real` / must-fix — 追加テストが cold-import 回帰を構造的に隠している

テスト module 自身が `s8b_holdout_freeze`、`s8b_ratified_freeze`、`s8c_arm_inputs` を top-level で先に import する (`test_s8c_acceptance_receipt_v2.py:15-18`)。そのため production の関数ローカル import (`s8c_acceptance_receipt.py:703-704,811`) は全テストで module cache hit となり、初回 import の失敗、fork callback 登録、source introspection を検査しない。

既存 AST test も trial registry と layer3 の名前だけを見る (`test_s8c_acceptance_receipt_v2.py:245-261`) ため、この巻き込みを検出できない。

成果物影響: CI が緑でも clean process の verifier だけが正しい v2/v3 receipt を拒否し、受理集合と Layer 3 参照が実環境で縮む可能性が残る。

clean interpreter から v2 verifier を呼ぶ test と、無関係な oracle/env module が import されないことを確認する test が必要である。

### 3. `疑い` / nit — fixture の正例が production resolver と shared-oracle になった

fixture は `resolve_arm_input` の結果で期待 receipt を作る (`test_s8c_acceptance_receipt_v2.py:100-110`)。verifier も同じ resolver を使う (`s8c_acceptance_receipt.py:813-824`) ため、resolver が誤って drift しても fixture と verifier が同時に動き、この file 単独の正例は緑を保つ。

ただし repository-wide では `test_trial_registry.py:656-669` が content digest を固定値で pin し、descriptor も手組みしている (`test_trial_registry.py:683-704`)。よって現時点では補助的な検出面があり、must-fix とはしない。

成果物影響: 外部の固定値 control が失われた場合、誤った resolver 出力が標準 verifier の受理集合へ入り、将来の certified 選択が誤条件へ結び付く。現在の成果物値は変わらない。

### 4. `real` / nit — Git subprocess が大幅に増える

`resolve_arm_input` は arm にかかわらず off artifact を検証する (`s8c_arm_inputs.py:434-459`)。descriptor と freeze の各 blobについて `ls-tree` と `show` を実行する (`s8c_arm_inputs.py:336-365`) ため、1 resolver は 4 Git subprocess、六セルで 24 回となる。

fixture はさらに report 用 commit を追加した (`test_s8c_acceptance_receipt_v2.py:153`) ため、旧 fixture 比で 1 実行あたり次の増分となる。

- resolver: `6 × 4 = 24`
- 追加 `_commit_all`: `git add`、`git commit`、`rev-parse` の 3
- 合計: `+27`

この file は parameterize 展開込みで fixture を 18 回使うため、fixture 変更だけで `+486`。新 verifier gate は静的な到達順で resolver 65 回、`+260`。両者で少なくとも `+746` Git subprocess であり、新設 4 test の従来相当 setup まで含めると `+788` 以上になる。

静的見積りは段 4 の 3.5〜5 秒程度と整合するが未実測である。

成果物影響: 値や受理集合は変わらない。CI 上限超過時に検証結果自体が得られなくなるだけなので nit とする。

## 裁定照合

`refuted` — 段 4 裁定との直接不一致は見つからない。

- legacy loader は引数なし (`s8c_acceptance_receipt.py:707`)。subject `repository_root` は渡していない。
- production の新 import はすべて関数ローカル (`s8c_acceptance_receipt.py:703-704,811`)。
- expected `arm_binding_digest` 比較は追加されず、理由コメントがある (`s8c_acceptance_receipt.py:841-846`)。
- 新 gate は v2/v3 のみ (`s8c_acceptance_receipt.py:1121-1126`)。
- `git status --short` は指定 2 file の変更だけ。
- binding の `measurement_head` exact 比較も追加済み (`s8c_acceptance_receipt.py:929-933`)。

成果物影響: 裁定逸脱による値、受理集合、参照の変更はない。

## 指定既存 test の静的判定

`refuted` — 差分そのものによる赤化は確認できない。すべて未実走。

- `test_trial_registry.py` 正例:
  - temp repo に off artifact を作成、commit 済み (`test_trial_registry.py:287-310`)
  - frozen descriptor/digest は再導出値と一致 (`test_trial_registry.py:656-704`)
  - binding に正しい `measurement_head` がある (`test_trial_registry.py:613-646`)
  - verifier 呼出は `test_trial_registry.py:1615-1617`
  - legacy freeze は verifier checkout から読むため subject repo に複製不要
- `test_s8c_acceptance_receipt.py`:
  - fixture は明示的に v1 (`test_s8c_acceptance_receipt.py:97-113`)
  - production gate は v2/v3 限定 (`s8c_acceptance_receipt.py:1121-1126`)
- `test_layer3_report.py`:
  - 実 verifier fixture は v1 (`test_layer3_report.py:320-336`)
  - verifier 呼出は `test_layer3_report.py:355-357`
- `test_reflux_originless_compatibility.py`:
  - receipt は issuer から生成して bytes を読むだけ (`test_reflux_originless_compatibility.py:75-100`)
  - verifier は呼ばない。今回の差分は schema/issuer/serialized bytes を変えない

成果物影響: これら既存正例が保持する受理集合と baseline bytes は静的には不変。

## fixture の帰属と期待値

`refuted` — 既存期待値の変更、反転、緩和、削除はない。

既存負例は新 rederive より先の gate で従来どおり落ちる。

- pairwise collision は parse 時 (`s8c_acceptance_receipt.py:504-523`)
- descriptor divergence、report/run-start/binding digest は `_verify_v2_trial_arm_execution` 内 (`s8c_acceptance_receipt.py:947-980`)
- origin mismatch も rederive 前 (`s8c_acceptance_receipt.py:897-917`)
- C02 欠落は rederive 成功後も最終 gate (`s8c_acceptance_receipt.py:1146-1154`)

成果物影響: 既存負例の赤理由と、それが保護する受理集合は変わらない。

## 揮発値

`refuted` — working-tree hash や固定 commit OID の焼き込みはない。

`introduction` は temp repo で毎回導出し (`test_s8c_acceptance_receipt_v2.py:91-92`)、report、binding、trial へ同じ値を伝播する (`test_s8c_acceptance_receipt_v2.py:114,122,145`)。`"f" * 40` は M4 の不一致 mutant であり期待値ではない。

生成 artifact を変えると commit OID も変わり正例が追随するが、これは所見 3 の shared-oracle 問題であって揮発値の焼き込みではない。

成果物影響: checkout や時刻による固定 OID 不一致で受理集合が縮む経路はない。

## M1〜M5

`refuted` — 不成立の変異はなく、再照準は不要。

- M1: 既存 gate は自己整合した 79 を通し、新 content 比較だけが拒否する (`test_s8c_acceptance_receipt_v2.py:281-313`, `s8c_acceptance_receipt.py:841-845`)。
- M2: extra key は 4-key projection に入らず、key-set gate だけが拒否する (`test_s8c_acceptance_receipt_v2.py:316-343`, `s8c_acceptance_receipt.py:739-782`)。
- M3: extra derangement key は resolver の既存 `.get` 経路に影響せず、exact gate だけが拒否する (`test_s8c_acceptance_receipt_v2.py:346-365`, `s8c_arm_inputs.py:446-452`)。
- M4: report top-level head は保持し binding head だけを変えるため、新比較だけが拒否する (`test_s8c_acceptance_receipt_v2.py:368-387`, `s8c_acceptance_receipt.py:890-933`)。
- M5: loader は既定 `ROOT` (`s8b_ratified_freeze.py:1409-1418`)。subject root へ戻す mutant では、legacy freeze を複製しない既存正例 (`test_trial_registry.py:287-310,1615-1617`) が `legacy-read` 一理由で赤になる。

成果物影響: M1〜M5 は意図した gate を一意に監視しており、mutation harness の誤帰属による受理集合の見誤りはない。

## 総括

must-fix:

1. v2/v3 verifier から env、floor、build、sort oracle への import 連鎖を切り、正しい receipt の受理を無関係な source/package/process 副作用から独立させる。
2. clean interpreter の cold-import test を追加し、現在 top-level test import が隠している失敗面を検査する。

nit:

1. target-local fixture と verifier が同じ resolver を共有するため、独立した固定 authority assertion を加える余地がある。
2. 少なくとも `+746` Git subprocess の所要増。キャッシュまたは六セル一括再導出を検討すべき。

pytest、collect-only、実時間計測はいずれも未実走。静的レビューのみ。