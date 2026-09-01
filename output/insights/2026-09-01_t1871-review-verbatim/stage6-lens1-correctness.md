## 検算した主張

静的検査のみ実施した。ファイル変更・ビルド・テスト実走は行っておらず、緑は主張しない。

- YCSB では `pro_set_` を一度生成した後、同じ procedure を `RETRY` から再試行する。全 abort は `abort()` を通り、成功時だけ `commit()` → `writePhase()` へ進むため、更新順序を正しく固定すれば「同一 YCSB transaction の abort streak」になる。[ycsb.hh:102](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/include/ycsb.hh:102>)、[ycsb.hh:108](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/include/ycsb.hh:108>)、[ycsb.hh:149](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/include/ycsb.hh:149>)、[transaction.cc:706](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:706>)

- worker ごとに一つの `TxExecutor` が worker thread のスタック上に構築されるため、射影された runner/YCSB 経路では file-scope `thread_local` の単一所有は成立する。[runner.hh:172](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/common/runner.hh:172>)、[runner.hh:183](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/common/runner.hh:183>)、[ycsb_silo.cc:33](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/ycsb_silo.cc:33>)

- `validationPhase()` は `lockWriteSet()` を先に実行し、lock 系 abort では read validation に到達しない。従って `kLockConflict` / `kUpdateAbsent` で `b_r` が常に真という分析は正しい。[transaction.cc:437](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:437>)、[transaction.cc:449](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:449>)

- `Tidword` の raw word は epoch/TID/state bit を同居させ、commit TID は `max_rset_`、`max_wset_`、直前 TID、thread-local epoch から生成される。生の `.obj_` を撤回した判断は支持する。[tuple.hh:12](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/include/tuple.hh:12>)、[transaction.cc:557](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:557>)

## must-fix

1. **`unsigned` の retry depth は無限量ではなく、中心論証が成立しない。**

   シートは値域を `ℕ` とし「上限が無い」「意味空間が有限でない」とするが、契約上の型は有限幅の `unsigned` である。通常の加算なら `UINT_MAX` の次で 0 に wrap し、連続 abort 数という意味も失う。飽和させても値域は有限である。[contract v2:115](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/output/insights/2026-09-01_t1871-stage-b-sheet-trigger-gating-v2.md:115>)、[contract v2:124](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/output/insights/2026-09-01_t1871-stage-b-sheet-trigger-gating-v2.md:124>)、[contract v2:145](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/output/insights/2026-09-01_t1871-stage-b-sheet-trigger-gating-v2.md:145>)

   exact 型、初期値、increment が gate 評価の前か後か、reset の正確な位置、wrap/saturation 方針を B で凍結し、「意味的に無限」ではなく固定予算下の操作的非網羅へ主張を戻す必要がある。現状の `DW-O13` は実測値が少数かだけを見ており、有限幅という静的反例を閉じない。[contract v2:191](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/output/insights/2026-09-01_t1871-stage-b-sheet-trigger-gating-v2.md:191>)

2. **`result_` proxy でないという区別は構造的に保たれていない。**

   YCSB の `local_abort_counts_` は各 `abort()` の直後に増え、`local_commit_counts_` は成功 commit 後に増える。提案 counter は同じ abort event で増え、同じ commit event で 0 になるため、これらの履歴をフィルタした fitness signal である。commit が一度も起きない starvation schedule では、値はその worker の累積 abort 数と一致する。[ycsb.hh:149](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/include/ycsb.hh:149>)、[ycsb.hh:161](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/include/ycsb.hh:161>)、[ycsb.hh:166](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/include/ycsb.hh:166>)

   従って「run の fitness signal ではない」と断言しながら、大閾値による長期進捗適応を auditor ギャラリーへ送るだけでは D48 の proxy 禁止を満たさない。[contract v2:127](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/output/insights/2026-09-01_t1871-stage-b-sheet-trigger-gating-v2.md:127>)、[contract v2:150](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/output/insights/2026-09-01_t1871-stage-b-sheet-trigger-gating-v2.md:150>)。説明が実保証より強い F564 型である。[failures.md:F564](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/failures.md:15910>)

   また、YCSB では同一 transaction retry だが、汎用 runner は任意の `Workload::run()` を呼ぶだけであり、commit せず別の logical transaction へ進まないことは一般には証明されていない。`reconnoiter_end()` にも commit を伴わない `begin()` がある。[runner.hh:192](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/common/runner.hh:192>)、[transaction.cc:724](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:724>)。これは caller を追わず意味を一般化する F142 型である。[failures.md:F142](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/failures.md:5492>)

   「worker の commit 間 abort streak」と「現在の logical transaction の retry depth」のどちらを契約するかを選ぶ必要がある。前者なら D48 に対する明示裁定、後者なら logical transaction 交代点で reset できる別の骨格が必要である。

