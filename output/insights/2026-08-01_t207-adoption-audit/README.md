# [T-207] `codex/p3-autonomous-trial` 取り込み監査 (2026-08-01)

CLAUDE.md 規律 6 の「別セッション/別 AI の作業物の取り込み時には独立コンテキストでの
敵対裏取り (real/refuted 選別) を行う」に基づき、`codex/p3-autonomous-trial` (tip `402086d`) の
未 land 成果 1,907 行を main へ取り込む前に実施した監査の正本である。

## 対象

2026-07-29 に別セッションが作り、一度も land されていなかった 5 ファイル。

| ファイル | 行数 |
|---|---:|
| `orchestrator/campaign/p3_autonomous_workload_trial.py` | 1070 |
| `orchestrator/campaign/claude_projected_provider.py` | 290 |
| `orchestrator/tests/test_p3_autonomous_workload_trial.py` | 280 |
| `output/insights/2026-07-29_t178-autonomous-ycsb-abc-dry-run.md` | 131 |
| `docs/phase3-s8c-autonomous-trial-runbook.md` (取り込み時に改名) | 136 |

## 逐語

- `s2-integration-plan-verbatim.md` — 段 2 統合プラン起草 (codex `gpt-5.6-sol`、reasoning=max、read-only)
- `s3a-integration-scope-verbatim.md` — 段 3 敵対レンズ A (統合手順と scope の整合・実効性)
- `s3b-discipline6-audit-verbatim.md` — 段 3 敵対レンズ B (規律 6 の取り込み監査)

## land stopper 3 件の裁定 (段 4、親 → 段 6 で 2 件を再裁定)

レンズ B は「現状のまま land 不可」として land stopper 3 件を挙げた。親が 1 件ずつ裏取りし、
段 6 のレビュー B が親の裏取り 2 件を反証したため、**段 6 で LB-1 / LB-3 の判定を訂正した**。
最終判定は **LB-1 = real (scope 外)、LB-2a = real (本 wave で修正)、LB-3 = real (族既存・scope 外)**
であり、land stopper として本 wave を止めるのは LB-2a だけである。

### LB-1「規律 3 の構造化失敗理由が次世代へ届かない」→ **real / scope 外 / 段 6 で訂正**

**段 4 の初回裁定は refuted だったが、これは誤りである (erratum)。** 親は
`p3_s4_loop.py` の `project_whiteboard()` が「critic の attribution や棄却理由の technical
explanation は載せない — planner がそれを読んで棄却理由から採用値を逆算できる structural
inference リスク (規律2/6)」と意図的に落としていること、および red digest
(`load_rejections` / `load_verify_abort_signals` / `load_diff_rejections`) が存在することを
根拠に refuted としたが、**red digest の到達先は critic であって次世代の planner/coder ではない**。

段 6 のレビュー B が指摘したとおり、8c の次世代 payload
(`p3_autonomous_workload_trial.py` の planner_payload / coder_payload) が受けるのは
descriptor・現行 metrics・leading indicators・**抽象 whiteboard** だけであり、
`_whiteboard()` は `loop_core.whiteboard_for_planner()` (= direction/magnitude/result/delta_pct)
しか返さない。critic の `attribution/recommend/avoid/uncertainty` は
`reverse_recommended` の boolean へ畳まれて停止カウンタになる。

human-supervised loop では、この critic 帰属を**メインセッション (人間側) が消費**していた
(D39)。8c はそのメインセッションを Python へ置換したが、消費の職務を再実装していない。
したがって 8c 自律モードでは、次の variant 生成が受け取るのは「失敗した」「逆方向」までで
「なぜ壊れたか」ではない。**これは規律 3 に対する実在の狭まりである。**

本 wave で実装しない理由は、直せば済む欠陥ではなく設計択一だからである — critic 帰属を
planner 入力へ流すことは D39/D45 が構造的に禁じたリーク経路そのものであり、
「機序を漏らさずに失敗理由だけを還流させる」設計を新たに決める必要がある。
**したがって D106 は運転条件を明記する。** 制限の正しい条件は「正式系列か否か」ではなく
**前 iteration の critic 出力を次世代の生成へ使うかどうか**である。cross-generation 還流が
起きない 1 generation/cell の運転では本欠陥は発火しないため許可し、
**2 generation 以上 (= 還流が起きる運転) を裁定まで禁止する**。正式系列 (H1/H2) は
同一 generation budget を要求するため、この条件により自動的に禁止側へ入る。起票 = [T-238]。

