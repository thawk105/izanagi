静的読解のみで判定した。blocker はある。案Aは条件付きで成立するが、案Bは正式比較の代替にはならず、B→A の adaptive selection も現状案のままでは通せない。

## L1-1

**主張:** 親 brief の P1 は、SI hook を移植先でも同等の検証力を持つ先例へ一般化しており、SI 固有の冗長な read 欠落と、ERMIA の非冗長な hidden read を区別していない。

- 根拠:
  - 親は hook の存在から「2本目の展開」と一般化している: [brief.md:23–28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-s1-design-choice/brief.md:23)、[brief.md:68–69](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-s1-design-choice/brief.md:68)。
  - SI は read 後に同じ key を update/delete すると `read_set_` から消す: [si/transaction.cc:239–247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/external/ccbench/cc/si/transaction.cc:239)、[si/transaction.cc:360–366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/external/ccbench/cc/si/transaction.cc:360)。hook は最後に残った `read_set_` だけを出す: [si/transaction.cc:526–553](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/external/ccbench/cc/si/transaction.cc:526)。
  - ただし SI は snapshot 後の write があれば first-updater-wins で abort する: [si/transaction.cc:197–207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/external/ccbench/cc/si/transaction.cc:197)。したがって、この同一-key RMW read の省略だけから現行 SI の G2 false-green までは主張できない。
  - Silo は read→update 後も read element を残し、全 read を出す: [silo/transaction.cc:524–547](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/external/ccbench/cc/silo/transaction.cc:524)、[silo/transaction.cc:584–607](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/external/ccbench/cc/silo/transaction.cc:584)。加えて X/P の整合性計装も持つ: [silo/transaction.cc:390–435](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/external/ccbench/cc/silo/transaction.cc:390)、[silo/transaction.cc:608–623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/external/ccbench/cc/silo/transaction.cc:608)。
  - ERMIA には成功 read なのに `read_set_` に入らない実分岐がある: [ermia/transaction.cc:160–174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/external/ccbench/cc/ermia/transaction.cc:160)。
  - verifier の wr/rw 辺は記録された `t.reads` だけから作る: [dsg.py:81–105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/orchestrator/verifier/dsg.py:81)。

- 具体的な失敗筋書き: ERMIA に SI 型の「commit 時に最終 `read_set_` を列挙するだけ」の hook を移植する。`v_sstamp` の `else` 分岐で成功した read が、write-skew の一方の rw 辺を担っていても R 行が出ない。DSG からその辺が消え、二辺の cycle が一辺になって `serializable` へ false-green する。

- 深刻度: **must-fix**。非 serializable な候補が受理集合・fitness に入る可能性がある。段2プランは pending-read buffer と負例を要求しており、[s2-plan.md:46–52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-s1-design-choice/s2-plan.md:46)、[s2-plan.md:129–135](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-s1-design-choice/s2-plan.md:129)を削らなければ、この親 brief の一般化は修正できる。

## L1-2

**主張:** 親 brief の「verify が COMMIT 必須前段」という M3 だけでは規律2を保証せず、現行 trace v1 は部分履歴を certified にできる。

- 根拠:
  - 現 schema は C/R/W のみで、期待件数も終端 E もない: [trace.hh:17–23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/external/ccbench/include/trace.hh:17)。
  - pipeline が独立に数えるのは trace 内の C 行だけ: [pipeline.py:261–289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/orchestrator/campaign/pipeline.py:261)。
  - txid 検査は `max(txid)+1` なので末尾欠落を認識できない: [parse.py:213–223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/orchestrator/verifier/parse.py:213)。
  - 末尾 txn 全欠落と C 後の R/W 欠落が実際に `certified` になる characterization が固定されている: [test_verifier.py:601–638](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/orchestrator/tests/test_verifier.py:601)。

- 具体的な失敗筋書き: 二 transaction の write-skew trace で、txid=1 の全行、または C 以降の R/W だけが末尾切断される。run が rc=0 で少なくとも一つ C が残れば `trace-empty` ではなく、txid も密に見える。cycle の片側が消え、verifier が certified、続いて COMMIT と fitness が記録される。

- 深刻度: **blocker（採用条件）**。受理集合と性能値の両方が汚染される。段2プランの trace-v2、stdout commit 数照合、v1 再認証禁止 [s2-plan.md:23–40](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-s1-design-choice/s2-plan.md:23)を一体で入れるなら解消するが、いずれかを後送りした案Aは受理不可。

