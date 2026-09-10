## 検算した主張

- **構文的非列挙性は成立する。** AST 深さ、式長、定数個数に上限がなければ、候補文字列は無限であり、有限 candidate set は契約から導出できない。[plan.md:76](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/plan.md:76>)

- **意味的非列挙性は成立しない。** 入力は 8 値の要因と二つの 64 bit 値なので有限である。さらに `kUnset` は常に true という制約があるため、意味の異なる述語数の上限は `2^(7 * 2^128)` である。等値比較、任意定数、無制限の boolean 結合が許されるなら、理論上は各入力点を列挙する正準 DNF により完全列挙器を構成できる。無限なのは有限個の意味に対する冗長な構文表現であり、[plan.md:78-89](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/plan.md:78>) の論証だけでは実効的な広さを示せない。

- **ただし理論上有限であることと、固定予算内で列挙可能であることは別である。** 理論上限は極端に大きく、全 64 bit 値が実効入力なら完全列挙は現実的でない。D1067 の「特定の事前登録済み生成器に対する固定予算下の優越」には使いうる。しかし実環境の到達値が少数クラスへ縮退していないことを、まだ示していない。

- **静的には `max_*` が単なる 0/非 0 の二値へ縮退するとは言えない。**
  - `begin()` は両方を 0 にする。[transaction.cc:55](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:55>)
  - `max_wset_` は lock 成功済み prefix の record version だけを取り込み、競合または absent で失敗した要素自身は取り込まない。[transaction.cc:145](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:145>)
  - `max_rset_` も検証成功済み prefix の最大値で、失敗要素は取り込まれない。[transaction.cc:449](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:449>)
  - record version は commit 時に epoch/tid を用いて更新されるため、正確な値は DB 進捗に応じて変化しうる。[transaction.cc:557](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:557>)
  
  一方、早期 abort や最初の要素での失敗では 0、後段失敗では成功済み prefix の最大値、という強い相関がある。実効値域の大小は静的資料だけでは確定できない。

- **D 段の列挙可能部分空間は失われていない。** 現行 5-bit wire は新文法でも表現できる有限部分空間であり、§3-D が要求する「列挙可能な部分空間」を満たす。[axis-onboarding.md:164](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/inputs/axis-onboarding.md:164>)、[axis_trigger_gating.py:77](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/orchestrator/campaign/axis_trigger_gating.py:77>)。旧部分空間が生きているという二値判断も D50 が支持する。ただし、C 段で旧 wire の lowering が逐語同値であることを証明する必要がある。

- **D1012 の三すくみは解消していない。** [plan.md:89](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/plan.md:89>) の「回避する」は過大である。有限部分空間を D 偵察用に残すことは D 段を実施可能にするだけで、B-5 の非 LLM アームとの support 非対称を解消しない。D1067 自身も行き止まりは消えないと明記しており、解消したのは必要性主張を捨てたことである。これは軸の致命傷ではなく、B-5 事前登録側の課題である。

- **D47 の「新軸」gate との衝突はない。** 本件は新しい hole の発見ではなく、D48 が明示的に予約した同一軸の契約改訂である。さらに phase 正本は旧 headline の復活経路として「D48 差し戻し事項の消化」を明記している。[phase3-main-experiment.md:170](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/phase3-main-experiment.md:170>)。ただし「新軸」ではなく「同一軸の contract v2」と呼ぶべきである。

- **(c') は新契約全体へ自動継承できない。** 現行 (c') は D48 決定 2、すなわち旧 wire-only 契約で偵察空間と coder 空間が一致することを根拠にしている。[phase3-main-experiment.md:163](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/phase3-main-experiment.md:163>)。改訂後も旧部分空間には掛かるが、二観測を使う全空間には掛からない。

- **新規シートを作る判断は正しいが、4 参照という実測は現在の worktree では誤りである。** `git grep` の tracked hit は 8 件だった。内訳は、正本・履歴文書 3 件、コード内の設計・provenance 宣言 2 件、保存済み campaign provenance 3 件である。[archive:96](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/archive/phase3-s6-s8a-completed-details.md:96>)、[decisions.md:1724](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/decisions.md:1724>)、[axis_trigger_gating.py:8](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/orchestrator/campaign/axis_trigger_gating.py:8>)、[loop:206](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/orchestrator/campaign/p3_s4_loop_trigger_gating.py:206>)、[patches/README.md:291](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/patches/README.md:291>)。bytes hash pin は確認されなかった。どの consumer もシート本文を実行時に parse してはいないが、in-place 改訂は歴史的 provenance の意味を遡及変更するため不適切である。

## must-fix

