# [T-1871] 非列挙のコード片軸 — 軸オンボーディング段階 B の実施記録と裁定パッケージ

**位置づけ:** `docs/axis-onboarding.md` の**段階 B (設計敵対レビュー、D41 型)** を 1 軸ぶん実施した記録。
対象は D48 決定 2 末尾が「段階 B 差し戻し (シート改訂 + 再レビュー) 事項」として予約した
**構文契約のメンバ読取拡張**の消化である。段階 C 以降は実施していない。実装面の差分は 0 byte であり、
変異 matrix は `DW-S04` により対象外、受入全走は実施する。dev-wave 段 4 の親裁定は
**「実体化しない — 裁定パッケージを返す」**である。

**結論: 非列挙のコード片軸は実体化できなかった。段階 B の条件付き採用を D 番号で凍結しない。**
軸そのものを続けるか、条件の定義を改めるかは**ユーザー裁定** (§6)。

一次資料 (逐語) = `2026-09-01_t1871-review-verbatim/` (段 2 プラン 1 本 + 段 3 敵対相談 2 本 +
段 6 敵対レビュー 3 本)。

---

## 1. 何を試し、何が起きたか

1. **v2 初版 (段 2 草案):** hole 到達時点で生存する既存メンバのうち、生の
   `max_rset_.obj_` / `max_wset_.obj_` の 2 観測だけを許可する契約。
   → **段 3 レンズ A が reject。** `Tidword` の上位 32 bit がそのまま epoch であり、
   生の word を許すと D48 が禁じた進捗 proxy を丸ごと復活させる。`.epoch` を名前で禁じながら
   `.obj_` を許すのは綴りだけの恒真化である。**親はこれを real として採り、案を撤回した。**
2. **v2 第 2 版 (段 4 の親裁定):** 生の word を撤回し、派生 boolean 2 つ
   (`max_rset_.obj_ == 0` / `max_wset_.obj_ == 0`) と、骨格が新設する連続 abort 数
   (`abort()` で増やし `writePhase()` で 0 に戻す thread_local) を許可観測とする契約。
   → **段 6 の 3 レンズが全員 reject。** 理由は §3・§4。
3. よって本 wave は**軸を実体化せず**、実施記録と裁定パッケージを残す。

---

## 2. 段 1 の実測 (親、実コード裏取り。レビューの訂正を反映済み)

| # | 事実 | 一次資料 |
|---|---|---|
| M1 | hole = EVOLVE-BLOCK 内の代入 1 行 `izanagi_gate_pass = ...;`。述語変数の宣言・`if`・`Backoff::backoff()` 呼出し・stock 枝は marker 外 = coder 不可触 | `patches/silo-backoff-trigger-gating-variant.patch` |
| M2 | hole 到達**前**に `read_set_.clear(); write_set_.clear(); node_map_.clear();` が走る。**ただし `clear()` が保証するのは論理要素数 0 だけ**で、capacity・bucket 数・格納アドレスは履歴と個体識別を残す。禁止の結論は変わらないが、親 brief 初版の「全観測が恒真 0」は誤りだった | `cc/silo/transaction.cc:38-40` |
| M3 | hole 時点の生存メンバは親 brief 初版の列挙 (`pro_set_` / `max_rset_` / `max_wset_` / `mrctid_` / `backoff_` / `epoch_timer_*` / `status_`) では**非網羅**。`gc_records_` / `log_set_` / `latest_log_header_` / `quit_` / `callback_` / `logfile_` / `reconnoitering_` / `is_ronly_` / `is_batch_` も残る | `cc/silo/include/transaction.hh:35-62` |
| M4 | **単一所有 (data race 不在) は段階 B で閉じた。** worker 本体が実行器を worker スレッド自身のスタック上に構築する (`Tx trans = make_tx(thid, quit, backoff);`)。silo の生成関数は `TxExecutor(thid, &CCBenchResults[thid], quit)` を返す。段 3・段 6 の独立レンズが同じ所在で追認した | `common/runner.hh:172,183`、`cc/silo/ycsb_silo.cc:38` |
| M5 | `validationPhase()` は `lockWriteSet()` を**先に**呼び、その後で読み集合検証に入る。`max_rset_` の更新は各読み要素の検証成功**後**、`max_wset_` の更新は各 non-INSERT 要素の施錠成功**後** | `cc/silo/transaction.cc:383,437,450-474,155-191` |
| M6 | `abort()` / `begin()` / `writePhase()` は同一の既開通編集面にある。骨格が commit と abort をまたぐ状態を、信頼境界を触らずに保持することは**技術的には可能**である (採否は別問題。§4) | `cc/silo/transaction.cc:27,55,557` |
| M7 | `Tidword` は `uint64_t obj_` と bitfield (`lock:1 / latest:1 / absent:1 / tid:29 / epoch:32`) の無名 union。「上位 32 bit がそのまま epoch」は pinned な GCC / x86-64 の bitfield 配置に依存する記述だが、commit TID の数値比較自体が epoch 優先の配置を前提にしているため、生の word が進捗 proxy になるという判断は変わらない | `cc/silo/include/tuple.hh:12-31`、`cc/silo/transaction.cc:563` |
| M8 | 偵察地形は 3 workload とも floor 超が cross-run 再現済み (軸は生。二値としてのみ引用する) | `output/insights/2026-07-11_s8a-trigger-gating-recon.md` |
| M9 | 既存シート path の参照は **8 ファイル**。bytes hash pin は無い。親 brief 初版の「4 参照」は過少計上で、段 3 レンズ B が訂正し親が `git grep -l` で再検算した | `git grep -l "2026-07-10_s8a-stage-b-sheet"` |
| M10 | 対象 3 workload (balanced / write-heavy / read-heavy) は `READ` / `WRITE` / `READ_MODIFY_WRITE` しか実行せず、insert・scan の要因は発火しない。D50 は実効要因を `{lock-conflict, readvali-tid, readvali-locked}` の 3 つと確定している | `include/ycsb.hh:55,117`、D50 |

