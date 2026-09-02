## 総括

**差し戻し。最重要は、旧実行記録の未裁定 U11 を落としたうえ、同じ ID を anti-replay 問題へ再利用している点である。**
加えて U7 を根拠なく「解決済み」とし、継承した DBLP 二重判定と矛盾している。
catalog 本体は生成器と byte 一致し、schema・件数・論理式・shard 境界に契約外の差はなかった。
裁定が要求した「整列キー非単射」のテストは、名前に反して衝突を作っておらず未充足である。
pytest は未実走。`check_docs.py` は実走して「違反なし」、schema・AST・JSON・catalog は静的検査のみ行った。

## 所見

### 1. must-fix — 未裁定 U11 が消え、別問題へ ID が再利用されている

- **主張:** 旧実行記録の U11「同じ work ID が頁境界で重複する場合の条件 5」を継承せず、新版では U11 を anti-replay の問いへ再利用している。
- **根拠:** 旧 U11 は [prior-execution:233](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2091-openalex-cond1-order/verbatim/prior-execution-2026-08-30.md:233)。段 3 は別裁定なしに U11 を落とさないよう要求している [stage3-coherence:107](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2091-openalex-cond1-order/artifacts/dev-wave-t2091-openalex-cond1-order/stage3-coherence.md:107)。一方、新 amendment の継承表は U9 までしか残さず [new amendment:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2091-openalex-cond1-order/docs/related-work/claim-survey/2026-09-02-axis1-search-amendment.md:88)、新版 U11 は anti-replay である [new amendment:221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2091-openalex-cond1-order/docs/related-work/claim-survey/2026-09-02-axis1-search-amendment.md:221)。
- **帰結:** 「U11」の参照先が二義的になり、arXiv 重複 ID の未裁定事項が解決記録なしに消える。
- **確度:** 現物で確認した。
- **成果物への影響:** 凍結 successor の裁定台帳が未決事項を保存できないため、U11 の旧意味を別 ID へ退避するか継承してから発行する必要がある。

### 2. must-fix — U7 を「閉じた」とする記述が継承契約と矛盾する

- **主張:** 二つの判定を併記しただけでは U7 は解決していない。
- **根拠:** 新 amendment は U7 を「旧実行記録が両判定を併記して閉じた」とする [new amendment:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2091-openalex-cond1-order/docs/related-work/claim-survey/2026-09-02-axis1-search-amendment.md:88)。しかし旧実行記録は「どちらを正とするか人間の裁定」と明記し [prior-execution:116](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2091-openalex-cond1-order/verbatim/prior-execution-2026-08-30.md:116)、U7 自体にも「決めていない」とある [prior-execution:229](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2091-openalex-cond1-order/verbatim/prior-execution-2026-08-30.md:229)。さらに新版が引き継ぐ旧 §10.3 も同じ未裁定状態を規定する [prior-amendment:517](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2091-openalex-cond1-order/verbatim/prior-amendment-2026-08-29.md:517)。
- **帰結:** DBLP の登録 tokenizer と legacy literal echo のどちらを最終判定に使うか、同一契約内で決まっているとも未決とも読める。
- **確度:** 現物で確認した。
- **成果物への影響:** 新 epoch の DBLP 完走判定の正本が一意にならないため、U7 を未決として残すか、実在する人間裁定を引用する必要がある。

### 3. must-fix — U13 の file/byte 数は「追加分」と「拡張後総量」を混同している

- **主張:** `2,258 file / 102,738,024 bytes` は旧 epoch 4 path の量ではなく、既存凍結集合を含む拡張後総量である。
- **根拠:** `git ls-tree -r -l HEAD` 実測では、U13 が列挙する旧 amendment・catalog・実行記録・bundle は **2,130 file / 99,925,266 bytes**。既存 `FROZEN_PREDECESSOR_PATHS` は **128 file / 2,812,758 bytes**で、合算して初めて **2,258 / 102,738,024**になる。新版は列挙した旧 epoch 物自体の「計」として後者を書く [new amendment:223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2091-openalex-cond1-order/docs/related-work/claim-survey/2026-09-02-axis1-search-amendment.md:223)。
- **帰結:** 裁定者が追加費用と最終検査集合の総費用を区別できない。
- **確度:** 現物で確認した。
- **成果物への影響:** U13 を「追加分 2,130 / 99,925,266、拡張後総量 2,258 / 102,738,024」と訂正する必要がある。

### 4. must-fix — 「整列キー非単射」のテストが衝突を作っていない

- **主張:** `distinct-sort-keys-remain-distinct` は通常の値差しか検査せず、裁定 F4 の非単射ケースを満たさない。
- **根拠:** 裁定は非単射の負例追加を明示する [stage4-ruling:12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2091-openalex-cond1-order/stage4-ruling.md:12)。追加ケースは `alpha,beta` 対 `charlie,alpha` である [test_axis1_search_runner.py:452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2091-openalex-cond1-order/orchestrator/tests/test_axis1_search_runner.py:452)。実関数で算出すると `alpha` と `charlie` の `_openalex_oqo_sort_key` は異なり、`alpha_charlie_key_collision=False` だった。
- **帰結:** 選択的に衝突する整列キーへの退行を、この名前のテストは拘束しない。
- **確度:** 現物で確認した。
- **成果物への影響:** 裁定 §4.7 の受入被覆が未完成なので、実際に同一 sort key となる異なる node を用いた検査が必要である。

