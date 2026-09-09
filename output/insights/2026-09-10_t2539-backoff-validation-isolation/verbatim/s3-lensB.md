## real 所見

1. **静的非交差から既存 1 group の認証転用へ含意が飛躍している。**  
   何が壊れるか: checker が証明するのは編集 region と静的 call closure の非交差だけであり、「未実行の backoff 条件も既存認証で覆われる」とは言えない。brief はこの二つを直接接続している。[brief.md:5](/home/SFC/tanab/.claude/jobs/4edef424/tmp/t2539/brief.md:5)、[brief.md:9](/home/SFC/tanab/.claude/jobs/4edef424/tmp/t2539/brief.md:9)、[s2-plan.md:81](/home/SFC/tanab/.claude/jobs/4edef424/tmp/t2539/s2-plan.md:81)、[s2-plan.md:108](/home/SFC/tanab/.claude/jobs/4edef424/tmp/t2539/s2-plan.md:108)。  
   反例または飛躍: `Backoff::backoff()` は abort cleanup 後に呼ばれるため、待ち時間を 0 と長時間で変えれば、次の transaction が読む版、lock 競合、validation の成功と失敗の系列が変わる。[transaction.cc:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/transaction.cc:27)、[transaction.cc:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/transaction.cc:47)、[transaction.cc:449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/transaction.cc:449)。しかも実際の D2 は完全形式証明を外し、trace ベースの確率的検証を採用しているため、schedule 全称の根拠はない。[decisions.md:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/docs/decisions.md:22)、[decisions.md:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/docs/decisions.md:29)。  
   直し方: checker を認証標本削減の十分条件にしない。全 schedule への転用には別の普遍的な schedule-closure 論証が必要であり、それが scope 外なら verdict を静的非交差だけに限定する。

2. **checker は「純 timing」を証明しない。**  
   何が壊れるか: `PASS` は closure 外の編集内容の副作用を検査しない。CLI は一般の patch を受け、`abort()` と `Backoff::backoff()` を closure 外として固定する。[s2-plan.md:43](/home/SFC/tanab/.claude/jobs/4edef424/tmp/t2539/s2-plan.md:43)、[s2-plan.md:89](/home/SFC/tanab/.claude/jobs/4edef424/tmp/t2539/s2-plan.md:89)、[s2-plan.md:136](/home/SFC/tanab/.claude/jobs/4edef424/tmp/t2539/s2-plan.md:136)。  
   反例または飛躍: `abort()` の `write_set_.clear()` を削る patch は次 transaction の状態を汚染し得るが、現在の判定式では closure 外なので PASS になる。[transaction.cc:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/transaction.cc:38)。正例 patch が実際に local な待ち時間計算だけを変えることは読めるが、その純性は checker の結論ではない。[silo-backoff-fixed.patch:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/patches/silo-backoff-fixed.patch:58)。  
   直し方: exact な登録 patch の digest に限定した判定であることを出力に含めるか、「純 timing」は別の副作用検査または人手根拠と明示する。一般 patch に対する PASS を acceptance と呼ばない。

3. **`commit()` 除外は、validation 判定の実効性を覆うには狭すぎる。**  
   何が壊れるか: `commit()` は単なる無関係な caller ではなく、validation の返値が write を許可する唯一の直近 consumer である。[transaction.cc:706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/transaction.cc:706)。  
   反例または飛躍: `if (validationPhase() || true)` のように変えても validation closure 自体は同じで、commit region は計画上の V 外なので PASS になる。  
   直し方: 広い「validation enforcement」主張を残すなら、`commit()` の callsite と validation 結果から `writePhase()` への control edge を別 boundary として含める。含めないなら「callee の下向き閉包だけ」と verdict に明記する。正例 patch は `commit()` を触らないため、この追加で理由なく赤にはならない。

4. **`writePhase()` 除外は、正しさ非改変の根拠としては狭すぎる。**  
   何が壊れるか: validation 成立後でも、version 決定、tuple 更新、unlock は serializability の実装そのものである。[transaction.cc:557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/transaction.cc:557)、[transaction.cc:640](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/transaction.cc:640)、[transaction.cc:658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/transaction.cc:658)。  
   反例または飛躍: UPDATE の `storeRelease` を削る patch や、lock を保持せず write する patch は validation 本体を変えずに正しさを壊すが、現計画では PASS になる。  
   直し方: 「correctness logic に触れない」と主張するなら `writePhase()` を success sink として別 boundary に含める。純粋な validation closure 検査に留めるなら、write/writeback 正しさを非保証として出力する。

5. **brief が指す decision の識別子と行根拠が stale で、checker は置換根拠にならない。**  
   何が壊れるか: `docs/decisions.md:403` は D2 ではなく D22 である。実際の D2 は 22 行目、D22 は 395 行目から始まる。[decisions.md:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/docs/decisions.md:22)、[decisions.md:395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/docs/decisions.md:395)。さらに D22 の `transaction.cc:517-540` は現在 wal/update で、commit trace は 584 行以降に移り、現在は epoch/tid だけでなく R/W と lock coverage も記録する。[transaction.cc:517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/transaction.cc:517)、[transaction.cc:584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/transaction.cc:584)、[transaction.cc:618](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/transaction.cc:618)。no-wait 即 abort の現在位置も 160-164 行であり、D22 の 154-157 は外れている。[transaction.cc:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/transaction.cc:160)。  
   直し方: 本 checker は D22 の「コード編集面非交差」という一部分を補強する、と位置づける。verifier 可視性、workload の競合被覆、P2-4 実測を調べないため D22 全体の根拠置換とは書かない。D22 の参照更新は scope 外の裁定パッケージ候補にする。

