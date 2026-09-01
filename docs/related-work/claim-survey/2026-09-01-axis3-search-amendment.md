# 2026-09-01 — 軸 3 文献検索の構造的完走条件 amendment (凍結)

- **作成日:** 2026-09-01 (規約適合した後継物として凍結した日)
- **内容起草日:** 2026-08-28 (本文の起草日。旧稿は main へ一度も着地していない)
- **入力 commit:** `dcf9224a1` — 本文を導いた起点であり、本文書を凍結した commit ではない
- **入力 digest の所在:** 下記 input path 群の内容は入力 commit `dcf9224a1` の Git blob そのものであり、
  blob OID がその digest である。索引の実測値だけは repo の外にあり、endpoint・取得日・
  観測した field 名で束縛する。**本文書自身の SHA-256 は
  `orchestrator/related_work_search.py` の `FROZEN_AMENDMENT_SHA256` が持つ**
  (本文書はこの値を literal で持たない — 自己 hash 循環を作らないため)
- **入力 path:**
  `docs/related-work/claim-survey/2026-08-27-axis3-search-preregistration.md` (旧登録) /
  `docs/related-work/claim-survey/2026-08-27-axis3-index-measurements.md` (索引実測) /
  `docs/related-work/claim-survey/2026-08-27-axis1-search-execution.md` (参照した実行記録) /
  `docs/related-work/README.md` の「7.7 主張軸別の調査状態と、不在主張の成立条件」 /
  `docs/decisions.md` の
  「D1183. 複数窓にまたがる取得は機械可読な再開点を残す」・
  「D1206. 索引が版番号を返さない場合は代替の来歴で固定してよい」・
  「D1207. 完走述語の構造的な不成立は宣言的除外でなく契約の改訂で閉じる」・
  「D1208. 凍結物への注記は後継物で行い、届かない残余は限界として明記したうえで充足と認める」・
  「D1209. 判定資料の階層が行ごとに違う属性欄は、集計と行間比較を一般に禁じる」
- **文献 cutoff:** 旧登録 §2 の暦年境界 **2026-12-31** をそのまま引き継ぐ。変更していない
- **規則の正本:** `docs/related-work/README.md` の
  「7.7 主張軸別の調査状態と、不在主張の成立条件」
- **改訂の根拠:** D1207。再開点は D1183

> **凍結物である。** 旧登録と旧索引実測は 1 byte も変更しない。
> 本文書は旧登録の語・枝・cutoff・除外を取り替えず、構造的に成立しなかった完走条件と
> query identity だけを後継化する。実行値は repo 外 raw bundle と別の実行記録が持つ。
> **この文書に検索結果を書き戻してはならない。**
> 進行中の可変状態の正本は `docs/worklog.md` の末尾エントリであり、ここではない。

## 0. 判定

旧登録の 1543 主 query ID は本 amendment で supersede する。旧 ID では preflight も本走も行わず、
応答を後継 ID へ再利用しない。後継主 query は arXiv 360、OpenAlex 10、DBLP 1523 の計 1893 本である。

これは旧結果を見た後の意味的 amendment である。直接の入力は、軸 1 実行で観測した
要求件数 field のこだま、OpenAlex の正規化主キー重複と `meta.count` の差、arXiv の結果窓である。
軸 3 自身についても旧登録前の query-equivalent pilot 8 本の cardinality を親が見ている。
取得結果から語、10 枝、cutoff、包含、除外、判定語彙を変更してはいない。

**軸 3 は `RW0` のままである。** 本 amendment は検索を 1 本も完走させず、世界の不在を支持しない。

## 1. query ID の後継集合

### 1.1 arXiv — 10 枝を 36 個の非重複年 shard へ写す

旧 `AX3-Q<n>@arxiv` (`n=1..10`) は次の 36 ID へ写す。

```
AX3A1-Q<nn>-S<YYYY>@arxiv    nn = 01..10, YYYY = 1991..2026
```

各 ID の検索ブロック、field、page size、位置遷移は旧登録と同じで、日付閉区間だけを
`submittedDate:[YYYY01010000 TO YYYY12312359]` とする。36 区間は旧登録の
`[199101010000 TO 202612312359]` を、同じ minute 精度の字句領域で gap 0・overlap 0 に分割する。
実行前の validator が全 10 枝についてこの exact cover を再導出する。

単年 shard の preflight が索引の結果窓を超えた場合、その ID を `blocked` とし本走しない。
結果を見て runner 内で細分化せず、別日付・新 ID の後続 amendment へ送る。

### 1.2 OpenAlex と DBLP — 一対一の新 ID

OpenAlex は `AX3-Q<n>@openalex` を `AX3A1-Q<nn>@openalex` へ写す。filter、field、cutoff、
page size、cursor 遷移、期待 AST は旧登録と同じである。

