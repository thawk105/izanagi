## レンズ A

静的検査の結論は、**plan の無条件な absent 除外は、そのままでは受理できません**。候補列挙の既存限界と組み合わさり、旧形では失効した受領証を新形では誤って再利用する反例があります。以下の行番号は指定 worktree のものです。pytest・実機監査は実行していません。

### must-fix

**M1 — P1/P2 は「候補から外れる時点で属性が変わる」遷移を取り落としています。**

- **根拠:** brief L19–26、checker L2275–2337、L2473–2501。属性で過去の merge の実装 path が変わる経路は checker L1725–1755、既存テスト L7831–7865。
- **成果物への影響:** 新形だけが古い成功 prefix を再利用し、全史 oracle の finding と rc=1 を取り落として rc=0 を返しうる。
- **是正案:** 次の反例を負例として先に固定し、P1/P2 の無条件な等価性主張を撤回する。反例を閉じられない間は現行条件を維持する。候補列挙の変更や追加の再利用条件による解決は、scope 外の**裁定パッケージ候補**である。

反例は、既存 `_attribute_merge_repo` の `tools/shared_lines.py` を、専用 directory 内の `tools/retired/shared_lines.py` に移した形で構成できます。

1. A の履歴に、互いに離れた行の編集を統合した Claude author の merge M を置く。属性なしでは combined patch が空で、M の実装 path は空、全史監査は rc=0。
2. A の index には `tools/retired/shared_lines.py` があり、`tools/retired/.gitattributes` は absent。ここで受領証を作る。
3. 子 commit B で、その directory の最後の tracked path を削除する。B 自身は有効な Codex author とし、policy・registry 等は変更しない。
4. B の監査前に、untracked の `tools/retired/.gitattributes` を置き、`shared_lines.py -diff` とする。

| 観測 | A | B |
|---|---|---|
| 現行 `working` の当該 entry | `[path, absent]` | 候補外なので entry なし |
| 新形の当該 entry | absent 除外で entry なし | 候補外なので entry なし |
| 過去の M を再監査する属性入力 | 当該規則なし | 当該規則あり |

他の束縛を一定にすると、現行は digest 不一致で全史へ戻り、新形は一致して M を省略します。既存テストが示す `-diff` による combined patch の変化を使えば、oracle は M の Codex author 欠落を検出します。

これは、**A/B とも候補外だった directory の変更を旧新とも見逃す既存限界とは異なります**。現行の absent entry の削除が検出していた遷移を、本変更が新たに受理します。旧 checker の受領証を新 checker で読む話でもありません。各実装について同じ実行 bytes で A→B を比較する反例です。

P2 の「実在属性が A から残っているなら、候補脱落で旧新とも失効する」は正しいですが、上記の absent→候補外実在を覆いません。

### should

**S1 — 負例と変異 matrix の帰属を具体化する必要があります。**

- **根拠:** brief plan §2/§4、テスト L7956–7994、L8082–8169。
- **成果物への影響:** 条件不足の負例では、属性束縛を壊す実装でも緑となり、誤った再利用を検出できない。
- **是正案:** 新 directory の候補入り、属性の index 登録有無、cold の位置、失敗する assertion を各ケースに明記する。M1 の反例も追加する。

特に「新 directory に untracked `.gitattributes`」には二通りあります。

- tracked child を追加して候補に入れるなら、新形でも新設を検出する。
- tracked child のない新 directory なら、旧新とも列挙しない。単に fallback を期待するテストは仕様と一致しない。

working の保持を検査する負例では、`.gitattributes` 自体を index に登録すると `indexed` の変化が失効を肩代わりします。候補となる tracked child を保持し、属性だけを untracked のまま変更する必要があります。削除も「属性だけの削除」と「最後の tracked child も削除」を分けるべきです。

