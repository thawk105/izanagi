## 所見

### 1. must-fix — `--full-history` の完全性が未証明

plan は `C` を正確な改版集合として使いますが、親実測が示したのは 1 repo、1 HEAD での一致だけです。資料自身も一般保証ではないと認めています。[parent-measurements.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1759-t1742-ratification-history/parent-measurements.md:25) の 17 件一致から、[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1759-t1742-ratification-history/s2-plan.md:27) の全履歴規則を導くことはできません。

実装が必要とする最小条件は、`C` が次をすべて含むことです。

`T(H) = {H の到達可能 commit c | c の台帳 entry が少なくとも一つの実親と異なる}`

これに台帳を持つ root 導入も含めます。`C` の順序と余分な要素は不要です。安全にするなら path 制限なしの全 ancestor DAG を列挙し、entry 差分から `T(H)` を自前で作るか、少なくとも全 DAG との completeness cross-check が必要です。

成果物への差分: 遷移が `C` から漏れると、削除や置換を含む履歴の digest が批准集合へ混入し、未批准 lock の `certified` 受理とレポート値が可能になります。

### 2. must-fix — 「実親数」と「台帳を持つ親数」が資料内で矛盾

plan は実親が 2 個以上なら merge 規則と明記しています。[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1759-t1742-ratification-history/s2-plan.md:32) 一方、親 probe は実際には台帳を持つ親だけを数え、16 個の 2 親 merge を「親 1 個扱い」としています。[parent-measurements.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1759-t1742-ratification-history/parent-measurements.md:40)

author が probe 側の分類を踏襲すると、F600 型 merge は強化後の 1 親規則「ちょうど 1 行追加」に入り、byte 不変なので再び拒否されます。分岐条件は必ず実親総数に固定し、台帳なし親は merge 規則内で空列として扱う必要があります。

成果物への差分: 誤分類を残すと現 main の 16 merge が引き続き偽赤になり、certified v2 lock は 0 件のままです。

### 3. must-fix — strict suffix は正しい cherry-pick と rebase を拒否

親 `[a,c]` に、別 branch で承認済みの `b` を cherry-pick し、元の時系列を保つため `[a,b,c]` と解決すると、集合としては 1 行だけ増え、既存行 `a,c` の相対順も保存されています。しかし末尾追記ではないため拒否されます。rebase でも同じ形になります。

1 親規則を次まで弱めれば、既存否定例を維持できます。

- 親 rows は子 rows の部分列
- `set(child) = set(parent) + exactly one new digest`
- 行数差は 1

置換、既存行の並べ替え、削除、複数行追加は依然拒否されます。

成果物への差分: strict suffix のままでは批准集合が同じでも cherry-pick の解決順だけで lock 作成可否が変わり、正しい digest の certified lock と A-2 レポートが欠落します。

### 4. must-fix — merge の共通 supersequence 要求は、正しい批准集合にも解がない

台帳の公開結果は `frozenset` ですが、merge 規則は全親の行順を同時保存します。独立 branch が同じ承認を別順で記録した場合、正しい和集合を表す子が存在しません。

例:

- `P1 = [a,b]`
- `P2 = [b,a]`
- 子の集合は `{a,b}` で正しい
- 重複行は禁止されるため、`P1` と `P2` の両方を部分列にする子は存在しない

octopus では `P1=[a,b]`, `P2=[b,c]`, `P3=[c,a]` の循環も作れます。行順が批准の意味に含まれないなら、merge は exact union のみを要求する方が成果物の意味と一致します。行順も監査対象なら、並行批准に適用できる一意な全順序を別途定義する必要があります。

成果物への差分: 現規則では全 digest が人間承認済みでも全 merge 解が拒否され、正しい批准集合に対応する certified lock が作れません。

### 5. must-fix — mode-only 変更の拒否は、守る値と対応していない

plan は `100644` から `100755` への変更を検出力後退の例としますが、批准の公開値は JSONL bytes 由来の digest 集合であり、tree mode は値に入りません。[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1759-t1742-ratification-history/s2-plan.md:21)

