## 検算した主張

静的検査のみ実施した。ファイル変更・ビルド・pytest 実走は行っておらず、テスト緑は主張しない。

親の「約 16 状態」は成立しない。`lockWriteSet()` が読み検証より先に走り、`max_wset_` は各 non-INSERT 要素の成功処理末尾、`max_rset_` は読み要素の全検査通過後に更新される点は正しい。[transaction.cc:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:145)、[transaction.cc:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:383)、[transaction.cc:449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:449)

ただし、実行順から得られるセル上限は次になる。

| 要因 | セル上限 | 根拠 |
|---|---:|---|
| lock-conflict | 2 | 読み検証前なので `b_r=true`。失敗前に line 191 を通った要素の有無で `b_w` が分かれる |
| update-absent | 2 | lock 成功後だが `max_wset_` 更新前に abort するため同じ 2 セル |
| readvali-tid | 4 | write 側 2 × 読み失敗が先頭か後続か 2 |
| readvali-locked | 4 | 同上 |
| node-vali | 4 | 全 read 検証後なので read 集合空/非空 × write 側 2 |
| insert-node / scan-node | 各 1 | validation 前なので両 `max_*` は初期値 |
| kUnset | 0 | 出力が常に true に固定され、述語自由度なし |

対象の三つの YCSB workload は `READ` / `WRITE` / `READ_MODIFY_WRITE` しか実行せず、insert・scan を呼ばない。[ycsb.hh:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/include/ycsb.hh:55)、[ycsb.hh:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/include/ycsb.hh:117) さらに D50 は実効要因を `{lock-conflict, readvali-tid, readvali-locked}` の三つと確定している。[decisions.md:1864](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/decisions.md:1864)

したがって対象 workload の静的上限は `2 + 4 + 4 = 10`、意味の異なる truth vector は最大 `2^10` である。実際の joint support は 10 以下であり、正確な値には DW-O13 が必要である。全 workload を対象にするなら逆に insert/scan を捨てられず、セル上限は `2+2+4+4+4+1+1=18` になる。シートの 16 は、YCSB の観測範囲と全 enum 範囲を混同している。[sheet:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/output/insights/2026-09-01_t1871-stage-b-sheet-trigger-gating-v2.md:88)

## must-fix

1. `izanagi_retry_depth_` は意味空間を無限にしない。

   シートは counter を `unsigned` としながら、自然数全体で上限がないと扱っている。[sheet:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/output/insights/2026-09-01_t1871-stage-b-sheet-trigger-gating-v2.md:124)、[sheet:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/output/insights/2026-09-01_t1871-stage-b-sheet-trigger-gating-v2.md:145) C++ の `unsigned` は有限幅であり、通常の加算なら wrap する。幅を `w`、到達する非 counter 状態数を `R` とすれば、入力点は最大 `R * 2^w`、boolean 関数集合も有限である。無限に残るのは冗長な構文表現だけで、シート自身が退けた B-1 の論拠へ戻る。

   exact 型、初回 abort で観測する値、increment と gate の前後関係、overflow 方針を凍結しても有限性は変わらない。ここを「固定予算内で操作的に列挙不能」へ弱めるなら、非列挙軸という中核定義自体の B 段再裁定が必要である。

2. §3 の 16 / `2^16` を撤回し、対象範囲別の数え方へ直す必要がある。

   対象 YCSB では上限 10、全 enum を数えるなら上限 18 で、16 になる一貫した範囲がない。[sheet:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/output/insights/2026-09-01_t1871-stage-b-sheet-trigger-gating-v2.md:92)、D50。また `b_w` は「施錠成功ゼロ」と同値ではない。update-absent は CAS 成功後、`max_wset_` 更新前に return する。[transaction.cc:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:172)、[transaction.cc:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:185)

3. DW-O13 の成功条件を B-5 の固定予算へ結び付ける必要がある。

   条件 10 の joint support・distinct 数・集中度・cross-run 再現は、小さい実効値域を検出する検査としては妥当である。[sheet:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/output/insights/2026-09-01_t1871-stage-b-sheet-trigger-gating-v2.md:191) しかし有限測定から無限 support は証明できず、現状の「数種類でなければ非列挙」という判定は成立しない。

   fail 条件は、事前登録した非 LLM 生成器の試行予算に対して、到達 truth-vector 数、頻度集中、候補間の truth-vector 重複率が十分に非網羅かへ結び付けるべきである。quit 時点で打ち切られた retry の censoring も記録対象に要る。

4. D44 適格性を確認する正例が弱い。

   契約自体は、例えば要因 A と要因 B に異なる二つの retry 閾値を置く述語を表現できるため、直ちに「閾値 1 個」へは潰れない。runtime 入力がスカラーであることと、探索対象がスカラー値一個であることは別である。D44 の禁止は後者である。[phase3-main-experiment.md:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/phase3-main-experiment.md:98)

   ただし必須条件 5 は「各観測を使う正例」に留まり、二つの閾値を独立に変更できることを証明しない。[sheet:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/output/insights/2026-09-01_t1871-stage-b-sheet-trigger-gating-v2.md:177) 少なくとも二要因の閾値を片方ずつ変え、それぞれ別の truth vector になる三候補を admission・materialization まで通す条件へ強化すべきである。実装 admission が共有閾値一個へ正規化するなら D44 違反で reject となる。

