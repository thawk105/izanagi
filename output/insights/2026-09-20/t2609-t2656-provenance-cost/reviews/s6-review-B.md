## レンズ B

静的検査では、判定・findings・rc・受理集合を変える実装欠陥は確認できませんでした。patch をメモリ上で逆適用して AST を比較し、**既存関数・テストの期待値変更なし、新規テスト関数26本**を確認しました。pytest・変異試験・性能測定は実行していません。

以下、`checker` は `tools/check_ai_provenance.py`、`tests` は `orchestrator/tests/test_check_ai_provenance.py` を指します。

### must-fix

なし。

### should

なし。成果物の変化を立証できない指摘は、指定に従い nit としました。

### nit

**N1. 「`--range` は従来」の射程を親取得に限定して明記する。**

- **根拠:** `s4-ruling.md:37,40`、`checker:2077–2079,2113–2125`、`tests:7311–7344,8688–8705`。
- **成果物への影響:** 固定 message・環境では判定差なし。ただし ancestry のある `--range` でも、実装面 commit の repo parser 呼出しが2回から1回になる。
- **是正案:** 「親・path 取得は authoritative 限定、values 共有は ancestry のある両経路」と報告に明記する。指定の既存計数テストは `%s`・`%B`・`log` を数えており、parser 回数は固定していないため矛盾しない。段4の(a)と(d)をこの読み方で解釈すれば実装は整合する。

**N2. consumer 列挙に、checker 改版による初回 cold 費用の説明が足りない。**

- **根拠:** `checker:2344–2358`、`dev_wave_land.py:3555,3569–3583`、`s5-author.md:66–73`、`s4-ruling.md:19–22`。
- **成果物への影響:** 受理集合は変わらない。既存受領証を再利用できない初回全史走が480秒を超えれば、監査結果を得る前に land が失敗する。
- **是正案:** author 報告に「checker SHA256 が環境 digest に入るため、旧版の全 partition の受領証は新版では再利用できない」を追加する。段4は cold 比較を要求しているが、この失効理由を明記していない。brief 訂正と相談Bには改版直後の cold への言及がある。

  親の実測記録には、固定 tip、新旧 checker の blob／bytes SHA、cold の成立理由、実行場所、worker 数、wall・CPU・ピークメモリ、rc・出力比較を残す。480秒との比較では、監査本体と、dispatch の待ち・準備・回収を含む呼出し全体を区別する。timeout 自体の変更は段4の scope 外。

**N3. 同じ構築元から導かれる冗長な検査と、重複実行するテスト部分がある。**

- **根拠:** `checker:1655–1664,1987,2011–2021`、`tests:8576–8605`。
- **成果物への影響:** 現行 caller では削除しても判定・findings・rc は変わらない。
- **是正案:** `parents.keys() != index.keys()` は両方が同じ `rows` の `row[0]` から作られるため冗長。parser の `result.keys() != set(requested)` も、全見出しから辞書を作り `headers == requested` を確認した後では冗長。削除可能だが、主要コストではない。

  `test_batch_merge_keeps_combined_diff_contract` 冒頭の既存テスト本体呼出しは、既存の acceptance assertion を再実行する。その部分だけなら fixture 構築へ分離できる。ただし後半の batch 注入と `--cc` 呼出し比較には新規検出力があり、**テスト全体の削除対象ではない**。

### scope・受理集合・fail-closed の確認

| 対象 | 静的評価 |
|---|---|
| `_parse_path_batch` | `checker:1644–1665`。非空要求への空 stdout、終端不正、空 token、見出し順・件数不一致を拒否。最終 commit 後の40／64桁 hex path も検査する。 |
| `_batch_nonmerge_paths` | `1668–1680`。取得要求だけ重複除去し、失敗時は辞書全体を破棄。空要求は subprocess なし。 |
| merge 設定 gate | `1683–1691`。両設定の rc=1 の場合だけ有効。その他のrc、指定4例外は無効化へ戻り、stdout/stderr は捕捉される。例外漏れや新しい公開診断は確認できない。 |
| merge 親 batch | `1694–1714`。親番号ごとに独立取得し、同じ親OIDでも slot を統合しない。結果は全 slot 成功後だけ返す。後半失敗時の先行結果公開なし。 |
| `_Ancestry.parents` | `2011–2026`。閉包全体を保持し、閉包外親・不正OID・重複行・順序不正等では親表全体を破棄。既存 ancestry 計算を置き換えていない。 |
| `_commit_paths` の2引数 | `1773–1791`。`parents` と `parent_paths` は(a)(c)に対応する必要な注入点。`None` と空 tuple を区別し、intersection → `--cc` は不変。 |
| values 共有 | `1482,1614,2077`。`[]` を再parseしない。oracle は値を注入せず従来のparseを通る。 |
| 選択・順序 | `2590–2635`。receipt／correction 後の最終 selected から取得し、worker には元の selected を渡す。重複監査と `pool.map` の結果順を維持する。 |

