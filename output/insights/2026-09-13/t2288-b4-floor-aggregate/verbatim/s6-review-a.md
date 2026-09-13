## must-fix

以下、`I`＝[issuer](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2288-impl/orchestrator/campaign/p3_b4_floor_artifact_issuer.py)、`T`＝[追加テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2288-impl/orchestrator/tests/test_p3_b4_floor_artifact_issuer.py)、`F`＝[floor_pair_driver](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2288-impl/orchestrator/campaign/floor_pair_driver.py)。判定は静的検査であり、pytest・変異検査は実行していない。

**所見1: spec 間の全出力 path 非共有を、追補にない受理条件として追加している。**

根拠: I:1049、1061–1064。各 spec 内の出力 path 相異は既存 F:1271–1274 の条件だが、新実装はこれを**異なる spec 間**にも拡張している。例えば、summary 出力は別々で、各 summary が自己の spec の窓・層・標本を完全に報告していても、二つの spec が同じ window artifact path を宣言すると `aggregate_output_reuse_error` になる。これは、期待列に対する summary 閉包の欠落・重複とは別の条件である。指定追補 (b)・(c) にこの要求はない。

成果物への影響: 明示期待列と全 summary の閉包が一致する入力でも発行・v2 読込を拒否し、集約成果物の受理集合を契約より狭める。

推奨対応: spec 間の包括的な path 非共有 gate を除く。既存の spec 内相異検査、summary path 重複拒否、期待 spec と summary の一対一対応は維持する。

**所見2: 公開経路の正例と主要負例がなく、閉包・再構成の検査を無効化しても追加テストが検出できない。**

根拠: T:823 は `FloorPairSpec`、T:913 は検証済み summary オブジェクトを直接構築する。T:1020 の三入力正例は内部合成関数まで、T:1153 の発行正例は publisher の直接呼出しまでである。公開 API を呼ぶ T:1087 は期待 pin の形式不正で止まり、T:1068 の loader 負例は schema／必須欄で止まる。

具体的には、I:1174 の「期待 spec に対応する summary が欠落した」検査や、I:1278 の再構成結果との比較を削除しても、これらの追加テストはその変更点へ到達しない。親裁定 `s4-adjudication.md:81` が要求する「3 spec → 発行 → resolver → 材料レポート」の正例も存在しない。

成果物への影響: 最大値を持つ入力の欠落による floor 低下や、成果物側の非保証・出所改変の誤受理を、回帰テストが見逃す。

推奨対応: 登録済みの公開経路正例を追加し、それを基に期待列固定での source 欠落、自己整合した値改変、非保証脱落、単体有効な identity 不一致、不正 member 混在を作る。各停止 code を固定する。実行環境の制約とは別に、テスト自体が未作成である点を解消する。

## 所見 (nit)

**所見3: `aggregate_empty_stratum_error` は公開経路では到達不能な重複検査である。**

根拠: I:639 は各 stratum の値列を非空とし、I:651–660 は実 samples との対応を要求する。I:1091 の閉じた層集合一致を通った後では、各 stratum に retained sample が必ず存在するため、I:1134 の `retain_count == 0` は成立しない。

成果物への影響: この分岐を除去しても公開経路の値・受理集合・参照は変わらないため、nit。

推奨対応: 独立した有効 gate として数えない。空層の負例は既存自己整合検査で停止すると記録する。

**所見4: 追補の実装対応はあるが、事前登録本文への転記は未完了である。**

根拠: `docs/phase3-b4-reflux-ablation-preregistration.md:237` の直後は依然として `PerfConfig` 欄であり、指定追補はない。差分も issuer とテストの二ファイルだけである。

成果物への影響: 実行時の floor 値は変わらないが、参照する事前登録本文に集約規範が掲載されない。ここでは実装バグと混同せず nit とする。

推奨対応: 親の残作業として明記し、裁定済みの位置・逐語で反映する。実測や §5 値セル記入まで進める必要はない。

## 負例の到達段階の判定

