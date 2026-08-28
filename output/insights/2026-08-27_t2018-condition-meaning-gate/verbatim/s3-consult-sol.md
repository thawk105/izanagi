## 総括

**NO-GO。blocker は 7 件。**

段2 plan は、制御された fixture 上では F707 と F718 を別理由で落とせる構造を持つ。しかし現状の証明対象は「適用後 source の実 TU における意味」ではなく、**抽出 block を人工的な macro・有限 context で再コンパイルした観測**である。証明名と成果物主張が実態より強い。

調査は read-only の静的検査と整数式の再導出のみ。pytest、C++ compiler probe は実走しておらず、緑とは報告しない。

## Findings

### 1. [real][critical][scope 内][blocker] 抽出 block は実 TU の前処理・型文脈を保存しない

- file:line: [s2-plan.md:51-64](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s2-plan.md:51)、[silo-backoff-fixed.patch:45-73](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/patches/silo-backoff-fixed.patch:45)、[source_digest.py:199-225](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/source_digest.py:199)
- 反例:

```cpp
#ifdef __GNUC__
double now_backoff = 0;
#else
// EVOLVE-BLOCK-BEGIN ...
#if BACKOFF_FIXED >= 0
double now_backoff = BACKOFF_FIXED;
#else
double now_backoff = Backoff_.load(std::memory_order_acquire);
#endif
// EVOLVE-BLOCK-END ...
#endif
```

実 TU は `__GNUC__` 枝で 0 を使う。抽出器は外側の条件を捨て、marker 内だけを人工 TU で評価するため、1000 を観測して偽緑になる。`__GNUC__` は既知 builtin なので既存 conditional coverage もこの形自体を拒否しない。

同様に marker より前の `#define BACKOFF_FIXED 0`、include が供給する補助 macro、class member、overload、型 alias、TU 注入 macro が実 TU と人工 TU で異なりうる。

- 成果物影響: `compiler-evaluated-applied-source-declared-context-meaning` は過大主張。A1/A3 が「実行側と同じ意味」を保証しない。
- 最小修正: marker block 単体をコンパイルせず、捕捉した**全 header の一時 instrumented copy**を元の class/member/include 文脈でコンパイルする。marker 直前で `start` を宣言値へ上書きし、marker 直後で `now_backoff` を sink へ渡して return する。外側条件で marker が dead なら出力欠落として拒否する。

### 2. [real][high][scope 内][blocker] 非負 case だけなら通るが、stock branch を含む API にはなっていない

- file:line: [s2-plan.md:45-59](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s2-plan.md:45)、[silo-backoff-fixed.patch:69-73](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/patches/silo-backoff-fixed.patch:69)、[backoff_extended_sweep.py:282-288](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/backoff_extended_sweep.py:282)
- 反例: schema は負の `define_value` を禁じていない。`BACKOFF_FIXED=-1` は stock branch を選び、standalone TU では `Backoff_` と `std::memory_order_acquire` が未解決になって compile failure になる。正しい stock case が `compiler-failed` で偽赤になる。
- 成果物影響: 合成枝だけを評価して `BACKOFF_FIXED` 全体の meaning gate と数えると A1/A3 を過大主張する。
- 最小修正: Finding 1 の全 header instrumentation を採用する。代案は v1 schema を `BACKOFF_FIXED >= 0` に限定し、証明名へ `synthesized-branch` を含める。case ごとの macro 漏れを避けるため、case × context ごとに別 TU とする。

### 3. [real][critical][scope 内][blocker] supply membership は要求値が実 macro 値へ届いたことを示さない

- file:line: [source_digest.py:695-717](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/source_digest.py:695)、[source_digest.py:739-754](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/source_digest.py:739)、[model.py:61-63](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/model.py:61)
- 反例:

```cmake
BACKOFF_FIXED=${CCBENCH_BACKOFF_ALT}
```

`parse_supplied_macros()` は左辺 `BACKOFF_FIXED` を返すので membership は通る。driver が渡すのは `-DCCBENCH_BACKOFF_FIXED=1000` であり、実 TU は `CCBENCH_BACKOFF_ALT` の既定 0 を受け取る。一方、人工 TU は直接 `-DBACKOFF_FIXED=1000` を置くため意味検査も通る。