| 変異 | 静的に確認できる kill の見込み |
|---|---|
| M-1 `working=[]` | 既存 `additional_attribute_sources` の `untracked`／`nested` が適切。root 属性を commit するテストだけでは index 束縛が肩代わりする。 |
| M-2 absent を再包含 | 新 directory 導入の正例が適切。変更前後の fingerprint と、監査対象が delta のみであることの両方で kill できる。 |
| M-3 unreadable を absent 扱い | 現計画では不足。既存 L8106 のテストは system source に一定の読取エラーを与えて反復するだけで、working の unreadable 除外を kill しない。候補 path の absent→`lstat` EACCES 等を固定して追加する。 |
| M-4 index 束縛を除去 | 既存 `additional_attribute_sources[index]` が適切。root 属性を stage 後に unlink するため、working の状態変化に依存しない。変更行ではなく維持する既存契約の変異。 |
| M-5 kind を落とし sha256 だけ | 現状の記述では kill を保証できない。symlink は元々 target の sha256 を持たず、通常 file との差が残るため、既存同一 bytes テストが通りうる。正確な変異差分を事前登録する。 |

M-3/M-5 の survivor を直ちに「等価変異」としてはいけません。例えば kind 除去でも regular→directory は検出できる一方、sha を持たない異種状態の区別は失われます。逆に、本当に列挙順しか変えず最終的な順序を保存する変異なら等価候補です。`working` の `sorted` を単に削るのは、JSON 配列順が digest に入るため等価ではありません。

### nit

**N1 — 「absent は Git の入力ではない」では、必要な等価性を言い切れていません。**

- **根拠:** brief P1、D2045「属性 fingerprint」、checker L2283–2341。
- **成果物への影響:** 文言だけでは判定は変わらないが、M1 を既存限界として誤分類する。
- **是正案:** 「不存在そのものは属性規則の bytes を供給しない」と「入力探索状態を捨てても再利用が等価」を分ける。

通常の worktree/index 属性解決との対応は次のとおりです。

| 属性入力 | 現行 fingerprint の対応・限界 |
|---|---|
| root と照合対象 path の祖先 `.gitattributes` | root＋**現在の index path** の祖先だけ。過去の監査対象 path の祖先を網羅しているわけではない。 |
| worktree 属性がない場合等の index fallback | `.gitattributes` の index metadata を束縛。mode/OID だけでなく stage も含む。実際に fallback する場合に限定せず常に束縛する。 |
| `info/attributes` | `rev-parse --git-path` で解決して束縛。 |
| `core.attributesFile` | config の path 解決結果を読み、未設定時は XDG/HOME 既定を読む。 |
| system | `_system_attributes_path()` の解決結果を読む。全 `GIT_ATTR_*` の作用をこの関数だけで表現しているわけではない。 |

要求された境界の分類は以下です。

- **候補外 directory／index にない過去 path:** 両時点で候補外なら旧新共通の限界。候補脱落を伴う場合は M1 の新規差がある。
- **directory symlink:** 候補 path の `lstat/read_bytes` は途中の directory symlink をたどる。候補内の属性変更は新形でも保持する。最終 `.gitattributes` symlink は link 文字列を束縛し、regular と区別する。
- **`.gitattributes` が directory:** absent ではなく directory の kind として残る。「実在する file だけ」という説明は不正確。
- **大文字小文字／NFC・NFD:** 名前は index の bytes から hex 化され、独自の正規化はない。alias による重複・過剰束縛はありうるが、それだけで今回固有の誤受理を示したことにはならない。
- **`attr.tree`／属性 source 指定:** checker argv に `--attr-source` はない。対応 Git で設定・環境による tree source が働く場合、「Git も tree を読まない」という一般命題は成立しない。設定値・環境値は束縛するが、可変 ref 名の解決先を属性 fingerprint が束縛することは指定コードから確認できない。通常形とは別の既存限界として扱うべき。
- **`GIT_ATTR_*`／bare・worktree 混在:** 値の変更や解決済み config の変更は environment 側で失効する。ただし同じ値のまま解決先が変わる場合まで保証しない。指定コードから全モードの完全性は証明できず、今回の absent 除外の正当化にも使えない。

候補列挙の拡張、source 解決の追加、bare 用の条件追加は**裁定パッケージ候補**です。

