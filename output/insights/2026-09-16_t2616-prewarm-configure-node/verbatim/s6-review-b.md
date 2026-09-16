## 現物で確かめた事実

必読9ファイルを読み、HEAD が `7e52e24053b826c2eab84dc563b28f355ce14079` であることと、基点との差分を確認した。以下は**静的読解のみ**。pytest・変異の実走・ファイル変更は行っていない。

行番号の略記は次のファイルを指す。

- C = [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/orchestrator/tests/conftest.py)
- R = [real_repo_receipt_memo.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/orchestrator/tests/real_repo_receipt_memo.py)
- O = [sort_swo_oracle_receipt_memo.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/orchestrator/tests/sort_swo_oracle_receipt_memo.py)
- T = [test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node/orchestrator/tests/test_real_repo_serialization.py)

- **[real] 待機は consumer の有無によらず worker の collection hook に入っている。** C:2447 が待機を呼び、C:2361–2362 が両 memo を読む。controller の旧 barrier は早期 job がある場合に限り省略される（C:2558）。
  **変異:** C:2447 を consumer がいる場合だけ呼ぶ形にする。resolver を停止させ、consumer 不在 worker の test body が開始したら検出する。T:6045 の検査は空 collection を使ってこの条件を狙っている。

## fail-closed の後退に関する所見

- **[refuted] 未通知の cache miss を pending だけで救済する経路はない。** C:2348 は workerinput の明示がなければ待たない。R:660／O:710 の pending 分岐にも `early_job is not None` が必要で、本体不在は R:667／O:717 で失敗する。従来の blocking flock 自体の待ちは残る。
  **変異:** 本体なし・pending ありで `get()` を呼び、遅れて本体を公開する。未通知 reader は公開を待たず `cache-missing` になるべき。T:6159 に対応する検査がある。

- **[refuted] timeout・例外から worker が resolver へ倒れる新経路はない。** C:2361–2362 は reader factory の `get` だけを呼ぶ。R:619–693／O:661–745 に prewarm 呼出しはなく、内外の worker guard も C:880／937／2432／2440 に残る。
  **変異:** timeout を捕捉して `return self.prewarm(...)` に置換する。失敗要求と resolver 呼出し0回の両方で検出する。

- **[real] 120秒は成功返却までの硬い上限になっていない。** R:466／O:486 は lock 取得前に期限を確認するが、取得後の読取り・unlock・close を終えてから再確認しない。成功結果は R:682／O:735 でそのまま採用される。特に最後に読む oracle が期限を越えて成功しても、C:2362 の後には期限検査がない。
  **変異:** oracle の非 blocking flock 呼出しを期限直前で停止し、期限後に writer が正常公開してから取得を成功させる。現実装は値を返し得る。これは**R4 の「到達したら赤」への反例**であり、旧実装との差分としての赤→緑とは区別する。

- **[refuted] marker の偽造だけで期限を更新し続けることはできない。** deadline は R:651–652／O:701–702 で一度決まり、pending の再作成や更新時刻では延長されない。failed は本体より先に検査される（R:655／O:705）。ただし上記の I/O・実行停止を含む硬い時間上限の穴は別に残る。
  **変異:** 同じ pending を繰り返し再作成しつつ fake clock を進める。期限到達で赤になるべき。

- **[refuted] path 伝播によって D573 の事前予測防止が弱まった証拠はない。** nonce は controller で新規生成される（C:2744／2801）。worker は UID・nonce・HEAD から path を再構成し、通知値と完全一致を要求する（R:636–648、O:684–698）。marker を操作できるのは作成・削除等の権限を持つ主体であり、少なくとも同一実行ユーザーの worker/plugin は候補になる。別ユーザーの可否はディレクトリ権限等に依存する。in-flight path 観測後の改竄は、D573 が元から対象外としている境界である。
  **変異:** nonce B の worker に nonce A の正常公開済み path を渡す。`early-job-identity-mismatch` で拒否するべき。