## L1-3

**主張:** 案Aは observer-effect 防壁まで一括導入しなければならず、現行の diff-of-diffs と nm は移植先の `#if TRACE` 外漏洩を検出できない。

- 根拠:
  - 現行対象は `backoff.hh` と Silo transaction に固定されている: [source_digest.py:73–82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/orchestrator/campaign/source_digest.py:73)。
  - 実際の diff-of-diffs もその固定集合だけを反復する: [source_digest.py:699–730](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/orchestrator/campaign/source_digest.py:699)。
  - 同関数自身が、`#if TRACE` 外の検証専用メタデータは判定不能と明記する: [source_digest.py:711–715](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/orchestrator/campaign/source_digest.py:711)。
  - nm は文字列 `izanagi_trace` だけを見るうえ、strip の穴も明記されている: [buildcache.py:1021–1034](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/orchestrator/campaign/buildcache.py:1021)。
  - プランは protocol-aware map と旧/new pin の TRACE=0 TU 同一検査を要求している: [s2-plan.md:71–81](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-s1-design-choice/s2-plan.md:71)、[s2-plan.md:127–141](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-s1-design-choice/s2-plan.md:127)。

- 具体的な失敗筋書き: ERMIA の pending-read vector または更新処理が誤って `#if TRACE` 外に置かれ、名前には `izanagi_trace` が含まれない。現行 diff は ERMIA source を読まず、nm も通過し、TRACE=0 perf binary に割当て・clear・コピーが残る。さらに汚染済みの新 pin を baseline にした後は、一般化済み diff-of-diffs も「汚染 pin と同じ」と判定するため、旧/new pin の TU 同一検査だけが最後の防壁になる。

- 深刻度: **blocker（導入順序条件）**。正しさ受理集合ではなく、perf 値・protocol 順位・参照 binary が変わる。protocol map、全 build 出口の CMakeCache/nm、旧/new pin の TRACE=0 同一性を同じ admission に束縛する場合のみ所見解消。

## L1-4

**主張:** 親 P2 の「certified 外と宣言すれば整合」は誤りであり、案Bが規律2と整合するのは正式比較を一切生成できないよう機械隔離した場合だけである。

- 根拠:
  - 親 P2 は宣言を十分条件としている: [brief.md:66–72](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-s1-design-choice/brief.md:66)。
  - 規律2は anomaly 候補を即失格とし、最適化圧力が正しさを攻撃する前提である: [CLAUDE.md:67–71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/CLAUDE.md:67)。
  - 段2プランは別 ledger、COMMIT/certified/fitness 禁止、公式 consumer 拒否、AST 到達不能検査を具体化している: [s2-plan.md:157–173](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-s1-design-choice/s2-plan.md:157)。
  - 現行公式 admission は runtime type だけでなく文字列 path も受けるため、型の宣言だけでは隔離にならない: [artifact_admission.py:346–351](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/orchestrator/campaign/artifact_admission.py:346)。一方、公式 `campaign.lock` と `runs/wal.jsonl` がなければ拒否する: [artifact_admission.py:577–585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/orchestrator/campaign/artifact_admission.py:577)。

- 具体的な失敗筋書き: correctness 未評価という注記を残したままでも、stock ERMIA の値を certified Silo と同じ比較表へ置き、winner、採用候補、headline の決定に使う。正しさバグで同期処理を省いて速くなった stock 値ほど選ばれやすく、対抗馬だけ verifier を免除した reward hacking になる。

- 深刻度: **blocker**。案Bを正式な段7比較として採ると、比較表の片側、winner、reference set が未認証値で変わる。段2プランの6条件 [s2-plan.md:211–220](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-s1-design-choice/s2-plan.md:211)は実効的な機構だが、それを満たしたBは「正式比較案」ではなく、非採用・非 headline の別成果物である。

## L1-5

**主張:** 案Bの「性能フィードバックに使わない」という条件と、BでAの移植先を adaptive selection する段階案は両立しない。

- 根拠:
  - Bの許容条件は variant 生成や性能フィードバックへの不使用を要求する: [s2-plan.md:213–218](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-s1-design-choice/s2-plan.md:213)。
  - 同じプランが、人間によるA移植先の選択を許す: [s2-plan.md:220–222](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-s1-design-choice/s2-plan.md:220)。
  - 第3案ではそれを明示的に `adaptive selection` と呼び、候補を絞るとしている: [s2-plan.md:230–236](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-s1-design-choice/s2-plan.md:230)。
  - 規律3は verifier 結果を毎 iteration の次手シグナルにすることを要求する: [CLAUDE.md:73–76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/CLAUDE.md:73)。

