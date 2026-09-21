# Silo の関数単位合成空間 — 設計 (軸 `silo-function-policy`、2026-09-21)

- 位置づけ: 設計文書。軸オンボーディング (`docs/axis-onboarding.md`) の段階 B (軸定義シート + 3 レンズの設計敵対レビュー) に当たる。採用判断の正本は同じ wave の decisions fragment (条件付き採用と必須条件)。可変状態の正本 (worklog 末尾・`docs/phase3.md`) にはしない。
- 作成: 2026-09-21、dev-wave `worktree-dev-wave-silo-function-synthesis-space` (基準 local main `36fb14a3d`)。実装・build・計算投入はしていない。実装は次の wave で Codex author が行う。
- 根拠のユーザー裁定: VLDB 方針の裁定 項 3 (LLM が関数単位でコードを書ける合成空間を開く。現行の編集面の制限を広げてよい。正しさゲートは不変)、項 4 (1 タスクの計算が 2 node 時間以上なら投入前に確認)。控えの逐語は `verbatim/vldb-direction-verdicts.md`。
- 以下の file:line は同 commit の worktree で確かめた。`T:` は `external/ccbench/cc/silo/transaction.cc`。「案」「設計値」は新規設計で、実装済み・較正済みではない。

## 0. 要約

1. **境界は「方策と仕組みの分離」。** LLM が書くのは、abort 後に何 µs 待つか、lock 競合時に待って再試行するか中断するか、成功 commit 時に自分の状態をどう更新するか、の 3 関数と補助関数・状態型だけ。CAS・unlock・absent 検査・validation・tid 生成・writePhase・trace・同じ txn の再試行は、人間が一度入れる骨格が持つ。
2. **validation と lock の仕組みは v1 で開かない。** そのため v1 は「LLM が壊した CC 論理を verifier が捕らえる」ことを実証する空間ではない。機構を開く後続版の前提は、差分分析 P0 の検出力測定である。
3. **受理する C++ は型付きの部分言語 policy-C++ v1 に閉じる。**
   - 算術・bit・shift の被演算子は `uint32_t` / `uint64_t` だけで、`bool` は論理・比較・条件にしか使えない。
   - pointer・配列・loop・再帰・記憶域指定子・template・演算子 overload・代替綴りは禁止。
   - 検査は、許可リストの構文検査 (型付き・名前解決つき) と、候補本文を CC ヘッダ抜きの単独 TU で compile する検査の 2 段で行う。
4. **状態は worker 内で txn をまたいで持てる。** 骨格が所有する `thread_local` を 1 個だけ参照で渡し、成功 commit ごとに通知する。共有状態と時刻は渡さない。レンズ B の推奨に従い、txn をまたぐ負荷追従を表現するための選択である (レンズ A と auditor は txn 内に限る案を支持した、§2.5)。
5. **探索の共通表現は「領域の C++ 本文」。** random / sweep / 非 LLM 進化 (後に BO) は、型付き有限 IR (policy-C++ v1 の部分集合) の上で動く。比較は、同じ IR 上の探索法比較 (非 LLM×IR と LLM×IR) と、LLM×C++ による空間拡張の比較に分ける。
6. **見積り (投入しない)。** B-5 試走の旧単価から換算したシナリオ値で、上下限ではない。
   - C 段 (生死確認・負例・機構変異・受入): 合計 2.41〜4.12 node 時間。
   - D 段の偵察: 1.15〜2.69 node 時間。
   - 最初の比較試走: 8.98〜21.1 node 時間 + LLM 8.0〜10.4 時間。
   - 3 段とも 2 node 時間以上になりうるので、投入前にユーザー確認が要る。

## 1. 背景と依頼

- 現行の編集面は `#if` 合成枝の中身だけである。#include・関数・型の追加は禁止で、編集できる file は 3 本 (`orchestrator/campaign/source_digest.py:85-100` の `EVOLVE_BLOCK_SOURCES` / `ALLOWLIST`、`docs/phase3.md`「EVOLVE-BLOCK 機構」)。
- 既存の軸はどれも有限で列挙し尽くせる。
  - backoff の値 1 個: 1..1000 µs。
  - sort: 79 値。
  - trigger: 5 bit。
- B-5 試走では LLM・random・sweep の差が 1.06% で、床 3% の内側だった (差分分析 §1)。
- 依頼の返却物は次の 5 つ。
  1. 境界と骨格
  2. 検出力を保つ方法
  3. driver・coder role への接続
  4. 非 LLM と LLM が同じ空間を探索できる表現
  5. 試走の見積り
- 依頼は加えて、validation・lock 取得の周辺を含めるかの判断を求めた。

## 2. 書き換え面の境界と骨格 (返却物 1)

### 2.1 境界

| 箇所 | 現行 | v1 |
|---|---|---|
| `abort()` T:27-53 | 集合の clear 後、`#if BACK_OFF` (T:42) 下で `Backoff::backoff` (T:47) | cleanup は骨格。待機量だけ方策が返し、骨格が上限つきで待つ |
| `lockWriteSet()` T:145-193 | `expected.lock` なら status=aborted・取得済み prefix を unlock・return (T:160-164) | 方策が retry / abort を返す。CAS・trace 記録・unlock・absent 検査 (T:185-187) は骨格 |
| `validationPhase()` T:383- | write set を sort (T:408) してから lock (T:437)、read 版・他者 lock・node 版を検査 (T:458/470/481) | 開かない |
| `writePhase()` T:557- / `commit()` T:706-713 | tid 生成・trace・書込み・unlock | 開かない。`commit()` の成功直後に方策へ成功通知を呼ぶ骨格を足す |
| YCSB の再試行 `include/ycsb.hh` | `makeProcedure` は RETRY (108) の前 (102)。abort 後は同じ手順を再試行 (150-164) | 変えない。方策は txn の破棄・再生成・計数に触れない |

- lock 取得順は sort 済みである (T:408 → T:437)。そのため、上限つきの lock 待ちを入れても deadlock しない。
- 読み手は lock が外れるまで spin する (T:255)。したがって、骨格が漏らした lock に読み手が到達する workload では、既存の `trace-timeout` に落ちる。legacy verify は RMW (`pipeline.py:147`) で読みを含む。

### 2.2 validation・lock の仕組みを含めるか — 含めない

- 仕組みを開けば、「LLM が壊した候補を verifier が捕まえる」ことは測れる。
- しかし既存の証拠 (D38 の被覆検査 T:624-631 / T:650-655、`patches/broken-silo-*.patch` の負例) から、LLM が書いた CC 機構に対する検出力を一般化できない。
  - 有限 trace、未到達の競合、torn read、abort 中の作用は死角である (`.claude/agents/auditor.md` 冒頭)。
  - この状態で機構を開くと、certified の意味が保てない。
- v1 で測れるのは次のもの。
  - 関数生成の有効率
  - reject の分類
  - 検証費用
  - 探索法と表現の比較
- 機構を開く後続版の前提は、P0 の検出力測定 (意味の異なる CC 変異 20〜40 個) である。

### 2.3 置き場 — include の前には置けない

- 当初案 (P4) は、CC ヘッダの include より前に領域を置き、CC の大域を定義点で未宣言にする案だった。これは成立しない。
  - 骨格 patch も include を足せない。include 行は HEAD と順序込みで比較される (`source_digest.py:2160` `assert_includes_match_head`)。
  - identity の preprocess は `-nostdinc` で include を外す (`source_digest.py:1647` `_cpp_normalize`、実処理は :1686-1687)。
  - 最初の CC include `include/atomic_tool.hh` (T:5) の時点で、`<atomic>`・epoch 系・FLAGS・`CCBenchResults`・`rdtscp` が同時に見える。経路は `atomic_tool.hh:3` → `common.hh:4/25/50/69`、`tuple.hh` → `util.hh` → `result.hh` / `tsc.hh` (段 2 草稿 §1.3)。
  - その手前では、方策に要る型すら揃わない。
