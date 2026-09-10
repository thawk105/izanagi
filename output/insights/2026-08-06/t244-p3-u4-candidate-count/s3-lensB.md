## 所見

### B-1 — real / must-fix：candidate 下限が到達不能な policy を受理する

プランは `batch_distinct_candidate_count_min` を 1 以上の整数として追加しますが、上限および他の予算値との整合検査がありません。[plan.md:63](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s2/plan.md:63) [plan.md:81](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s2/plan.md:81)

候補 wire は 5 bit なので最大 32 種です。[reflux_ir.py:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_ir.py:36) したがって candidate 下限 33 は永久に達成不能です。さらに、現行 feasibility は floor を member 下限で検査し、最大 batch 数も `qmax // batch_min` で求めます。[reflux_origin_ledger.py:303](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:303) [reflux_origin_ledger.py:2171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:2171)

例えば member 下限 2、candidate 下限 3、`qmax=2` は提案後の検査を通りますが、certifiable batch は一つも作れません。これは failures の `[自己不整合]` と `[受理集合の過剰縮小]` の再発です。[failures.md:1404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/docs/failures.md:1404)

candidate 下限を 32 以下に制限し、feasibility の実効行数下限を少なくとも `max(member_min, candidate_min)` として再計算する必要があります。32/33 と `qmax < candidate_min` の境界テストも D96 の変更単位に必要です。

**成果物影響:** 到達不能 authority が受理され、試行台帳が予算を消費しても certifiable terminal に到達できず、材料レポートと proof chain が参照すべき terminal event を生成できない。

### B-2 — real / must-fix：tombstone を数えるという受理意味論に境界テストがない

プランは tombstone row も distinct candidate 数に含めると宣言しています。[plan.md:53](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s2/plan.md:53) 一方、D166 では tombstone は未実行行であり、ledger は物理 query を観測しないと定義されています。[decisions.md:8274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/docs/decisions.md:8274) [decisions.md:8286](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/docs/decisions.md:8286)

予定テストには A/A と A/B、aggregate、aborted batch はありますが、「第2候補が tombstone にだけ現れる」境界がありません。[plan.md:207](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s2/plan.md:207) `_apply_event` だけを non-tombstone 集計へ変える変異は、codec golden が残っていても検出できません。F60 が警告する gate と負例の非対応です。[failures.md:1416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/docs/failures.md:1416)

`A accepted, A accepted, B tombstoned`、candidate 下限 2 の seal を明示的に受理する境界テストが必要です。公開 snapshot と sealed event の count も同時に固定すべきです。

**成果物影響:** tombstone を含めるか否かで同じ台帳の `OriginSealed` 受理が反転し、certified 選択集合と proof-chain terminal 参照が実装差で変わる。

### B-3 — real / must-fix：追跡済みの実行可能 consumer が改名 closure から漏れている

機械的な語彙走査結果は次のとおりです。

- standalone `cardinality`: 360 箇所、100 files
- substring `cardinality`（識別子内を含む）: 899 箇所、129 files
- `batch_cardinality_min`: 40 箇所、17 files
- `reserved_cardinality`: 13 箇所、4 files
- `_MAX_BATCH_CARDINALITY`: 146 箇所、9 files

大半の `output/insights` は歴史記録なので書き換えるべきではありません。ただし、親実測 M1 が挙げる liveness probe は現行 ledger を import する実行可能 consumer です。[parent-measured.md:10](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/parent-measured.md:10) ここは旧 manifest key を生成し、旧 snapshot field を参照しています。[liveness_probe.py:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:42) [liveness_probe.py:178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:178)

プランの編集対象にこの consumer がありません。[plan.md:117](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s2/plan.md:117) probe を現行 API に更新するか、歴史的・非実行 artifact として明示的に固定する必要があります。既存 receipt は履歴記録なので、形式的な proof として再生成を要求するものではありません。

