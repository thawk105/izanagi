## 所見

### 1. 「新節がなければ書けない」という必要性の前提が誤っている

- 判定: real
- file:line 根拠: `tools/spool_fold.py:716-735` は `再発` の H3 とその後の任意 payload しか検査せず、`tools/spool_fold.py:1547-1567` は payload 全体を再発本文として取り込む。したがって `### F196` の下に `- **supersede: ...**` を置けば現行文法で受理される。
- 成果物影響: 新節なしでも canonical への追記は可能で、受理集合は変わらないが、supersede を再発として記録するため台帳の型・監査レンズが汚れる。
- 是正案: brief の「表現できない」を「表現できるが意味を誤る」に訂正し、純増は機械的検出力ではなく「専用の意味空間・shape・重複検査」と記述する。

### 2. 新節を追加しても `再発` 経路から supersede を迂回できる

- 判定: real
- file:line 根拠: 現行 `tools/spool_fold.py:1548-1567` は再発 payload を任意文字列として保持し、段2プラン自身も `s2-plan.md:34-39` で再発 branch を変更しないとしている。
- 成果物影響: 書き手は専用節の shape／重複検査を避けて `再発` に supersede 文を置けるため、同じ canonical 出力が再発扱いになり、意味の一意性が成立しない。
- 是正案: `再発` payload の先頭が `- **supersede:` なら拒否する reserved-prefix 検査を追加するか、「節の使い分けは規約のみで機械的には排他的でない」と明記する。

### 3. 正本間で supersede と再発の使い分けが決まっていない

- 判定: real
- file:line 根拠: `docs/failures.md:15-16` は同じ型の再発を既存 F へ追記すると規定し、`docs/spool/failures/README.md:38-41` も再発だけを定義している。段2プランの docs 更新範囲 `s2-plan.md:205-220` に `docs/failures.md` は含まれない。
- 成果物影響: 書き手が F196 のような後続事実による更新を再発／supersede のどちらにも書け、再発件数と監査対象集合が揺れる。
- 是正案: `docs/failures.md` に「同型の新たな発生は再発、既存記述が後続事実で古くなっただけなら supersede。supersede は再発件数に数えない」と一文追加する。

### 4. P4 の「fold は補わない」は実データには合うが、誤用を検査しない

- 判定: real
- file:line 根拠: `s1-brief.md:71-76` は本文非空白だけを要求し、日付・prefix を書き手へ委ねる。実際、`docs/spool/worklog/README.md:71-80` と `docs/phase3.md:661-664` では書き手が `発火記録:` と日付を本文へ入れている。一方、予定される supersede regex は `s2-plan.md:5,23,64` で非空白までしか要求しない。
- 成果物影響: `- F196 stale` のような行も gate を通り、canonical に supersede と識別できない追記が入り、後続 reviewer の stale 判定を誤らせる。
- 是正案: P4 は維持したまま、本文を `- **supersede: YYYY-MM-DD** — <非空本文>` に固定する。opaque payload を許すなら、docs も「prefix は慣行で必須ではない」と明記する。

### 5. check_docs・dry-run・land の実効経路がテスト計画から漏れている

- 判定: real
- file:line 根拠: `tools/check_docs.py:724-767` は実際に `tools/spool_fold.py` を動的 import して `validate_spool_tree` を呼ぶ。`tools/dev_wave_land.py:2257-2270` は land 前に `plan_fold` を実行し、`tools/dev_wave_land.py:1869-1880` は lock 内で apply・docs 検査・staging を行う。段2テスト一覧 `s2-plan.md:147-168` は `test_spool_fold.py` だけである。
- 成果物影響: parser 単体の結果だけが確認され、check_docs の finding 化、CLI dry-run の JSON/rc、lock 内 land の実適用が未認証のままになる。
- 是正案: `orchestrator/tests/test_check_docs.py` に supersede の valid/invalid 経路、`test_spool_fold.py` に CLI dry-run の failure、`test_dev_wave_land.py` に実 failures fragment の lock 内 fold を追加する。production file の編集自体は不要でも、scope には含める。

### 6. 実 canonical 202 件を使う正例がなく、F196/F197 境界の誤実装を検出できない

- 判定: real
- file:line 根拠: 実 canonical の helper は `orchestrator/tests/test_spool_fold.py:2027-2050` に存在するが、現テスト `:2053-2084` は worklog 経路だけを検査する。段2計画 `s2-plan.md:140-166` も `_repo` の合成 F を使う設計で、`_repo` 自体は `orchestrator/tests/test_spool_fold.py:77-81` に F1 しか持たない。実対象は `docs/failures.md:4819` の F196 と `:4843` の F197 である。
- 成果物影響: 挿入位置を EOF と誤実装しても合成 fixture では通り、F196 の追記が F197 側へ流れて failure report の帰属を壊し得る。
- 是正案: `_copy_real_canonical_family` に F196 supersede fragment を追加し、F197 heading 直前への exact splice、F197 本文不変、202 見出し数不変を固定する。