DBLP は旧 `AX3-Q<枝>-<語ID>-<語ID>@dblp` 1523 本の先頭を `AX3A1-` に替える。
語の直積、前方一致の連言、page size、offset 遷移、cutoff の client-side 判定は変えない。

### 1.3 control・lookup・補助経路

旧登録の control 41 stream と補助経路 188 streamにも `AX3A1-` namespaceを与える。
`C-ANCHOR` は旧10枝でなく、本節の後継主 query の索引別和集合を検査する。
229 は logical stream 数である。resolver、retry、page、同一 request の共有を含む wire attempt 数ではない。

主 query 1893 と非主 logical stream 229 の計 2122 行を registration catalog へ必ず accounting する。
補助経路の opaque ID は、request、exact response locator、0 件・複数件・field 不在時の停止を
registration seal で先に固定した resolver だけが補う。人が応答を見て候補を選ばない。

## 2. 完走と代替来歴

完走述語、索引固有 work ID、work-family、意味的 amendment、page 単位の
「版が取得不能な場合の代替来歴」は 7.7 の一般規則だけを正本とし、ここへ複製しない。
本 amendment 固有の field locator は次のとおりである。

| 索引 | 実要素 | 索引固有 work ID | 宣言総数 |
|---|---|---|---|
| arXiv | namespace 付き XPath `/atom:feed/atom:entry` | `/atom:feed/atom:entry/atom:id`。URL の末尾 ID から `vN` を落とす | `/atom:feed/opensearch:totalResults` |
| OpenAlex | JSON Pointer `/results` の配列要素 | `/results/<n>/id` の OpenAlex work URL を `W...` へ正規化 | `/meta/count` |
| DBLP | JSON Pointer `/result/hits/hit` の配列要素 | `/result/hits/hit/<n>/info/key` | `/result/hits/@total` |

OpenAlex は全 occurrence を record 台帳へ残し、distinct work ID を `meta.count` と照合する。
異なる work ID が同じ DOI / arXiv 主キーへ写っても取得時には削除せず、work-family 層へ送る。

**旧登録 §7.1 条件 1 (解釈照合) は 3 索引すべてに適用する。** 本 amendment はこの条件を
supersede しない。arXiv は `/atom:feed/atom:title`、DBLP は `/result/query` が返す解釈後クエリを
正規化後の文字列一致で照合し、OpenAlex は `/meta/x_query/oql` を部分文法で構文解析した AST 一致で
照合する。**解釈照合は旧登録 §7.1 条件 0 (request 一致) と独立であり、互いに代替してはならない**
(D1123)。旧索引実測は arXiv の `feed>title` と DBLP の `result.query` の echo を
6 syntax class すべてで観測しており、この条件は実装可能である。

## 3. 二段 preflight と実行順

1. **registration preflight (network 0):** amendment、2122 行の catalog、旧1543 ID の全被覆、
   年 shard、OpenAlex parser の正例 7 / 負例 6、schema、実行器、argv、入力 commit を検査し seal する。
2. **live preflight:** 固定済み request を送り、全行を `ready` / `unavailable` / `blocked` として記録する。
   応答を本走の page 0 へ再利用しない。resolver・availability・retryを含む wire attempt を数える。
3. **本走:** `ready` 行だけを arXiv → OpenAlex → DBLP、各索引内の新 ID 辞書順で実行する。
   `unavailable` / `blocked` を母集合から消さず、軸全体は `未完走` とする。

最初の外部 request は固定した `AX3A1-L-ID-01@openalex` である。HTTP 429 の場合はその 1 request の
代替来歴と `Retry-After` を保存し、他 request を送らず checkpoint する。HTTP 200 は
`transport_available` を意味するだけで、anchor の `lookup_resolved` とは別に判定する。

20 万 request 上限は resolver、availability、preflight retry、本走 retry の全 wire attempt に適用する。
30 暦日は最初の外部 request から数える。利用可能性や件数を理由に検索式・除外を変えない。

**registration seal が束縛するのは、封印対象として列挙した closure の bytes である** — amendment、
catalog、source、schema、OQL fixture、argv/phase contract、入力 commit における各 input path の
blob。**repository 全体の HEAD 一致を受理条件にしない。** 記録を commit すれば HEAD は必ず動くため、
HEAD 全体を条件にすると seal が発行と同時に再利用不能になる。Python interpreter の版と依存
package の版は**来歴として記録するが受理 gate に入れない** — 無関係な環境更新で seal が腐るためである。