各部は plan v2 の(a)〜(d)に対応しており、scope 外の一般化はありません。ただし、**480秒達成に全最適化が個別に必要かは未証明**です。段4:25 が候補別 ablation を見送っているため、その証明を今回の必須修正にはしません。

見出し検査だけでは、正しい見出し間で path が取り違えられた出力を検出できません。しかし指定 argv でそのような出力になる具体的条件は確認できませんでした。実 Git の完全出力比較は、non-merge の空 root／中間／末尾を `tests:8389–8416`、merge の親 slot 対応を `8534–8566` で検査します。`--always` が全見出しを出す前提では、OID型pathは余剰見出しとなり全体fallbackします。

CR／CRLF の変換は両経路とも `_git` の `text=True`（`checker:1194–1206`）を通ります。non-merge の衝突を含む比較は `tests:8419–8433`。merge も同じ decode → set → intersection → `--cc` を使い、新版だけ別の正規化を行う箇所はありません。

patch の hunk は validator・取得 helper・ancestry・監査への注入に限られます。`main`、dispatch 判定、`authoritative` 述語、`--force-dispatch`、受領証の bindings／publish 本体への変更はありません。

### テスト品質・変異分類

26本のうち、**既存テストと完全重複し、新規検出力がない関数は確認できませんでした**。既存 fixture の再利用や同じ出力の比較でも、新しい取得経路・fallback・呼出し契約を検査しています。部分的な重複はN3のとおりです。

- 現行 checker hash、tree hash、固定 tmp path の焼込みはありません。OIDは実 Git で生成しています。`'f' * 40` 等は破損／hex名の試験データです。
- 成功時の出力比較は実 Git を通します。stub は破損・例外・config rc の注入等に使われており、成功時の等価性を偽の Git 出力だけで証明していません。
- `_path_oracle_audit` は今回の取得・values共有を避ける経路です。ただし独立した旧版 checker そのものではなく、親担当の固定全史比較を代替しません。

| 変異 | author の分類の評価 |
|---|---|
| M-1／M-2／M-3 | 契約差で妥当。親tuple・fallback・argv／見出しを固定する。 |
| M-4 | 判定差で妥当。部分辞書を使うと先頭の実装author違反が消える。 |
| M-5 | 契約差で妥当。提示fixtureでは主に全体fallbackを固定しており、判定差killとは言い切らない。 |
| M-6 | 判定差で妥当。設定を無視すると gitlink merge が受理から拒否へ変わる。 |
| M-7 | 判定差＋契約差で妥当。先行空集合の利用で違反が消え、全親legacy呼出しも失う。 |
| M-8 | 判定差で妥当。混在message・重複selectedにより欠落／author findingが変わる。 |
| M-9 | 契約差で妥当。空値の再parse回数を検出する。 |

これらは静的な期待killの評価であり、実測killではありません。

consumer の静的列挙は、変更対象の棚卸しとしては十分です。一方、「callerを変更していない」だけでは CLI・rc・stdout 契約の実証にはなりません。land の bytes／blob照合はそのまま有効で、改版に伴う主な未記載事項はN2です。

### subprocess 数・メモリの見積もり

設定gate通過・全batch成功・親表有効を仮定すると、提示された計測内訳から消える呼出しは次のとおりです。

| 種類 | 削減数 |
|---|---:|
| `show %P` | 11,308 |
| non-merge `diff-tree` | 7,061 |
| merge `diff` | 8,502 |
| repo `interpret-trailers` の重複parse | 2,224 |
| 合計 | **29,095** |

残りは **24,502 + batch数 + config 2回**です。内訳は repo parser 11,769、隔離parser 11,315、`--cc` 1,418。batch数は通常 `1 + 最大親数` で、最大2親なら計24,507回。提示6種類の旧計53,597回に対して約54%減ですが、**wallの54%減を意味しません**。pool前の逐次batch費用も増えます。

12,000 OIDのstdinはSHA-1で約0.49 MB、SHA-256で約0.78 MBです。親付き要求はその約2倍です。

一方、**path list の上限はcommit数だけでは算出できません**。総path出現数を `P`、path文字列総量を `S` とすると、常駐量は `O(S + P + commit数 + 親辺数)`。raw出力、分割文字列、list／set、先行親batchが一時的に共存します。ASCII中心なら概算で文字列総量の数倍＋pathあたり約80〜160 bytes程度を見込みます。例として12万path・平均100 bytesなら追加量は数十〜100 MB程度が目安ですが、保証上限ではありません。Git子プロセスと既存message／ancestryも含め、親のcold全史実測でピークを記録すべきです。

## 総括

**GO — 静的実装レビューとして。**

plan v2 の必要なfallback・部分結果非公開・oracle維持を満たし、受理集合や公開出力を変える欠陥は確認できませんでした。既存テストAST不変も確認済みです。

ただし、固定全史の旧新版一致、M-1〜M-9の実測kill、cold全史の480秒関門は未検証です。本判定は、それらを完了済みとする land 承認ではありません。