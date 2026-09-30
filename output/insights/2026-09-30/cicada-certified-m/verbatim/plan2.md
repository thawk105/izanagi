## 1. inline 版

**結論。** `INLINE_VERSION_OPT=1 ∧ INLINE_VERSION_PROMOTION=0` を M に含める。主比較の BEST はこの構成であり、ここを範囲外にすると D2305 項 4 が認めた性能値の扱いに M の証拠を結び付けられない。ただし「非 inline と同じ三関数に足すだけ」という (P1) の実装見積りは採らない。inline slot の初期化と権利の返却・再取得も個別に覆う。

**根拠と追加 site。**

- slot の所有者は `Tuple::inline_ver_`。初期ロードでは `Tuple::init()` が `latest_` を slot に向け、`inline_ver_.set()` を呼ぶ。もう一方の `init()` は slot を指すが `set()` は呼ばない。両方の初期化形を区別する。[`include/tuple.hh:24-36,74-108`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/include/tuple.hh:24>)
- GC による切り離しは `gc_versions()` の `next_ = nullptr` から `gcAfterThisVersion()` に渡る。inline slot はそこで `returnInlineVersionRight()` により `unused` へ戻る。未設置版の abort でも `writeSetClean()` が同じ返却をする。[`transaction.cc:831-840`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/transaction.cc:831>)、[`include/transaction.hh:173-196,343-367`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/include/transaction.hh:173>)
- 再取得は `Tuple::getInlineVersionRight()` の `unused → pending` CAS、使用準備は `newVersionGeneration()` の `inline_ver_.set()`。通常版の pool 再取得は同関数の `pop_back()` と `set()`。`Version::set()` の両 overload は wts・status・next を書き直す。[`include/tuple.hh:54-71`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/include/tuple.hh:54>)、[`include/transaction.hh:217-245`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/include/transaction.hh:217>)、[`include/version.hh:85-99`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/include/version.hh:85>)
- md_20 の三点比較は、選択時・read set 登録時・commit 時の **wts** を比べた。M の B は登録後の**切り離し・返却・再取得という事象**を見る。同一 wts での再利用と、返却されたがまだ再取得されていない状態も B の対象になる。md_20 自身も選択から登録までと書換え途中の限界を記す。[`vhash-cicada-best-config-verify/README.md:46-62,78-82`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/output/insights/2026-09-29/vhash-cicada-best-config-verify/README.md:46>)
- PROMOTION=1 は既存 trace patch の `#error` を保つ。[`instr-cicada-trace.patch`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace.patch>)

**(P1) との差。** 対象を広げる判断には賛成。追加 site は三関数の inline 分岐だけでは足りず、`Tuple` の権利操作と初期化を含む。初期化時の世代設定と再取得時の増分を二重計上しない設計が要る。

## 2. B の方式

**結論。** GC 権を読み手が保持する方式は採らない。第一候補は TRACE 専用の単調世代番号、ただし **「read 登録から tx 終了まで」の限定された B** として採る。`read_internal()` が版 pointer を得てから登録するまでの窓を含めた主張が必要なら、版外の事象台帳だけでも足りず、選択時の観測をさらに設計する必要がある。壊し B の生死確認でこの限定を隠さない。

**方式の比較。**

| 方式 | 検出と順序 | 行数・拡張 |
|---|---|---|
| 版内の世代番号 | 返却・切離し・再取得で単調増分し、登録時と終了時を照合する。版を解放しない範囲に限定。登録前に起きた事象と、並行する切離しの後先を確定できない窓がある | 小さい。`REUSE_VERSION=0` では終了時の版参照が危険 |
| 版外の事象台帳 | 版 object を終了時に参照せず、切離しなどの履歴を保存できる。追記と登録・終了照合に共通の順序点が要る。単なる mutex 追加でも GC 権取得を妨げない形にする | 大きい。object の再割当てを識別する鍵を設計すれば `REUSE_VERSION=0` に拡張可能 |

GC 権を保持すると、取得失敗した `gcq_` 要素は再試行されず捨てられるため、観測対象の回収挙動自体が変わる。[`transaction.cc:815-818`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/transaction.cc:815>)