通常 blob のまま bytes が同じなら、実行 bit の変化を理由に A-2 を停止する実益が示されていません。symlink、gitlink、非 blob は拒否しつつ、`100644` と `100755` の同一 blob 遷移を no-op とする余地があります。

成果物への差分: mode 固定を残すと批准集合が完全に同じでも certified lock が 0 件になり、レポート値だけが filesystem metadata に依存します。

### 6. must-fix — gate は新規 lock 作成だけに届き、既存 lock の受入には届いていない

投影資料で数えられる production 経路は次です。

- `require_ratified_closure`: 直接 caller は `verify_ratified_contract_loader_binding()` 1 箇所。[contract_loader_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/contract_loader_binding.py:387)
- その caller: 正本テストの期待 inventory では `ident.py::_capture_current_loader_binding` 1 箇所。[test_t671_source_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/tests/test_t671_source_binding.py:736)
- 新規 lock: `ident.ensure_campaign_identity()` が未批准を拒否し、批准済みなら lock を作る 1 経路がテストされています。[test_t671_source_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/tests/test_t671_source_binding.py:450)
- 既存 lock: `ident.verify_against_lock` は live binding 検査だけで、ratification caller ではありません。
- artifact 受入: `artifact_admission.py::_verify_committed_loader_binding` は `binding_from_authority` と `verify_committed_contract_loader_binding` だけを呼ぶ想定です。後者は commit blob と記録 digest の一致しか見ません。[contract_loader_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/contract_loader_binding.py:405)
- `campaign_lock.py` は codec と 25 path 定義だけで、ratification gate は呼びません。
- dispatch、受入全体、レポートから gate へ至る production edge は、投影資料内にはありません。

したがって plain JSON lock を偽造できない別根拠がなければ、正しい blob map を持つ未批准 v2 lockが受入側を通る可能性があります。これは投影された call inventory からの推論であり、未投影の dispatch 実装までは証明できません。

成果物への差分: creation-only のまま lock の真正性も無い場合、受理 artifact 集合へ未批准 lock が入り、レポートの `certified` 参照が台帳と無関係に立ちます。

### 7. must-fix — この修理だけでは A-2 は開かない

module 自身が 25 path closure に含まれるため、修理で closure digest は変わります。既存行 `db511c3d...` は不一致のままです。[brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1759-t1742-ratification-history/brief.md:27) さらに D905 は、成りすませない批准実行主体が完成するまで批准を進めない裁定です。

従って正しい完了状態は「履歴検査を通過した後、`enforcement-source-closure-unratified` で拒否」であり、A-2 certification の成功ではありません。

成果物への差分: 履歴関数だけ直しても新 digest の批准行、certified lock、A-2 レポート値はすべて未生成のままです。

### 8. must-fix — shallow、graft、replace の拒否範囲が過大

shallow の全拒否は安全側ですが、正しい履歴も必ず拒否します。現時点の実 checkout、共有 fixture、T671 fixture はすべて non-shallow です。投影資料で gate が shallow checkout 上を走る実 artifact、計算ノード clone、dispatch、CI 経路は見つかりません。唯一の shallow 経路は plan が新設する合成テストです。

また、次は明白な偽赤です。

- 空の `.git/info/grafts` が存在するだけ
- 到達不能 commit 用の replace ref があるだけ
- replace ref は実行引数と環境で既に無効化されているのに、その存在だけで拒否

shallow は信頼済み genesis/checkpoint が無い限り拒否が妥当ですが、「full history checkout が新規 certification の前提」と運用契約へ明記すべきです。replace ref の存在拒否は削除可能です。graft は少なくとも空の通常 file と有効な内容を区別すべきです。

成果物への差分: 現案では正しい批准履歴でも shallow checkout、空 graft file、無関係 replace ref のいずれか一つで受理集合が全面的に空になり、certified lock 作成が停止します。

### 9. must-fix — 性能は node/edge 線形ではなく、blob bytes では二次になりうる

