結論は NO-GO です。親の 3 主張のうち、狭義の `measurement_head` 一致だけは確認できましたが、「層 3 必須」「実走 arm 認証」「計測対象全体の一致」は反証できました。

### 所見 1: 層 3 鎖は正式受入の必須経路ではない

- 主張: `assert_campaign_layer3_chain` の呼出しは、`do_build=False` と campaignless failure を含む全受入の必須な層 3 検証ではない。
- 原典: `orchestrator/campaign/trial_registry.py:5733-5817`、`orchestrator/campaign/autonomous_trial_completeness.py:4062-4069`、`orchestrator/tests/test_trial_registry.py:1799-1820`
- なぜ real か / なぜ refuted か: `do_build=False` は関数を呼ばずに進む。campaignless failure は関数を呼ぶが `continue` し、persisted Layer 3 report の再読・WAL 再構築比較へ到達しない。テストも、この迂回を含む bundle が receipt 発行まで進むことを固定している。したがって 5796 行の呼出しだけでは「必須経路」の証拠にならない。
- 成果物影響: certified 選択は現状変わらないが、層 3 未検証の 6 trial が `AcceptedTrial`、report/journal hash、cross-binding leaf hash を持つ非 certifying receipt として受理される。D863 の第 1 条件を閉じたとは扱えない。

### 所見 2: `layer3-chain-absent` は certifying 判定を駆動していない

- 主張: `layer3-chain-absent` が receipt を非 certifying にするという説明は因果が逆で、現行 receipt は理由コードと無関係に常に非 certifying である。
- 原典: `orchestrator/campaign/trial_registry.py:5899-5944`、`orchestrator/campaign/s8c_acceptance_receipt.py:273-301`、同 `:393-401`、同 `:988-1000`
- なぜ real か / なぜ refuted か: issuer は理由コードを追加するが、parser は理由列の整列・一意性と `t468-approval-authority-absent` だけを要求し、`layer3-chain-absent` の条件付き存在を再導出しない。`certifying=True` は 395 行で無条件拒否されるため、「理由コードが積まれても true」の経路は構成できなかった。一方、理由を省いた tracked receipt は他の参照が正しければ standalone verifier を通り得る。cross-binding についても verifier は leaf digest の aggregate を再計算するだけで、層 3 鎖を再実行しない。
- 成果物影響: 現行 certified 集合は空のままなので直接の拡大はない。しかし receipt の理由集合は層 3 欠落の独立証明ではなく、将来 `certifying=True` を導入するときに再利用できない。これは nit ではない。

### 所見 3: 宣言 arm から実際の CCBench source までの因果鎖が切れている

- 主張: arm 検査は provider 入力 bytes までは到達するが、その入力から得た proposal が実際に build・bench された source であることまでは認証しない。
- 原典: `orchestrator/campaign/trial_registry.py:5320-5340`、同 `:5632-5720`、`orchestrator/campaign/autonomous_trial_completeness.py:834-867`、同 `:870-952`、同 `:3289-3333`、同 `:3336-3398`、`orchestrator/campaign/artifact_admission.py:671-723`
- なぜ real か / なぜ refuted か: historical arm input、report/run-start、cell descriptor、保存 provider payload は厳密に照合されるので、単純な report field の嘘は落ちる。しかし `_cross_binding_proposals` は proposal bytes を hash するだけで `coder` 内容を解釈せず、WAL source・trigger binding・variant と比較しない。trigger provenance も `variant/build_attempt_id/commitment` だけを照合し、`proposal_path` や proposal の coder 値を消費しない。したがって走行側は arm A の整合した payload/proposal 一式を残しつつ、別の有効 source B を build・bench した WAL を作れる。
- 成果物影響: receipt の `arm_execution` と `arm_binding="execution-bound"` が、実測 variant の生成原因を証明しない。現状の receipt は非 certifying だが、将来その hash を certified 選択へ流すと on/off/swapped 差の帰属と proof chain が不正になる。

### 所見 4: `measurement_head` 一致は計測対象全体の一致ではない

- 主張: 6 report が同じ `measurement_head` を持つことは保証されるが、環境契約、ratified generation、実走 producer、campaign 全体の同一性までは保証しない。
- 原典: `orchestrator/campaign/trial_registry.py:5517-5526`、`orchestrator/campaign/s8c_acceptance_receipt.py:490-502`、`orchestrator/campaign/autonomous_trial_completeness.py:713-831`、`orchestrator/campaign/layer3_report.py:551-586`、`orchestrator/campaign/trial_registry.py:730-757`、`orchestrator/campaign/s8c_arm_inputs.py:409-459`
- なぜ real か / なぜ refuted か: 同一 Git commit という狭い主張は反証できなかった。また各 full-build cell は workload、scale、固定 CCBench pin、campaign lock と個別に束縛される。しかし env tag の一意性は campaign 内だけで、6 campaign 間の環境契約一致検査はない。`measurement_env` は absent または `pegasus` の両方を許すため、同一 head の 6 report に異なる環境を混在できる。campaign ID は共通値ではなく、6 件すべて別値であることが必須である。さらに on/swapped descriptor は `measurement_head` の blobでなく現在 import 中の freeze moduleから導出され、commit 引数が実際に使われるのは off artifact だけである。ratified generation hash は acceptance の照合対象に存在しない。
- 成果物影響: receipt は `measurement_head` を 1 値として示しながら、参照する Layer 3 report の `env_tags` や環境契約が異なる束を受理し得る。将来の arm 比較では環境差が treatment effect に混入する。親の表現は「同じ測定 authority Git commit」に狭める必要がある。