- 採る案は次のとおり。
  - 領域は include 列の後 (T:9 の後) に置く。
  - 封じ込めは配置ではなく、受理契約 (§2.7) と単独 TU compile で行う。
  - 別 TU 案は採らない。protocol の CMakeLists と `ALLOWLIST` の変更を要するため。

### 2.4 骨格の擬似差分 (未実装の構造図)

```
cmake/Options.cmake:
+ set(CCBENCH_SILO_POLICY_VARIANT 0 CACHE STRING "izanagi: 0=stock, 1=function policy (EVOLVE-BLOCK, silo only)")
  ccbench_universal_definitions() に SILO_POLICY_VARIANT=${CCBENCH_SILO_POLICY_VARIANT} を追記

transaction.cc: include 列 (T:1-9) の後
+ #ifndef SILO_POLICY_VARIANT / #error / #endif        (供給漏れを止める)
+ #if SILO_POLICY_VARIANT
+   #if !BACK_OFF || NO_WAIT_LOCKING_IN_VALIDATION != 1 || NO_WAIT_OF_TICTOC != 0 → #error   (flag の別名化を止める)
+   namespace izanagi_silo_api { enum・Context・Response 型 }   (骨格型。単独 TU 用の api header と同じ正本から生成)
+   namespace izanagi_silo_policy {                           (外枠は marker の外の骨格)
+ #endif
+ // EVOLVE-BLOCK-BEGIN silo-function-policy
+ #if SILO_POLICY_VARIANT
+   [hole: namespace izanagi_silo_policy の本体だけ = PolicyState・定数・補助関数・必須 3 関数]
+ #else
+ #endif
+ // EVOLVE-BLOCK-END silo-function-policy
+ #if SILO_POLICY_VARIANT
+   }  // namespace izanagi_silo_policy
+   namespace izanagi_silo_skel { thread_local 状態の実体、要因記録、PRNG、上限つき待機器、__attribute__((noipa)) の呼出し wrapper }
+ #endif

abort(): T:47 を #if SILO_POLICY_VARIANT で分岐 (ON = 骨格 wrapper 経由の上限つき待機、OFF = Backoff::backoff を逐語保存)
lockWriteSet(): 内側ループを #if SILO_POLICY_VARIANT で分岐 (§2.6)。既存の TRACE ブロックは位置も内容も変えない
begin(): 要因を unset に戻す。7 つの abort 代入点: 要因を記録 (§2.5)
commit(): writePhase() 成功後に成功通知
```

- 軸 OFF (既定 0) では、領域・骨格・呼出し点がすべて消え、stock と preprocess が一致する (inert、src_token = stock)。
- **軸 ON のとき、`BACK_OFF` が 1 でない、または no-wait 系 flag が固定値 (1 / 0) でない genome は `#error` にする。** genome の flag が実際の挙動を表さなくなるのを防ぐためである。`BACK_OFF=0` のままだと abort hook が黙って呼ばれない。
- namespace の開き・閉じは marker の外の骨格に置く。coder の implementation は namespace の本体だけで、`render_hole` (`p3_s4_loop.py:693`) が置換するのも marker 間の #if 枝の行だけになる。
- 空の stock 枝・複数行 hole・名前空間 scope の領域は、既存の parser と検疫で扱える。
  - `diff_quarantine.py:567` `parse_template_file` は `begin < if < else < endif < end` だけを要求する (:637)。
  - `render_hole` は行の slice を置換する。
- 呼出し点は marker の外の固定骨格なので、複数 marker 対応は要らない。

### 2.5 hook の署名・観測・状態

```cpp
namespace izanagi_silo_api {
enum class PolicyAction : uint32_t { retry = 0, abort = 1 };
enum class AbortReason : uint32_t { unset, lock_conflict, update_absent, read_tid, read_locked, node_validation, insert_node, scan_node };
struct AbortContext  { AbortReason reason; uint64_t rand; };
struct LockContext   { uint32_t attempt; uint64_t rand; };
struct LockResponse  { PolicyAction action; uint32_t wait_us; };
struct CommitContext { };
}
// hole が定義する必須 3 関数 (署名は固定、それぞれちょうど 1 つ):
uint32_t policy_after_abort(PolicyState& s, const izanagi_silo_api::AbortContext& c) noexcept;
izanagi_silo_api::LockResponse policy_on_lock_conflict(PolicyState& s, const izanagi_silo_api::LockContext& c) noexcept;
void policy_on_commit(PolicyState& s, const izanagi_silo_api::CommitContext& c) noexcept;
```

- **要因の記録。** 骨格の 7 記録点を写像として固定する。
  - insert の node 版不一致 T:98 → `insert_node`
  - lock 競合 T:162 → `lock_conflict`
  - update 対象の不在 T:187 → `update_absent`
  - read の tid 変化 T:458 → `read_tid`
  - read が他者の lock T:470 → `read_locked`
  - node 版 T:481 → `node_validation`
  - scan の node 版 T:739 → `scan_node`
  - `begin()` で `unset` に戻す。既存 trigger 骨格 (`patches/silo-backoff-trigger-gating-variant.patch`) の記録点と同じ集合である。
  - 実際に待機を決める用途なので、軸 ON で両 build に存在する CC 本来の状態とし、`#if TRACE` には置かない。
- **観測するもの。** abort 要因、同じ tuple での試行番号、骨格の PRNG による乱数 (待ち時間の揺らぎ用)。
- **渡さないもの。** 時刻、read/write set の大きさ、競合位置、`thid_`、key、tuple pointer、Tidword、epoch、FLAGS、`result_`、`quit_`。
  - 時刻と共有状態を v1 に入れないことは、レンズ A (所見 6) と B (所見 9) が支持した。set の大きさと競合位置は段 2 草稿 (§6) が外し、レンズ A は型 15 の代理を増やすと評価した (所見 5 の表)。
  - 骨格・固定型の外の識別子 (`thid_`・key・pointer・Tidword・epoch・FLAGS・`result_`・`quit_`) は、受理契約と単独 TU compile で参照できない。
  - `result_` を隠しても、自前の事象列から作れる代理は消えない (D1409 の代理の壁)。この設計は代理を消したのではなく、局所的な代理を許容している。
- **状態。**
  - 骨格が `izanagi_silo_skel` に置く `thread_local` の PolicyState 1 個を参照で渡す。寿命は worker thread で、骨格は reset しない。
  - hole は書換え可能な持続状態 (静的・thread 記憶域の可変変数) を定義しない。関数内の自動変数と、namespace scope の `constexpr` 定数 (静的記憶域だが不変) は §2.7 の範囲で書ける。
  - 方策は `policy_on_commit` で自ら reset すれば、txn 内だけの状態を再現できる。txn 内状態の案は部分集合である。
  - 共有状態と時刻は v1 に入れない。

**状態の射程 (段 4 の択一) — 各レンズの判定と親の推論。**
- **レンズ A** は txn 内状態を推奨した。txn 内でも、lock の試行番号や連続する lock 競合 abort に応じた待機、つまり局所的な競合適応は表現できると明記している (レンズ A 所見 6)。worker 内の txn 間履歴については、型 3・12 の進捗の代理と型 15 の持続的な優先が増えるが、メモリ安全で骨格が固定なら害は進行性・性能・一般化に留まる、と判定した (同所見 5 の表)。
- **レンズ B** は、worker 内の限定した txn 間履歴と成功通知を v1 に入れるよう推奨した (レンズ B 所見 9)。成功時に状態が全消去されると、最近の競合傾向が違っても新しい txn が同じ状態から始まるためである。
- **auditor** は草稿どおり txn 内状態を支持した (条件 9)。txn 間履歴と共有状態を併せた場合について、次を判定した (「依頼 4」への回答)。
  - 型 3・12・15 と、協調的な liveness 崩しが新たに可能になる。
  - 契約が守られる限り、害は直列化可能性に及ばず性能値の歪みに留まる。
  - ただし例外が 2 つある。非 atomic の共有は data race で正しさに届く。型 3 と組むと、認証した経路と計測した経路が別になる。