**世代番号の具体案。** `Version` に `#if TRACE` 内の `std::atomic<uint64_t>` を置き、constructor で初期化する。`Version::set()` は世代を **戻さない**。事象を起こす site は `gcAfterThisVersion()` の通常版を pool に入れる直前・inline slot を返す直前、`newVersionGeneration()` の通常版を pool から取った直後・inline 権を得た直後、`writeSetClean()` の未設置通常版・inline 版を返す直前である。[`include/version.hh:25-59,85-99`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/include/version.hh:25>)、[`include/transaction.hh:173-245,343-365`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/include/transaction.hh:173>)。`Tuple::init()` は初回の基準世代を一度だけ確立し、通常の `set()` に増分を任せない。[`include/tuple.hh:74-108`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/include/tuple.hh:74>)

登録時には世代 acquire → wts acquire → 世代 acquire を読み、一致しなければ違反として記録する。終了時は保存した世代と現世代を照合する。増分側は `acq_rel`、照合側は acquire とし、切離しの状態変更に先立つ記録が必要か、状態変更直後の記録を線形化点にするかを実装時に固定する。**世代の一致だけで、登録前に pointer が差し替わった事実は復元できない。** `read_internal()` は latest 取得から版列走査、pending 待ちを経て `emplace_back` する。[`transaction.cc:79-126`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/transaction.cc:79>)。走査の各候補で世代を先取りして再確認すれば窓を狭められるが、最初の pointer 取得と最初の世代 load の間は残る。これは「選択から登録まで保護された」と主張しない限界として一次資料に書く。

終了照合は、書く tx では `cpv()` 後、`traceCommit()` と set clear より前の `writePhase()`、read-only では `commit()` の早期 return 前に置く。[`transaction.cc:895-958`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/transaction.cc:895>)。**abort した tx を無条件に除外する案には反対する。** YCSB は commit 前に body を使い、validation 失敗後に `abort()` へ入る。生存中に読んだ版の安全を言うなら、`abort()` の read set clear 前にも B を照合し、commit trace には出さない別の母集団として数える。[`include/ycsb.hh:121-164`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/include/ycsb.hh:121>)、[`transaction.cc:745-756`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/transaction.cc:745>)。親が「commit した tx だけ」と裁定するなら、論文の「生存中の tx」「全 tx」はその表現に狭める必要がある。

**走行中の `delete` の再確認。** YCSB point read/update を起動器で固定し、`REUSE_VERSION=1` なら通常版は GC 時 pool に入り、未設置 abort 時も pool に入る。[`include/transaction.hh:185-189,358-364`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/include/transaction.hh:185>)。`delete rec` は DELETE 後の `gc_records()`、`delete we.rcdptr_` は INSERT abort、版の残りの解放は `~TxExecutor()` と終了時 `deleteDB()` である。[`transaction.cc:745-750,845-855`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/transaction.cc:745>)、[`include/transaction.hh:97-106`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/include/transaction.hh:97>)、[`util.cc:219-257`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/util.cc:219>)。forwarding の三 patch は read 選択・時刻前進・GC 安全点と計器を変更するが、`gcAfterThisVersion`・`newVersionGeneration`・`writeSetClean` に `delete` を追加していない。[`cicada-forwarding-variant.patch`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/cicada-forwarding-variant.patch>)、[`cicada-forwarding-gc.patch`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/cicada-forwarding-gc.patch>)、[`cicada-forwarding-target.patch`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/cicada-forwarding-target.patch>)。これは指定範囲での経路読解であり、全構成の不存在証明ではない。

**(P2) との差。** 世代案を推す点は同じ。`REUSE_VERSION=1` の固定、abort の扱い、登録前の窓、並行時の線形化点を明示しない「B を全 tx で保証」は過大である。

## 3. U

**結論。** 公開側の記録を `cpv()` の status store 直前に独立に作り、`traceCommit()` が実際に出す W の要素と多重集合で双方向照合する。書く tx ごとの TRACE 専用 `vector` に `(storage,key,Version*,generation,wts,op)` を保持する。設置 CAS の成功記録も別 field とし、公開記録との対応を調べる。

