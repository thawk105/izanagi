静的レビューの結論は、現 plan のまま author へ渡すのは危険です。特に、空 ledger 期間の trust root 差替え、検証器自身による自己批准、fixture と source binding の矛盾が blocking です。

Web 検索、pytest、書込みは行っていません。

## 所見

### F1 — critical: 空 ledger の間は trust root を別鍵へ替えても何も検出しない

1. **一行の主張:** 人間 bootstrap 後、最初の receipt より前なら、AI 鍵への trust root 差替えと最初の自己署名 receipt が完全な full-history 上でも受理されます。

2. **成立条件:** verifier は現在 HEAD の root だけを読む (`recovered/u2/enforcement_source_ratification_receipt.py:183-228`)。空 ledger は無条件に空列になる (`:281-285`)。過去 root の blob/history は列挙せず、存在する row だけを現在鍵で検証する (`:331-337`)。plan は空 ledger で land する (`s2-plan.md:129-145`)。

   実在する書込経路は次です。

   - Write/Edit/apply_patch の直接書込は `guard_write.py:155-171,237-243,345-357` で拒否される。
   - しかし `tools/set_root.py` のような repo script を作り、その内部の `open(..., "wb")` で書く経路は `hooks/README.md:198-200,303-304,341-345` が明示する防護外。
   - 回収 broker 自身も SSH subprocess 内の redirect (`ratification_broker.py:160-164,238-240`) で同じ境界を越える。改訂 broker から TOFU を消しても、一般の script/subprocess 面は残る。
   - hook が未信頼の worktree では黙って外れる (`hooks/README.md:28-45`)。MCP/apps/plugins/子 process も防護外 (`:112-115`)。
   - 替えた値の staging は親 M13 のとおり `git add -- hooks/...` で止まらない。

3. **再現できる状態:** commit H0 に人間鍵 A の canonical root と空 ledger。AI が script 経由で鍵 B の root、未批准 closure C、空 ledger を commit H1 に置く。B で `source_commit=H1`, serial=1 の receipt を署名し H2 で ledger へ追加する。ledger history は `[] -> [B1]` なので +1、source binding も C=H1 なら成立し、過去 A を使う row は一件もありません。

4. **成果物影響 (DW-G05):** AI が選んだ未承認 closure C が批准済み集合へ入り、その C で certified 選択結果、report、campaign.lock の closure map、proof chain が生成されます。

5. **scope:** 内。D905/D906 と信頼根同一性の中心です。

---

### F2 — critical: 受理判定器とその caller が判定対象 closure の内側にあり、自己批准できる

1. **一行の主張:** root と署名が完全でも、AI は live verifier/caller を「常に digest を返す」実装へ変更して署名検査自体を消せます。

2. **成立条件:** `ident.py:234-240` は current HEAD/live bytes を capture・照合した後、同じ working tree から import 済みの `verify_ratified_contract_loader_binding` を呼びます。実体は `contract_loader_binding.py:14,387-398` で live ratification module へ委譲します。これらは `campaign_lock.py:47-49` の closure 内ですが、呼出し前に以前批准済み verifier bytes と比較する外側の実行器はありません。

3. **再現できる入力または状態:** `contract_loader_binding.py:387-402` を `return closure_digest_sha256(...)` 相当へ変更して commit する。または新 v2 verifier の `require_signed_ratification()` を無条件 return にする。`capture_contract_loader_binding()` はその悪性 bytes 自身を正直に hash し、`ident.py:443-458` はそれを authority として新 campaign.lock へ記録します。

4. **成果物影響 (DW-G05):** receipt がゼロでも任意 closure が certified authority に入り、選択結果・report・台帳参照が「署名済み」と同じ受理形で生成されます。

5. **scope:** 内。v1 から残る構造欠陥ですが、D905 完了を名乗る前に外部の固定 verifier/launcher、または前版からの検証鎖が必要です。

---

### F3 — high: trust root の連続性は current path と攻撃者制御の local DAG にしか束縛されない

1. **一行の主張:** 過去 receipt が root 変更を検出するのは「同じ ledger path と同じ reachable DAG が維持される」場合だけです。

2. **成立条件:** root history 自体の検査がなく、ledger path は定数 (`recovered/u2/...:33-39,394-405`) です。main の full-history 検査も canonical remote/main tip を pin せず、local HEAD の shallow/graft だけを拒否します (`enforcement_source_ratification.py:276-317,551-558`)。

   条件別の判定は次です。

   - 同じ path で ledger を削除: recovered は `:420-427`、main DAG は `:573-577` で拒否。
   - constant を変えず rename: current ledger 不在または deletion として拒否。
   - verifier の ledger path constant も新 path へ変更: old path の historyを一度も問い合わせない。新 path は新規 introduction として扱える。
   - shallow clone: recovered は拒否せず、depth=1 の `[B1]` を最初の一行として受理可能。plan が main の `:276-281` を再利用すれば拒否。
   - replace ref: recovered も `_v1_git` を使う (`recovered/u2/...:117-121`) ため、`enforcement_source_ratification.py:31-38,173-178,203-208` により無効。
   - commit-graph: 同じ hardening で無効。
   - partial clone: commit traversal は残る。promised blobを取得できなければ `_require_git` (`:228-240`) が失敗するため、全部通す側には倒れない。
   - shallow でない orphan/rewrite history: 検出不能。B rootとB1だけを持つ新しい完全 DAG は `--is-shallow=false` です。

