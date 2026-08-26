静的レビューの結論は、must-fix 10 件、nit 2 件です。特に、履歴 snapshot の TOCTOU、R11/R12 の実効上限、broker と検証子の非対称性は、現状の受理根拠を弱めます。

## 所見

### 1. full-history 検査と履歴取得の間に shallow 境界を差し込むと、信頼根差替えと台帳書換えを同時に隠せる

1. **一行の主張:** `_assert_immutable_trust_root_history` と `_assert_linear_ledger_history` は、安定した DAG には効くが、検査中に履歴 view が変わると過去の不正を取り逃す。
2. **成立条件:** `enforcement_source_ratification_receipt.py:214-219` が full-history 確認後に別 command で親 map を取得する。実処理は `enforcement_source_ratification.py:276-317` と `:337-384`。`test_enforcement_source_ratification_receipt.py:448-471` は full-history 確認を外した shallow repo が受理されることまで実証している。
3. **再現できる入力または状態:** `C0: trust=K0, ledger=A`、`C1: trust=K1へ変更、ledgerを空へ書換え`、`C2: closure B`、`C3: K1でBを署名` とし、shallow/graft 確認後かつ `git log` 前に C1 を shallow boundary にする。C1 は親無しの唯一の trust/ledger introduction に見え、C3 の B が受理される。
4. **成果物影響 (DW-G05):** 本来は K0→K1 と A→空の履歴で拒否される B が受理集合へ入り、台帳・レポートは隠された履歴を持たない線形 proof として扱われる。
5. **判断:** **must-fix**。raw commit object の parent を直接たどるか、少なくとも shallow/graft に影響されない単一 snapshot へ束縛する必要がある。

### 2. R11 は署名回数だけ線形で、履歴 blob の総読込量と prefix 比較は二次になる

1. **一行の主張:** 有効な一行追加履歴でも、各 prefix blob を全て保持・再走査するため、R11 の実効 gate は `O(N²)` bytes/time になり得る。
2. **成立条件:** `enforcement_source_ratification_receipt.py:390-411` が全 historical OID の全 bytes を memo 化し、`:420-422` が全 blob を再走査、`:462-480` が各 prefix を比較する。上限検査は head blob に対してだけ `:807-810` で行う。`test_enforcement_source_ratification_receipt.py:761-814` は5行と同一OIDだけを測る。
3. **再現できる入力または状態:** 約2 KiBの正規署名行を一 commit 一行で2048件積むと、head は約4 MiB以内だが、保持する全 prefix の合計は約4 GiBになる。さらに `:726-755` の source closure batch は blob size/aggregate size 無制限である。
4. **成果物影響 (DW-G05):** 値が正しい長い台帳や大きい過去 closure が timeout/OOM で処理不能となり、実効受理集合から certified 選択結果が脱落する。
5. **判断:** **must-fix**。historical bytes、source batch、commit 数に aggregate 上限を設け、R11 の主張も scalar-multiply 回数だけに限定すべき。

### 3. broker の remote Git は verifier と違って replace refs・global config・ambient environment を無効化していない

1. **一行の主張:** broker は置換された HEAD closure を表示・署名できるが、検証子は実 HEAD closure を読むため、必ず拒否される行を commit できる。
2. **成立条件:** broker の remote command は `tools/ratification_broker.py:262-279` で bare `git` と `GIT_CONFIG_NOSYSTEM=1` だけを使う。検証子側は `enforcement_source_ratification.py:30-56,159-217` の absolute Git、replace-ref 無効化、環境 scrub を使用する。
3. **再現できる入力または状態:** HEAD H に対して `refs/replace/H -> H'` を置き、H' の trust/ledger は同じだが closure bytes だけ変える。broker は H' の digest を `source_commit=H` として署名する。検証子は replace ref を無効化して H の実 bytes を読み、source digest 不一致で拒否する。
4. **成果物影響 (DW-G05):** verifier が受理していた空台帳へ無効な署名行が追加され、以後は全行検証のため certified 選択結果・レポート生成が全面拒否になる。
5. **判断:** **must-fix**。remote shell を allowlist 環境と absolute executable に固定し、verifier と同じ Git hardening を使う必要がある。