plan の process 数式自体は成立します。`V=|C|`、`E=sum indegree(c)`、最大親数を `K` とすると、

`N_git = 6 + V + S + I(B>0)`

`S <= 1 + V + E`

従って、

`N_git <= 8 + 2V + E <= 8 + (K+2)V`

です。10 秒は全体 timeout ではなく各 process の timeout なので、Git 待ちだけで最大約 `10 * N_git` 秒へ増えます。

より大きな穴は batch のデータ量です。1 行ずつ増える `V` 個の異なる blob をすべて読む場合、平均行幅を `L` とすると出力量は、

`Q = sum |blob_i| = L * V(V+1)/2 = Theta(LV^2)`

です。merge subsequence 検査も `sum(indegree(c) * rows(c))` まで増えます。「入力データ量は DAG node/edge に線形」という [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1759-t1742-ratification-history/s2-plan.md:147) の結論は誤りです。

破綻条件の一例は、長期運用で批准行と distinct blob が増え、単一 `cat-file --batch` の全 blob 展開が低速 object store 上で 10 秒を超える場合です。

成果物への差分: 正しい大規模台帳が `ratification git command timed out` で拒否され、certified 選択と A-2 レポートが台帳規模に応じて消失します。

### 10. must-fix — テスト計画は主要な誤実装を殺せない

提案された test (a) は、台帳導入前に分岐した親を持つ実際の F600 形を再現しており妥当です。共有 `ratified_enforcement_source` と T671 fixture も、non-shallow の 1 親導入 1 行なので新規則で壊れない構造です。[conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/tests/conftest.py:190)

不足する殺傷点は次です。

- cherry-pick/rebase による中間挿入
- 同じ行の独立な二重追加
- 3 親以上の octopus merge
- 台帳なし branch への merge 後の再 merge
- 不正遷移を中間 commit に置き、HEAD は一見正常にする履歴
- 空 graft、無関係 replace ref の偽赤
- `cat-file --batch` parser の truncated、余剰、missing object
- shallow な実受入、dispatch 経路
- `V`, `K`, blob 総量を増やす性能境界

特に全否定例を HEAD に置くと、「全 node を検査せず HEAD と親だけ検査する」誤実装が生き残ります。

成果物への差分: テストが通っても中間の不正批准を見逃す実装や、正しい octopus/cherry-pick を拒否する実装が land し、批准集合と certified lock の受理集合が履歴形状で変わります。

### 11. should-fix — revert と merge-time 批准の意味が未裁定

批准行を `git revert` して `[a,b] -> [a]` に戻す履歴は必ず拒否されます。また merge commit 自体で人間が新規行を批准しても「merge で新規行 0」のため拒否されます。

批准が永久で revocation 不可ならこれは正しい拒否です。人間による撤回や merge-time approval が正当操作なら偽赤です。削除を緩めるのではなく、revocation tombstone や別署名記録を定義すべき論点です。

成果物への差分: 未裁定のままでは人間が正しく撤回した digest も批准集合に残り続けるか、撤回 commit を含む全履歴が拒否され、どちらの場合もレポートの批准参照が人間判断とずれます。

## 構成した偽赤履歴

記号 `[a,b]` は台帳 rows、`-` は台帳なしです。

1. Cherry-pick / rebase:

```text
O[a] --- S[a,b]
  \
   T[a,c] --- D[a,b,c]
```

`D` は `T` に `b` を 1 行だけ追加し、`a,c` の順序も保存しますが、suffix append でないため拒否されます。`D=[a,c,b]` なら通るため、批准集合が同じでも conflict resolution だけで結果が変わります。

2. Revert:

```text
O[a] --- B[a,b] --- R[a]
```

`R` は正当な revocation を許す契約なら偽赤、批准が永久なら正しい赤です。

3. 同じ行の独立追加:

```text
O[] --- L[x] ----\
  \               M[x]
   --- R[x] -----/
```

これは intended merge 規則で受理可能です。plan に positive test がありません。

二つの同じ批准を逆順で独立記録すると、`L[x,y]` と `R[y,x]` の exact union を表す共通 supersequence がなくなり、正しい集合でも拒否されます。

