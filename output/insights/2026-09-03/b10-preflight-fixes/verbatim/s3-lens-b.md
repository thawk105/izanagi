## 所見 1 — 壁時計の実行時出現は 5 か所だが、提案テストは 3 consumer の食い違いを確実には赤にしない

深刻度: must-fix

B-10 shape の実行契約を、数値、時刻、12h、720 分、乗算式の表記で走査した。実行時 consumer は次の 5 か所だけで、別表記の追加箇所はなかった。

- `tools/pegasus/b10_backoff_shape_campaign.sh:5` — PBS `12:00:00`
- `tools/pegasus/b10_backoff_shape_campaign.sh:170` — submit receipt の `43200`
- `tools/pegasus/b10_backoff_shape_campaign.sh:261` — qstat 実測値の `43200`
- `tools/pegasus/submit_b10_backoff_shape.sh:200` — 投入要求の `43200`
- `orchestrator/campaign/b10_backoff_shape_sweep.py:492` — driver receipt 検査の `43200`

テスト側の鏡像は `orchestrator/tests/test_b10_backoff_shape_sweep.py:1896-1899` であり、上の 5 consumer には数えない。過去の receipt、insight、他 campaign の 12 時間値も同様に除外した。

プランは 4 個の数値 consumer を JSON から派生させ、PBS 1 個を意味比較するため、意味上の対象数との差は 0。ただし `s2-plan-a2.md:173-180` のテスト仕様では、submit receipt は dry-run の値比較で赤にできる一方、job receipt validator、scheduler validator、driver validator は「定数を参照する」という source 検査だけである。例えば `int(walltime_s) + 1` や `_b10_walltime_s(root) + 1` にしても参照検査は通る。

PBS の `12:00:00` をテスト側で秒換算して JSON と比較する経路は、実装側に同じ換算器が存在しないため恒真ではない。

成果物影響: 3 consumer の式だけがずれてもテストが通り、正式 job の起動拒否または誤った scheduler 値の受理へ進みうる。

## 所見 2 — 共有 `policy.json` の追加 field は他 campaign の意味検査には耐えるが、既存 SHA golden を確実に壊す

深刻度: must-fix

`tools/pegasus/policy.json` は B-10 専用ではない。追加 top-level field は、`.get()` や部分キー参照をする `orchestrator/campaign/loop.py:89-105` などでは拒否されない。また `orchestrator/tests/test_pegasus_policy_registry.py:434-493` の禁止対象 `_MOVED_KEYS` にも該当しない。

一方、file 全体の bytes は別 campaign の identity である。

- `orchestrator/campaign/silo_ladder_rung1.py:2563-2580`
- `orchestrator/qualification/t126_driver.py:873-895`
- `orchestrator/tests/test_silo_ladder_rung1_evidence.py:1263-1275`
- `orchestrator/tests/test_t126_pegasus_tools.py:1450-1468`

追加後は `orchestrator/tests/pegasus_policy_expected_goldens.py:5-7` の current SHA が必ず不一致になる。この file と上記 consumer tests は、`s2-plan-a2.md:523-531` の変更 file 一覧にない。歴史 SHA は同 file の `:8-10` に分離済みなので、そちらを書き換える必要はない。

成果物影響: Silo/T-126 の歴史成果物は維持できるが、current-policy pin が古いままになり受入テストが赤となり、現行 policy 参照が不整合になる。

## 所見 3 — 固定 report root は 3 通発行を防ぐが、135 gate は「全 3 job 終端」を証明しない

深刻度: must-fix

`reports/final` と `mkdir(..., exist_ok=False)` を使う案は、同じ binding group から完全な report が 3 通できることを防ぐ。根拠は `s2-plan-a2.md:323-331` と `orchestrator/campaign/b10_backoff_shape_sweep.py:2641-2645`。

しかし 135 record の成立時点は job 終端より早い。最後の block file は `os.open(O_CREAT|O_EXCL)` で先に可視化され、`os.write`、`fsync`、`close` の順で完成する (`b10_backoff_shape_sweep.py:2295-2305`)。最後の record 後にも self-read と completion 判定が残り、さらに job script が `job-result.json` を書いてから終了する (`b10_backoff_shape_campaign.sh:352-383`)。