3. **`kUnset` negative control と外側 fail-safe が矛盾している。**

   シートは marker 外で `kUnset` 時に無条件 `true` へ上書きし、候補式の意味検査を不要にすると決めた。一方、negative control には依然として `kUnset=false` の reject を要求する。[contract v2:151](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/output/insights/2026-09-01_t1871-stage-b-sheet-trigger-gating-v2.md:151>)、[contract v2:169](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/output/insights/2026-09-01_t1871-stage-b-sheet-trigger-gating-v2.md:169>)

   外側上書きが正本なら、hole 内の `reason != kUnset` は無害であり、対象 gate 単独で拒否すべき契約違反ではない。逆に禁止するなら、その token/AST 条件を構文契約へ明記する必要がある。現在の負例は単一理由性を持たず、F28/F143 型になる。[failures.md:F28](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/failures.md:838>)、[failures.md:F143](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/failures.md:5507>)

4. **v1 candidate の bytes 保存条件は、新しい counter 骨格と両立しない。**

   v2 は abort increment と `writePhase()` reset を追加するため、flag 1 の preprocessed `transaction.cc` は、述語が v1 と同じでも v1 実装と同じ bytes にはならない。`source_digest` は `transaction.cc` 全体の preprocess 結果を identity に入れるため、正しく別 digest になる。[contract v2:117](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/output/insights/2026-09-01_t1871-stage-b-sheet-trigger-gating-v2.md:117>)、[contract v2:188](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/output/insights/2026-09-01_t1871-stage-b-sheet-trigger-gating-v2.md:188>)、[source_digest.py:1977](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/orchestrator/campaign/source_digest.py:1977>)

   reset store は共有 DB や serializability を直接変えないが、成功 commit の hot path に TLS store を一つ追加し、abort 側にも increment を追加する。従って v1 の既測性能地形が a fortiori 保存されるとも言えない。[transaction.cc:557](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:557>)。条件 9 は「hole RHS の lowering 保存」へ限定し、v2 骨格下の v1 全点は再実測対象とすべきである。materialization と実 build まで届かなかった F19 型にも該当する。[failures.md:F19](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/failures.md:357>)

## should-fix

- **`b_w` の説明は実コードと一致しない。** `lockWriteSet()` は CAS で current element の lock を取得した後に absent を検査し、`max_wset_` の更新はそのさらに後である。従って先頭 UPDATE が absent の場合、lock は成功済みなのに `b_w == true` になる。[transaction.cc:169](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:169>)、[transaction.cc:185](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:185>)、[transaction.cc:191](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:191>)。正確な意味は「それ以前に `max_wset_` へ取り込まれた non-INSERT 要素がない」である。また INSERT は先頭で skip されるため、「途中なら偽」も一般 workload では成り立たない。[transaction.cc:156](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:156>)。YCSB の UPDATE-only 範囲へ限定するならその限定を表へ書くべきである。

- **positive/negative 分離は literal な reject-all 問題を閉じるが、reject-most は閉じない。** 許可観測を一度ずつ使う少数の正例だけを特別受理し、残りの正当な grammar を拒否する gate でも条件 5 は通り得る。[contract v2:177](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/output/insights/2026-09-01_t1871-stage-b-sheet-trigger-gating-v2.md:177>)。正例は production の公開 materialization/build 経路を通し、各 operator、literal 境界、enum、nesting、gate 対象外枝を覆う必要がある。F82、F110、F161、F554 が該当する。[failures.md:F82](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/failures.md:3598>)、[failures.md:F110](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/failures.md:4652>)、[failures.md:F161](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/failures.md:6057>)、[failures.md:F554](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/failures.md:15672>)。負例の subtype 照合はよいが、identity churn 共通集合を機構固有 kill と数えない F568 の条件も必要である。[failures.md:F568](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/failures.md:15977>)

