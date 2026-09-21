静的検査と提供 log の読解のみです。テスト・変異は実行していません。以下、`C/` は `orchestrator/campaign/`、`T/` は `orchestrator/tests/` を指します。

## 1. 束縛

**refuted／nit（修正不要）** — 単一 driver の前提では今回または採用済み attempt に束縛され、過去の同 variant の refs は混入しません。成果物の対応関係を変える欠陥は認めません。

根拠は [p3_s4_loop.py:1658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop.py:1658)。certified／duplicate は返却された commit、aborted は abort、なければ start を使い、未確定なら null です。rejected は `record_diff_reject` が毎回新しい ID の start／abort を追加してから返すため（同ファイル:990）、過去の reject／retry があっても末尾は今回の abort になります。refs は variant と attempt ID の双方で絞り、record 全体を出現順に hash 化しています（:1675）。

## 2. 受理集合の変化

**real／must-fix［誤前提］［consumer 取り残し］** — hash 不能値を既存検査がすべて拒否するという前提は成立せず、B-5 では拒否 sidecar／rc=3 を経由せず停止します。放置すると従来の走行が消え、失敗台帳への記録経路も変わります。

具体例は、通常 proposal の任意項目 `planner.uncertainty` に `NaN` を置く入力です。`assert_closed_proposal_schema` はキー集合の検査で（`C/projection_guard.py:269,291`）、`PlannerProposal` は値検査をせず、coder の値域検査もこの項目を見ません（`C/p3_s4_loop.py:633,651,2884`）。

新しい [hash 呼出し:3710](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop.py:3710) は拒否処理の `try` 外で、例外型も `B4ProtocolError(RuntimeError)` です（:524,543）。単に呼出しを内側へ移すだけでは既存 catch に入りません。受理域縮小を明記し、hash 不能時を B-5 の既存拒否経路へ接続する修正・回帰検査が必要です。

## 3. 評価前の検証

**real／should-fix［防壁の射程誤認］** — 評価前検査と退避時の bytes 保持は成立しますが、「`.corrupt.*` が残る限り停止」という無条件保証はありません。正常 report が併存すると未処理退避を残したまま記録を更新できます。

[loader:1561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop.py:1561) は、原本が**不在の場合だけ**退避ファイルを検査します。これは段2プランの条件付き仕様には一致しますが、今回の検査項目の強い表現とは異なります。

それ以外は refuted です。drive 内の読取りは認可検査・消費・評価より前（:2967,2990,3010,3046）、入口停止で report を新設しません。`os.link` 失敗なら原本が残り、link 成功後の unlink 失敗なら両名が残ります（:1574）。通常の操作失敗で元 bytes を失う順序ではありません。

## 4. P4 の限定

**real／should-fix［誤前提］** — continuation の再利用拒否は一致しますが、bootstrap の再実行拒否を無条件に書くのは過大です。WAL 未生成の結果では公開済み entry が再実行で上書きされ得ます。

[docstring:1616](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop.py:1616) に対し、bootstrap 履歴検査は WAL bytes がなければ通過します（:2576）。ID 未確定の aborted は report に記録できるので（:2495,1652）、説明を「履歴が残る bootstrap」に限定すべきです。

continuation は消費 record の排他的 link により再利用を拒否します（:2676）。非 B-4 の certified→duplicate、reject の新 attempt／同 iteration 上書き、provenance 公開前に checkpoint を進めない説明はコードと一致します。

## 5. 入力隔離

**refuted／nit（実装修正不要）** — report や `proposal_document` を planner／coder／critic 入力へ流す新経路は認めません。whiteboard・critic 入力・certified 判定への混入はありません。

[ live journal writer:3149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_s4_loop.py:3149) は指定キーから envelope を構築し、`agent_record` 全体を展開しません。追加された `proposal_document` は入りません。report の読取りは carrier の検証・merge に閉じています。

ただし、この隔離を出力 bytes で確かめる新テストは現状失敗しており、実測による裏付けは未成立です（項目7）。

## 6. caller

**refuted／nit（修正不要）** — codec 経由の v2 追加と不正 v1 の受理縮小は裁定どおりです。不正 lock から issuer が呼ばれ、適格行や台帳が増える経路は認めません。

