## 結論と調査範囲

**現行契約のまま在庫を増やせる可能性はあるが、この段で調達可能と確認できた適格赤は 0 件である。** 自然発生した diff-quarantine 赤を記録する経路は実在する。一方、現在の在庫からの回収も、既存 base campaign の単純継続も成立しない。

指定された 7 ファイルをすべて読了し、対象 worktree の `HEAD=d97c423bdd14e0b416cb4f585d350e6c2b251287` と照合した。親 checkout の作業ファイルは読んでいない。実測場所は `pegasus02`、実行は読み取りのみである。

出力先ファイルのパスが提示されておらず、ファイル書込みも禁止されているため、本回答を成果物本文とする。ファイル作成・編集・commit・campaign 実走は行っていない。

以下の実装パスはすべて指定 worktree 内の `orchestrator/campaign/` 配下、事前登録は `docs/phase3-b4-reflux-ablation-preregistration.md` を指す。

## P1-a — 記録クラスとして支持。ただし発生原因の限定には反証

base の `rejected` 書込みは、次の３経路である。

|実装位置|逐語・分岐|
|---|---|
|`p3_s4_loop.py:1872–1877`|`record_diff_reject(...)` → `project_whiteboard(state, planner, "rejected")`。preflight rejection|
|`p3_s4_loop.py:1894–1899`|同上。`--no-build` の検疫 rejection|
|`p3_s4_loop.py:1906–1911`|同上。build 有効経路の検疫 rejection|

`p3_s4_loop.py:942` は記録契約を明記している。

> `diff 検疫 reject を WAL に BUILD_START→ABORT(reason=diff-quarantine) で焼く。`

評価後は、certified の場合だけ `success`、それ以外は次の記録になる。

> `project_whiteboard(state, planner, "fail")`  
> — `p3_s4_loop.py:1968`

重複した既存 aborted variant も `:1792` で `fail`。sort は `p3_s4_loop_sort.py:431`、trigger は `p3_s4_loop_trigger_gating.py:854` が同じ分類である。したがって、通常の verify / liveness 赤だけでは第１項の `whiteboard.result == "rejected"` を満たさない。

ただし、「diff 検疫 reject だけ」を**原因**の限定として読むなら反証がある。

- sort の `p3_s4_loop_sort.py:237–265` は SWO oracle の `REJECT` を `DiffRejectSubtype.SORT_SWO_ORACLE` に包み、`record_diff_reject` と `rejected` に送る。
- 同ファイル `:270–272` は同じ経路に `auditor gate reject` があることを明示する。
- trigger の `p3_s4_loop_trigger_gating.py:546–557` も `apply_mandatory_deny_only_veto(...)` の拒否を同じ経路に送る。

つまり、**記録上は diff-quarantine に限られるが、その原因は純粋な diff 検査だけではない。** もっとも §5 の選択済み driver は base（事前登録 `:158`）なので、sort / trigger の赤を代わりに採る案には使えない。

解析 adapter もこの区別を保存する。

> `terminal_reason == "diff-quarantine"` かつ `whiteboard_result ... REJECTED` → `B4BlockStatus.REJECTED`  
> その他の `ABORT` かつ `... FAIL` → `B4BlockStatus.ABORTED`  
> — `p3_b4_analysis_adapter.py:497–508`

これは**アーム結果の写像**であり、precursor の `fail` を適格な `rejected` に読み替える許可ではない。

## P1-b — 一律の因果関係は反証。現時点の適格未確定は支持

適格性判定は、呼び手から渡された真偽値を使う。

> `and attempt.calibrated_workload_member`  
> `and attempt.bootstrap_member`  
> `and attempt.reference_is_unique`  
> `and not attempt.arm_digest_received`  
> — `p3_b4_analysis_ledgers.py:928–931`

