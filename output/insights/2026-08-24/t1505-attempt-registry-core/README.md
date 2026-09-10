# [T-1505] attempt 状態機械のドメイン非依存 core 抽出 — 一次資料

wave `dev-wave-t1484-floor-restart-registry` (2026-08-23〜2026-08-24)。
branch `worktree-dev-wave-t1484-floor-restart-registry`。
状態の正本は `docs/worklog.md` 末尾と `docs/phase3-8b-restart-runbook.md` の R-5 節であり、
本書は逐語と実測値の保管場所である。

## この wave が実装したもの

D672 (床値の救出台帳は共通 core を抽出して 8b から使う) に従い、次まで実装した。

- `orchestrator/campaign/attempt_registry_core.py` — ドメイン非依存の attempt 状態機械。
- `orchestrator/campaign/trial_registry.py` — 8c の実 `def` による委譲 facade。
- `orchestrator/campaign/s8b_attempt_profile.py` — 8b の domain profile (production 未配線)。
- 差分テスト・8b profile の状態機械テスト・facade 再束縛検出テスト。

**救出経路そのものは完成していない。** 8b の production 配線・trusted launcher・
再抽選規則は、ユーザー裁定を要することが確定したため実装していない。
返した 5 点は `verbatim/ruling-package.md`。

## 実測値

| 項目 | 値 |
|---|---|
| 抽出元の範囲 | `trial_registry.py:1818-3431` (抽出前 HEAD `5a4cbfa8` 時点で 1,614 行) |
| 8c 固有 acceptance (移していない) | 同 `:3432-3557` |
| `trial_registry.py` の差分 | 909 行削除 / 405 行追加 (facade 化) |
| 新規 core | 1,473 行 |
| 新規 8b profile | 437 行 |
| 新規テスト | 2 file |
| codex 子 | 9 本 (plan 1 / consult 2 / author 3 / review 2 / fix 2)、すべて rc=0 |
| 段 3 敵対所見 | 16 件すべて real、refuted 0 |
| 段 6 敵対所見 | must-fix 6 / should-fix 4 / nit 2 |
| 段 6 焦点再レビュー | regressed 0、closed 8 / partial 5、新規 must-fix 1 |

## 変異 matrix (2026-08-24)

`mutation-ledger.json` が台帳、`mutation-spec.json` が spec。
`repo_head=74dd2203e520626ebe016ba5c8d86d0405f24c94`、
`spec_sha256=12cfbc055a171481c00cc5135174b9f63dd1ea95e595d328ea42c64aa9885cd6`。

baseline PASSED。**登録 6 件すべて KILLED、期待 node と完全一致 (matching=6)。**

| M | 変異位置 | 意味 |
|---|---|---|
| M1 | core の「観測後の再走禁止」guard を無効化 | 受理集合が広がる |
| M2 | 8b profile の理由一致 policy を `False` へ | 値を見た後の理由付け替えが通る |
| M3 | facade `reserve_attempt_slot` を実 `def` から再 export へ | 構造 pin |
| M4 | facade `create_attempt_registry_genesis` を top-level 再束縛 | 構造 pin (C03 では検出できない型) |
| M5 | budget key を反復込みへ戻す | 凍結 protocol の retry 予算が `n_sessions` 倍になる |
| M6 | core の未知 event 拒否を無効化 | 拒否理由が変わる |

M3 / M4 は挙動を変えない構造 pin であり、`DW-M08` に従い「受理集合を変えず構造化シグナルを
pin する変異」として扱う。M1 / M2 / M5 / M6 は受理集合または拒否理由が期待方向へ変わる kill である。

## 親が実走した検査

子は環境の都合で pytest を実走できなかった (runner が計算ノードを要求し preflight `rc=16`)。
**テストの実走はすべて親が `tools/run_tests.py` で行った。**

| 時点 | 対象 | 結果 |
|---|---|---|
| 段 5 後 | equivalence + 8b profile + `test_trial_registry.py` | 210 passed |
| 段 5 後 | 8c 述語 + invariant + p3_autonomous + reflux + spawn_sites | 500 passed |
| fix 第 1 巡後 | core 群 | 221 passed |
| fix 第 1 巡後 | consumer 群 + holdout_observation | 551 passed |
| fix 第 2 巡後 | core 群 | 225 passed |
| fix 第 2 巡後 | consumer 群 | 551 passed |

各 commit 後に `tools/check_ai_provenance.py` の全史監査を rc=0 で通した。

## 逐語

- `verbatim/stage2-plan.md` — 段 2 の read-only codex plan。
- `verbatim/stage3-lens-sol.md` / `verbatim/stage3-lens-luna.md` — 段 3 敵対 2 レンズ。
- `verbatim/stage4-adjudication.md` — 段 4 の親裁定 (所見 18 件の real/refuted と採否、変異事前登録)。
- `verbatim/stage6-review-sol.md` / `verbatim/stage6-review-luna.md` — 段 6 敵対レビュー。
- `verbatim/stage6-refocus.md` — 段 6 fix 後の焦点再レビュー (所見ごとの対応表)。
- `verbatim/ruling-package.md` — ユーザーへ返した 5 点。

## この wave で覆った前提

- **親の provisional 裁定 5 件のうち 4 件が段 2 / 段 3 の子に反証された。**
- **親が段 4 で立てた論証 A18 が段 6 のレビューに反証された。** 「未知 event は拒否されるので
  profile の event 表へ足すだけで 8c の受理集合を変えずに拡張できる」としたが、core の replay が
  既知 4 種以外をすべて terminal として扱う `else` 分岐だったため、表に名前を足した瞬間に
  terminal の semantic が付いていた。fail-closed へ直し、裁定パッケージへ訂正を明記した。
- **抽出で 8c の受理集合が広がっていた箇所が 2 件あり、どちらも段 6 のレビューが見つけた。**
  焦点走が全緑でも受理集合の等価性は保証されない。
