結論は「write set の格納形式」を第一候補として条件付き採用です。親の (P1) の選択自体は支持しますが、その根拠の一部、(P2) の安全性、G1 の生死確認には修正が必要です。現状では段階 C 着手条件を満たしていません。(P3) の「本 wave は実装なし」は支持します。

## 第 1 部　下位軸の比較と第一候補の選定

### 親 brief との食い違い

1. G1 は実 TU の include 閉包を再現していません。

   [transaction.hh:9](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/include/transaction.hh:9) が `backoff.hh` を取り込み、[backoff.hh:14](/home/SFC/tanab/github/izanagi/external/ccbench/include/backoff.hh:14) が大域で `using namespace std;` を宣言しています。したがって現行 TU の [transaction.cc:408](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/transaction.cc:408) の非修飾 `sort` は、custom iterator でも通常の非修飾 lookup から `std::sort` に到達します。

   よって「custom container を成立させるには `std::sort` への修飾が必須」という G1 は不成立です。修飾は衛生上望ましくても、現コード上の必須骨格変更ではありません。

2. M11 の「vector では 1 要素 skip」は言語仕様上の保証ではありません。

   [transaction.cc:124](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/transaction.cc:124)〜127 は `erase(itr)` 後に無効化済み iterator を `++itr` する UB です。vector の特定実装で skip に見える可能性はありますが、保証できません。deque 等への交換で意味が変わる以前に、現行 vector も正しい意味論の基準にはできません。

3. G2 が示すのは簡約した 37 use site の構文成立だけです。M11、move-only 要素の lifetime、iterator/reference invalidation、実 TU の依存関係は証明していません。

### 3 候補の比較

| 候補 | hole 候補と現行編集面 | 機械列挙性 | M7 動作点での機序 |
|---|---|---|---|
| 格納形式 | [transaction.hh:35](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/include/transaction.hh:35) と 36 の間に `WriteSet` 完全型を置く。現行 `EVOLVE_BLOCK_SOURCES` 外 | `vector/deque/容量値` の選択に狭めれば再び有限探索。完全な container 実装を合成対象にすれば、小さい値グリッドへは還元できない | 約 5 要素では allocation 削減は薄い。stock vector は [transaction.cc:689](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/transaction.cc:689) の `clear()` 後も capacity を保持する。一方、要素の連続性、TxExecutor 内 inline 領域、sort 時の move、linear search、hot/cold field の接触量には地形を持ちうる。未実測 |
| 検証順序 | [transaction.cc:450](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/transaction.cc:450) の read-set loop の直前に「全要素の順序 view」だけを作る hole。現行編集面内。検証本体 451〜475 は固定必須 | 約 5 要素なら実現順序は最大 `5! = 120`。動的 priority policy を許しても、短い comparator/順位式の探索へ戻りやすい | abort する transaction では stale/locked element を早く見つける余地があるが、成功 transaction は全要素を検証する。sort/view 構築コストが数個の load 削減を上回る可能性も高い |
| ロック粒度の表現 | 表面的には [transaction.cc:145](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/transaction.cc:145) の `lockWriteSet()`。ただし真の粒度変更は unlock 352〜381、read validation 450〜475、writePhase 614〜674、さらに [tuple.hh:12](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/include/tuple.hh:12)〜36 に波及する。完全な軸は編集面外を含む | 現 transaction 内の 5 要素を group 化するだけなら set partition は Bell 数 `B5 = 52` で、容易に列挙可能。global bucket/range lock まで許せば非列挙的になるが、単一 hole では正しさを隔離できない | 少数 CAS の削減と false conflict 増加のトレードオフはありうる。ただし stock は tuple の cache-line 内 tidword lock であり、別 lock 表現の共有状態・read 側整合まで必要 |

裁定は「格納形式」です。(P1) の第一候補は支持します。

ただし「これを解けばロック粒度も同じ機構に載る」という理由は支持しません。検証順序には型 hole の仕組みを再利用できますが、真のロック粒度は tuple lock の読み書き全体へ波及し、単なる container alias では表現できません。

## 第 2 部　軸定義シート

- 軸名: `silo-writeset-storage`

- 変異型: `データ構造／型選択`。§4 に追加する第 3 型。コードとして配送されても、意味上は既存の「コード片軸」へ分類しない。

