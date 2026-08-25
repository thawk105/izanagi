---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t1574-t1529-t1495-swo-isolation
seq: 1
---

## {{D:swo-isolation-boundary}}. sort SWO oracle の隔離境界を採用し、保証しないことを exact field で固定する

**決定 (D766 の要求に対する実装と、その保証範囲の確定):**

候補 comparator は worker process で走らせる。hardened worker が停止したことを確認してから
初めて Python 側が final protocol pipe を作り、broker が `SCM_RIGHTS` で受領する。broker は
受領後に fork せず、worker を完全に reap してから final frame を書く。worker から broker への
内部 channel は候補自身が返す bool の列だけを運び、違反の判定 (corpus write / abort /
sandbox 違反 / 呼出し回数逸脱) はこの channel の内容から導かず broker の `waitid` 結果だけから決める。

corpus は匿名 arena へ集約する。構築 phase に限定した global `operator new` / `operator new[]`
(aligned overload を含む) を arena へ向け、全 nonzero pointee range を inventory して
arena 外が 1 つでもあれば fail-closed とし、その後 `mprotect(PROT_READ)` する。
候補実行前に arch 検査付き default-deny allowlist seccomp を導入し、拒否は
`SECCOMP_RET_KILL_PROCESS` とする。`rt_sigaction` / `rt_sigprocmask` / `sigaltstack` /
`mprotect` / `mmap` / `munmap` / `mremap` / `pidfd_getfd` / `io_uring_*` / `dup*` / `fcntl` /
`recvmsg` / open 系 / `ptrace` / `process_vm_writev` を allowlist に入れない。
filter install・`no_new_privs`・arch 検査のいずれかが失敗したら候補を実行せず停止する。

**保証するもの:** 候補が protocol write fd を一度も所有しないこと。候補が
実 `WriteElement<Tuple>` の snapshot 対象 memory を変異させられないこと。

**保証しないもの (exact field として receipt に持たせる):** 候補が報告した関係行列が、
その comparator の真の関係であること。`active_write_set` / `active_order` / `sort_called` /
`relation[]` は候補と同じ address space の書込み可能領域に残る。
これを閉じるには候補を副作用のない検証済み IR へ制限して trusted interpreter で評価するか、
broker が `ptrace` 相当で戻り値を採取するかが要り、いずれも本決定の範囲外である。

**理由:**
- D766 が挙げた 2 条件は fd capability と snapshot memory であり、関係行列の provenance を
  含まない。実装した境界はその 2 条件を満たすが、それ以上を主張してはならない。
  非主張を receipt の field にしないと、読み手には恒真な保証と区別が付かない。
- 封印 (`memfd` + `F_SEAL_WRITE`) は採らない。生きた非 trivial C++ object の storage を
  `munmap` すると object lifetime が終わり、同アドレスへ貼り直しても placement new なしの
  使用は未定義動作になる。正しさ検査器を未定義動作の上に立てられない。
  加えて封印は memfd object の bytes を守るがアドレス範囲を守らず、
  候補が `munmap` して匿名の書込み可能 memory を同アドレスへ貼れることを実測した。
- `waitid` は fault address も access type も返さない。したがって `SIGSEGV` / `SIGBUS` を
  corpus write と断定しない。一般の execution fault として分類する。
  8 つの allocation class がすべて拒否されることは変わらず、変わるのは台帳に載る主張だけである。

**却下した選択肢:**
- 親が fd を持ったまま `fork` し子で直後に `close` する — 子は短時間でも fd capability を継承し、
  D766 の「一度も所有しない」を満たさない。
- seccomp denylist — filter の列挙漏れが 1 つあれば保証が落ちる。
- `mprotect` だけ・封印だけ — 前者は候補が解除でき、後者はアドレス範囲を守らない。
  両者は互いを包含しないため併用も検討したが、object lifetime の問題で封印は採らなかった。
- 候補 TU から magic や writer helper の名前を除くことを防壁に数える — 隠蔽であり、
  D696 と D766 が防壁として数えることを禁じている。実装はしてよいが negative control の根拠にしない。

