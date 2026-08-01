## 総括

- **高 / must-fix / NO-GO:** 壊れた `loop_state.json` の `ValueError` / `WhiteboardLeakError` が `_assert_fresh_campaign_state()` から素通しになる。CLI は partial report に収容するが、direct API の例外契約と report のエラー型が不安定。
- **高 / must-fix / NO-GO:** 変異 V1 は、別の fixture+build 拒否により診断文字列の違いだけで赤くなる。DW-M03 上 KILL と数えられない。
- **中 / land 前 must-fix:** 現在の差分には新 D と docs 追随がなく、D96 の「新 D」要件は未充足。既定値変更による campaign ID・report・journal の実値変更を必ず記録する必要がある。
- **低 / nit:** V2 は受理集合拡大の証拠ではなく「artifact 作成前拒否」の冗長外側 gate の証拠。V3 は単独変異として成立する。
- **正当運用:** 現 runbook の正規 3 手順に freshness gate 由来の新規失敗はない。現 worktree の `output/campaigns/` に 8c checkpoint も存在しない。

## 所見

### B-01 — 壊れた checkpoint が supervisor 例外へ正規化されない

何が壊れるか:

[`_assert_fresh_campaign_state()`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:198) は `load_loop_state()` を無捕捉で呼ぶ。後者は JSON/schema 異常時に `ValueError`、`delta_pct` leak 時にその subclass である `WhiteboardLeakError` を投げる。[p3_s4_loop.py:343](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_s4_loop.py:343) [p3_s4_loop.py:421](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_s4_loop.py:421)

したがって direct `_run_workload()` では素の例外が貫通する。正規 `run_trial()` 経路では広い `except Exception` に収容され、partial report と CLI rc=2 になるため、CLI 全体が traceback 終了するわけではない。[p3_autonomous_workload_trial.py:954](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:954) [p3_autonomous_workload_trial.py:1089](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:1089)

それでも F68 型である。`report.json.fatal_error.type` が `AutonomousTrialError` でなく `JSONDecodeError` / `ValueError` / `WhiteboardLeakError` に揺れ、direct API は supervisor 契約外の例外を返す。

必要な修正:

- `_assert_fresh_campaign_state()` 内で checkpoint の読取・decode・schema 検査失敗を捕捉し、cause を保持した `AutonomousTrialError` に包む。
- 壊れた state を `None`、すなわち fresh と扱ってはならない。
- 実ファイルの壊れた JSON、および `delta_pct != None` の checkpoint を使う境界テストを追加する。現テストは loader を `LoopState()` / `None` に monkeypatch するだけで例外経路を覆わない。[test_p3_autonomous_workload_trial.py:236](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/tests/test_p3_autonomous_workload_trial.py:236)

成果物影響: 放置すると、同じ破損 checkpoint に対する terminal report の `fatal_error.type` と direct caller の結果契約が入力形状次第で変わり、report のエラー分類が安定しない。

判定: **must-fix**。

### B-02 — V1 は別 gate による診断差だけで赤くなる

V1 の期待 node は `--provider fixture` を指定しながら `--no-build` を付けていない。[test_p3_autonomous_workload_trial.py:353](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/tests/test_p3_autonomous_workload_trial.py:353)

`main()` の generation validator を削除しても、その直後の fixture+実 build gate が同じ invocation を拒否する。[p3_autonomous_workload_trial.py:1051](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:1051)

したがって変異後も:

- invocation は拒否される。
- build preparation には到達しない。
- `run_root` も作られない。
- テストが赤くなる理由は `match="承認済み上限"` と別 gate のメッセージが一致しないことだけ。

これは DW-M03 が明示的に KILL から除外する「診断文字列だけの赤」である。`--provider claude-headless` の正当な build 経路に差し替え、validator 削除時に `competing_bench_pids()` 等の sentinel へ実際に到達させる必要がある。

成果物影響: 放置すると、変異台帳 V1 が実際には維持されている拒否を KILL と誤記し、受理集合防壁の証拠参照が偽になる。

判定: **must-fix**。

### B-03 — V2 / V3 の単一理由性