- SOURCE_REL: `cc/silo/include/transaction.hh`

  現行 [source_digest.py:68](/home/SFC/tanab/github/izanagi/orchestrator/campaign/source_digest.py:68) の外。

- マーカー ID: `silo-writeset-storage`

- hole の位置と骨格:

  [transaction.hh:35](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/include/transaction.hh:35) の `read_set_` 後、現行 36 行の `write_set_` 前。前提として trusted baseline に `WriteSet` alias が導入済みであること。

  ```cpp
  #ifndef WRITESET_STORAGE_VARIANT
  #error "WRITESET_STORAGE_VARIANT must be defined"
  #endif
  // EVOLVE-BLOCK-BEGIN silo-writeset-storage
  #if WRITESET_STORAGE_VARIANT
    class WriteSet {
      /* coder が完全実装を返す唯一の領域 */
    };
  #else
    using WriteSet = std::vector<WriteElement<Tuple>>;
  #endif
  // EVOLVE-BLOCK-END silo-writeset-storage
    WriteSet write_set_;
  ```

  stock branch の preprocessed text を baseline と一致させるため、alias 化などの固定 scaffold は template patch だけに混ぜず、新しい pinned baseline に先行して置く。

- 構文契約:

  - `WriteSet` は default constructible/destructible。
  - `WriteElement<Tuple>` の copy を要求せず、move construction／move assignment／destructionを正しく扱う。[silo_op_element.hh:39](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/include/silo_op_element.hh:39)〜80 の `unique_ptr` 所有権を二重解放・漏洩しない。
  - public `iterator` は random-access iterator で、`operator*` が `WriteElement<Tuple>&`、`operator->` が同要素を指す。
  - `begin/end/size/clear/emplace_back/erase(iterator)`、range-for、`std::sort`、prefix end を受ける `unlockWriteSet` を満たす。
  - `clear()` は全 live element をちょうど 1 回破棄する。capacity 方針は変異可能。
  - mutable `static`／`thread_local` 状態、時計、乱数、`thid_`、`Result`、trace 状態を参照しない。`static constexpr` の純粋な型定数は可。
  - default constructor で heap allocation や前計算を行わない。計測開始前への仕事の移動を禁止する。
  - 新規 include、前処理指令、global/function/friend/asm、外側 class/namespace を閉じる token を禁止する。
  - この最後の構造制約を検査する機械 gate は未実装・方式未定。

- stock の動作:

  `std::vector<WriteElement<Tuple>>` の insertion-order AoS。validation 前に [transaction.cc:408](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/transaction.cc:408) で storage/key 順に sort し、その順で lock／write／unlock する。`clear()` は capacity を保持する。

  ただし現行 [transaction.cc:124](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/transaction.cc:124)〜127 は UB なので、これを修復した新 pinned baseline を stock の意味論とする。現行挙動を container 契約として模倣してはならない。

- フラグ名: `CCBENCH_WRITESET_STORAGE_VARIANT`、ソース側 `WRITESET_STORAGE_VARIANT`。`0=stock`、`1=合成型`。

- 壊しうる不変条件:

  - 成功した insert/delete/update と write-set 要素の 1 対 1 対応。
  - iteration が `size()` 個の同一 logical element を欠落・重複なく返すこと。
  - move-only payload、key、op、rcdptr の同一性と lifetime。
  - sort 前後および partial unlock の prefix 同一性。
  - 全 non-INSERT write が lock 済みで writePhase に到達すること。
  - pointer/reference/iterator の有効期間。
  - `erase` 後に無効 iterator を利用しないこと。M11 は現時点でこの不変条件を既に破っている。
  - container が transaction 間・worker 間の共有状態を持たないこと。
  - stock/perf と trace build の意味論が一致すること。