**根拠。** 設置は `validation()` の二つの CAS 成功点、公開は `cpv()` の committed store、W emit は header の `traceCommit()` にある。[`transaction.cc:515-530,687-720`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/transaction.cc:515>)、[`instr-cicada-trace.patch`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace.patch>)。forwarding 三 patch は前進先と読取り・GC 安全点を変えるが、公開 store を別関数へ移していない。公開直前に status が `pending` であること、記録の版 wts が `wts_.ts_` すなわち C 行の版に等しいことを確認する。`group_commit>0` は `gcpv()` が別公開経路になるので、起動器の明示 flag と stdout flag 束縛で 0 を強制し、加えて TRACE の実行時 guard で非 0 を fail closed にする。[`transaction.cc:723-738,899-904`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/transaction.cc:723>)。`group_commit` は実行時 flag なので `#error` では止められない。

`#if` に新たな条件語は入れず `#if TRACE` のみにする。patch の追加条件語は `test_ccbench_spawn_sites.py` の全 patch 定義一覧へ入るためである。[`test_ccbench_spawn_sites.py:684-760`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/orchestrator/tests/test_ccbench_spawn_sites.py:684>)

**検出力の限界。** `cpv()` の write set 走査で公開記録を作り、後の write set 走査で W を作るだけなら、二走査の間の削除・置換は検出できる。一方、`cpv()` に到達する前に write set から要素が失われ、その版が公開されなかった場合は、両方から消えて恒真になる。設置 CAS の記録との照合で一部を補えるが、write API intent の完全な保存は M の範囲外である。これを U の万能な網羅性とは呼ばない。

**(P3) との差。** 公開記録と W の双方向性には賛成。設置記録の役割と、同じ write set を二度見る構造が検出できない欠落を明記する。

## 4. read 側 API 照合

**結論。** 母集団は公開 `read()` の呼び出しである。入口で `(storage,key,read_set_.size())` を控え、各 return で結果と分岐を照合する。外部 read の成功時だけ、その呼び出しで増えた要素が**ちょうど一つ**、storage・key が一致、返した body pointer が登録版の `body_` と一致することを要求する。

**根拠。** 入口は `transaction.cc:144`、read set 再読は `:156-160`、own-write は `:161-165`、tree と `read_internal()` の外部 read は `:170-184`、成功 return は `:185-190`。不在の二つの return は `:175,178`。[`transaction.cc:144-190`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/transaction.cc:144>)。(a) は既存 read 要素、(b) は既存 write 要素の版の body と一致させ、新規登録を 0 とする。(c) は一つの新規登録と一致させる。`WARN_NOT_FOUND` は独立計数し、今回の全 key 既存 YCSB cell では 0 を要求する。tx 終了時は、(c) に対応づかなかった read set 要素を 0 とする。abort 分も clear 前に調べる。

forwarding variant は `read_internal()` の版選択部分と `read()` の近傍を変更するが、成功外部 read の最後の `read_set_.emplace_back()` と body 返却という契約が残るかを重ねた source で検査する。[`cicada-forwarding-variant.patch` の `@@ -100…` と `@@ -175…`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/cicada-forwarding-variant.patch>)。前進後に未設置 write の wts と read 要素の `later_ver_` を更新する箇所があるため、API 照合は呼び出し時の pointer・key を保存し、終了時の `later_ver_` の値へ依存させない。[`cicada-forwarding-variant.patch`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/cicada-forwarding-variant.patch>)

**(P3) との差。** 大筋は一致。件数の一致だけに簡略化せず、呼び出しごとの対応と余分な登録を検査する。`scan()` は同じ規則を適用できないので起動器から除外する。[`transaction.cc:429-460`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/transaction.cc:429>)

## 5. 出力の書式

**結論。** M の診断は stderr の固定書式にし、既存の trace stream と C/R/W/E の bytes を一切変えない。例:

```text
CICADA_M_VIOLATION kind=B_DETACH thid=3 tx_seq=42 key=0011223344556677 ver=0x... gen_seen=7 gen_now=8 wts_seen=123 event=gc_detach
CICADA_M_SUMMARY schema=1 tx_commit=... tx_abort_checked=... read_external=... read_reread=... read_own_write=... read_not_found=... b_checked=... u_published=... u_w_rows=... api_checked=... b_violation=... u_violation=... api_violation=...
```

`kind` は許可値一覧で解析し、未知・欠落・重複 field を拒否する。版 pointer は診断用であり、run 間の識別子には使わない。`thid` と thread 内の `tx_seq` を違反と壊し event の双方に入れる。wts はその時点の版 wts と tx wts を別名で載せ、二義化しない。`IZANAGI_` という語は patch 内に置かない。

集計は thread ごとの cache line を分けたカウンタに蓄え、終了時に一度だけ足す。既存 `cicada_trace::report` は YCSB `main()` で `atexit` 登録される。[`instr-cicada-trace.patch`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace.patch>)。M の report は **同じ `cicada_trace::report` から呼ぶ形**にし、二つの `atexit` 登録順への依存を避ける。登録を追加するなら順序を実測し、終了前に worker が join 済みであることも確かめる。`izanagi_trace::next_txid()` は `traceCommit()` 内で初めて得るので、abort や read 時の違反には使えない。帰属の主キーは `(thid,tx_seq)`、commit 後の照合用に `tx_wts → C 行 txid` を起動器で解決し、一意でなければ失敗とする。[`launch_gcfix_run.py:663-677`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/stage7/launch_gcfix_run.py:663>)

**(P4) との差。** 1 行集計には賛成。ただし thread 集計をそのまま複数行出すと要求の「ちょうど 1 行」と衝突する。違反行の帰属には tx 通番と tx wts の両方が要る。

## 6. 置き場と重ね方

**結論。** 新規 `patches/instr-cicada-trace-m.patch` は既存計装の上に置く。`instr-cicada-trace.patch` の既存行は変更しない方針を先に試す。ただし、**両順序に fuzz なしで当たることは静的読解だけでは確定できない**。親の適用確認で実 patch bytes を条件ごとに検証する。

**hunk 案。**

- `include/version.hh:25-59` に TRACE 世代 field・constructor 初期化・増分 helper。
- `include/tuple.hh:54-108` に inline 権の返却・再取得と初期化の記録。ただし同一事象を `transaction.hh` でも増分しない。
- `include/cicada_op_element.hh:12-19` に登録時の世代・wts 控え。既存 instr が `trace_read_wts_` を足した場所なので、その実 preimage を使う。
- `include/transaction.hh:38-52` に tx ごとの M 記録、`:173-245,343-367` に退役・再利用・abort 返却、既存 `traceCommit()` の**前後**に U と API の照合を加える。trace emit の式はそのまま残す。
- `transaction.cc:34-43,79-190,515-530,687-720,745-756,895-958` に通番、read 境界、設置・公開、abort と commit の照合。
- `ycsb_cicada.cc:23-32` は report 登録を変える必要がある場合に限る。

forwarding variant は `read_internal()`、`read()`、`begin()` 近傍を広く触り、GC patch はその近傍と `gc_versions()`、target patch は forwarding が増やした関数群を触る。[`cicada-forwarding-variant.patch`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/cicada-forwarding-variant.patch>)、[`cicada-forwarding-gc.patch`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/cicada-forwarding-gc.patch>)、[`cicada-forwarding-target.patch`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/cicada-forwarding-target.patch>)。従って M を `instr → variant → gc → target → M` の**最後**に置き、共通の stock 用 bytes は variant の挿入行を文脈に含めず、変更点の周囲を短い安定文脈で切る。`instr → M → variant → gc → target` は variant の大きな read hunk と衝突しやすい。適用検査では各段の `git apply --check` に加え、実適用で offset/fuzz の出力を保存する。GNU `patch` の fuzz なしと `git apply` 成功は同義でないので、要求の判定方法を固定する。