## {{D:swo-dependency-manifest-location}}. oracle の依存 manifest hash は test fixture 側に置き、共有 policy へ書かない

**決定:** D399 が「`expected config.h hash` をどこへ置くかは D115 と D152 の双方に抵触しうる
未解決の設計択一であり、裁定が要る」と残していた残余を閉じる。masstree の pin 済み source と
生成 `config.h` を test fixture として repo が所有し、その全 file の SHA-256 manifest を
contract components schema へ 1 component として加える。共有 policy は 1 byte も変更しない。

検証は production 側に置き、検証済み bytes を private scratch へ複製してそこを `-I` に渡す。
compile 前後で manifest を再検証し、`-M` の dependency closure が manifest 内にあり
期待母数を満たすことを検査する。receipt の manifest hash は固定値でなく実際に compile した
private copy から導く。

**理由:**
- D399 は「共有 checkout でしか成立しない祖先 fallback に依存し続けると、login で緑・
  計算ノードで赤という再現しない失敗が残る」と既に退けていた。fixture 所有はその直接の帰結である。
- 同じく D399 が「masstree の `config.h` は上流 `.gitignore` が除外する生成物で Git 非管理であり、
  HEAD を固定しても中身は自由に変わりうる」と記していた。HEAD pin だけでは受理集合が固定できない。
- fixture の manifest は共有 policy ではないので D115 (共有 policy 不変) に触れず、
  cache root を policy から導出しないので D152 にも触れない。
- 検証器が production compile 経路から切れていると、receipt が canonical manifest を主張しながら
  compiler が実際に読んだ bytes と結ばれない。manifest hash を固定値で書くのはその状態である。

**却下した選択肢:**
- 共有 policy へ `masstree_config_sha256` を足す — D152 に反し pin が二重正本になる。
- 検証を test 側だけに置く — production の受理集合を拘束しないので、receipt の主張が空になる。
- `config.h` を手書きの最小版にする — autoconf 生成 header を手で再現するのは誤りの温床であり、
  上流と乖離した受理集合を静かに作る。上流生成物を逐語で pin する。

## {{D:swo-oracle-assert-strictness}}. oracle は本番 build より厳しい assert 設定で候補を判定する

**決定:** `_COMPILE_FLAGS` の末尾へ `-DFORCE_ENABLE_ASSERTIONS=1` を加え、全 include の後に
`#ifdef NDEBUG` の `#error` sentinel を置く。ccbench 本体は masstree を
`./configure --disable-assertions` で建てるため、そのままでは oracle の翻訳単位で
NDEBUG 依存の上流 assert がすべて消える。oracle はこれを継がず、常に assert を live にする。

同時に corpus の全要素へ実 body と nonempty write value を与え、`body_.get_val()` を読む
合法な候補が正例として通るようにする。候補由来の abort は `UNAVAILABLE` でなく構造化 reject に分類する。

**受理集合は両方向へ動く。** assert が live になることで上流事前条件を破る候補は reject 側へ動き、
実 body が入ることで body を読む候補は accept 側へ動く。

**理由:**
- 変更前は「同じ候補の判定が、依存 masstree をどう configure したかで変わる」状態だった。
  proof chain が機体依存であり、正しさ検査器としてこれを許せない。
- `FORCE_ENABLE_ASSERTIONS` は masstree 自身が `config.h` に用意した switch であり、
  上流の改変にも `-DNDEBUG` の追加にも assert の緩和にも当たらない。
  D696 が却下した 3 案のどれでもない。
- 検査器の目的は本番 build の再現ではなく違反の検出である。忠実性より検出力を採る。
- body を空のまま assert abort を常態化させる案は、実 `WriteElement` の代表性を落とし、
  合法な候補を構造的に拒否する。

**却下した選択肢:**
- oracle の assert 設定を本番 build に合わせる — 事前条件違反を検出できない。
  この択一はユーザーが上書きしうる。
- `-DNDEBUG` を足す / 上流 `view()` の assert を緩める — D696 が規律 2 違反として却下済み。
- flag を tuple の途中へ入れる — 位置で `COMPILE_FLAGS_SHA256` が変わり、
  実装者依存の identity になる。末尾で固定する。