- verifier の死角:

  - C/R/W trace は [transaction.cc:594](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/transaction.cc:594)〜607 で、その時点で container に残った要素から生成される。container が要素を先に落とすと、意図された操作自体が trace に現れない。
  - lock coverage も [transaction.cc:614](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/transaction.cc:614)〜623 で同じ container を再走査するため、欠落要素には自己整合的に沈黙する。
  - 既存 permutation 検査 [transaction.cc:403](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/transaction.cc:403)〜435 は sort 直前後だけを見る。emplace/erase 時点の欠落、同じ rcdptr を保った key/op/body 改変、偽の `size()`／iterator は見ない。
  - verifier の Integrity は現状 X/P までで、[model.py:126](/home/SFC/tanab/github/izanagi/orchestrator/verifier/model.py:126)〜142 に storage conservation／lifetime の欄がない。
  - M11 の invalid iterator は crash/hang/anomaly が偶然顕在化しなければ見えない。
  - ASan が検出しない論理的な漏洩・重複・仕事の計測前移動は見えない。

- reward hack 仮説:

  - `emplace_back` を無視・重複排除し、lock/write/trace をまとめて減らす。
  - `end()`／iterator／`size()` を偽装し、既存の自己参照型 assert に同じ短い集合だけを見せる。
  - `clear()` で destructor を省略し、短時間 run の throughput と引き換えに leak を先送りする。
  - default constructor で reserve／前計算を済ませる。TxExecutor は [runner.hh:183](/home/SFC/tanab/github/izanagi/external/ccbench/common/runner.hh:183) で start barrier 前に構築され、計測開始は同 294〜297 行なので、正しさを壊さず計測境界を攻撃できる。
  - M11 の UB や container 固有 invalidation を利用し、delete 処理を短絡・省略する。

- positive control 設計:

  - 独立した trace-only logical-write shadow を emplace 点 [transaction.cc:109](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/transaction.cc:109)、137、547 と erase 点 124〜127 で更新し、validation 前に `(storage,key,rcdptr,op)` multiset を container と照合する。新 trace tag／Integrity field 名は未定。
  - broken case A: N 回目の emplace を落とす → conservation 検査だけが赤。
  - broken case B: iterator が先頭を重複し末尾を隠す → multiset 検査が赤。
  - broken case C: move-owned element を二重破棄する → ASan が赤。
  - M11 regression: cancel-previous-write を含む transaction で erase 後 iterator 使用がなく、logical shadow と container が一致。
  - stock control は新 violation 0。既存 legacy+s2 verifier を置き換えない。

- 偵察の列挙空間:

  全空間は意図的に非列挙型であり、有限 grid にしてはならない。D 段で使う bounded representative panel の具体構成は未定。stock、inline/spill、segmented 等の代表層を「生死確認用であって全探索ではない」と凍結する必要があり、未定のまま C へ進めない。

- 感度を持つ workload:

  - 主点: S2 の balanced、高 contention。
  - 感度対照: 同一 thread/tuple/skew の write-heavy。write set が大きくなりやすい。
  - 負け確対照: read-heavy。write-set 格納形式への感度が弱い。
  - exact な set size は乱数と重複 key に依存し、M7 の約 5 は期待値であって固定値ではない。

- 計測動作点:

  [pipeline.py:65](/home/SFC/tanab/github/izanagi/orchestrator/campaign/pipeline.py:65)〜68 の t48／1M／skew 0.9／rr50／rmw=false／max_ope=10。約 5 要素では定常 allocation 差より locality、move、search、sort の差が主機序となる。

  新 pin／新 identity に対する floor 較正は未確認。地形は未実測であり、存在を主張しない。

## 第 3 部　編集面制限の設計

### マーカーと固定 scaffold

- BEGIN/END: [transaction.hh:35](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/include/transaction.hh:35) と現行 36 行の間。
- hole 外の固定変更:

  - [transaction.hh:36](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/include/transaction.hh:36): `WriteSet` alias と alias 型 member。
  - [transaction.hh:140](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/include/transaction.hh:140): `WriteSet::iterator` に統一。
  - [transaction.cc:367](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/transaction.cc:367): 定義側を `TxExecutor::WriteSet::iterator` に統一。
  - [transaction.cc:124](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/transaction.cc:124)〜127: erase 後は直ちに loop を抜け、無効 iterator を増分しない。
  - [Options.cmake:23](/home/SFC/tanab/github/izanagi/external/ccbench/cmake/Options.cmake:23) 後: flag 既定 0。
  - [Options.cmake:67](/home/SFC/tanab/github/izanagi/external/ccbench/cmake/Options.cmake:67) 前: universal definition 配線。
  - `transaction.cc:408` の `std::sort` 修飾は現コード上の必須変更から外す。

