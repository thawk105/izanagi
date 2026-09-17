# [T-2757] mocc を変異探索面へ入れる前の、独立の auditor-live 相当の機械実証 — 設計 (2026-09-17)

authority: none
default_effect: no-state-change

- wave: `dev-wave-t2757-mocc-mutation-proof-design` (branch `worktree-dev-wave-t2757-mocc-mutation-proof-design`、docs のみ、実装面 0 byte)
- 起点: ユーザーの `/dev-wave [T-2757]` 引数 (D2114 項 1、D579)。一次資料 = `output/insights/2026-09-17/cross-protocol-scope-release/README.md` §6
- 逐語: `verbatim/` (親 brief、段 2 plan、段 3 レンズ A / B、段 4 裁定、prompt 3 本)。sha256 は `verbatim/MANIFEST.json`
- 計測・build: なし。本 wave は設計だけを行い、コード・patch・テスト・driver を 1 byte も書いていない

## 0. 位置づけと非解禁 — この文書が認可しないこと

D579 は「将来 `cc/mocc/transaction.cc` を Phase 3 の変異探索対象 (EVOLVE_BLOCK hole) にする wave は、trace-hook 許可を safety net と
みなさず、独立の auditor-live 相当の機械実証を別途用意すること」と定めた。本文書はその**実証の設計**を後続実装者が使える形で固定する。

**この設計の完了は、次のどれも認可しない。**

- mocc を変異探索面へ入れること (D579 の限定は不変)。
- pin 前進 (D2114 項 3、D1603 の材料 3 点 → [T-167] 再承認の手続きは不変。D1373 の関門を迂回しない)。
- 温度述語を正式な変異軸として採用すること (`docs/axis-onboarding.md` の段階 A (人間承認) / B (敵対レビュー) は別途要る)。
- certified な合成・評価の開始。**後続の実証 wave が緑になっても、それだけでは探索の認可にならない。** 実証 wave の緑は「D579 が要求する証拠が
  揃った」ことを示すだけで、探索開始は pin 手続きと producer の proof surface (§11) が別途揃ってからの判断である。

## 1. 出発点 — Silo 版 auditor-live の定義と、mocc で既に済んでいる部分

D38 決定 4 が定めた auditor live = **機械 4 点 + n=1 定性 2 点**:

| # | 点 | Silo での実体 | mocc での現状 (本 wave 開始時点、main `38353207f`) |
|---|---|---|---|
| 1 | auditor.md 実体化 | `.claude/agents/auditor.md` (ギャラリー型 1〜21、チェックリスト 14 項) | 実体は共有。ただし型 8 (`write_set` の一部を lock せず)・型 9 (`check.lock && !searchWriteSet`)・型 13 (`silo-writeset-sort`)・型 16 (`silo-backoff-trigger-gating`) とチェックリスト 11〜13 は Silo の識別子を名指し。mocc の識別子 (`CLL_` / `RLL_` / `ReaderWriterLock` counter / 温度) は 1 箇所も無い |
| 2 | 被覆 assert が実 variant で発火 | lockskip / early-unlock (D38)、permutation (D41) | **patch 水準で済** (T-2294、D1686): `patches/broken-mocc-{lockskip-validation,permutation-erase,early-unlock}.patch` で X / P が発火、compute 実走 14 check all_pass (`output/env/pegasus/calibration/s3_mocc_lock_coverage.json`) |
| 3 | positive control suite の赤/緑 | pytest + `s3_lock_coverage.py` all_pass | **済** (T-2294): `orchestrator/tests/test_mocc_proof_surface.py` 21 node + `orchestrator/campaign/s3_mocc_lock_coverage.py`、変異 matrix 19/19 KILLED |
| 4 | 入力隔離の構造 | Read-only + 入力射影 | 構造は protocol 非依存 (共有) |
| 5 | fresh auditor が hack diff を独立検出 (n=1) | `output/insights/2026-07-06_s3-auditor-live-n1.md` (A=lockskip reject) | **未** |
| 6 | negative control (benign diff) を pass (n=1) | 同上 (B=benign reorder pass) | **未** |

D579 が「閉じない」と明記した 3 点のうち X/P は T-2294 で閉じ、**I 行 (T-152 write-intent) と hot/cold** が残っていた。
Silo の gate (`orchestrator/tests/test_campaign.py::test_lock_path_edit_surface_requires_auditor_live`) は
「`cc/silo/transaction.cc ∈ EVOLVE_BLOCK_SOURCES` ⟹ `s3_lock_coverage.json` all_pass」の含意で、**mocc は D579 で既に
`EVOLVE_BLOCK_SOURCES` に居る** (`orchestrator/campaign/source_digest.py`、3 要素目) ので、同じ前件は mocc に対して常時 true になり、
「trace-hook 用の所属」と「変異面の導入」を区別できない (§10)。

**過去の実測と、今回初めて要求する保証は分ける (レンズ A 所見 7)。** T-2294 の 14 check・19/19 KILLED は当時の資材 (計装 patch・負例 3 本・
workload 2 種) に束縛された実測であり、hot/cold や新 template の保証には転用しない。19/19 のうち patch SHA 不一致による consumer 拒否は
独立した意味検出力に数えない (T-2294 README §4 の注)。

## 2. mocc の lock 経路の現物 (hook branch 先端 `e9e477ca`、`cc/mocc/transaction.cc`、行番号は同 commit のもの)