[caller:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/campaign/p3_b4_prerun_caller.py:68) が byte decoder を使用し、:85 で codec の `ValueError` と UTF-8 エラー等を変換します。codec は non-certifying、非 canonical inner／outer、不正 authority を拒否します（`C/campaign_lock.py:901,917,919,931,1148`）。v1 の trial 欠落は `.get`→unknown trial であり、KeyError は漏れません。

ここでの authority 検査は **codec の構造・値域検査**です。実在 authority の admission 検査まで証明したとは扱いません［防壁の射程誤認：refuted］。

## 7. test の検出力と代表性

**real／must-fix［テスト代表性］［変異帰属］［consumer 取り残し］** — 新テスト11件が対象 assertion 前に失敗しています。放置すると attempt 束縛・破損時停止・入力隔離を検出したという誤った検証記録になります。

修正箇所は以下です。

- `T/test_p3_s4_loop.py:7246`：未定義 `STAGE_VERIFY_DONE`。S4／S5／S6 の対象2件が未到達。
- [同:7385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-evidence-carrier/orchestrator/tests/test_p3_s4_loop.py:7385)：既に存在する reports に `mkdir()`。S8／S13 の対象8件が未到達。
- 同:7491：fixture に WAL がなく admission で停止。S14 の bytes 比較が未到達。
- `T/test_p3_b4_closed_critic.py:2749`：既存 launcher fixture の commit に attempt ID／対応 start がない。新契約に追従させる必要があります。

変異ごとの静的判定は次のとおりです。

| 変異 | 検出設計の判定 |
|---|---|
| S1・S2 | 実 drive／writer と checkpoint 順序・失敗後再実行を通す。恒真ではない |
| S3 | 同 variant の2 attempt を実際に追加し、refs 混入を比較 |
| S4・S5・S6 | fixture 修正後に評価可能。現状の NameError は KILL に数えられない |
| S7 | 他 iteration の保持と同 iteration 更新を比較 |
| S8・S13 | 後段 loader と重複。例外だけでは不十分だが、評価・認可未呼出し assertion は区別できる。まず fixture 修正が必要 |
| S9 | regular file の fsync だけを失敗注入し、directory fsync と区別 |
| S10 | raw bytes hash は整形差分で検出可能。ただし receipt 付き document の main 通過自体はこのテストでは覆わない |
| S11 | capture 欠落による停止を検出。hash 算法の検出とは区別すべき |
| S12 | 実 drive／writer の B-5 早期 return を検査。評価部分は stub |
| S14 | WAL 不在を直すまで判定不能 |
| C1〜C5 | 実 codec／caller／issuer を通す構成で、登録された拒否・過剰拒否・例外漏れを区別可能 |

期待 refs はその走行の WAL から算出し、時刻・ランダム ID の固定値焼込みはありません［恒真ゲート：refuted］。binding は module／worker ごとに再利用され、今回の焦点走は167.68秒、lock timeout／error は報告されていません。ただし base fixture は test 全体で read lock を保持するため（同:7146）、将来の長時間化まで安全とは言えません。

## 8. 焦点走の結果

**real／must-fix［変異帰属］** — 失敗12件はすべて本 wave のテスト追加・契約変更に帰属します。既存非帰属や drift として除外すると、成果物の検証状態を過大評価します。

[focus-f1.log:516](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/focus-f1.log:516) の内訳は以下です。

| 分類 | 件数・根拠 |
|---|---|
| 新規 fixture 不備 | 11件：mkdir 8、未定義定数2、WAL 不在1 |
| 新契約への既存 fixture 追従漏れ | 1件：launcher-positive の attempt 証拠不足 |
| drift／既存非帰属の failure | 提供 log には該当する根拠なし |
| error | 0件（同:1030 の failure digest） |
| skip | 15件。理由・nodeid が提供 log にないため帰属分類不能 |

集計は **12 failed／4689 passed／15 skipped、167.68秒**（:528）。stdout に16,041 bytesの省略があり（:12）、skip を既存非帰属と断定できません。失敗12件は digest に全件収録されています。

## 総括

**NO-GO。** B-5 の hash 失敗処理と、機能検査に到達しないテスト／既存 fixture の修正が必要です。退避ファイル存在時の保証と bootstrap 再実行説明も、実際の条件に合わせて限定してください。変異 KILL の成立は、正常系を直した後の親の実走で判断すべきです。