- 成果物影響: F707 の「値が届かなかった」変種を偽緑にする。既存 parser の公開 API は textual supply set であり、exact compiler input ではない。
- 最小修正: `source_digest` に、左辺、右辺 cache 名、bare/KV 区別を返す公開 API を追加する。case 値は CMake cache override として流し、mapping 後の実効 macro 集合を evaluator へ渡す。post-configure の exact 値を使わない限り、証明名は textual supply に限定する。driver 群への義務化は行わない。

### 4. [real][high][scope 内][blocker] 同一 source bytes は守るが、入力 tuple と build の snapshot は守らない

- file:line: [s2-plan.md:49-52](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s2-plan.md:49)、[source_digest.py:114-121](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/source_digest.py:114)、[s8b_compiler_input.py:101-133](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/s8b_compiler_input.py:101)
- 反例: source A を読み、続いて Options B と protocol CMake B を読む間に checkout が切り替わる。証拠は A+B の混成になる。その後 source が C へ変わっても、module 単独では build 前再照合されない。
- 成果物影響: `source_sha256` は evaluator 内の二度読みを防ぐだけで、「適用後 checkout」や後続 build との同一性を示さない。
- 最小修正: `openat`、`O_NOFOLLOW`、前後 `fstat` で3入力を安定読取し、source、Options、protocol CMake の全 hash と compiler realpath/version/argv を evidence に入れる。build 境界との一致を再照合しない本 wave では proof 名を `captured-source` とする。

### 5. [real][critical][scope 内][blocker] expected/observed set の意味論が未定義で、恒真と偽赤の両方がある

- file:line: [s2-plan.md:46-50](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s2-plan.md:46)、[s2-plan.md:58-64](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s2-plan.md:58)、[s2-plan.md:175-178](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s2-plan.md:175)
- 反例:
  - `expected_values=["5"]` と observed IEEE bits の変換規則が未定義。
  - context A/B の期待 `{x,y}` に対し、実装が A→y、B→x でも集合比較は通る。
  - `-0.0` と `+0.0` は Python 数値集合なら同一だが IEEE bits は異なる。
  - define 0 と1000が別 NaN payloadを返せば bits 集合は異なり、injective と誤認できる。
  - 同一 context の重複は集合で潰れる。
  - `start==1 || start==2` のときだけ期待値、それ以外は0という decoder は計画中の有限 witness を全通しする。実 `rdtscp()` regime との束縛はない。
  - nondeterministic decoder を一度ずつ走らせると、同じ意味の2点が偶然別出力になり injectivity が偽緑になる。
- 成果物影響: declared meaning と grid injectivity の両方が恒真化しうる。出力行数だけ合っていても case/context の重複・欠落を検出できない。
- 最小修正:
  - float64 の期待値も16桁 lowercase bitsに固定する。例: 0=`0000000000000000`、5=`4014000000000000`、999=`408f380000000000`、1000=`408f400000000000`。
  - NaN/Infinity は observed 側でも拒否する。signed zero は bits のまま区別する。
  - context を一意な ID で管理し、期待値は case × context の pointwise map とする。
  - 出力は `(case_index, context_index, token)` の完全な直積を要求する。
  - injectivity は unordered set ではなく context→bits のベクトルを比較する。
  - 同一 executable を複数回走らせて一致を要求し、それでも証明名は `finite-witness` とする。

### 6. [real][high][scope 内][blocker] fixture が凍結 patch bytes または実 applied source に束縛されていない

- file:line: [s2-plan.md:83-100](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s2-plan.md:83)、[silo-backoff-fixed.patch:60-74](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/patches/silo-backoff-fixed.patch:60)
- 反例: fixture の divisor と期待 JSON を同時に変更すれば、fixture 自身の decoder と checker は整合したまま緑になり、凍結 patch の現行 decoder は一度も検査されない。
- 成果物影響: F718 回帰が self-confirming fixture になる。F707 fixture も CMake function 全体を欠かすと `macro-not-supplied` ではなく `supply-set-unavailable` で死ぬ。
- 最小修正:
  - frozen patch の target-side `EVOLVE-BLOCK-BEGIN` から `END` を読み出し、正例と F707 fixture の block bytes と完全一致させる authority-anchor node を置く。
  - `f707-missing-supply` は正例 tree から `BACKOFF_FIXED=${CCBENCH_BACKOFF_FIXED}` の1行だけを除いた exact single mutation とする。他の供給行を残し、parser の非空条件を満たす。
  - F718 declared fixture は1000の1 caseだけにし、meaning mismatch を単一理由にする。0/1000の衝突は injectivity-only fixtureへ分離する。

