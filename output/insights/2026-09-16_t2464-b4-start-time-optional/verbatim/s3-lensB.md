## 総括

**追補案そのものを止める凍結違反・発行済み admission record は、指定 worktree では見つからなかった。** 挿入位置は正しく、plan の追補文をメモリ上で挿入したところ、§5.1.1 の raw bytes・H5 部分列・raw/semantic SHA はすべて不変だった。

ただし、**親 brief の D1789 の要約、pin 閉包の説明、plan の consumer 列挙には修正が必要**。未記入欄の数も親が誤っている。

指定9ファイルはすべて読めた。ファイル変更・commit・Git 状態変更は行っていない。**テストは実走していない**。以下の実測は、読取検索・JSON 内容確認・メモリ上の SHA 比較である。

参照の略記：

|略記|ファイル|
|---|---|
|B|`/home/SFC/tanab/.claude/jobs/1c1ec45a/tmp/wave-t2464/s1-brief.md`|
|P|`/home/SFC/tanab/.claude/jobs/1c1ec45a/tmp/wave-t2464/artifacts/t2464-b4-start-time/s2-plan.md`|
|V|`/home/SFC/tanab/.claude/jobs/1c1ec45a/tmp/wave-t2464/verbatim/d1789-d1790.md`|
|D|`docs/phase3-b4-reflux-ablation-preregistration.md`|
|A|`orchestrator/campaign/p3_b4_admission_record.py`|
|C|`orchestrator/campaign/p3_b4_analysis_prereg_consumer.py`|

## 所見1：D1789 を「本文への追記なら可」と一般化してはいけない

**所見**  
親 brief の「in-place で書き換えず追補で訂正する」は、訂正先と適用時点を落としている。D1789 は、発効して解析した後には**追記も含めて事前登録文書の bytes を変えず、insight の erratum に記録する**裁定である。

**根拠 (`file:line`)**  
`B:43` に対し、逐語 `V:3-5` は訂正先を insight に限定する。現物は `D:34` で発効前 draft、`D:159,162-166` に対象外の未記入6欄がある。

**放置したとき成果物の値・受理集合・参照がどう変わるか**  
この要約を後続 cohort に流用すると、「既存行を保持した追記」を理由に測定時点の whole-file SHA を変えてしまう。既存 record があれば、`A:777-783` の HEAD 文書一致が破れる。今回の文書追補を許す根拠は、発効前の現状と D1871 の明示した本文反映であり、「追記だから SHA 束縛に安全」ではない。

**重大度：P2。brief の裁定要約は要修正。本 wave の停止事実ではない。**

D1790 についても、測定時点の束縛と解析規則を区別する原則は正しいが、`A:775-783` の現行 admission verifier が旧版・新版の再解析を許すという意味にはならない。今回はその受理条件を変更しない。

## 所見2：波及列挙は helper 経由を一部辿っているが、文書 consumer が欠落している

**所見**  
plan は critic fixture → producer → material report という二段の参照を挙げており、module 名検索だけではない。しかし、文書を直接読む prerun issuer と、floor resolver 経由の material report を列挙していない。

**根拠 (`file:line`)**

- `P:144-161` の production 列挙に両経路がない。
- `orchestrator/campaign/p3_b4_prerun_issuer.py:194-214` は文書全体から publication root 宣言を抽出する。
- `orchestrator/campaign/p3_b4_material_report.py:215-220` は floor resolver を呼ぶ。
- `orchestrator/campaign/p3_b4_floor_artifact_issuer.py:1470-1505` は文書全体から floor 行を一意に探す。
- `orchestrator/tests/test_p3_b4_material_report.py:153,194` は producer 側の admission fixture を差し替えて使用する。さらにその fixture は `orchestrator/tests/test_p3_b4_raw_record_producer.py:57-65` で critic 側から導入される。

**放置したとき成果物の値・受理集合・参照がどう変わるか**  
今回の追補文には publication root 宣言や floor 行がないため、読解上これらの抽出値は変わらない。しかし、節 SHA 不変だけでは両経路の不変を証明しない。追補内容や位置が変わった際、発行拒否・floor 解決拒否を見逃す確認計画になる。

**重大度：P2。consumer 列挙と焦点走集合を補完すべき。**

焦点走への追加は次のとおり。

|追加する test file|理由|
|---|---|
|`orchestrator/tests/test_p3_b4_prerun_issuer.py`|`:278-292` が実文書の publication root 宣言を検査する。plan にない直接 consumer。|
|`orchestrator/tests/test_p3_b4_raw_record_producer.py`|`:57-65,362` の helper 経路と projection closure の検証。|
|`orchestrator/tests/test_p3_b4_material_report.py`|`:153,194,1009` の admission fixture／floor resolver 経路。|
|`orchestrator/tests/test_p3_b4_floor_artifact_issuer.py`|`:689-700,1327` の文書セル解決。文書 consumer の確認として追加する。|

