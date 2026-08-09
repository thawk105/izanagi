# erratum — 機械 `decision` 行は採点器欠陥 (F176) を含む

本書は `output/insights/2026-08-09_t181-certified-rerun/` の認証済み台帳に対する **erratum** である。
台帳の数値ファイル (`aggregate.json` / `verify.json` / `manifest.json` / `apparatus-pin.json` /
`schedule.json` / `verdict*.json` / `run-outputs/*`) は 1 byte も変更していない。
本書は値を訂正するのではなく、**どの値が採点器の欠陥に汚染されているか**を列挙し、
[T-184] が何を使ってよいかを定める。

## 1. 認証は成立している (ただし「pin した装置の下で」)

`aggregate` / `verify` はともに rc=0、`valid=true`、`experiment_complete=true`、
`failure_reasons=[]`、`reader_agreement = {agreed:10, total:10, rate:1.0}` である。
これは `apparatus-pin.json` が pin した装置 sha256 `58f1176e…` の下での replay 認証であり、
本 erratum はその認証を取り消さない。

## 2. 汚染閉包 — s03 の 1 件から 8 個の field へ伝播している

s03 (POS / max) の総括は `**NO-GOです。**` で始まる。当時の採点器は決定語の直後がひらがなだと
抽出しない lookahead を持っていたため抽出 0 件となり、「決定が一意でない」と誤判定して
rc=23 を返した。これが F176 である。結果、s03 は `failure_class="post-treatment"` となり、
`primary_judgment_ledger` の `k` から外れた (`k` は `failure_class is None` の slot だけ数える)。

汚染されている field は次の 8 個である。**「decision 行だけ」ではない。**

| # | field | 台帳の値 | s03 が正常採点されていた場合 |
|---|---|---|---|
| 1 | s03 の score | `valid=false` / `decision=null` / failure reason 1 件 | `true` / `NO-GO` / `[]` |
| 2 | `resource_ledger[s03].failure_class` | `post-treatment` | `null` |
| 3 | `primary_judgment_ledger.max` | `{k:2, n:3}` | `{k:3, n:3}` |
| 4 | `post_treatment_reliability.max` | `1` | `0` |
| 5 | `decision.reason` | `max=2/3 high=3/3` | `max=3/3 high=3/3` |
| 6 | `decision.quality_decision` | `benchmarkまたはmax基準が不安定` | `この6 runでは劣化を観測しなかった` |
| 7 | `decision.pos_adoption_eligibility` | `{max:false, high:false}` | `{max:true, high:true}` |
| 8 | `decision.adoption_eligibility` | `{max:false, high:false}` | `{max:true, high:true}` |

**7 と 8 に注意すること。** 集計は `max_k <= 2 and high_k == 3` の分岐で
**max だけでなく high も不適格**にする。すなわち機械台帳は現在「どちらの arm も採用適格でない」と
言っているが、人手裁定に基づく読みは**その反対**である。
`neg_excluded_arms` が空であることは、両読者の verdict がすべて `findings=[]` であること
(`verdict-log.jsonl` / `verdict-freeze.json` / `revealed-map.json` と `verdicts-*.json` の
join で確かめられる) から従う。`manifest.json.judgments` は `findings` を持たないので、
judgments だけを根拠にしてはならない。

汚染されない field: `experiment_complete`、`decision.row` (`POS_PRIMARY`)、`neg_excluded_arms`、
`reader_agreement`、`new_finding_ledger`、`online_max_escalation_candidate`、
`zero_component_total_only`、`token_usage_observations`、`resource_ledger` の資源数値。

## 3. [T-184] が使ってよいのは人手裁定の側である

**機械 `decision` 行と `primary_judgment_ledger` および両 eligibility を実質的に引用してはならない。**
代わりに、凍結された human-derived の判定を次の join で導く。

```
schedule.json の slots[].slot_id  =  manifest.json の judgments[].slot_id
  group by schedule の {case, arm}
  分母 = その群の slot 数
  分子 = judgments[].r1_detected == true の件数
  併せて judgments[].reader_agreement == true を要求し、
  judgments[].score_input_sha256 で読者が見た出力 bytes を束縛する
```

結果は **POS/high = 3/3、POS/max = 3/3、NEG/high = 0/2、NEG/max = 0/2**、全群 agreement = n。
両読者 (親 + 独立第二読者) は s03 の R-1 を true と裁定しており、一致は 10/10 である。

**許される結論は README が既に定めた範囲まで** — 「この 6 run では劣化を観測しなかった」であり、
非劣性・同等性・採用の証明ではない。この証拠は**段 6 の focused review という工程に限定**され、
他工程へ外挿できない。また [T-184] の依存のうち充足されるのは [T-181] だけであり、
[T-184] 全体の開始可否は [T-180]〜[T-183] の状態による。

## 4. 是正後の装置で旧 manifest を `verify` してはならない

[T-685] の裁定 (b) により **10 run の再走は行わず**、採点器だけを是正した ([T-685] wave)。
是正後の装置は本走時の pin (`58f1176e…`) と別物である。

**旧 manifest を是正後の装置で `verify` / `aggregate` すると、s03 で
`score canonical replay mismatch` が出て `experiment_complete=false` になり、
品質台帳と decision は null 化され、rc=24 になる。**
`_replay_manifest` が `score_run` を再実行して凍結 score と canonical bytes 比較するためである。

これは台帳の無効化ではなく、**装置が変わったという事実の現れ**である。
本台帳の認証は pin した装置の下でのみ意味を持つ。混同しないこと。

## 5. 本 wave での回帰検査 (これは T-181 の行ではない)

参考として記す。**以下は [T-685] wave の是正が正しく効いたことの回帰検査であり、
[T-181] の機械結果を訂正した値ではない。台帳のどの field も置き換えない。**

- 是正後の装置で `run-outputs/s03-POS-max.md` を**再採点**すると rc=0 / `decision=NO-GO` /
  `r1_candidate=True` になる。これは既存の run 出力を採点し直しただけで、再走ではない。
- 他 9 run と歴史 control 2 本の判定は是正前後で不変。
- `apparatus-pin.json` の sha256 は歴史記録として不変のままにしてある (F61)。

## 6. retention — この directory は回帰 fixture になった

`run-outputs/s03-POS-max.md` (sha256 `393df342…`) は、是正後の採点器の
`test_f176_accepts_real_s03_artifact` が **bytes を pin して参照する control** になった。
本 directory を移動・整理・削除する場合は、当該テストが同時に壊れる。
`DW-O09` の閉包にこの辺が増えたことを、以後の凍結 pin 検索で見落とさないこと。