### 所見 5: P1 の `loop_state.iteration` は独立な世代数証拠ではない

- 主張: sealed `loop_state.iteration` は report/journal と別ファイルではあるが、実走世代数を WAL または層 3 から独立再導出した値ではない。
- 原典: `/work/1/SFC/tanab/dev-wave-jobs/t822-evidence-gaps/s2-plan.md:3-24`、`orchestrator/campaign/p3_s4_loop.py:630-665`、同 `:689-741`、`orchestrator/campaign/layer3_report.py:504-529`、`orchestrator/campaign/autonomous_trial_completeness.py:3242-3269`
- なぜ real か / なぜ refuted か: 原典自身が checkpoint は抽象状態の射影で、正本は WAL と記す。`state_from_dict` も「iteration 整合・entry 件数・campaign/run origin は検査しない」と明記し、保存は last-writer-wins である。Layer 3 と cross-binding が checkpoint から意味として読むのは `whiteboard` だけで、`iteration` は artifact hash に含まれるだけである。同じ走行側が report、journal、checkpoint を `2` に揃えれば、提案された四者等式は通る。
- 成果物影響: 実 CCBench 実行が 2 世代未満でも、4 値を同じにした bundle は新 gate を通る。しかも現行 receipt と `AcceptanceSummary` は構造的に `certifying=False` なので、brief の「certified 受理集合が狭まる」という成果物影響も現状では誤りである。変わるのは非 certifying receipt の発行集合である。

### 所見 6: P2 は弱い自己整合検査についてだけ成立する

- 主張: `trial_registry.py` だけで実装できるのは checkpoint hash と自己申告値の照合までで、要求された独立証明を実装するには completeness または producer/L3 の変更が必要である。
- 原典: `/work/1/SFC/tanab/dev-wave-jobs/t822-evidence-gaps/s2-plan.md:48-55`、`orchestrator/campaign/autonomous_trial_completeness.py:3175-3239`、同 `:3761-3797`
- なぜ real か / なぜ refuted か: cross-binding receipt が返すのは `artifact_refs` の path/hash であり、世代数の意味的射影ではない。`trial_registry.py` で raw JSON を再解釈すると、cross-binding consumer の責務を重複実装するだけで origin と WAL 対応は増えない。実保証にするには、completeness が checkpoint originと世代対応を検証して意味付き射影を返すか、各世代を campaign WAL に記録して Layer 3 が再構築する必要がある。
- 成果物影響: 現プランの 2 file 変更では偶発的不一致だけが拒否され、整合した虚偽 bundle の受理集合は変わらない。正しい修正は競合中の `autonomous_trial_completeness.py` を含むため、P2 の条件に従えば着地待ちへ戻すべきである。

### 所見 7: プランは現在の受理集合を広げないが、絶対規律 2 の恒真保証禁止に触れる

- 主張: hard failure 自体は受理集合を狭めるが、同一 producer の checkpoint を「独立証拠」と呼んで完了根拠にする点が恒真な保証である。
- 原典: `/work/1/SFC/tanab/dev-wave-jobs/t822-evidence-gaps/s2-plan.md:71-107`、同 `:121-135`、`CLAUDE.md:45-52`
- なぜ real か / なぜ refuted か: mismatch を例外にする方向は規律 2 を緩めていない。しかし no-build/campaignless を証明外へ残し、full-build でも同じ走行主体の 4 値一致だけを見る述語を「独立再導出」としている。これは検査を弱めるコードではなく、弱い述語を強い証明として扱う意味論上の緩和である。
- 成果物影響: 現在の certified 選択は変わらないが、T-1211 と D863 を閉じたと記録すると、将来の certifying issuance がこの虚偽の完了状態を参照する。台帳上は T-1211、P1、P2、D863 の第 1・第 2・第 3 条件を open のまま残す必要がある。

## 総括

- 第 1 項は反証できた。no-build は層 3 関数を呼ばず、campaignless failure は呼んでも鎖検証を迂回する。
- 第 2 項は反証できた。arm bytes は provider 入力まで届くが、proposal と実 build・CCBench source の因果束縛がない。
- 第 3 項は部分反証できた。共通 `measurement_head` 自体は保証されるが、環境・ratified generation・実走 producer の一致ではない。
- P1、P2 は反証できた。`loop_state.iteration` は同一走行側の未検証 checkpoint で、正しい修正は trial_registry 単独では完結しない。
- 現プランは受理集合を広げないが、恒真な保証を完了根拠にするため、このまま実装へ進めるべきではない。