3. **再現できる状態:** old path に A receipt がある履歴から、verifier定数を `hooks/new-ledger.v3.jsonl` へ変更し、B rootとB1を新 path に一行 introduction として置く。または全履歴を B root/B1 の orphan historyへ作り替える。

4. **成果物影響 (DW-G05):** old A ledger の拒否履歴を参照せず、B が認めた closure を現行批准集合として選択結果・report・proof chain が参照します。

5. **scope:** 内。root blobの全 commit 不変検査または明示的な root-rotation chain が必要です。

---

### F4 — high: bootstrap は鍵紛失・交代・schema/path 更新のたびに再発する

1. **一行の主張:** 現 schema は一度きりの bootstrap を実現せず、root rotation を表現できません。

2. **成立条件:** 各 receipt に key ID/epoch はなく、全 rowを現在の一鍵で検証します (`recovered/u2/...:292,331-337`)。過去 rowを A で検証してから A 署名の rotation recordを読む構造もありません。

3. **再現できる状態:** A で一件以上 receipt を発行後、秘密鍵を紛失または B へ交代する。rootをBへ替えるとA rowの署名検証が失敗し、替えなければ新 rowを発行できません。回復には ledger epoch/pathの初期化、過去 rowの再署名、または旧鍵Aによる事前rotationが必要です。

4. **成果物影響 (DW-G05):** 安全側なら以後のcertified campaignが全停止し、強制再bootstrapを許すなら過去の批准集合とreport参照が切断または置換されます。

5. **scope:** 内。鍵運用の必須ライフサイクルであり、親の裁定が必要です。

---

### F5 — high: plan の署名 fixture は source binding の正例になっていない

1. **一行の主張:** planどおりのfixtureは、plan自身が要求する「source commitの27 blobと署名digestの一致」を必ず破ります。

2. **成立条件:** planは実repoからclosure digestを取る (`s2-plan.md:186-189`) 一方、synthetic repoにはkey、trust root、空ledgerだけを置き、そのHEADを`source_commit`にします (`:188-190`)。現fixtureもsynthetic repoにはmarkerとledgerしかありません (`conftest.py:203-235`)。source binding追加要求は `s2-plan.md:395,437` です。

3. **再現できる入力:** synthetic HEADをcat-fileすると27 closure pathが存在しない。それでもreceiptのdigestはreal repoの27-path mapです。正しいverifierは拒否します。112 consumerを通すためsource checkをmonkeypatchまたは弱化すると、本番との差が固定されます。

4. **成果物影響 (DW-G05):** broad test群が緑でも本番receiptは通らないか、逆にsource bindingを欠いた実装が通り、reportの`source_commit`が署名対象closureを指さなくなります。

5. **scope:** 内。synthetic repoのsource commitへ27 pathのexact bytesをcommitしてからtrust/ledgerを追加すべきです。

---

### F6 — high: `source_commit` の現検査は装飾で、planの予定テストも reachability を単独では殺さない

1. **一行の主張:** 現実装は任意のexisting commitを許し、予定テストはclosure一致だけを殺してreachability削除を検出できません。

2. **成立条件:** 現検査は40hexと`cat-file -e`だけです (`recovered/u2/...:268-278`)。planのKILLED nodeは「reachableだが別closure」の一例だけです (`s2-plan.md:437`)。

3. **再現できる入力:** HEADからunreachableなdangling commit Uを作るが、その27 blobは署名digest Dと一致させる。valid signatureの`source_commit=U`を用意する。digest bindingを残しreachability checkだけ削除すると、この入力は通り、planの「reachableだが別closure」テストは依然赤のままです。

4. **成果物影響 (DW-G05):** certified reportとledgerがunreachableでGC可能なcommit Uをsourceとして記録し、選択結果の再現参照が消失します。

5. **scope:** 内。`unreachable + same closure`専用negative testが必要です。

---

### F7 — high: 「受理集合を広げない」はland直後にしか証明されていない

1. **一行の主張:** planの空ledger論証は時点限定で、最初のv2 receipt後にはv1が拒否するdigestをv2が受理します。