6. **`PASS` と `accepts` の語り口が、規律 2 を弱める根拠に転用される。**  
   何が壊れるか: plan は rc 0 を単に `PASS`、正例 test を `accepts_registered_backoff_patch` と命名し、brief はこれを未認証条件を増やさない根拠にする。[s2-plan.md:49](/home/SFC/tanab/.claude/jobs/4edef424/tmp/t2539/s2-plan.md:49)、[s2-plan.md:132](/home/SFC/tanab/.claude/jobs/4edef424/tmp/t2539/s2-plan.md:132)、[brief.md:9](/home/SFC/tanab/.claude/jobs/4edef424/tmp/t2539/brief.md:9)。  
   反例または飛躍: 後続の利用者が PASS を「correctness verified」と解釈し、実行した variant の anomaly を無視したり、認証を省略できる。  
   直し方: verdict 名を `NO_STATIC_VALIDATION_CLOSURE_INTERSECTION` 相当にし、非保証を機械可読 evidence に含める。実走で anomaly を検出した variant は、この verdict に関係なく即 reject することを明記する。

## refuted 所見

- **sort comparator を閉包に含める判断は妥当。** `std::sort` は `write_set_` の順序を決め、その直後に同じ順序で lock を取る。[transaction.cc:408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/transaction.cc:408)、[transaction.cc:437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/transaction.cc:437)。実 comparator は `WriteElement::operator<` である。[silo_op_element.hh:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/include/silo_op_element.hh:67)。strict weak ordering 違反は順序だけでなく未定義動作と lock coverage 破壊につながることも現 source が明記している。[transaction.cc:391](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/external/ccbench/cc/silo/transaction.cc:391)。これは広すぎる closure ではない。

- **入力を指示として解釈する経路は、提示 plan からは認められない。** patch は UTF-8 unified diff のデータとして解析され、rename、path traversal、binary 等を拒否する。[s2-plan.md:13](/home/SFC/tanab/.claude/jobs/4edef424/tmp/t2539/s2-plan.md:13)。source のコメント、文字列、literal は構文解析前に除去される。[s2-plan.md:22](/home/SFC/tanab/.claude/jobs/4edef424/tmp/t2539/s2-plan.md:22)。patch コメントを意味判定や命令として採用する設計ではない。

- **既存策だけで validation 非交差まで証明済み、という疑いは否定した。** `condition_meaning_gate.py` は supply と限定的 branch/runtime witness を持つが、動的到達性や correctness を証明しないと明記する。[condition_meaning_gate.py:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/orchestrator/campaign/condition_meaning_gate.py:12)、[condition_meaning_gate.py:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/orchestrator/campaign/condition_meaning_gate.py:19)。`source_digest` は identity と許可 path の防壁であり、call relation の証明ではない。[source_digest.py:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/orchestrator/campaign/source_digest.py:95)、[source_digest.py:2337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/orchestrator/campaign/source_digest.py:2337)。

- **正例 patch が validation/lock 実装を直接編集する疑いは否定した。** 実編集は CMake の define 供給と `Backoff::backoff()` 内の待ち時間選択である。[silo-backoff-fixed.patch:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/patches/silo-backoff-fixed.patch:19)、[silo-backoff-fixed.patch:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/patches/silo-backoff-fixed.patch:48)。問題は直接編集ではなく、そこから動的な認証転用へ進む含意である。

## verdict 文言の提案

`PASS` は、「指定 source revision と指定 patch の in-memory post-imageについて、checker が扱える raw-config union call graph上で `TxExecutor::validationPhase` を根とする下向き閉包と、編集 function regionおよび変更 TU macro参照との静的交差を検出しなかった」ことだけを意味する。thread interleaving、validation 判定系列、abort/retry lifecycle、`commit()` による判定消費、`writePhase()`、serializability、動的 anomaly 不在、または他 group の認証転用は証明しない。実走で anomaly を検出した variant はこの結果にかかわらず即 reject し、`ERROR` は PASS と扱わない。

## 親 brief への異議

- `docs/decisions.md:403` を D2 と呼ぶのは誤りで、対象は D22。実際の D2 は完全形式証明を scope 外とする決定であり、むしろ 1 group から全 interleaving へ一般化できないことを補強する。
- worklog entry 1406 自体が「違う schedule の再サンプリングで、13 設定の保証は 1 設定とほぼ同じ」と既に断定している。[worklog.md:1330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/docs/worklog.md:1330)。本 wave はこの断定を機械化できず、静的非交差という狭い補助根拠しか追加できない。
- 「既存策不足」という結論自体は正しいが、証拠一覧は不完全。既存 `p3_s4_loop` は coder 編集を template 適用後の backoff hole に閉じ、構造検疫と grammar gate を通している。[p3_s4_loop.py:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/orchestrator/campaign/p3_s4_loop.py:30)、[p3_s4_loop.py:604](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2539-validation-isolation/orchestrator/campaign/p3_s4_loop.py:604)。これは validation 非到達を証明しないが、編集面制約と macro meaning は既存策、今回の新規性は両者と validation closure の静的な接続に限られる。
- brief の current source anchor、`validationPhase=383`、`commit=706`、abort 内 backoff call=47、leader call=720 は確認でき、ここは refuted である。

## 総括

checker は有用な静的非交差証拠にはなるが、既存 1 group 認証を未実行 schedule へ拡張する licence にはならない。  
P1-a は comparator が妥当、`commit()` と `writePhase()` は広い正しさ主張には狭すぎる。  
静的読解のみであり、テスト緑は主張しない。