### 7. 親の性質検索と「純増 3 点」の一般化が実測と一致しない

- 判定: real
- file:line 根拠: `s1-brief.md:27-29` は Python hit をテスト2ファイルだけとしているが、実 checkout には `tools/check_docs.py:727-757`、`tools/dev_wave_land.py:1299-1304,2257-2264`、`tools/spool_fold.py:934-938` も存在する。さらに `failure-duplicate` は payload 重複ではなく `tools/spool_fold.py:1574-1584,1790-1795` の canonical ID 重複である。
- 成果物影響: scope と検査被覆の根拠が過少計上され、実際の consumer を含まないまま「純増は3点」と報告することになる。
- 是正案: production consumer、CLI、land、validator、テストを別々に列挙し、「検出力」と「意味上の表現力」を分けて再集計する。

### 8. F196 起点の DW-G05 影響はまだ「疑い」である

- 判定: 疑い
- file:line 根拠: `s1-brief.md:50-58` は F196 を読む reviewer が再訪を起票するとするが、実際には F196 の直後に `docs/failures.md:4843-4859` の F197 が runbook 7.3 の是正済み内容を明記している。
- 成果物影響: reviewer が F196 だけで判断する場合は重複再訪が増えるが、F197 まで読む運用なら certified 選択・受理集合・report 値は変わらない。
- 是正案: 「再訪が起きる」と断定せず、「F196 単体参照では誤読し得る」と書く。supersede は歴史的な F196 の事象を消すものではなく、現行状態を局所的に明示するものと定義する。

## scope から漏れている層 (裁定パッケージ候補)

- 人間／AI の fragment 作成層: P4 を「opaque payload」にするか、日付・`supersede:` prefix を機械必須にするか。
- `check_docs.py` の spool guard: production consumer と `test_check_docs.py` の負例・正例。
- `spool_fold.py --dry-run`: semantic rejection の CLI rc、JSON、無書込性。
- `dev_wave_land.py`: 実 failures fragment を lock 内で fold・検査・staging する統合経路。
- 正本: `docs/failures.md` の運用規則。`docs/spool/README.md` と failures README だけの更新では不十分。
- 実データ: `_copy_real_canonical_family` を使った F196/F197 境界の byte-exact 正例。
- `docs/spool/worklog/README.md` と `docs/phase3.md` は編集不要でも、P4 の比較対象・実運用証拠として scope 表へ明記する。

## 親 brief への異議

- **P1**: 節名と順序は構文上妥当。ただし `supersede` の意味定義がなく、`再発` 経路からの迂回も残る。
- **P2**: `見送り追記` と同じ1物理行は整合するが、既存 failures の再発本文には複数行実例もある。supersede に証拠 pointer を要求するなら、1行制約を維持するか要裁定。
- **P3**: F 見出し直前への挿入、再発→supersede の順は現行 recurrence 実装と整合する。ただし実 canonical 正例が必要。
- **P4**: 書き手が日付・prefix を付ける実運用は確認できるが、現計画では欠落を拒否しない。
- **P5**: literal target を raw parse で固定する方針は妥当。placeholder 解決を先に行わないことをテストで固定すべき。
- **P6**: 列挙された7条件は概ね十分だが、再発への誤用と prefix 欠落が抜けている。
- **P7**: `docs/spool` の列挙更新だけでは足りず、`docs/failures.md` の運用規則を追加対象にすべき。
- **P8**: 実 canonical への dry-run dogfood は有効だが、実 land lock 経路・check_docs 経路・実 canonical テストの代替にはならない。

## 変異候補

1. `## 再発` の supersede-looking payload をそのまま受理する変異。専用 prefix の排他を採るなら拒否テストで殺せる。
2. placeholder 解決後に target regex を適用し、`- {{F:future}} ...` を受理する変異。`failure-supersede-shape` のテストで殺せる。
3. F196 の挿入 offset を次の F 見出しでなく EOF／F197 の後にする変異。実 canonical F196/F197 golden で殺せる。

## 総括

新節は「書けるようにする」ためではなく、再発と現行状態の更新を意味的に分離し、専用検査を与えるために必要です。ただし現計画のままでは再発経路による迂回、prefix 欠落、正本規則の未更新、実 consumer・実 canonical のテスト欠落が残ります。

pytest は実行していないため、緑・closed は主張しません。