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

## land stopper 3 件の裁定 (段 4、親)

レンズ B は「現状のまま land 不可」として land stopper 3 件を挙げた。親が 1 件ずつ裏取りした結果、
**1 件が real、2 件が refuted** である。

### LB-1「規律 3 の構造化失敗理由が次世代へ届かない」→ **refuted**

批判された射影は 8c が導入したものではなく、main に既存の `p3_s4_loop.py` の
`project_whiteboard()` が行っている。同関数の docstring は「critic の attribution
(なぜ効いた/壊れたか) や棄却理由の technical explanation は載せない — planner がそれを読んで
棄却理由から採用値を逆算できる structural inference リスク (規律2/6)」と明記しており、
**意図的なリーク制御**である。8c supervisor はこれを継承しただけで、規律 3 の
「なぜ壊れたか」は red digest 側 (`load_rejections` / `load_verify_abort_signals` /
`load_diff_rejections`) から loop 入力に入っており消えていない。

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
`DW-G03` (族一般化には独立 2 例) と D96 の手続に従う別裁定 → [T-222]。

### LB-3「探索 run を公式 `output/campaigns/` へ書く (D65 違反)」→ **refuted / scope 外**

main に land 済みの既存 s4 driver (`p3_s4_loop_trigger_gating.py`、`p3_s4_loop_sort.py`) も
build 時は同じ `campaign_layout()` → `output/campaigns/` を使う。`ExplorationCampaignLayout` の
consumer は `s8b_oracle_exploration.py` **1 件だけ**で、D65 決定 (2) の namespace 分離は
s8b oracle artifact 族の契約である。8c の挙動は既存 s4 族と同一で新規違反ではない → [T-223]。

## 説明と実装の食い違い 4 件 (段 4 で採用、docs を訂正して land)

起草時の D99 本文・runbook が主張していたもののうち、実装で裏が取れないもの。

| # | 起草時の主張 | 実装 | 訂正先 |
|---|---|---|---|
| 1 | 「supervisor は既存 pipeline を迂回・**再実装しない**」 | `_preview()` が DiffQuarantine と禁止識別子検査を supervisor 側でも再実行する (pre-audit)。authoritative path が後段で再検査するため受理集合は広がらないが「再実装がない」は偽 | D106 決定 (1)、runbook §1 |
| 2 | 「`max-wall-seconds` は supervisor 全体の上限」 | 時刻検査は workload / generation の境界のみ。1 回の role 呼び出し (最大 1200 秒) や build/verify/bench は期限を跨いで走り切る。**hard wall ではない** | D106 決定 (4)、runbook §5 |
| 3 | 「mediated schema を object 配列へ明確化した」 | consumer は要素が `dict` であることしか検査せず、`{}`・未知キー・非文字列 field を含む要素が通る | D106 決定 (4)、runbook §5 |
| 4 | 「diff と designated context **だけ**を auditor へ渡す」 | 実 payload には workload / descriptor / generation / policy を含む common 部も入る | runbook §1 |

加えて、report の `fresh_context` / `observed_tool_events` / `fixed_generations` /
`performance_early_stop` / `scientific_claim` は**実挙動から導出した観測ではなく定数の自己申告**で
あることを runbook §5 と D106 決定 (2) へ明記した (恒真ゲートを「証明」と読ませない)。

## 番号衝突 3 件 (分岐中に main が同じ番号を別内容へ使用)

| 衝突 | branch 側の意味 | main 側の意味 | 解消 |
|---|---|---|---|
| `D99` | 8c bounded trial の設計裁定 | `[T-143] RuleOps v1` | `D106` へ採番 |
| worklog `(61)` | 8c 実装 wave | `Codex dev-wave 資源効率監査` | verbatim 追記せず本 wave の新エントリへ要約収容 |
| `T-179` | live build pilot の再開タスク | `worker 資源台帳` (完了済み) | `T-221` へ採番 (insight 2 箇所) |

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