1. **非列挙性の主張を二層化すること。**  
   「構文集合は無限」と「意味空間は有限だが固定予算では非網羅」を分ける必要がある。現在の [plan.md:78-89](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/plan.md:78>) は前者だけから B-5 適格性を導いている。厳密な意味的非列挙を要件とするなら本軸は reject であり、D1067 の条件付き優越を基準にするなら「操作的に非網羅」と限定すべきである。

2. **DW-O13 相当の値域実測を C 着手前条件へ追加すること。**  
   要因別・workload 別・独立 run 別に、`(reason, max_rset_.obj_, max_wset_.obj_)` の joint support、0 比率、distinct 数、頻度集中度、epoch/tid/flag の分布、cross-run 到達再現性を測る必要がある。B-5 側では、事前登録した生成器が生む述語の truth-vector distinct 数も held-out 入力上で測る。比較予算内に実効 truth-vector を列挙し尽くせる、または少数クラスへ集中する場合は B へ差し戻す。現行 15 条件にはこの gate がない。[plan.md:161-177](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/plan.md:161>)

3. **D1012 を「解消済み」と記録しないこと。**  
   正しい位置づけは「三すくみは残るが、D1067 により必要性主張を捨てたため、正確に凍結した生成器に対する条件付き比較は可能」である。非 LLM 生成器の文法、複雑度分布、編集面、予算、重複縮約、support 非対称の開示は B-5 事前登録側の scope であり、本 wave の軸シートだけでは B-5 を発火させない。根拠は D1012 決定理由と D1067。