旧壊し三本は `transaction.cc` の read 再検査、rts 更新、read-only 版選択と、共通して `begin`・`abort`・`writePhase`・read-only commit に hunk を持つ。[`broken-cicada-*.patch`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/broken-cicada-skip-read-recheck.patch>)。M はそれらの**同じアンカー直近**を避け、旧壊しを M の後に置いて各一本ずつ厳密適用を確認する。衝突した場合は M の hunk の分割・移動を優先し、既存 instr や所有外 patch の変更は最後の選択にする。

**(P5) との差。** 新 patch・既存 instr 不変には賛成。両系列への無 fuzz 適用と旧壊しとの無衝突は、現段階の確認済み事実ではなく、実装時の合格条件である。

## 7. 壊し B

**結論。** 無マクロの新規 `broken-cicada-m-early-reclaim.patch` を、stock YCSB の**read-only tx が body を使い終えた後、commit の前**という単一 site に置く案を第一候補とする。`include/ycsb.hh:158-161` が候補だが、共有 workload を変えるなら Cicada だけの build に限定できるか、親の段 4 で所有・適用面を決める。`read()` の返却前に待たせると body 消費中の再利用を招くので、生死確認の目的に合わない。

壊しは既読版が一つ以上ある read-only tx で間引いて発火し、自 thread の `ThreadRtsArray` をその時点の `MinWts−1` へ上げ、`GCFlag[thid]` も立てて 1–10 ms 待つ。flag が無いと leader は全 worker の flag を待つため境界が進まない。[`util.cc:281-322`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/util.cc:281>)。長い待ちの間に writer が同じ key の後続版を公開し、leader の `MinRts` が後続版 wts を越えると、writer 側の `mainte()` → `gc_versions()` が旧版を切り離して pool へ入れる。[`transaction.cc:687-720,806-842,859-888`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/transaction.cc:687>)、[`include/transaction.hh:173-196`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/include/transaction.hh:173>)。再利用は `newVersionGeneration()`、inline slot なら同関数の権利再取得に現れる。[`include/transaction.hh:217-245`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/include/transaction.hh:217>)

条件は GC 10 µs、複数 worker、少数 tuple、高 skew の read/write 混合を起点とし、default と BEST の各々で `reached / changed / committed` を出す。`reached` は待機 site に来た回数、`changed` は下限を実際に上げた回数、`committed` はその tx が正常 commit した回数とし、inline 版を読んだ回数は別 field で数える。違反は `(thid,tx_seq,key,読んだ版 pointer・世代)` が壊し event と一致する場合に限り帰属させる。異常終了・timeout・計数行欠落は不合格。

**到達性の懸念。** 自 thread の `ThreadWtsArray` が古いままなら `MinWts−1` は十分先へ行かず、後続版を切り離せない列がある。また `gc_versions()` は GC 権取得に失敗した gcq 要素を捨てる。したがって `changed>0` だけを発火の証拠とせず、実際の B 違反を生死確認で要求する。到達しなければ同じ壊しを本走へ持ち込まず、forwarding-gc の既存待機安全点で P5 を再現する案、または待機と writer の順序を同期させた stock 案へ設計変更する。

**(P6) との差。** P5 型は有力だが、stock に単に「最新の MinWts−1」を代入するだけで回収に到達するとは言えない。正常終了と同じ tx への帰属を実測 gate にする。

## 8. 壊し U

**結論。** `broken-cicada-m-drop-write.patch` は `writePhase()` の `cpv()` 後、`traceCommit()` 前で、公開済み write 要素を一つ `write_set_` から外す。まず各 build/run で一回だけ、write set が非空の tx に発火させる。`cpv()` が既に status を committed にしているため pending を残さない。[`transaction.cc:687-720,895-913`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/transaction.cc:687>)

壊し event に `(thid,tx_seq,tx_wts,storage,key,ver,generation)` と `reached / changed / committed` を載せる。`changed` は実際に一要素を外した回、`committed` は trace commit まで正常到達した回。U の `published_without_W` 違反が同じ版に対応することを要求する。write set の erase は後続の clear に影響するので、破壊するのは `cpv()` の完了後に限る。

**(P6) との差。** site は一致。`committed>0` と版単位の帰属を合格条件にし、単なる U 違反総数だけでは通さない。

## 9. TRACE=0 同一性