### 7. [real][high][scope 内][blocker] 変異 anchor が過剰決定されている

- file:line: [s2-plan.md:154-168](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s2-plan.md:154)、[test_silo_ladder_rung1.py:80-110](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/tests/test_silo_ladder_rung1.py:80)
- 反例:
  - renderer の固定0変異は positive と F718 の複数 node を落とす。
  - declared comparison 削除は F718 を `grid-not-injective` で別理由 kill し、uniform-shift も落とす。
  - marker extractor 変異に対する comment node は、marker uniqueness ではなく後段の意味比較でも落ちる。
  - fixture divisor 変異は authority drift と F718 golden の両方を落とす。
  - `expected_values=["0"]` は schema 上は正当であり、closed-schema test は「decoder からの自動生成」を判別できない。
- 成果物影響: mutation score が、どの predicate に歯があるかを示さない。
- 最小修正: production predicate の変異だけを mutation spec に入れ、1変異1焦点 nodeへ分割する。fixture drift は mutation score でなく authority-anchor nodeで守る。

### 8. [real][medium][scope 内][non-blocker] 親実測の hash-bit 列と start witness が再現可能に記録されていない

- file:line: [parent-measurements.md:10-43](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/parent-measurements.md:10)、[s2-plan.md:24](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s2-plan.md:24)、[silo-backoff-fixed.patch:70](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/patches/silo-backoff-fixed.patch:70)
- 反例と再導出:
  - `start=1` は hash 上位 bit 1、`start=2` は bit 0。plan の「1/0」は正しい。
  - v=1500 では start 1→696、start 2→358。親表の700.5は別の bit 0 witnessなら可能だが、その exact start が記録されていない。
  - v=2500 は bit 0→250、bit 1→750。親表は「bit 0 / 1」の列へ750/250と書いており、列見出しが逆。
  - q=1 の値は上位 bitだけでなく下位63 bitの剰余にも依存する。2観測を完全な実現集合とは扱えない。
- 成果物影響: 1500/2500を将来 golden にすると偽赤になる。集合一般化は「複数値を取りうる」まで正しいが、表の2値を分布全体とはできない。
- 最小修正: exact start、hash、上位 bit、下位剰余、期待 bits を context ごとに記録する。

### 9. [real][high][scope 内][non-blocker: 段2 plan は訂正済み] 親 brief は「未配線 gate が投入前に止める」と矛盾している

- file:line: [s1-brief.md:40-52](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s1-brief.md:40)、[s2-plan.md:172-175](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s2-plan.md:172)
- 反例: P5 は driver 配線0本とする一方、成果物影響は1000点を gate が投入前に止めるとする。module が存在するだけでは `backoff_extended_sweep.py` から呼ばれない。
- 成果物影響: 現 driver が保護済みと誤読される。段2 plan の scope 上限はこの点を正しく訂正している。
- 最小修正: 「T-1999 後に配線された場合だけ止める」と書き換え、現 driver は未保護と明記する。

### 10. [real][medium][scope 外: 裁定パッケージ] 「上端999では閉じない」の根拠が過大

- file:line: [parent-measurements.md:38-43](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/parent-measurements.md:38)、[s1-brief.md:41-42](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s1-brief.md:41)
- 反例: `0 <= v <= 999` を機械的な値域制約にすれば、常に商0で decoder は恒等になり、現在の fixed-magnitude grid の衝突は閉じる。3000や3007はその値域から除外されるため反証にならない。
- 成果物影響: 「999制限」と「1000以上も表現できる新符号化」の選択肢比較を不当に狭める。ただし999制限だけでは define-decode 族全体や他8 defineは閉じない。
- 最小修正: grid/符号化は編集せず、裁定パッケージへ次を分離する。
  - A: `BACKOFF_FIXED` の固定量 domain を0..999へ機械制限する。
  - B: 1000以上を表現できる衝突なし符号化へ変更する。
  - C: 族一般の meaning gate は別に維持する。