- 具体的な失敗筋書き: correctness bug で最速になった ERMIA stock をBが示し、その値で ERMIA だけをAへ移植し、MOCCを候補集合から落とす。Aの fresh rerun はB標本の再利用を防ぐが、未検証値が「何を検証するか」を既に変更しており、Aで落ちれば第二 protocol の certified 行自体が残らない。

- 深刻度: **blocker（B→A 段階案）**。false COMMIT はAが防いでも、certified 候補集合・比較対象 protocol・参照の選択が未検証性能で変わる。Bを単なる非作用的資料に限定するか、正式候補集合をBと独立に固定しない限り採れない。

## L1-6

**主張:** 案Aは structured ABORT の記録までは示すが、それを次の variant／移植修正へ実際に還流する consumer 経路を示していない。

- 根拠:
  - 新 driver の記述は `space_for()` 列挙と `pipeline.evaluate()` 呼出しまで: [s2-plan.md:93–96](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-s1-design-choice/s2-plan.md:93)。
  - プランは WAL に流すだけで規律3を維持できると結論している: [s2-plan.md:143–145](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-s1-design-choice/s2-plan.md:143)。
  - pipeline は原因を ABORT payload に保存するが、自身では次手を生成しない: [pipeline.py:908–918](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/orchestrator/campaign/pipeline.py:908)。
  - 既存の還流は `load_rejections()` が admitted WAL を読む経路: [digest.py:235–267](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/orchestrator/critic/digest.py:235)。既存 loop は評価後に明示的に critic digest を作る: [p3_s4_loop.py:1025–1035](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/orchestrator/campaign/p3_s4_loop.py:1025)。

- 具体的な失敗筋書き: ERMIA の版写像 mutant が orphan read または integrity mismatch で ABORT される。新 driver はその行を記録して次の flag/protocolへ進むだけで、どの read・版写像が壊れたかが次の hook 修正入力へ渡らない。verifier は「最後に回すゲート」に戻り、同型の失敗を繰り返せる。

- 深刻度: **must-fix**。COMMIT 受理集合は直ちには広がらないが、次手生成入力と失敗原因の参照鎖が欠落し、規律3の成果物である構造化フィードバックが機能しない。

## 所見なしとした項目

- **案Aの候補別版写像:** 所見なし。プランは ERMIA dormant の shifted cstamp [ermia/transaction.cc:548–561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/external/ccbench/cc/ermia/transaction.cc:548)と active の raw cstamp [ermia/transaction.cc:755–767](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/external/ccbench/cc/ermia/transaction.cc:755)を分離し、MOCC は protocol 自身が検証する read set [mocc/transaction.cc:888–941](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/external/ccbench/cc/mocc/transaction.cc:888)を trace source にしている。

- **案Aの最終 COMMIT 配置:** 所見なし。現行コードは全 verify pass 後だけ `res.certified=True` とし、COMMIT をその内側に閉じている: [pipeline.py:980–1027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/orchestrator/campaign/pipeline.py:980)、[pipeline.py:1071–1095](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s1-design-choice/orchestrator/campaign/pipeline.py:1071)。

- **完全隔離されたBの規律1:** 所見なし。exact clean pin、両 arm TRACE=0、別 run、CMakeCache と nm の全出口検査をすべて満たす限り、検証計装による比較の非対称は生じない。ただし L1-3 の pin 汚染検査は引き続き必要。

- **非作用的なB artifact:** 所見なし。別 basename/schemaで公式 WALを作らず、公式 consumerが機械拒否し、順位・選択・headline・後日の昇格に一切使わないなら、正しさゲートを「通過した」成果物ではないため規律2の受理集合を変えない。

## 総括

- **blocker あり。**
- 案B単独を正式な cross-protocol 比較として採ることは規律2違反。
- Bの値でA移植先を絞る段階案も、未検証性能を次手へ使うため現状のままでは blocker。
- 案Aは trace-v2、独立 commit 数照合、protocol-aware observer gateを同時導入する場合のみ成立する。
- SI hook はSI固有の先例であり、ERMIA/MOCCへの一般的な trace completeness 証明ではない。
- 案Aには structured ABORT を実際の次手へ渡す consumer 配線の追記が必要。