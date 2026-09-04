# A-2 正式 certification (outer reject) の結果節化 — 一次資料

wave `dev-wave-a2-reject-results-section`、branch `worktree-dev-wave-a2-reject-results-section`、base = local main `df8b9d1e7`。
2026-09-04。親 = Claude (manager)、実装 = Codex `role=author` (D95)。

## 何をしたか

完走済み A-2 4-cell certification (attempt `t2022-20260828c`、outer `reject`) を、新しい測定なしに論文材料へ落とした。

- `docs/paper-story/results/2026-09-04-a2-certification-reject.md` — 結果節の統制稿 (A-2 の性能 / 別走行の correctness / 旧系列との関係)、表 1、
  negative result の枠 (S' の追試失敗と畳まない)、限定 11 件の実配置。
- `docs/paper-story/figures/fig5_a2_certification_reject.{png,pdf,provenance.json}` — 2 列 (write-heavy / balanced) × 2 行 (throughput / abort 率)。
  生成器 `tools/plotting/plot_a2_certification.py`、テスト `orchestrator/tests/test_plot_a2_certification.py`。
- README 3 件 (`docs/paper-story/README.md` の results 系列規則と stale 注記、`figures/README.md` の fig5 節と caption、`tools/plotting/README.md` の A-2 節)。
- 決定 fragment: results 系列の新設。

## 判定の再解釈について (command が起動時の確認を求めた点)

D1198 の関門族 (供給 / 実行側の意味) は [T-1999] で 2026-09-01 に義務化され、A-2 実走 (2026-08-28) より後である。T-2226 (D1611) は 09-04 に着地、
T-2228 (A-2 経路で 2 層目が通るか) は本 wave 時点で稼働中。A-2 成果物に意味関門の記録は無い。
**判定 `reject` は当時の protocol 出力として不変 (規律 7)。再測定はしない。** 結果節・caption・README stale 注記に
「意味関門は本走行に未適用。後日の緑は遡及的に認証しない。逆の結果が出れば新しい日付の results file で改める」を入れた。

## 段ごとの一次資料 (逐語は `verbatim/`)

| 段 | file | 要点 |
|---|---|---|
| 1 | `s1-brief.md` | scope、既裁定、割れうる前提 P1〜P6、実測値表 |
| 2 | `verbatim/s2-plan.md` | file:line 設計、brief への所見 7 件 (全件採用)、変異候補 10 件 |
| 3 | `verbatim/s3-lens-a.md` / `s3-lens-b.md` | 各 10 件、全件 real |
| 4 | `s4-ruling.md` | real/refuted、プラン v2、変異事前登録 M1〜M13、brief の一般化の証拠 |
| 5 | `verbatim/s5-author.md` | 生成器 548 行 / テスト 395 行 (fix 後 561 / 447)、実データ CLI 実走成功 |
| 6 | `verbatim/s6-review-a.md` / `s6-review-b.md` / `s6-fix.md` / `s6-fix2.md`、`s6-ruling.md` | A: must-fix 4 + nit 1、B: must-fix 2 + nit 2 (1 件 refuted)、親 1 件、受入赤 1 件の fix |
| 7 | 本 README、`mutation-ledger.md` | 変異台帳、検査結果 |

## commit

- A `7bd03172e` — 実装 + docs + fig5 (20 file)。
- `951e02ba8 merge main` — 受入 1 の post-claim merge (tool が作成、main `d1c579639`)。
- C `6a9c4d080` — test file の自走 harness (4 行)。
- B — 本 README・台帳・fragment (記録 commit)。

## 検査

- 焦点走 1 (fix 前、計算ノード request 977106.nqsv): 97 passed、rc=0、81 s。
- 焦点走 2 (fix 後、request 977152.nqsv): 99 passed、rc=0、82 s。
- 焦点走 3 (fix2 後、meta-test + 新 test): 26 passed、rc=0、9.6 s。
- 変異: `mutation-ledger.md` — baseline PASSED、16/16 KILLED (kill 15 + diagnostic pin M7)、SURVIVED 0、期待 node 完全一致。
- 受入全走 1 (tip A + post-claim merge、計算ノード): 20420 passed / 68 skipped / 1 failed (`test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`、
  本変更に帰属、fix2 で閉じた)。rc=70 (child-verdict)。
- 受入全走 2 (記録 commit B の後、land 対象 tip): 本 README 作成時点では未実施。結果は job dir の receipt と land の監査列が束縛する。
- `check_docs.py` 緑、`git diff --cached --check` 緑 (逐語 1 件を可逆正規化、下記)。full provenance 監査 (commit A 後): 8142 件、新規違反なし、rc=0。

## 逐語の可逆正規化 (erratum)

`verbatim/s6-review-b.md` は原文が Markdown の行末 2 空白改行を 16 行持ち、`git diff --check` に抵触した。DW-S07 に従い行末空白だけを落とした。
原文 sha256 `ed17063931918d8b1b97bd103c8e1a9fab1d82b47fde5c6524cd905dc7154ee1` (8688 bytes) → 正規化後 `8a6ab124469203d01064d7a602b8b10d6181057bb217d69e3be586420bc25746` (8656 bytes)。
復元は変更 16 行の行末へ半角空白 2 個を戻す。可視文字は不変。

## 本 wave でやらなかったこと (裁定パッケージ候補)

- results 文書の表を provenance と機械照合する test (レンズ A #1)。採るなら生成器が表の Markdown を吐く形が先。
- 生成器の一般 hardening (path containment、TOCTOU 再 hash、3 file commit protocol) (レンズ B #10)。
- T-2228 が A-2 経路の意味関門で赤を出した場合の results 系列の改訂手順 (レンズ B #3)。

## 限界

- 図と表の値は既存 attempt の WAL / raw JSON / certification.json だけから出した。符号差の原因、read-heavy (A-6)、noise floor は未取得のまま。
- durable authority は repo 外にある。図の再生成にはその path が要る (provenance の `external_source_locator`)。