- **V2:** `run_trial()` の検査を消しても `_run_workload()` の検査が残る。[p3_autonomous_workload_trial.py:643](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:643) その時点までに `run_root`・journal が作られ、内側例外は partial report に収容されるため、期待テストは「artifact-free な早期拒否を失った」という一理由で赤くなる。[p3_autonomous_workload_trial.py:897](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:897)  
  **有効だが、受理集合拡大の KILL ではなく、冗長な外側 gate の fail-before-artifact 証拠として記録すべき。**
- **V3:** direct `_run_workload()` には他の budget validator がない。削除後はテスト fixture の wall budget が既に満了しているため provider を呼ばず正常 return し、拒否集合が実際に広がる。[test_p3_autonomous_workload_trial.py:219](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/tests/test_p3_autonomous_workload_trial.py:219)  
  **単独変異の証拠として成立する。**

判定: V2 の台帳分類だけ **nit**。V3 は問題なし。

### B-04 — CLI 既定値変更は campaign identity と成果物値を変える

事実は正しい。`generation_budget` は `search_config` に入り、[p3_autonomous_workload_trial.py:435](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:435) `canonical_preimage()` は `search_config` 全体を hash 対象にする。[ident.py:76](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/ident.py:76)

例えば `live-abc-g1 / ycsb-a` は同じ identity helper で:

- budget 2: `p3-t178-ycsb-a-workload-conditioned-autonomous-b993f4a3`
- budget 1: `p3-t178-ycsb-a-workload-conditioned-autonomous-61441b66`

となる。さらに journal と report の `generation_budget_per_workload` も 2 から 1 に変わる。[p3_autonomous_workload_trial.py:909](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:909) [p3_autonomous_workload_trial.py:989](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:989)

波及検索の結果:

- runbook 3 例はすべて `--max-generations 1` を明示しているため、既存例の identity は変わらない。
- 所有外の Python caller・scheduler は見つからない。
- `FROZEN_MANIFEST`、role review ledger、他テストに 8c campaign ID や当該 module SHA の pin はない。
- 歴史 insight の dry-run は budget 1 で、正式 freeze ではない。
- `output/campaigns/` に `p3-t178-*` directory、`workload-conditioned-autonomous` lock、8c `loop_state.json` はいずれも 0 件。

ただし外部環境に旧 default=2 campaign があれば、同じ flag 省略 invocation は別 IDへ移り、明示 `2` も新 gate が拒否するため、その campaign をこの supervisor から継続できなくなる。これは意図した縮小だが、新 D の成果物影響に必要である。

成果物影響: flag 省略時の campaign ID/root、journal budget、report budget、生成・certified 候補の最大件数が変わる。

判定: コード変更自体ではなく、**新 D・runbook・phase3 への記録が land 前 must-fix**。

### B-05 — 保証名には過大・過小の両方がある

過大記載:

- 「既存 campaign state」は広すぎる。拒否するのは `load_loop_state()` が検出する `loop_state.json` であり、`campaign.lock`、WAL、provenance だけが残る layout は受理する。
- 「fail-closed」は provider 非到達という意味では成立するが、B-01 を直すまでは supervisor 例外型まで閉じていない。
- 「3 層で artifact 作成前」は、`main()` と `run_trial()` では成立するが、direct `_run_workload()` について保証できるのは「同関数の下流処理前」まで。caller が既に作った artifact は対象外。

過小記載:

- `_run_workload()` に exact-int、bool、絶対範囲 `1..10` の契約も新設された。従来正常 return した `0` や `True`、後段 `TypeError` になった `1.0` も早期 `AutonomousTrialError` へ変わる。
- CLI default は単に現在 1 なのではなく、`MAX_APPROVED_GENERATIONS` から意図的に独立した literal 1 として AST 固定されている。[test_p3_autonomous_workload_trial.py:88](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/tests/test_p3_autonomous_workload_trial.py:88)
- freshness gate は build/no-build 両 layout と injected provider 経路にも掛かる。ただし injected `drive` が一 callable 内で複数 iteration を回すことまでは防がない。

判定: docs の保証名修正が **must-fix**。

### B-06 — D96 は現 snapshot では未充足

D96 は新 D と境界テストを同じ変更単位に要求する。[decisions.md:4271](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/docs/decisions.md:4271)