したがって report は次のいずれにもなりうる。

- 最終 file の途中を読んで拒否する。
- `os.write` 後に完全な 135 件を読み、3 本目がまだ未終端のまま発行する。
- その後 3 本目が fsync、completion 判定、job-result で失敗する。

全 job 終端を保証するのはプラン記載どおり人の投入手番だけで、135 gate ではない。

成果物影響: 後に非零終了する job の record を、すでに全 job 終端済みの入力として report の受理集合へ入れうる。

## 所見 4 — attempt ごとの ordinal reset と単純件数は実際に異なる値を出す

深刻度: must-fix

WAL producer は `build_attempt_id` と tag を書くが repetition を書かない (`orchestrator/campaign/pipeline.py:1485-1502`)。反復番号は loop 変数にしかない (`:1521-1529`)。

食い違う具体例は、同一 `(workload, variant, performance)` について次の WAL がある場合。

- attempt A に 3 件、attempt B に 2 件の `verify_done`
- 件数規則: 5 完了
- attempt ごとの ordinal reset 後に attempt を投影から外す規則: `{1,2,3} ∪ {1,2}` となり 3 完了

逆に attempt A が 5 件、attempt B が 1 件なら、件数は 6 の overrun だが、ordinal の集合だけなら 5 に見える。別途 raw overrun を拒否しなければ false-complete になる。同一 attempt 内の複製 frame は、どちらの規則でも別 repetition と区別できない。

親実測 C は官製 4 campaign の 197 と 287 を再現した事実として支持できる。ただしその標本に tag 上限超過や同一 variant の複数 attempt がないため、「件数だけで一般に足りる」という含意までは証明していない。

開示としては、反復が交換可能で物理的な番号を持たない以上、選定済み campaign 内の `(workload, variant, tag)` ごとの件数を使い、登録上限超過を拒否する方が妥当。ordinal は `1..件数` の論理枠を表すだけとし、各 WAL frame へ番号を帰属させないのがよい。

成果物影響: 上の 3+2 入力では completed slot が 5 と 3、incomplete slot が 0 と 2に分かれ、完全性 report の値が変わる。

## 所見 5 — campaign の名指しは満たすが、採用 campaign 集合は report phase が暗黙に決める

深刻度: should-fix

`s2-plan-a2.md:371-400` は full campaign ID、workload、raw 件数、tag 内訳を出すため、「197」の既知の取り違えは防げる。

一方、入力集合は `s2-plan-a2.md:323-328` の current campaign 導出と、`:455-471` の `e3de15eb` 固定 adapter によって collector 自身が選ぶ。設計文書 `verbatim-design-s6.md:35-37` が未裁定とした「どの campaign の記録を完了として採るか」を実装が決める形である。

D1509 決定 3 は write-heavy について完走した 45 セルを残すため、`e3de15eb` の選択を支持する。balanced/read-heavy は本 wave の新 binding で走る campaign を採り、過去の `15e75b3f` / `ed8a676b` を混ぜないことまで親裁定で明文化する必要がある。`068fd2cd` を採っても verify 件数は同じ 197 になるが、performance row は別物である。

成果物影響: campaign 選択が変わると 270 側の数値が同じ 197 のままでも、135 row の受理集合と judgement が変わる。

## 所見 6 — v2 optional host では新規 row のノード名欠落を拒否できない

深刻度: must-fix

プランは新 writer も `b10-backoff-shape-block/v2` のままとし、validator は `execution_host` が存在するときだけ検査する (`s2-plan-a2.md:418-451`)。現 validator も row の exact key set を要求せず、個別 field だけを見る (`b10_backoff_shape_sweep.py:2360-2398`)。

このため current binding の新規 v2 row から `execution_host` を除いた入力も「legacy v2」と同じ扱いで通る。writer のテストは生成漏れを検出できても、collector の受理契約では新旧を区別できない。

