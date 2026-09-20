| 所見 | 判定 | 根拠 |
|---|---|---|
| should A-S1 | **closed** | [TL:9884](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-pair-launcher/orchestrator/tests/test_p3_s4_loop.py:9884)〜9971。実 gate を復元し、supply 赤／meaning 赤で拒否例外・campaign 未到達・証拠 bytes を検査。候補値20の拒否も追加。 |
| should B-S1 | **closed** | [TL:10013](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-pair-launcher/orchestrator/tests/test_p3_s4_loop.py:10013)〜10032。新 option なしの候補 main から、identity 確定後の cfg を捕捉して固定 preimage と比較。固定定数は変更なし。 |
| should B-S2 | **closed** | [TL:10216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-pair-launcher/orchestrator/tests/test_p3_s4_loop.py:10216)〜10256。layout factory の入力を記録し、両経路それぞれの campaign ID、および両経路間の一致を検査。 |
| nit B-N1 | **closed** | [TL:10086](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-pair-launcher/orchestrator/tests/test_p3_s4_loop.py:10086)〜10129。実行 helper を共有し、転送と lock 復元の検査を別 node に移した。test から別 test を呼ぶ重複を解消。 |
| should 焦点走 red 1 | **closed** | [namespace:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-pair-launcher/orchestrator/tests/test_p3_exploration_namespace.py:425)〜428。AST pin は11／2、runtime pin は1を維持。静的再集計とも一致。 |
| should 焦点走 red 2 | **closed** | [wiring:324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-pair-launcher/orchestrator/tests/test_p3_b4_wiring_probe.py:324)〜329。47→49へ更新。由来を `p2_2 + genome` とし、`source_digest` が旧閉包に既在だったことを明記。完全な閉包差の独立再集計には後述の制約あり。 |

## テストの実効

以下、TL は `test_p3_s4_loop.py`、L は `p3_s4_loop.py` を指します。

**A-S1：実 admission と拒否処理を通っています。** TL:9893で `_REAL_CONDITION_GATE` を戻し、gate 内で置換するのは下位の supply／meaning evaluator です。周辺の compiler 選択、checkout、applied、campaign は fixture／stub なので、「テスト全体で下位 evaluator だけを模擬」とまでは言えません。

record は production の `_issue_arm_record()` が発行する `ConditionArmRecord` です。同関数は構造検証と issuer capability の付与を行い、実 `require_condition_gate_family()` は exact 型・整合性を検証します（`condition_meaning_gate.py`:1076–1101、4090–4131）。meaning 赤のケースでは supply を構造的に有効な green にしており、supply 赤に隠れた拒否ではありません。

L:462–513の admission・証拠保存・例外まで実処理です。TL:9890–9892で evidence directory と環境変数を用意し、TL:9967–9971で両 arm と admission の保存 bytes を比較します。`evidence_write_failures` 不在も検査しています。

stock は実 main→実 stock 関数を通ります。実呼出し先 `L.run_campaign` の spy が呼ばれれば `calls` に追加されるため、TL:9959の空配列検査が未到達を保証します。候補値20は gate の直接呼出しによる拒否回帰検査であり、候補 main 全体の未到達検査ではありません。

**B-S1：捕捉位置は identity 確定後です。** `--no-build --value 20` は新 option を使いません。spy は layout factory 自体ではなく `_run_one_iteration_resolved` の入口ですが、L:3225–3231で policy／knowledge を束縛し、L:3352で同じ cfg から layout ID を計算した直後、L:3354–3358でその cfg を渡しています。現在のコードでは campaign 境界の cfg 観測として有効です。`--no-build` なので実 `run_campaign` には進みません。

B-S2 は factory の入力も独立に観測するため、fixture が常に同じ layout を返すことによる見逃しを閉じています。

B-N1 は両 node の名前と従来の期待値を維持しています。lock 専用 node は `records / threads / perf_workload / extime / reps` から `PerfConfig` を復元し、verify mode と evaluate 境界の `extra_correctness` を照合します。

## 件数・inventory・残存失敗

decorator の case 数を静的に数え、次を確認しました。