入力型にもそのまま３つの `bool` がある（同ファイル `:136–142`）。型検査は `:331–338` であり、この関数自体が §5 の値セルを読んで所属・一意性を立証するわけではない。**真を渡せることと、正直に真と認定できることは別である。**

特に母集合欄を先行条件にすると依存関係が逆転する。事前登録 `:196–198` は、

> 「その規則から一意に決まる `analysis_manifest` が実在し」  
> 「その artifact path と sha256 と行数、および `scheduled_attempt_registry` の artifact path と sha256」

を書けるときに初めて記入可能としている。母集合欄は適格判定と選択の**結果**であり、その空欄だけで `bootstrap_member` を偽・判定不能と確定してはならない。

正しい必要条件は次のとおり。

|判定|必要な根拠|
|---|---|
|`calibrated_workload_member`|採用された校正済み `PerfConfig` の workload と当該走行との一致。対象 workload は全件使用|
|`bootstrap_member`|事前固定した bootstrap 集合の実体・固定時点と初期 proposal の一致|
|`reference_is_unique`|最初の certified 祖先が一意で、その throughput receipt が `PerfConfig`・`env_tag` の一致で特定できること|

根拠は事前登録 `:442–445`、`:572–580`。現在の §5 の校正欄・環境欄が未記入なのは `:163`、`:165` で確認した。また、

> 「性能比較用 calibration ではない」  
> — `p3_s4_loop.py:1566`

なので既定 `PerfConfig` を代用品にはできない。

**今日得た `rejected` 行を直ちに適格と呼べない、という結論は支持する。ただし「３欄が空欄だから３真偽値とも必ず確認不能」という説明は採らない。** Bootstrap の先行固定や適合する参照証拠の実在は、それぞれ独立に確認すべき事項である。

## P1-c — 新規の研究在庫の供給方針として支持

D1936 項８の逐語 `d1936-item8.md:5–7` は、

> 「合成ループから得た適格な少数の赤precursorを使い」  
> 「母集合を作るための追加基盤は採らない」

としている。検疫を意図的に落とす手作り proposal・生成器・fixture 経路は、今回の明示禁止事項にも該当する。

実装も通常 campaign の説明で、

> `fixture red を正系列に混ぜない`  
> — `p3_s4_loop.py:1512`

としている。

ただし「実走」を build 到達と同一視してはいけない。自然な proposal が検疫で拒否されれば、`p3_s4_loop.py:1913` で返り、build は始まらない。それでも正常な供給候補になり得る。

また `--no-build` でも `rejected` 行は作れるが、同ファイル `:2527–2529` は、

> `No-build is a wiring-only path, including machine/auditor rejects.`  
> `Its WAL ... is not an admitted campaign consumer input`

と明記する。これは第１項の素材を観察する経路であって、**適格在庫の調達完了を保証する経路ではない。**

## P1-d — 支持。ただしこの Codex セッションでの実行可能性とは別

実装の説明は明確である。

> 「実 LLM (planner/coder/critic) はメインセッションが spawn する」  
> — `p3_s4_loop.py:2544`

> 「実 planner/coder proposal (JSON) を受けて checkpoint 継続で 1 iteration を回す」  
> — `p3_s4_loop.py:2568–2569`

実処理も `:2768` で `load_proposal_file(...)`、`:2783` で `drive_iteration(...)` を呼ぶ。`load_proposal_file` の説明も `:2264` に「メインセッションが spawn した planner/coder の構造化出力」とある。

したがって、この CLI の起動だけでは自然な新規 proposal は供給されない。

なお `.codex/agents/README.md:15` は `runtime activation | active 0 / blocked 14`、`:38–39` は generic child を dormant role の代替にしてはならないとする。既存の適法な Claude role 実行面での供給と、この read-only Codex 段での実行を混同しない。

## 許容される在庫増加経路

選択済み base、現在確認した実装・成果物の範囲では、供給経路は以下に整理できる。新しい供給源・driver への変更は含めない。