親 P3 の v3 writer、旧 v2 と新 v3 の限定受理は、この区別を明示できる。別案としても、通常の current-binding validator では host 必須、`e3de15eb` 専用 adapter だけ欠落可、という区別が必要である。

成果物影響: 新しく測ったセルが実行ノード不明のまま report に入り、D1126 が求めるセルからノードへの参照が失われる。

## 所見 7 — 旧 write-heavy の現在の拒否原因は実測どおりで、限定 adapter は現 wave には有効だが一回限り

深刻度: should-fix

親実測 D は正しい。静的再確認でも、

- current driver SHA: `94d2cb330476...`
- commit `0a07481b8` の driver SHA: `34072fb2a5a5...`
- 保存 provenance の値: `output/insights/2026-08-31_t1905-b10-formal-run/reports/write-heavy/b10_backoff_shape_provenance.json:13-15`

が一致した。current validator は current binding と analysis SHA を要求するため (`b10_backoff_shape_sweep.py:2380-2385`)、現行 main だけでも旧 45 セルを拒否する。「本 wave が作った不一致ではない」は正しいが、D1509 決定 3 を満たすには本 wave で解消が必要である。

プランどおり report 専用 adapter が `e3de15eb`、歴史 lock、spec、patch、formula、45 logical cells を exact に検査し、通常 validator を先に通さないなら、旧 v2 schema や host 欠落によって 45 セルが落ちる経路は見つからない。

ただし固定 ID は D1509 向けの一回限りである。次に driver を編集すると、この wave で作る balanced/read-heavy も歴史 binding になり、`e3de15eb` だけの adapter では再集約できない。次系列では、再利用する campaign と歴史 binding を改めて事前に名指しする必要がある。

成果物影響: adapter 無しでは旧 45 セルが全落ちし、固定 adapter を恒久規則と誤認すると次系列で以前の campaign が受理集合から落ちる。

## 所見 8 — brief と段 2 の文書更新方針が食い違う

深刻度: should-fix

`brief.md:37-42` は、signal bug が main で修正済みなので「設計文書側の訂正」を行うとする。一方 `s2-plan-a2.md:533-545` は `docs/b10-multinode-formal-run-design.md` を触らないとしている。実際の設計文書 `docs/b10-multinode-formal-run-design.md:228-231` には修正前の複合 `local` が現在形で残っている。

また brief の N6 `brief.md:55-60` にある「出現順で数えるほかない」は、親実測 C の件数方式と食い違う。P2 の enforcement closure 理由も、handoff A と `campaign_lock.py:49-74` が反証している。driver を同 file に置く結論自体は analysis hash (`b10_backoff_shape_sweep.py:1377-1394`) から支持できる。

成果物影響: authoritative design の必須修正一覧と repetition 規則の参照が古いまま残り、次の投入判断と台帳参照が現行コードと食い違う。

## 所見 9 — consumer test と行番号台帳は、共有 policy golden 以外は網羅されている

深刻度: nit

`test_ccbench_spawn_sites.py` の B-10 行番号は、台帳本体 `:827-840` と exact 集合の複製 `:2598-2603` の 2 組であり、プランは双方を更新対象にしている。`:2652` は synthetic path だけで実行行番号ではない。

参照関係を辿った範囲では、`test_campaign.py:5329`、`test_official_perf_closure.py:48,82,87`、`test_hooks.py:2577,2622` は caller 数や path class が変わらないため更新不要。抜けは所見 2 の policy SHA golden とその 2 consumer tests だけである。

成果物影響: なし。所見 2 を除けば、既存 consumer test の期待値に追加の脱落は見つからない。

## 所見 10 — 同型問題の他 campaign での存在

深刻度: nit