| 経路 | 行 | 何をするか |
|---|---|---|
| `read_internal` の hot/cold 分岐 | 296 | `loadepot.temp >= FLAGS_temp_threshold` なら `lock(tuple, false)` (r_lock) を取り `needVerification=false`。cold は OCC 再読 loop (316〜356)、hot は tidword 1 回 load + payload 読み (357〜363)。どちらも `read_set_.emplace_back(..., expected)` (364) |
| abort 後の再試行 | 280〜292 | `inRLL != nullptr` なら温度に関係なく `lock(tuple, inRLL->mode_)` |
| `update` の hot 施錠 | 459 | hot なら `lock(tuple, true)` を update 時点で取る (cold は validation まで取らない)。RLL に居れば温度に関係なく取る (473)。write_set_ 登録は 477 |
| `delete_record` の hot 施錠 | 566 | update と同型 (RLL は 580) |
| `lock()` | 720〜900 | CLL_ を sort し canonical mode を判定。violation があれば末尾を unlock + erase (834〜858)、RLL_ の先行要素を無条件 lock (860〜882)、最後に本命を `w_lock()` / `r_lock()` して CLL_ に積む (884〜888)。`vioctr > 100` の trylock 枝 (750〜810) |
| `construct_RLL` | 902〜983 | write_set_ 全部 (905〜913) と、`failed_verification_` または hot な read (970) を RLL_ に積む。温度の上昇則は 941〜953 (`rnd_.next() % (1 << temp) == 0` で +1、`TEMP_MAX` 20) |
| `validation` phase 1 | 989〜1000 | `sort(write_set_)` 後、非 INSERT を `lock(rcdptr_, true)` (993) — この sort が P 検査の対象 (D1686) |
| `validation` read 検査 | 1008〜1039 | read_set_ 全要素を経路に関係なく tidword (epoch, tid) 比較 (1010〜1013) し、`W_LOCKED ∧ searchWriteSet == nullptr` なら abort (1024〜1036) |
| `writePhase` | 1115〜1213 | C/R/W 行 (TRACE)、payload `memcpy` (1169)、tidword publish (1195)、`unlockCLL()` (1207)。D1686 の X 検査点 3 つ = 入口 / payload 直前 / publish 直前 |
| 温度の runtime flag | `cc/mocc/include/common.hh:40` | `DEFINE_uint64(temp_threshold, 10, …)` — build define ではなく gflag。0 で温度述語が常に true、`TEMP_MAX`(20) 超で常に false |
| YCSB の操作生成 | `include/ycsb.hh:65〜73, 128〜133` | `ycsb_rratio=0` かつ `ycsb_rmw=false` なら全操作が `Ope::WRITE` → `tx.update()` の直接呼出 (read_set_ を作らない blind update) |

## 3. 現物検算で分かったこと — 安全論拠の限定と、stock mocc の静的反例候補

### 3.1 親 brief の新事実 (段 3 が訂正した部分を反映)

- **F-a: T-2294 の compute 実走 6 走は hot 経路の実行証拠を持たない。** 温度は `construct_RLL` (abort 経由) の `failed_verification_` でしか上がらない。
  1 thread の 4 走は「単一 thread では競合が無く温度が上がらない」という code からの推論で全記録が温度述語 false と見なせる (abort 数は JSON に
  無く、実測値ではない)。4 thread の 2 走も hot 到達の計数・hot 専用負例が無く、「X 検査は hot 経路でも歯を持つ」は未実証。
  JSON の `runs.*` に hot/cold を弁別する field は無い。
- **F-b (撤回・限定):** 親 brief は「hot/cold は正しさの入力ではない (torn read は validation で必ず捕まる)」と書いたが、**この証明は成立しない**
  (§3.2)。本設計は「温度述語の変更は骨格 (validation・CLL/RLL・X/P 計装) を変えないので、**既存防壁の保存と発火範囲を検査する**」設計とし、
  hot/cold 自体の正しさ非関与を定理として置かない。
- **F-c: I 行 (write-intent、T-152) は Silo の auditor-live 機械 4 点に含まれていない。** Silo の gate が読むのは `s3_lock_coverage.json` (X のみ)。
  P は D41 が sort 軸のために足し、I は「別 pin として承認済み・未統合」(D1603) のまま。
- **F-d (訂正):** mocc の proof 実走は**現行 pin を前進させずに実施できる** (T-2294 の driver は `patchharness.checkout(e9e477ca)` で fresh
  checkout を作り、superproject の gitlink を動かさずに compute で走った)。ただし pin 非依存ではなく、e9e477ca の full SHA と patch SHA に
  強く束縛される。変異探索 loop (`orchestrator/campaign/p3_s4_loop.py` の `PIN` は `511c9538…` の literal) と certified 比較は
  D1373 の関門 = pin 前進を要する。

### 3.2 stock mocc (RWLOCK 版) の静的反例候補 2 件 — 実走未確認、還元判断: ユーザー確認待ち

**(a) 版と counter の別読みによる観測間隙 (レンズ A 所見 1)。** cold 読み (316〜356) は counter 検査 (322) → body 読み (347〜348) → 版の再読 (350〜352)
の順で、validation (1008〜1039) は版 (1010〜1013) と counter (1024) を別々に読む。次の順序は現物の code だけでは排除できない。

1. reader R が x の旧版 T0 を取り (320)、counter が非 writer であることを確認する (322)。
2. writer W が x を正常に施錠し payload を更新する。R の body 読み (347〜348) がその途中に重なる (torn body)。
3. W の publish 前なので R の再読 (350) も T0 で loop を抜ける。
4. R の validation で版比較 (1010〜1013) は T0 == T0 で通る。**その直後、counter 読取 (1024) の前**に W が publish (1195) と unlock (1207) を済ませる。
5. R は解放済み counter を読み、版比較・writer 検査の両方を通って commit する。

Silo は lock bit を tidword に同居させるので版の再読が lock 状態も同時に見るが、mocc の RWLOCK 版は lock を別 counter に持つため、この
順序が構造的に残る。hot 読み (357〜363) から r_lock を抜いた場合も同じ隙間になる。**これは stock の性質であり、温度述語の hole とは独立。**
W の X/P は正常なので既存計装では観測できない。

- 発見: cold 読みと validation の版/counter 別読みにより torn read が commit しうる (静的)。
- 再現条件: 未実走。多 thread・hot key・小さい value で発生確率が上がると推定 (根拠なし、仮説)。
- 該当コード: `cc/mocc/transaction.cc` 320〜352、1010〜1013、1024、1169、1195、1207 (e9e477ca)。
- 仮説: D2114 が「実装由来か hook 由来か未確定」とする mocc の G2 anomaly 5/42 の**根因候補**。T-1943 (1 cell、no-G2) は否定していない。
- 還元判断: ユーザー確認待ち。実走検証は worklog の新規 T へ。