### LB-2a「`--provider fixture` + 実 build を CLI が禁じていない」→ **real / 本 wave で修正**

`--provider {fixture,claude-headless}` と `--no-build` は独立 flag で、`--provider fixture`
かつ実 build が受理されていた。この組合せでは入力を監査せず無条件 `pass` を返す fixture auditor を
積んだまま build → legacy+S2 → bench が走り、COMMIT が campaign 台帳へ入る。legacy+S2 verifier は
生きているので serializability は守られるが、**reward hack の番人である semantic auditor だけが
no-op になる**。8c が新規に持ち込んだ経路であり既存 driver に対応物がない。規律 2 に直接触れる。

→ D106 決定 (6) として CLI 層で fail-closed 拒否し、境界テストを同じ変更単位へ置いた。

### LB-2b「`--claude-executable` が任意バイナリを受理する」→ **real / scope 外**

main に land 済みの `orchestrator/campaign/s8b_prediction_runner.py` も
`claude_executable_sha256` を**記録するだけで承認 hash と照合しない** (絶対 path であることだけを
要求)。8c provider は同じ族の作法を踏襲しており新規の緩みではない。族全体の trust root 新設は
`DW-G03` (族一般化には独立 2 例) と D96 の手続に従う別裁定 → [T-236]。

### LB-3「探索 run を公式 `output/campaigns/` へ書く (D65 違反)」→ **real / 族既存 / scope 外 / 段 6 で訂正**

**段 4 の初回裁定は refuted だったが、これも判定語が誤りである (erratum)。** 親が確認した事実
—— main に land 済みの既存 s4 driver (`p3_s4_loop_trigger_gating.py`、`p3_s4_loop_sort.py`) も
build 時は同じ `campaign_layout()` → `output/campaigns/` を使い、`ExplorationCampaignLayout` の
production consumer は `s8b_oracle_exploration.py` **1 件だけ**である —— は正しい。
しかし段 6 のレビュー B が指摘したとおり、**既存 producer も同じ挙動であることは D65 適合の
証拠にならない**。D65 決定 (2) の本文は「探索は `output/exploration/campaigns/`」と書いており、
s8b 族に限定していない。

したがって正しい判定は「**D65 の文言に対しては実在の逸脱。ただし 8c 固有ではなく s4 driver 族
全体の既存挙動であり、本 wave で 8c だけを移すと族内で二重規範になる**」である。
族全体の namespace 移行として別裁定へ送る → [T-237]。**8c を「D65 適合」とは記述しない。**
D65 が既に「探索は exploration namespace」と決定済みである以上、`DW-G03` は未遵守を続ける
理由にはならない — 族単位でまとめて是正するという**順序**の理由にとどまる。
なお LB-3 の解消は LB-1 の裁定とは独立であり、LB-1 が裁定されても LB-3 は閉じない。

また、`output/autonomous-trials/` は D13 の二軸 (campaign / env) にも D65 の exploration
namespace にも属さない第三の root である。本 wave では `output/README.md` へ
「探索の運用記録であって正式 proof chain ではない」と自然言語で登録するに留めた。
型・path による機械的な防壁は無く、これも [T-237] の族単位裁定に含める。

## 説明と実装の食い違い 6 件 (段 4 で 4 件、段 6 で 2 件を追加。docs を訂正して land)

起草時の D99 本文・runbook・phase3 が主張していたもののうち、実装で裏が取れないもの。
**本表がこの wave の correction ledger の正本であり、D106 と phase3.md はこの 6 件を指す。**