### 4. broker と verifier の wire contract は二重管理され、target 互換性を検査していない

1. **一行の主張:** 現在の署名 bytes は一致するが、broker 自身の定数で自己完結しているため、運用 copy の版ずれや SHA-256 object format を検出せず無効行を commit する。
2. **成立条件:** broker の schema/domain/fields は `tools/ratification_broker.py:68-88`、verifier は `enforcement_source_ratification_receipt.py:38-66`。broker は64桁 object ID を `tools/ratification_broker.py:92,322-335,677-681` で許すが、receipt の `source_commit` は `enforcement_source_ratification_receipt.py:48,534-539` で40桁限定。broker test は `test_ratification_broker.py:631-639` で broker 自身の定数だけを使う。
3. **再現できる入力または状態:** SHA-256 Git repo を target にすると broker は64桁 HEAD を署名・commit するが verifier は必ず拒否する。また空台帳に対して DOMAIN が一 byte 異なる古い運用 broker を使っても、broker 内では全検査を通る。
4. **成果物影響 (DW-G05):** verifier 非互換の最初の行が台帳へ固定され、その後の正しい receipt も含め受理集合が空になる。
5. **判断:** **must-fix**。少なくとも非40桁 HEAD を署名前に拒否し、broker 生成行を production verifier で受理させる cross-module E2E test が必要。

### 5. 新規署名を commit 前に検証せず、PATH と可変 key path を信頼している

1. **一行の主張:** 別鍵への差替えや不正な OpenSSL wrapper が64 bytesを返すだけで、無効署名を台帳へ commit できる。
2. **成立条件:** executable は `tools/ratification_broker.py:696-700` の `shutil.which`、key は `:158-176` で一度 lstat した後 `:179-225,707,771` で path を再度開く。新規 signature は長さしか検査せず、そのまま `:773-786` で commit する。test fixture 自身が `test_ratification_broker.py:130-166,188-193` で PATH wrapper を許している。
3. **再現できる入力または状態:** public key 取得後、署名前に key file を別鍵へ atomic rename する。または PATH 上の `openssl` が実 public key を返した後、署名時に64 bytesのgarbageを返す。どちらも broker は commit まで進む。
4. **成果物影響 (DW-G05):** 無効行が全台帳を拒否状態にし、wrapper が key を読めた場合は将来の certified 受理集合そのものを任意に拡張できる。
5. **判断:** **must-fix**。key を `O_NOFOLLOW` で一度開いた fd に固定し、生成 signature を captured public key で transaction 前に検証すべき。

### 6. source closure の tree mode を検査しないため、symlink source の署名を regular source へ流用できる

1. **一行の主張:** `source_commit` の path が mode `120000` でも object type は blob なので、同じ blob bytes を持つ後世の regular file を批准できる。
2. **成立条件:** broker は `tools/ratification_broker.py:282-297` で blob bytes だけを読む。verifier も `enforcement_source_ratification_receipt.py:665-718` で `objecttype == blob` しか見ない。一方 live binding は `contract_loader_binding.py:159-208` で regular non-symlink を要求する。
3. **再現できる入力または状態:** source commit S で一 path を symlink、symlink target bytes を `pass` とする。S を署名後、子 commit T で同 path を内容 `pass` の regular Python file へ置換する。他26 pathは同一にする。T の live binding と S の signed digest は一致し、S は reachable なので受理される。
4. **成果物影響 (DW-G05):** certified 値の digest は一致するが、台帳・レポートの `source_commit` は production の regular-file 条件を満たさない別の実行形を参照する。
5. **判断:** **must-fix**。source 27 path についても tree mode を `100644/100755` に限定すべき。もし意図的に bytes-only とするなら、live binding との非対称性について親の明示裁定が必要。

### 7. R6 の表示は初回 receipt では内容を出さず、Unicode control も端末へ素通しする

