静的検査のみを行った。pytest および実測 script は実走していない。

## 1. `merge-file` の結果から「手解決だった」とは断定できない

1. 主張  
   `git merge-file -p --diff3` は blob 単位の低水準 text merge であり、実際の merge strategy の忠実な代理ではない。[measure_mergefile.py](/work/1/SFC/tanab/dev-wave-jobs/known-violation-review-20260823/measure_mergefile.py:33) は単一 merge base を選び、temp file に書いた三つの blobだけを処理する。このため rename/directory-rename、path 固有の `.gitattributes` と custom merge driver、mode・gitlink、historical Git version/option、実際に `git merge` が実行されたかを再現しない。

2. 再現例  
   対象 path に custom driver を設定し、driver が `%A` をそのまま採用して rc=0 を返す repository を作る。実際の `git merge` は競合なしで完了する一方、同じ base/ours/theirs blob を無関係な temp file に書いて `git merge-file` へ渡すと custom driver は適用されず、内容次第で conflict rc になる。rename 後の path に merge 属性を付けた場合も同型になる。

3. 成果物への影響  
   script が実証するのは「素の blob-level text merge が競合した、またはその自動出力と最終 blob が違う」までである。「10 件は実際の merge で競合し、人が手解決した」という分類値はこの script 単独では成立しない。G5 は少なくとも「proxy-conflict、実際の解決過程は未確定」へ弱める必要がある。ただしこれは案 A を救わない。後述の述語反例と D721 により、撤去可能件数は安全側では 0 のままである。

## 2. `_commit_paths()` は finding 対象 path 集合ではない

1. 主張  
   `_commit_paths()` は実装面・非実装面を問わず changed path を返す。[validate_implementation_author()](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:1490) がその後 `_is_implementation_path()` で絞った集合だけを `missing-codex-author` の対象にする。一方、三つの測定 script は `_commit_paths()` 全体を評価している。

2. 再現例  
   merge に次の二つを含める。

   - `tools/checker.py`: 両親の純粋 interleave
   - `docs/report.md`: merge 自身が novel 行を追加

   checker の Codex author finding は前者だけを対象とするが、`measure_union.py` と `measure_subseq.py` は後者も集計し、commit 全体を genuine と誤分類する。`prevented.py` も非実装 docs path が一つあるだけで `paths <= LEDGER` を偽にする。

3. 成果物への影響  
   10/4 件と案 B の 12 件は、実装面 path だけへ明示的に絞った再測定なしには exact 値と呼べない。方向として、案 A の候補数と案 B の防止可能数を過少評価し得る。追補が列挙した現物では ledger file だけだったとされるため、現存値が実際に変わるとは裏取りできないが、land 根拠としては再測定が必要である。

## 3. 10 件・4 件という測定は plan v1 の bytes 述語を測っていない

1. 主張  
   `measure_union.py` と `measure_subseq.py` は `bytes.splitlines()` を使うが、plan v1 は `bytes.split(b"\n")` で末尾空要素を保持すると定義している。また `measure_subseq.py` は plan の「result の出現数が親の総数以下」という条件を実装していない。`git show` の失敗確認も `measure_union.py` にはない。

2. 再現例  

   - 最終 LF: 両親を `b"x"`、結果を `b"x\n"` とする。両 script はすべて `[b"x"]` と見て pure-interleave とするが、plan の分割では結果だけ `[b"x", b""]` となり novel 行がある。
   - 出現数: 両親を `[b"x"]`、結果を `[b"x", b"x", b"x"]` とする。両親は結果の subsequence で novel 0 だが、結果の3回は親合計2回を超える。測定 script は strong、plan は不成立となる。
   - result deletion: `git show <merge>:<path>` が失敗すると `measure_union.py` は空 stdout を空 file と扱い、`tot == 0` へ落とし得る。

3. 成果物への影響  
   「plan v1 の述語を満たす4件」という値は未実証である。LF保持、全 subprocess rc、mode/object type、出現数条件を含めて再測定するまで、撤去対象4 SHAは台帳に残し、想定撤去件数は0とすべきである。

なお、[is_subsequence()](/work/1/SFC/tanab/dev-wave-jobs/known-violation-review-20260823/measure_subseq.py:21) 自体の iterator 消費は重複行にも正しく働く。`[x, x]` は `[x]` の subsequence にならない。問題はその外側の述語と未実装の出現数条件にある。