**結論。** pin C と `pin C + instr + M` を、default と BEST の二 genome でそれぞれ比較する。`Version` の TRACE field は header を通じて Cicada の四 workload target に入るため、YCSB の三 TU だけでは足りない。[`cc/cicada/CMakeLists.txt:1-14`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/CMakeLists.txt:1>)

雛形 1 の `trace_zero_identity()` は、target を `ycsb_cicada.exe`・`tpcc_cicada.exe`・`bomb_cicada.exe`・`sbomb_cicada.exe` に回し、各 target の `compile_commands.json` から全 Cicada TU の前処理・命令列・symbol を比較する形へ拡張する。[`launch_gcfix_run.py:370-405,447-477`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/stage7/launch_gcfix_run.py:370>)。各 target の `transaction.cc`・`util.cc`・workload `.cc` は別 compile command なので、target ごとに比較する。default は OPT=0、BEST は `BACK_OFF=0, OPT=1, PROMOTION=0, REUSE=1, WRITE_LATEST_ONLY=0`。[`vhash-cicada-best-config-verify/README.md:29-40`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/output/insights/2026-09-29/vhash-cicada-best-config-verify/README.md:29>)。`#else` の `#line` を保ち、`__LINE__` 由来の差も拒否する。

**(P1/P5) との差。** TRACE=0 同一性を要する方針は同じ。Version の配置を触る以上、四 target の各 compile command を証拠にする。

## 10. 起動器

**結論。** repo 外の新起動器を雛形 1 の実行・判定骨格と雛形 2 の forwarding 構成から作る。各 build の CMake cache と各 TU の `-D` を照合し、全 run の argv と stdout flag を束縛する。`REUSE_VERSION=1`、`SINGLE_EXEC=0`、`group_commit=0`、OPT=1 なら PROMOTION=0 を起動前と実成果物の両方で強制する。雛形 1 は PROMOTION=1 なので、その値をそのまま流用しない。[`launch_gcfix_run.py:33-37,331-349`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/stage7/launch_gcfix_run.py:33>)

E-max は `instr → variant → gc → target → M`、macro は `CICADA_FWD_ENABLE, CICADA_LONGTX, CICADA_FWD_COUNT, CICADA_GC_SAFEPOINT, CICADA_GC_WAIT, CICADA_GC_COUNT` を既存 cell と同じように供給する。検査 cell は tuple 50/skew .9 と tuple 10,000/skew 0、GC 10/100 µs、8 thread、長い thread 2 本、10 read 後 10 ms 待機である。[`launch_cicada_run_target.used.py:35-66,609-628`](</work/1/SFC/tanab/tmp/vhash-forwarding-target-policy-2026-09-29/jobs/verify2/launch_cicada_run_target.used.py:35>)

合格は、stock/forwarding で正常終了、巡回 0、integrity の**数値項目**すべて 0、C 行数 = `commit_counts_`、`CICADA_TRACE_READ_WTS_MISMATCH n=0` が一行、M 集計が一行、M の違反行・違反件数 0、該当する B/U/API の照合件数 >0。`integrity.clean` は Cicada で構造上 false なので要求しない。[`vhash-forwarding-target-policy/README.md:158-172`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/output/insights/2026-09-29/vhash-forwarding-target-policy/README.md:158>)。壊しは、同 cell の stock 対照が合格し、事前登録した違反 kind >0、版・tx の帰属が成立し、正常終了した場合だけ合格する。既存壊し三本は M の存在で巡回検出が消えないことも別判定にする。

| job 群 | run |
|---|---:|
| default stock K/W/R × t1/t4 | 6 |
| BEST stock K/R × t4/t48 | 4 |
| E-max A10/A100/B10/B100 | 4 |
| 壊し B default・BEST、壊し U と各 stock 対照 | 少なくとも 6 |
| 旧壊し三本 on M と各 stock 対照 | 少なくとも 6 |

