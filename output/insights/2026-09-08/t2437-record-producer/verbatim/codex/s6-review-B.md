## B-1: terminal WAL 結合が発行 record まで閉じていない

**主張:** A-1 の検査は `derive_physical_result()` の引数内だけで成立し、発行 record が参照する ordered-WAL と結合されていない。`DerivedPhysicalResult` も直接構築可能である。

**根拠:** derive は生の `ordered_wal_records` から結果だけを返す [reflux_result_evidence.py:488](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:488)。assembler はその結果と任意の `ordered_wal_ref` を独立に受ける [reflux_result_evidence.py:694](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:694)。issuer は参照 bytes の存在と digest しか検査しない [reflux_result_evidence.py:858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:858)。テスト自身も derive を経ず dataclass を直接構築する [test_reflux_result_evidence.py:748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_result_evidence.py:748)。同じ attempt ID の別 projection を参照させれば FC01/FC04/FC05B を通過後、terminal stage または snapshot 不一致で FC07 になる [reflux_formal_consumer.py:1133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:1133)。

**帰結:** producer API が consumer 不受理の record を正常発行でき、A-1 の成果物保証が caller の慣習に退化する。

**推奨:** must-fix — derive token に projection digest を束縛して assembler で一致確認するか、issuer が projection を resolve・parseしてその records から derive する統合経路にする。同一 attempt の別 terminal ref 負例も追加する。

**確度:** real 確定。

## B-2: 統合経路は P6 へ届くが B-5 docstring が欠落

**主張:** 統合テストの物理経路は静的に正しい。一方、docstring は salts の未行使しか書かず、裁定された「synthetic source 束縛限定・production 到達性を示さない」を明記していない。

**根拠:** 新しい sibling tree を使う [test_reflux_formal_consumer.py:818](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_formal_consumer.py:818)。33件すべてが production derive/assemble を通る [test_reflux_formal_consumer.py:839](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_formal_consumer.py:839)、[同:923](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_formal_consumer.py:923)。sealed member は canonical raw bytes を渡して作る [同:945](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_formal_consumer.py:945)。`evaluate_formal_origin()` は FC07 検査後にのみ P6 を返す [reflux_formal_consumer.py:1445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:1445)、[同:1480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:1480)。しかし docstring は salts と ledger replay のみ [test_reflux_formal_consumer.py:813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_formal_consumer.py:813)。

**帰結:** 受理集合への影響はないが、テストが証明する範囲を production 到達性へ誤読できる。

**推奨:** must-fix — docstring に synthetic Silo source 束縛限定であり production issuer 到達性を証明しない旨を追記する。

**確度:** real 確定。

## B-3: 新規24 nodeid が受入所要台帳に未登録

**主張:** 新規 nodeid は24件で、現在の台帳には1件も追加されていない。

**根拠:** 静的AST計数は `test_reflux_result_evidence.py` が14定義・23 nodeid、consumer側が1 nodeid。既存台帳は旧consumer nodeから続き [acceptance_duration_ledger.json:11503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/acceptance_duration_ledger.json:11503)、新名称のhitは0件だった。coverage gate は実collectionを分母にして90%のみ要求する [test_acceptance_schedule_order.py:704](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_acceptance_schedule_order.py:704)。作者もcollection未実走を明記している [s5-author.md:123](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/s5-author.md:123)。

**帰結:** 分母だけ24増え、集約90% gateが通っても新規nodeのexact pinは未成立のままになる。

**推奨:** must-fix — 親が実collectionとJUnit実測後に `--add-only` で24件を追加する。実測前の推定値登録はしない。

**確度:** real 確定。

## B-4: fixture・golden・record bytes は不変

**主張:** fixture builder、baseline、golden 4個、`wal.py`、`pipeline.py`、verifier、docsに差分はない。同じ入力の producer record と fixture builder record は、accepted の `null` を含め byte exact に一致する。

**根拠:** builder と production はともに sorted・compact・UTF-8・末尾LFなしで canonicalizeする [reflux_origin_fixture_builder.py:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/reflux_origin_fixture_builder.py:94)、[reflux_result_evidence.py:730](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:730)。golden 4個は不変 [test_reflux_result_evidence.py:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_result_evidence.py:31)、baseline は1848 bytes・同じSHA-256 [reflux_origin_fixture_baseline.json:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/reflux_origin_fixture_baseline.json:23)。読取専用の純関数照合でも rejected/accepted とも dict・bytes一致を確認した。

**帰結:** 現物ではFC01/FC04の変化はない。仮にraw bytesだけ違えばdigest pairでFC01、member digestを追随させても写像fieldが違えばFC04で落ちる [reflux_formal_consumer.py:630](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:630)、[同:803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:803)。

**推奨:** nit — 追加修正なし。

**確度:** real 確定。

## B-5: witness digest は WAL 往復後も同一

**主張:** consumer と producer は同じ shared digestを使用し、受理可能な anomaly で key順、list順、int/float、Unicode escapeによる乖離はない。