4. **(c') の適用範囲を明記すること。**  
   旧 5-bit 部分空間には (c') を維持し、拡張空間については未判定とする。D1012 に従い、本 wave で拘束力ある事前登録を先行改訂してはならない。B-5 発火時の日付付き、ユーザー承認付き改訂へ送ること。根拠は D52、D1012、[phase3-main-experiment.md:166](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/phase3-main-experiment.md:166>)。

5. **軸 identity と契約 version を分離すること。**  
   `MARKER_ID` と `SOURCE_REL` の据え置きは正しいが、現行実装は明示的に fixed 5-bit wire である。[p3_s4_loop_trigger_gating.py:16](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/orchestrator/campaign/p3_s4_loop_trigger_gating.py:16>)。`axis-onboarding.md` も同軸を wire-only と記録する。[axis-onboarding.md:229](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/inputs/axis-onboarding.md:229>)。新シートと D entry には `contract_version`、`designed/inactive` 状態、旧 D48 のどの節をいつ supersede するかを置く。C/E 同期完了前に既存 consumer が新契約を指す状態にしてはならない。

6. **リーク防壁を「偵察値禁止」だけで終えないこと。**  
   草案には低位 bit、record 世代、transaction class 近似など、coder にとって具体的な探索ヒントになる仮説が含まれる。[plan.md:91-113](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/plan.md:91>)。現行機構がシート本文を coder 入力にしない設計なのは確認できた。[axis_trigger_gating.py:11](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/orchestrator/campaign/axis_trigger_gating.py:11>)、[loop:183](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/orchestrator/campaign/p3_s4_loop_trigger_gating.py:183>)。新契約でも、coder へ渡すのは許可観測、演算子、sentinel、単一代入 frame だけの固定 projection とし、シート、裁定台帳、値域実測、risk 仮説を入力にしないことを凍結する必要がある。

## should-fix

- **brief の参照数を 4 から 8 へ訂正すること。** [brief.md:38-41](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/inputs/brief.md:38>)。同時に「consumer を壊す」は、実行時 parse の破壊ではなく、歴史的正本と provenance の意味を遡及変更することだと限定すると正確になる。

- **brief の M2/M3 を plan 側の訂正へ揃えること。** `clear()` は size/empty を恒値にするが capacity、bucket、address まで消さない。また生存メンバ列挙は非網羅である。[brief.md:67-68](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/inputs/brief.md:67>)、[plan.md:22-25](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/plan.md:22>)。禁止判断は維持できるが、brief の一般化は誤りである。

- **15 条件を次のように rightsize すること。**

  | 分類 | 対象 | 判定 |
  |---|---|---|
  | (a) 規律 2 に不可欠 | 2、3、4、5、6、7、10、14、9 の admission 部分 | 維持。ただし 4 と 10、9 の新規部分は一つの typed-admission 条件へ統合する |
  | (b) 過剰または重複 | 8 の既存 7-store 全再証明、9 の旧 misattribution 設計やり直し、11 の新規指標一式の即時実装、15 | 既存証拠の回帰確認へ縮小する。11 は指標と発火条件の登録までとし、新 instrumentation は発火時の別 scope。15 は標準受入手順なので D 条件から外す |
  | (c) C 段設計へ送る | 3〜7、統合後の 9/10、12 の旧 wire 同値証明、14 | B では要求と fail 条件だけ凍結し、実装方式を先取りしない |
  | B 段に残す | 1、2、13、(c') scope、contract version、DW-O13 gate | B 出口と将来入力の境界なので C へ先送りしない |

- **消化判定を客観化すること。** 特に #3 の「単一 owner を証明」、#11 の閾値、#14 の「同一契約」、#15 の「関連テスト」は現状では主観判定になりうる。[plan.md:165-177](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/plan.md:165>)。callsite/writer 一覧、正規 grammar schema、consumer-version 一致検査、数値付き reachability fail 条件を成果物として指定すべきである。

- **工数を sort 軸の約 5 セッションへそのまま当てはめないこと。** source 編集面は既開通なので形式的な `+1` は不要だが、現行 E driver は trusted emitter の固定 wire しか受けず、構文検査も candidate admission ではない。[loop:168](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/orchestrator/campaign/p3_s4_loop_trigger_gating.py:168>)。typed parser、semantic normalization、negative controls、projection、driver schema 改訂、値域実測が純増する。§6 自身も sort の約 5 セッションは好条件下の実測で、死角数に比例すると限定している。[axis-onboarding.md:263](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/inputs/axis-onboarding.md:263>)。C の設計確定前に総工数を固定しない方がよい。

## nit

- [plan.md:146](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/plan.md:146>) の「非列挙コード片へ戻す」は、旧シートの型名と現行 wire 実装を混同しやすい。「同一 hole の contract v2 として member-aware expression へ再拡張する」が正確である。

- 静的 admission の禁止入力は「positive control」より「admission mutation-red」または「negative control」と呼ぶ方が、既存 misattribution positive control と混同しない。[plan.md:124-139](</work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1871-nonenum-axis-stage-b/plan.md:124>)

## refuted (草案・brief の主張のうち、根拠を確認して支持したもの)

- **P1-2 は支持する。** D47 必須条件 4 は新規 axis-proposer 提案の hole 差異 gate であり、D48 が明示的に予約した契約差し戻しの消化を禁止しない。D48 と [phase3-main-experiment.md:170](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/docs/phase3-main-experiment.md:170>) が直接根拠になる。

- **P1-3 の新規シート判断は支持する。** 件数は誤っているが、旧シートは履歴的な wire-only 契約の正本であり、in-place 改訂は provenance を遡及変更する。bytes hash pin がないことは新規作成判断を弱めない。

- **P1-4 の構造部分は支持する。** 旧 5-bit wire は明確な有限部分空間であり、§3-D は全 coder 空間の代表性ではなく列挙可能な部分空間の獲得を要求している。旧部分空間の生死も二値として確認済み。ただし C で旧 lowering の同値証明が必要である。

- **二つの `.obj_` の rvalue 読取自体は静的に初期化済みである。** constructor と `begin()` の 0 初期化、および `Tidword` コピーによる更新を確認した。[transaction.hh:68](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/include/transaction.hh:68>)、[transaction.cc:55](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1871-nonenum-axis-stage-b/external/ccbench/cc/silo/transaction.cc:55>)。これは UB 不在の一部を支持するが、実効値域の広さは支持しない。

- **草案へ偵察の勝ち gate、利得値、順位が直接混入した形跡はない。** 軸の生死は二値に限定されている。残る問題は、草案中の仮説を将来 coder 入力へ転写しない経路保証である。

## verdict

adopt-with-conditions

1. 非列挙性を「構文的無限」と「固定予算下で操作的に非網羅」に分け、意味的には有限であることを明記する。
2. DW-O13 の値域・truth-vector 実測と、比較予算に結びついた数値付き fail 条件を凍結する。実効空間が小さければ B へ差し戻す。
3. D1012 の三すくみは未解消と訂正し、B-5 は exact な非 LLM 生成器と予算の事前登録まで休眠を維持する。
4. (c') を旧 5-bit 部分空間へ限定し、拡張契約の事前登録改訂は発火時のユーザー裁定へ送る。
5. 同一 marker のまま `contract_version` と activation state を導入し、現行 wire consumer と新契約を二義化させない。
6. C 段で旧 5-bit lowering の逐語・意味同値を証明し、有限部分空間を維持する。
7. coder/planner には contract-only projection だけを渡し、シート、裁定台帳、値域実測、risk 仮説を入力禁止にする。
8. 15 条件を統合・客観化し、typed admission と値域実測を含む現実的な C 段工数へ再見積もりする。

## 総括

この案は、同一 hole の安全な contract v2 としては成立しうる。有限の偵察部分空間も維持でき、D47 とも抵触しない。一方、現在の「AST が無限だから非列挙」という論証だけでは B-5 適格性を示せず、D1012 や (c') も解消済みではない。

従って段階 B では条件付き採用が妥当だが、現時点では「B-5 を実行可能にした軸」とは扱えない。値域実測、契約 version、事前登録の scope 修正、contract-only projection が次の fail-closed 条件である。検査は静的のみで、テスト緑は主張しない。