## 4. 案 A は具体的な実装著作を免除する

1. 主張  
   novel 0、出現数上限、全親 subsequence をすべて満たしても、merge author が実装上の意味を著作できる。したがって案 A は Codex author gate を緩める。

2. 反例  

   デコレータ順序の例:

   ```python
   # P1
   @audit
   def check(value):
       return value

   # P2
   @authorize
   def check(value):
       return value

   # R
   @audit
   @authorize
   def check(value):
       return value
   ```

   P1・P2 はともに R の subsequence、R の全行は親由来、出現数も上限内である。しかし R は `audit(authorize(check))` を選んでおり、逆順とは挙動が異なる。相対順を決めたこと自体が実装著作である。

   同一行重複ならさらに直接的である。両親が同じ `hooks.append(register)` を1行ずつ持ち、R が同じ行を2回置けば、各親は subsequence、結果2回は親合計2回以内、novel 0である。それでも二重登録という新しい挙動を merge author が作っている。

3. 成果物への影響  
   案 A を入れると、この形の Claude-only merge から `missing-codex-author` が消え、受理集合が拡大する。提案された4 SHAを外せば表面上は53→49、missing-codex-author は19→15になるが、その値は緩んだゲートによるもので受理不可である。D721を supersedeしても反例は消えないため、正しい値は53件維持、撤去0、案 A の land 不可である。

## 5. 案 B の docs-only 化は Codex author 契約の抜け道になる

1. 主張  
   provenance 規約は実装面に「テスト・checker・hook・probe・harness・生成器・機械設定」を含むと逐語で定める。[ai-provenance.md](/work/1/SFC/tanab/dev-wave-jobs/known-violation-review-20260823/ai-provenance.md:33) checker の受理集合を変える JSON 台帳は checker 資材か機械設定であり、散文 docs ではない。ところが現行 `_is_implementation_path()` は `docs/**/*.json` を実装面にしない。[実装面テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/orchestrator/tests/test_check_ai_provenance.py:686) でも、prefix 配下の JSON と通常 docs を区別している。

2. 再現例  
   Claude author だけの commit で `docs/provenance/known-violations/<sha>.json` を追加し、過去の raw finding と一致する SHA/kind/value を置く。commit 自体は docs-only と判定され Codex author を要求されない。その後の全史監査は JSON を読み、過去 finding を抑止する。つまり Codex author を要する checker 変更を path 選択だけで docs へ逃がせる。

3. 成果物への影響  
   台帳追加に対する author gate が消え、受理集合を Claude-only commit で変更可能になる。案 B を採るなら、データ directory 自体を実装面として分類する必要がある。例えば実装 prefix 配下に置くか、対象 directory を `_is_implementation_path()` へ明示追加することが最低条件である。「docs-only になること」を収益としている現案 B は却下すべきである。

## 6. 案 B は schema 同値性と新しい入力面を定義できていない

1. 主張  
   現行 `_known_violation_registry()` は単なる型確認ではなく、full lowercase SHA、kind 集合、ruling、note、malformed の value、制御文字、重複などを fail-closed で検査する。[現行 validation](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:901) JSON 化案には同値な schema、file discovery、HEAD との結合条件がない。

2. 再現例  

   - 現行53 entryには `649fe5...` の2 findingがある。したがって53 entryは52 commitである。`<sha>.json` を1 entry 1 fileとすると二つが同名衝突し、片方を上書きする。array 化すれば「1件1file」ではなくなる。
   - 標準 JSON parser は同一 object 内の重複 keyを通常は後勝ちで失う。unknown field、filenameと本文SHAの不一致も別途拒否が必要である。
   - loader が worktree の glob を読むなら、HEADにない untracked JSONを置くだけで findingを抑止できる。`Path.read_text()` で symlinkを追えば repository外の内容も入力になる。

