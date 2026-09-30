# 段 4 裁定 v2 — md_33 中間案 M の実装 (wave dev-wave-cicada-certified-m、2026-09-30)

入力: s1-brief.md (追補 F-a〜F-e 込み)、plan2.md (段 2 v2)、consult2-a.md (レンズ A)、consult2-b.md (レンズ B)。`invalidated-v1/` は DW-O13 読了遅れで無効化した旧版で、本裁定の根拠にしない。裁定 inbox (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/`) の最新は 2026-09-30-rulings-full40-verdicts.md (= D2305、着手前に既読)、新しい裁定なし。

## 所見の裁定

| ID | 裁定 | 処置 |
|---|---|---|
| plan2 異議 1・B2 (inline の site) | real | 採用。inline の実行中事象は `TxExecutor` の 3 関数 (`gcAfterThisVersion`・`newVersionGeneration`・`writeSetClean`) の inline 分岐に 1 か所ずつ置き、`Tuple` 側には置かない (二重計上を避ける)。世代の初期値は `Version` の constructor。`Tuple::init(body,param)` は初期ロード、`Tuple::init(ver,initial_wts)` は INSERT 経路で範囲外と一次資料に書く |
| plan2 異議 2・A1・B4 (登録前の窓) | real | 採用。下の B 仕様の「登録時 snapshot の妥当性検査」で窓の中の取り違えを検出し、残る場合 (窓の中で同じ object が同じ tuple の別の確定可視版として再利用され、一貫した snapshot が取れた場合) は記録と実行が一致することを論拠とともに一次資料へ書く。論文の文は「読んだ版は登録時点で同じ key の確定済み可視版として一貫しており、登録から tx 終了まで回収・再利用されていない」に合わせ、「選択の瞬間から」は言わない。この論拠は段 6 レビューの攻撃対象に指定する |
| plan2 異議 3 (abort も照合) | real | 採用。abort の read set clear 前でも B・API を照合し commit / abort / read-only を分けて数える。abort の違反も不合格 |
| plan2 異議 4・A5 (壊し B の到達) | real | 採用。下の壊し B 仕様 |
| plan2 異議 5 (厳密適用) | real | 採用。段 5 の子が実測、親が再実測 |
| plan2 異議 6・B5 (見積りの混同・対照の共有) | real | 採用。同一 genome・cell・stack の stock 対照を共有し、生死確認で run・build・判定の時間を別々に測ってから本走の node 時間を再計算 |
| A2 (世代の順序) | real | 採用。下の B 仕様で順序を固定 |
| A3 (U の公開記録は store の後) | real | 採用。下の U 仕様 |
| A4・B1 (API の正例なし) | real | 採用 (一部)。外部 read (c) の登録漏れを起こす壊し `broken-cicada-m-skip-read-register.patch` を足す (forwarding が変える read 経路の失敗型)。(a) 再読・(b) own-write の誤対応と「余分な登録」の発火確認は今回しない。一次資料で「API 照合のうち発火を確かめたのは (c) の登録漏れだけ」と書く |
| A6 (E-max の TRACE=0) | real | 採用。E-max の patch 列で M 無し / 有りも比べる |
| A7 (母集団の独立計数) | real | 採用。tx の begin・commit・abort・read-only commit と `read()` の呼び出しを入口側で独立に数え、照合件数と一致することを起動器が要求する (照合済み = 母集団) |
| B3 (既存 patch を変えない、mismatch 行は回帰指標) | real | 採用。`instr-cicada-trace.patch` は変えない。READ_WTS_MISMATCH は従来どおり 0 を要求するが B の代わりにしない |
| B6 (旧壊し 3 本の役割) | real | 採用。M を重ねた後の巡回検出の回帰確認として各 1 run。M の発火証拠と区別して書く |

refuted: なし。親 brief の撤回: (P1) の「3 関数に足すだけ」の範囲説明 (初期化 2 overload の区別を足す。計装箇所は 3 関数のまま)、(P2) の「世代→wts→世代だけで足りる」、(P6) の壊し 2 本 → 3 本、見積り 0.22〜0.36 node 時間 → 生死確認後に再計算。

## 確定仕様 (plan v3)

**範囲:** YCSB point read / update (INSERT・DELETE・scan なし)、`SINGLE_EXEC=0`・`group_commit=0`・`REUSE_VERSION=1`・`WRITE_LATEST_ONLY=0`。genome = default (`INLINE_VERSION_OPT=0`、他は cmake 既定を明示) と BEST (`BACK_OFF=0`・`INLINE_VERSION_OPT=1`・`INLINE_VERSION_PROMOTION=0`・`REUSE_VERSION=1`・`WRITE_LATEST_ONLY=0`)。stack = stock (`pin C → instr → M`) と E-max (`pin C → instr → variant → gc → target → M`)。

**置き場と適用:** 新規 `patches/instr-cicada-trace-m.patch`。同じ bytes が上の 2 stack の両方に `git apply` で当たる (fuzz なし、offset も出さない) こと、既存壊し 3 本が `pin C → instr → M → 壊し` に当たることを子が実測する。当たらない場合は M の hunk を分割・移動し、それでも当たらなければ止めて報告 (所有外 patch と instr patch は変えない)。新しい `#if` の条件語は `TRACE` だけ、`#else` 側 `#line` で行番号を保つ、patch 内に `IZANAGI_` の語を置かない。

**B (読み束縛):** `Version` に TRACE 専用の `std::atomic<uint64_t> trace_gen_` (constructor で 0、`set()` は触らない) と `trace_last_event_` (最後の事象種別、診断用)。
- 事象 site (版を再利用可能にする / 再利用する瞬間): `gcAfterThisVersion` の pool 積み直前・inline 返却直前、`newVersionGeneration` の pool から取った直後で `set()` の前・inline 権取得直後で `set()` の前、`writeSetClean` の pool 積み直前・inline 返却直前。
- 順序 (seqlock 型): 事象側は `trace_gen_.fetch_add(1, acq_rel)` の後に `atomic_thread_fence(release)`、その後に版の状態を変える。読み手の snapshot は `g1 = trace_gen_.load(acquire)` → wts・status・所属判定の load (acquire) → `atomic_thread_fence(acquire)` → `g2 = trace_gen_.load(relaxed)`。この順序で「snapshot の途中に事象があれば g1 ≠ g2」になることを子が patch のコメントで 5 行以内に論証し、段 6 レビューが攻撃する。
- 登録時 (`read_internal` の `read_set_.emplace_back` の直前、forwarding stack では前進の分岐を含む全経路で登録直前): 合格 = `g1 == g2` ∧ 所属 tuple が一致 (通常版は TRACE 専用 `trace_owner_` を版の生成・再利用 site で設定、inline 版は `&tuple->inline_ver_` との pointer 一致) ∧ status = committed ∧ `wts <= 読み手の基準時刻 (trts)`。不合格は `B_WINDOW`。snapshot の世代を `ReadElement` に保存 (`trace_read_gen_`)。登録直後に `trace_read_wts_` (既存) と snapshot の wts の一致も見る (不一致は `B_WINDOW`)。
- 終了照合: 各経路で Cicada 本体が read set の `ver_` を最後に使った後 (子が file:line で列挙) に `trace_gen_ == trace_read_gen_` を照合。不一致は `B_RETIRED` (`trace_last_event_` を出す)。経路 = 書く tx の `writePhase` (emit の前)、read-only の `commit` 早期 return の前、`abort` の clear 前。
- 論拠 (一次資料へ): body の消費は登録の後 (`read()` が `&ver->body_` を返すのは `read_internal` の登録の後、YCSB は commit 前に消費) なので、登録から終了までの不変で消費した body が記録した版のものであることを担う。登録前の窓で同じ object が同じ tuple の確定可視版として再利用された場合、snapshot はその版の wts を示し R 行もその wts を出すので記録は実行と一致する。版選択規則への適合は主張外 (md_24 §3.1)。

**U (公開):** tx ごとの TRACE 専用記録に 3 種を積む — 設置 (validation の CAS 成功直後、key・版 pointer)、公開 (`cpv()` の各 store の直前に status = pending を確認 (違反 `U_NOT_PENDING`)、store の**後**に status を読み直して期待値と一致したら (key・版・op・その時点の版 wts) を記録、不一致は `U_STORE`)。`traceCommit` の W 走査の前に: 設置集合 = 公開集合 (版 pointer で、違反 `U_INSTALLED_UNPUBLISHED`・`U_PUBLISHED_UNINSTALLED`)、公開集合 = W 行の集合 (key・op の多重集合、違反 `U_MISSING_W`・`U_EXTRA_W`)、公開時の版 wts = C 行の版 (違反 `U_WTS`)。status を committed / deleted にする store の全 site を子が grep で列挙し、`group_commit=0` で `cpv()` だけであることを示す。`group_commit != 0` は TRACE 起動時に異常終了 (実行時 flag なので `#error` でなく実行時検査)。主張は「対象経路で `cpv()` が公開した版と、設置した版と、W 行の照合」に限り、`cpv()` 以前の write set の欠落 (write API intent の保存) は範囲外と書く。

**read 側 API 照合:** plan2 §4 のとおり。abort 分も clear 前に照合。`WARN_NOT_FOUND` と forwarding の `ERROR_PREEMPTIVE_ABORT` は別計数 (前者は YCSB cell で 0 を要求)。

**母集団の独立計数 (A7):** `begin` 数、commit 数 (書く tx / read-only)、abort 数、`read()` 呼び出し数を入口側で数え、集計行に照合件数と並べて出す。起動器は「B 終了照合の tx 数 = commit + abort (read set 非空のもの)」「API 照合の呼び出し数 = `read()` 呼び出し数」「commit 数 = stdout の commit_counts_ = C 行数」を要求する (正確な等式は子が実装に合わせて定義し、段 6 で照合)。

**出力書式 (U2 の正本):**
- 違反: `CICADA_M_VIOLATION kind=<KIND> thid=<n> tx_seq=<n> tx_wts=<n> outcome=<commit|abort|ronly|pending> key=<hex> ver=<0xptr> gen_seen=<n> gen_now=<n> wts_seen=<n> event=<語>` (KIND は `B_WINDOW`・`B_RETIRED`・`U_NOT_PENDING`・`U_STORE`・`U_INSTALLED_UNPUBLISHED`・`U_PUBLISHED_UNINSTALLED`・`U_MISSING_W`・`U_EXTRA_W`・`U_WTS`・`API_EXTERNAL`・`API_REREAD`・`API_OWN_WRITE`・`API_EXTRA_REGISTER`・`API_NOT_FOUND_RESERVED` から子が確定。未使用の値は置かない)。field の順序固定、1 件 1 行、全件出す。
- 集計: `CICADA_M_SUMMARY schema=1 <key>=<n> ...` をちょうど 1 行、既存 `cicada_trace::report()` の中から出す。key 一覧は子が確定し U2 と共有する (段 5 は U1 → U2 の順に直列化せず、U2 には上の必須 key 名を渡し、U1 の確定後に親が突き合わせる)。
- 壊しの診断: `CICADA_BREAK_EVENT slug=<slug> thid=<n> tx_seq=<n> tx_wts=<n> key=<hex> ver=<0xptr> ...` を全件、終了時 `CICADA_BREAK_FIRED slug=<slug> reached=<n> changed=<n> committed=<n> ...` を 1 行 (md_3 の形式を継ぐ)。

**壊し 3 本 (無マクロの無条件、`pin C → instr → M → 壊し`、`cc/cicada/` の中だけ):**
- `broken-cicada-m-early-reclaim.patch` (B、P5 型): `cc/cicada/` 内の単一 site (第一候補は `commit()` の read-only 経路、body 消費の後・照合の前) で、選んだ tx について自 thread の `ThreadRtsArray` をその時点の `MinWts−1` へ上げ、`GCFlag[thid]` を立てながら短く待つ (共有 workload `include/ycsb.hh` は変えない、起動器が `cc/cicada/` 外の touch を拒否するため)。診断は reached・rts_raised・gcflag_set・待機中の `MinRts` の前後・committed と、壊した tx の既読版の (key・ver)。合格 = 同じ (thid・tx_seq・ver) への `B_RETIRED` (または `B_WINDOW`) が 1 件以上、帰属しない B 違反 0、M 側の事象種別 (pool 積み / inline 返却 / 再利用) を内訳で出す。default と BEST で別々に成立確認。到達しなければ本走に進まず、forwarding-gc の待機安全点で P5 を再現する案へ設計変更して段 4 へ戻す。
- `broken-cicada-m-drop-published-write.patch` (U): `writePhase` の `cpv()` の後・`traceCommit()` の前で、選んだ tx の write set から公開済み要素を 1 つ外す。合格 = 同じ版への `U_MISSING_W` (と設置集合との差の違反) が帰属。
- `broken-cicada-m-skip-read-register.patch` (API (c)): 外部 read の一部で `read_set_.emplace_back` を飛ばし body は返す。合格 = 同じ呼び出しへの `API_EXTERNAL` が帰属。巡回が出るかは記録するが合否に使わない。

**起動器 (repo 外、U2):** plan2 §10・§12 のとおり。合否: stock / E-max = 正常終了 ∧ 巡回 0 ∧ integrity 数値項目 0 (`clean` は使わない) ∧ C 行 = commit_counts_ ∧ READ_WTS_MISMATCH 0 ∧ M 集計ちょうど 1 行 ∧ 違反行 0 ∧ 集計の違反件数 0 ∧ 母集団の等式 ∧ 照合件数 > 0 (該当面) ∧ INSERT / DELETE / scan 0。壊し = 事前登録 kind の違反 > 0 ∧ その kind の違反の全件が壊しの事象に帰属 ∧ 他 kind の違反 0 ∧ 同 cell の stock 対照が合格 ∧ 正常終了。旧壊し 3 本 = 既存の巡回帰属規則 (md_3) で「期待した経路で検出」。TRACE=0 同一性 = 4 target × 2 genome の pin C 対 pin C + instr + M、と E-max stack の M 無し対 M 有り (同じ compile command)。run の時間上限は plan2 §12 の式を生死確認で決める。cmake cache・compile command の `-D`・run argv で範囲の固定を三重に確かめる。

## 変異の事前登録 (DW-M01)

repo の pytest は変えない。変異は起動器が一時 checkout に重ねる job dir の patch で行い、tracked file を変えない (DW-M05 の独自 harness: 一時 checkout は run ごとに作り直す)。各壊しは 1 site、各変異は 1 照合だけを常に合格にする。

| ID | 変異 (M の上に重ねる) | 入力 | kill 期待 |
|---|---|---|---|
| MV-B | B の登録時 snapshot 判定と終了照合を常に合格にする | 壊し B (default) | 起動器が「未発火」(B 違反 0) と分類し、壊しの診断 reached > 0・rts_raised > 0 |
| MV-U | U の照合を常に合格にする | 壊し U | 「未発火」(U 違反 0)、診断 changed > 0 |
| MV-API | API 照合を常に合格にする | 壊し API | 「未発火」(API 違反 0)、診断 changed > 0 |

## 計算

生死確認 job 1 本 (1 node) を先に投げる: default stock K t4、BEST stock R t4、E-max A10 t8、壊し B default と BEST (と各専用 cell の stock 対照)、壊し U、壊し API (default K t4 を対照に共有)、旧壊し skip-read-recheck K t4、TRACE=0 同一性の一部 (default・BEST の ycsb target)。観測: 各述語の入力 field の実在と値、run・build・判定の時間、trace の bytes。これで run 時間上限と本走の node 時間を再計算し、合計 (生死確認を含む) が 2 node 時間以上なら本走を投げず見積りを一次資料に書いてユーザー確認を求める。本走は残りの run と変異 3 本と TRACE=0 同一性の残りを 4〜5 job に割って同時投入。

## 段 5 の分割

- U1 (worktree `/work/1/SFC/tanab/izanagi/.codex/worktrees/cicm-u1`、branch `dev-wave-cicm-u1`): `patches/instr-cicada-trace-m.patch`、壊し 3 本、変異 patch 3 本 (木の中の `.m-work/mutations/`、親が job dir へ退避)。
- U2 (worktree `/work/1/SFC/tanab/izanagi/.codex/worktrees/cicm-u2`、branch `dev-wave-cicm-u2`): 木の中の `.m-work/launcher/launch_cicada_m.py` (と必要なら job 投入 script)。親が job dir へ退避。U1 と並列。