| # | 起草時の主張 | 実装 | 訂正先 |
|---|---|---|---|
| 1 | 「supervisor は既存 pipeline を迂回・**再実装しない**」 | `_preview()` が DiffQuarantine と禁止識別子検査を supervisor 側でも再実行する (pre-audit)。authoritative path が後段で再検査するため受理集合は広がらないが「再実装がない」は偽 | D106 決定 (1)、runbook §1 |
| 2 | 「`max-wall-seconds` は supervisor 全体の上限 / safety 上限」 | 時刻検査は workload と generation の**先頭だけ**。期限超過後も、その generation の coder・auditor・drive/build・critic を新たに開始する。上限ではなく「**次の境界で開始を止める閾値**」である | D106 決定 (4)、runbook §5、phase3.md |
| 3 | 「mediated schema を object 配列へ明確化した」 | top-level は exact だが、配列要素は `dict` 判定だけ。`{}`・未知キー・非文字列 field を含む要素が通る | D106 決定 (4)、runbook §5 |
| 4 | 「diff と designated context **だけ**を auditor へ渡す」 | 実 payload には workload / descriptor / generation / policy を含む common 部も入る | runbook §1 |
| 5 | 「source role SHA + effective prompt SHA + payload/envelope SHA + session/model/token provenance を**全 attempt に**束縛」 | `_invoke()` の invalid 分岐は `error_artifacts` (payload/envelope の path と SHA) だけを journal へ書き、`response.provenance` を捨てる。さらに valid 分岐でも token 数は**検査するだけで provenance へ保存しない**。fixture provider の valid attempt は session / token / envelope をそもそも持たない | phase3.md、D106 決定 (2)、runbook §4 |
| 6 | 「resume は MVP 範囲外」(= 前回状態を引き継がない、と読める) | fresh 検査は外側 `run_root` だけ。同じ workload/config なら campaign id は内容 hash で同一になるため、**別の `--run-root` を指定しても build 側は同じ公式 campaign root を再利用し、planner 前に旧 `loop_state.json` を読む** | D106 残余、runbook §5 |

加えて、report の `fresh_context` / `observed_tool_events` / `fixed_generations` /
`performance_early_stop` / `scientific_claim` は**実挙動から導出した観測ではなく literal**で
あることを runbook §5 と D106 決定 (2) へ明記した。ただし段 6 のレビュー B の指摘に従い、
**5 field を同列の「恒真ゲート」とは呼ばない** — `scientific_claim` は gate ではなく意図的な
scope label であり、`fresh_context` / `observed_tool_events` の周辺には `num_turns`・session-id・
permission denial・server-tool counter の部分検査が実在する。正確な言い方は
「**これらの field 自体は実証ではない**」である。

## 番号衝突 3 件 (分岐中に main が同じ番号を別内容へ使用)

| 衝突 | branch 側の意味 | main 側の意味 | 解消 |
|---|---|---|---|
| `D99` | 8c bounded trial の設計裁定 | `[T-143] RuleOps v1` | `D106` へ採番 |
| worklog `(61)` | 8c 実装 wave | `Codex dev-wave 資源効率監査` | verbatim 追記せず本 wave の新エントリへ要約収容 |
| `T-179` | live build pilot の再開タスク | `worker 資源台帳` (完了済み) | `T-235` へ採番 (insight 2 箇所) |

## refuted された懸念 (親 brief・段 2 が過大に恐れていた点)

レンズ B が独立に refuted と判定したもの。

- 通常の authoritative drive は全 gate を再実行するため、pre-audit の重複は受理集合を広げない
- `--no-build` は correctness / 性能認証へ昇格しない (`dry-pass` 止まり)
- planner justification / uncertainty の coder へのリークは v3 でコード・実 payload とも塞がれている
- env allowlist は正確に `PATH/HOME/LANG/LC_ALL/TERM` の 5 変数
- production provider に supervisor 水準の retry loop はない
- CLI の競合 `ycsb_*.exe` 検査と pinned disposable worktree は実装済み
- `numactl` を空 command へ置換する入口はなく、不在 host で bench まで成功する経路はない
- 現 main との API rename / signature drift はない
- insight の定量値 (6 SHA、12/12 valid、3/3 dry-pass) は捏造でなく、現存 artifact と byte 一致
- source role 本文は外部入力ではなく repository 内 byte を read-once / hash している

## 親自身の実測値に対する訂正 (レンズ A の指摘、採用)

- 「取り込み対象テスト 5 passed (request `875777.nqsv`)」が保証するのは **merge 前・単独ファイル走行**
  だけである。主要 trial test は `_fake_drive()` / `_fake_preview()` を注入しており、実 preview、
  `drive_iteration()`、build、legacy+S2、bench を一度も通していない
- 「`check_docs.py` 緑」は **5 ファイルだけを staged した snapshot** の結果で、merge 後 docs の緑を
  含意しない
- 「pin 閉包 0 件」は basename の直接 literal 参照が 0 件であることの確認にすぎず、glob・
  directory scan・HEAD inventory・README allowlist を原理的に拾わない。実際 holdout freeze scan の
  `file_count` と RuleOps の動的 inventory は対象集合が増える (受理結果は不変)
- したがって正しい不変条件は「既存 tracked bytes と certified acceptance は不変。
  動的 inventory / scan の対象集合は意図どおり増える」である
