# n-pilot R33 事前登録の後継 — [T-2154] / D1461

2026-09-09 発行。**先行する事前登録の bytes は 1 つも変えていない。**

## なぜ後継を出したか

n-pilot driver (`orchestrator/campaign/s8b_oracle_n_pilot.py`) の `build_binaries` にある
`build_fn` は build sink でありながら、測定条件の関門族 (D1198) が配線されていなかった。
配線には driver の bytes を変える必要があり、先行する事前登録がその digest を束縛していたため、
条件関門の族一般化 ([T-1999]) は当時この 1 件を繰延べ台帳へ登録して見送っていた。

D1461 (2026-09-02) が「事前登録が driver の digest を束縛している member は、**凍結解除ではなく
後継の事前登録を発行して配線する**」と裁定した。本 dir はその後継である。

先行 wave [T-1981] は同じ束縛に当たって撤去を見送り、「1 byte でも変えると successor 事前登録の
発行が要る。再発行はユーザー裁定に属する」と記録している。D1461 がその裁定にあたる。

## 先行と後継

| | 先行 | 後継 (本 dir) |
|---|---|---|
| path | `output/insights/2026-08-16_t1142-n-pilot-prereg/protocol-r33.json` | `protocol-r33-successor.json` |
| `source.commit` | `73517bc0901ab2e61d11d4593f46151ddbf90526` | `ecf690a26825b0d8d693505c3bb7b842824cbc8f` |
| `source.driver_sha256` | `d447688a39734a292cf5710dbd4656320c45be846b13a995278e083b403a4ab1` | `65527f026d6e3cd55e513938d50d5454de55f562b9a289ce6a55101f03728301` |
| その他の全 field | — | 先行と完全に同一 |

**差分はこの 2 field だけである。** 後継は先行の document を読み込み、この 2 key だけを
上書きして生成した (`json` の deep copy → 2 key 上書き → 全 field の再帰比較で
`source.commit` と `source.driver_sha256` 以外が動いていないことを確認)。
**値を人手で打ち直していない。** 段 3 のレビューが、段 2 プランの手書き転記に 1 文字欠落
(63 桁の `contract_sha256`) を見つけたため、転記そのものを機構から外した。

実験設計 (33 round、2 holdout × 6 configuration、3 allocation、resampling、drift 診断の閾値、
`measurement_declaration`) は先行と同一である。**後継は測定計画を変更していない。**
変えたのは「どの driver bytes に対して回すか」だけである。

## 先行の `source.commit` はこの repo に存在しない

先行が記録している `73517bc0901ab2e61d11d4593f46151ddbf90526` は、この repository の
到達可能な commit ではない (`git cat-file -e` が非 0)。この field は記録専用で実行時には
照合されない — driver が照合するのは job script が観測した repo HEAD と `git rev-parse HEAD` の
一致であって、`source.commit` ではない。そのため今まで誰も踏んでいなかった。

**帰結として、先行が記録している driver digest を歴史 blob から再導出する経路は無い。**
先行側の digest は、テストが literal 定数として保持する形でだけ残る (規律 7 — 当時その bytes に
束縛して事前登録したという事実は、後から再現できなくても事実である)。
後継はこの型を繰り返さないよう、記録する commit が実在し・履歴に含まれ・その時点の driver blob の
digest が記録値と一致することをテストで固定する。

## 起動手順

先行 dir の `r33-qsub-procedure.md` は凍結済みで、先行の protocol を指したままである
(発効後の事前登録は erratum でしか直さない — D1789)。**後継で走らせるときは、
protocol の path を後継へ向ける。** 起動 script 自体の変更は要らない。

`tools/pegasus/oracle_n_pilot.sh` は protocol を環境変数
`IZANAGI_PILOT_PROTOCOL` から解決し、全 mode で `--protocol` として driver へ渡す。
後継で走らせるときは次を渡す (repo root からの相対 path を絶対 path に解決して渡すこと。
script は symlink を拒否する)。

```
IZANAGI_PILOT_PROTOCOL=<repo>/output/insights/2026-09-09_t2154-n-pilot-prereg-successor/protocol-r33-successor.json
```

先行の protocol を渡した実行は、driver の bytes が変わっているので
`driver sha256 が protocol と不一致` で必ず fail-closed する。これは意図した挙動である。

## 配線した関門が実際に何を検査するか (誇張しない)

`build_binaries` は build sink の戻り値に対して
`require_returned_condition_evidence` を無条件に呼ぶ。期待 request digest は freeze の
binding entry の flags から独立に導出し、record 側は `prepared` が実際に材料化した
source tree に対して評価した結果を使う。両辺の出所が違うことが、この関門が恒真でない理由である。

**live 被覆は 12 cell 中 8 cell である。** 実測 (本 wave):

| configuration | cell 数 | 関門対象の macro | 意味の節 |
|---|---|---|---|
| `backoff_fixed_best` | 2 | `BACKOFF_FIXED` | 確立する |
| `ident_all` / `system_gate` | 4 | `BACKOFF_TRIGGER_GATING` | `unestablished` |
| `sort_best` | 2 | `SORT_VARIANT` | `unestablished` |
| `p2_2_flag_opt` / `stock_common` | 4 | なし | — |

- 「要求した define が供給され実効化した」正例検査が実際に走るのは **8 cell**。
- そのうち「実行側の意味」まで確立するのは **`BACKOFF_FIXED` の 2 cell だけ**である。
  残り 6 cell の意味の節は `unestablished` のまま admitted になる。これは D1198 の設計どおりで、
  意味 witness の実装は [T-2153] の backlog である。
- 関門対象の macro を持たない 4 cell では期待 digest が空集合になる。それでも
  record が tuple であることの型検査と digest の等値検査は空集合の早期 return より前に走るので、
  record を持たない戻り値と、freeze が宣言していない macro の record は拒否される。

**「37 macro を守った」とは書かない。** 閉包検査が 37 macro 全件を被覆済みと数えるのは、
この sink に macro の字面が 1 つも無く、戻り値検査を exact な動的被覆として扱う規則によるもので、
実際に評価が走る macro は上表の 3 種である。

## この関門が言わないこと

条件 evidence は「要求した測定条件が供給され実効化したか」しか言わない。
**「その条件で建った binary か」は言わない。** 注入された `build_fn` が正しい record を運びつつ
別の binary を返す経路は、この関門では閉じない。これは build 同一性の問題で、
配線前から存在する注入 seam の性質である (本 wave は受理集合を狭める方向にしか動いていない)。
本 wave の scope 外として裁定パッケージへ送った。