plan が後続確認に挙げた3 driver loop と producer-auth experiment は維持してよい。既定5ファイルにも外すべきものはない。

一方、`test_ccbench_spawn_sites.py:173` は `_git_call` の spawn 箇所、`test_t671_source_binding.py:83` と `test_artifact_admission.py:116` は launcher のソース列挙である。今回そこは変えないため、**この差分の焦点走には追加不要**。通常の受入全走から除外するという意味ではない。

## 所見3：親 brief の「pin なし」「living だけ」は保証範囲を広く読める

**所見**  
whole-file SHA の固定 literal がないことと、whole-file SHA を消費する経路がないことは別である。また `check_docs.py` は単なる byte 予算登録ではない。

**根拠 (`file:line`)**

- `B:25-27` の説明に対し、`A:240-255,775-783` は record 内の文書 SHA と HEAD 文書を検証する。
- `tools/check_docs.py:146` は LIVING_DOCS 登録。
- 同 `:6721-6760` は行番号参照、現況再掲、D番号、ファイルパス等を検査する。

**放置したとき成果物の値・受理集合・参照がどう変わるか**  
literal 検索だけで「文書変更の影響なし」と判断すると、動的に発行された record の失効を見逃す。また追補の参照誤りによる docs 検査失敗も予測できない。

**重大度：P2（pin 閉包の説明）、P3（docs checker の説明）。**

現物から確認した参照経路は次のとおり。**文書 whole-file SHA とコード projection SHA を分ける必要がある。**

|経路|消費・波及の実体|
|---|---|
|record → admission verifier|`A:240-255` の JSON フィールドは `preregistration_binding.content_sha256`。`:775` で指定 commit の文書を検証し、`:782` で HEAD 文書との一致を要求する。|
|verifier → launcher|`orchestrator/campaign/p3_b4_launcher.py:381-394` が検証し、record SHA・commit を起動 context に束縛する。|
|verifier → critic → sidecar|`orchestrator/campaign/p3_b4_closed_critic.py:1268,1931` が再検証。`:368-395` が文書 SHA を sidecar に転記し、`:1941-1950` が sidecar bytes を検証する。|
|sidecar → producer → report|`orchestrator/campaign/p3_b4_raw_record_producer.py:1913-1924` が文書 SHA フィールドを持つ sidecar を読む。`:1735` で sidecar の証拠 hash を保持する。material report は `:238` で assembly を呼び、`:705-717` で source bytes／hash を保持する。これは文書 whole-file SHA を現在の文書と独立に再照合する経路とは区別する。|
|コード変更 → projection closure|critic `:632-670`、producer `:987-1045` が admission validator の bytes を hash に含める。**事前登録文書はこの列挙に含まれない。** 今回コードを変えるため closure は変わる。critic `:687-705` と producer `:1174-1195` が旧宣言／receipt との不一致を拒否する。|
|文書 → analysis consumer → receipt|`C:1038-1054` が文書を読み、`:399-407` で **§5.1.1 のみ**を pin する。whole-file SHA consumer ではない。|
|文書 → floor resolver → material report|floor issuer `:1470-1516`、material report `:215-220`。floor セル内の artifact SHA を使い、文書全体の SHA は pin しない。|
|文書 → prerun issuer|issuer `:194-214`。publication root 宣言を読む。文書全体の SHA は pin しない。|
|文書 → docs checker|`tools/check_docs.py:146,6694-6760`。文書 lint であり、whole-file SHA pin ではない。|

### 発行済み成果物の現物確認

読取探索の結果：

- `git ls-files --others --exclude-standard` の出力は空。
- tracked ファイル名探索に加え、hidden／ignored を含め、Git メタデータを除いて schema 文字列を検索した。
- JSON の候補2件は過去の mutation ledger。JSON 最上位が `schema_version = p3-b4-prerun-admission/v1` の record は0件。
- `A:99-101` の必須3パスは、実ファイルとしてもすべて不在。
- 拡張子を限定しない schema 検索も、実装・テスト・文書・過去の検査記録のみだった。

したがって、**この worktree の探索範囲では発行済み admission record 0件という親の結論を支持する**。repo 外の成果物不在までは主張しない。