## should-fix

- v1 の 32 点は、形式上は §3-D の列挙可能部分空間になる。各部分集合を enum 等値比較と boolean 結合だけの canonical predicate に写せば、有限列挙と構成的安全性を与えられる。[axis_trigger_gating.py:77](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/orchestrator/campaign/axis_trigger_gating.py:77)、[axis-onboarding.md:169](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/inputs/axis-onboarding.md:169)

  ただし必須条件 9 は、raw v1 wire が v2 AST admission を直接通るのか、wire から canonical RHS へ lowering するのかを明記していない。[sheet:188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/output/insights/2026-09-01_t1871-stage-b-sheet-trigger-gating-v2.md:188) 一対一性、重複なし、kUnset を含む truth-table 同値、保存対象 bytes の範囲を固定すれば、この穴は閉じる。

- D 段は v1 の 32 点だけでも形式的には実施可能だが、それは既実施の旧空間を再確認するだけで、retry 次元の実効性を検査しない。v2 の偵察には、DW-O13 後に性能値を見ず凍結した有限閾値集合 `T` と、要因ごとの閾値ベクトルから canonical AST を全列挙する部分空間を追加すべきである。比較・boolean・定数だけに限定すれば全点の安全性を構成的に示せる。全空間の代表性は主張しない。

- B-5 の切り分けは概ね正しい。D1067 は固定予算・固定編集面で事前登録した生成器との条件付き比較しか要求しないため、非 LLM 生成器の文法、複雑度分布、重複縮約、予算、support 非対称は B-5 事前登録側の仕事である。D1012 の三すくみを未解消とした記述も正しい。D1012、D1067。ただし現 v2 は非列挙適格性をまだ満たさないため、B-5 は引き続き発火不能である。

- 約 5 セッションという sort 軸の実測を本件へそのまま当てるのは非現実的である。sort は編集面既開通・死角が実質一つという好条件だった。[axis-onboarding.md:268](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/inputs/axis-onboarding.md:268) 本件の純増は、typed AST admission、拒否 subtype と受理正例、counter 骨格と overflow 契約、O13 計装・実測、v1 wire lowering と全 32 点同値検査、contract-version 同期、contract-only projection、depth-sensitive D 生成器、E driver の wire から式への schema 改訂である。現実的には約 5 セッションに少なくとも 2〜4 セッションを加えた規模を見込むべきである。

## nit

- `b_w` / `b_r` は意味名でなく `max_wset_is_zero` / `max_rset_is_zero` と呼ぶ方が正確である。現在の説明は更新位置から導ける意味より強い。[sheet:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/output/insights/2026-09-01_t1871-stage-b-sheet-trigger-gating-v2.md:85)

- 必須条件 9 の「bytes 保存」は、骨格に counter と派生 boolean が増える以上、TU 全体の逐語同一ではあり得ない。v1 wire、canonical RHS、preprocess 後 stock のどの bytes を指すか限定すべきである。

## refuted (シートの主張のうち、根拠を確認して支持したもの)

- retry lifecycle の骨格は成立する。procedure は RETRY label より前に一度だけ生成され、abort は同じ procedure へ戻り、commit 後に `run()` が返る。[ycsb.hh:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/include/ycsb.hh:102)、[ycsb.hh:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/include/ycsb.hh:108)、[ycsb.hh:161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/include/ycsb.hh:161) したがって、commit で reset する counter は現在の YCSB では「同一 logical transaction の連続 abort」を表せる。

- executor の単一 worker 所有は確認できる。`Tx trans` は worker thread のローカルであり、同じ thread が workload を逐次実行する。[runner.hh:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/common/runner.hh:172)、[runner.hh:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/common/runner.hh:183)

- v1 5-bit wire は v2 が表現可能な安全な有限部分空間になり得る。必須条件 9 を canonical mapping と全点同値検査まで具体化すれば、§3-D の形式要件を閉じられる。

- 「要因別の独立閾値ベクトルを表現できる」という構文上の主張は支持する。従って D44 違反は必然ではなく、実 admission が単一共有閾値へ縮退するかが判定点である。

- D1012 の三すくみを未解消のまま残し、B-5 発火を別の事前登録・ユーザー承認へ送る切り分けは支持する。D1012、D1067。

## verdict

reject

## 総括

contract v2 は、複数要因に独立した retry 政策を持たせられる点では D44 の単一スカラー軸から脱し得る。しかし中核論証である「`unsigned` counter が自然数全体を与え、意味空間を無限にする」は成立せず、親の到達点 16 も対象 YCSB では最大 10である。

これは条件追加だけで閉じる実装漏れではない。非列挙を厳密な意味的無限として維持するのか、固定予算下の操作的非網羅へ定義変更するのかを B 段で再裁定し、到達点解析、DW-O13、D 段部分空間、B-5 発火条件を一緒に組み直す必要がある。