**(b) hot 読みの `absent` 非対称 (段 2 plan、親が現物確認)。** cold 読みは `expected.absent` で abort する (341〜344) が、hot 読み (357〜363) は
検査せずに body と版を読む。DELETE を含む workload では、削除済み record を hot 経路で「存在する」として読み、validation の版比較を通る
組合せがありうる (静的、GC 寿命・API 挙動を含む実走確認は未実施)。YCSB には DELETE が無いので本設計の実証範囲には入らない
(T-2294 README §6 の「DELETE 経路は build と静的読解のみ」と一致)。

- 還元判断: ユーザー確認待ち。

**この 2 件が意味すること:** 「X + P + validation 無傷」は mocc 全体の正しさを証明する集合ではない。本設計が固定するのは、温度述語の
変更に対して**既存防壁が保存され、発火範囲が実測で示される**ことまでである。mocc は確実な第 2 成功例ではない (D2114 理由節) — 「名指し条件で
成立可否を判定できる」ことが最初の到達点であり、その判定には (a) の実走検証が要る。

## 4. hole 候補の比較と採用案

| 候補・位置 | 正しさとの関係 | 骨格 (template) が触る行 | 読取契約 | 該当する既知型 / 評価 |
|---|---|---|---|---|
| **温度述語**: 296 / 459 / 566 / 970 の 4 site を file-scope inline helper の 1 hole に括る | 早期施錠と再試行集合の方針。最終 validation・CLL/RLL・X/P を変えない (§3 の限定つき) | file-scope (18〜22 付近) に helper、4 述語を呼出へ。970 の `|| failed_verification_` は骨格に残す | 骨格が値渡しする `temp`・`threshold`・コンパイル時定数だけの pure な bool 式 1 個 | 型 3/4、8/9、11/13、15/16。mocc 固有 (MOCC を MOCC たらしめる knob)、編集範囲が小さい → **proof の接続先候補として採用** |
| 温度上昇則 (941〜953、特に 943) | 更新方針。shift 範囲・`TEMP_MAX`・CAS・epoch reset を巻き込むと UB・状態破壊 | 943 の判定 + 乱数を骨格で採取する追加行 | 現温度と骨格が採った乱数の値渡し。hole 内 `rnd_.next()` 禁止 | 契約と被覆証明が温度述語より大きい → 見送り |
| `lock()` の `vioctr > 100` (770) | trylock/abort と解放・再取得の選択。liveness・施錠経路への影響が広い | 770 + helper | `vioctr` と定数だけ | 既存 `max_ope=5` では stock の `>100` 枝の実行証拠を得にくい → 見送り |
| abort の backoff (1079〜1089、特に 1084) | cleanup 後の待機。correctness から最も遠い | 1084 の gate または値 hole | D48 と同型 | D48 とほぼ同型で mocc 固有性が薄い (実装費用ではなく固有性を優先した選択) → 見送り |

**採用の意味 (レンズ B 所見 1):** 温度述語は **proof の接続先候補**である。正式な軸としての採用は `docs/axis-onboarding.md` の段階 A (人間承認) /
B (3 レンズ敵対レビュー、軸定義シートの偵察列挙空間・計測動作点の確定) を別途通す。本 wave の段 3 は 2 レンズで、軸定義の仕事はしていない。
軸が別の hole に変わった場合、§5〜§6 の template 依存部分だけを再検証し、経路共通部分 (§7〜§8) は再利用する。

## 5. template (骨格) と読取契約 — 実装 wave 2 の要件

候補名: marker id `mocc-temperature-predicate`、template `patches/mocc-temperature-predicate-variant.patch`、軸定数 module
`orchestrator/campaign/axis_mocc_temperature.py` (前例 `axis_trigger_gating.py` の**方式を機械転写せず**、PIN の扱いは現行の承認契約に従う)。

- file-scope inline helper に**唯一の** EVOLVE-BLOCK を置く。hole は bool を返す式 1 個。marker 内は `#if / #else / #endif` 1 組
  (`diff_quarantine.py` の parser 契約)。4 個の marker に分割しない。
- helper の引数は温度と閾値の値渡しだけ。型は元の `loadepot.temp` と `FLAGS_temp_threshold` の型を保存する (宣言元は
  `cc/mocc/include/tuple.hh` / `common.hh`、実装時に確認)。
- 296 / 459 / 566 / 970 の比較を helper 呼出へ置換する。**契約 = 4 site で同じ温度分類を使う** (レンズ B 所見 5)。970 の `|| failed_verification_`、
  lock 呼出、status 判定、CLL/RLL 操作、validation、write_set_ 登録 (477) は固定 (骨格)。
- OFF (既定 0) 側では helper 宣言も消し、4 site の元の比較文を逐語保存する。「helper を常駐させて最適化で消えるから inert」とはしない —
  source identity は前処理本文の一致で決まる (`source_digest.py`)。
- flag 配線: `cmake/Options.cmake` の universal 相乗り (`CCBENCH_MOCC_TEMP_PREDICATE` → `MOCC_TEMP_PREDICATE`、既定 0)。親が現物で確認:
  `ccbench_add_protocol` (cmake/ProtocolHelpers.cmake:19〜29) が `ccbench_universal_definitions` を全 protocol に供給するので、Silo 軸
  (`SORT_VARIANT` / `BACKOFF_TRIGGER_GATING`) と同じ方式で mocc TU に届く。`cc/mocc/CMakeLists.txt` (ALLOWLIST 外) は触らない。
- 読取契約 = 「`temp`、`threshold`、bool / 整数定数による比較・論理結合のみ」。代入先追加、参照・pointer、関数呼出、型定義、global、`FLAGS_*` の
  直接参照、`thid_`、`result_`、CLL/RLL/read/write/node container、乱数、時刻、TRACE 判別を禁止する。D48 決定 2 (要因 enum + コンパイル時定数)
  を**そのまま転記しない** — 今回は CC-native な温度と runtime threshold の値渡しを明示的に許す別契約である。