- **親の推論。** 依頼が名指しした「競合の状態に応じた待機方策」のうち、txn をまたぐ負荷追従は txn 内状態では表現できない。その部分を表現するため worker 内の txn 間履歴を採った (レンズ B の理由)。auditor の 2 つの例外は次のように扱う。
  - data race: 共有状態を入れないことで除く。
  - 型 3 の留保: 次の 2 点で扱う。
    - LLM×C++ の全候補に性能構成の verify を適用し、verify と perf の workload の差を縮める (§3.2)。
    - 「verify で性能側と同じ分岐を踏んだとは言えない」という限定を報告に残す (§3.1)。
- 根拠のユーザー裁定は項 3 と依頼文である。D48 の読取禁止は trigger 軸の契約として不変で、D1409 が保留した trigger 軸の問いもこの決定で解消・変更しない。両者は、新しい軸での代理の許容を承認した根拠ではない。

### 2.6 lock ループ (骨格の仕様)

- tuple ごとに `attempt = 0` から始める。内側ループの毎周回の先頭で `attempt >= 32` を判定する。CAS 失敗も 1 周として数える。CAS 失敗時は `compareExchange` が expected を書き戻すので (`include/atomic_wrapper.hh:67-69` の `__atomic_compare_exchange_n`)、再読込は要らない。
- `expected.lock` を見たら、`__attribute__((noipa))` の wrapper 経由で `policy_on_lock_conflict` を呼ぶ。
  - action の判定は組込型比較 `static_cast<uint32_t>(r.action) == 0u` で行う。
  - retry なら `min(wait_us, 50)` µs を骨格の busy wait で待ち、`loadAcquire` で expected を読み直して次の周回へ進む。
- abort・未知の action・上限到達のいずれも、stock の abort 出口を通る。
  - status=aborted、要因 `lock_conflict`、取得済み prefix の unlock、return。
- abort 後の待機は `min(policy_after_abort(...), 1000)` µs。軸 ON では `BACK_OFF=1` が必須 (§2.4)。`ADD_ANALYSIS` の計数は保つ。
- 上限 (1000 µs / 50 µs / 32 周回) は全生成器に共通の試走設計値であり、最適値ではない。
- 上限は hook が戻る場合の待機上限である。hook 自身の停止は、受理契約 (loop・再帰の禁止) で保証する。
- 既存の TRACE ブロックは新しい `#else` に巻き込まない。対象は `clear_shadow` (T:152)、CAS 成功時の `record_lock` (T:179)、被覆・retention の検査である。巻き込むと diff-of-diffs の差分内容が変わる。

### 2.7 受理契約 policy-C++ v1 (型付きの許可リスト)

**字句。**
- 代替綴り (`and` `or` `not` `bitand` `bitor` `compl` `xor` と `_eq` 形) と digraph (`<:` `:>` `<%` `%>` `%:`) は全拒否する。
- 次も全拒否する: `__` を含む識別子 (事前定義マクロと組込関数を含む)、先頭 `::`、文字列・文字 literal、`[` `]`、`->`。
- 整数 literal の接尾辞は `u` か `ul` (大文字・小文字の組合せを含む) だけを許す。接尾辞なし・`l` 単独・`ll` / `ull` 系は拒否する。

**型の体系。** 対象は x86_64 Linux (LP64) の GCC である。
- **U32** = `uint32_t` = `unsigned int`。**U64** = `uint64_t` = `unsigned long`。どちらも `int` への昇格を受けない。
- literal の型は C++17 の規則どおりに決め、値が `UINT64_MAX` を超える literal は拒否する。
  - `u` 接尾辞: 値が 32 bit に収まれば U32、収まらなければ U64。
  - `ul` 接尾辞: U64。
  - C++17 の候補型の列には `unsigned long long` も含まれる。しかし対象では `unsigned long` と `unsigned long long` がともに 64 bit で、`UINT64_MAX` 以下の値は先に `unsigned long` に収まる。したがって literal の型は U32 / U64 に閉じる。
- ほかに `bool`、`izanagi_silo_api` の列挙型 (`PolicyAction` / `AbortReason`)、`izanagi_silo_api::LockResponse`、`PolicyState`、骨格 Context の型がある。

**名前解決。** 識別子が指してよいのは次だけである。
- 自前の宣言 (PolicyState とそのメンバ・定数・関数・引数・局所変数)
- `izanagi_silo_api::` の型・列挙子・Context field
- `uint32_t` / `uint64_t` / `bool`
- `std::min` / `std::max` (呼出し位置だけ)

**上位の宣言** (hole = `izanagi_silo_policy` の本体)。
- `struct PolicyState { T name = literal; ... };` をちょうど 1 つ。
  - メンバの T は U32 / U64 / bool で、16 以下。既定初期化子 (その型の literal) 必須。
  - メンバ関数・constructor・演算子・static メンバは持たない。
- `constexpr T name = 定数式;`
  - T は U32 / U64 / bool。定数式は literal・先に宣言した constexpr 定数・下の演算子だけで作る (呼出しなし)。
  - namespace scope の constexpr は静的記憶域を持つが不変なので、書換え可能な持続状態の禁止 (§2.5) に当たらない。
- 関数定義。必須 3 関数 (§2.5 の署名、それぞれちょうど 1 つ) と補助関数を書ける。
  - 戻り型は U32 / U64 / bool / `izanagi_silo_api::LockResponse` / `void`。
  - 引数は U32 / U64 / bool / 列挙型の値渡しか、`PolicyState&` / `const PolicyState&` / `const izanagi_silo_api::AbortContext&` / `const izanagi_silo_api::LockContext&` / `const izanagi_silo_api::CommitContext&`。引数名は自由。
  - 定義前の使用 (前方宣言) と自分自身への参照は禁止で、したがって呼出し graph は DAG になる。
  - すべて `noexcept` とする。

**文。**
- 初期化子つき局所宣言。
  - T は U32 / U64 / bool / 列挙型 / `izanagi_silo_api::LockResponse`。`const` を付けてよい。
  - 初期化子の中で宣言中の変数を参照しない。
- 代入・複合代入。**独立した式文 (`x = e;`、`x += e;`) としてだけ書ける。** 式の部分式には書けない (同じ状態を別名の参照で 2 回書く、順序づけられない書込みを作らないため)。代入先は次の 3 つだけ。
  - const でない局所変数
  - const でない `PolicyState&` 引数のメンバ
  - 局所の `LockResponse` のメンバ
- `++` `--` とカンマ演算子は禁止する。
- 自前の関数の呼出しは式の中に書ける。ただし式の中の呼出しどうしは C++17 では不定順序であり、順序なしではない。そのため、補助関数の中の代入が未定義動作を作ることはない。
- 呼出し文 `helper(args);` (戻り型 void の自前の関数だけ)。
- `if` / `else`、ブロック `{ }`。
- `switch`。
  - 条件は U32 / U64 か列挙型。case label は整数 literal か完全修飾の列挙子。
  - 各 case と default を `break` か `return` で閉じる。case 内の局所宣言はブロックで囲む。
- `return`。
- 非 void 関数は、関数本体の最後の文を `return` にする。loop と goto が無いので、これで全経路が return する。末尾に「全枝が return する if」を置く形は、この狭い規則では拒否する。

**式と型の規則 (構文検査が部分式ごとに型を付ける)。**