2. **成立条件:** briefの不変条件は無条件です (`s1-brief.md:30`)。planはland時の空集合だけを根拠にします (`s2-plan.md:129-145`)。共有closure定数は27 pathへ変わるため、旧v1台帳の25-path digestは新mapと一致しません。

3. **再現できる状態:** 共通25 pathを含む新27-path closure D27を用意する。v1台帳にはD27がないのでv1は拒否する。A保有者がv2 receiptを一行追加するとv2はD27を受理する。F1のB鍵takeoverなら、同じ拡大が人間authorizationなしでも起こります。

4. **成果物影響 (DW-G05):** v1では生成不能だったD27由来のcertified選択結果・report・proof chainがv2で新規生成されます。

5. **scope:** 内。ただし「新しい外部署名eventは受理集合比較から除外する」という意味なら、その限定を親が明文化する必要があります。

---

### F8 — high: 新判定を通らない既存の制御経路がある

1. **一行の主張:** `require_environment_contract=False` と既存lock再開はsigned gateを呼びません。

2. **成立条件:**

   - `verify_against_lock(..., False)` はv1 lockを許し、`ident.py:340-341`でratification前にreturn。
   - `ensure_campaign_identity(..., False)` は`_capture_current_loader_binding()`を呼ばずv1 textを作る (`:410-414,443-461`)。
   - `ensure_resumable_wal`と`ensure_resumable_attempts`がflagをそのまま転送する (`:367-404`)。
   - stored lockがある場合は`verify_against_lock`後にreturnし (`:427-433`)、trueの場合も`verify_live_contract_loader_binding`だけで現在のratification ledgerを再検査しない (`:343-351`)。

3. **再現できる状態:** official callerが誤ってFalseを渡して新lockを作る。またはroot/ledgerが後から無効になった状態で既存v2 lockをresumeする。射影内には環境変数やCLI flagからFalseへ変換するコードはありません。射影外callerの悉皆は親確認が必要です。

4. **成果物影響 (DW-G05):** False経路では未批准closureでlock/WAL/選択結果を作れ、resume経路では現在の批准集合から消えたclosureを使うreportとproof chainが増え続けます。

5. **scope:** 前半はguided exemptionとの境界確認が必要、後半のresume再検査方針は内。official caller inventoryは射影外のため親確認事項です。

---

### F9 — medium: divergent signed branchesの拒否は正しいが、一度mergeすると履歴を恒久的に使えなくする

1. **一行の主張:** planの数学的結論は正しいものの、通常のparallel branch運用とは両立しません。

2. **成立条件:** `S1 -> SL(serial=2, prev=S1)` と `S1 -> SR(serial=2, prev=S1)` は同じlinear chainへ両方置けません。planはこのmergeを拒否します (`s2-plan.md:76-93`)。

3. **再現できる状態:** leftとrightがそれぞれ一receiptを追加してmergeする。merge fileで片方を選んでも、もう片方のsigned siblingがparent historyに残るため、planの「divergent parentを拒否」規則ではmerge以後の全descendantが拒否されます。

   履歴編集の判定は次です。

   - 2行をsquashして1 commitで導入: `+2`違反。
   - receipt commitのrebase: signed `source_commit`が新HEADからunreachableになれば拒否。
   - cherry-pick: source commitが新HEADからreachableで、ledger chainがprefixの場合だけ維持可能。
   - 1行だけのfold/squash: signed sourceがreachableかつclosure不変なら維持可能。

4. **成果物影響 (DW-G05):** 誤った成果物は受理しませんが、該当merge以後は新規certified選択結果・report・ledger参照を一件も生成できません。

5. **scope:** 内。安全性はfail-closedですが、mainへのreceipt追記を単一writer/CASで直列化する運用契約か、DAG-native schemaが必要です。

## 実質的に判定していない検査

以下は削除しても成果物の受理集合が変わらないため、すべて **nit** です。

- `ed25519_verify.py:97-98`: parity再検査は到達不能。
- `ed25519_verify.py:99-100`: 通常到達域では平方根検査から導かれる冗長な曲線式。
- `ratification_broker.py:102`: `_ssh(..., missing_ok=False)`は`None`を返さないため恒真assert。
- `ratification_broker.py:209`: `_worktree_file(..., missing_ok=False)`後なので恒真assert。
- `enforcement_source_ratification_receipt.py:468`: 全rowは`:374-377`で既に`decision=="ratify"`に限定済み。
- `closure_paths_sha256` (`:367-373`) と `trust_root_sha256` (`:379-388`) は、それぞれ署名済みpath/current verification keyから再計算する診断値です。planは`s2-plan.md:454`でsecurity matrixから外しており、この扱いは正しいです。`s2-plan.md:41`の「path/hash/root binding」という表現だけは独立防御と誤読されるためschema整合性と書くべきです。

## 検査を削除しても赤にならない計画箇所

