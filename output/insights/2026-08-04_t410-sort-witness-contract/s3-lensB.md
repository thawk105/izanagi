# 敵対検証結果

結論から言う。**現 `s2-plan.md` はそのまま段5へ送ってはならない。** ただし、**[T-410] 自体を「実装しない」で閉じるのも誤り**である。原因同値ではなく、origin に束縛された閉じた「観測同値」として設計し直せば実装可能である。

## 1. `reason` は comparator の壊れ方ではなく、事後検査の分岐名である

- **判定:** real
- **根拠:** プランは `(kind, reason)` を「同じ理由で危険」のキーにするが、producer はまず size を検査し、size が同じ場合だけ `rcdptr_` multiset を検査している。[s2-plan.md:69](/work/1/SFC/tanab/dev-wave-jobs/t410-sort-integrity-witness/s2-plan.md:69)、[transaction.cc:421](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/external/ccbench/cc/silo/transaction.cc:421)。D138 の契約自身も、正規化は「症状の分類であって機序の同定ではない」と明記する。[README.md:182](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/output/insights/2026-08-03_t244-p6-contract/README.md:182)、[README.md:207](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/output/insights/2026-08-03_t244-p6-contract/README.md:207)
- **失敗シナリオ:** 非反射・非対称・非推移のどの comparator 違反も UB 後に「無傷」「size 変化」「size 同一だが rcdptr multiset 変化」のいずれにもなり得る。したがって comparator-law → reason は関数ですらなく、全射でも単射でもない。さらに `[(key=a,ptr=A),(key=b,ptr=B)] → [(a,B),(b,A)]` のように pointer の対応だけが入れ替わると、size と pointer multiset は双方不変なので P 行は出ない。ところが writePhase は key を trace へ出しつつ、その `rcdptr_` へ実データを書き込むため、key と実更新先が食い違う。[transaction.cc:601](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/external/ccbench/cc/silo/transaction.cc:601)、[transaction.cc:631](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/external/ccbench/cc/silo/transaction.cc:631)
- **成果物影響:** 他に cycle・integrity 違反がなければ `permutation_violations=0` のまま `clean=true`、`certified=true` になり得る。材料レポートにも witness が無く、proof chain は誤った W key を実更新先として扱う。
- **scope:** 「reason は因果理由でなく postcheck 観測コード」と契約を直すのは scope 内。完全な WriteElement permutation 検査や comparator-law 検査は C++ producer 改変なので裁定パッケージ候補。

なお positive control の “swap” は実際には swap ではなく、片方の pointer をもう片方で**上書き**している。[broken-silo-permutation-swap.patch:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/patches/broken-silo-permutation-swap.patch:9)。本物の pointer swap は現検査を通過する。

## 2. プラン記載の式そのものは同値関係である

- **判定:** refuted
- **根拠:** 有効な `SortIntegrityWitness` の領域を `kind="sort-permutation"` に限定すれば、`reason` の文字列一致は射影の等号なので反射律・対称律・推移律を満たす。[s2-plan.md:73](/work/1/SFC/tanab/dev-wave-jobs/t410-sort-integrity-witness/s2-plan.md:73)
- **失敗シナリオ:** 成立しない。未知 kind を領域へ混ぜれば反射律が崩れるが、プランは未知 kind を拒否して領域外に置く。
- **成果物影響:** 数学的な三法則を理由に設計を却下しても、certified・材料レポート・proof chain は改善しない。欠陥は式の形式でなく、`reason` に与えた意味と実装上の別 equality にある。
- **scope:** 変更不要。ただし定義域を明記することは scope 内。

## 3. 実装には二つの equality ができ、schedule ノイズが実効キーへ戻る