| 演算 | 被演算子の型 | 結果の型 |
|---|---|---|
| `+ - * & | ^` | 両辺 U32 / U64 | どちらかが U64 なら U64、両方 U32 なら U32 (C++17 の通常算術変換) |
| `/ %` | 両辺 U32 / U64、右辺は非零の整数 literal | 上と同じ通常算術変換 (左辺の型ではない。例: `x / 1ul` は U64) |
| 単項 `~ -` | U32 / U64 | 被演算子の型 |
| `<< >>` | 左辺 U32 / U64、右辺は左辺の型の幅未満 (U32 は 32 未満、U64 は 64 未満) の整数 literal | 左辺の型 |
| `+= -= *= &= |= ^=` | 代入先 U32 / U64、右辺 U32 / U64 | 代入先の型 (計算後に代入先の型へ変換。U64→U32 は剰余で定義済み) |
| `/= %=` | 代入先 U32 / U64、右辺は非零の整数 literal | 代入先の型 |
| `<<= >>=` | 代入先 U32 / U64、右辺は代入先の型の幅未満の整数 literal | 代入先の型 |
| `=`、局所宣言の初期化、`return` の値、実引数 | U32 と U64 の間は相互に可 (剰余で定義済み)。bool・列挙型・`LockResponse` は同じ型だけ (例: U32 を返す関数で `return true;` は拒否し、`static_cast<uint32_t>(true)` を要求する) | 代入先・宣言・戻り値・仮引数の型 |
| `< <= > >=` | 両辺 U32 / U64 | bool |
| `== !=` | 両辺 U32 / U64、または両辺 bool、または両辺が同じ列挙型 | bool |
| `! && ||` | bool だけ | bool |
| `?:` | 条件は bool、両枝はまったく同じ型 (U32 と U64 の混在は不可) | 枝の型 |
| `static_cast<uint32_t / uint64_t / bool>` | U32 / U64 / bool / 列挙型 | 指定型 |
| `std::min(a, b)` / `std::max(a, b)` | 2 引数で、a と b がまったく同じ型 (U32 どうし / U64 どうし)。明示 template 引数・initializer_list 形・比較関数引数は禁止 | その型 |
| 呼出し | 自前の関数だけ。実引数の型は仮引数と同じ (U32 と U64 の間は代入と同じく可) | 戻り型 |
| メンバ読出し | `名前.メンバ`。名前は `PolicyState`・Context・`LockResponse` 型の引数か局所変数、メンバは宣言済みのもの | メンバの宣言型 |
| 列挙子 | `izanagi_silo_api::PolicyAction::retry` のように完全修飾 | 列挙型 |
| `LockResponse` の構築 | `izanagi_silo_api::LockResponse{PolicyAction 型の式, U32 の式}` の集約初期化だけ | `LockResponse` |

- bool に算術・bit・shift を使うこと (`b + b`、`~b`、`b << 1u`) は禁止する。bool から数値へは `static_cast<uint32_t>(b)` を明示する。これで `int` への昇格を経る signed overflow と負値 shift が生じない。
- **禁止 (許可リストに無いものは全て)。**
  - pointer、配列、参照 (固定引数形以外)、単項 `&` / `*`
  - template、lambda、他の cast、`new` / `delete`、`this`
  - `static` / `thread_local` / `extern` / `inline` / `mutable` / `volatile` / `union`
  - `asm`、`namespace` / `using` / `typedef`、演算子 overload、変換関数
  - `throw` / `try`、loop (`for` / `while` / `do`)、`goto`
- **機械執行 (いずれも build 前)。**
  1. 既存の DiffQuarantine。領域外の差分、前処理指令、`//` `/*`、行末 backslash、marker 文字列を拒否する。
  2. 既存の `coder_effect_gate.scan_host_effects`。host 効果を拒否する。上限は領域全体で 256 KiB / 4096 token (`coder_effect_gate.py:114-115`)。
  3. **型付きの構文検査。** 上の字句・名前解決・宣言・文・式の規則を受理する parser で、受理できない構文は全て拒否する。禁止語の grep ではない。
  4. **単独 TU compile。** hole 本文を、`<cstdint>`・`<algorithm>` と固定の api header (骨格型と署名。実 TU の骨格型と同じ正本から生成し、一致を検査する) だけの TU で `-std=c++17 -Wall -Wextra -Werror -fsyntax-only` にかける。-D は与えない。
- 2 段 (3 と 4) の分担は次のとおり。
  - 構文検査で閉じるもの: 宣言形、記憶域、呼出し graph、式の型、初期化の自己参照、演算子別の右辺制約、return の位置、代替綴り。
  - 単独 TU compile で閉じるもの: 未宣言の外部名 (CC の大域・FLAGS・`TRACE` 等の -D マクロ・`izanagi_trace`・`rdtscp`)、型不一致、署名不整合。
  - 実 build の `-Wall -Wextra -Werror` (`cmake/CompileOptions.cmake:32`) は、さらに外側の網である。
- この構文検査が既存 hole の閉じた領域制約に代わるのは、この軸だけである。既存 3 軸の受理集合は変えない。
- **契約が構造的に除く未定義動作。** 構文検査器と単独 TU compile が仕様どおり実装されている限り、次を除く。
  - OOB (pointer・配列なし)
  - signed overflow と負値 shift (算術・bit・shift の被演算子は U32 / U64 だけ)
  - 初期化前読出し (初期化子必須、初期化子での自己参照禁止)
  - 非停止 (loop・再帰なし)
  - return 欠落 (最後の文が return)
  - 過大 shift と零除算 (右辺は literal で、幅未満・非零)
  - 順序づけられない同一対象への書込み (代入・複合代入は独立した文だけ、`++` `--`・カンマ演算子なし)
- 残る不確実性は、構文検査器と compile 検査の実装の誤りである。そのため C 段で、手書き方策と契約負例に UBSan 付き単独 TU harness を 1 回だけ回す (§3.3)。

## 3. 検出力を保つ方法 (返却物 2)

### 3.1 観測者効果の分離 (規律 1)

- 方策・要因記録・待機器は TRACE に依存せず、両 build に載る。コストは性能側にも載る。
- trace と被覆検査は、従来どおり compile 時に除去する。
- hole は前処理指令を持てない。式中で `TRACE` を参照すれば、`_trace_pair_diff` (TRACE=1/0 の preprocess 差) に差分行が出て、既存の `assert_trace_diff_matches_head` (`source_digest.py:2205`) が止める。単独 TU compile でも未宣言で落ちる。
- ただし、preprocess の一致は実行軌跡の一致を保証しない。
  - trace の遅延で競合の順序が変われば、同じ方策が別の応答を選ぶ。worker 内の状態は reset されないので、verify と perf で状態の温まり方も違う。
  - 契約適合の方策なら、どの応答も骨格の直列化可能性条件を弱めない。
  - しかし「verify で性能側と同じ分岐を踏んだ」とは言えない。報告ではこの限定を保つ。

### 3.2 verify 構成と reject 分類

- この軸の候補は、LLM×C++ の全候補と比較の全 arm に、legacy (200 records / 4 threads / RMW / 1 秒、`pipeline.py:147`) と実際の性能 workload の verify の両方を適用する。S2 の balanced だけでは代表させない。
- 新しい reject 閾値は作らない。現行の分類は次のとおり。
  - `build-error` (`pipeline.py:2028`)
  - `trace-timeout` (120 秒、`:357` / `:527`)
  - `trace-run-nonzero-exit` (:581)
  - `trace-empty` (:587)
  - `trace-no-abort-counts` (:593)
  - verifier の verdict (`non-serializable` / `indeterminate`)
  - `bench-no-throughput` (:1441)
- 報告では次を混ぜない。
  - 検疫・契約の赤 / build の赤 / liveness の赤 (timeout・empty・no-throughput) / integrity の赤 (X・P) / G2 の赤
  - 人為的な骨格負例の赤。これを「LLM 方策の anomaly」と数えない。
- 一部の worker だけが飢餓になっても、全体の C 行があれば `trace-empty` にはならない。公平性は認証しない。
  - YCSB は同じ txn を再試行し続ける。そのため飢餓は「長い txn の後回し」ではなく、「worker の駐車 (実質的なスレッド数の削減)」として現れる。

### 3.3 C 段の正例・負例 (事前登録の候補)

実体を名指しし、期待する検査と期待 verdict を先に書く。候補ごとの gate ではなく、C 段で 1 回走らせる。