## epoch 波及の独立検算

- 旧 epoch `AX1-20260829-E1`: 1,546 file。1,545 file は旧凍結物・`output/insights/`・archive・歴史文書で、残る 1 file は新 amendment の「旧 epoch を継続しない」という意図的参照だった。
- 旧 catalog path: 768 file。歴史物 766 file、残る 2 file は README の旧行と新 amendment の入力 path だった。
- 旧 amendment path: 8 file。新 catalog／generator の `supersedes`、README、新 amendment の入力参照を含め、すべて意図的だった。
- 短縮 ID、日付断片、parametrized node ID、duration ledger key も検索した。active な production/schema/test pin に旧 epoch の取り残しはない。runner の fallback は新 epoch 16 箇所だった。
- `output/insights/**`、`docs/archive/**`、旧 amendment/catalog/execution に `git diff` はなく、書き換えてはならない歴史物は不変だった。
- 新 catalog は 1,286,495 bytes、SHA-256 `8e23d63a799c8ab9d25151012c34bc738dbb422ac3dfb237999c359137c816ab`。`render_catalog_json()` と byte 一致し、Draft-07 schema error は 0。
- 実測件数は logical 267 / leaf 263 / aggregate 3 / exclusion 1。旧 catalog に epoch・amendment path・`supersedes` の許可変更だけを施した文書と JSON 全体が一致し、論理式・request・shard 境界の差はなかった。

## 新 amendment の検査

旧 §8 の五要件は、文面上はすべて存在する。

| 要件 | 検査結果 |
|---|---|
| 新しい日付の文書 | 2026-09-02 の新規 file |
| 新 epoch | `AX1-20260902-E1` |
| 新 query ID | 267 ID 全件が新 epoch。旧 ID なし |
| 全枝の再実行 | §4 で明記。旧 183 leaf も算入しない |
| 独立レビュー | §4 に段 3・段 6 review の記載あり。ただし本レビューは must-fix を返すため、修正反映後の確認が必要 |

逐語継承について、catalog は許可差分以外が旧版と完全一致し、枝・shard・DBLP echo は変わっていない。§9 の母集合外一覧、§6 の control／補助探索／感度監査、条件 2〜6、§7.1 導出式、§8 停止条件、§10.3 DBLP 二重判定も参照継承されている。ただし、所見 1・2 のとおり裁定台帳部分がその継承と矛盾する。

限界記述は、以下について実装と一致した。

- 任意 bundle path を受け、新規 bundle を強制しない。
- 旧生応答の再包装を機械的に拒否しない。
- quota 判定は `reset_seconds` を使わない。
- schema const 更新により旧 bundle を HEAD checker で検証できない。
- 未実装 schema 層は classification / work-family / controls / supplemental / sensitivity の 5 層。

92 頁は一次 artifact の `pages_compared=92`、`identical_modulo_ordering=92`、`genuinely_different=0` と一致し、同 artifact の `what` だけが 78 と書くという開示も正しい。数値上の不一致は所見 3 の U13 だけだった。

## 裁定の実装漏れ

1. `validator.py` の再帰 canonical 化・重複 member 拒否・docstring更新: **実装済み**。
2. `runner.py` の重複 member 拒否・fallback literal 16 箇所: **実装済み**。
3. `catalog.py` の epoch・amendment・直前 `supersedes`: **実装済み**。
4. schema 3 本の epoch/path/説明更新: **実装済み**。
5. validator/check/run CLI の既定 path: **実装済み**。
6. generator 由来の新 catalog: **実装済み、byte 一致**。
7. テスト・mutation node pin・duration ledger: **一部未実装**。同一 join flatten、空文字列、重複 member 等はあるが、整列キー非単射の実効テストが欠ける。

scope 外項目への逸脱は検出しなかった。`FROZEN_BASE_COMMIT` / `FROZEN_PREDECESSOR_PATHS`、epoch 欠落 gate、anti-replay、出力先防護、quota gate、versioned schema dispatch、歴史 bundle は変更されていない。

追加は軽量な 21 node で、既存 ledger の同種 node は約 0.001 秒であるため、静的見積りは実行時間で約 0.02〜0.1 秒、pytest 配送込みでも受入 walltime への増分は 1 秒未満と見込む。18 秒の凍結検査は変更されていない。ledger は旧 node ID 3 件を同じ 0.027〜0.028 秒で改名し、`nodeid_count == 19,519` は維持している。新規 test file はないため file 列挙 meta-test の集合は不変。これらは実測ではなく静的推論であり、pytest は未実走である。