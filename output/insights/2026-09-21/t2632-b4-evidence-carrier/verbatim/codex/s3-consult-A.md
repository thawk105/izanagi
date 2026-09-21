静的検査の結論は、**P4 の回復説明と、変異・入力隔離テストの設計に修正が必要**です。hash の配管、codec 経由化、参照点の定義には、以下の範囲で矛盾を認めません。テスト・変異は実行していません。

以下、`C/` は `orchestrator/campaign/`、`T/` は `orchestrator/tests/`、`plan` は [s2-plan-r2.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/s2-plan-r2.md)、`brief` は [stage1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/stage1-brief.md) を指します。

## 1. 束縛の正しさ（辺 A）

**判定: refuted。ただし失敗後の再実行は項目 3 の問題を持つ。**

- loader は `C/p3_s4_loop.py:2619` で一度読んだ bytes を parse し、その document から評価用 proposal を構成します（`:2692`）。plan:122–148 の capture はその document を渡すため、別 path・再読による差替え窓を増やしません。
- receipt key の除去は既存 canonical identity の仕様そのものです（同 `:526–542`）。raw bytes の hash と混同していません。
- certified duplicate は実際に採用された commit payload を返します（同 `:1863–1883`）。plan:70–79 の「commit の attempt ID を選び、元 WAL record を variant と attempt ID の両方で絞る」は、stage 最後勝ち・receipt 除去の問題を避けます。`C/wal.py:2867–2889` をそのまま hash 入力にしない判断は正しいです。
- reject は同じ `diffq-*` でも毎回新しい ID を start/abort に書きます（`C/p3_s4_loop.py:980–998`）。通常の単一駆動では、今回追加したペアを選ぶ P6 は成立します。
- dry-pass、ID 未確定、B-5 duplicate-skip の null は、証拠を捏造しない扱いです。

**限界:** `variant/build_attempt_id` は iteration 自体の一意 ID ではありません。duplicate の複数行は同じ attempt を指し得ます。また直接 API の hash=null は、完全な辺 A が得られた行とは扱えません（plan:156–158）。

## 2. 規律 2・D39 決定 3

**判定: refuted（計画された変更経路について）。**

writer の挿入は既存評価・whiteboard 射影の後です（plan:101–107）。`project_whiteboard` と `whiteboard_for_planner` は既存の五 field を構成し（`C/p3_s4_loop.py:1199–1242`）、critic は admitted campaign view から digest を作ります（同 `:2882–2894`）。この計画に provenance を入力へ読む追加経路はありません。

capture に document を追加しても、live journal writer は role 別 output/input を明示的に取り出すため、capture 全体が入力や envelope に混入する形ではありません（同 `:2939–2969`）。

ただし、**正常完了時の判定・射影不変と、書込み失敗時の停止挙動不変は別**です。後者まで「1 bit も変わらない」とは言えません。入力隔離テストの射程不足は項目 7 に記します。

## 3. fail-closed の意味（P4）

**判定: real — must-fix。［誤前提］［防壁の射程誤認］**

plan:114、178–183、378 は、provenance 公開後・checkpoint 前の中断を上書き merge で回復できると説明していますが、次の経路を区別していません。

| 経路 | 再実行時の実際の性質 |
|---|---|
| 通常の certified | 同じ proposal なら既存 attempt の duplicate 解決が可能 |
| diff-quarantine reject | `record_diff_reject` が新しい attempt を追加する。既存 attempt の再利用ではない |
| B-4 bootstrap | checkpoint が bootstrap のまま WAL が残ると、非空履歴との矛盾で停止し得る |
| B-4 continuation | 評価前に receipt を消費済みなので、同じ receipt の再利用は拒否される |

根拠は `C/p3_s4_loop.py:985–997`、`:2387–2407`、`:2494–2499`、`:2821`。at-most-once の既存テストもこの拒否を要求します（`T/test_p3_s4_loop.py:5459–5507`）。

さらに、同 iteration の全 field 上書き（plan:180）は、reject の再試行で最初の attempt への対応を失います。別 proposal で再開した場合も、公開済みの古い hash を置換できます。これは「同じ entry の冪等追加」より広い契約です。

trigger も評価後・checkpoint 前に書きますが、**既存 report の読み書きを評価前にも行います**（`C/p3_s4_loop_trigger_gating.py:1117`）。base 案は破損を評価後に初めて検出するため、「先例と同じ性質」と一括できません。

**必要な修正:** P4 の保証を「checkpoint を確定しない」に限定し、上記の回復不能・再評価・対応消失を明記する。失敗後の二回目の呼出しまで検証する。

**放置時の影響:** WAL に評価済み attempt があるのに whiteboard/carrier に対応が残らず、後続の precursor・参照点候補から欠落し得る。certified を誤って増やす問題ではない。

## 4. caller の受理域

**判定: refuted。**

plan:224–241 の codec 一本化と `.get("trial")` は妥当です。

- canonical v2、未知 schema、authority の形は codec が検査します（`C/campaign_lock.py:901–928`）。
- non-certifying schema と schema 無し reserved field は通常 decoder に救済されません（同 `:906–910`、`:930–933`）。
- UTF-8 不正も `CampaignLockCodecError` に変換されます（同 `:1148–1156`）。
- 同例外は `ValueError` の派生なので、caller の既存 catch と `campaign_input_unreadable` に乗ります（`C/p3_b4_prerun_caller.py:82–83`、`:149–156`）。

