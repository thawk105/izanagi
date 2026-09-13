# 段 4 裁定 — A-1 sizing 証明書と本走 policy の凍結

裁定 inbox を段 4 直前に再走査した。local main は a551cdd30 のままで、wave 開始後の更新はない。

## 採用する real 所見 (scope 内)

### R1 — sized policy の bytes が module pin されていない (sol 所見 1)

`_policy_identity` (`orchestrator/campaign/paper_story_a1_paired.py:1015-1016`) は sized study に対して
policy hash を `None` で返す。`validate_policy:1703-1708` と `load_policy:1724-1726` は
`expected_policy_sha is not None` を条件に検査するため、sized では policy bytes の pin が発火しない。
親が実装と実測で確認した (pilot は `V3_PILOT_POLICY_SHA256`、v2 は `POLICY_SHA256` を持つ)。

**成果物影響:** これが無いと、README の hash を変えないまま disk 上の sized policy の
`schedule_root_seed`・出力先 path・`sizing_inputs` の証明書参照を差し替えても loader を通る。
本走の物理順と束縛先が凍結後に変わりうる。

**採用する形:** 既存機構の対称適用。`V3_SIZED_POLICY_SHA256` を追加し `_policy_identity` から返す。
新しい gate 機構は作らない。

### R2 — 十進文字列の受理で float 側の正値・有限条件が落ちる (luna 所見 1、sol 所見 4)

`_positive_decimal:1252-1261` は `Decimal` 上の正値・有限だけを見る。
`Decimal("1e-999")` は正だが `float(...)` は `0.0` になる。現行 sized 分岐 (`:1477-1485`) の
`_finite_number` は float の有限性を見ているので、素朴に文字列受理へ替えるとこの条件が消える。

**成果物影響:** `k` が 0 になる policy を受理すると区間半幅が 0 になり、`planned_sigma_tps` が 0 なら
variance plan の判定が壊れる。受理集合が広がる。

**採用する形:** sized 分岐で `_positive_decimal` に加え、元の値の `float()` 変換が有限かつ正である
ことも要求する。変換が例外になる値は拒否する。

### R3 — 十進文字列の受理そのもの (plan 変更面 1)

証明書の `planned_sigma_tps` は生成側 `.17g` の十進文字列であり、JSON 数値へ落とすと
`Decimal(str(float))` が別の値になる。親が独立に再現した。

| workload | 証明書 | float 化後の str() |
|---|---|---|
| write-heavy | 66403.452108019716 | 66403.45210801972 |
| balanced | 56697.435713574683 | 56697.43571357468 |
| read-heavy | 74668.489566274948 | 74668.48956627495 |

`k` (= 2.8315526875186725) は round-trip するので影響しない。

**成果物影響:** この修正が無ければ、本番の証明書と一致する sized policy を書けない。本 wave の
完了判定 (c) が達成できない。**したがって本題の本体実装であって追加防壁ではない。**

### R4 — D1452 の consumer 側照合 (plan 変更面 2、luna 所見 7)

裁定 D1452 は「反復数と候補格子を決める道具の受理範囲を、sized certificate と consumer が
事前登録の値と照合する形へ直す」と決めている。証明書側は既に記録している
(`policy.search.trials` / `policy.certification.trials` / `policy.candidate_grid.registered_minimum` /
`.maximum` / `policy.root_seed.digest`)。consumer 側が未実装である。

sol が構成した反例を採る: 証明書の `candidate_grid.maximum` を 4096 → 4095 に変えても、
実現候補列は `30,40,…,4090` のまま変わらず、既存 consumer は n/df/k/sigma だけを見るので受理する。
つまり登録外の候補範囲で選んだ証明書が通る。**照合は恒真ではない。**

**成果物影響:** 無いと、事前登録と異なる試行回数・候補範囲・root seed を申告した証明書で
本走の反復数を決められる。事前登録の拘束が実効を持たない。