### 生死確認 (`DW-G01`)

新規実測は起こしていない。M8 の既測が軸の生を支える。ただし「拡張空間は上位集合だから地形も生存する」
という一般化は**使えない** — 骨格に更新点が増えれば preprocess 後の bytes も性能地形も同一ではないため、
v1 の既測点は v2 骨格の下では再実測対象になる (段 6 レンズ 1)。

---

## 3. 敵対レビューの裁定台帳 (5 レンズ、全員が独立コンテキスト)

| レンズ | 段 | 対象 | verdict |
|---|---|---|---|
| A 正しさ・reward hack・UB | 3 | v2 初版 (生の word) | **reject** |
| B 実効性・非列挙性・既裁定整合 | 3 | v2 初版 | adopt-with-conditions |
| 1 正しさ・reward hack・UB | 6 | v2 第 2 版 (counter) | **reject** |
| 2 非列挙性・軸適格性 | 6 | v2 第 2 版 | **reject** |
| 3 リーク制御・既裁定整合・scope 規律 | 6 | v2 第 2 版 | **reject** |

`docs/axis-onboarding.md` §3-B の出口 gate は「3 レンズ全員 adopt (条件付き可)」である。
**満たしていない。** さらに段 6 レンズ 3 が指摘したとおり、段 3 の 2 レンズが検査したのは
撤回済みの初版であり、**第 2 版を検査したレンズは 1 本だけ**である。
3 レンズ要件は本数の面でも未充足であり、これは親が段 4 で中心設計を差し替えたことの帰結である。

### 採用した所見 (real)