|経路|前提・所要|成果物・凍結契約|今回の判定|
|---|---|---|---|
|既存の自然発生赤を whiteboard から回収し、未確認だった適格性を確認する|既存 `rejected` 行と対応する実測証拠。新規 LLM/build 不要、読取り・照合のみ|元の whiteboard、WAL、proposal、bootstrap 固定証拠、参照 receipt。§5.1.1 全条件と全件保持を適用|現在の３ campaign は全７行 `success`。回収可能数０|
|継続可能な通常 base campaign で自然な proposal を処理する|既存 role による通常の合成。digest 非汚染、事前固定 bootstrap、校正 workload、共通参照点を満たすこと。拒否発生までの回数・時間は不明|`--run-iteration` → 検疫拒否 → WAL と whiteboard、checkpoint。`p3_s4_loop.py:2498–2510`。赤以外・失敗も保存|経路は実在。ただし現存 base checkpoint は wall budget 超過で単純継続不可|
|別途正当に開始される通常 base campaign の自然発生赤を受け取る|通常研究目的の campaign 開始、既存実行面・予算・環境。赤のためだけの再試行・campaign 量産はしない|同じ供給源・同じ契約。独立した正当な campaign identity と予定 attempt 全件の証拠が必要|条件付きの将来経路。今回、実行可能な開始入力一式までは確認していない|

後二者は同じ供給機構の継続／新規開始である。保存済みの自然な proposal を処理する場合も、その一部として扱う。結果を見て失敗しそうな proposal だけ選ぶ経路は設けない。

`--no-build` は生死確認用の補助経路に留める。verify / liveness の `fail`、digest 単独、fixture、sort / trigger、成功例を使う追加経路は採らない。

すべての候補で、**赤が出ること、適格であること、201 行の manifest が生成できることを別々に判定する。** `p3_b4_analysis_ledgers.py:1076–1083` は適格行が不足すれば `B4DesignNotFeasible`、十分なら先頭201行とする。

## DW-G01 — 現在の在庫と単純継続の生死を先に確認する

最安の確認は、**「現物から１件回収できるか。なければ既存 base campaign をそのまま継続できるか」**の読取り probe とする。以下は100行以内の使い捨て shell driver に相当し、今回実行済みである。

指定 worktree を cwd として実行する exact command：

```bash
jq -s '{files:length,rows:([.[].whiteboard[]]|length),rejected:([.[].whiteboard[]|select(.result=="rejected")]|length),base:{iteration:.[0].iteration,start_wall:.[0].start_wall,budget_iterations:(.[0].iteration>=10),budget_walltime:((now-.[0].start_wall)>=3600)}}' output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/loop_state.json output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d/loop_state.json output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/loop_state.json
```

期待値と実測値は一致した。

```json
{
  "files": 3,
  "rows": 7,
  "rejected": 0,
  "base": {
    "iteration": 4,
    "start_wall": 1783558138.794761,
    "budget_iterations": false,
    "budget_walltime": true
  }
}
```

停止判定の根拠は次の逐語である。

> `MAX_ITER = 10` / `MAX_WALLTIME_S = 3600`  
> — `p3_s4_loop.py:164–165`

> `elapsed = time.time() - state.start_wall`  
> `return StopDecision(True, "budget-walltime")`  
> — 同ファイル `:1265`、`:1271`

入口停止なら `run_one_iteration` を呼ばず、`"ran": False` を返す（`:2488–2493`）。

**判定：現在の在庫回収と既存 base の単純継続は NO-GO。** Checkpoint の時刻や予算を書き換えて再開する案は採らない。

これは新しい通常 campaign で自然な赤が生じないことの証明ではない。自然発生率を測る live probe は未実施であり、この読取り結果をその成功・失敗に代用しない。

## 律速と本 wave の変更計画

**現在、最初に確定している不足は供給０件である。適格性確定側も独立した未充足条件であり、どちらが所要時間の律速かは未測定である。**

