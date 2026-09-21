静的検査で **must-fix 3 件、should 4 件**です。編集・commit・テスト実行はしていません。以下、`C/` は `orchestrator/campaign/`、`T/` は `orchestrator/tests/`、`V/` は指定された `verbatim/` を指します。

1. **must-fix — plan §3：submission 後の Tier0 証拠検査が手順から抜ける。**

   根拠：[plan:211](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/codex/s2-plan.md:211) は「submission が無い場合」にだけ Tier0 を読みます。一方、同:215 は submission と拒否の矛盾検出、同:225 は通過証拠の添付を要求しています。現行 `C/b5_generator_contrast.py:330` 以降の投入後経路は、Tier0 を見ず WAL から certified を返せます。

   **影響：Tier0 証拠が欠落・不一致でも、driver の endpoint 選択に certified 評価が入る実装になり得ます。**

   修正：新契約の search/score では submission の有無と独立に Tier0 証拠を読む手順へ変更。submission が有効なら **B は保持**し、Tier0 証拠の欠落・拒否・矛盾は選択資格を与えず記録する。通過証拠を台帳へ運ぶところまで明記してください。

2. **must-fix — P4／plan §3：コンパイラの終了失敗は候補起因の証拠にならない。**

   根拠：plan:198 はコンパイラ終了失敗を候補起因としますが、実際の [buildcache.py:2855](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/campaign/buildcache.py:2855) と同:2908 は configure/build の `OSError`・`SubprocessError`・`RuntimeError` を同じ `BuildError` に包みます。同:3816 の非ゼロ終了には、依存物障害や資源不足も含まれ得ます。traceback の拒否境界だけでは区別できません。

   **影響：環境障害を生成器の失敗として A 枯渇・fallback に変えるか、逆に候補失敗を無料 retry に変える危険があります。**

   修正：型・例外 chain から確定できる事実と原因推定を分け、「コンパイラ非ゼロ＝candidate」を撤回。帰属不能は retry なしの欠測とする案を明記し、候補起因の判定方法を具体化してください。構造化された build 失敗証拠が必要なら、現在編集対象外の buildcache 変更として裁定パッケージへ返すべきです。

3. **must-fix — plan §3：共通 Tier0 契約の cohort 内一致が検査対象に入っていない。**

   根拠：plan:255 は各台帳と証拠の整合を要求しますが、現行 [report.py:467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/campaign/b5_generator_contrast_report.py:467) の構成比較には `tier0_status`／`tier0_contract` がありません。固定文字列 `contract_id="b5-tier0/v1"` だけでは timeout・argv の一致を表せません。

   **影響：arm ごとに異なる smoke 条件、または未実装と実装済みの混在を、共通ゲートの比較として report が受理し得ます。**

   修正：新契約について、実値を含む Tier0 契約を cohort の共通構成比較へ追加。過去 pilot の読取り互換と、registered 比較としての受理条件を分け、混在・timeout 差・flags 差の負例を追加してください。これは今回の report 所有範囲内です。

4. **should — P6／P7／plan §6：実効 handshake 期限の算定と欠測時運用が不足。**

   根拠：plan:365 は末尾で 2700 秒使えない点を認識しています。しかし [driver:671](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/campaign/b5_generator_contrast.py:671) は、job 終了時刻より **1800 秒前**に待機を打ち切ります。概ね実効待ち時間は `min(2700, 残walltime−1800)` です。例えば残り 2000 秒なら約 200 秒で終わり、request に書く 2700 秒後の期限とは異なります。

   **影響：親が通常の実測範囲内で応答しても LLM 系列だけが欠測となり、対比較の判定可能性が失われます。**

   修正：設計記録に実効期限、poll 誤差、親確保の時点、親停止・遅延時の終了処置を明記。p=4 は独立した親を確保できる条件付き運用案とし、10〜13分の実測から同時4本の応答上限を保証しないことを残してください。期限表示や launcher の変更が必要なら、別所有面の裁定候補へ分けます。