1. **一行の主張:** 初回批准は hash しか表示されず、2回目以降も valid UTF-8 の C1/bidi control で表示を偽装できる。
2. **成立条件:** `tools/ratification_broker.py:489-494` は `old is None` のとき path と hash しか表示しない。`:465-486` は byte `<0x20` だけを escape し、UTF-8 decoding 後の U+009B、U+009D、U+202E 等をそのまま出す。`test_ratification_broker.py:507-525` は C0/ESC だけを検査する。
3. **再現できる入力または状態:** 空台帳で任意の悪性 closure を置けば、operator は内容を一 byte も見ず `y` を押せる。既存台帳がある場合は、source comment/string に UTF-8 encoded C1 CSI または bidi override を入れる。
4. **成果物影響 (DW-G05):** operator が実際の source 表示を確認できないまま悪性 digest を署名し、その digest が certified 受理集合と台帳・レポートへ入る。
5. **判断:** **must-fix**。初回も全 bytes を表示し、LF以外は安全なASCII byte表現へ単射に escape すべき。

### 8. conftest fixture は binding と receipt を別 Git repository から作る

1. **一行の主張:** fixture consumer は production では存在しない「実 repo の binding commitを、合成 repo の署名 sourceで批准する」形を受理する。
2. **成立条件:** `conftest.py:222-223` で実 repo の binding/map を取得し、`:232-290` で同じ bytes を別 repo に commit・署名し、`:297` では receipt の `_REPO_ROOT` だけを合成 repo へ差し替える。
3. **再現できる入力または状態:** binding の `contract_loader_commit` は実 repo の commit X、receipt の `source_commit` は合成 repo の commit Y とする。27 digest が同じなので fixture consumer は通る。
4. **成果物影響 (DW-G05):** fixture consumer の pass 数は、campaign.lock の commit reference と receipt proof chain が同一 repo に属する production 形を証明しない。
5. **判断:** **must-fix**。`contract_loader_binding._REPO_ROOT` も合成 repo へ向け、receipt commit 後の合成 HEAD から binding を取得すべき。

### 9. broker は current blobs だけを検査し、target verifier が拒否する履歴へも成功 receipt を追加する

1. **一行の主張:** current ledger が正規なら、過去に行書換えや trust-root 変更があっても broker は成功を返す。
2. **成立条件:** broker は `tools/ratification_broker.py:729-739` で current trust/ledger blob だけを読む。verifier は `enforcement_source_ratification_receipt.py:786-814` で reachable 全史を検査する。
3. **再現できる入力または状態:** 過去に valid row A から別の valid serial-1 row B へ書換え、current blob を B の正規 chain にする。broker は B を検証して C を追記・commit するが verifier は A→B の非prefix履歴で拒否する。
4. **成果物影響 (DW-G05):** 台帳には新しい署名・commit reference が増える一方、certified 受理集合は空のままで、broker の成功報告と実際の gate が食い違う。
5. **判断:** **must-fix**。approval 前に target と同じ履歴検査を行う互換 preflight が必要。

### 10. 防壁風だが削除しても赤にならない、または到達不能な検査が複数ある

1. **一行の主張:** dead/redundant check が security barrier に見える状態が残っている。
2. **成立条件:** `enforcement_source_ratification_receipt.py:75-82` の `_GIT_HARDENING_BINDING` は未使用。trust head absent `:286-291` と ledger head absent `:485-493` は「introductions exactly one」と削除検出を通過した後には到達不能。`:367-376` の total-byte/LF は `:400-409` が先に拒否する。`:766,774` と broker `:714,737` の assert は前段契約上常に真。broker `:445` の path type 検査も直前の tuple equality が通った場合は常に真。
3. **再現できる入力または状態:** `_GIT_HARDENING_BINDING`、二つの head-absent 分岐、`_validate_ledger_blob_bounds` の total-byte/LF 分岐を個別に削除しても既存負例の受理結果は変わらない。
4. **成果物影響 (DW-G05):** certified 値・受理集合・参照は変わらず、防壁数とテスト網羅性の報告だけが実態より強く見える。
5. **判断:** **nit**。削除するか、独立防壁ではないことを明記すべき。

## 変異事前登録

### 11. M17 は実効 transaction gate ではなく冗長な preflight helper を測っている