固定 alias／M11 修復を template patch だけに入れると、stock branch の preprocessed text が現 pinned HEAD と異なり `src_token="stock"` を維持できません。したがって固定 scaffold は trusted baseline commit と新 pin に置き、template patch はその baseline の alias を stock branch に逐語保存する設計とします。

### 編集面 3 定義

【編集面制限の弱化】

以下へ `cc/silo/include/transaction.hh` を追加します。

- identity 対象: [source_digest.py:68](/home/SFC/tanab/github/izanagi/orchestrator/campaign/source_digest.py:68)
- tracked 改変 allowlist: [source_digest.py:71](/home/SFC/tanab/github/izanagi/orchestrator/campaign/source_digest.py:71)
- write hook の複製定数: [guard_write.py:37](/home/SFC/tanab/github/izanagi/hooks/guard_write.py:37)

これはファイル単位では transaction header 全体を coder-writeable にするため、明確な編集面制限の弱化です。絶対規律 2 に触れる裁定事項として人間承認が必要です。

含意は次のとおりです。

- `source_digest.compute()` は [source_digest.py:187](/home/SFC/tanab/github/izanagi/orchestrator/campaign/source_digest.py:187)〜194 で header を digest の第 3 part として含む。既存 non-stock variant の digest／variant ID は再計算時に変わる。
- stock は新 pin 上で current digest と baseline が一致する場合だけ [source_digest.py:287](/home/SFC/tanab/github/izanagi/orchestrator/campaign/source_digest.py:287)〜296 により `"stock"` を保つ。
- 新 pin は [ident.py:76](/home/SFC/tanab/github/izanagi/orchestrator/campaign/ident.py:76)〜103 の campaign identity も変える。旧 certified record を新 campaign の証拠として暗黙再利用してはならない。
- [test_hooks.py:262](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_hooks.py:262)〜264 は 2 個の `EVOLVE_BLOCK_SOURCES` の一致だけを検査する。`ALLOWLIST` との包含／一致は現在未検査なので、3 定義全体の drift gate が必要。
- [guard_write.py:98](/home/SFC/tanab/github/izanagi/hooks/guard_write.py:98)〜111 は designated file 内の行位置を見ず、header 全体を許可する。また Codex hook は [hooks/README.md:15](/home/SFC/tanab/github/izanagi/hooks/README.md:15)〜18 のとおり未配線。hook 単独を hole 防壁と数えてはならない。

### HEAD 固定 include の下での型空間

[source_digest.py:197](/home/SFC/tanab/github/izanagi/orchestrator/campaign/source_digest.py:197)〜216 により、header の include 行は pinned HEAD と完全一致が必要です。

利用可能なのは [transaction.hh:3](/home/SFC/tanab/github/izanagi/external/ccbench/cc/silo/include/transaction.hh:3)〜20 の明示 include と、その固定された推移閉包から到達する宣言だけです。

- 明示的に依存できる主な標準型は `vector`、`set`、`string_view`。
- `deque`、`unordered_map`、`unique_ptr` 等は現 TU で推移的に到達していますが、別 header の偶然の include に依存するため、構文契約で無条件に新規利用可能とは扱わない。
- Boost／Abseil 等の外部 container や新しい標準 header は使えない。
- self-contained custom container は可能性があるが、実 TU で未確認。
- 新 include が必要なら variant hole には足さず、別の trusted baseline／信頼境界改訂として B へ差し戻す。

### 単一 marker で足りるか

物理的な変異位置としては単一 marker で足ります。可変物を `transaction.hh` 内の一つの完全型へ集約し、全 consumer は固定 scaffold にできるため、複数 marker 化は不要です。

ただし「単一 marker だけで安全」は誤りです。

[diff_quarantine.py:459](/home/SFC/tanab/github/izanagi/orchestrator/campaign/diff_quarantine.py:459)〜493 が機械拒否するのは前処理指令、marker、コメント delimiter、line splice までです。任意の型定義に必要な `{}` を許すと、coder が `};` で外側 class を閉じ、同じ物理 hole 内で global/function を定義する意味的逸脱は現行 gate では止まりません。同ファイルの 14〜20 行も text gate を C++ 意味論の完全な防壁にしないと明記しています。