| 区分 | 対照 | 期待 |
|---|---|---|
| 正例 | 軸 OFF の inert 骨格 | src_token = stock、include 一致、diff-of-diffs 一致 |
| 正例 | 軸 ON の手書き方策 (待機 0 + 即 abort、静的 5 µs / 10 µs、上限内 retry) | build・verify 緑、honest identity (別 digest) |
| 骨格負例 | 既存 3 負例 (norw / lockskip / early-unlock) を軸 ON の経路に積み直す | 順に `non-serializable` / X `not-locked-at-entry` / X `lock-lost-before-write`。break が軸 ON の compile 経路に載っている証拠 (preprocess 後の出力に break が残る) を添える。方策は即 abort と最大待機の 2 通り |
| 機構の変異 | clamp を削除し UINT32_MAX を返す方策 | `trace-timeout` (clamp ありなら pass) |
| 機構の変異 | 待機後の再読込を削除し「待機 0 で retry」の方策 | 焦点試験「他者の解放後、上限内に取得へ進む」が不成立。timeout を期待しない (上限で abort に落ちる) |
| 機構の変異 | 周回上限だけを削除 | sort 済みの取得順なので、今回の正しさ検査では検出を期待しない。検出力の主張に使わない |
| 機構の変異 | hook の abort 出口または上限出口で prefix unlock を省く | 読み手がその lock に到達する legacy verify (RMW) で、読み手の spin (T:255) により `trace-timeout` |
| 機構の変異 | abort / lock / 成功通知の各 hook の配線解除 (3 走)、要因の誤記録 | 試験専用 probe build (下記) の計数で赤 |
| 契約負例 (単独 TU) | `Masstrees`・`FLAGS_thread_num`・`TRACE`・`izanagi_trace::record_lock`・`rdtscp`・`GlobalEpoch` を参照する hole | 単独 TU compile で赤 |
| 契約負例 (構文) | `__TIME__`・`__COUNTER__`、`static` 局所・追加 `thread_local`、`operator==`、template、配列、loop、再帰、`(b1 + b2) << 31u`、`(~b) << 1u`、`uint32_t x = x;`、`x = helper(x)` 形の自己参照、最後の文が return でない非 void 関数、`s.m /= v` (v は変数)、部分式の代入 `(a.m = 1u) + (b.m = 2u)`、`x++`、カンマ演算子、`bitand`・`<:`・`:>`・`%:`、U32 を返す関数の `return true;` | 構文検査で赤 (`%:` は DiffQuarantine でも赤になるかを確かめる) |
| 契約負例 (骨格) | 軸 ON かつ `NO_WAIT_OF_TICTOC=1`、軸 ON かつ `BACK_OFF=0` | `#error` で build 赤 |
| 境界正例 | 上限を超える待機量を返す方策 | clamp されて戻る (reject ではない) |

- **検査器の自己試験。** 検査段ごとに、正常な検査器なら赤、壊した検査器なら通る組を登録する。
  - 単独 TU に大域宣言を誤って公開する変異 → 大域参照の負例 (`Masstrees`・`GlobalEpoch` 等) が通る。
  - 単独 TU へ -D でマクロを誤って供給する変異 → `TRACE` 参照の負例が通る。
  - 型付き規則を外した構文検査器 → 型の負例 (`(b1 + b2) << 31u` 等) が通る。
  - 代替綴りの字句規則を外した構文検査器 → 合法な二項の `x bitand y`・`a and b` を含む候補が構文検査を通る (正常な検査器なら字句段で赤)。単項 `bitand` や `<:` は後段の単項 `&`・添字の禁止でも赤になるので、字句段の自己試験には使わない。
- **hook ごとの発火の証拠。** C 段の焦点試験に限って、試験専用の probe build で取る。
  - probe は `CCBENCH_` 名前空間の外のマクロ (既存 `IZANAGI_BREAK_*` と同型) を使い、pipeline からは定義できないようにする。
  - 計数する実体は次のとおり: abort hook の呼出し、lock hook の呼出し、成功通知の呼出し、retry 後の取得成功、上限による abort、clamp の発生、要因別の abort。
  - 成功通知の焦点試験: 成功 commit ごとに 1 回呼ばれ、abort では呼ばれず、方策が更新した状態が次の txn の hook から見えること。
- **UBSan harness。** 手書き方策と契約負例 (UB を含む版) を、UBSan 付きの単独 TU harness で 1 回だけ駆動する。login で秒単位の検査で、node 時間には数えない。入力は全 abort 要因 × 試行番号 0〜33 × 呼出し列とする。構文検査器の誤りを見る観測点として置く。
- 候補ごとの TRACE 計数 (PIN 前進を伴う信頼済み計装) は v1 では入れない (§3.4)。

### 3.4 見送り (発火条件つき)

| 見送るもの | 理由 | 発火条件・既定の扱い |
|---|---|---|
| 候補ごとの sanitizer harness (auditor T3) | 型付きの部分言語が UB の型を構造的に除く (§2.7)。構文検査器の誤りは C 段の UBSan harness 1 回と自己試験で見る | C 段の UBSan harness または自己試験が赤になった、または構文検査を通った LLM 候補で UB が 1 件でも見つかった |
| 候補ごとの TRACE hook 計数 + PIN 前進 (auditor V6) | 契約適合の方策なら、lock hook の空振りは正しさを損なわない。C 段の機構試験は probe で足りる | **既定で、報告の lock 方策を「verify 中の発火証拠なし」と表示する。** 発火の証拠を添えた場合だけ解除する。試走の報告で lock 方策の効果を帰属する必要が出たら計装を入れる |
| 新 X 理由 `lock-held-at-abort` (auditor T5(d)) | lock を漏らせるのは方策でなく固定骨格で、C 段の prefix unlock の変異は読みを含む legacy verify で `trace-timeout` に落ちる | 読みを含む workload でも timeout にならない lock 漏れの実例 |
| per-worker の commit 分布の記録 (auditor V11) | CCBench の結果出力は `ALLOWLIST` の外。既存の残存リスク (D41 条件 3) と同じ扱い | **コードの形で判定する。** 単調に増えるだけの状態 (飽和加算など) が、待機の上限や abort に至る経路を持つ方策は疑いありとする。IR の系列も含めて、全系列の endpoint 候補と勝ち候補に auditor の公平性目視を課す。疑いがあれば記録の実装を別 wave で諮る |
| 共有状態・時刻の開放 | 型 3・12・15 と協調的な liveness 崩しの経路が増える。data race は正しさに届く | 局所・worker 内の方策で地形が平坦と分かった |
| validation・lock 機構の開放 | §2.2 | P0 の検出力測定の完了 |

## 4. 既存 driver と coder role への接続 (返却物 3)

- **段の順序 (オンボーディング §1、DW-G01)。**
  1. C 前の小さな docs wave: 手順書 §4 の第 3 列と planner 例外 (§8)。
  2. C: 骨格 patch、api header、構文検査と単独 TU compile、焦点試験と §3.3 の負例、手書き方策 数本の生死確認 (既存 evaluator か 100 行以内の使い捨て driver)。軸定数は C 段の module に置く。
  3. D: IR の機械偵察。
  4. 人間判断 (継続 / 見直し)。
  5. E: 兄弟 driver と role。
  6. F: 別セッションで実 LLM 系列。
  - 専用 LLM driver を C より先に作らない。C 出口は E の成果物に依存させない。
- **兄弟 driver** `orchestrator/campaign/p3_s4_loop_policy.py` (E 段)。
  - 再利用するもの: `quarantine` (`p3_s4_loop.py:716`)、`record_diff_reject`、`make_critic_digest(..., reflux=True)` (:1164)、auditor の digest 照合 gate、`pipeline.evaluate`。
  - 転用しないもの: sort の IR admission、trigger の wire、B-4 / 8c 固有の分岐。
  - 新 marker 用に、`quarantine` へ §2.7 の構文検査と単独 TU compile を差し込む分岐を足す。
