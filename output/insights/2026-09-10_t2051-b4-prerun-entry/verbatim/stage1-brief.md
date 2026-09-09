# 段 1 brief — [T-2051] B-4 分析経路の正式起動口

wave `dev-wave-t2051-b4-prerun-entry` / branch `worktree-dev-wave-t2051-b4-prerun-entry` /
起点 main `7f17e1c63` / worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry`

## 研究前進

止めている研究は B-4 (段 4 架構の還流 ablation)。事前登録 §7.1 の全件報告と primary outcome は、
**B-4 標本を 1 block も取得できていない**ため 1 bit も進んでいない。本 wave の完了判定は
「正式経路へ production の実データを 1 回通し、report を出す。出ないなら止まった地点を層ごとに
構造化して返す」。最小差分は、止まっている層が**コードの欠落なのか、事前登録・母集合の欠落なのか**を
実測で確定させ、前者なら発火する実装を 1 単位入れることである。

## 確定済みユーザー裁定 (依頼文より)

- Codex `role=author` = D95。実装面は親が直接編集しない。
- 規律 2 (正しさゲートを緩める変異を許さない) は緩めない。
- 本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
- 「公開呼び手を置くだけで終わらせない」= 発火しない呼び手を成果と数えない。

## 親の実測 (本 job で全件実行)

| # | 事実 | 根拠 |
|---|---|---|
| M1 | report 側の正式起動口は実在し稼働する | `python3 orchestrator/campaign/p3_b4_material_report.py --help` rc=0。不在 root に `publication_rejected: publication_root_invalid` rc=2 |
| M2 | 依頼 4 項目のうち 3 項目は着地済み | producer / durable writer = 2026-08-29、report generator / sanctioned command = 2026-09-01。出所は `output/insights/2026-09-01_t2049-b4-material-report/README.md` |
| M3 | 残るのは certified-selection connection 1 語のみ | 同上 README「残るのは certified-selection connection の 1 語だけである」 |
| M4 | その 1 語は T-2139 が「現 checkout では完成できない」と裁定し、再開条件 3 件を残した | `output/insights/2026-09-01_t2139-b4-certified-selection-connection/README.md` |
| M5 | 再開条件 3 件は今日も 1 件も成立していない | `report.complete` 0 件、生成後の正規呼び手 0 件、耐久化した判定の置き場 0 件 |
| M6 | B-4 の production 成果物は全種 0 件 | `prerun-issuer-receipt.json` / `analysis-manifest.json` / `scheduled-attempt-registry.jsonl` いずれも `output/` 配下に 0 件 |
| M7 | B-4 marker を持つ campaign は 0 件 | `campaign.lock` 30 件を `b4_reflux_ablation` で grep、rc=1 (hit 0) |
| M8 | 正式 launcher は publication を必須入力にする | `p3_b4_launcher.py:673-685` — bootstrap は `--b4-prerun-publication` と `--b4-attempt-id` 必須 |
| M9 | その publication を作る CLI も production 呼び手も無い | `issue_b4_prerun_publication` の呼び手は 0 件 (名前の文字列参照が `p3_b4_producer_auth_experiment.py:491` にあるだけ) |
| M10 | 予定表の型を実成果物から導く production 経路も無い | `B4ScheduledAttemptInput` の出現は ledgers 自身と prereg consumer の検証 probe だけ |
| M11 | 分析は 201 件の eligible 行を要求する | `p3_b4_analysis_ledgers.py:1076,1083,1158` (`EXPECTED_BLOCK_COUNT`、不足は `design_not_feasible`) |
| M12 | eligible の必要条件は `whiteboard_result == REJECTED` + 赤 class | `p3_b4_analysis_ledgers.py:922-936` |
| M13 | **production の赤 precursor は 0 件** | 3 driver の loop campaign 全部で whiteboard 7 件、内訳は success 7 / rejected 0 (base 4、sort 1、trigger 2) |
| M14 | 事前登録 §5 は 6 欄が `未記入`、§6 は 1 つでも未充足なら実走禁止 | `docs/phase3-b4-reflux-ablation-preregistration.md:154-168, 624` |
| M15 | 「母集合」欄は規則参照では埋められず、manifest と registry の実体 path・sha256・行数を要求する | 同 §5.1 の母集合 bullet |
| M16 | closure 5 file は §5 に sha256 pin。現物と一致 | 同 doc:161、`sha256sum` 一致を実測 |
| M17 | `evaluate_analysis` の production caller inventory は exact pin (2 件) | `orchestrator/tests/test_p3_b4_analysis_path.py:357-371` |
| M18 | 稼働 wave との編集面重複なし / 同名 wave なし | 全 worktree の未 commit 差分を `p3_b4|phase3-b4|b4_` で走査し hit 0。`git worktree list` に t2051 無し |

## P1 — 親の provisional 裁定 (段 3 の攻撃対象)

**本 wave に、今日発火する実装面の純増は無い。** 根拠は M2〜M13 の連鎖である。分析経路が止まって
いるのはコードの欠落ではなく、**母集合が 0/201 で、§6 が実走を禁じている**ためである。したがって
publication 発行の CLI を置いても正当に発火せず、それは依頼が禁じた「公開呼び手を置くだけ」に当たる。
成果物は「層ごとに構造化した停止地点 + 裁定パッケージ」になり、実装面 diff は 0 になる見込み。

**子はこれを反証せよ。** 今日の repo で発火する実装面の純増を 1 つでも file:line で名指しできるか。
名指しできるなら P1 は倒れ、段 5 でそれを実装する。名指しできないなら、その不在を独立に裏取りせよ。

## 不変条件

- closure 5 file (`p3_b4_analysis_{contract,adapter,ledgers,path,prereg_consumer}.py`) を 1 byte も変えない。
- `evaluate_analysis` の新規 production caller を作らない (M17 の exact pin)。
- 事前登録 doc の §5 値セルを埋めない。凍結文面を本 wave で書き換えない。
- 規律 2 / 3 を緩めない。verdict・受理集合を広げる変更をしない。
- B-4 の正式実走・qsub・build・性能測定を行わない (dev-wave は campaign 実行ループではない)。

## 成果物の形

1. `output/insights/2026-09-09_t2051-b4-prerun-entry/` — 層 L1〜L5 の構造化停止地点、一次資料、逐語。
2. 台帳 fragment (`docs/spool/`) — worklog、必要なら decisions。
3. P1 が倒れた場合のみ、Codex `role=author` による実装 1 単位。

## 並列分割方針

段 2 = plan 1 本。段 3 = 2 レンズ並列 (A: 正しさ・権威境界と親の一般化、B: 発火可能性・整合と
scope 外層の取り残し)。段 5 以降は段 4 の裁定で決める。