`s3-lens-sol.md` 所見9の表と照合した。以下の「到達」は**コードから判断した到達性**であり実走結果ではない。内部関数テストは、Git・較正・凍結 spec の公開 admission を通した証拠にはならない。

| 追加負例（T の行） | 到達段階・判定 |
|---|---|
| window `missing`（938） | 一窓は残るため既存非空検査を通り、I:1081 の window 閉包不一致へ到達 |
| window `extra`（938） | 形式上有効な ID。I:1081 へ到達 |
| window `duplicate`（938） | 既存 window 行検証には重複検査がなく、I:1081 へ到達 |
| window `campaign`（938） | campaign 本体を変えず window 行のみ変更。I:1081 へ到達 |
| window `path`（938） | canonical な別 path。I:1081 へ到達 |
| partial `derivation`（959） | samples と strata を同時削除。同一値なので最大も整合し、I:1091 へ到達 |
| partial `campaign`（959） | sample 分割は維持。I:1119 の当該窓への射影照合へ到達 |
| partial `cell`（959） | I:1097 へ到達。ただし dataclass 差替えであり、変更 spec の hash／較正 admission は迂回 |
| sample `missing`（977） | 対応 values も一件削除し、I:1108 の完全分割へ到達 |
| sample `extra`（977） | index 20 は既存の非負整数検査を通り、I:1108 へ到達 |
| sample `overlap`（977） | dropped の一行を retained index に変更。I:1108 の非交差検査へ到達 |
| `sample-count`（977） | I:1110 の dropped sample 件数へ到達 |
| `record-count`（977） | I:1111 の dropped record 件数へ到達 |
| `campaign-count`（977） | I:1123 の campaign 件数へ到達 |
| `stratum-count`（977） | I:1130 の stratum 件数へ到達 |
| `threshold`（977） | 型検査を通り、I:1138 の閾値文字列比較へ到達 |
| `fraction`（977） | 有効な分数形式のまま、I:1136 の再計算値比較へ到達 |
| `admissible`（977） | bool 型検査を通り、I:1139 へ到達 |
| statistics（1011） | `difference_formula` 変更なので既存 upper-function 検査には掛からず、I:1146 へ到達 |
| identity `env_tag`（1058） | I:1187–1189 へ直接到達。単体有効な公開入力ではない |
| identity `protocol`（1058） | 同上。receipt からの導出は再実行しない |
| identity `threads`（1058） | 同上。較正束縛は再実行しない |
| schema `unknown`（1068） | I:1348 の `artifact_schema_error`。再構成の証拠ではない |
| schema `v1-as-v2`（1068） | I:1262 の `authority.aggregation` 欠落。detail も assert |
| pin 空列（1087） | I:1036 の期待列非空条件 |
| pin 重複（1087） | I:1046 の期待 path 重複条件。summary 閉包検査ではない |
| pin `../`（1087） | I:1043 から path 検証で停止 |
| pin 大文字 hash（1087） | I:1044 から hash 形式検証で停止。hash 実体照合ではない |
| pin 一要素（1087） | I:1040 の pair 形状検証で停止 |
| CLI summary のみ（1103） | 集約必須引数不足で停止 |
| CLI output-dir 欠落（1103） | 同上 |
| CLI expected-spec 欠落（1103） | 同上 |
| CLI 二モード併記（1103） | argparse の相互排他で停止 |
| CLI 旧モード＋expected-spec（1103） | aggregate 専用引数混入条件で停止 |
| CLI 旧モード＋output-dir（1103） | 同上 |
| 整合済み過剰欠測（1126） | 件数・分割を整合させており、I:1140 の `3 * 20 > 40` へ到達 |
| 既存出力への再発行（1153） | I:981 付近の create-only publisher へ到達。ただし公開集約 API の再発行ではない |

各追加負例は例外型だけでなく code を assert している。CLI は終了値と診断文言も確認する。上表の内部負例について、「手前の別検査で赤になるだけ」という誤照準は認めなかった。