- **planner は外す。** planner-v4 の方向契約 (増加 / 低下 / 両探索 + magnitude) は、複数 hook・補助関数・状態型に合わない。
- **coder role は 2 つの出力形に分ける。**
  - **LLM×C++**: `.claude/agents/coder-v4-autonomous-policy.md` を新設する。
    - fresh・tool なし・構造化出力とし、出力は `implementation` (namespace 本体の C++) と `justification` の 2 つ。
    - 入力は次のとおり。
      - 固定の接続仕様 (§2.5・§2.7)
      - 自系列の履歴。候補本文・結果分類・reject コード・verifier の構造化 digest・critic 診断 (既存 K2 射影の兄弟 key) を、データとして渡す。
  - **LLM×IR**: 同じ入力で、出力を IR JSON (§5 の IR schema) にする。この出力は、非 LLM の IR arm と同じ IR admission と trusted renderer を通る。LLM×C++ の経路とは区別する。
  - どちらも **justification は台帳に残すが、critic と次の coder には渡さない。** 自由文が探索条件を誘導する経路を作らないためである。
  - 候補本文はコメントを持てない (DiffQuarantine が拒否する)。
- **auditor** は LLM 由来の候補 (LLM×C++ と LLM×IR) に、digest 照合 gate と目視を行う。LLM が出した IR でも auditor gate を通すのは、sort 軸の前例 (`p3_s4_loop_sort.py` の auditor gate) に倣う。
  - 非 LLM の IR 候補 (trusted renderer 出力) には auditor 段を省く。ただし公平性の目視 (§3.4) は、全系列の endpoint 候補と勝ち候補に課す。
  - 目録への追加案: 型 22 名前解決の乗っ取り / 23 マクロ識別子による判別 / 24 保存域の迂回 / 25 メモリ安全の迂回 / 26 hook 別の空振り。型 17〜21 の免除段落は「sort IR と、この軸の機械 IR 候補に限る」と改める。逐語は `verbatim/s3-auditor.md` の「role 定義の更新案」。その案にある T3 必須・候補ごとの計数必須の文言は、本設計の §3.4 (見送り) に合わせて直してから承認を求める。
  - **`.claude/agents/` の変更 (coder 新設・auditor 改訂) はユーザー明示承認が要る。** E 段の着手条件とし、本 wave では承認を得たことにしない。
- **build admission。** class 名は `build_admission.py:95-104`、source evidence と receipt・CLI authority からの導出は :656-701 にある。
  - 非 LLM の IR renderer の出力は、generator receipt により `MACHINE_GENERATED` とする。
  - LLM×C++・LLM×IR の候補と、Codex が書いた手書き対照は、CLI opt-in 付きの `CODER_AUTHORED` とする。Codex が書いたものを `HUMAN_REVIEWED` にしない。

## 5. 共通表現と公平な比較 (返却物 4)

- **材料化形式** は「領域の C++ 本文」である。候補 identity は genome flags + 骨格 / PIN + 材料化された全 source の source_digest。
  - 同じ本文でも flags や骨格が違えば別候補になる。
  - preprocess hash は意味的同値の判定器ではない。
- **型付き有限 IR** (段 2 草稿 §4.2 の案を基に固定)。
  - 入力: abort 要因、lock の試行番号、状態の scalar。
  - 状態: 最大 4 field。
  - 式: 定数・比較・条件式・min / max・飽和加減算・有界 shift、深さ ≤ 4、node ≤ 64。
  - 出力: 待機量、lock の action + 待機量、次の状態。
  - 停止性と算術安全を構成で保証する。
  - 描画規則は決定的で、出力は policy-C++ v1 の部分集合に入る。
  - この値は試走用の契約値で、較正済みではない。
- **random / sweep / 非 LLM 進化** は IR の上で型を保って動く (進化は型を保つ subtree 置換)。任意の C++ 文字列をランダム生成しない (オンボーディング §3-D)。
  - BO は repo に既存の実装も依存宣言も無い (レンズ B の静的検索)。最初の結果には必須にせず、後段 (差分分析 P2) へ送る。
- **2 つの比較を分ける。**
  - 比較 A (同じ IR): 非 LLM×IR と LLM×IR。探索法の差を言える。LLM×IR は §4 の IR JSON 出力形で、非 LLM の arm と同じ IR admission・trusted renderer を通る。
  - 比較 B (空間拡張): LLM×C++ (policy-C++ v1) と IR の各 arm。表現と探索法を合わせた差であり、純粋な探索法の優劣とは言わない。
  - 最小の arm は、非 LLM×IR・LLM×IR・LLM×C++ の 3 つ。
- **共通条件。** 評価数 B、提案数 A、初期候補、観測、workload、verify、rep、停止、故障 retry、endpoint 再評価を揃える。
  - 前処理の拒否は A だけを消費し、pipeline へ投入した候補は B を消費する。compile / 正しさの失敗も B から除かない。B-5 の A/B 分離 (`b5_generator_contrast.py`) を踏襲する。
  - ただし B-5 の値文法・3 arm (:53)・slot schema・値による endpoint 同一性は、新しい候補 identity へ置き換える必要がある。
- **初期候補。**
  - exact reference: stock、元 flags の `p2_2_flag_opt` (`B0-L-W0`、`output/s1-freeze/known_axes_freeze.json:92/318`)、調整済み静的 backoff を元の適用方法で再評価する。
  - 新骨格内の seed: 待機 0 + 即 abort、静的 5 µs / 10 µs。
  - 両者を同一 identity と偽らない。
  - 既知最良を全 arm に見せる比較は、「既知結果を条件とする探索」と明記する。D 段の偵察の順位・勝ちコードは LLM に渡さない (オンボーディング §3-D の firewall)。

## 6. 試走の node 時間と LLM 時間の見積り (返却物 5、投入しない)

**出所。**
- B-5 試走: `output/insights/2026-09-20/t2797-b5-contrast/README.md` §6.3 / §8.2 (write-heavy 1M / 48 threads / 3 秒 / 5 rep)。
- 受入全走: 直前の wave (`dev-wave-wave-startup-cost`) の受入 1 回。job dir の `acceptance-final2-1.started.txt` / `.finished.txt` が 17:16:22 → 17:39:05 (22.7 分)、shard 数 3。

| 定数 | 値 | 出所の種類 |
|---|---|---|
| 1 session の固有費 | 217〜509 秒、中央値 498 秒 (53 session。lock 待ちの推定を差し引いた値を含む。直接測った lock 待ちなしの 7 session は 499〜510 秒) | 実測 |
| 予算換算の単価 | 510 秒 | 同 §8.2 の換算値。新軸の上限ではない |
| LLM 1 巡 | 10〜13 分 (critic 4〜5 分・planner 約 1 分・coder 約 1 分・親の処理) | 実測 (旧運用) |
| 共有 lock 待ち | subprocess wall 53,805 秒の 59% | 実測からの推定 |
| 受入全走 1 回 | 3 shard × 22.7 分 = 1.14 node 時間 | 前 wave の実績 1 回。3 shard が各々 1 ノードを全区間占めたと仮定した換算 (上限ではない) |

**以下は旧単価 (217 秒 / 510 秒) によるシナリオ換算であり、上下限ではない。** 新しい軸では単価を変えうる要因が未測定である。
- 関数の量と最適化による build 時間
- lock 方策による abort 数と成功数
- trace のイベント量と verify の時間・メモリ (旧試走でも performance verify の 1 rep は 34〜91 秒と 2.7 倍違った)
- auditor の所要
- 長いコード生成の所要

C 段の負例・変異・probe は verify で止まる走が多く、実費は 1 session より短い見込みである (未測定)。表では 1 session として換算した。

