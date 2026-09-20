## 判定と範囲

**must-fix は 0 件、should は 1 件です。静的レビューとして GO と判断します。**

指定資料はすべて読めました。ファイル書込み・pytest・build・計測は実施していません。author／fix1 のテスト件数・変異 kill は報告として確認したもので、本レビューで再実測した結果ではありません。

以下、L＝`p3_s4_loop.py`、P＝`pipeline.py`、C＝`loop.py`、TL／TJ／TV＝指定の各テストファイルです。

## must-fix

該当なし。

段4裁定・追補1についても、今回の実装範囲を止める仕様誤りは見つかりませんでした。ただし「B-5 の系列開始 stock 全体が実装済み」「実 compiler で STOCK 成立済み」とは認定できません。

## should

**S1：stock の condition gate について、赤判定から評価停止までの負例を追加する。**

- **根拠：** [TL:9843](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-pair-launcher/orchestrator/tests/test_p3_s4_loop.py:9843) の新テストは、meaning の stub が `MeaningBoundaryReached` を投げるため、family admission と拒否処理まで到達しません。既存の拒否・証拠保存テストは候補値を使い、stock 評価テストでは autouse fixture が gate を無効化しています。consult A-M2 が求めた「stock の拒否伝播」は直接には閉じていません。
- **成果物への影響：** stock だけ family admission の赤を無視する回帰を、今回のテスト群が受理する余地が残ります。その場合、拒否すべき stock が評価 WAL を生成できます。
- **是正案：** stock 呼出しに `_REAL_CONDITION_GATE` を戻し、下位 evaluator が supply 赤／meaning 赤を返すケースを追加する。実 family admission を通し、例外・拒否証拠・`run_campaign` 未到達を確認してください。

現物の L:462–465 は候補と stock に共通して拒否を実施しているため、これは現在の実装不具合ではなく被覆不足です。変異の生存は本レビューでは実走していません。

## nit

該当なし。stdout の `p3 S4 pair: candidate_rc=... stock_rc=...` は終了コードの表示であり、それ自体を「pair 測定成立」の宣言とは扱いません。

## 境界ごとの確認結果

| 論点 | 確認結果 |
|---|---|
| **規律2** | P:1719–1722 は legacy を先頭に維持。P:2185–2188 は repetition の拒否で即停止し、P:2434–2440 は全 pass 通過後だけ certified に進みます。P:2705–2720 は拒否結果を bench より前に返します。新経路は screening を渡していません。 |
| **stock admission** | L:1917–1927 は STOCK の場合だけ generator receipt を発行。非 STOCK では stock-baseline 条件も成立せず、review／generator receipt と coder authority もないため、`derive_build_admission` の最終拒否へ落ちます。P:1835–1860 の接続は fail-closed です。 |
| **stock 成功条件** | L:1997–2006 は certified・非 aborted に加え、既定 STOCK variant と BUILD_START の STOCK token の両方を要求します。admission 前の source 制限と評価後の WAL 確認は異なる層であり、矛盾しません。quarantine を省くことは、任意の提案を stock として受け入れることにはなっていません。 |
| **admission class** | 追補1どおり `machine-generated`／`backoff-sweep` です。full PIN と短縮 PIN の比較を変更せず、既存 generator admission を使用しています。critic の stock 分類は L:1113–1127 の `src_token` によるため、class 名の差で candidate に化けません。 |
| **receipt の再現性** | `p3-s4-loop-stock-control/v1\|genome_sha256` は固定生成手順と genome の入力識別として妥当です。これ単独は attempt 識別子ではありませんが、generator receipt は exact source evidence も含めてハッシュ化されるため、その区別を失いません。 |
| **同 campaign** | identity は spec・PIN・search tag・search config・trial の5要素。K2 manifest SHA／knowledge level と admission policy は search config に束縛されます。policy は coder authority の有無で変わりません。宣言値は receipt の同一 bytes 条件で整合を要求します。 |
| **既定 identity** | base `371674ea6` と現物の `default_cfg`／`default_perf`／値域検査／`_resolve_duplicate` の関数本文は bytes 一致でした。固定 preimage の spec 文字列・既定設定・policy 構造と正準 JSON 形式も整合しています。較正・verify 未指定時に新 key を追加する処理はありません。 |
| **較正・emit** | L:3163–3173 で動作点と verify mode を確定してから emit／評価へ分岐します。`perf_workload` は既存の `workload` と意味を混在させず、records・threads・extime・reps と合わせて実効値を束縛します。 |
| **stock gate** | L:427–442 の stock comparison、適応枝の `MeaningCase` は A-1 paired:6894–6918 と同型です。`fixed_sub` は pinned-clean 確認済みで、隔離 worktree 必須により評価 tree と分離されます。候補の `_require_condition_gate(sub, genome)` と既存順序テストも維持されています。 |
| **exact correctness** | C:153–162 → `performance_correctness_workload(perf)` → C:782–792 の `extra_correctness` に接続。legacy＋performance `reps` 回、性能契約との numactl 一致を維持しています。TL:9982以降は実 lock の preimage から flags／reps を復元して evaluate 境界と照合します。 |
| **TV の拒否検査** | 新テストは trace 実行境界で赤／緑 trace を供給し、停止判断自体は stub にしていません。`do_bench=True` のまま `measure_point` を呼出し禁止にし、legacy 赤・performance 初回赤・最終回赤について ABORT と COMMIT 不在を検査しています。 |
| **LoopState・skip** | stock 分岐は LoopState 作成・iteration・whiteboard・checkpoint 更新より前に return。terminal skip は復元せず rc=1、ID がなければ表示しません。`_refresh_critic_digest` の抽出は既存 fixture の入力・射影・出力先を維持しています。 |
| **job body** | 空値を含む不正 stock env は prebuild 前に拒否。stock の manifest／宣言値は候補と同値で、coder-role 等は渡しません。候補失敗後も stock を試行し、候補非零優先の集約値が EXIT trap の `driver_rc` に入ります。 |

候補側 `_resolve_duplicate` は変更されておらず、stock と候補は genome／source による別 variant です。stock の generator admission を追加したことで、候補の duplicate 復元先を stock に差し替える経路は見つかりませんでした。

## 未実測と事前登録の射程

実 compiler による S4 template の inert／STOCK 成立は未測定です。stock 正例テストは source・compiler 境界を模擬するため、その代替証拠にはなりません。

また、今回の候補後 stock は D2172項3の K2 同 job 対照の結線です。B-5 §5.4 の初回 planner への `current_perf` 供給、block stock、§5.3 の session 品質契約、§5.5 の残余引数・seed・verifier 版の発効束まで成立したとは言えません。段4裁定§5はこの限定を明記しており、今回の段階実装との矛盾はありません。

`campaign.lock` は指定した exact 動作点を復元する記録です。実 argv の独立観測記録とは区別が必要です。候補拒否でも既存 CLI が rc=0 を返し得るため、pair 成立は両 attempt の新規 WAL outcome で判断してください。

## 総括

**must-fix：0件。should：1件。GO。**

GO の対象は今回の実装・結線の静的レビューです。実 compiler での STOCK 成立、同 job の両測定成功、B-5 全体の成立を認定するものではありません。