現 `git diff` は実装・テストの 2 ファイルだけなので:

- 新 D: **未充足**
- 境界テスト: **概ね正しく同定済み**

境界テストの正確な分類は次のとおり。

- generation の一次境界: `test_generation_budget_boundary_at_ratified_launch` の literal 1/2。[test_p3_autonomous_workload_trial.py:71](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/tests/test_p3_autonomous_workload_trial.py:71)
- freshness の一次境界: `test_run_workload_rejects_existing_campaign_state` と `test_run_workload_accepts_fresh_campaign_state` の正負 pair。
- 入口・副作用境界: `main` / `run_trial` / direct `_run_workload` の3テスト。
- 型境界: bool、0、1.0。
- AST default test: 受理集合境界ではなく F69 対策の構造 pin。

したがって裁定の境界同定は generation/freshness について正しい。ただし B-01 の壊れた checkpoint 境界が欠け、V1 fixture は無効である。

成果物影響: 新 D なしで land すると、変更された campaign 受理集合と identity を説明する設計台帳参照が存在しない。

判定: **stage 7 で同一 commit に新 Dを含めるまで must-fix**。

## 正当運用の破壊検査

| runbook / 運用 | layout と identity | freshness gate の結果 | 新規破壊 |
|---|---|---|---|
| §3.1 fixture no-build | `output/autonomous-trials/fixture-abc-g1/campaigns/<workload別ID>` | 新規 root のため通る | なし |
| §3.2 Claude no-build | §3.1 と異なる trial id・run root。3 workload は別 ID | 各 layout が fresh なら通る | なし |
| §3.3 live build | 共有 `output/campaigns/<workload別ID>`。dry-run とは trial id も root も異なる | 現 worktreeには該当 state がなく通る | なし |
| 同じ trial id で no-build 後に build | **runbook にその手順はない。** textual campaign ID は同じだが、no-build は `<run_root>/campaigns`、build は共有 `output/campaigns` | fresh な別 `--run-root` を使えば no-build state は build gate に当たらない。既定 run root を再利用すると従来から run-root gate で拒否 | freshness gate 由来の破壊なし |
| 3 workload を1 invocation | workload は `search_config` と `trial` に入り、A/B/C の layout は分離される。[p3_autonomous_workload_trial.py:428](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:428) | workload ごとに独立検査 | なし |
| crash 後の再実行 | runbook は既に「新しい trial id」を明記する。[runbook:56](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/docs/phase3-s8c-autonomous-trial-runbook.md:56) 新 trial id は canonical preimage の `trial` を変え、新 campaign ID になる | 正当な recovery は通る | **運用文書の追随漏れなし** |
| 同一 build campaign の再利用 | 別 run root でも同じ公式 layout | 新たに拒否 | 意図した縮小。runbook の正当手順ではない |
| 1 cellだけ stale な3-cell invocation | stale cell で supervisor-errorとなり、`break` により後続の fresh cell も走らない。[p3_autonomous_workload_trial.py:954](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/orchestrator/campaign/p3_autonomous_workload_trial.py:954) | invocation の残りを停止 | 文書化すべき nit。現 runbook の新-ID手順では発火しない |
| 現 `output/campaigns/` | `loop_state.json` は s4/s5/s8a の3件のみ。8cは0件 | 既存8c手順を塞ぐ対象なし | なし |

runbook の [143–146行相当](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux/docs/phase3-s8c-autonomous-trial-runbook.md:143) は、現在も「別 run-root で旧 state を読む」と書いており、実装後は「読む前に拒否する」へ更新が必要である。

## 受理集合の正確な記述

以下は新 D にそのまま置ける粒度である。