| # | 所見 | 出所 |
|---|---|---|
| R1 | 生の `.obj_` は禁止した proxy を内包する。上位 32 bit の epoch により、比較 1 個で実行進捗による政策切替ができる | 段 3 A |
| R2 | 単一所有は C でなく B の決定事項である (観測の採否が変わるため)。→ 親が M4 で閉じた | 段 3 A |
| R3 | admission 契約が機械判定可能な形まで閉じていない。「unsigned の全域演算」は演算子の閉集合でなく、`kUnset` の保証は任意の再帰式に対する意味検査を要する | 段 3 A |
| R4 | positive control が負例だけだと、**全件拒否する gate でも全負例が赤になり合格してしまう**。非自明な正例が要る。さらに正例が少数だと「大半を拒否する gate」も通る | 段 3 A / 段 6-1 |
| R5 | 「正しさを原理的に壊せない」は「serializability safety を直接変更しない」へ限定すべき。starvation の schedule は構成できる | 段 3 A / 段 6-1 |
| R6 | 検疫の end-to-end 配線は射影外で未確認。保証は module-level に留まる | 段 3 A |
| R7 | 非列挙性の主張を二層化せよ。構文集合が無限なのは自明で、それだけでは適格性を示せない | 段 3 B |
| R8 | `DW-O13` の値域実測が要る。fail 条件は B-5 の固定予算へ結び付けよ | 段 3 B / 段 6-2 |
| R9 | D1012 の三すくみは**未解消**。解消したのは D1067 が必要性主張を捨てたことである | 段 3 B / 段 6-2 / 段 6-3 |
| R10 | (c') は旧 5-bit 部分空間へ限定し、拡張契約についての事前登録改訂は発火時のユーザー承認へ送れ。シート単独で既裁定の射程を変えてはならない | 段 3 B / 段 6-3 |
| R11 | 同一 marker のまま契約を版で分けるなら、`contract_version` を Markdown だけでなく proposal schema・campaign identity・provenance・resume gate・template contract に束縛し、不一致で停止させよ | 段 3 B / 段 6-3 |
| R12 | coder へ渡すのは contract-only projection だけにせよ。ただし D45 は「Read 遮断後もメインセッションの手動射影と自然文の justification が既知限界」と明記しており、「必須条件が塞ぐ」は実装より強い保証である | 段 3 B / 段 6-3 |
| R13 | 既存シート参照は 4 でなく 8 | 段 3 B |
| **R14** | **`unsigned` は有限幅なので、連続 abort 数を足しても意味空間は無限にならない。** 幅 w・その他到達状態 R なら入力点は最大 R×2^w で、述語集合も有限。無限に残るのは冗長な構文表現だけで、R7 の論拠へ逆戻りする | 段 6-1 / 段 6-2 |
| **R15** | **連続 abort 数は絞り込んだだけの fitness 信号である。** `local_abort_counts_` は同じ abort で増え、`local_commit_counts_` は同じ commit で増える。commit の起きない starvation ではワーカーの累積 abort 数と一致する。D48 の proxy 禁止を満たさない | 段 6-1 |
| R16 | 汎用 runner は任意の `Workload::run()` を呼ぶだけで、commit せず別の論理トランザクションへ進まないことは一般には証明されない。`reconnoiter_end()` にも commit を伴わない `begin()` がある。「ワーカーの commit 間 abort 連続数」と「現在の論理トランザクションの再試行深さ」は別物である | 段 6-1 |
| R17 | 親の到達点「16」は範囲が混在している。対象 YCSB 3 workload では上限 **10**、全要因を数えるなら **18** | 段 6-2 |
| R18 | `b_w` は「施錠成功ゼロ」と同義でない。`update-absent` は CAS 成功後・`max_wset_` 更新前に return する。正確な意味は「それ以前に `max_wset_` へ取り込まれた non-INSERT 要素がない」 | 段 6-1 / 段 6-2 |
| **R19** | **新設 counter は D48 と親 brief が対象にした「既存メンバ読取の拡張」を越えており、骨格状態の新設である。** 同一軸の契約改版か新しい複合軸かを段階 A の人間 gate で裁定し直す必要がある | 段 6-3 |
| **R20** | **3 レンズ要件が本数の面で未充足。** 段 3 の 2 本は撤回済み案を見ている | 段 6-3 |
| R21 | `kUnset` の fail-safe を marker 外の frame で上書きするなら、hole 内の `reason != kUnset` は無害であり、負例として拒否する理由がない。現在の負例は単一理由性を持たない | 段 6-1 |
| R22 | 骨格に更新点が増える以上、v1 候補の「bytes 保存」は TU 全体の逐語同一ではありえない。条件は「hole 右辺の lowering 保存」へ限定し、v1 の全点は v2 骨格の下で再実測対象とせよ | 段 6-1 / 段 6-2 |
| R23 | 必須条件のうち auditor ギャラリー追加と fairness/liveness 台帳は、`DW-G05` の一行影響を書けず、ユーザーが scope 外とした「仮想リスク向けの検査・台帳追加」に当たる。must-fix から外し、既知リスクの記述に留めよ | 段 6-3 |

### 却下した安全論拠 (同じ誤りを次の軸で繰り返さない)

- (a) 「生の 64bit word を許しても、bitfield 名 (`.epoch` / `.tid`) を禁止すれば進捗 proxy は塞がる」
  — 塞がらない。word の上位 32 bit が epoch であり、比較 1 個で復元できる (R1)。
- (b) 「`clear()` 済みコンテナは全観測が恒真 0 なので情報を持たない」— `size()` / `empty()` は恒真だが
  capacity・bucket・アドレスは残る。**禁止の結論は同じだが理由が違う** (M2)。
- (c) 「構文集合が無限だから非列挙」— 意味空間の広さを示していない (R7)。
- (d) 「単一所有は C 段で裏取りすればよい」— 観測の採否が変わるので B の決定事項 (R2)。
- (e) 「`unsigned` の連続 abort 数は自然数全体を与えるので意味空間が無限になる」(親の段 4 裁定)
  — **有限幅なので成立しない** (R14)。これは本 wave で親自身が犯した誤りである。
- (f) 「連続 abort 数は run の fitness 信号ではなく、失敗し続けているトランザクション自身の
  競合フィードバックである」(親の段 4 裁定) — **構造的に区別されていない** (R15)。

---

## 4. 中心的な発見 — 二重の壁

この hole で非列挙のコード片軸を作ろうとすると、性質の違う壁に 2 枚ぶつかる。

### 壁 1: 有限幅の壁 (定義の問題)

**C++ の観測はすべて有限幅である。** 入力空間が有限なら、そこから boolean を返す述語の集合も必ず有限になる。
`unsigned` の counter を足しても、幅を w とすれば入力点は最大 R×2^w で頭打ちになる (R14)。
**したがって「非列挙」を厳密な意味的無限として要求する限り、コード片軸は原理的にどれも不適格である。**
これはこの hole の欠陥ではなく、条件の書き方の問題である。

現行の復活条件 (`docs/phase3-main-experiment.md` 2026-07-12 追記) は
「非列挙のコード片軸が実体化し、偵察が floor 超地形を確認した場合にのみ検証可能」と書いており、
「非列挙」の意味を定義していない。**この語を厳密な意味的無限と読むなら、条件は到達不能である。**

### 壁 2: 代理の壁 (設計の問題)

述語空間を広げるには、hole から見える量を増やすしかない。しかし増やせる候補はいずれも
D48 が禁じた代理になる。

| 増やす候補 | 何の代理になるか | 出所 |
|---|---|---|
| 生の `Tidword` word | epoch = 大域の進捗時計、TID = record 世代 | R1 |
| `mrctid_` / `backoff_` / epoch timer / GC・WAL 残量 | run 自身の fitness 信号 | 段 2 草案 |
| アドレスの整数化 | ワーカー識別 (`thid_`) | 段 2 草案 |
| `pro_set_` / `is_ronly_` | トランザクション種別 = 公平性の犠牲 | 段 2 草案 |
| 連続 abort 数 (新設) | `local_abort_counts_` を絞り込んだ fitness 信号 | R15 |

安全側へ倒し切ると、残るのは派生 boolean 2 つだけで、到達点は対象 workload で 10、全要因でも 18 に留まる
(R17)。しかもそのうち `b_r` は lock 系要因で恒真であり、**述語が自分の候補集合に含意されて何も禁じない**
型になる。

**つまり、空間の広さと reward hack の遮断が、この hole では正面から衝突する。**
両立させる観測は、既存メンバの中には見つからなかった。骨格で新設する量にも、
いま思いつく限り同じ壁がある。

---

## 5. 軸定義シート (§2) — 埋まった欄と未定の欄

段階 B の入口として §2 を実コード裏取りで埋めた。**採用はしない**が、記入自体は次の設計の出発点になる。

| 欄 | 記入 |
|---|---|
| 軸名 | `silo-backoff-trigger-gating` (同一 hole の契約改版として扱う。新軸名は付けない) |
| 変異型 | コード片軸。出力は値でなく単一の boolean 述語代入 (`value` フィールドなし) |
| SOURCE_REL | `cc/silo/transaction.cc`。既に `EVOLVE_BLOCK_SOURCES` と file allowlist の中で、拡張は不要 |
| マーカー ID | `silo-backoff-trigger-gating` (据え置き) |
| hole の位置と骨格 | `TxExecutor::abort()` の `#if BACK_OFF` 内、3 コンテナ clear の後。coder 面は述語代入の右辺だけ (M1) |
| 構文契約 | **未定。** 安全側 (派生 boolean のみ) では空間が足りず (壁 1・壁 2)、広げると禁止代理が復活する。演算子・literal 幅・型・飽和方針まで含めて未確定 (R3, R5 相当) |
| stock の動作 | `BACK_OFF=1` なら要因・状態によらず 1 回 `Backoff::backoff(FLAGS_clocks_per_us)` を呼ぶ |
| フラグ名 | `CCBENCH_BACKOFF_TRIGGER_GATING` (TU macro `BACKOFF_TRIGGER_GATING`)。0=stock / 1=variant。`_BASE` は `BACK_OFF: 1` を明示 |
| 壊しうる不変条件 | **serializability safety を直接変更しない** (「原理的に壊せない」とは書かない)。触りうるのは starvation・abort storm・epoch 進行と GC のタイミング・適応 Backoff との帰属混同。契約違反を通した場合は UB・sentinel fallback 破壊・入力隔離の破れ |
| verifier の死角 | abort 経路の hole は trace event を出さない。trace は commit / writePhase と P/X 検査が中心で、述語の入力・gate 判定・部分的な starvation・UB による最適化を見ない。**pre-build admission は verifier とは別の必須の一次防壁である** |
| reward hack 仮説 | §4 の壁 2 の表がそのまま該当する。加えて恒真・恒偽への縮退、`kUnset` のときだけ条件を評価して stock fallback を破る型 |
| positive control 設計 | (1) admission negative control = 禁止面ごとの独立入力が build 前に構造化 reject され、各負例が**対象 gate 単独で**拒否されたことを subtype で照合。(2) nontrivial acceptance control = 各許可観測・各演算子・literal 境界・入れ子を覆う正例が production の公開経路で受理・materialize・build される (**reject-all だけでなく reject-most も閉じる**、R4)。(3) 既存の要因記録 misattribution positive control は単一スレッド characterization が効くので維持。fairness / liveness は characterization 不能な死角として規律 3 の見送り扱い |
| 偵察の列挙空間 | 列挙可能な部分空間 = 現行 v1 の 5-bit wire (32 点)。各部分集合を enum 等値比較と boolean 結合だけの正準述語へ写せば、有限列挙と構成的安全性を与えられる (段 6 レンズ 2 が具体化)。**全空間の代表性は主張しない** |
| 感度を持つ workload | balanced / write-heavy / read-heavy を据え置く。偵察の勝ち候補・数値・順位は転記しない |
| 計測動作点 | p2_2 確定動作点 (t48 / 1M / skew 0.9)。これは v1 部分空間の既測条件であって、拡張空間の floor を意味しない |

---

## 6. ユーザー裁定を求める事項

### 裁定 1 (中心) — 復活条件の「非列挙」をどう定義するか

`docs/phase3-main-experiment.md` 2026-07-12 追記の「非列挙のコード片軸」の意味を確定させたい。
壁 1 により、この語の読み方が軸の存否そのものを決める。

- **択 a — 「固定予算の下で操作的に列挙し尽くせない」へ定義し直す。**
  D1067 は既に主張を「固定予算・固定編集面の下で、事前登録した非 LLM 生成器より高い score」へ
  狭めている。この主張に意味的無限は要らず、必要なのは
  「事前登録した生成器の試行予算では到達 truth-vector を覆い尽くせない」ことだけである。
  代償 = 拘束力ある事前登録 (`docs/phase3-main-experiment.md`) の文言改訂を伴うため、
  D1012 の作法により日付付き・ユーザー承認付きの発火 commit が要る。
- **択 b — 厳密な意味的無限を維持する。** この場合、壁 1 によりコード片軸は原理的にどれも不適格であり、
  旧 headline 主張の復活条件は到達不能である。条件そのものを撤回するのが筋になる。
- **択 c — 判断を保留し、B-5 と後段 ([T-1872]) の休眠を継続する。** 現状維持。

**親の推奨は択 a。** 理由 = 壁 1 は個別の hole の欠陥ではなく条件の書き方の問題であり、
D1067 が主張範囲を狭めた時点で意味的無限は既に不要になっている。
択 b は誠実だが、復活条件を撤回すると旧 headline 主張の保存自体が無意味になる。

### 裁定 2 — 骨格が新しい状態を持つ案を、この軸で追うか

段 6 レンズ 3 は「骨格所有の連続 abort 数は D48 が予約した『既存メンバ読取の拡張』を越えており、
同一軸の契約改版か新しい複合軸かを段階 A の人間 gate で裁定し直す必要がある」と指摘した (R19)。
加えて R15 が「この量は絞り込んだ fitness 信号である」と示している。

- **択 a — 追わない。** 既存メンバ読取の範囲に留め、壁 2 を「この hole では両立しない」と結論する。
- **択 b — D48 の proxy 禁止に対する明示裁定を置いた上で追う。** 「いま失敗し続けている度合い」を
  gate の入力として許すかどうかは、規律 2 に触れる設計判断であり、AI の裁量で決めるべきでない。
  許すなら、どの範囲まで (連続数のみ / 閾値比較のみ / 上限付き) を同時に決める必要がある。
- **択 c — 段階 A へ戻し、axis-proposer に別 hole を提案させる。**

**親の推奨は択 b を検討した上で、まず択 a。** 理由 = R15 の指摘は構造的で、
「fitness 信号ではない」という区別を実装で保証する手立てが本 wave では見つからなかった。
規律 2 の面を持つ判断を、証拠の裏付けなしに親が採るべきでない。

### 裁定 3 — レンズ本数の数え方を規則にするか (裁定境界の変更)

本 wave では、親が段 4 で中心設計を差し替えた結果、**段 3 の 2 レンズが差替え後の版を見ていない**
状態が生じた (R20)。一般規則にするなら次の形になる。

> ドメイン正本がレンズ本数を指定する設計レビューでは、dev-wave 段 4 の裁定で中心設計を
> 差し替えた場合、差替え後の版を要求本数のレンズが検査するまで出口 gate を満たしたとしない。
> 段 3 のレンズ数を、差替え前の版に対するものとして本数へ算入しない。

これは**親の裁定権限を制約する規則**であり、裁定境界の変更に当たる。
`docs/skill-self-improvement.md` の dev-wave 終端は、この類型を実装せず裁定パッケージへ送ると定める。
よって本 wave では採用せず、採否をユーザーへ返す。行き先候補 =
`docs/dev-wave/workers.md` の `DW-S03` または `docs/dev-wave/core.md` の `DW-S04`。

### 裁定 4 — 段階 A の人間 gate をやり直すか

裁定 2 で択 b または択 c を採る場合、`docs/axis-onboarding.md` の段階 A 人間承認 gate を
改めて通す必要がある (R19)。この gate の判定材料には
「提案の hole 位置と骨格が既存軸台帳と構造的に異なるか」が含まれる (D47 必須条件 4)。

---

## 7. 段階 C へ送る条件 (次に B を通す設計が現れたときの前提)

段 6 レンズ 3 の rightsize に従い、`DW-G05` の一行影響を書けない条件は must-fix から外し、
§8 の既知リスクへ移した。見出しも「C 段着手前」ではなく
**「C 段で消化し、C 出口までに確認する」**へ改めた (実行順序が成立しないため)。

**B で凍結すべきもの (契約と権威):**

1. **段階 B の出口を満たす。** 設計に対し 3 レンズが全員 adopt または adopt-with-conditions を返し、
   契約が D 番号で凍結されていること。**撤回・差替えのあった設計は、差替え後の版を 3 本とも見る。**
2. **allowlist を観測単位で凍結する。** 許可集合が明示列挙・既定禁止であり、
   未列挙 identifier と `this` 経由の迂回が拒否されること。禁止 registry の全項目に個別の負例。
3. **`kUnset` の fail-safe を意味検査なしで機械執行する。** marker 外の frame が
   `kUnset` のとき無条件に `true` を上書きする形にすること。**このとき hole 内の
   `reason != kUnset` は無害になるので、負例から外す** (R21 の自己矛盾を解消する)。
4. **意味契約を閉じる。** 演算子の exact 集合、literal の幅と suffix と範囲、counter を使うなら
   その型・初期値・increment と gate 評価の前後関係・reset 位置・飽和か wrap か。
   C の実装裁量に残すと受理集合が実装者ごとに変わる (段 6 レンズ 3)。
5. **contract version を機械 identity に束縛する。** proposal schema・campaign identity・
   provenance・resume gate・template contract のすべてに版を持たせ、不一致で停止させること。
   Markdown の記述だけでは二義化を防げない (R11)。
6. **リーク経路の遮断設計を書く。** versioned な機械 schema から固定射影を生成し、
   自由記述の経路と親による文書転記をどう扱うかまで定めること。
   D45 の既知限界 (手動射影・自然文 justification) を「塞いだ」と書かない (R12)。

**C で消化し C 出口までに確認するもの:**

7. **型付き pre-build admission を実装する。** identifier・メンバ連鎖・演算子・literal 型・
   単一代入・AST 文法を build 前に機械検査し、欠落・未知構文・parse 不能で例外停止すること。
   構造検疫を意味保証に数えない。
8. **negative control と nontrivial acceptance control の両方を通す。** 正例は production の
   公開 materialization / build 経路を通し、各演算子・literal 境界・enum・入れ子を覆うこと。
   **reject-all だけでなく reject-most も閉じる** (R4)。負例は対象 gate 単独で拒否されたことを
   subtype で照合し、identity churn の共通集合を機構固有の kill と数えない。
9. **hole の単一代入性を実証する。** marker 内で変更可能なのが述語代入 1 個だけで、
   骨格側が frame として不変であること。
10. **stock inert と identity を実証する。** flag 0 が pinned stock と同一 `src_token="stock"`、
    flag 1 が別 digest、TRACE の diff-of-diffs が一致すること。
11. **骨格の中立性を確認する。** 既存の要因記録 7 点は回帰確認で足りる。新しい更新点を足す場合は、
    abort 分岐・commit 経路・共有 DB 更新の制御フローを変えないことを個別に確認する。
12. **v1 部分空間の保存を「hole 右辺の lowering 保存」として証明する。** 一対一性・重複なし・
    `kUnset` を含む truth-table 同値・保存対象 bytes の範囲を固定すること。
    **TU 全体の bytes 同一は骨格が変われば成立しないので要求しない。v1 の既測点は再実測対象** (R22)。
13. **`DW-O13` の値域実測を行う。** workload 別・独立 run 別に joint support・0 比率・distinct 数・
    頻度集中度・cross-run 再現性・打ち切られた retry の censoring を測る。
    **fail 条件は「実測値が少数か」ではなく、事前登録した非 LLM 生成器の試行予算に対して
    到達 truth-vector 数・頻度集中・候補間の truth-vector 重複率が十分に非網羅かへ結び付ける** (R8)。
    有限測定から無限 support は証明できないので、壁 1 の静的反例はこの実測では閉じない。
14. **D44 適格性は generator の凍結時に判定する。** 契約が要因別の独立閾値を表現できることと、
    実際の生成器が単一閾値へ縮退しないことは別である。後者は B-5 発火時の事前登録側で判定する。

---

## 8. 残存リスク・既知限界

- **本 wave は性能を一切測っていない。** 地形について何も主張しない。
- 5 レンズはいずれも静的検査のみで、pytest を走らせていない (`DW-O05`)。テスト緑は主張しない。
- 検疫の end-to-end 配線 (実 caller が必ず `validate()` を消費すること) は射影外で未確認である。
  保証は module-level に留まる (R6)。
- **auditor ギャラリーへの新型追加と、fairness / liveness の指標台帳の新設は、
  本 wave の must-fix から外した** (R23)。`DW-G05` の一行影響を書けず、ユーザーが scope 外とした
  仮想リスク向けの検査・台帳追加に当たるためである。リスク自体は消えていない —
  履歴依存の gate は v1 の要因のみ gate より細かい starvation を生みうる (段 6 レンズ 1 が
  具体的な schedule を示した)。将来この設計を追うなら、別途承認された scope で扱う。
- 逐語には具体的な述語構成のヒント (低位 bit・record 世代・トランザクション種別の近似・
  閾値の置き方) が含まれる。**coder / planner の入力へ射影してはならない。**
  現時点で coder へ届いた事実はなく、**v2 の拡張空間には実測された勝ち点が存在しない**
  (v1 の偵察には具体点の記録があるが、それは本 wave の対象外である)。
- 本 wave は `docs/phase3-main-experiment.md` を改訂していない。(c') の射程についての
  §3 R10 の整理は**提案**であって、既裁定の射程を変えたものではない。
- 親自身が段 4 で 2 つの誤りを犯した — 却下論拠 (e) の有限幅と (f) の fitness 代理。
  どちらも段 6 の独立レンズが捕まえた。**中心設計を段 4 で差し替えると、
  段 3 のレンズ 2 本が差替え後の版を見ていない状態になる** (R20)。これは手順上の教訓である。