したがって必要なのは複数 marker ではなく、実 diff から得た構文木／同等の構造表現について「変更された宣言が固定 `WriteSet` 型の内部だけ」を検証する、data-structure 固有の fails-closed shape gate です。方式は未定であり、これがない現状では C に進めません。

### hole 外逸脱を止める現行層と不足

1. 既存 coder は [coder-v4-autonomous-sort.md:4](/home/SFC/tanab/github/izanagi/.claude/agents/coder-v4-autonomous-sort.md:4) と 23〜26 行のとおり tools なしで、文字列しか返さない。

2. [p3_s4_loop.py:141](/home/SFC/tanab/github/izanagi/orchestrator/campaign/p3_s4_loop.py:141)〜151 の `render_hole()` は marker 内行だけを置換する。

3. [diff_quarantine.py:392](/home/SFC/tanab/github/izanagi/orchestrator/campaign/diff_quarantine.py:392)〜510 は hole 外削除・挿入、別ファイル、frame 改変を reject する。

4. 呼び手は [p3_s4_loop.py:640](/home/SFC/tanab/github/izanagi/orchestrator/campaign/p3_s4_loop.py:640)〜650 で `passed=False` なら build へ進まない。

5. [patchharness.py:162](/home/SFC/tanab/github/izanagi/orchestrator/campaign/patchharness.py:162)〜189 は適用前の tracked dirty tree を拒否し、[source_digest.py:299](/home/SFC/tanab/github/izanagi/orchestrator/campaign/source_digest.py:299)〜335 は別 allowlist file への逸脱を拒否する。

6. 一方、designated header 内への直接 edit と、物理 hole 内からの C++ scope escape は上記だけでは閉じません。前者は tool-less 入力経路＋pinned-clean、後者は新 shape gate が必要です。`source_digest` は変更を identity に載せますが、意味的逸脱そのものを拒否する防壁ではありません。

## 第 4 部　axis-onboarding テンプレ改訂の骨子

既存 2 列は現行記述を変えず、第 3 列だけを追加します。

| 論点 | スカラー値軸 (backoff が型) | コード片軸 (sort が型) | データ構造／型選択軸 |
|---|---|---|---|
| フラグ設計 | 数値 sentinel (`BACKOFF_FIXED`) | on/off (`SORT_VARIANT`) | on/off。stock branch は pinned baseline の完全型／alias を逐語保存し、合成 branch は固定名の完全型を供給 |
| coder 出力スキーマ | `value` + 実装 literal | 実装のみ (`value` なし) | 実装のみ (`value` なし)。型名・manifest・安全 verdict を coder 自己申告にせず、型名は骨格固定、digest／contract 結果は harness が導出 |
| pre-build 整合チェック | `assert_value_literal_consistent` (値と literal の機械照合) | **auditor 機械 gate** — `auditor.diff_digest` (sha256) を proposal 必須フィールドにし、driver が実 diff の digest と機械照合。不一致 = `AuditorGateFailure` で即停止。「宣言止まり」(照合なしの verdict 参照) は fail-open であり不可 (D43) | 実 diff digest 照合 + 物理 DiffQuarantine + 完全型 shape gate + container concept/law gate。欠落・解析不能・未知結果は build 前に停止 |
| 安全性の問診 | 値域・オーバーフロー | **言語契約 (UB) を必ず含める** — 非 SWO で introsort が OOB/ハング (write_set 16 要素 = insertion-sort 閾値、D42 条件 1)。「クラッシュしない」は恒真化した安全に見える罠 | object lifetime、move-only ownership、alignment、iterator category/invalidation、erase、allocator、shared mutable state、ABI/layout、operation conservation、計測開始前への仕事移動を必須問診。M11 を独立項目にする |
| 偵察の列挙 | 値グリッド | 構文契約からの構成的列挙 + 安全性の機械検査。ランダム生成は不可 (D46 決定 4) | 全空間の網羅列挙を要求しない。事前凍結した bounded representative panel で生死だけを見る。panel は各点が law gate を通り、網羅性・機械探索優越を主張しない |
| auditor の役 | 目視 (段 4 では未配線) | pre-build 機械 gate + ギャラリー型目視 | diff digest／shape／law の機械 gate に加え、所有権、隠れ共有状態、操作欠落、trace 自己整合型 hack、計測境界移動を敵対レビュー |