**採用する形:** 期待値は事前登録 §5.4/§5.5 の literal (20000 / 100000 / 28 / 4096 / root seed digest) を
consumer 側の定数として置き、型込みで exact 比較する。**道具側は一切変更しない。**
差し込み位置は luna 所見 7 に従い、既存の workload 検査の**後**とする (既存の拒否理由の優先順位を保つ)。

### R5 — schedule 原像は「pilot 後・本走前の新規選定」と書く (sol 所見 2)

本走の 3 つの `schedule_root_seed` とその導出原像は、今回新たに選ぶ値である。
pilot の観測を見た後に選べる位置にあるため、「pilot 前から凍結済み」と書いてはならない。

**成果物影響:** 誤った凍結時点を書くと、事前登録の前向き性の主張が事実と食い違う。

**採用する形:** sized 事前登録 README に、原像 literal と導出規則を書き、
「pilot 完走後・本走投入前に新規に凍結した」と明記する。pilot の TPS・選ばれた n・実現順序を
理由に別の原像へ引き直さないことも書く。

### R6 — 親の所要時間の一般化は誤り (sol 所見 8、nit)

親は brief に「本番値でも数分」と書いたが、実際は 0.36 秒だった。原因は 3 workload とも
最初の候補 n=30 で認証を通り、候補格子を 1 件だけ評価して停止したためである
(証明書の `candidates` 長 = 1、`selected.order_index` = 0)。試行回数に単純比例しない。
記録側で訂正する。凍結済み設定を変える理由には使わない。

## refuted (採らない)

### (P1-3) `authority.formal=true` — 採らない。選択の余地がない

親が実装で確認した。`orchestrator/campaign/ident.py:48-51` と
`orchestrator/campaign/wal.py:120-124` はいずれも sized study
(`paper-story-a1-20260901-balanced5-sized-v1`) を A-1 非認証 lane の exact identity 集合へ入れており、
`ident.py:66-67` と `wal.py:144-146` が独立に `formal is False` と
`promotion_prohibited is True` を要求する。`formal=true` にすると campaign identity 検査で落ちる。

したがって sized policy は `formal=false` / `promotion_prohibited=true` /
`final_estimate_eligible=true` の組で凍結する。後者は「本走の観測値が登録済み解析の対象になる」
という意味であり、投入認可でも正式昇格でもない。これを README に明記する。

### 30 対がどこかで 60 に固定されている — refuted

`paper_story_a1_paired.py:1762` の `group_count = reps // 10` を親が確認した。30 対なら 3 組・
対ブロック 6 本・arm ブロック 12 本・各先行 3 本になる。受領証は `2 * reps` を要求する。
luna が driver / pipeline / loop / wal / ident / job script を数え上げ、sized を 60 対へ固定する
検査は見つからなかった。pilot 側の 60/12/6 は sizing の入力設計なので `sizing` block に保つ。

### driver を変えると pilot の測定と証明書が無効になる — refuted

replay receipt が束縛する source は生成側と検証側の 2 つの道具であり、driver は含まない
(親が receipt の `sources` を実物で確認した)。規律 7 のとおり、現行コードとの差だけでは
記録済みの測定を無効にしない。ただし sol が指摘した「変更後 checkout での同じ raw bundle の
再 materialize は現行 bytes 同一性に依存する」は既存制約として真であり、本 wave は再 materialize を
使わない。

### 本 wave が規律 2 を緩める経路を新設するか — refuted

新設しない。変更は sized 統計値の型・証明書の登録値照合・policy pin に限られ、
`verify-not-certified` と anomaly 検査、bench 前の correctness gate に触れない。

## scope 外 (裁定パッケージとしてユーザーへ返す)

**sized 本走の実行面は未完了である。** 本 wave は実装しない。完了報告に「本走が起動可能になった」と
書かない。luna が数え上げた未整備箇所:

- `paper_story_a1_paired.py:7077-7079` — source contract の study / attempt 一致を無条件要求し、
  エラー文も pilot attempt-0004 を名指しする
- `orchestrator/campaign/paper_story_a1_source.v1.json:3-4` — contract 自体が pilot study と attempt-0004
- `tools/pegasus/paper_story_a1_paired.sh:1362-1372` — 依存 source staging と
  `--third-party-source-root` の付与が pilot 限定