- 閾値 0 / 21 による hot / cold 強制は stock と stock 等価な述語 (B) について成立する。`temp >= 11` のように引数 threshold を使わない候補へ同じ
  強制被覆を自動的に主張しない。

**4 site の効果と実証範囲 (レンズ B 所見 5):**

| site | 効果 | 静的確認 | 動的確認 (本設計) |
|---|---|---|---|
| 296 read の hot 分岐 | r_lock を読み前に取るか | 骨格固定・DQ | **なし** (§6 の負例は update 分岐のみ) |
| 459 update の早期 w_lock | validation 前に w_lock を取るか | 同上 | hot 専用負例 (§6) |
| 566 delete の早期 w_lock | 同上 (DELETE) | 同上 | **なし** (YCSB に DELETE なし) |
| 970 construct_RLL の read 追加 | abort 後の再試行で read を pre-lock するか | 同上 | **なし** (RLL 経路の witness は未設計) |

## 6. hot 専用負例と実行証拠 — 保証名を固定する

**択一: 「負例の発火で hot 経路 (update 分岐) の実行を示す」を採る。計数 line は足さない。** 保証名は
**「stock 等価述語における hot-update 負例の到達と、既存 X 3 検査点の検出」**に固定し、4 site 全被覆・read 側 hot 経路・RLL 再試行・候補ごとの
型 4 (空振り) を含意しない (レンズ A 所見 3)。read 側の独立 witness は設計上の選択肢として残すが、本設計の要件にはしない。

新設候補: `patches/broken-mocc-hot-update-unlock.patch`、裸 define `IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK`。

1. 459 を温度述語 true の block に展開し、`lock(tuple, true)` が成功した直後だけ `w_unlock()` して、対象 pointer を診断専用の thread-local
   pending に記録する。CLL の writer 記録は残す。
2. validation の 993 は変更しない。CLL に writer 記録が残るため `lock()` は 744〜746 で戻り、**実 counter が欠落したまま**既存 X 検査へ到達する。
3. writePhase の publish 検査後・1195 の store 前に、pending の lock を **`pending->rwlock_.w_lock()` で直接**再取得し pending を消す
   (`TxExecutor::lock()` を使うと stale CLL で再取得が省略され、末尾の `unlockCLL()` が counter を `0 → 1` に壊す — レンズ A 所見 2)。
4. abort に流れた場合は 1069 の `unlockCLL()` **前**に同じ方法で再取得して消す (二重 unlock 防止)。
5. 裸 directive は owner file に 1 回 (condition gate の exactly-one 契約、D1686)、複数 site は `if constexpr` で従わせる。診断専用状態の TRACE 隔離と
   `#line` 復元 (D1687) を確認する。

**発火 workload U = `ycsb_rratio=0, ycsb_rmw=false, ycsb_max_ope=1`** (他は T-2294 の SINGLE/HIGH と同じ)。親が現物で確認: この組合せは全操作が
`Ope::WRITE` → `tx.update()` の直接呼出になり、read_set_ を作らず 1 txn = 1 update。多操作 (T-2294 の W = rmw=true / max_ope=5) では次の
`lock()` の canonical restore (834〜858) が stale CLL 要素を再解放しうるので balanced にならない。

期待 (1 thread、hot 強制 `--temp_threshold=0`): `not-locked-at-entry` / `lock-lost-before-write` / `lock-lost-before-publish` の 3 reason が
それぞれ正数、cycle 0、verdict indeterminate。cold 強制 (21) と既定 (10、初期温度 0・blind update で温度上昇なしの前提つき) では沈黙し stock と
同じ certified。timeout・hang は失敗として扱い、完走未確認を「balanced 実証済み」と書かない。4 thread は counter に owner が無いため reason
ごとの正数を保証せず観測のみ。**同じ workload U の stock 対照 (6 走) を必ず併走させる** (負例が stock まで赤になる恒真負例でないことの対照)。

## 7. 実証 matrix (36 走) と check 契約

走 = 3 regime (hot 0 / cold 21 / default 10) × 2 thread (1 / 4) × 対象 {stock-W、lockskip-W、perm-erase-W、early-unlock-W、hot-update-unlock-U、
stock-U} = 36。stock は X/P 計装付きで、template を使う場合は ON の stock 等価述語 B で走る。略号: E/W/T = X の 3 reason、C = cycle、
S = serializable かつ certified、I = indeterminate、N = non-serializable。

| regime | 対象 | thread 1 | thread 4 | 区分 |
|---|---|---|---|---|
| hot / cold / default | stock-W | S、X/P=0、C=0、非 INSERT write>0 | 同左 | **受入必須** (6 走) |
| hot / cold / default | stock-U | 同上 | 同上 | **受入必須** (6 走、負例の対照) |
| cold | lockskip-W | I、E/W/T>0、P=0、C=0 | X>0、P=0 (C>0 なら N、C=0 なら I) | **受入必須** (2 走) |
| default | lockskip-W | I、E/W/T>0、P=0、C=0 | X>0、P=0、C は固定しない | **受入必須** (2 走) |
| hot | lockskip-W | X の発火量は不確実 (早期 lock が欠落を補う場合がある)。X>0 なら I | 観測 | 観測のみ (2 走) |
| hot / cold | perm-erase-W | I、X=0、P=`size-changed`>0、C=0 | P>0、X=0 を期待、C は固定しない | **受入必須** (t1 の 2 走)、t4 は観測のみ |
| default | perm-erase-W | 同上 | 同上 | 観測のみ (2 走、旧 JSON の default/t1 と同条件だが template 状態が違えば別命題) |
| hot / cold | early-unlock-W | I、E=0、W/T>0、P=0、C=0 | E=0、保持違反>0 を期待 | **受入必須** (t1 の 2 走)、t4 は観測のみ |
| default | early-unlock-W | 同上 | 同上 | 観測のみ (2 走) |
| hot | hot-update-unlock-U | I、E/W/T>0、P=0、C=0 | X>0、P=0 を期待、reason 別正数は保証しない | **受入必須** (t1)、t4 は観測のみ |
| cold / default | hot-update-unlock-U | S、X/P=0、C=0 | S、X/P=0、C=0 | **受入必須** (4 走) |