- **raw `.obj_` 撤回の理由には ABI 限定を付けるべきである。** C++ ソースだけでは bitfield の allocation order は portable に確定せず、「上位 32 bit がそのまま epoch」は pinned GCC/x86-64 ABI への依存を含む。[tuple.hh:12](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/include/tuple.hh:12>)。もっとも、commit TID の数値比較自体が epoch 優先の配置へ依存しているため、現行実装意図と raw word の進捗 proxy 性は明白であり、撤回判断は変わらない。[transaction.cc:563](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:563>)

- **新しい liveness 反例を規律 3 の対象へ明記する必要がある。** 例えば「depth が閾値以下の間だけ backoff」という述語では、一度閾値を越えた loser だけが待機を永久に失い、commit して 0 へ戻る worker との非対称が自己強化される。NO_WAIT lock conflict と同一 procedure の即時 retry がこの schedule を許す。[transaction.cc:155](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:155>)、[ycsb.hh:108](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/include/ycsb.hh:108>)。これは serializability 反例ではないが、v1 の reason-only gate より細かい履歴依存 starvation である。条件 13 の指標には depth bucket 別の commit/gate-pass 率と saturation/wrap 到達を加えるべきである。[contract v2:200](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/output/insights/2026-09-01_t1871-stage-b-sheet-trigger-gating-v2.md:200>)

## nit

- worker streak を採用するなら、`izanagi_retry_depth_` より `izanagi_worker_abort_streak_` の方が意味を誤読しにくい。現状は file-scope `thread_local` であり、`TxExecutor` または logical transaction の member ではない。[contract v2:115](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/output/insights/2026-09-01_t1871-stage-b-sheet-trigger-gating-v2.md:115>)、[runner.hh:183](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/common/runner.hh:183>)

## refuted (シートの主張のうち、根拠を確認して支持したもの)

- `b_r` は lock-conflict/update-absent 要因で恒真であり、その要因との conjunction は候補集合を狭めない、という分析を支持する。[transaction.cc:437](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:437>)、[transaction.cc:449](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:449>)

- 生の `.obj_` を禁止した判断を支持する。epoch/TID/state をまとめて観測でき、commit TID の生成経路とも直接結び付く。[tuple.hh:14](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/include/tuple.hh:14>)、[transaction.cc:567](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:567>)

- retry depth は strict な `thid_` の代理ではない。全 worker が 0 から始まり、値は abort/commit 履歴で変わるため、固定 worker ID を直接復元できない。ただし履歴依存の公平性 partition は作れるため、liveness 所見は残る。[runner.hh:183](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/common/runner.hh:183>)、[ycsb.hh:108](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/include/ycsb.hh:108>)

- 新設宣言・increment・reset の全行を `#if BACKOFF_TRIGGER_GATING` 内へ置けば、flag 0 では preprocess 出力から消える。現行 patch の stock 枝も元の backoff 呼出しを保存し、`source_digest` は preprocess 後の `transaction.cc` 全体を比較するため、flag 0 identity の設計主張は支持する。[patch:38](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/patches/silo-backoff-trigger-gating-variant.patch:38>)、[patch:101](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/patches/silo-backoff-trigger-gating-variant.patch:101>)、[source_digest.py:2108](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/orchestrator/campaign/source_digest.py:2108>)

- gate と TLS counter は abort 判定や共有 tuple の更新規則を直接変更しないため、「serializability safety を直接変更しない」という限定表現を支持する。性能、タイミング、starvation まで不変という意味ではない。[transaction.cc:27](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:27>)、[transaction.cc:640](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:640>)

## verdict

reject

## 総括

contract v2 は raw `.obj_` の proxy 問題、`b_r` の縮退、flag 0 identity、serializability の限定表現を正しく処理している。

しかし新設 counter は有限幅であり、「意味空間が無限」という中心論証を満たさない。さらに、commit の無い実行では worker-local abort counterそのものになり、D48 が禁じた fitness/progress proxy との区別も構造的に閉じていない。logical transaction の retry depth と worker の commit 間 abort streakも混同されている。

この二点は表現修正だけではなく軸の適格性と許可観測そのものを左右するため、現 contract v2 は凍結できない。加えて `kUnset` control の自己矛盾、overflow/update 順序の未定義、v1 bytes 保存の不可能条件を B 段で解消してから再レビューが必要である。