| 段 | 規模案 | node 時間 (換算) | LLM 時間 (換算) | 確認 |
|---|---|---:|---:|---|
| C 段の生死確認 | 手書き方策 3 + 対照 3 = 6 session | 0.36〜0.85 h | なし | 下の合計で判定 |
| C 段の骨格負例 | 3 負例 × 2 方策 = 6 走 | 0.36〜0.85 h | なし | 同上 |
| C 段の機構変異・probe | clamp 削除 1・再読込削除 1・上限削除 1・prefix unlock 省略 1・hook 配線解除 3・要因誤記録 1・probe 正例 1 = 9 走 | 0.54〜1.28 h | なし | 同上 |
| C 段の受入全走 | 1 回 | 1.14 h | なし | 同上 |
| **C 段の合計** | 21 走 (4,557〜10,710 秒) + 受入 | **2.41〜4.12 h** (丸めた受入 1.14 h を足した値。受入を 1,363 秒のまま足すと 2.40〜4.11 h) | | **2 node 時間以上なので投入前に確認** |
| D 段の IR 偵察 | IR 16 点 + 対照 3 = 19 session (まず write-heavy) | 1.15〜2.69 h | なし | 2 h 以上になりうるので確認 |
| 最初の比較試走 | 3 arm × 3 独立系列 × (初期 3 + 探索 8 + endpoint 5) + block 対照 5 = 149 session | 8.98〜21.1 h | LLM 2 arm × 3 系列 × 8 巡 = 48 巡、8.0〜10.4 h + auditor | 確認対象 |
| 最小の LLM×C++ 1 系列 (ComSys 向けの最初の結果候補) | 初期 3 + 探索 8 + endpoint 5 = 16 session | 0.96〜2.27 h | 8 巡 1.3〜1.7 h | 上側で 2 h 以上になるので確認 |

- 構文検査器・単独 TU compile・UBSan harness の試験は login で秒単位で、node 時間に数えない。
- 判定の単位は、1 タスク (1 本の実験、または 1 本の wave) の job 合計である。job を分割して 2 時間未満に見せない。
- LLM の応答を待つ間もノードを確保する運用なら、その待ちも node 時間に入る。B-5 試走では handshake 待ちが約 7,360 秒あった。
- 並列 job で流すには、node-local の bench lock (D2209 は B-5 mode 限定) が要る。これが無いと、共有 lock で直列化される。
- ComSys 2026 (原稿 10/30) へ向けて最初に取れる結果の候補は、D 段の生死確認の後の小さな LLM×C++ 系列である。報告する値は次のとおり。
  - 提案数・構文検査通過数・build 到達数・certified 数・reject の内訳
  - build / verify / 生成の時間
  - stock・既知最良・静的 backoff に対する endpoint
  - 探索法の優劣 (比較 A / B) はこの結果では主張しない。

## 7. 軸定義シート (オンボーディング §2)

| 欄 | 記入 |
|---|---|
| 軸名 | `silo-function-policy` |
| 変異型 | 関数群 + 複数 hook + worker 内状態 (§4 の既存 2 型に収まらない第 3 型、§8) |
| SOURCE_REL | `cc/silo/transaction.cc` (既に `EVOLVE_BLOCK_SOURCES` / `ALLOWLIST` 内、`source_digest.py:85-100`)。ALLOWLIST 拡張は不要 |
| マーカー ID | `silo-function-policy` |
| hole の位置と骨格 | include 列 (T:1-9) の後の名前空間 scope の単一領域 (namespace の外枠は marker 外)、空の stock 枝。呼出し点 (abort T:47、lockWriteSet の内側ループ T:158-184、commit T:706-713、要因記録 7 点、begin) は marker の外 |
| 構文契約 | §2.7 policy-C++ v1 |
| stock の動作 | `BACK_OFF` 下の Cicada 適応 backoff (`include/backoff.hh:44-108`)、no-wait の lock 競合 (T:160-164) |
| フラグ名 | `CCBENCH_SILO_POLICY_VARIANT` → `SILO_POLICY_VARIANT` (on/off、0 = stock)。軸 ON は `BACK_OFF=1`・no-wait 固定を要求 |
| 壊しうる不変条件 | 契約違反による CC 状態への干渉・UB (契約で構造的に排除、残りは検査器の誤り)、lock 保持時間と convoy、worker 間の進行の偏り (公平性)、要因記録の取り違え。骨格の誤配線なら lock の解放漏れ・取得不足 |
| verifier の死角 | 少数 worker の飢餓・tail latency・worker 間の優先偏り・要因の誤記録は G2 に現れない。非空の trace は全 worker の進行の証明ではない。trace の遅延と状態の温まり方の差で、verify と perf の分岐が変わりうる |
| reward hack 仮説 | 事象の統計から legacy verify と perf を判別する (型 3)、自前の commit / abort 計数を fitness の代理にする (型 12)、単調に増えるだけの状態で worker を恒久的に駐車して見かけの throughput を稼ぐ (型 15)、履歴で条件づけた lock 枝が verify 中に発火しない (型 4)。名前解決の乗っ取り (型 22 案) とマクロ識別子による判別 (型 23 案) は受理契約と単独 TU compile で閉じる |
| positive control 設計 | §3.3 (骨格負例と機構の変異と契約負例を分ける) |
| 偵察の列挙空間 | §5 の型付き有限 IR (停止性・算術安全を構成で保証) |
| 感度を持つ workload | write-heavy を初手、balanced を次段、read-heavy は待機コストの対照に残す (新規は未測定) |
| 計測動作点 | 1M records / 48 threads / skew 0.9 / 3 秒 / 5 rep (B-5 と同じ)。新骨格での床値の適用確認は未了 |

## 8. オンボーディング §4 の第 3 列の案

`docs/axis-onboarding.md` §4 の表に次の列を足す案である。§4 は改訂を D41 水準のレビューに掛けると定めている。本 wave の 3 レンズはこの案を段 2 草稿 §7 として攻撃した。手順書本体への反映は、C 前の小さな docs wave で行う。その際、planner 再利用を前提とする段階 E の記述 (`axis-onboarding.md` の段階 E「coder 定義」の planner-v4 再利用) に、この軸の例外を合わせる。

| 論点 | 関数群・複数 hook・状態の軸 (function-policy が型) |
|---|---|
| フラグ設計 | on/off。型・状態・呼出し点・要因記録を全て軸 OFF で消す。軸 ON が前提とする他 flag は `#error` で固定する |
| coder 出力スキーマ | C++ 版は単一領域の implementation (value なし)、IR 版は IR JSON。どちらも justification は還流しない |
| pre-build 整合チェック | 単一領域の検疫 + effect gate + 型付きの構文検査 + 単独 TU compile + 実 diff に束縛した auditor gate (LLM 由来の候補) |
| 安全性の問診 | UB (式の型・初期化・shift・除算)・状態の寿命・停止・呼出し graph・外部参照・代替綴り・lock 保持時間・公平性。IR の保証を自由 C++ に拡張しない |
| 偵察の列挙 | 構成的に安全な型付き IR の部分空間。部分空間の結果と全空間の生死を区別する |
| auditor の役 | 関数・状態と固定骨格の境界、代理、公平性、検証条件への依存を監査。非 LLM の機械 IR 候補は auditor 段を省くが、endpoint 候補と勝ち候補の公平性目視は課す |
| marker と呼出し点 | marker は 1、呼出し点は複数。呼出し点と namespace の外枠を hole にしない |
| 状態 | 骨格が所有する 1 個を参照で渡す。hole は書換え可能な持続状態 (静的・thread 記憶域の可変変数) を定義しない (namespace の constexpr 定数は可) |
| 実験主張 | IR 内の探索法比較と C++ 空間拡張の比較を分けて報告する |

## 9. 条件付き採用の必須条件

実装着手前 (C 段の前) に固定するもの:
1. §2.7 の受理契約を、producer (coder role の接続仕様、C++ 版と IR 版) と consumer (型付きの構文検査・単独 TU compile) の両側で一致させる。字句 (代替綴り・digraph)、名前解決、式の型の規則、初期化子の自己参照禁止、return の位置、switch の閉じ方を含む。
2. §2.4〜2.6 の骨格仕様を固定する。
   - namespace の外枠を marker 外に置くこと
   - 別 namespace と完全修飾、noipa の wrapper
   - 組込型の action 判定
   - lock の周回上限の位置と CAS 失敗の計数
   - 待機後の再読込と prefix unlock
   - 要因の 7 点写像
   - 軸 ON での `BACK_OFF`・no-wait flag の `#error`
   - api header と実 TU の骨格型を同じ正本から作ること