受入必須の走は各 1 つ以上の check に対応させ (下表)、観測のみの走には未実測の正数を要求しない。hang・欠落・別 integrity 異常
(`version_dups` / `dup_txids` 等) は区分を問わず赤。多 thread の cycle 正数 (T-2294 の 3,754) は既観測値であり受入条件にしない。

| check 名 (候補) | 対応する必須走 / 要求 |
|---|---|
| `stock_{hot,cold,default}_{t1,t4}_certified_and_silent` | stock-W 6 走 |
| `stock_u_{hot,cold,default}_{t1,t4}_certified_and_silent` | stock-U 6 走 |
| `cold_lockskip_t1_three_reasons_cycles_zero` / `cold_lockskip_t4_x_positive` / `default_lockskip_t1_three_reasons_cycles_zero` / `default_lockskip_t4_x_positive` | lockskip 4 走 |
| `perm_{hot,cold}_t1_only_size_changed` | perm-erase t1 2 走 |
| `early_unlock_{hot,cold}_t1_retention_without_entry` | early-unlock t1 2 走 |
| `hot_update_unlock_hot_t1_three_reasons_cycles_zero` | hot 専用負例の主証拠 |
| `hot_update_unlock_{cold,default}_{t1,t4}_silent` | 負例が対象経路以外で沈黙 (4 走) |
| `matrix_runs_complete_and_terminated` | 予定 36 走の実 argv・終了状態・verifier record の欠落なし (存在・完走の検査であって期待値の検査ではない) |
| `hot_path_evidence_method_is_negative_control` | JSON の `hot_path_evidence.method == "negative-control"` と保証名 (§6) の文字列固定 |
| `trace0_nm_izanagi_zero` / `trace0_strings_izanagi_trace_zero` / `trace0_logical_rows_identical` | 規律 1 (D14 / D1687)、同一 template 状態で計装なし↔あり |
| `toolchain_matches_policy` / `all_broken_patch_touch_sets_are_transaction_only` | T-2294 と同型 |
| (wave 2 のみ) `template_off_stock_identity` / `template_on_benign_identity_distinct` / `quarantine_accepts_benign_hole` / `quarantine_rejects_frozen_frame_and_outside_edits` / `auditor_digest_and_deny_only_controls` / `consumer_binding_controls` | §8 / §9 / §10 |

**DQ 拒否対照の対応 (wave 2、段 4 A6 / 段 2 plan):** `quarantine_rejects_frozen_frame_and_outside_edits` は、mocc の実 template と実 working diff に対する
parameterized control とする。stock 枝改変は `frame-altered`、970 の fallback 削除・CLL/RLL・validation・X/P 計装・write_set_ 登録 477・RLL 構築
905〜913 の侵食は `outside-region`、hole 内の禁止 directive は `hole-escape`、HEAD と不整合な anchor は `malformed` を期待する (4 subtype は
`orchestrator/campaign/diff_quarantine.py` に実在)。benign B は受理する (`quarantine_accepts_benign_hole`)。共有 parser の網羅テストを複製するのではなく、
当該 template への接続を検査する。

**JSON の生成元 (DW-O13、レンズ B 所見 3):** 既存 driver (`s3_mocc_lock_coverage.py` 343〜435) は argv・終了状態を run record に保存せず異常時は
例外にする。新 producer は run ごとの実 `argv`・`verdict`・`certified`・`total_cycles`・X/P 総数と reason・txn / write 数・終了状態を記録する。
旧 JSON に無い field を旧証拠へ要求しない (旧 14 check は歴史的結果として保持)。`condition_gates` は実 producer が出す `supply` / `meaning` /
`admission` の構造を参照する (要約版の `supply=null` を失敗と読まない)。`schema_version`、`ccbench_commit` (e9e477ca)、`template` (wave 2)、
`patches` (sha256)、`workloads` (W / U)、`trace0`、`legacy_proof` (旧 JSON の path / sha256 と 14 check の参照)、`checks`、`all_pass` を持つ。
`n1_a_rejected` / `n1_b_passed` は `checks` / `all_pass` に**入れない** (D38 決定 4 の点 5 / 6 は機械 4 点と別記録)。

## 8. 同一性の比較対象と patch 積層順 (レンズ B 所見 2)

「同じ template 状態」というだけでは検査の意味が定まらない。次の 4 比較は別の検査であり、合格として主張する内容が違う。

| 比較 | 合格として主張するもの | 正本 |
|---|---|---|
| 無 template ↔ template OFF (計装なし) | 実 resolver による `src_token="stock"` (stock genome が cache-hit) | `source_digest.py` (D23 / D48 決定 2 型) |
| template OFF ↔ ON の B (計装なし) | ON が別 identity になること、実 TU への flag 供給 | 同上 |
| 同一 template 状態の計装なし ↔ あり | TRACE=0 の前処理「(論理行番号, 非空本文) 列」の一致 (`#line` ±1 を検出) | D1687 |
| 旧 pin ↔ pin 候補 | TRACE=0 正規化前処理 + include 活性の同一性 | D297 (別 T = [T-2756] の材料 (2)) |

- 計装 patch `instr-mocc-lock-coverage.patch` の `#line` 7 箇所 (17 / 990 / 991 / 1158 / 1169 / 1187 / 1195) は **e9e477ca 無 template の論理行**を復元する。
  template (CC-native 骨格) は helper と 4 分岐を前方に挿入するので、template 適用後に同じ計装 patch を重ねると復元番号が合わない。
  **計装 patch の `#line` は template 適用後の論理行に合わせて再生成する** (template 依存部分)。旧計装 patch は旧 JSON の sha 束縛のため bytes を
  変えず保持する (wave 1 = template なしでは旧計装 patch をそのまま使う)。
- D1687 の `#line` 例外は `#if TRACE` 計装向けである。CC-native 骨格 (template) の識別は前処理本文一致 (上表 1〜2 行目) で行い、D1687 を骨格の
  承認根拠にしない。
- binary 比較を補助 witness として残すなら、source / build の path 長を揃える条件 (T-2294 の等長 dir) を引き継ぐ。

## 9. auditor 入力と n=1 定性