5. **should — P3／plan §2・§3：smoke 数値の役割入力への流出経路が残る。**

   根拠：plan:186・225 は throughput を含む Tier0 証拠を event に添付します。[driver:775](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/campaign/b5_generator_contrast.py:775) は event 全体を親向け `slot-*.json` にコピーします。`expected_inputs` は bench 由来ですが、`assert_inherited_inputs` は任意の leading indicators 全体を同様には照合しません。

   **影響：fitness が不変でも、smoke 値を親が leading indicator／critic 材料へ射影して生成候補を変える経路が残ります。**

   修正：smoke 数値は監査証拠に限定し、役割入力の性能・診断射影から除外する契約を追加。plan:288 の不変検査を endpoint/current_perf だけでなく leading indicators にも広げてください。親側射影が今回実装外なら未閉鎖面として明示します。

6. **should — plan §4・§5：変異と検査対象の対応が一部成立していない。**

   根拠：plan:265 は smoke helper から gateway/parser を検査しますが、同:309 の「trace binary へ変更」は通常、呼出し元の `pf.binary → tr.binary` 変異です。helper 単体検査はその変更箇所を通りません。また同:277 の正常な実走だけでは、Tier0 通過後の anomaly reject 継続を証明できません。

   **影響：誤った binary の smoke や correctness 迂回が残っても、提示された検査対応表では検出済みと誤認し得ます。**

   修正：実挿入点から smoke へ渡る binary/hash/trace 属性を検査する node を割り当てる。加えて「Tier0 passed → 通常 verify で anomaly → B=1、bench 不採用、endpoint 不採用」の負例を明記。変異は対象行に到達した検査の失敗へ帰属させてください。

7. **should — P2／plan §3：BuildResult の argv を実行 argv と混同しない。**

   根拠：plan:186 は configure/build argv を記録しますが、[buildcache.py:2131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/campaign/buildcache.py:2131) は完成先 `bdir` から再現用 argv を再構成します。実 configure は同:2819 で staging を対象に組まれます。cache hit では当該 attempt に configure/build 実行自体がありません。

   **影響：Tier0 台帳の build 実行参照が、実際に実行したコマンドであるかのように記録されます。**

   修正：再現用 argv と実行観測を区別して命名し、`cached` と併記。cache 同一性は contract namespace・cache entry・binary hash の一致で確認し、再構成 argv の一致だけでは検収しないでください。

## 総括

- **must-fix は3件**：投入後の Tier0 証拠検査、build 失敗の帰属、cohort 内の共通契約一致。
- **P1：賛成。** 子の候補経路へ挿入し、stock を除外する位置は妥当。
- **P2：条件付き賛成。** 同じ applied 区間・引数・admission なら再利用可能。実 cache hit は親の実測待ち。claim を自動回収しない方針は維持。
- **P3：条件付き賛成。** rr50、既存 parser、同じ bench lock、実測 max から timeout を固定する方針は妥当。数値射影と検査対応を補強。
- **P4：原案に反対。** 一律候補起因は不可。plan の修正方向は正しいが、コンパイラ終了失敗の扱いが未解決。
- **P5：賛成。** 開始印は必要。開始印だけで walltime 原因を断定せず、投入前回収から B を増やさない。
- **P6：条件付き賛成。** fresh context・1親1系列は妥当。brief:32 の配置根拠は plan の訂正を採用し、実効期限と親遅延時運用を補完。
- **P7：条件付き賛成。** 21,259秒を共通基準とする案は実測の出所が明確。ただし追加 Tier0 費・他 workload・A=30 の完走保証ではない。
- 子→sidecar→driver→台帳→report→header は所有表に入っています。T-2632 land 後の U2、T-2830 所有面の非編集も妥当です。build 原因証拠や親運用の追加実装が必要なら、未実装の裁定候補として分離してください。