最低約 26 run。雛形の既存 job Elapse は 1 job あたり約 80–220 秒、E-max 検査 job は 221 秒だった。[`vhash-forwarding-target-policy/README.md:158-165`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/output/insights/2026-09-29/vhash-forwarding-target-policy/README.md:158>)。**1 run が 80–220 秒という brief の換算は採らない。** build 再利用・M の同期費用・trace 量による増分を生死確認で測り、`Σ job Elapse < 7200 秒` を投入前に再計算する。4–5 job に分け、各 job に stock 対照と対応する壊しを同居させ、複数計算ノードへ同時投入する。見積り超過なら依頼の 2 node 時間境界に従う。

**(P4/P5) との差。** 起動器の合否へ入れる点は同じ。run 数・時間の旧見積りは今回の job 表と生死確認を加えると根拠が足りない。

## 11. 所有と波及

**結論。** repo で新規・変更するのは `patches/instr-cicada-trace-m.patch`、壊し B/U の二 patch、`patches/README.md` の三 entry、一次資料、spool fragment。repo 外に起動器と job 成果物を置く。`orchestrator/verifier/`、forwarding 三 patch、CCBench gitlink は変更しない。

全 patch 走査 consumer は少なくとも次の三つに新 patch が掛かる。

- `test_p3_s4_loop.py:8692` は全 `.patch` 内の `IZANAGI_` token を走査する。[`test_p3_s4_loop.py:8692`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/orchestrator/tests/test_p3_s4_loop.py:8692>)
- `test_mocc_template_proof.py:95,106` は全 `.patch` を読み、MOCC marker の有無を判定する。[`test_mocc_template_proof.py:95`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/orchestrator/tests/test_mocc_template_proof.py:95>)
- `test_ccbench_spawn_sites.py:684-760` の `_patch_added_define_interfaces()` は全 `.patch` の追加 `#if` 条件語を拾い、登録済み定義一覧と比べる。新条件は `TRACE` だけにし、条件 gate の定義一覧を増やさない。[`test_ccbench_spawn_sites.py:684-760`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/orchestrator/tests/test_ccbench_spawn_sites.py:684>)

世代・abort・inline・U・read API・集計を含めると md_24 の「計装 +150〜250 行、起動器 +50〜100 行」は**目標値であって上限として約束できない**。特に独立した公開記録と呼び出し単位の照合、四 target の TRACE=0 比較、壊しの帰属解析で起動器は 100 行を超えうる。行数より検出面と出力契約を優先し、実装時に実数を報告する。

**(P5) との差。** 所有境界は一致。consumer は新 patch の名前だけで無関係とは扱わず、全件走査の入力として確認する。

## 12. 合否述語の入力と到達可能性

**結論。** 本走前に、各述語の**実際の出力 field**と要求値への到達性を生死確認 job で検証する。到達不能な述語は合否に採用せず、原因と代替観測を段 4 に戻す。合否用の数値と、到達を示す壊し event は別入力として保存する。

| 述語 | 生の入力 | 要求 |
|---|---|---|
| 巡回 | verifier JSON の cycle 件数・判定 field | stock 0、旧壊しは登録した巡回を検出 |
| integrity | verifier JSON の `integrity` 数値 field 11 種 | stock すべて 0。`clean` は使わない |
| C = commit | raw `trace_*.log` の C 行数、stdout の唯一の `commit_counts_` | 一致 |
| 既存 mismatch | stderr の唯一の `CICADA_TRACE_READ_WTS_MISMATCH n=` | stock 0 |
| M 集計 | stderr の唯一の `CICADA_M_SUMMARY schema=1 …` | 各 field を厳格 parse、対象面の checked >0 |
| M 違反 | stderr の `CICADA_M_VIOLATION` と集計の種別件数 | stock 0、壊しは事前登録 kind >0。行数と件数も一致 |
| 壊し帰属 | stderr の壊し event と M 違反の `(thid,tx_seq,key,ver,generation)`、必要なら C 行 wts→txid | 対応一意、`reached≥changed≥committed>0` の該当部分 |

