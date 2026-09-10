# [T-2027] 消える根の第 2 クラスを manifest schema v3 の根クラスにした (2026-09-01)

D1322 が裁定した根クラス 2 (job 専用作業領域 `/scr/0_<jobid>.nqsv/{gflags,glog}-install/…`
の 7 件) の根相対化を実装した wave の一次資料。**実装そのものの記録は worklog と
decisions 台帳にある。** ここに置くのは実測・裁定・レビュー逐語・変異の証拠である。

## この directory の中身

| file | 内容 |
|---|---|
| `brief.md` | 段 1 brief。親の実測 (M1)〜(M4) を含む。**(M3)/(M4) を「新事実」と書いた箇所は誤りで、段 4 裁定 §0 が訂正している** |
| `s2-plan.md` | 段 2 の実装プラン逐語 |
| `s3-consult-a-firing-and-efficacy.md` | 段 3 敵対相談 A の逐語 (発火条件と実効性のレンズ) |
| `s3-consult-b-accept-set.md` | 段 3 敵対相談 B の逐語 (受理集合と正しさ境界のレンズ) |
| `s4-adjudication.md` | 段 4 裁定。**D1220 の発見と、それによる形 B の不採用** |
| `s6-review-a-accept-boundary.md` | 段 6 敵対レビュー A の逐語 |
| `s6-review-b-call-closure.md` | 段 6 敵対レビュー B の逐語 |
| `s6-review-adjudication.md` | 段 6 レビュー裁定。親の probe による F1 の再現表を含む |
| `mutation-prereg-verification.md` | 実装後の現物に対する単一理由性検査 |
| `mutation-erratum.md` | anchor の一意化と m06 → m06b 再照準の経緯 |
| `mutation-spec-probe.json` | 期待 node 採取用 spec (全件 SURVIVED 期待) |
| `mutation-spec-real.json` | 本走 spec (実測した完全 node 集合を KILLED 期待で登録) |
| `mutation-result.json` | 本走の判定 |
| `probe-d1192-conditions.md` | D1192 統合条件の実測 |
| `probe-cross-job-preimage.md` | job をまたいだ cache preimage の field 差分 |
| `probe-admission-variation.md` | `admission` の leaf ごとの job またぎ差分 |

probe の script 本体は repo 外
(`/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2027-root-class2/`) に置き、repo へ入れていない。

## 実測の要点

**(1) D1192 の統合条件は 4 つのうち 2 つが半分しか満たない。**
「同一 cache entry」と「同一 descriptor」は満たす。「同一拒否述語」はコードの性質としては
同一だが production の lifetime では同一でない。「同一是正 3 択」は集合が同じで効き方が違う。
**親は「remedy になるのは (a) だけで選択は同一」と読んで束ね、段 3 のレンズ 2 本は
「効き方まで同一でなければ 4/4 とは書けない」と読んだ。読みの相違は裁定へ返した。**

**(2) 別 job の cache hit は 2 つの独立した機構で起きない。**
cache identity の preimage は `dependency_prefix` に jobid 入り絶対 path を持ち、
entry directory 名はその preimage の SHA-256 である。加えて
`admission.source.source_root` が job 専用 checkout の絶対 path を 3 箇所で持つ。
実 completion 20 件のうち同一 genome の 5 件 (5 job) で測ると、内容由来の field
(`src_token` / `source_bytes_sha256` / `tracked_diff_sha256`) は job をまたいで一致し、
path 由来の field だけが 5 通りに分かれた。

**(3) これは新事実ではない。D1220 (2026-08-28) が既に限界として記録している。**
親は段 1 でこれを「承認済み裁定の前提を覆す新事実」と書いたが誤りで、段 4 直前の再走査で
D1220 を見つけて裁定を組み直した。**既裁定は機構名で引く** — T 番号や D 番号では出なかった。

**(4) 根解決の過剰必須化は同型の 2 例目だった。**
段 6 レビュー A が見つけ、親が repo 外 probe で 7 ケース再現した。1 例目は根クラス 1 の
実装で起きて着地後の監査が見つけていたが、**F 台帳に登録されていなかったため 2 例目の
設計時に参照されなかった。**

## 主張しないこと

- **cross-job の再束縛が発火するとは主張しない。** D1220 の限界により、別 job の cache entry が
  選ばれること自体が起きない。本 wave が変えたのは耐久記録の中身だけである。
- **床値実測の主経路が緑になるとは主張しない。** 床値 job の実投入はしていない。
- **`dependency-prefix` 根の entry が origin へ帰属することを検証できるとは主張しない。**
  根クラス 1 も同じ弱さを持つ。durable な root commitment は本 wave の射程外で、裁定へ返した。
- 変異 matrix が示すのは、登録した 6 変異が焦点 4 file の範囲で kill されることだけである。
  gate と検査を同じ主体が変更できる限り、意図的な弱体化への完全な防壁ではない (D387)。