## 第 5 部　段階 B 出口の必須条件リスト案

裁定形式は「条件付き採用」。次の全項目が緑になるまで段階 C に着手しません。

1. `DW-B01 review-adopt`

   3 独立レンズの構造化 verdict がすべて `adopt` または `adopt_with_conditions`。未解決 high/critical が 0、journal path と digest が decision に記録されていること。

2. `DW-B02 human-boundary-record`

   `transaction.hh` の編集面追加が「編集面制限の弱化」と明記された人間裁定 record が存在し、B decision がその固定参照を持つこと。

3. `DW-B03 edit-surface-drift`

   2 個の `EVOLVE_BLOCK_SOURCES` が完全一致し、`transaction.hh` を含み、かつ全 source が `ALLOWLIST` の部分集合であることを機械テストする。header 内 direct edit が許可され、隣接 header が拒否される反例も緑であること。

4. `DW-B04 identity-honesty`

   新 pin の stock が `src_token="stock"`、header hole の意味変更が non-stock digest、include 追加／差替えが `RuntimeError`、trace/perf diff-of-diffs が一致すること。旧 non-stock digest／WAL を新 campaign が terminal skip に使わないこと。

5. `DW-B05 baseline-scaffold`

   新 pin 上で alias member、header/source の iterator signature が型一致し、[patchharness.py:162](/home/SFC/tanab/github/izanagi/orchestrator/campaign/patchharness.py:162) の pinned-clean が通ること。M11 の source pattern に `erase(itr)` 後の同 iterator 増分がなく、erase regression が ASan 緑であること。

6. `DW-B06 real-tu-contract`

   簡約 probe ではなく実 `transaction.cc` TU を、凍結した production compiler manifest と C++20／`-Wall -Wextra -Werror` で stock と非 `std` reference container の双方がコンパイルできること。全 `write_set_` use site の機械抽出結果に未分類行が 0 であること。

7. `DW-B07 confinement`

   marker ID の BEGIN/END が各 1 個、`parse_template_file()` が単一 frame を返すこと。hole 外変更、別ファイル、frame 改変、重複 marker、外側 class close、global/static mutable、friend/asm、raw directive の各 broken input が pre-build で reject され、build spy 呼出回数が 0 であること。

8. `DW-B08 container-laws`

   move-only sentinel を使う law harness で emplace、iteration、sort、erase、clear、destruction count、prefix iterator が全 pass。copy 要求、double destruction、短い iterator、偽 size の negative control が各々失敗すること。

9. `DW-B09 conservation-positive-control`

   stock は conservation violation 0。drop-emplace、duplicate/omit iterator、key/op/body corruption の各 broken case が対応する独立 check を赤にし、verifier verdict が `indeterminate` へ倒れること。検査点と broken case の集合が 1 対 1 であること。

10. `DW-B10 reward-boundary`

    container default construction時の heap allocation countが 0、時計・乱数・Result・thread id・mutable global の参照が shape gate で reject されること。計測前 preallocation を行う broken case が赤になること。

11. `DW-B11 representative-panel`

    bounded representative panel の exact source/digest、退化点、stock、選定規則が事前凍結され、全点が `DW-B08` を通ること。「網羅探索」「machine optimum」と解釈するフィールドが schema に存在しないこと。現状は未定なので赤。

12. `DW-B12 template-third-column`

    `axis-onboarding.md` §4 の既存 2 列が byte 不変で第 3 列だけ追加され、docs checker と 3 レンズレビューが緑であること。

現時点では、少なくとも B01、B05、B06、B07、B11 が未達または未確認です。したがって裁定は「条件付き採用、C 着手不可」です。

## 第 6 部　本 wave で実装しうる最小の項目

なし。

本 wave 内で実装しないことにより、既存の certified 選択結果、レポートの受理集合、試行台帳参照を変更しません。逆に編集面・pin・source digest の一部だけを先行変更すると、それらの identity／参照を変えながら安全 gate が未完成になるため、(P3) に反対できる項目はありません。

ファイル変更およびテスト実行は行っておらず、緑は主張していません。