| 対象 | 統合1 | 統合2 |
|---|---:|---:|
| TL 全体 | 550 | 553 |
| 新 gate 拒否 test | 0 | 2 |
| lock 復元 test | 1 | 2 |

したがって **550＋2＋1＝553** です。`value in (-1, 20)` は test 内ループなのでケース数を倍増させません。これは「553 passed」という報告の件数との整合確認であり、成功の再実証ではありません。

AST 再集計は layout **11**、`run_campaign` **2**。追加された呼出しは L:3245と1986です。layout 用 cfg は `build_context.policy` に束縛済みで、campaign 呼出しにも `build_context` が明示されています。候補 runtime では stock 分岐を通らないため、runtime pin の1も整合します。

赤1のログが直接示すのは `11 == 10` の失敗です。そこで停止していた後続の `run_campaign` pin も、現物の2件に合わせて更新されています。赤2のログは `49 == 47` で、更新先49と一致します。

閉包コメントも読めたコードと整合します。L:98の新しいトップレベル import から `p2_2`、その `p2_2.py`:35から `genome` が加わります。`source_digest` は旧来の `pipeline` 経由で到達します。`_load_static_modules()` は関数内 import を除いた再帰閉包を追うため、この説明は妥当です。fix2 報告の `partial` は指示文の module 名との相違ですが、事実に合わせた訂正自体は未了ではありません。ただし **exact な追加2件・削除なしの全閉包比較は、今回は独立再集計を完了していません。**

残存失敗は wiring:1524–1542の `git status --short` に対する許可集合検査です。子の未commit変更に TL と namespace test が含まれれば失敗します。clean な統合作業木では `changed == set()` となり、この assertion の失敗原因は消えます。今回の `git status --short` も空でした。

## README の整合と nit

[README:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-pair-launcher/tools/pegasus/README.md:373)〜392は、次の主要契約と整合しています。

- 未設定／0は既定の1起動、1は候補後にstockを起動し、空値・他値は早期拒否。
- stock argv は同 receipt・manifest・宣言値を受け取り、coder authority／role・候補値・proposal を受け取らない。
- 候補失敗後もstockを試み、候補非零を優先してrcを集約。EXIT trap の `driver_rc` にも同値が入る。
- stock 成功は certified・非 aborted と variant／STOCK token の確認に依存し、skip はrc1で復元しない。
- pair 成立をjob rc／campaign IDから認定せず、実 compiler の STOCK 成立も未測定と明記。

`stock-baseline` admission や B-5 全体の完成を含意する記述は見つかりません。

**nit C-N1：digest 更新条件を補うと正確です。** README:386の「stock 後に再生成」は無条件に読めますが、[L:2013](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-pair-launcher/orchestrator/campaign/p3_s4_loop.py:2013)では「skip でなく、WAL record が存在する場合」に更新します。「stock が skip でなく WAL が存在する場合、admitted view から再生成する」への修正が適切です。実装変更を要する不具合ではありません。

対象 fence は402–417の1個、qsub行は416の1本です。同行の契約対象5 env名は各1回で、stdout／stderr の evidence 出力先も維持されています。`test_readme_tagged_qsub_fence_routes_both_streams_to_evidence` の文面契約と整合します。

## 退行と変更範囲

fix2 のtest差分で、既存期待値の変更は inventory pin 2箇所だけです。verify／lock の assert は専用 node へ移動しており、期待値の緩和・反転・skip追加はありません。固定 preimage は両統合commit間で一致しました。

統合commit間の変更は **test 3 file＋親のREADME**。production の変更はありません。

## 総括

**must-fix：0件。GO。** 指定6所見はclosed。新規指摘はREADMEの条件省略というnit 1件です。pytest・ファイル書込みは行っておらず、実走成功・実 compiler のSTOCK成立・pair測定成立は認定していません。

閉包差分とfenceの自動再集計は、PreToolUse hookが「未登録Pegasus実行体／ログインノードの実行制限」を理由に拒否しました。その部分は独立再実測済みとせず、静的照合の範囲で判断しています。