供給だけ増やしても、校正 workload・事前固定 bootstrap・一意な参照点・digest 非汚染の証拠がなければ適格在庫は増えない。逆にそれらを整えても、現存７行から赤は得られない。

本 wave 内で閉じられる内容は以下とする。

1. 今回の計数、書込み経路、停止条件、P1 の訂正を確定する。
2. 親の段４で、既存の通常合成 campaign から供給を得る実行面・入力・予定が実在するかを判断する。
3. 実在する場合だけ、既存経路で自然な結果を採取する。赤１行取得は brief の第１項に関する達成とし、適格性全体の達成とは分けて報告する。
4. 実在しない場合は「この wave では調達不成立」と記録する。自然発生が構造的に不可能と一般化しない。

**実装面は差分ゼロを推奨する。** 次の既存箇所を使用・維持する。

|file:line|計画|
|---|---|
|`p3_s4_loop.py:2567`、`:2768`、`:2783`|既存 proposal 入力・iteration 経路を使用。LLM driver を新設しない|
|`p3_s4_loop.py:1872–1913`、`:1968`|現在の reject / fail 分類を維持|
|`p3_b4_analysis_ledgers.py:922–936`|適格性述語を変更しない|
|同 `:1050–1105`|201行・順序・選択規則を変更しない|
|`p3_b4_prerun_issuer.py:835–843`|不足時の `"fewer than 201 eligible scheduled attempts"` を維持|

別タスクへ送るのは、採用する校正・環境・bootstrap・参照証拠の整備、必要な通常 campaign の実行、B-4 全体の残存解除条件である。少数在庫で実走できるかは **T-2633** に残す。

なお校正・成果物採用を一律に「新規ユーザー承認待ち」としてはならない。事前登録 `:1128–1136` は D1641/D1812 による既存の AI 委任を明記している。別タスクはその適用範囲を確認して進める。

## 不成立時に insight へ残す最小記録

- **対象固定**：日時、hostname、worktree、HEAD、読んだ３つの checkpoint の path・sha256。
- **再現可能な観測**：上記 exact command、stdout、７行すべて `success`、`rejected=0`。mtime は根拠にしない。
- **供給分類**：全 whiteboard 書込み位置、diff-quarantine と `fail` の違い、sort / trigger の原因分類に関する留保。
- **停止理由**：既存 base の `start_wall`、１時間上限、入口停止の実装位置。
- **適格性の未確定事項**：校正 workload、bootstrap 固定証拠、祖先・receipt、digest 非汚染。母集合欄の空欄を循環した理由にしない。
- **到達範囲**：「第１項該当数」「全条件適格数」「manifest 成立」を分ける。未実施の合成・計測を明記する。
- **再開条件**：正当な通常 base campaign の新しい whiteboard／実行予定と、必要な適格性証拠が得られたとき。T-2633 の裁定だけでは赤０件は解消しない。
- **不採用経路**：digest 単独、fixture、故意の検疫失敗、成功例置換、driver 変更、n 削減を採らなかったこと。

任意パスとして参照を試みた `p3_b4_prerun.py` と `p3_b4_proposal_binding.py` は存在しなかった。前者の実処理は実在する `p3_b4_prerun_issuer.py`、proposal 読込みは `p3_s4_loop.py` で確認したため、調査は継続した。

## 総括

- **在庫を０から増やせるか：条件付き。** 通常 base 合成で自然な検疫赤が生じ、凍結済み適格条件を証拠で満たす必要がある。現在確認済みの適格在庫は０件。
- **本 wave で閉じられること：** 差分ゼロで在庫・記録経路・既存継続不可を確定し、調達可否を記録する。新規供給の構造的不可能までは証明していない。
- **別タスクへ送ること：** 通常合成の実行と適格性証拠の整備、B-4 残存解除条件。少数実走と201行契約の関係は T-2633 に残す。