- **判定:** real
- **根拠:** `@dataclass(frozen=True)` の通常 equality は `reason` だけでなく `thid` も比較する一方、`equivalence_key` は thid を捨てる。[s2-plan.md:23](/work/1/SFC/tanab/dev-wave-jobs/t410-sort-integrity-witness/s2-plan.md:23)。さらに JSON は equivalence key を保存せず、thid を含むイベント列だけを保存する。[s2-plan.md:101](/work/1/SFC/tanab/dev-wave-jobs/t410-sort-integrity-witness/s2-plan.md:101)。現 critic は `clean` と `notes` 以外の非空値を、その値ごと dict repr にする。[digest.py:609](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/critic/digest.py:609)
- **失敗シナリオ:** run A は `trace_0.log` に `P size-changed` が1件、run B は `trace_1.log` に同じ P が1件。意図したキーは同じだが、dataclass equality と JSON equality は異なる。さらに既存 positive control 相当では 249,252 件または879,025件あり、再走時にはその件数分の dict が critic prompt に展開され得る。[s5_permutation_coverage.json:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/output/env/linux-baremetal/calibration/s5_permutation_coverage.json:16)、[s5_permutation_coverage.json:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/output/env/linux-baremetal/calibration/s5_permutation_coverage.json:27)
- **成果物影響:** 同じ危険クラスでも thread・発火件数により材料レポートと critic 入力の bytes、切詰め位置、次手が変わる。将来の `witness_class_set` も、event equality を使えば別集合になる。certified は不変。
- **scope:** scope 内。event と class を型として分離し、`thid` を class 比較対象外にする正規化 API と class-set 化を置くべき。

## 4. 未知 reason は捨てられないが、意味層では fail-open になる

- **判定:** real
- **根拠:** 現 parser は任意の単一 token を `permutation_violations` に追加する。[parse.py:154](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/verifier/parse.py:154)。プランは未知 reason を文字列自身の新しい危険クラスとして採用する。[s2-plan.md:90](/work/1/SFC/tanab/dev-wave-jobs/t410-sort-integrity-witness/s2-plan.md:90)。一方、P6 の仮説クラスと反証テストは source failure より前に固定する必要がある。[README.md:211](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/output/insights/2026-08-03_t244-p6-contract/README.md:211)
- **失敗シナリオ:** 将来 emitter が `P size-mismatch-v2`、または typo の `P size-change` を出す。`kind` は既知なので未知-kind gateを通り、観測後に新しい equivalence class が自動生成される。これは事前登録されていない意味を「対応済み」と扱う経路である。
- **成果物影響:** 現 verifier では count が増えて `indeterminate` になるため、正しさシグナルは捨てられず受理集合は緩まない。しかし将来 P6 では未知意味から class hash・validation basis・cut を作れてしまい、proof chain と禁止集合が偽になる。
- **scope:** scope 内で、既知 reason を閉じた enum へ写像し、未知は raw token を保存しつつ `recognized=false` とする。P6 adapter は未知 reason を `P6ContractError` にする。parse error にして現行受理集合を変えてはならない。

未知 **kind** については、Literal、closed schema、consumer の拒否を予定しており、プランが完全に無視しているという批判は refuted。ただし P6 handler 自体は未実装なので、「D138(4)をend-to-endで満たした」とはまだ名乗れない。

## 5. 「整数と自然文の詰め替えだけ」は強すぎるが、P6-ready の名乗りは過大

- **判定:** real
- **根拠:** P 行は自由 prose ではなく `P <reason>` の二 token record であり、イベント列・kind・source hint を分離すること自体には機械可読性がある。[parse.py:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/verifier/parse.py:12)。したがって「何も構造化していない」は refuted。しかし提案型の意味フィールドは依然 `reason: str` だけであり、producer が実際に検査した真偽を型で表していない。[s2-plan.md:24](/work/1/SFC/tanab/dev-wave-jobs/t410-sort-integrity-witness/s2-plan.md:24)
- **失敗シナリオ:** `reason="rcdptr-set-changed"` を consumer が「pointer association swap を検出した」と読む。しかし producer が証明したのは「size は同じ、rcdptr multiset は異なる」だけであり、swap はむしろ見逃す。自然言語名から保証を過大解釈する。
- **成果物影響:** 材料レポートの原因分類と critic の修正方針が、実測していない comparator 機序や pointer 対応関係を参照する。proof chain の witness 説明も producer 保証より強くなる。
- **scope:** scope 内で `reason` をそのまま意味キーにせず、`size_preserved` と `rcdptr_multiset_preserved` の閉じた観測状態へ写像する。完全な comparator 座標・txid・key は存在しないので追加してはならない。