4. Octopus merge:

```text
P1[a,b] --\
P2[b,c] --- M{a,b,c}
P3[c,a] --/
```

どの子順序も 3 親すべてを部分列として保存できません。

5. 台帳あり branch を台帳なし branch へ merge、その後再 merge:

```text
O[-] --- N[-] ---- M[a] --------\
  \             /                M2[a,b]
   L[a] -------/--- L2[a,b] ----/
```

実親数で分類すれば `M` と `M2` はどちらも受理できます。台帳を持つ親数で分類すると `M` が unary 0-add とされ、F600 が再発します。

6. ff-only land と main の反復取込み:

```text
main: M0[a] --- M1[a,b] --- M2[a,b,c]
wave:    \------ W1[a,b] ----- W2[a,b,c]
```

wave 側 merge は exact union なので受理可能で、最後に current main の descendant なら ff-only land できます。ただし「2 行目ができれば合流枝が必ず発火する」は過剰一般化です。wave が最新 main から分岐し、その後批准変更がなければ同一台帳 merge は path log に出ない可能性があります。

7. 正しい bytes の metadata 変更:

```text
P mode=100644 rows=[a]
C mode=100755 rows=[a]
```

批准集合は不変ですが plan は拒否します。

## 射程の穴と裁定パッケージ候補

1. 批准の意味

   推奨候補は「成果物上は grow-only set」とし、1 親では親列を部分列として保存し exactly one digest を追加、merge では exact union のみとする案です。行順も証拠なら、並行 branch 間の全順序を別契約で定義する必要があります。

2. enforcement の時点

   推奨候補は、D906 の偽造不能な受領証が完成するまでは certified lock の各受入、dispatch、report 前に批准を再検査する案です。受領証完成後は、その署名が lock、closure digest、批准時点を束縛するなら receipt 検証へ置換できます。

3. shallow 運用

   現時点で shallow gate 実経路は投影内にありません。新規 certification は full-history checkout 必須と明記し、計算ノードや CI が shallow を採用するときは gate 前に full fetch する案を推奨します。証拠なしに shallow を受理する案は不可です。

4. revocation

   批准は永久か、撤回可能かを裁定対象にしてください。撤回可能なら行削除を許すのではなく、対象 digest と人間権限を束縛する tombstone schema が必要です。

5. scope 拡張

   `ident.py` の新規 lock 作成だけを本 wave の契約とするなら、artifact 受入と dispatch が scope 外であることを明記し、別 task へ切り出す必要があります。「批准 gate を実装済み」と総称するのは不可です。

## 親 brief への反論

- 「merge commit を改版と数えない」は不正確です。merge は片親行の欠落や新規行混入を検査する必要があり、正しくは「merge を unary append と数えない」です。
- P3 の「誤差ゼロ」は実測から証明されていません。親資料自身が一般保証を未確認としています。
- brief の「main が 1 commit 進む positive control」は、単なる無関係な 1 親 commit なら旧実装でも path log に出ず、F600 を殺せません。plan の pre-ledger side branch を持つ merge 形が必要です。
- M5 の「親 1 個扱い 16」は plan の実親分類と矛盾し、強化後規則では再発原因になります。
- shallow 拒否は安全性には必要ですが、現時点では守る実 artifact path がありません。実運用で壊れないという根拠にはなりません。
- closure digest の変更、既存批准行の失効、D905 の実行主体未完成が残るため、「この関数を直せば A-2 が開く」という因果は成立しません。

## 総括

現 plan は現 main の F600 を直す方向としては妥当ですが、そのまま author へ渡すには不足です。最優先は、`--full-history` 完全性への未証明依存の除去、実親数による merge 分類の明文化、cherry-pickと octopus の偽赤解消、そして creation-only gate と artifact 受入の射程差の裁定です。

shallow な実運用経路は指定資料内にはありません。pytest と履歴 probe は実行しておらず、以上は指定された 13 ファイルだけによる静的所見です。