**N2 — 属性は実際に判定へ届きます。CAB hit と `--cc` は別経路です。**

- **根拠:** checker L1223–1283、L1537–1562、L1668–1791、L1982–2001、テスト L7852–7865。
- **成果物への影響:** 説明だけの修正では成果物は変わらない。属性束縛の削除を正当化できる状況ではない。
- **是正案:** command 名ではなく argv と消費する出力を単位に記述する。

| 経路 | 判定への到達 |
|---|---|
| `diff-tree --name-only`、親比較の `diff --name-only` | tree/index の変更 path を取得する。通常、`-diff` でその path 自体を消す経路ではない。 |
| `diff-tree --cc -p` | **到達する。** stdout が空かどうかで merge の実装 path を選別する。`-diff`／binary 判定の変更が findings に届くことを既存テストが明示する。 |
| `log -S` | scope／implementation 導入点と CAB policy hit 集合を求める内容比較経路。diff driver／textconv 等は、この command で有効になる条件まで分けて評価する必要がある。全 command で同じ扱いではない。 |
| message 取得用 `log --no-walk --format=…`、`interpret-trailers`、祖先列挙の `rev-list` | 属性による本文変換を使う経路ではない。trailer parser はさらに隔離されている。 |
| `export-ignore`、`eol`／`text` | authoritative 監査の指定 argv に archive／checkout はない。これらによる直接の trailer 変換や、既存 commit blob の再正規化は確認できない。probe の checkout とは分ける。 |

`cab_hits` は L1999 の policy 文書への `log -S` の結果です。**`--cc` の実装 path 増加が CAB hit 増加なのではありません。** 属性束縛を削除する必要性評価は否定です。combined diff だけで必要性が成立しています。

**N3 — P3 は保守性を保つが、errno は不要な失効も生みます。**

- **根拠:** checker L2287–2300、テスト L8106–8141。
- **成果物への影響:** errno が変わるだけで digest が変わり、判定が同じでも cold に戻る。これは現行にもある挙動。
- **是正案:** P3 に「同一 errno の反復安定性を既存テストが覆う」と限定して書く。

`lstat` 失敗は `kind=unreadable`、regular の読取失敗は数値 kind＋`unreadable=errno` です。両方を残す必要があります。EACCES→EIO 等は不要な失効になりえますが、同じ unreadable 表現の背後の変化まで検出できるわけではありません。errno 正規化は本 wave の必須修正ではありません。

**N4 — 親 brief の集計は attributes を失効要因として支持しますが、「ほぼ毎回 cold の主因」「本 fix だけで回復」までは支持しません。**

- **根拠:** brief L3–7、L28–34、checker L2344–2379、L2386–2457、L2473–2531。
- **成果物への影響:** 集計説明だけでは再利用可否は変わらない。実装後も別 binding により cold が継続しうる。
- **是正案:** 結論を「attributes による隣接失効の削減」に限定するか、同 partition の祖先受領証対で全 binding の差を示す。

各数値が示せる範囲は限定されています。

- **424 件／11 partition:** 保存された成功受領証の分布。監査試行回数、cold 回数、land 専用件数ではない。
- **同 checker の直近 8 件で digest 8 種:** その 8 件相互の attributes 一致はない。ただし同 checker は同 environment／partition を意味せず、各実行が別の祖先受領証を利用した可能性も排除しない。
- **候補 2,835／index 29,684:** 当該 snapshot の探索規模。履歴全体の原因比率ではない。
- **実在属性 root 1 件:** 当該候補集合・時点について absent 除外が有効そうだという証拠。過去の worktree、候補外、外部属性 source の状態は示さない。
- **60 commit の 50% が新 dir:** 旧 digest が変わる機会の指標。directory 削除、属性変更、別 binding、古い一致受領証への再利用を含む cold 率ではない。

実 land で warm 連鎖するには、少なくとも次が必要です。

