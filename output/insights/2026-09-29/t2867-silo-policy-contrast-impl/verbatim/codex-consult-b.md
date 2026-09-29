## 総括

plan は必要な評価経路を押さえている一方、台帳と CLI の設計が大きい。特に、台帳から導ける状態を別ファイルにも保存し、単位 file に重複して載せる部分を削れる。  
生死確認に必要なのは、3 系列それぞれの job 1・評価 1 と、計測 WAL の終端および Job Elapse である。score・参照・進化も依頼が名指すため実装は要るが、その計算実走を発効前の生死確認へ足す必要はない。  
brief の「約 3〜3.5 node 時間」は投入前の枠としては使えるが、政策経路の実測値ではない。

## 所見

1. **should-fix — 台帳と単位 file に状態を重複保存している。** plan は多数の nullable 共通 field を持つ14種の event、さらに単位 file に系列座標・slot 一覧・endpoint を載せ、全 field を照合する（`s2-plan/out.md:19-42,75-81`）。草稿が要求するのは「要求単位と台帳から導いた次単位」の起動時照合である（`docs/silo-policy-generator-contrast-preregistration.md:250-254`）。単位 file は台帳の場所、単位種別・番号、候補 path・digest に絞り、残りを導出できる。**成果物への影響:** certified 選択・report・見積りは変わらず、途中死の停止も維持できる。**推奨: 縮小。**

2. **should-fix — critic 用の第二の状態ファイルは不要。** `contrast_critic_digest.json` に前回以後の slot を保存する案（`s2-plan/out.md:83-87`）は、台帳の slot 結果と critic 実行記録から導ける。WAL から digest を作る既存関数もある（`orchestrator/campaign/p3_s4_loop_policy.py:479-484`）。**成果物への影響:** coder に届く診断と report は変わらず、更新漏れの可能性だけ減る。**推奨: 削除。**

3. **should-fix — driver の対照専用 action を増やしすぎている。** 四つの新 action を提案しているが（`s2-plan/out.md:44-55`）、既存の coder 入力・preview・拒否記録・評価には呼べる関数がある（`orchestrator/campaign/p3_s4_loop_policy.py:282-306,388-431,490-530`）。A/B の計上は系列制御側で一度行い、driver には既存関数を使う薄い対照経路を設ければよい。通常 loop の停止判定を通さない点は必要（同 `:434-455`、草稿 `:96-99`）。**成果物への影響:** 評価結果は変わらず、二重計上の経路を減らせる。**推奨: 縮小・再利用。**

4. **should-fix — round tool と親の責務を一つの機会に寄せられる。** 六つの subcommand と別の親・状態管理を見込む（`s2-plan/out.md:89-91,109`）が、依頼上の単位は「原提案 a を一回進める」である。役割入力の生成と保存は一つの round 操作にまとめられる。429 の判定には既存 `classify_exit` を直接使える（`tools/pegasus/b5_llm_parent.py:41-50`）。一方、既存 `Parent` は B-5 の config、指示文、`--resume` と許可 tool に結合しており、そのまま流用すると「a ごとに新 session」に反する（同 `:69-89,159-171`）。**成果物への影響:** 保存する役割入出力と保留結果は変わらない。**推奨: 縮小・部分再利用。**

5. **should-fix — B-5 report の返す数の名前を誤用しない。** plan は「certified・品質正常な探索点を持つ系列数」を `decide_comparison(v2=True)` へ渡す案である（`s2-plan/out.md:93-95`）。判定の閾値は一致するが、既存関数はその数を `certified_endpoint_counts` という名前で結果にも出す（`orchestrator/campaign/b5_generator_contrast_report.py:128-151`）。**成果物への影響:** 判定自体は合っても、report が生成器の成立数を endpoint 数と誤表示する。薄い表示変換を置き、両方の実数を別名で報告する。**推奨: 縮小。**

6. **should-fix — 再利用の境界を明確にできる。** `t2849` の `SeriesLedger` は event 種別・終了理由に結合するため直接 import は難しいが、連番・create-only 書込の約45行は移せる（`orchestrator/campaign/t2849_comparison_harness.py:49-92`）。B-5 の `classify_session`、`wal_timing`、`integer_log_weights` は直接使える（`orchestrator/campaign/b5_generator_contrast.py:82-94,265-305`）。`classify_slot` 全体は B-5 の sidecar・genome・WAL 形に結合するため、無理に共通化しない（同 `:308-319`）。統計核は import し、B-5 台帳射影と固定12系列の `pair_differences` は局所実装でよい（`orchestrator/campaign/b5_generator_contrast_report.py:48-115,177-185`）。**成果物への影響:** 分類・検定は同じで、政策固有 schema を B-5 に押し込まずに済む。**推奨: 再利用。**