## 並行性に関する所見

- **[refuted] 通常の背景例外を握り潰して最終的に緑にする経路は見つからない。** endpoint の例外は C:2384 で保存され、C:2416–2423 で再送出、C:2323 で job に保存、C:2372 で回収される。cleanup の抑制は既に別の例外が伝播している場合だけ（C:3273、C:2852）。
  **変異:** JSON 公開直後の writer unlock を `EIO` にする。worker の拒否と controller 回収時の例外を要求する。T:6200 に対応する検査がある。

- **[real] marker 更新失敗で背景 thread が終了しても、pending が残って worker は期限まで待ち得る。** C:2312 の rename と、回収側 C:2328 の rename がともに失敗すると pending が残る。後者より前に `job["error"]` は保存されるため最終失敗は残るが、worker はそのメモリ上の例外を見られない。
  **変異:** pending→failed の rename だけを一貫して `EIO` にする。worker は即時の `prewarm-failed` ではなく timeout へ進み、controller は例外を返す。これは遅い赤である。

- **[real] controller 回収は無期限で、worker の120秒とは独立している。** C:2370 の外側 join と C:2403 の内側 join に timeout がない。resolver が終了しなければ、worker が赤を出しても session は終了しない。
  **変異:** resolver を Event で300秒超停止させる。worker の失敗後も controller の回収が戻らないことを検出する。5分上限をこの実装だけから保証できない。

- **[refuted] reader が pending の待機中に lock を保持する経路はない。** pending は `_MISSING` を返し（R:666／O:716）、`_locked` が unlock・close してから外側で sleep する（R:497–514／691、O:517–534／744）。
  **変異:** pending 分岐内へ sleep/retry を移す。writer の公開が reader に阻まれることを検出する。

- **[unknown] 多数 reader による writer の starvation は静的検査では排除できない。** reader はすべて排他 lock を10ms間隔で再取得する（R:469／691、O:489／744）。コードに公平性の保証はないが、writer が継続して負ける実際のスケジュールは未測定である。
  **変異:** 複数 reader の再取得を同期させ、各解放直後に別 reader が先行する順序を与える。writer の公開所要と timeout 件数を測る必要がある。

- **[real] 待機で読んだ snapshot は consumer に引き継がれない。** C:2361–2362 の instance は使い捨てで、公開 endpoint は別 singleton を読む（R:703／722、O:755）。Aを待機で読み、その後本体をschema-validなBへ置換すると、consumer はBを読む。receipt は初回読取りを保持する（R:692）ため、worker間の初回読取り時刻によってA/Bが分かれ得る。oracle は reader の結果を保持せず返す（O:745）。
  **変異:** worker W1 の初回 consumer がAを読んだ後、W2 の初回 consumer 前に同じpathをBへ置換する。A/B不一致を検出する。**ただし、これは既存のcache改竄境界でも成立する。今回新設された赤→緑や、正常な単一writerでのD518違反とは断定しない。**

- **[real] stale prune は走行中の別sessionのmarkerを削除できる。** 保護対象は自分の `current_path` だけで、他sessionの生存確認やlock取得を行わず、mtimeが6時間より古ければ削除する（R:399–408、O:414–423）。長時間停止したsessionや時計の前進で条件を満たす。通常の5分以内・時計変動なしのsessionではこの条件に入らない。
  **変異:** 生存中session Aのpendingを6時間超のmtimeにし、session Bのprewarmからpruneする。Aのpendingが消える。削除後のAは即missやendpointのunlink失敗へ進み得るため、単純な緑化ではない。

## 受理集合が変わる箇所 (緑→赤 / 赤→緑)

- **[real] 赤→緑：通知済みjobでreaderがwriterより先にlockを取る順序。** R:660–666／O:710–716 がmissを待機へ変え、期限内公開を受理する。これは裁定が意図した拡大である。
  **変異:** writerのlock取得をreaderの最初の存在検査後へ遅らせる。通知ありだけ成功するべき。