3. 成果物への影響  
   `649fe5...` の一方を失えば、もう一方の raw finding が残って全史監査・landが失敗する。逆に untracked/symlink入力を受ければ、HEADの台帳を変えず受理集合だけが広がる。少なくとも次を定義しない案 B は意味同値ではない。

   - filenameを `<sha>--<kind>.json` 等にして1 findingを一意化
   - duplicate key、unknown/missing key、型、文字規則の厳格拒否
   - filenameと本文のSHA/kind一致
   - regular tracked fileのみ、symlink・untracked・ignored file拒否
   - pinned HEADのtreeから読むか、worktreeとHEADの完全一致を検証
   - 現行の重複・note・value invariantsをそのまま再利用

## 7. 案 C の逐語ミラーは、全史監査が見ない台帳値を守っている

1. 主張  
   親の「ruling/note は受理集合に効かないから pin する価値がない」は成立しない。まさに受理判定に使われないからこそ、全史監査ではその改変を検出できない。逐語ミラーは SHA/kind/valueだけでなく、ruling、note、順序、件数、kind集合、note-required集合を独立に固定している。[逐語ミラー](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/orchestrator/tests/test_check_ai_provenance.py:1861)

2. 再現例  
   任意の entry の `ruling` を非空の `"fabricated-ruling"` へ変更する。現行 validator は非空文字列として受理する。`_known_violation_audit()` は照合に commit/kind/valueしか使わず、rulingもnoteも参照しない。[照合箇所](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:1943) 実 commit 照合テストも31件について `(commit, kind)` だけを assertする。[実 commit テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/orchestrator/tests/test_check_ai_provenance.py:2290) したがって全史監査はgreenのまま、現行逐語ミラーだけが改変を検出する。missing系 entryのnoteを空にして説明を消す例も同様である。

3. 成果物への影響  
   受理集合とland可否を変えずに、台帳の裁定根拠・公開noteだけを偽造または消去できる。つまり台帳成果物の値が変わるのに全史監査は検出しない。依頼が示した却下条件を満たすため、案 C は却下すべきである。競合を減らすなら、逐語保証を削るのではなく、独立oracleもentry単位へ分割する必要がある。

## 8. 53件の生成器分類には実在する誤分類がある

1. 主張  
   `classify.py` は canonical trailerを検査せず、commit bodyに文字列 `AI-Agent:` が含まれるかだけを見る。また missing-codex-author の mergeを無条件にG5、それ以外を無条件にG6へ入れる。[classify.py](/work/1/SFC/tanab/dev-wave-jobs/known-violation-review-20260823/classify.py:25) これは生成器の全数分類ではない。

2. 再現例  
   `3f2c43d758...` の逐語noteには「AI-Agent行とCo-Authored-By行の間の空行で trailer block 不成立」と明記されている。[ミラー内の当該entry](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/orchestrator/tests/test_check_ai_provenance.py:1982) `has_agent` は真になるため、scriptはこの `missing-ai-agent` をG6「managerが実装面を直接commit」へ落としている。実際の生成器は trailer block配置誤りであり、G6ではない。

3. 成果物への影響  
   G6=9 は誤りで、少なくともG6=8、新カテゴリ「trailer block配置誤り」=1へ直す必要がある。合計は53 registered findingsのままだが、unique commitは52である。履歴書換え、文法緩和、PR-C01拡張を使わず既存 findingを消す別経路は、指定資料からは見つからなかった。さらに案 Aも却下すべきなので、安全な撤去可能数は4でも49でもなく0、残置は53である。

## 推測・未確定

`growth.py` は registryを構文解析せず、file全体の文字列 `KnownViolationSpec(` の出現数を数えている。comment、docstring、別fixtureに同じ文字列が入るだけで見かけの件数が増える。現在値53との一致は確認されているため現時点の値は支持されるが、過去20増加点・2減少点の各時点に偽出現がなかったことは指定資料から裏取りできない。従って34→53と約10件/日の値は有力だが、厳密値とするには各blobの registry literalだけを構文的に数え直す必要がある。

## 総括

案 A: 却下。全親subsequenceでもデコレータ順序や同一行重複による実装著作を通し、D721の問題を解消しない。  
案 B: 現案は却下。docs-only化がauthor gateの抜け道になり、schema・tracked HEAD・複数finding/SHAの契約も不足している。  
案 C: 却下。全史監査が検出しないruling/note改変を逐語ミラーだけが検出している。  
案 D: 採用。コード・台帳を変更せず53 findingを維持し、分類訂正と、実装面扱いのentry単位台帳設計を別タスクへ切り出す。