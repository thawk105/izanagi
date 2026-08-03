# 変異本走 transport の生死確認 — dev-wave 逐語 (2026-08-03)

- `authority: none`
- `default_effect: no-state-change`

変異本走を「1 変異 = 1 qsub」から「harness ごと計算ノードの 1 ジョブへ束ねる」形へ移せるかの
生死確認 (`DW-G01`)。**恒久実装は行っていない。** 可変状態の正本は `docs/worklog.md` の該当エントリと
`docs/decisions.md` の該当 D であり、本ディレクトリは一次資料を凍結するだけである。

anchor = `ea6ca433eb83d666ec64f3629cc35c769a2b5c19`

| ファイル | 段 | 内容 |
|---|---|---|
| `s1-brief.md` | 1 | 親 brief。前提実測と provisional 裁定 (P1)〜(P4)。**うち 3 件は後に誤りと判明** |
| `s2-plan.md` | 2 | codex プラン起草 (read-only)。恒久実装を NO-GO と判定 |
| `s3-lens-a-correctness-barrier.md` | 3 | 敵対レンズ A — 正しさ防壁 (blocker 5 件) |
| `s3-lens-b-evidence-scope.md` | 3 | 敵対レンズ B — 証拠・受理集合・変異事前登録 (NO-GO) |
| `s4-ruling.md` | 4 | 親の裁定 — 生死確認までを実施し恒久実装はしない |
| `s5-author-report.md` | 5 | 実装子の完了報告 (使い捨て driver 一式) |
| `s6-review.md` | 6 | 焦点敵対レビュー (blocker 3 件、must-fix 6 件) |
| `s6-fix1-report.md` | 6 | fix 1 — 束ね投入器の PATH 正規化漏れ |
| `s6-fix2-report.md` | 6 | fix 2 — 比較器の厳格化 (4 field → 全 field 再帰比較) |
| `s6-fix3-report.md` | 6 | fix 3 — 比較器の誤検出 2 件の是正 |
| `RESULT.md` | — | 親による結果の確定 (実測値の正本) |
| `driver/` | — | 使い捨て driver 一式の逐語 (spec / 両 leg の起動 script / 比較器 / 手順) |
| `leg1-ledger-dispatch.json` | — | 現行経路 (1 変異 = 1 qsub) の変異台帳 |
| `leg2-ledger-bundle.json` | — | 束ね経路 (1 ジョブ内 local) の変異台帳 |
| `leg2-attempt1-ledger-erratum.json` | — | 束ね経路 1 回目の台帳。baseline 赤で停止 (erratum、`DW-M02`) |
| `compare-*.txt` | — | 比較器の出力 (初版 / 厳格版 / 最終版) |
| `evidence/` | — | leg 1 の scheduler provenance と両 attempt の job log |

## この wave が閉じたこと

- **transport を変えても 3 変異の verdict は変わらない** (`status` / `failed_nodes` /
  `matches_expectation` / collection の収集 node 列が完全一致)。
- **削減量を実測した** — 内側 pytest の仕事量はほぼ同じで、消えるのは順番待ちだけ。
- **束ね投入器は sanctioned job script の環境正規化を逐語で写す必要がある** — 写さないと
  内側の suite が別物になることを実測した (1 回目の baseline 赤)。

## この wave が閉じていないこと

- cross-node flock (`_lock_path_for` は node-local `/tmp`)
- walltime kill 後の復元 (NQSV の signal と grace が未確認)
- `--resume` による dirty tree の回収 (構造的に不可)
- `dispatch_compute.py` の `total_deadline` が queue 待ちを running walltime から差し引く欠陥
- 恒久 dispatcher 経路そのもの (`mutation` task、argv/env validator、transport 証拠、hook 層)
- 41 変異規模での連続実行

## 証拠の保存方針

- 変異台帳は全文を凍結した (先例: `2026-08-02_t316-build-admission/`)。
- leg 1 の scheduler provenance (`receipt.json` / `request.json` / `result.json` / `dispatch.sh` /
  `interpreter_probe.py` / `.e`) は `evidence/leg1-dispatch-submissions/<nonce>/` へ固定した。
  **job stdout (`.o`) は台帳の `artifact.stdout` に同内容が `stdout_sha256` で束縛されているため
  重複させていない。**
- 使い捨て worktree はこの固定の**後**に削除した。