現文書の whole-file SHA は
`09109bf472980fcceaa99b9aeab95f088b6d122d027aa62cd70d7031c4a4f47a`。
literal の一致先は親の主張どおり `output/insights/2026-09-16_t2545-b4-publication-root/README.md:54` の記録1件だった。

## 所見4：未記入数と一部 anchor が誤っている

**所見**  
残りは5欄ではなく6欄。対象行を含めると7行に `未記入` がある。

**根拠 (`file:line`)**  
`B:14,22-23` に対し、現物は `D:159,162,163,164,165,166,167`。plan の訂正が正しい。

anchor も、検査関数全体は `A:602-688`、fixture は `orchestrator/tests/test_p3_b4_admission_record.py:81-112`。親の `B:93,97` は末尾欠落／開始位置ずれがある。label 定義の開始は `A:77`、§0 の対象例外は `D:38-41`。

**放置したとき成果物の値・受理集合・参照がどう変わるか**  
実文書が変更後も拒否される結論は変わらない。ただし未解決作業数を過少に伝え、関数末尾の expectation 束縛・返却を検査対象から落としやすくする。

**重大度：P3。数値・anchor の訂正。**

## 追補文面と挿入位置の判定

`P:132-134` の文面を逐語で検査した結論は、**D1871 による限定的な規範変更として成立する**。

- 「開始時刻を発効条件から外す」は、`D:40-41` の無条件な閉鎖文と字面上は衝突する。しかし D1871 がまさにこの例外を決めている。旧本文を残して、後続の追補で読みを訂正すること自体は今回の依頼に沿う。
- 「上の追記で未裁定としていた…確定した」は、`D:353-355` の留保を明示的に閉じる。閉じたふりとは判断しない。
- 「他の9欄」「非空かつ既存の予約 sentinel に該当しない」は、開始時刻以外を一括免除する文面ではない。
- `P:134` は記入権限・値セル変更・発効・正式実走の認可を明示的に否定しており、権限の含意は見つからない。

ただし旧 §0 だけを読む人は、変更後も開始時刻の `未記入` で閉じると誤読する。本文を変更せず、追補内に「§0 の『placeholder 語が1つでも残る限り』は、この開始時刻の `未記入` に限り適用しない」と明記すれば参照関係がさらに明確になる。**これは文面改善であり、現案を凍結違反とする所見ではない。**

挿入位置は実測読取で一致した。**`D:357` が開始時刻項目の末尾、`:358` が空行、`:359` が §5.1.0 見出し**。修正不要。

## §5.1.1 SHA 不変の論証

plan の結論を覆す前提違いは見つからなかった。ただし `P:218` の一般的な失敗条件は、実装上の条件をすべて列挙してはいない。

|実装上の変化条件|根拠|
|---|---|
|文書が strict UTF-8 でなくなる／入力が bytes でなくなる|`C:238-242,302-303`|
|HTML comment の状態が後続行へ持ち越され、見出しが隠れる／現れる|`C:215-233,251`|
|backtick／tilde fence の状態が変わり、見出しが隠れる／現れる|`C:253-269`|
|正規化後の H4 fingerprint が0件または複数になる|`C:270-281,305-315`|
|対象 H4 の後の最初の level ≤ 4 見出しが変わり、抽出終端が動く|`C:317-321`|
|内側 H5 が6件でなくなる、順序または fingerprint が変わる|`C:322-331`|
|抽出した節・H5 部分が空になる、または節内 bytes が変わる|`C:332-344`|
|semantic 正規化の入力が変わる|`C:348-361`。これは抽出節だけを入力にし、前方の状態は引き継がない。|

今回の通常段落はこれらを起こさない。前方に非該当の見出しを追加するだけでも通常は問題ないが、同じ fingerprint の H4、comment／fence 状態、終端・H5 の変化は区別する必要がある。

**メモリ上の実測結果**：

- 現物の抽出範囲：`D:407` から `D:692` の直前。
- plan 文面を2字下げで `D:357` の直後へ挿入して比較。
- raw bytes 一致、H5 部分列一致。
- raw SHA：`0ceab4cd064eb8ff6c5dba22364fff04a6d708de8acb9d9cde52115f0891df30`、定数一致。
- semantic SHA：`5d0b189bd68391b4a6876bd24400230e7186f6bc1fe374ea298d44edebcfd1a7`、定数一致。
- 文書全体の SHA は変化。

これは**提示された追補案の比較結果**であり、後続 author が実際に作る差分の検証や pytest の成功を示すものではない。

## scope 外

新しい gate・台帳・互換層の追加提案はない。既存 record の SHA 貼り替えや旧新版の同時受理も、本 wave の修正に含めるべきではない。