## 6. `thid` は payload ではなく filename 由来の hint である

- **判定:** real
- **根拠:** プラン自身が thid は P 行ではなく path からの推定だと認めるが、wire 名は無条件の `"thid"` である。[s2-plan.md:44](/work/1/SFC/tanab/dev-wave-jobs/t410-sort-integrity-witness/s2-plan.md:44)、[s2-plan.md:53](/work/1/SFC/tanab/dev-wave-jobs/t410-sort-integrity-witness/s2-plan.md:53)。producer は通常 `trace_<thid>.log` を作るが、parser は任意の `trace_*.log` を読む。[trace.hh:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/external/ccbench/include/trace.hh:49)、[parse.py:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/verifier/parse.py:197)
- **失敗シナリオ:** thread 2 が生成したファイルを保存・収集段で `trace_7.log` に rename すると、P 自身には照合情報がないため witness は `thid=7` と断定する。C 行に thid 2 が残っていても、プランには filename と C 行の照合規則がない。
- **成果物影響:** 材料レポートと critic が誤った thread を発生源として次手を作る。受理集合は変わらないが、台帳上の witness 内容と実 emitter 帰属が食い違う。
- **scope:** scope 内。`source_thread_hint` または `trace_stream_hint` とし、`basis="canonical-filename"` を明示し、equivalence から除外する。

## 7. グローバルな `(kind, reason)` は D138 の origin 境界を破る

- **判定:** real
- **根拠:** プランは kind を含めたものを「グローバルなキー」とする。[s2-plan.md:69](/work/1/SFC/tanab/dev-wave-jobs/t410-sort-integrity-witness/s2-plan.md:69)。しかし D138 は cut key を origin manifest・emitter・verifier policy・environment contract・IR schema に束縛し、変更時は新 origin とする。[decisions.md:6767](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/docs/decisions.md:6767)。P6 出力も normalizer・axis adapter・emitter・verifier の hash を別途持つ。[README.md:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/output/insights/2026-08-03_t244-p6-contract/README.md:254)
- **失敗シナリオ:** emitter v1 と v2 がともに `size-changed` を使うが、v2では検査対象または意味を変更する。裸の `equivalence_key` は両者を同一 class にするため、旧 origin の再現証拠や generalized cut が新 origin へ混入する。
- **成果物影響:** 将来の禁止集合が安全な候補を落とし、certified 選択が変わる。proof chain の `witness_class_set` と source refs も異なる producer 意味を一つに束ねる。
- **scope:** 同値関係を「固定 origin 内」と定義するのは今の scope。origin hash、仮説、`B \ C_exact`、cut install を witness 内へ詰めるのは却下し、P6 実装へ延期する。これらは D138 の外側 envelope の責務であり、P 行に架空の candidate 座標を作ってはならない。

## 8. P0 は branch 発火証拠にはなるが、新 witness の E2E 証拠にはならない

- **判定:** real
- **根拠:** 既存 artifact は deliberate erase/overwrite positive control の aggregate count だけを持つ。[s5_permutation_coverage.json:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/output/env/linux-baremetal/calibration/s5_permutation_coverage.json:16)。driver は検証後に raw trace を削除する。[s5_permutation_coverage.py:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/campaign/s5_permutation_coverage.py:163)。プラン自身も、この artifact は新 witness 経路の再現証明にならないと認める。[s2-plan.md:224](/work/1/SFC/tanab/dev-wave-jobs/t410-sort-integrity-witness/s2-plan.md:224)。既知失敗型 F15/F21 も、fixture・静的配線を live E2E と誤認しないことを要求する。[failures.md:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/docs/failures.md:157)、[failures.md:263](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/docs/failures.md:263)
- **失敗シナリオ:** 新 parser が multi-file trace の thid を誤帰属する、または大量 P の一部を落とす。旧 JSON には witness・raw file・順序・thread がないため、aggregate countとの照合だけでは退行を検出できない。それでも「既存 s5 artifact で新経路を確認済み」と記録できてしまう。
- **成果物影響:** certified 値は不変だが、受入記録・proof chain が実在しない historical witness E2E を参照する。材料レポート経路の live 発火も未確認のままになる。
- **scope:** P0 を「P record 分岐が実在するので、表現層について DW-G04 の最小 gate は満たす」まで狭めるのは scope 内。新経路の historical E2E は未確認と明記し、将来の認可再走へ送る。