**外部 request 前の全test・docs・provenance緑はmanagerのrelease gateであり、実行器自身が
acceptance receiptを検証する機械関門ではない。** managerはこの順序を守り、未受入codeからlive CLIを
起動しない。production成果物はcanonical CLIの`--live` sessionだけが発行する。bundle validatorが
保証するのは、seal済みphase argv・live session marker・requestごとのone-shot send receipt・WALの
構造的一貫性までであり、CLIを起動した主体の人間性や因果性を証明しない。

## 4. 中断と再開

checkpoint は 7.7 と D1183 に従う。action は排他的な tagged union とし、cursor の出所になった
entity body digest、committed ledger prefix digest、直前 checkpoint digest、registration seal、
catalog / parser / runner / schema digest、期限、wire attempt、次回送信可能時刻を持つ。
応答と ledger prefix の commit が確定していない状態では自動的に次 page へ進まない。

**D1183 が要求する 2 本の完全 request を、action の選択によらず常に両方保持する。** すなわち
cursor 継続用の完全 request と、独立 pass 開始用の完全 request を同じ checkpoint に併置し、
どちらを実行するかは `action` だけが決める。**選ばれなかった側の request を欠落させてはならない。**
`state` と `action` の合法な組は表として固定し、表にない組を拒否する。
**`restart_branch` は枝の先頭 (arXiv `start=0` / DBLP `f=0` / OpenAlex `cursor=*`) だけを指し、
次 offset への継続の別名にしてはならない。** 継続は `continue_cursor` である。

WALはraw受領と意味commitを分ける。transport return直後のentity body/header/requestは
`response_received`として先に永続化し、required field・OQL・lookup判定を通った後だけ
`response_committed`へ進む。**`response_received` は応答を受領した時刻を持つ。** 送信前に記録する
intent 時刻は request の意図時刻であって取得日時ではなく、7.7.4 が求める取得日時としては使わない。
finalizationはhash chain末尾の`bundle_finalized/v1` markerをcommit recordとし、
marker後のcrashではrequestを再送せず、report/result・ledger・親preflight digestへidempotentにfoldする。
retry可能な429/503 tailはmarkerを持たない`in_progress`として残す。

D1183の5 actionはschema語彙として保持する。ただし本実行器が自動生成・実行するresume actionは
`continue_cursor` / `restart_branch` / `not_applicable`に限る。`start_independent_pass`と
`blocked_on_ruling`のproducer/executorは本amendmentの実装scope外であり、schema受理をE2E保証に数えない。
**この scope 制限は、上記の「2 本の完全 request を常に保持する」義務を免除しない。**

## 5. D1209 と取得後の境界

将来のrecord判定は `evidence_tier`、入力 locator、`tier_validation_id` を持つ。tier が混在する列の
無差別集計と行間比較を拒否し、別途妥当化した tier 別解析は拒否しない。本実行器は取得とraw来歴までを
担当し、tier enforcementとwork-family個別裁定は実装しない。取得件数をそれらの完了へ読み替えない。

本 amendment と取得器は record の取得・来歴・resume までを扱う。一次資料の全件分類、alias / work-family
の個別裁定、補助経路との感度監査、RW3/RW4 判定、不在表現は後続作業であり、取得件数から代用しない。

## 6. 限界

- 年 shard は API 全体の恒久的な結果窓や snapshot を証明しない。単年でも超過すれば本走しない。
- 3 索引とも snapshot token を持たず、同数入れ替えを構造的に排除できない。
- registration seal と checker は同じ repository の同じ主体が変更でき、意図的改変への完全な防壁でない。
- production markerはcanonical live sessionとの構造的一貫性を固定するもので、CLI起源の人間性や
  remote attestationを証明しない。同一UIDがsource、private state、全WAL frame、manifest、validatorを
  一括して整合改変する攻撃は保証範囲外である。**canonical CLI process の private state
  (session の receipt 台帳、module 内の connection alias) を直接操作する Python 呼び手も、
  この保証範囲外に含まれる。** 実装が塞ぐのは、呼び手が自分で production を名乗る自己申告の経路である。
- **本 amendment に対応する実行器は、登録段までの実行器である。** DBLP 題名 lookup と
  補助経路 188 stream の resolver は未実装で `blocked` として catalog に accounting され、
  control の評価器も未実装である。**未評価の control は完走を主張しない** (fail-closed)。
  live 本走にはこれらの後続実装と、その時点での再登録が要る。
- **arXiv が同一 work ID を頁境界で 2 回返し、宣言総数では 1 回だけ数える事象**が軸 1 の実行で
  観測されている。本実行器は再出現を完走拒否として扱う (厳格側)。この扱いを維持するかは
  人間裁定に属し、裁定が付くまで軸 3 の live 本走は開始できない。
- 後継物、7.7 の規則、claim-survey README の 3 導線で注記を届けるが、旧凍結物だけを開く読者へは届かない。
- 旧登録の「母集合の外」と cardinality pilot 後の登録という限定はすべて残る。