3. §3.3 の正例・負例・検査器の自己試験を、位置・期待する検査・期待 verdict とともに事前登録する。
4. C 段のタスク合計の node 時間を見積もり、投入前にユーザー確認を取る (§6 の換算は 2.41〜4.12 h)。
5. 手順書 §4 の第 3 列と planner 例外の反映 (C 前の docs wave)。

C 段の出口で確認するもの:
6. 軸 OFF の inert identity、軸 ON の honest identity、include 一致、diff-of-diffs を実測する。
7. 既存 3 負例を軸 ON の経路で 2 方策の下で再走し、期待 verdict と完全一致させる。
8. probe build で、3 つの hook (abort・lock・成功通知) の発火、上限、再読込、prefix unlock、要因記録を確認する。
9. 構文検査と単独 TU compile の契約負例がすべて赤になり、検査段ごとの自己試験が働くことを確認する。UBSan harness を 1 回回す。

D 段・E 段の前に満たすもの:
10. D 段の偵察と比較試走は、それぞれ投入前に node 時間の見積りでユーザー確認を取る。
11. `.claude/agents/` の変更 (coder 新設・auditor 改訂) の具体差分にユーザー明示承認を得る (E 段)。
12. E 段と F 段は別セッションにする (新設 agent は同一セッションで spawn できない)。

## 10. 研究主張の射程と残存リスク

- **v1 で言えること。**
  - LLM が書いた関数の有効率 (構文・build・liveness・正しさ)
  - reject の分類
  - 生成・build・検証の費用
  - 同じ IR 上の探索法比較
  - C++ 空間拡張の効果
- **v1 で言えないこと。**
  - 「LLM が壊した CC 論理を verifier が捕らえた」こと
  - 任意 C++ の安全
  - 全実行の正しさ
  - 公平性
  - verify と perf で同じ分岐を踏んだこと
- 安全についての文言 (レンズ A): メモリ安全・外部干渉なし・契約適合の方策が正常に返る限り、方策の選択は固定骨格の直列化可能性条件を弱めない。任意 C++ の適合性、全実行の正しさ、停止性、公平性を構成上保証するものではない。certified は有限の観測履歴についての判定である。
- **残存リスク。**
  - 構文検査器と単独 TU compile の実装誤り。
  - worker 内状態による公平性の犠牲 (目視以外の観測点なし)。
  - trace の遅延と状態の温まり方による verify / perf の分岐差。
  - 上限値 (1000 µs / 50 µs / 32 周回) の妥当性。
- TPC-C への適用は範囲外である。pipeline は YCSB 以外を検証前に拒否する。TPC-C の認定は別 wave の設計で扱う。

## 11. 経緯と逐語

| 段 | 内容 | 逐語 |
|---|---|---|
| 1 | 親 brief (暫定裁定 P1〜P8) | `verbatim/brief.md` |
| 2 | codex (read-only) の設計草稿。P4 を反証、P2 の安全主張を撤回、P5 を縮小、比較 A / B を分離 | `verbatim/s2-plan.md` |
| 3 | レンズ A (正しさ境界・報酬ハック)、レンズ B (整合・過剰削除・見積り)、auditor role。3 本とも adopt_with_conditions | `verbatim/s3-consult-A.md`、`verbatim/s3-consult-B.md`、`verbatim/s3-auditor.md` |
| 4 | 親の裁定 (所見 27 件の real / refuted と採否、プラン v2) | `verbatim/s4-ruling.md` |
| 7 (1 巡目) | 焦点再レビュー: codex review (NO-GO、must-fix 8)、auditor 再確認 (adopt_with_conditions 維持、must-fix 2) → 親の裁定と訂正 | `verbatim/s7-review-A.md`、`verbatim/s7-auditor-focus.md`、`verbatim/s7-focus-ruling-1.md` |
| 7 (2 巡目) | 焦点再レビュー: codex focus (NO-GO、closed 18 / partial 5、must-fix 2) → 親の裁定と訂正 | `verbatim/s7-focus-2.md`、`verbatim/s7-focus-ruling-2.md` |
| 7 (3 巡目、最終) | 焦点再レビュー: codex focus (NO-GO、2 巡目の 5 件は全て closed、新規 must-fix 1) → 3 巡上限により親が裁定して閉鎖 | `verbatim/s7-focus-3.md`、`verbatim/s7-focus-ruling-3.md` |

- 段 2・3・7 のプロンプトは wave の job dir に置いた (repo 外)。
- 段 4 で中心設計を 2 点変えた。
  - 決定 4 = 受理契約の具体化
  - 決定 5 = 状態の射程
- 変えた版を同じレンズで確認した結果と訂正は §12 に書く。

## 12. 検査の記録

- **焦点再レビュー 1 巡目 (段 4 後の版)。**
  - codex review は NO-GO。must-fix 8 件で、主な内容は次のとおり。
    - bool の昇格による signed 算術
    - 初期化子の自己参照
    - hole 境界と許可文法の不一致
    - 成功通知 hook の検査漏れ
    - LLM×IR の経路
    - 状態射程の帰属
    - 単独 TU の自己試験
    - C 段の見積り項目
  - auditor 再確認は adopt_with_conditions を維持した。must-fix は R1 (signed 算術・自己初期化・return 欠落) と R2 (代替綴り・digraph) の 2 件、should は R3〜R7 の 5 件。
  - 親は全件を real として採用し、本稿の §2.1・§2.4〜2.7・§3.1〜3.4・§4〜§9 を訂正した。各所見と訂正の対応は `verbatim/s7-focus-ruling-1.md`。
  - codex review は、段 4 の 27 件の閉包表・引用行 (全件一致、補足 3 件)・§6 の掛け算 (全件一致) を静的に確認した。
- **焦点再レビュー 2 巡目 (1 巡目の訂正後の版)。**
  - codex focus は NO-GO。1 巡目の 23 項目のうち closed 18、partial 5。1 巡目の反例 (bool の昇格・自己初期化・return 欠落・代替綴り) は閉じたと判定した。
  - must-fix は 2 件。
    - 型表の `/ %` の結果型が C++17 の通常算術変換と不一致で、literal の型と `unsigned long` / `unsigned long long` の区別も未固定だった。
    - namespace scope の `constexpr` の記憶域が状態の規則と衝突し、宣言の型集合・呼出し文・メンバ読出しの記法も未確定だった。
  - nit は 3 件 (字句段の自己試験、帰属の一括表現、C 段合計の丸め)。
  - 親は 5 件とも採用し、§2.5・§2.7 (型の体系を追加、型表を書き直し)・§3.3・§6・§8 と fragment 決定 4・5 を訂正した。対応は `verbatim/s7-focus-ruling-2.md`。
  - 引用行 7 件・fragment の書式・§6 の全数値 (受入の実時刻 1,363 秒を含む) は一致と判定した。
- **焦点再レビュー 3 巡目 (最終)。**
  - codex focus は、2 巡目の 5 件をすべて closed と判定した。一方で新たな must-fix を 1 件挙げ、NO-GO とした。代入式を部分式に埋め込めるので、同じ状態を別名の参照で 2 回書く順序づけられない書込みから、UB を作れるという指摘である。
  - DW-O16 の 3 巡上限に達したので 4 巡目は回さず、親が裁定して閉じた。
    - 代入・複合代入を独立した文に限り、`++` `--`・カンマ演算子の禁止を明記した。
    - 式の中の自前関数の呼出しどうしは C++17 では不定順序であり、順序なしではないので UB にならない。これを親が検算した。
    - nit 2 件 (literal の 64 bit 上限の説明、初期化と return の変換規則) も訂正した。
    - 対応は `verbatim/s7-focus-ruling-3.md`。
- 受入全走は、この記録 commit の後に走らせる。その結果と land の結果は、本稿ではなく次の記録で扱う。