| 新検査 | plan上のテスト完全性 |
|---|---|
| source closure digest binding | `s2-plan.md:437`の専用testで殺せる |
| source reachability | 同testは「reachableだが別closure」なので、reachabilityだけ削除しても赤にならない |
| trust root history不変 | 検査自体もnegative testもない |
| ledger/trust path constant変更によるhistory再intro | negative testがない |
| trust root canonical bytes + LF | canonical正例だけで、noncanonical negative/KILLED nodeがない |
| trust-root Git mode | `s2-plan.md:59`にproseはあるが、`:436`のnamed KILLED nodeはledger modeだけ。別nodeが必要 |
| row count / JSON nesting bound | blob/line testはあるがrow-count/nestingの単独testがない |
| shallow | v2 counterpartが明記されているため殺せる |
| divergent sibling | negative追加が明記されているため殺せる |
| broker absent-trust / non-TTY / control escape | `s2-plan.md:438-440`相当があり殺せる |
| broker remote Git hardening | defectは`:115`で認識しているがtest列挙`:120`にPATH/config/replace負例がない |

## M11と署名対象の検算

M11が証明したのは、与えられた`(public_key, message, signature)`に対するEd25519方程式の挙動までです。次は測っていません。

- crafted low-order `R`、全noncanonical `R`。
- `_DOMAIN_PREFIX`とreceipt bodyの結合。
- `_SIGNED_KEYS`の選択。
- canonical JSONの衝突・型潰れ。
- trust root/path/historyの選択。
- `source_commit`とclosure digestの対応。
- brokerが人間へ表示したbytesと署名bodyの一致。
- broker/verifier/caller bytesの実行時integrity。
- import shadowing、runtime monkeypatch。
- ledger size/row/nestingによるCPU・memory DoS。

コード検算では次のとおりです。

- `_DOMAIN_PREFIX`は固定version prefix + NULで、後続は`{`から始まるcanonical JSONです (`recovered/u2/...:42,331-336`)。境界衝突は見つかりません。
- `_SIGNED_KEYS`はsignature自身以外の全9 fieldです (`:46-58`)。署名対象のfield抜けはありません。
- duplicate keyは拒否 (`:85-95`)。raw rowとcanonical bytesも一致必須 (`:310-318`)。
- 受理される型域では、異なるreceipt bodyが同じcanonical bytesへ潰れる経路は見つかりません。signature文字列だけが異なるreceiptが同じsigned bytesになるのは意図どおりです。
- したがって問題は「同じ署名が別digestへ使える」ことではなく、署名されたdigest Dと`source_commit=S`の意味対応を検査しないことです。悪性brokerはclean commit Sを表示しながら別closure digest Dを署名させ、live Dを受理させられます。

## M1〜M14の一般化結果

| 測定 | 静的検算 |
|---|---|
| M1 | digest値・0.43秒は再測していない。mainの不一致拒否ロジックは確認 |
| M2 | main 25 path、回収broker 27 pathをコードで確認 |
| M3 | recoveredがlinear、mainがDAGなのは確認。commit ancestry値は再測していない |
| M4(a) | 帰属は正しい。`subprocess.run(input=None)`はstdin PIPEを作らず継承する (`broker.py:54-56`) |
| M4(b) | 親とplanの結論どおり、当該赤はproduction到達前の偽前提 |
| M5 | 直接Write/Edit/apply_patchの拒否は確認。ただし「AIの書込が不可能」への一般化はF1のscript/subprocess経路で偽 |
| M6 | installed library/tool versionは再測していない |
| M7 | current fixtureがv1専用なのは確認。射影外pin位置は再棚卸ししていない |
| M8 | 射影内のlive chain `ident.py:239 -> contract_loader_binding.py:396`を確認 |
| M9 | direct new file拒否は確認。ただし全tool面での作成不能ではない |
| M10 | 112件countは再計数していない。fixture一箇所の影響が広い点は確認 |
| M11 | generic Ed25519監査として有効だが、integrationと署名対象選択は未計測 |
| M12 | 凍結artifact棚卸しは射影外のため再検算していない |
| M13 | 回収brokerのTOFU/SSH redirect操作列はコード上成立 |
| M14 | 追加pinは射影外のため再棚卸ししていない |

## 総括

blockingは三つです。

- 空ledger期間にtrust root AをBへ替え、B1を最初のrowにする操作を検出できない。
- ratification verifierとcallerがclosure内にあり、AIが検査そのものを無条件受理へ変更できる。
- planned fixtureのsynthetic `source_commit`に27 closure blobがなく、正しいsource bindingと両立しない。

加えて、root rotation、ledger path変更、完全履歴の作り直し、`require_environment_contract=False`、既存lock resumeの扱いには親裁定が必要です。これらを閉じるまでは「条件付きで実装可能」ではなく、信頼根と外部実行主体の設計を再度固定すべき段階です。