- job 内 report/finalizer は `tools/pegasus/b10_backoff_grid.sh:584-587` と `a5_second_boot_backoff_sweep.sh:593-817` に存在する。ただし両方とも job-unique output root を要求する (`b10_backoff_grid.sh:231-259`、A5 `:249-267`) ため、他 workload が書いている共有 directory を 3 job が集約する同一欠陥ではない。
- 同じ 2 wrapper の build cache は PBS job の `TMPDIR` または job 固有 checkout 配下である (`b10_backoff_grid.sh:252-256`、A5 `:460-480`)。A-2 も workload job root ごとの cache (`paper_story_a2_certification.sh:31-35`) であり、検査範囲では B-10 shape と同じ共有 cache の独立例はなかった。
- row/report への node 名非埋め込みは旧 B-10 grid にある。report provenance は campaign と workload だけ (`backoff_extended_sweep_report.py:740-745`) だが、同じ job-unique root の `reservation.json` には host binding がある (`b10_backoff_grid.sh:384-404`)。同型の surface は存在するが、root を介した追跡は可能である。

成果物影響: なし（nit）。本 wave で直す根拠にはしない。

## 総括

must-fix:

- job receipt、qstat、driver の壁時計式を実際に食い違わせて赤になる意味テスト
- `policy.json` 更新に伴う current SHA golden と 2 consumer tests の更新
- 「全 3 job 終端」を 135 gate が保証するという誤認の解消
- 270 枠について count と attempt-reset ordinal の択一
- 新規 record の node 名を必須にできる schema／validator 区別

壁時計の実行時出現総数は 5。内訳は `b10_backoff_shape_campaign.sh:5,170,261`、`submit_b10_backoff_shape.sh:200`、`b10_backoff_shape_sweep.py:492`。プランの意味上の対象数との差は 0。変更される数値 consumer は 4、残る PBS literal は 1。

未決 3 件の結論:

- driver bytes と identity: 親実測 D を支持する。新 balanced/read-heavy の新 identity と、旧 `e3de15eb` の report 限定受理を明示承認すべき。固定 adapter はこの系列だけの規則とする。
- repetition: attempt ごとの WAL 出現順は採らない。選定済み campaign の `(workload, variant, tag)` ごとの件数を用い、上限超過を拒否する。親 C の 197/287 再現は支持するが、一般性は支持しない。
- 135 構造欠落対 row 測定不能: 区別を支持する。1 本が record 書出し前に落ちれば report 自体を拒否し、135 row があり `missing` 等なら indeterminate を発行する。ただし 135 だけでは job 終端を証明しない。

親 brief の P1〜P5:

- P1: 支持。単一定数、4 派生 consumer、PBS literal の独立意味比較が最小形。ただし提案テストは未閉包。
- P2: 結論を支持、brief の理由には反対。driver 同居の根拠は enforcement closure ではなく analysis-code binding。
- P3: 支持。新 v3 と旧 v2 の限定受理の方が、新規 host 必須と旧 45 セル保存を区別できる。
- P4: 支持。135 performance cells と 270 verification slots は別母集団、別 object が必要。
- P5: 支持。`reservation.py:120-175` の既存 host binding が正しい取得元。

親実測 A〜D:

- A: 支持。driver は exact 24-path closure 外。
- B: 支持。prefix-map/no-RPATH の機構はあるが、異なる cache root の実 binary bytes 一致証明はない。
- C: 197/287 の現物再現は支持。複数 attempt／重複入力への一般化は反対。
- D: 支持。current main ですでに歴史 binding 不一致があり、旧 45 セルを通常 validator は受理できない。

親裁定へ返すべき設計択一:

- 新 identity を承認し、`e3de15eb` をこの系列だけ歴史 binding 付きで受理するか。
- repetition を「attempt 内出現順」ではなく「選定 campaign の tag 別件数」とするか。
- campaign 選択を `write-heavy=e3de15eb`、balanced/read-heavy=本 wave の新正式 campaign と明記するか。
- 135 構造欠落拒否と、存在 row の測定不能を indeterminate とする区別を確定するか。
- 全 job 終端を人の投入手番で保証するか、report が機械的な終端証拠を要求するか。
- 新 row を v3 で host 必須とするか、current-binding v2 だけ host 必須にして歴史 adapter のみ欠落可とするか。

静的検査のみで、pytest は実走していない。