verifier JSON の `integrity.clean` と「数値項目が 0」は異なる。M の `tx_wts` と版の `wts_seen`、trace `txid` と thread 内 `tx_seq` も別名を保つ。C 行の版は `wts>>32`・下位 32 bit であり、txid と混ぜない。[`instr-cicada-trace.patch`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/patches/instr-cicada-trace.patch>)、[`launch_cicada_run_target.used.py:70-94,528-548`](</work/1/SFC/tanab/tmp/vhash-forwarding-target-policy-2026-09-29/jobs/verify2/launch_cicada_run_target.used.py:70>)

生死確認は少なくとも次を同じ計算環境で一回ずつ走らせる。

1. default stock K-t4、BEST stock R-t4、E-max A10-t8。M 集計が各一行、B/U/API checked が該当する workload で正、全違反 0、C/commit と verifier 数値を観測する。
2. 壊し B default と BEST を同じ stock cell と対で走らせる。`reached,changed,committed`、inline read 件数、B 違反 kind と帰属、正常終了を観測する。B 違反 0 なら条件・同期設計を直し、0 のまま本走へ進めない。
3. 壊し U と同 cell stock。公開記録件数、W 件数、`published_without_W`、帰属を観測する。
4. 旧壊し三本のうち一つを M の上に重ね、巡回と M 集計の同時取得を観測する。残りは本走に入れる前に厳密適用を確認する。

時間上限は既存同種 job の **run 実測時間**の最大値 `T_old_max` を生出力から取り、同 cell の TRACE M probe で `T_M/T_old` を測る。`RUN_TIMEOUT_S = ceil(T_old_max × max(2, 1.5×観測倍率))` のように倍率と余裕を事前固定し、build と verifier 時間は別に計る。雛形の 120 秒を無検証で維持しない。[`launch_gcfix_run.py:1028,1461`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/stage7/launch_gcfix_run.py:1028>)。probe の run 時間、trace byte 数、判定時間、job Elapse を保存し、node 時間見積りを更新してから本走を投入する。

**brief の (F-e) との差。** 要求には一致する。新設 field はまだ実成果物に存在しないため、上表は実装契約であり、現時点の達成証拠ではない。

## brief への異議

1. (P1) の「同じ三関数の inline 分岐だけ」は、`Tuple::getInlineVersionRight()`・`returnInlineVersionRight()` と `Tuple::init()` を落としている。[`include/tuple.hh:54-108`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/include/tuple.hh:54>)
2. (P2) の世代番号は、版選択から read set 登録までの窓を閉じない。md_20 の三点比較の 0 件を B 全体の保証に読み替えられない。[`transaction.cc:102-126`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/transaction.cc:102>)
3. 「abort した tx は照合しない」は「生存中の tx が読んだ版」という目的と合わない。少なくとも B は abort の read set clear 前に照合する必要がある。[`transaction.cc:745-756`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/transaction.cc:745>)
4. (P6) の stock 壊し B は `GCFlag` と `MinWts` の条件を満たさないと発火しない。`changed>0` を B 違反の代用にできない。[`util.cc:281-322`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-certified-m/external/ccbench/cc/cicada/util.cc:281>)
5. (P5) の「両系列へ fuzz なしで当たる」と旧壊しとの重ね合わせは、hunk の近接から静的には保証できない。実 patch の厳密適用を合格条件に残す。
6. 20–26 run × 80–220 秒という node 時間見積りは、既存資料の **job Elapse** と **run 時間**を混同する恐れがある。生死確認後に再計算する。

## 総括

1. BEST を M に含め、PROMOTION=0 と `REUSE_VERSION=1` を固定する。
2. B は GC 挙動を変えない世代方式を第一候補とし、登録前の窓を明示する。
3. abort した tx の B 照合を含めるかを確定する。含めない場合は論文文言を狭める。
4. U は公開時の独立記録と W の双方向照合にし、write API intent 未保存の限界を書く。
5. M 出力の固定 field、違反 kind、壊し帰属キーを実装前に固定する。
6. 壊し B の stock site と、到達しなかった場合の forwarding-gc 案への切替条件を決める。
7. patch の両系列・旧壊しとの厳密適用、四 target × 二 genome の TRACE=0 一致を gate にする。
8. 生死確認で全述語の実入力と到達性、run 時間倍率を測り、2 node 時間未満を再見積りして本走へ進む。