**成果物影響:** liveness 材料の probe/receipt 参照が再実行不能になり、材料レポートの再現可能性が失われるが、既存 certified 選択値そのものは変わらない。

### B-4 — real / must-fix：名乗りが実在する発火路の上限を超えている

M5 の「P4 証拠を読む consumer は存在しない」は独立検索でも反証できませんでした。D166 も P4 証明を FAIL のままとしています。[parent-measured.md:52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/parent-measured.md:52) [decisions.md:8298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/docs/decisions.md:8298)

新 gate 自体は死んでいません。commit と replay は `_apply_event` を通るため、ledger 内の `OriginSealed` 受理では発火します。[reflux_origin_ledger.py:2941](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:2941) [reflux_origin_ledger.py:2364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:2364) しかし production authority は空で、production 初期化も禁止されているため、現時点で P4 evidence に接続する発火路ではありません。[reflux_origin_ledger.py:2781](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:2781)

それにもかかわらず親 brief は「P4 evidence acceptance」、プランは「certifiable evidence only」と名乗っています。[brief.md:37](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/brief.md:37) [plan.md:227](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s2/plan.md:227) 「certifiable `OriginSealed` acceptance」または「ledger terminal acceptance」まで弱めるべきです。

**成果物影響:** 材料レポートや proof chain が ledger 内部の terminal 受理を P4 証拠と誤引用し、証拠の値は不変でも参照の意味が偽になる。

### B-5 — real / must-fix：テスト編集 closure の件数が不足している

プランは既存 test function を 15 件としています。[plan.md:129](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p3-u4-candidate-count/s2/plan.md:129) 実際には V14 も `_MAX_BATCH_CARDINALITY` を8回参照しており、少なくとも16件です。[test_reflux_origin_ledger.py:1912](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:1912) [test_reflux_origin_ledger.py:1939](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:1939)

また、独立 abandoned-frame helper に旧 `"cardinality"` payload が残ります。[test_reflux_origin_ledger.py:248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/tests/test_reflux_origin_ledger.py:248) これは改名後に拒否される旧 wire を「独立見積り」として計算し、reserve frame を5 bytes 過小評価します。

**成果物影響:** 予算境界と受理集合を裏づける test oracle が stale または参照不能となり、その状態で生成した certified 選択・材料レポート・proof chain の受理根拠を信頼できない。

## 確認できた点

- M1〜M5、M7 に事実上の反証はありません。M6 の frozen manifest pin closure にも ledger/authority bytes はありませんでした。ただし B-3 の live probe は frozen artifact ではない別問題です。
- byte 包絡線は独立計算と一致しました。seal 2248/2249 は `1,048,300 / 1,048,766`、origin qmax 73718/73719 は `67,108,224 / 67,109,133` です。
- literal golden が壊れる test node は V01、V13、V16-salt、V21、V24 の5件で、プランはこの5件自体を認識しています。
- D96 の「新 D・実装・境界テストを同一変更単位へ入れる」という構造はあります。ただし B-1 と B-2 の受理境界が欠けるため、現状では実質的に未充足です。
- scope 外の sidecar、report v3、completeness、critic 後置、production provisioning を追加要求する裁定パッケージ候補はありません。
- pytest は実行しておらず、以上はすべて静的検査です。

## nit

- プランの `:1450` は `SealedBatch` 構築ではなく member 追加を指し、実際の構築は [reflux_origin_ledger.py:1458](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count/orchestrator/campaign/reflux_origin_ledger.py:1458) です。他にも decorator 行を class 行として示す1行ずれがあります。
- `docs/failures.md` 冒頭の型タグ一覧は9種ですが、実際の見出しには21種あります。本レビューでは実見出し側を使用しました。

## 総括

1. **NO-GO**
2. **must-fix: 5件**
3. 最も重い所見は **B-1**。到達不能な candidate policy を authority として受理できるため、gate を追加しながら certifiable terminal を永久に生成できない自己矛盾を導入します。