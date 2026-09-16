## 所見ごとの対応表

**全件閉鎖ではありません。前回の10件は closed 9件、partial 1件です。** 以下の節番号は[再レビュー対象稿](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/results/2026-09-16-b7-three-run-materials.md)を指します。

重大度は元の所見の分類です。closed 行の影響欄は、解消された問題を示します。

| 前回の所見 | 判定 | 重大度 | 照合結果・成果物への影響 |
|---|---|---|---|
| A：解析回数 | closed | should-fix | §2.5を「3度」に訂正。列挙した3日付と一致し、1回過少の説明を解消。 |
| A：表の行数 | closed | nit | 限定6を「主表の4行」に訂正。実数4対比較とのずれを解消。 |
| A：`同名 field` | closed | should-fix | §4.2が `attempt_id`、`schema_version`、`request_ids` 等を明記。存在しないキーへの誘導を解消。 |
| A：事前登録§9の無表示省略 | closed | should-fix | compiler版とheader閉包を区別する文を復元。連続4文の引用と一致。 |
| A：事前登録§7の非逐語引用 | closed | nit | 原文の2項目と句点を復元。引用形式のずれを解消。 |
| A：arm別source digestの帰属 | closed | should-fix | §1.4がWALの正確なpathを明記。reservationのrepository/gitlink束縛と区別され、2 digestも一致。 |
| B：限定19の広すぎる採用禁止 | closed | should-fix | 性能値を判断材料に使うこと自体は禁止しないと明記。用途制限の過剰な拡張を解消。 |
| B：A-5限定の欠落 | closed | should-fix | 限定20に事前登録§9の留保を追加。再起動の証拠と誤読する余地を抑制。 |
| B：事前登録§8のidentity実値 | **partial** | **should-fix** | arm別digestは追加済み。しかしjob body digest実値と、事前登録SHAの成果物側／解析規則側の明示は未掲載。**放置すると必須identityの欠落と二つの束縛の混同が下流へ残る。** |
| B：D1631の全体再導出範囲 | closed※ | must-fix | 指摘されたA-2/A-6のraw JSON・WAL未照合は解消。6 cellの標本・正しさと9ファイルのhashを今回も確認した。 |

※最後の closed は、前回が具体的に指摘した「転記済みinsightまでしか遡っていない」という欠落についてです。射影外の裁定原文や、本文が未読と明記するlock等まで再監査したという意味ではありません。

残るidentityの実値は、`reservation.binding.script_sha256` の
`dff913cb1044858b56f25721f2d0aac6539bbcf2a7ddb63b9e6b4bbcac7aecd8`。
事前登録SHAは両側とも `464e3af59a1ef0f776cad022a52ab87e1fdf2709abfc2062c058203bc813719c` ですが、二つの束縛としての説明が必要です。

## 派生値の再計算

raw JSONの6配列と `result.json` の2配列から計算しました。分散は整数で分子を求め、標本分散を  
`(nΣx²−(Σx)²)/(n(n−1))` として平方根を取り、平均で割りました。

| arm | 再計算した標本標準偏差／平均 | WALとの倍精度一致 |
|---|---:|---|
| rr5-stock | 0.03262426529519532 | 一致 |
| rr5-fixed10 | 0.0091676473320761 | 一致 |
| rr50-stock | 0.02928349930898821 | 一致 |
| rr50-fixed5 | 0.010942253518241333 | 一致 |
| rr95-stock | 0.013166532966358306 | 一致 |
| rr95-fixed2 | 0.01173175682351728 | 一致 |
| T-1998 baseline | 0.022721229214372803 | 一致 |
| T-1998 target | 0.012790608817328908 | 一致 |

残りの指定項目も再計算・照合しました。

| 項目 | 結果 |
|---|---|
| A-6の母標準偏差／median | stock **1.1827229019990715%**、fixed2 **1.0559881688105301%**。4桁丸めの1.1827%／1.0560%と一致。 |
| raw JSON・WALのSHA-256 | A-2のraw 4件＋WAL 2件、A-6のraw 2件＋WAL 1件。**9/9件**がmanifestおよび§4.3掲載値と一致。 |
| 2記録以上の標本列 | **8/8 arm、40/40値**が順序込みで一致。A-2は図6、A-6は指定された両READMEとも一致。 |
| correctness配列・traceフラグ | **6/6 cell**でlegacy 1要素、performance 5要素、`performance_trace_disabled_build=true`。 |
| arm別source digest | 登録2 armの`build_start.payload.build_admission.source.source_bytes_sha256`が、§1.4の`2d691b45…239a2c6`／`678b7203…580b12`と全桁一致。 |

T-1998のWALも実hashが `result.wal_sha256` と一致しました。

## 量化の全数確認

- CV一致：**8/8**。外れなし。
- 標本列一致：**8/8**。外れなし。
- raw／WAL hash一致：**9/9**。外れなし。
- correctness反復数・trace無効：**6/6**。外れなし。
- T-1998の`verify_done`：**8 genomeに各1件、計8件**。登録2 armはいずれも`serializable`、`certified=true`、`anomalies=0`、`tag=legacy`。
- T-1998の掲載性能標本：登録2 armの**10値だけ**。残る6 genomeの標本は掲載されていません。
- `result.json`：**23 key**で`correctness`なし。

ただし、§4.2の「3走行」を一括したmanifest照合表現には、次節の例外があります。

## 新しく壊れた箇所

1. **重大度: should-fix — §1.4のfield不存在が直後の説明と矛盾しています。**  
   [188行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/results/2026-09-16-b7-three-run-materials.md:188)はT-1998が`src_token`を持たないとしますが、WALの`build_start.payload.src_token`に実在し、直後のbaseline／target説明もその値を載せています。不存在の対象を`result.json`などに限定する必要があります。  
   **放置時の影響:** 下流が実在するsource identity fieldを存在しないものとして扱い、参照先を誤ります。

2. **重大度: should-fix — §4.2のhash照合範囲が§4.3より広くなっています。**  
   [533行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/results/2026-09-16-b7-three-run-materials.md:533)は「3走行」のraw JSONとWALをraw manifestへ照合したと読めます。しかし§4.3のmanifest照合9件はA-2／A-6の2 attempt分です。T-1998のWALは`result.wal_sha256`との照合で、束縛先が違います。  
   **放置時の影響:** T-1998にも同じraw manifestによる束縛があるという誤った証拠範囲が伝わります。

§2.2・§2.3・§2.4には、再計算で否定される新しい数値、番号ずれ、矛盾する消し残しは見つかりませんでした。

## 入口 README の 1 行

**件数は一致しています。**

| 記載 | 本文を数えた結果 |
|---|---|
| 限定20件 | §3の番号1〜20。欠番・重複なし |
| 3走行 | A-2、A-6、T-1998 |
| 4対比較 | 主表のデータ行4件 |
| 8 arm | 生標本表のデータ行8件、各5標本 |

## 総括

前回所見は**9件closed、identity掲載の1件がpartial**です。加えて、field不存在とmanifest照合範囲の説明に**should-fix 2件**あります。

指定された派生値6項目はすべて原データから確認できました。ファイル変更・測定・テストは行っていません。