v1 の通常 object は維持されます。ただし旧 `json.loads` が許した duplicate key・非有限値などは拒否されるため、**受理域の変更は「v2 を追加するだけ」ではなく、不正な旧入力の縮小も含みます**。これは裁定に整合します。

tracked 3 campaign の実物互換は本段では実測していません。plan:248 の留保は適切です。

## 5. 参照点と凍結事前登録

**判定: refuted。**

plan:202–210 は、D2194 項 3:9–14 と凍結参照文:1–8 に整合しています。

- precursor より前の最後の `success` を選ぶ。
- 同じ variant を二回指しても、後の iteration が同じ既存 attempt を参照するだけで、新しい評価とは数えない。
- commit/bench_done は同じ attempt の record 全体を canonical hash 化する。
- 祖先なし・同着・record 非一意・設定一致未確認では不適格とし、別の祖先へ戻らない。
- `reps` と `ycsb_max_ope` は不足のまま残す。

canonicalization の指定も `C/agent_outputs.py:69–78` と一致します。

この一意性は、対応 entry が存在することを前提とします。項目 3 の欠落・上書きを定義文だけで回復できるわけではありません。また carrier は append-only の `scheduled_attempt_registry` の代替ではありません（凍結母集合文:5–8、42–51）。

## 6. 親の実測と一般化

**判定: refuted（構造上の一般化）。実測値の再現確認は未実施。**

- **B-5 → B-4 の lock 形:** 10 件という観測数からの推定に頼る必要はありません。base の B-4 化は `search_config` に marker を追加し、`trial="p3-s4-loop"` を維持します（`C/p3_s4_loop.py:1583–1604`）。codec も `search_config` 内部にこの用途の独自分岐を持ちません（`C/campaign_lock.py:562–574`）。
- **stock と whiteboard:** stock 実装は LoopState を構成・更新せず、候補側の `drive_iteration` と分離されています（`C/p3_s4_loop.py:2019–2117`、`:3557`）。ただし stock は WAL と critic digest には触れます（`:2086`、`:2113–2116`）。「whiteboard に触れない」を「campaign の観測結果を変えない」へ一般化してはいけません。
- **certified-writer 目録:** report 書込みだけなら新しい `run_campaign` 呼出しや certified producer を増やしません。plan:320 の「更新不要の見込み」は合理的です。目録テスト本体は今回の必読射影外なので、exact inventory の一致まで独立確認したとは扱いません。
- **114 node:** brief:38–40 の件数を本段では再現していません。固定の除外集合として一般化せず、今回の各変異について失敗地点を確認する plan:310–314、372 は適切です。既存 pair fixture にも HEAD と live closure の一致要求が明記されています（`T/test_p3_s4_loop.py:10723–10726`）。

## 7. 恒真ゲート・テスト代表性・変異帰属

**判定: real。**

**A. S10 は記載どおりでは意味のある変異にならない — must-fix。［変異帰属］**

plan:349 は main の hash 計算を `hashlib.sha256(proposal_bytes)` に置換しますが、`proposal_bytes` は loader のローカル変数です（`C/p3_s4_loop.py:2620`）。main で使えるのは capture 内の bytes です。

`proposal_capture["proposal_bytes"]` を使う実行可能な変異にし、receipt/整形差による hash 不一致で落ちたことを確認すべきです。

**放置時の影響:** NameError による赤を canonical identity 検証の KILL と誤帰属し、誤った proposal hash を排除する証拠が成立しない。

**B. 新 carrier の入力隔離テストが不足 — should-fix。［防壁の射程誤認］［consumer 取り残し］**

plan:293 は whiteboard 関数の reader poison と既存 AST テスト維持を挙げます。しかし既存 AST テストは agent journal の名称を中心に検査し、critic digest を root に含めません（`T/test_p3_s4_loop.py:9378–9390`）。

planner context・coder 向け射影・critic digest を実際に生成し、provenance の有無や内容差で出力 bytes が変わらないことを検証する必要があります。既存関数への provenance 読取り注入を負例にできます。

**放置時の影響:** whiteboard 五 field を保ったまま、別入力や critic digest に attempt/hash が漏れる回帰を見逃せる。

**C. 分岐名の列挙だけでは代表性が確定しない — should-fix。［テスト代表性］［恒真ゲート］**

dry-pass・duplicate・B-5 早期 return・pair は plan:275–291 に明記されており、「先例を写しただけ」という疑いは反証できます。ただし実装時には次を固定すべきです。

- S4 は **採用 commit と最新 start の attempt ID が異なる** fixture を使う。既存 certified duplicate fixture は単一 attempt なので、そのままでは変異が等価になります（`T/test_p3_s4_loop.py:7992–8004`）。
- pair の carrier 検証には本物の `drive_iteration` を通す。既存 `pair_cli_case` は drive 全体を stub 化しています（同 `:10595–10612`）。
- 書込み失敗テストは checkpoint 不変だけで終えず、項目 3 の再起動結果まで検証する。
- invalid-lock 群には non-certifying lock を明示し、issuer 未呼出しも検査する。

**放置時の影響:** attempt 混入、pair の記録欠落、失敗後の対応消失があっても、受入・変異 matrix が緑になり得る。

## 総括

P1・P2・P3・P5・P6 と、P7 の二つの先例を使い分ける方向は妥当です。**P4 の回復保証の書き直し、S10 の修正、失敗後・入力隔離・複数 attempt を通すテスト具体化を先に行うべきです。**

B-4 の認可を再利用可能にする変更、新しい回復 gate・台帳、base provenance の admission 検査は本依頼の scope 外です。必要なら別の裁定パッケージとし、本 wave の修正へ混ぜないでください。