### 9.1 auditor.md の mocc 節 (実装 wave 2)

既存型番号の**mocc 向け説明として追加**する (新番号 22 以降を文章だけ足すと `auditor_gate.py` の型番号 1〜21 の schema が構造化出力を拒否する。
連番を足す場合は schema 更新も実装対象)。

| 現行箇所 | mocc での追記 |
|---|---|
| 型 8 | 「write-set の lock 欠落」の真実源を Silo の lock/shadow から、mocc の CLL 三条件 (`key_ == rcdptr_ ∧ mode_ ∧ lock_ == &rcdptr_->rwlock_`) + RWLOCK counter (`W_LOCKED`) に置換。早期 hot lock が後段 lockskip を隠す場合も説明 |
| 型 9 | `check.lock` ではなく 1010〜1013 と 1024〜1036。比較条件・read-set 全走査・abort を固定し、absent の検査まで存在すると誤記しない (§3.2 (b)) |
| 型 13 | `silo-writeset-sort` から mocc marker へ。4 callsite、CLL/RLL、validation、X/P 計装、write_set_ 登録 (477) は hole 外 |
| 型 16 | abort enum/store/sentinel ではなく、温度・閾値の値渡しと 4 callsite の対応、970 の fallback を監査 |
| チェックリスト 11 | mocc marker の hole と実 diff の行単位照合 |
| チェックリスト 12 | thread / key / storage による優先・fitness 適応を監査。sort IR の SWO 免除 (型 14) を mocc へ移さない |
| チェックリスト 13 | mocc の読取契約、helper 署名、呼出側引数、温度記録・CLL/RLL 骨格の無改変 |

mocc 節の 5 分類: (1) 読取契約違反 (型 16、内容に応じ 3/12/15)、(2) CLL/RLL 骨格改変 (型 8/10/13。P はこれらの保存検査ではない)、
(3) TRACE 3 検査点への侵食 (型 11/13: 入口 / UPDATE・DELETE payload 前 / publish 前)、(4) validation の骨抜き (型 9/13)、
(5) hot/cold の偽装 (型 3/4/16: 引数すり替え、4 site の一部だけ旧比較を残す、負例だけ別判定)。

auditor へ渡すもの: template、候補 working diff、実 digest、不可触箇所、性能値を除いた構造化 verify 結果。fitness / WAL、勝ち筋、期待 verdict は
渡さない。通常の Codex 子を role 名だけで起動して Claude の Read/Grep/Glob 契約と同等の隔離と扱わない。

### 9.2 n=1 定性 (D38 決定 4 の点 5 / 6) — 3 候補 (レンズ A 所見 5)

| 候補 | 内容 | 期待 | 何の実証か |
|---|---|---|---|
| A1' | 既存 `broken-mocc-lockskip-validation.patch` 相当の diff (validation phase 1 の `lock()` を飛ばす、marker 外) | reject | **D38 点 5 相当** (正しさ違反型の独立検出)。DQ が先に `outside-region` で拒否するが、それは DQ の positive control であり auditor の実証には算入しない。auditor には DQ を通さず直接見せる |
| A2' | hole 内の述語を `(FLAGS_clocks_per_us == 2100) && (temp >= threshold)` に変える | reject | 読取契約違反 (型 3/16) の弁別。直列性違反ではないと明記 |
| B' | hole 内の述語を `!(temp < threshold)` に変える | pass (Nit 可) | 点 6 (rubber-stamp 防止)。同じ型・同じ引数の論理等価 |

Silo の n=1 と同様に fresh・read-only・親の推論非共有・告白コメントなし・性能値なしで独立判定させる。保存するのは候補 diff、digest、入力射影、
実応答、実行権限の記録、限界。期待値を実応答として代入しない。親 brief の P4 (`thid_` / `result_` 読取) は file-scope helper では未宣言識別子の
指摘になるため採らない。hole 内の式から可視 global / 関数を介して副作用を起こす契約違反は marker 外差分を要さない — DQ が保証するのは物理行の
封じ込めであり、許可された純粋比較の集合と投入できる C++ テキストを混同しない。

## 10. mutation 面の gate — 鍵と執行範囲

Silo の gate は EBS 所属を前件にするが、mocc はその前件が常時 true (§1)。mocc 版の gate は次の形にする (実装は wave 2)。

- **発火条件:** `patches/*.patch` が `cc/mocc/transaction.cc` に EVOLVE-BLOCK marker を導入する、または軸定数 module が `SOURCE_REL` に加え
  `MARKER_ID` / `TEMPLATE_PATCH` を持つ mocc 軸として登録される。`SOURCE_REL == "cc/mocc/transaction.cc"` だけで全 module を探索しない
  (既存 proof driver が同じ定数を持つ)。現時点で前件は成立しない (mocc 対象の patch は計装 1 本・負例 3 本で marker なし。template・軸 module は不存在)。
- **機械要件:** (1) mocc 節を持つ auditor 定義と read-only・入力射影の構造、(2) e9e477ca・実 template・計装・負例の sha に束縛された proof JSON、
  (3) 旧 14 check と新設 hot/cold・hot 専用負例・quarantine control の必要 key が揃い各値が実観測由来、(4) 欠落 JSON・hot 証拠欠落・key 欠落・
  hash 不一致を拒否する parameterized control。既存 trace-hook だけなら発火せず、template のみ / 軸 module のみでも発火する。
- **consumer 束縛 (レンズ A 所見 4 / B 所見 4):** 新しい mocc mutation consumer (loop driver) が**実際に使う** source / template / PIN と proof JSON の
  束縛を、consumer 導入時テストで必須検査する。対照 3 種 — 別名・別配置の template、軸 module を使わず driver が定数を直接持つ形、marker 導入済み
  checkout を driver 直書き PIN で取る形 — が「拒否」または「同じ proof 要求へ到達」することを確認する。既存の NON_ADMISSIBLE 診断経路
  (T-2294 driver の literal PIN / SOURCE_REL) は正当であり禁止対象ではない。