## 9. 「したがって [T-410] は実装しない」は成立しない

- **判定:** refuted
- **根拠:** U5 は、D138 が P6 を実装しないと決めた後に、sort witness 新設を明示承認して [T-410] へ割り当てている。[worklog.md:1129](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/docs/worklog.md:1129)。D138(7) の不実装理由は、P6についての「設計だけ」という指示、real candidate witness 不在、未裁定の帰納段だった。[decisions.md:6774](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/docs/decisions.md:6774)。その全てを診断表現の追加へ機械的に移すことはできない。
- **失敗シナリオ:** 成立しない。P6 cut と違い、witness 表現は受理集合を狭めず、既存 P positive control で分岐自体も発火済みである。
- **成果物影響:** [T-410] を全面中止すると certified は現状のままだが、材料レポートは reason 内訳を自然文から読むまま、proof chain は sort の構造化 evidence を持てず、P6 は `NOT_IMPLEMENTED` の前提不足を残す。
- **scope:** [T-410] は継続。ただし現プランのままの実装は NO-GO。段4で意味契約を修正してから実装する。

## 総括

### (a) 推奨する同値関係

`O` を D138 の origin contract、すなわち origin manifest・emitter・verifier policy・environment contract・IR schema が固定された領域とする。

認識済み witness の観測コードを次で定める。

\[
c(w)=
\begin{cases}
(\mathrm{size\_preserved}=\mathrm{false},
 \mathrm{rcdptr\_multiset\_preserved}=\mathrm{NOT\_EVALUATED})
& \text{raw reason = size-changed}\\
(\mathrm{size\_preserved}=\mathrm{true},
 \mathrm{rcdptr\_multiset\_preserved}=\mathrm{false})
& \text{raw reason = rcdptr-set-changed}
\end{cases}
\]

固定 origin 内の有効領域 \(W_O\) について、

\[
w \equiv^{obs}_{O} w'
\iff
w,w'\in W_O
\land c(w)=c(w')
\]

とする。global class ID が必要なら、

\[
K_O(w)=H(O,\texttt{"sort-permutation-postcheck/v1"},c(w))
\]

とする。`thid`、出現順、run 内件数、txn 境界は含めない。未知 reason は \(W_O\) に入れず、raw token を保存した上で P6 は fail-closed にする。

これは「同じ comparator 原因」ではなく、**同じ producer 観測**の同値関係である。原因同値が必要なら、現 P 行の情報量では定義不能であり、producer 改変が要る。

### (b) 却下すべき提案

- raw `reason: str` をそのままグローバルな意味キーにする
- dataclass/JSON event equality と equivalence equality を併存させる
- 未知 reason を観測後の新しい危険クラスとして自動採用する
- `thid`、件数、順序を class key に含める
- P 行に存在しない txid・key・comparator-law 座標を捏造する
- 旧 aggregate artifact を新 witness E2E の証明と呼ぶ
- witness 自体に PrecommittedHypothesis や exact-cut key 全体を詰め込む

### (c) 親 brief の P0 / P1

- **P0:** 限定賛成。positive-control artifact は「P 分岐が発火可能」という表現層の DW-G04 根拠にはなる。しかし real candidate、new witness E2E、P6 発火 gate の根拠にはならない。
- **P1:** 記載どおりには反対。reason-only を causal equivalence と呼んではならない。固定 origin・閉じた観測コード・未知 reason fail-closed に直した観測同値なら賛成。

### (d) 「実装しない」が正解か

**[T-410] 全体については、いいえ。現 `s2-plan.md` をそのまま実装することについては、はい。**

段4で上記の意味契約へ修正し、event/class 分離、閉じた観測状態、origin 内同値、source-thread hint を確定してから実装すべきである。P6・cap-lift・exact-cut 結線は D138(7)どおり実装しない。

read-only の静的検査のみであり、pytest は実行していない。緑は主張しない。