1. **一行の主張:** M17 の同一入力は後段 transaction が再度拒否するため、「他層が拒否しない」という帰属条件を満たさない。
2. **成立条件:** `_require_ledger_cas` は `tools/ratification_broker.py:548-557,777`。transaction は同じ expected HEAD/OID と worktree/index を `:604-610` で再検査する。test は `test_ratification_broker.py:584-599` で helper を直接 monkeypatch するだけで、production call `:777` を削除しても赤にならない。
3. **再現できる入力または状態:** production の `_require_ledger_cas(...)` 呼出しだけを削除する。committed ledger の変更には HEAD変更が伴い transaction `:605` が拒否し、worktree変更は `:609-610` が拒否する。
4. **成果物影響 (DW-G05):** runtime の受理集合は変わらないのに、変異 report は preflight CAS を独立した KILLED gate と誤って記録する。
5. **判断:** **must-fix**。M17 は transaction の worktree blob comparison `:610` と `test_worktree_ledger_drift_is_rejected_inside_transaction` へ再照準するのが最も単一理由になる。

### 12. M10 の gitlink 帰属と「decision 検査を登録しない理由」は final code と一致しない

1. **一行の主張:** M10 は symlink には帰属するが gitlink は前段 object-type gate が拒否し、decision parser は現在唯一の有効 gate である。
2. **成立条件:** gitlink は `enforcement_source_ratification.py:470-475` の `object_type != blob` で拒否され、tree mode `:511-515` へ到達しない。symlink は blob なので mode gate へ届く。さらに final match は `enforcement_source_ratification_receipt.py:827-833` で digest/pathしか見ず、decision の再検査はない。
3. **再現できる入力または状態:** mode gateを無効化すると symlink parameter は受理されるが gitlink parameter は引き続き object-type で拒否される。parser の `decision != ratify` を無効化すると、署名済み `decision="reject"` の matching row が最終受理される。
4. **成果物影響 (DW-G05):** mutation report の gate attribution と security matrix が誤り、どの検査が certified 受理集合を守るかの参照がずれる。
5. **判断:** **nit**。M10 は symlink parameter のみに絞り、gitlink は object-type gateへ分離する。decision check は新規変異候補へ戻すべき。

M01〜M09のうちM10以外、およびM11〜M16は、登録された具体入力について前後の同一拒否層を見つけなかった。

## 受理集合・署名対象・省略経路の確認

- v1 が拒否して v2 が受理する具体形はある。旧v1 ledgerが空または対象 digest 不在で、新v2 trust rootと有効な署名 receiptがある状態である。別 ledger への意図した移行結果と読め、旧v1履歴の継承も要求するなら親の追加裁定が必要。
- 現 commit の署名 bytes は exact に一致する。broker は `DOMAIN + canonical(署名前9 fields)` を `tools/ratification_broker.py:760-772` で署名し、verifier は signature fieldを除いた同じ9 fieldsを `enforcement_source_ratification_receipt.py:589-595` で検証する。
- canonical encoder の設定も双方で `ensure_ascii=True`、`sort_keys=True`、compact separators、`allow_nan=False` と一致する。受理可能な型・field制約下では異なる signed payloadが同じ bytesへ潰れる形は見つからなかった。署名 field 自体を署名対象から除く点だけは意図した自己参照回避である。
- 既知の scope 外経路を除き、新規 certified lock 作成で環境変数、CLI flag、例外握り潰しによる v2 gate 省略は見つからなかった。
- R2、R3、R4、R5、R7、R8、R9は登録入力で発火する。R6はC0/ESCだけで不完全。R1/R13は安定した DAG では発火するが所見1の履歴view raceを持つ。R10はbytes/reachabilityには発火するがmodeを束縛しない。R11/R12は所見2の実効上限を満たさない。R17は安定した divergent bytes chainを拒否する。

## 総括

commit `5107ced3` は署名 payload 自体については broker/verifier 間で一致していますが、現時点では批准可能とは判断しません。最優先は以下です。

- full-history確認と履歴取得を一つの不変 snapshotへ束縛する。
- historical ledger/source closureのaggregate resource boundsを導入する。
- brokerのremote Git hardening、新規署名の自己検証、target verifierとのcross-E2Eを追加する。
- source tree mode、初回表示、Unicode controlを閉じる。
- fixtureのcross-repo受理形とM17の誤帰属を修正する。

pytest は実行しておらず、緑とは報告しません。親の実測値は指定資料M22の値を参照しただけです。