- **[real] 緑→赤：正常公開が待機期限より遅い入力。** 旧blocking flockに対し、R:466／O:486 は期限で失敗する。lock競合中のtimeout診断は `publication-timeout` ではなく `lock-acquire-failed` に包まれる（R:480、O:500）が、値へのfallbackはない。
  **変異:** writerがlockを持ったまま120秒を越え、その後正常公開する。新readerは失敗を維持するべき。

- **[real] 緑→赤：consumer不在shardのresolver障害。** `early=True` はconsumer条件を迂回する（C:883／940／2308）。以前は呼ばれなかったresolverの障害がsession失敗へ加わる。これはR8で認識された変更である。
  **変異:** consumer不在shardでのみresolverを例外にする。旧経路は呼出し0回、新経路は赤になる。

- **[refuted] 上記以外の、旧実装で赤になる不正snapshotを新実装が最終的に緑へ変える経路は確定できない。** failed優先、schema読取り、controller例外回収が残る（R:655／672、O:705／722、C:2372）。120秒超の成功返却は実在するが、比較対象は新しいR4契約であり、旧実装も無期限待機だった。
  **変異:** schema-validな本体とfailedを共存させる。早期readerと未初期化の通常readerの双方で赤を要求する。

## 相談 B の [unknown] 4 点の判定

- **[refuted] (a) JSON公開後のwriter unlock失敗による成功扱いは閉じている。** pending削除はprewarm全体の成功後だけ（C:2308–2312）。unlock失敗はR:503／O:523から伝播し、failedを優先する。
  **変異:** atomic replace成功後のunlockだけを失敗させる。T:6200がこの検査を持つ。ただし既存テストはcontroller回収後にworkerを呼ぶため、競合中の順序まで実走済みとは言えない。

- **[refuted] (b) ready後の本体消失を、そのまま再待機で救済する経路は閉じている。** pendingがなければ即miss（R:667、O:717）。同じ早期readerでpendingが再出現すれば `publication-regressed`（R:661、O:711）。
  **変異:** 待機hook成功後、singletonの初回consumer前に本体を消す。consumerは即赤になるべき。T:6172–6175は同じreaderでの検査なので、使い捨てinstanceからsingletonへの実経路は別途検査対象。消失と再配置が読取りの間で完結する場合のsnapshot差替えは前節の限界として残る。

- **[refuted] (c) 非競合I/O障害までretryする穴は閉じている。** retry対象は `EAGAIN`／`EACCES` のみ（R:472、O:492）。`EIO` は初回で伝播する。
  **変異:** 最初のlock取得だけ `EIO`、次は成功にする。再試行0回で赤を要求する。T:6188–6196が対応する。

- **[real] (d) controller回収の長期化は未解決。** C:2370／2403のjoinは無期限のままである。R9が実測判定へ委ねた点であり、コード上は閉じていない。
  **変異:** resolverをworker timeout後も停止させ続ける。controller終了まで含めたwallで検出する。本レビューでは受入実測をしていない。

## 総括

- **[real] R4の硬い120秒上限には反例がある。** 期限直前に開始したlock取得・読取りが期限後に成功すると、特に最後のoracle読取りはそのまま待機hookを通過する（O:486–534／735、C:2362）。
  **変異:** 最後のoracle取得を期限越えさせ、成功返却ではなく赤を要求する。

- **[unknown] 本変更の最終受理は、この静的レビューだけでは支持できない。** workerのresolver復活や旧赤の不正snapshot受理は指せなかったが、無期限回収（C:2370）と全shardへの追加解決（C:2308）が残る。新規赤0件・最遅shard300秒未満は別途実測が必要である。
  **変異:** consumer不在shardのresolverだけを遅延させ、controller回収を含む最遅wallと失敗件数を確認する。