> **決定:** 8c autonomous workload trial の production 承認済み generation budget は現在 1 generation/cell とする。`generations` は `bool` を除く exact `int` かつ実装上の絶対範囲 `1..10` を満たす必要があり、その後に承認上限 `MAX_APPROVED_GENERATIONS=1` を適用する。したがって現在受理する値は 1 のみで、整数 2..10 は「実装可能だが未承認」、0 以下・11 以上・bool・非 int は契約違反として拒否する。
>
> この検査を CLI `main()`、公開 `run_trial()`、direct `_run_workload()` の3入口に置く。CLI は build preparation 前、`run_trial()` は `run_root` と journal の作成前、`_run_workload()` は同関数の config/layout/provider 処理前に拒否する。
>
> `_run_workload()` は workload/config/trial から導出した campaign layout に対し、最初の provider 呼び出し前に checkpoint freshness を検査する。`loop_state.json` が存在せず loader が `None` を返す layout は受理し、parse 可能な既存 checkpoint は iteration 数・whiteboard 内容にかかわらず拒否する。壊れた、読めない、schema 違反または whiteboard leak を含む checkpoint は fresh と見なさず、supervisor 契約の `AutonomousTrialError` として拒否する。
>
> build なしでは `<run_root>/campaigns/<campaign-id>`、build ありでは共有 `output/campaigns/<campaign-id>` を検査する。同じ trial/config の no-build と build は同じ textual campaign IDを持ちうるが、通常は異なる root に置かれる。A/B/C は workload が identity に含まれるため別 layout である。build campaign では `--run-root` の変更だけでは identity は変わらず、新しい trial id が recovery 境界である。
>
> CLI の `--max-generations` 既定値は literal 1 とし、承認上限定数には連動させない。将来承認上限を引き上げても、別裁定で CLI default を変更しない限り flag 省略運転は 1 のままとする。
>
> この変更により、従来 flag 省略で budget 2 だった invocation は budget 1 となり、campaign ID/root、journal と report の generation budget、role attempt 数、WALへ到達しうる候補集合が変わる。明示 2..10 の CLI/programmatic invocation と、既存 checkpoint を読む build invocationは新たに拒否される。
>
> 本決定は T-244 の規律3還流設計を解決しない。任意注入 `drive` が一 callable 内で複数 iteration を実行する経路、trigger driver の直接呼び出し、checkpoint を持たない campaign.lock/WAL 残骸、freshness check と state 作成の並行 race は保証対象外である。

## docs に必ず含めるべき限定条項

- T-244 本体と規律3の還流設計は未解決であり、残余1の「機械 gate なし」だけを supersede すること。
- D106 残余3は「旧 state を再利用する」から「provider 前に拒否する」へ supersede すること。
- D106 の「最大10世代」は実装上の絶対範囲であり、production 承認上限は1だと分けること。
- D106 決定6の fixture+build programmatic carve-outは残ること。`generations=1, provider_kind=fixture, do_build=True` の直接呼び出しまで閉じたとは書かないこと。
- runbook の「機械 gate は無い」3箇所と、別 run-root で state を読むという説明を更新すること。
- crash recovery は新 trial id であることを維持し、「run-root だけ変更」で十分と書かないこと。
- freshness の対象は `loop_state.json` であり、campaign lock・WAL・provenance 全般ではないこと。
- 壊れた checkpoint は fresh 扱いせず、B-01 修正後の安定した supervisor error にすること。
- 一つの stale workload は generic supervisor-error となり、同 invocation の後続 workload も停止すること。
- no-build/build の root 分離、同一 invocation 内の workload 別 identity 分離を記載すること。
- CLI default 1 と approved max は意図的に非連動で、上限引上げ後も省略値は1のままだと記載すること。
- flag 省略変更で campaign ID、journal/report budget、候補集合が変わること。
- `drive/providers/preview` 注入、driver 直接反復、並行 start race は全面的な cross-generation 禁止保証の対象外とすること。
- `phase3.md` の「説明と実装の食い違い6件」では、campaign state 再利用を現行残余として残さないこと。
- 新 D と全境界テストを実装と同じ commit に含めること。D96 を docs の後続 commit で満たした扱いにしないこと。

## 確認できなかったこと

- sandbox=read-only のため pytest・変異 harness は実行していない。親の計算ノード実走 `19 passed` のみ前提とした。
- V1/V2/V3 の変異結果はコード上の到達経路による静的判定であり、実測台帳は未確認。
- 現 worktree 外の `output/campaigns/`、他ホスト、歴史的 `/tmp/izanagi-t178-live*` に残る artifact は確認していない。
- 段7の新 D・runbook・phase3・D106 supersede はまだ存在しないため、その最終文言と同一 commit 化はレビューできていない。