- 同じ common git-dir／object format、同一 environment partition。checker bytes・schema・解決済み `git config --list` 全文・継承 `GIT_*`／`LC_*`／`LANG` が一致する。
- policy、scope／implementation epoch、CAB hit OID 集合、registry manifest、attributes が一致する。
- 読める成功受領証が保存・保持され、その tip が現在 HEAD の祖先である。
- prefix の件数・digest、registry coverage、訂正／waiver／公開 records の検査が通り、delta 列挙も整合する。
- delta に correction candidate がなく、毎回実行する authoritative guards が通る。

checker 改版は partition を変え、registry 追加や CAB hit 増加は bindings を変えます。worktree ごとの config 差、継承環境差、保存失敗、淘汰も連鎖を切ります。land の `cwd=repository.wave`（L3555–3569）だけでは、同 partition は保証されません。

**N5 — 既存テストは緑を保てますが、一部は以前と同じ変異検出力を保ちません。**

- **根拠:** テスト L8144–8169、L8220–8252。
- **成果物への影響:** テストを据え置くだけでは現行成果物は変わらないが、「既存の意味をすべて維持した」という検証説明が過大になる。
- **是正案:** assertion の意味と、従来 kill していた変異を区別して記録する。

`independent_of_tip` は同じ index/worktree で引数だけ変えるため、新形でも正しい assertion です。ただし tip-tree 由来の候補差が**absent だけ**なら、新形では誤った tip-tree 列挙でも差が消えます。`many_commit_delta_warm_hit` も同様に、40 commit の delta 再利用は確認できても、従来の absent 候補差を使った tip-tree 列挙への感度は失います。

`candidate_directories_cover_git_paths` は候補内に実在属性を追加するため、新形でも意味を保ちます。ただし Git の属性解決結果との比較や receipt fallback 自体は検査していません。また、`tip-only` 分岐は parametrization に含まれず到達しません。

指定テスト群に「absent 除外だけで必ず赤になる」と断定できるものはありません。問題は、緑のまま失われる被覆です。

**N6 — probe は attributes の比較実験として妥当ですが、cold 率の分母と実 land の検証を分離すべきです。**

- **根拠:** brief plan §3、L32–34、checker L2353–2379。
- **成果物への影響:** probe の記述修正だけでは監査結果は変わらない。測定値を land の再利用率と誤認すると、未達の効果を達成済みと報告する。
- **是正案:** 固定した commit 列、旧新 checker bytes、checkout 成功、両関数の `REPO` が同一 clone を指すこと、外部属性環境を記録する。

60 snapshot 間の比較なら遷移は59本です。60 commit の各親→子を比較するなら、先頭の親を含む61 snapshot が必要です。初回 cold は別計上し、directory の追加だけでなく削除も数えます。

報告は例えば次の形が適切です。

> 固定した first-parent 列の T 遷移について、隣接 attributes fingerprint の不一致は旧 a/T、新 b/T。これは attributes 束縛単独の失効指標であり、実監査の cold 率・land wall・時間短縮率ではない。他 binding、partition、受領証探索は未測定。

「50%→x%」の50%を新 directory 導入率から流用してはいけません。旧 fingerprint の実測値で置き換える必要があります。

正しさだけなら、実 Git の小 repo で cold→新 dir→warm→受領証なし oracle を観測すれば足ります。**実 land の wave 間連鎖回復まで主張するなら**、共有 store を持つ二つの disposable worktree で、同じ新 checker・land 相当環境を使い、A の全史成功→子 B の新 dir 導入→B の delta 再利用を確認する最小実験が必要です。rc=0 や短い wall だけでなく、再利用 prefix／監査 delta を観測し、B の oracle と公開結果を比較します。これは M1 の反例を閉じた後に行うべきです。

## 総括

**must-fix は P1/P2 の反例です。** absent 候補の除外は、候補外属性という既存限界と組み合わさって、旧形が拒んだ受領証再利用を新たに許します。現在の scope を厳守するなら、無条件除外を採用せず裁定へ戻す必要があります。

新 directory 導入の正例は性能上の改善機会を示しますが、等価性の証明にはなりません。また、親 brief の集計から確実に言えるのは attributes が再利用を妨げる要因であることまでで、実 land の cold 連鎖が本 fix だけで解消するとは未証明です。