一方、所見9で挙げられた nonmax／rounded ratio、公開 spec 閉包、窓数、不正 member、source 改変、非保証脱落、invalid aggregate → report は未作成である。API 引数の存在を確認する T:1170 は、期待列が実際に独立使用されることの証拠にはならない。

## 追補との対応表

| 条項 | 実コードでの対応・判定 |
|---|---|
| (a) 保守側最大・1以上拒否 | I:669、675、736–740 で summary 内の最大を再導出し、I:884 → 835 で全 member の `floor < 1` を要求。I:1202 が `Fraction` 最大を選ぶ。平均・中央値・最小・clamp・切詰めへの公開経路は認めない |
| (b) 独立期待列・閉包・全件拒否 | I:1153 が呼出し側期待列を先にロード。I:1163 の実 pin と I:1164、1174 で比較。窓・層・標本の実側は document、期待側は spec。入力を除外して続行する catch／filter はない。ただし所見1の追加制限と所見2の証拠欠落あり |
| (c) 窓数・identity・和集合 | I:1059 で各 spec が二窓。従って窓数は全入力で一致。I:1187 が env／protocol／threads の一致、I:1191、1196 が workload／campaign の和集合 |
| (d) 全出所・exact 値・非保証 | I:1217–1223 が全 source の summary/spec pin、ratio、hex、section/items を保存。非最大入力も残る。平坦な非保証では重複文言も維持 |
| (e) create-only | I:1255 が既存 `_publish_create_only` を使用。既存 target に対する link が失敗し、削除・上書き・代替名への再試行はない |
| (f) 非保証 | I:42–50 に明記。F:910 は `sample_count >= 1`、F:919 は非重複だけ。n=62・24時間分離の追加機械検査はない |

閉包検査は恒真ではない。セル被覆は、層一致後には「spec の pair 配置が全セルを覆うか」という追加検査になるが、F:1060 の既存参照検査は未使用 cell を禁止しないため、これも恒真ではない。恒真になるのは所見3の空層分岐である。

loader の期待列は I:1277 で成果物内の記録から受け取る。この点は親裁定が明示的に許容した境界であり、発行 API の期待列を summary から導出する循環とは区別した。source と期待列を共に変更して外側 pin も更新する攻撃は、既存の採用責任として残る。

## 実装子の報告への反証

**所見5: 「機構単位の確認」という報告は妥当だが、独立期待列・再構成を確認した証拠には拡張できない。**

根拠: `s5-impl.md:54`、66–70 は内部テストの限界と公開経路未完了を明記しており、この自己申告への反証はない。ただし T:823–836 の spec は、JSON document の `windows` を更新せず別途構築した窓を持つ。さらに `orchestrator/tests/test_floor_pair_driver.py:166` の較正 payload は `{}` であり、この正例をそのまま実体 admission の正例にはできない。

成果物への影響: 報告の限定を外して受入証拠に使うと、所見2の値・参照の回帰を検出できない。報告自体は限定しているため、本項は nit。

推奨対応: 「内部関数の静的到達性」と「公開経路の成立」を引き続き分け、所見2を完了する。

ほかの報告事項は差分と整合する。

- 追加は15テスト関数。既存テスト・decorator・期待値の変更、反転、緩和、skip、削除はない。
- `issue_authoritative_floor`、`load_floor_pair_summary`、`_authority_value`、publisher、v1 定数・命名は不変。loader の v2 分岐追加後も v1 本文は維持される。
- CLI 本文は変更されているが、旧 `--s`〜`--summary` の省略形と反復時の最終値採用を壊す追加オプションはない。v1 成果物 bytes を変える変更は認めない。
- 追加 fixture に現行 checkout hash の差込みや揮発 payload の焼込みは認めない。合成 payload の hash 計算はあるが、凍結検証を通した証拠ではない。
- pytest 未実走という報告は、そのまま未実走として扱った。

## 総括

最大演算・値域拒否・独立閉包照合・全入力保存は、公開コード上は保たれている。  
契約にない spec 間 path 制限と、公開経路の正負例未作成を must-fix とし、段5完了は承認しない。  
静的レビューのみ実施し、編集・commit・pytest・変異検査は行っていない。