7. **should-fix — 行数と検査の見積りが依頼の時間枠に対して大きい。** U1〜U6 のコード・テスト見積りは合計約2,900〜3,900行で、各単位に厚い新規テストと変異候補を置く（`s2-plan/out.md:103-120,149-158`）。静的検査だけでは「全体5分以内」は証明できない。既存退行試験に、claim の相違、A/B 計上、機械 IR、固定10 µs、429、n=10 の各境界を少数加え、実時間を測って上限内の焦点集合を決めるのが妥当。**成果物への影響:** certified 選択と report は変わらず、検査 job の所要を抑えられる。**推奨: 縮小。**

8. **should-fix — 生死確認の費用を「実測」と「枠」に分ける。** brief は生死確認約1.5、検査最大約1.9 node 時間を合算する（`artifacts/brief.md:17`、`s2-plan/out.md:122-147`）。元の単価は B-5 候補からの換算で、政策候補の単価は未測定（`docs/silo-policy-generator-contrast-preregistration.md:388-405`）。さらに仮の walltime では3系列の job 1・評価だけで確保枠は最大4.5 node 時間になる（`s2-plan/out.md:145-147`）。**成果物への影響:** Job Elapse から取り直す §11.3 の計算式は変わらないが、投入前に示す費用の意味が正確になる。**推奨: 縮小。**

9. **nit — 固定10 µs の検査と、1 slot 1 計測 identity は残す。** 既存の fixed10 経路は patch・build option に加え、trace と bench の両 build で define を確認する（`orchestrator/campaign/silo_policy_recon.py:70-85,104-119,130-138`）。同じ variant の再測定には別 identity が要ることも既知である（`docs/decisions.md:73481-73492`）。**成果物への影響:** 削ると参照値の適用方法または fresh な score session を保証できない。**推奨: 維持。**

## 単位ごとの行数の再見積り

以下は静的な縮小案であり、実装後の実測行数ではない。括弧内は「コード＋焦点テスト」の概算。

| 単位 | plan | 縮小案 |
|---|---:|---:|
| U1 driver | 480〜640行 | 310〜440行。既存関数への薄い経路と必要な分岐に限定 |
| U2 job body | 105〜155行 | 60〜95行。既存 body に mode と単位 path の配線 |
| U3 生成器 | 510〜660行 | 350〜480行。IR の型・検証・描画と既存重みを使用 |
| U4 系列制御・起動器 | 910〜1,200行 | 500〜710行。単位 file と event を縮小し、系列 C の submit 手順を使用 |
| U5 round・親 | 490〜660行 | 290〜410行。一機会の操作へ統合 |
| U6 report | 440〜580行 | 220〜320行。統計核を import し政策固有の射影だけ実装 |
| **合計** | **約2,935〜3,895行** | **約1,730〜2,455行** |

生死確認は brief どおり **3系列×〔job 1、評価 1〕の6 job** に留める（`artifacts/brief.md:5,26`）。進化、score、参照の実装と固定入力試験は依頼範囲だが、これらの計算実走は発効後の本走に回せる。検査は焦点試験の実測所要を合計5分の上限と照合し、長い検査 job を作らない。

## brief の (P1)〜(P8) への判定

| 項 | 判定 |
|---|---|
| **P1** | **維持・縮小。** fresh な session と retry の claim 分離は必要。`slot/index/batch/attempt` の独立した設定項目は、衝突しない一つの slot identity に畳める（`artifacts/brief.md:19`、`s2-plan/out.md:13-15`）。 |
| **P2** | **維持。** 系列 identity と既定 cfg の bytes 不変は必要（`artifacts/brief.md:20`、`orchestrator/campaign/p3_s4_loop_policy.py:121-143`）。 |
| **P3** | **維持・縮小。** 起動時の次単位照合は草稿の要求。単位 file の重複 field と第二の状態保存は不要（`artifacts/brief.md:21`、草稿 `:250-254`）。 |
| **P4** | **維持。** 機械 IR の出自、auditor 省略、LLM arm での拒否は比較の意味を守る（`artifacts/brief.md:22`、草稿 `:195-202`）。 |
| **P5** | **維持・縮小。** 初期点の履歴と critic に届く実測は必要。別の digest 台帳は不要（`artifacts/brief.md:23`、草稿 `:110-121`）。 |
| **P6** | **維持。** 元の静的10 µs の適用方法と両 build の define 確認は、参照値そのものを定める（`artifacts/brief.md:24`、`orchestrator/campaign/silo_policy_recon.py:104-119,130-138`）。 |
| **P7** | **維持・表示を修正。** 統計核は再利用できる。探索点を持つ系列数を endpoint 数として表示してはならない（`artifacts/brief.md:25`、`orchestrator/campaign/b5_generator_contrast_report.py:128-151`）。 |
| **P8** | **維持。** 3系列の6 job と進化の固定入力試験で生死を確認できる。score・参照の単価は換算と明記し、Job Elapse 実測後に見積りを更新する（`artifacts/brief.md:26`、草稿 `:378-405`）。 |