- `paper_story_a1_paired.py:2194-2195` — source amendment の 4 file を binding へ加えるのが pilot 限定
- 同 `:4811`、`:4954`、`:5170-5181` — amended source の contract 照合と configure argv 受理形の差

これは「2 箇所の限定解除」ではなく、source 参照集合と build 証拠の受理形を sized へ揃える課題である。

## (P1) の確定

| 項目 | 確定 |
|---|---|
| P1-1 (D1452 を scope に入れる) | **採る** (R4)。裁定済み項目であり仮想リスクではない |
| P1-2 (置き場) | **採る**。ただし dir 名は `output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/` とする (現行の配置規約に従う) |
| P1-3 (formal=true) | **採らない**。実装が `formal=false` を強制する |
| P1-4 (新規 schedule seed) | **採る**。導出原像を README へ前向きに登録し、R5 の但し書きを付ける |
| P1-5 (本走専用の出力先) | **採る** |

## 変異事前登録 (DW-M01、実装前登録)

実装後に、各変異の赤理由が一つに絞れること (前後・内側の層が同じ入力を拒否しないこと) を確認する。

| ID | 変異 | 期待 kill node |
|---|---|---|
| M1 | D1452 照合の `search.trials` 期待値を `20000` → `19999` | search-trials の負例 |
| M2 | D1452 照合から `candidate_grid.maximum` の項を削除 | maximum の負例 |
| M3 | D1452 照合から `root_seed.digest` の項を削除 | root-seed の負例 |
| M4 | sized 分岐の float 側正値検査 (`> 0`) を削除 | underflow (`1e-999`) の負例 |
| M5 | `_policy_identity` の sized 戻り値を `V3_SIZED_POLICY_SHA256` → `None` へ戻す | policy bytes pin のテスト |

## gate の禁止 (署名) と通る正例

**禁止:** sized policy は、次のいずれかに当たる sizing 証明書を受理しない。

```
certificate.policy.search.trials              != 20000
certificate.policy.certification.trials       != 100000
certificate.policy.candidate_grid.registered_minimum != 28
certificate.policy.candidate_grid.maximum     != 4096
certificate.policy.root_seed.digest           != "e72bc005d156caea2c89085c563c72fa04bbeb4afd98160fca968da9a7f6b3b3"
```
いずれも型込みの exact 一致 (bool・float・文字列化した整数は拒否)。

**通る正例:** 本 wave が生成した証明書
`sha256=41d041963c8f3a175b5501810f52ab2619d9285f6f1eeb176790698131fc8299`。
上の 5 値は順に 20000 / 100000 / 28 / 4096 / e72bc005… であり、`status=selected`、
3 workload とも `selected.n=30` / `df=29` / `t_critical=2.8315526875186725` である。

## プラン v2 (段 5 の実装単位)

実装子 1 本。所有 path は次の 3 つだけ。

1. `orchestrator/campaign/paper_story_a1_paired.py` — R1・R2・R3・R4 と 2 つの事前登録 pin
2. `orchestrator/campaign/paper_story_a1_paired.v3-sized.json` — 新規
3. `orchestrator/tests/test_paper_story_a1_paired.py` — 新規・改訂テスト

親が担う: 証明書と replay receipt の最終配置、sized 事前登録 README の本文、
hash の確定順序、worklog / decisions / phase3、commit、受入、land。

## 凍結順序 (親)

1. 証明書を最終 path へ byte 同一で配置する。
2. 最終 path を引数にして replay receipt を作り直す (候補 receipt は path を記録しているので流用しない)。
3. README を凍結する (policy の hash は書かない)。
4. README の sha256 を driver の 2 pin と policy の `preregistration` へ入れる。
5. policy bytes を凍結し、その sha256 を `V3_SIZED_POLICY_SHA256` へ入れる。
6. 親が `load_policy(V3_SIZED_STUDY_ID)` と関連テストを実走する。