**根拠:** `result_to_dict()` はversion tupleをlistへ投影する [report.py:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/verifier/report.py:17)。canonical JSONはkey sort、`ensure_ascii=False`、compact encoding [reflux_origin_artifacts.py:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_origin_artifacts.py:55)。WAL writerもUTF-8の非escape表現を使い [wal.py:424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/wal.py:424)、consumerはparse後の値を再canonicalizeする [reflux_result_evidence.py:1035](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:1035)。list順は保持され、object順はsortで消える。`1`と`1.0`はparse後も型が異なり、cycle・edge・versionのfloatはexact-int検査で拒否される [reflux_result_evidence.py:327](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:327)。

**帰結:** producerのconstraint digestとFC07が再計算するdigestは同じ受理集合上で一致する。

**推奨:** nit — 任意で非ASCIIのreason keyを使うWAL往復回帰例を追加するとUnicode面のpinが明示的になる。

**確度:** real 確定。

## B-6: pin閉包とscopeは台帳以外維持

**主張:** 新module、新test file、xdist group、role、gate、一般化、S3、pipeline配線、provenance issuerは増えていない。変更は所有4ファイルだけである。

**根拠:** `git status --short` は次の4行だけだった。

- `orchestrator/campaign/reflux_formal_consumer.py`
- `orchestrator/campaign/reflux_result_evidence.py`
- `orchestrator/tests/test_reflux_formal_consumer.py`
- `orchestrator/tests/test_reflux_result_evidence.py`

15-file AST走査は `reflux_result_evidence.py` を既に含む [test_reflux_formal_consumer.py:2279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_formal_consumer.py:2279)。両test fileは既存allowlist内 [README.md:144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/README.md:144)。fixture baselineの独立再計算も維持される [test_reflux_origin_fixture_builder.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_origin_fixture_builder.py:107)。

**帰結:** 台帳未登録を除き、pin集合・role集合・production surface・参照bytesへの波及はない。

**推奨:** scope 外 — S3、production caller、追加gate・台帳一般化を本修正へ混ぜない。

**確度:** real 確定。

## B-7: 作者報告のnodeid数と未実走表記は整合

**主張:** 新規24 nodeid一覧と変異表に、存在しないnodeidや数え違いはない。未実走の必須pytestを緑とした箇所もない。

**根拠:** 現物は23 nodeid [test_reflux_result_evidence.py:542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_result_evidence.py:542) と統合1件 [test_reflux_formal_consumer.py:813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_formal_consumer.py:813)。M1からM14の各名称とM-C1の既存testは実在する。報告は必須束を「0件、rc=16」 [s5-author.md:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/s5-author.md:20)、新規24件をcollection未実行 [同:52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/s5-author.md:52) と明記している。verifier 105件等の実走主張はworktreeだけでは追認不能なので、本レビューの緑判定には数えていない。

**帰結:** 報告上の偽緑はないが、実collection・pytest受入は依然として未成立である。

**推奨:** nit — 現在の未実走表記を親の受入完了まで維持する。

**確度:** nodeid整合はreal確定、過去の実走主張は未検証。

## 裁定×実装 対応表

| 裁定項目 | 現物 | 判定 |
|---|---|---|
| A-1 terminal WAL結合 | derive内部ではreason・snapshot・attemptを照合 | 部分。record refとの結合欠落、B-1 |
| A-3 drift comment | [reflux_result_evidence.py:482](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:482) | 充足 |
| A-3 exact型負例3件 | bool、cycle bool、version float [test_reflux_result_evidence.py:674](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_result_evidence.py:674) | 静的に充足、未実走 |
| A-4 shared構造検査+digest | [reflux_result_evidence.py:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:320) | 充足 |
| consumer wrapperとFC07変換 | [reflux_formal_consumer.py:1102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_formal_consumer.py:1102) | 充足 |
| P4 typed issuance refusal | [reflux_result_evidence.py:222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:222) | 充足 |
| 3方向 derive | [reflux_result_evidence.py:488](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:488) | 局所APIとして充足 |
| 9-key assembler | [reflux_result_evidence.py:694](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:694) | 充足 |
| resolve先行issuer | [reflux_result_evidence.py:858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/campaign/reflux_result_evidence.py:858) | 仕様どおり。ただしB-1 |
| B-1 新tmp evidence tree | [test_reflux_formal_consumer.py:818](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_formal_consumer.py:818) | 充足 |
| B-2 salts未行使 | [test_reflux_formal_consumer.py:816](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer/orchestrator/tests/test_reflux_formal_consumer.py:816) | 充足 |
| B-5 synthetic限定 | test名のみ明示、docstring欠落 | 未充足、B-2 |
| B-7既存pin | 15-file AST、plain-runner、fixture baseline維持 | 充足 |
| 新規nodeid台帳 | 24件すべて未登録 | 未充足、B-3 |
| S3を実装しない | 該当差分なし | 充足 |
| fixture/golden/WAL/pipeline不変 | `git diff --exit-code` rc=0 | 充足 |
| scopeを所有4fileに限定 | `git status --short` 4行のみ | 充足 |

## 総括

must-fixは3件: WAL-ref結合、B-5 docstring、親側の24 nodeid台帳追加。  
最重はA-1が発行recordまで閉じず、producerがFC07不受理recordを書ける点。  
fixture/golden bytesとwitness digestの同一性、33件のP6到達構造は支持する。  
pytestは実行しておらず、緑とは判定していない。  
現状の実装は支持しない。B-1修正と残る受入作業後に再レビューが必要。