- **閉じないこと (正直に):** 任意の直書き経路を機械的に閉じたとは主張しない。汎用の新台帳・全経路解析は作らない (DW-G05、本 T の scope 外)。
  `patches/ledger.json` は ability probe 専用 (entry 1 固定) で、鍵や登録先に流用しない。
- 候補ごとの経路では DQ を先行させ、`auditor_gate.apply_mandatory_deny_only_veto` を使う。auditor pass は機械 reject を覆せず、digest 一致は
  帰属証拠に限る。auditor pass を C++ の意味上の安全性証明に格上げしない。
- n=1 記録 (§9.2) は wave 2 の成果物として必須だが、機械 4 点の充足へ合算しない。file の存在確認から監査の有効性を認定しない。

## 11. I・P・pin の境界

- **I 行 (write-intent) は本 gate に含めない。** 根拠は Silo との対称性ではなく、**許可された述語の作用範囲と固定骨格**にある: 値渡しの純粋述語は
  write_set_ を直接変更できず、update の write_set_ 登録 (477) と construct_RLL の write_set_ 全要素登録 (905〜913) は骨格として固定し、その侵食は
  DQ の対照に含める (レンズ A 所見 6)。I absent (`test_mocc_proof_surface.py` 410〜426 が期待) は維持し、write-intent 未実証を明記する。
  D1603 の pin 手続きを省略する根拠にはしない。
- **P** は sort 前後の size と `rcdptr_` multiset の保存だけを見る (D1686)。温度 hole が write-set を触らないことは編集契約と DQ 側の根拠であり、
  P が任意の write-intent 改変を検出する根拠ではない。
- **pin:** 本 proof は e9e477ca の隔離 checkout に診断 patch を適用し、materializer 登録簿で NON_ADMISSIBLE な build として実施する。superproject の
  gitlink と現行 pin は動かさない。**proof 完了は mutation 探索の認可ではない。** certified な合成・評価には、D579 の独立実証に加え、[T-2756] を含む
  D1603 / D297 / D2114 の pin 手続きと、実際の producer が必要な proof surface を持つことが別途要る。e9e477ca 単体は X/P absent (計装は out-of-tree
  patch)。**pin 候補へ X/P 計装をどう載せるか (izanagi-trace 側へ移すか、T-2295) は別途解決が必要で、既存 gate の例外追加で済ませない。**
  proof 用 OID (e9e477ca + patch sha) と探索用の承認済み OID は別契約として記す。

## 12. 実装成果物・登録箇所・費用 — 2 wave 分割

**wave 1 (経路共通の実証、template 不要、今すぐ投げられる):**

| 作る物 | 内容 |
|---|---|
| `patches/broken-mocc-hot-update-unlock.patch` | §6 (459 の hot block、`rwlock_.w_lock()` 直接再取得、abort 回復、exactly-one directive) |
| `orchestrator/campaign/s3_mocc_mutation_proof.py` | 36 走 (§7) と新 check、run record の記録処理。旧 driver は変更しない。既存 helper の接続候補 = 旧 driver 274〜340 / 343〜435 / 493〜591 |
| `orchestrator/tests/test_mocc_mutation_proof.py` | balanced 負例の静的検査 (`test_mocc_hot_unlock_is_balanced_on_commit_and_abort`、`..._has_unique_condition_witness`)、matrix・JSON・入力由来 check (`test_mocc_mutation_checks_are_input_derived`、`test_mocc_mutation_proof_json_is_complete_and_bound`) |
| `output/env/pegasus/calibration/s3_mocc_mutation_proof.json` | 新 proof (旧 `s3_mocc_lock_coverage.json` を上書きしない) |
| `patches/README.md` | 新負例と限定事項 (既存 mocc 節に隣接) |
| 登録簿 | `materializer_admission.py` (新 build launcher は NON_ADMISSIBLE、`test_s8b_floor_campaign.py::test_materializer_registry_covers_all_python_build_launches` の閉包)、`condition_meaning_gate.py` (新裸 define の DefineSpec・owner・値 0/1・一意 witness・driver ID)、`screening_driver.py` (裸 define の既存登録方式)、spawn_sites 側の裸 define 登録簿 (正確な path は実装開始時に既存 mocc 3 define の登録先を辿る) |

完了判定: 新 producer の実測証拠 (compute) と入力由来 check が all_pass、旧 14 check・旧 patch sha の保持、hot 専用負例の完走 (timeout なし)、
stock-U 対照 6 走の certified。**正式な template 導入は含めない。**

**wave 2 (template 接続の実証、前提 = wave 1 完了 + 軸の A/B):**

| 作る物 | 内容 |
|---|---|
| `patches/mocc-temperature-predicate-variant.patch` | §5 (1 helper・4 callsite・OFF 原文保存・Options.cmake universal) |
| `orchestrator/campaign/axis_mocc_temperature.py` | marker / source / template / flag / frozen bytes / 読取契約 |
| 計装 patch の template 版 | `#line` を template 適用後の論理行へ再生成 (§8)。旧計装 patch は不変 |
| `.claude/agents/auditor.md` | §9.1 |
| wave 1 の driver / test / JSON の拡張 | `template_*` / `quarantine_*` / `auditor_digest_*` / `consumer_binding_controls` (§7 の末尾行、§10) |
| `output/insights/.../auditor-n1.md` + 候補・応答 | §9.2 (機械 JSON とは別の定性素材) |
| gate test (候補 `test_mocc_mutation_surface_requires_auditor_live`) | §10 |

完了判定: 当該 template に束縛された機械証拠 (§8 の先頭 3 比較、DQ 対照、consumer 束縛対照、hot/cold 全 check) と、別記の n=1 素材 3 候補が揃うこと。
§8 の旧 pin↔pin 候補の比較は D297 に従う別 T の成果物であり、本 wave の完了条件には含めない。
**pin 前進・certified 探索の開始は、この 2 wave の完了から自動的には導かない。**