### 11. [nit][low][scope 内]

- file:line: [s2-plan.md:28-37](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/verbatim/s2-plan.md:28)
- 反例: 実入力が `BACKOFF_FIXED` の float64 しかない段で、int64/uint64と他8 define向けの汎用 schemaを入れると、未実在の意味契約を先取りする。
- 成果物影響: 分岐と未検査 surfaceが増える。
- 最小修正: v1は `BACKOFF_FIXED`、`float64`、`start:uint64_t` に限定し、他型は実 contract 入力が現れた waveで追加する。

## Refuted

- **case ごとの `#define` 自体が必ず compile を壊す、は refuted。** 非負の現行 caseでは前処理はTUを上から処理するため、関数直前の `#define`、block内 `#if/#else`、直後の `#undef` は成立する。問題はmacroがC++ scopeを持たないこと、stock枝、周辺文脈、複数copy間の漏れである。
- **1000/2000/3000が0になる点は refuted されない。** 剰余0では商1、商2、商3以上の全枝が0になる。より一般に1000の正の倍数は0へ落ちる。3007→7も式どおり。
- **F707を supply 不在だけで落とす処理順は妥当。** 有効な非空供給表を残し、対象mappingだけを除けば、marker/compileより先に `macro-not-supplied` を出せる。存在しない compiler を渡す検査も理由の優先順位を固定する。
- **F718を meaning mismatchだけで落とす処理順も妥当。** declared comparisonをinjectivityより先に行い、1000単独のdeclared fixtureへ分ければ、supply、materialization、compile後に `decoded-meaning-mismatch` だけを得られる。
- **同一 source bytesをhashとTUに使う案には局所的な価値がある。** sourceの二度読み混在は防ぐ。ただしOptions/protocol/buildとの混成は防がない。
- **`source_digest.BUILD_FLAGS` の C++20/O3/NDEBUG 再利用は core flag の整合として妥当。** include、TU注入macro、target固有defineまで同じになるわけではない。

## 推奨 plan v2

1. v1の主張を `BACKOFF_FIXED` のみに縮める。証明名は以下にする。

   - `compiler-evaluated-captured-full-source-declared-context-pointwise-witness`
   - `compiler-evaluated-captured-full-source-context-vector-injectivity-witness`

2. source、Options、protocol CMakeを安定snapshotとして読み、全hash、compiler realpath/version、argvを evidence に束縛する。実 buildとの再照合は本 waveでは行わず、dynamic reachabilityやexact build inputを名乗らない。

3. `parse_supplied_macros()` の名前集合だけを使わない。左辺→cache変数mappingを公開APIで取得し、CMake cache overrideから実効TU macro値を導出する。F707はmapping不在で落とす。

4. marker block単体TUを廃止する。捕捉した全 `backoff.hh` の一時copyをinstrumentし、元のinclude、class、member、周辺preprocessor文脈でコンパイルする。case × contextごとに別TUとする。

5. contractをpointwiseにする。

```text
case define_value
  context_id -> expected float64 bits
```

重複context、重複case、非有限observed、非正準bitsを拒否する。injectivityはcontext→bitsベクトルで比較する。

6. fixtureを分離する。

   - positive: 0、5、999
   - F707: positive treeから供給mapping1行だけ欠落
   - F718-declared: 1000のみ、期待 `408f400000000000`、観測 `0000000000000000`
   - F718-injectivity: 0と1000、期待値なし
   - outer-conditional、local macro redefine、stock -1、negative zero、NaN、重複row、欠落rowの敵対fixture

7. frozen patchからmarker blockを再構成し、fixture blockとのbyte完全一致を要求する。patch自体は編集しない。

8. mutation anchorは次の単一nodeへ限定する。

   - supply membership削除 → F707 reason node
   - cache mapping検査削除 → wrong-RHS node
   - full-source評価をblock-onlyへ縮退 → outer-conditional node
   - case define固定0 → positive-5 node
   - pointwise比較削除 → F718-declared-1000 node
   - injectivity比較削除 → F718-injectivity node
   - output cardinality削除 → duplicate-row node
   - finite検査削除 → NaN node

9. T-1999は裁定待ちのまま維持する。driver配線0本、現行1000点は未保護、grid/符号化の変更は裁定パッケージへ返す。