**費用 (概算、レンズ B 所見 6):** codex 子は wave ごとに 7〜10 本 (plan 1、consult 2、author 1〜2、review 2、fix 1〜3)。compute は wave 1 で
build 5〜6 binary (計装 stock、負例 4 本、TRACE=0) + 36 trace/verifier 走 + condition gate、wave 2 で template ON/OFF の identity と再走を追加。
T-2294 の 6 走 Elapse 130 秒の単純 6 倍 (約 780 秒) は粗い参考値で、build 共有・trace 量 (4 thread の trace は大きい) で変わる。変異 matrix
(T-2294 は 1,711 秒) は別費用。fresh auditor n=1 は実行面を確認した別枠 1 呼び。

新 driver 側で特殊化する箇所: `_require_condition_gate()` は driver ID を固定し、`_apply_owned_patch()` は transaction 単独 touch を要求するので、
Options.cmake も触る template (wave 2) は新 driver で 2 file touch を許し、負例 patch は transaction 単独のまま。

## 13. 未確定事項 (実装時に最初に確定する) と scope 外

未確定:
- `loadepot.temp` / `FLAGS_temp_threshold` の具体型 (tuple.hh / common.hh)。
- U workload で `update()` 直前に read_set_ が空であること (ycsb.hh:128〜133 の静的読解では空、実走で確認)。
- 既定閾値 10 + blind update で温度が上がらない前提 (default/U 沈黙の前提)。
- 4 thread の hot 強制で hot-update 負例が hang しないこと (canonical mode の待ちと pending の相互作用)。
- spawn_sites 側の裸 define 登録簿の正確な path。
- §3.2 (a) の実走可否 (別 T)。

scope 外 (本 T が足さないもの): read 側 hot 経路の独立 witness、RLL 再試行の witness、DELETE 経路の動的被覆、汎用 driver 登録台帳、全経路解析、
auditor 型番号の連番拡張、verifier の編集、TPC-C / BOMB での E 行 counter 一致、temperature-reset / KEY_SORT との相互作用。

## 14. 段 2 / 段 3 の所見と裁定

- 段 2 plan (codex read-only、`gpt-6-astra`、reasoning xhigh — DW-S02 の現行値は medium、親の argv 誤り、実害なし): 温度述語の条件付き採用、F-b の
  read/update 限定、absent 非対称の静的反例、P2 の鍵修正、n=1 の分離、hot 負例の balanced 設計、36 走、純増あり。
- 段 3 レンズ A (正しさ境界・恒真性、lane luna、medium): must-fix 4 (版/counter 観測間隙、hot 負例の保証範囲、gate の登録外経路、n=1 と点 5 の区別)、
  should 3、nit 1。修正して採用。
- 段 3 レンズ B (実効性・整合、lane luna、medium): must-fix 4 (軸 A/B/C との境界、同一性 4 比較と `#line`、36 走と check の対応、gate の執行範囲)、
  should 4。修正して採用、2 wave 分割を推奨。
- 段 4 裁定 (`verbatim/s4-ruling.md`): 全所見 real・採用 (refuted 0)。親 brief の誤り 5 件 (F-b の一般化、「同じ鍵では恒真」の言い方、「pin 非依存」、
  「全 cold」、P4 の負例) を訂正。
- 段 6 レビュー (docs 差分への敵対レビュー 1 本、`verbatim/s6-review.md`): NO-GO → must-fix 3 / nit 2 を親が逐語で適用し、追加 commit で閉じた。36 走と check の対応 (必須 25 / 観測のみ 11) と行番号・識別子の実在は一致、fragment 文法は適合、旧指示の採用なし、と確認。

| 所見 | 対象 | 対応 |
|---|---|---|
| M1 hot 未観測を「温度述語 false の記録のみ」に強めている | worklog / decisions fragment | closed — 「hot/cold を弁別する記録がなく hot 到達は未実証」「1 thread は code からの推論、4 thread は未確認」へ |
| M2 README 単独で DQ 拒否対照を復元できない | §7 | closed — 4 subtype (`frame-altered` / `outside-region` / `hole-escape` / `malformed`) と対象変更の対応を §7 に復元 |
| M3 wave 2 の完了条件が別 T の D297 pin 間比較を取り込む | §12、decisions 項 3 | closed — 「§8 の先頭 3 比較」「template に関する同一性 3 比較 (旧 pin↔候補は別 T)」へ |
| N1 1 thread の走数 | §3.1 | closed — 3 走 → 4 走 |
| N2 codex 子の本数の算術 | §12 | closed — 7〜9 → 7〜10 |

- 親が現物で検算した plan / consult の主張: cold 読み 322 / 347 / 350 の順序と validation 1010 / 1024 の別読み、hot 読みの absent 非検査 (341〜344 対
  356〜364)、Options.cmake universal の mocc TU 供給 (ProtocolHelpers.cmake:19〜29)、U workload の操作生成 (ycsb.hh:65〜73, 128〜133)、
  `patches/ledger.json` の entry 数 1、`p3_s4_loop.py` の PIN literal、EBS の 3 要素目 (いずれも一致)。

## 15. 「チェックリストの再掲に留まるか」の判定

**留まらない。** D579 / D38 / D1686 の再掲を超える純増: hot 経路の実行証拠の欠落 (F-a)、RLL による「全 cold」の不成立、stock mocc の観測間隙 (§3.2 (a))
と absent 非対称 (§3.2 (b)) という正しさ論拠の限定、balanced 負例の workload 制約 (U)、file-scope helper と n=1 入力の整合、mutation 登録を鍵にした
gate と consumer 束縛、同一性 4 比較と `#line` 再生成、pin と X/P producer の未接続、2 wave 分割。よって「実証 wave の plan 段へ統合」ではなく
本 insight を設計の正本とし、wave 1 / wave 2 を worklog の新規 T として起票する。

## 16. verbatim 一覧

`verbatim/parent-brief.md`、`verbatim/s2-plan.md`、`verbatim/s3-lensA.md`、`verbatim/s3-lensB.md`、`verbatim/s4-ruling.md`、
`verbatim/prompt-plan.md`、`verbatim/prompt-consult-A.md`、`verbatim/prompt-consult-B.md`、`verbatim/prompt-review.md`、`verbatim/s6-review.md`。行末空白のみ可逆に正規化 (内容は無変更)、
原文 sha256 と保存後 sha256 は `verbatim/MANIFEST.json`。
