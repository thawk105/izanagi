# findings 草案 (親の provisional 判定 — 敵対検証の対象)

すべて 2026-08-01、worktree `.claude/worktrees/dev-wave-token-hygiene`
(base = local main、branch `worktree-dev-wave-token-hygiene`) で実測。

## 実測した全 child 起動面 (S1 棚卸し)

### Claude 子

| # | 面 | model | effort | 検証機構 | live? |
|---|---|---|---|---|---|
| C1 | `.claude/agents/*.md` 13 role | opus 10 / sonnet 3 | high 10 / medium 3 | `codex_roles/spec.py` が frontmatter 必須 key を強制 | 合成ループ休止中 |
| C2 | ad-hoc `Agent` tool | 呼出し側が明示 | **指定不能** (param 不在) | `hooks/guard_agent.py` が model 未指定を拒否 (effort は構造上見られない) | live |
| C3 | Workflow `agent()` | opts.model | opts.effort | `tools/check_workflow_models.py` (advisory lint、拒否しない) | live |
| C4 | `s6_proposal_rounds.call_headless` | `opus` 既定 / canary `haiku` | `high` ハードコード | 凍結計測器 | 凍結 |
| C5 | `s8b_prediction_runner` | selector-8b frontmatter (opus) | `--effort high` 固定 | frontmatter を assert (`:1019-1022`) | 凍結 |
| C6 | `tools/dev_waves` supervisor | `--model` 必須 + `allowed_models` 許可リスト | `--effort` 必須だが **許可リストなし** (`_EFFORT_RE`) | 形のみ | 無人継続時 |
| C7 | 親セッション既定 `~/.claude/settings.json` | `opus[1m]` | **`xhigh`** | なし (repo 外) | 常時 |

### codex 子

| # | 面 | model | reasoning | 検証機構 | live? |
|---|---|---|---|---|---|
| X1 | `DW-S02` 段 2 プラン起草 | `gpt-5.6-sol` | **`max`** | 規律のみ | live |
| X2 | `DW-S03` 段 3 敵対相談 | `gpt-5.6-sol` | `max` | 規律のみ | live |
| X3 | `DW-S05-A` 段 5 実装 | `gpt-5.6-sol` | `high` | 規律のみ | live |
| X4 | `DW-S06-A` 段 6 敵対レビュー | `gpt-5.6-sol` | **未明記** | なし | live |
| X5 | `DW-S06-B` 段 6 fix | 段 5 契約を全文継承 → `high` | `high` | 規律のみ | live |
| X6 | `tools/codex_worker_launch.py` | `--model` 既定 `gpt-5.6-sol` | `--reasoning` 必須・**許可リストなし** | `--sandbox` にだけ `choices` あり | live |
| X7 | `codex_roles/launcher.py` (adapter) | manifest 固定 | manifest 固定 | **`:355` に許可リスト** `{low,medium,high,xhigh}` | runtime blocked |
| X8 | `codex_roles/spec.py` (manifest 契約) | `{sol, terra}` | `{medium, high}`、opus role は sol/high 固定 | 実装済み | runtime blocked |
| X9 | `.agents/skills/*` (codex 側 skill 入口) | ピンなし | ピンなし | なし | live |

## 親の provisional 判定

- **A1 (real / ユーザー手番)** — 親既定の effort が承認裁定の未適用分。
  実測: `~/.claude/settings.json` = `model: "opus[1m]"`, `effortLevel: "xhigh"`。
  2026-07-19 裁定 (a) の承認内容は `model: "opus"` **かつ** `effortLevel: "high"`
  (`docs/archive/worklog-phase3-0719.md:83,97`)。model 側は適用済み、**effort 側は未適用**。
  2026-07-06 協議決着「メインループは日常 `high` / 監査・設計の山場のみ `xhigh`」
  (`docs/archive/worklog-phase3-0702-0713.md:601`) とも不整合。
  波及: 親の全ターンに加え、C2 (effort 指定不能) の全 ad-hoc 子が xhigh を継承する。
  AI は repo 外ファイルを編集しないため**ユーザー手番**。
- **A2 (real / 構造的・回避不能)** — Agent tool に `effort` パラメータが存在しない。
  よって ad-hoc claude 子の effort は常にセッション値の継承であり、memory 規律
  「ad-hoc 子は model と effort を毎回明示」は Workflow `agent()` でしか履行できない。
  `guard_agent.py` が model だけを見るのは設計の怠慢ではなく管轄の限界。
  唯一の実効的な緩和は「effort をピンした named role にする」こと。
- **A3 (real / 新規)** — Claude CLI は不正な `--effort` を fail-open する。
  実測 (haiku, 本 worktree): `--effort bogus` →
  `Warning: Unknown --effort value 'bogus' — ignoring it and using the default effort.
  Valid values: low, medium, high, xhigh, max.` + 本文出力 + **rc=0**。
  対して `--model not-a-real-model` は **rc=1** で fail-closed。effort だけ fail-open。
  さらに `--output-format json` の receipt には **effort field が無い**
  (top-level keys に effort 不在、`modelUsage` は model/token/cost のみ) ため、
  served effort の事後 attest 経路がない。これは `docs/failures.md` の
  codex `model_reasoning_effort="ultra"` が rc=0 で通る事象の **Claude 側同型**である。
- **A4 (real / 新規・前回監査後の未監査面)** — `tools/dev_waves` (導入 `4042dcc` 2026-07-21、
  前回監査 `7f77ecb` 2026-07-19 より後) は model と effort の検証が非対称。
  `daemon.py:222` は model を運用者指定の `allowed_models` に照合するが、
  effort は `daemon.py:226` の非空 ASCII と `schema.py:831` の
  `_EFFORT_RE = [a-z][a-z0-9-]{0,31}` という**形だけ**。
  かつ `daemon.py:1685` は要求値 `effort` を記録するのに、子 receipt の
  `CLAUDE_RESULT_ALLOWED_FIELDS` (`receipt.py:22`) に effort field が無く照合できない。
  A3 と合成すると「台帳は要求どおりと記録、実体は既定 (= 現状 xhigh)」が無検出で成立する。
- **A5 (real / 実装せず裁定へ)** — `DW-S02` 段 2 プラン起草の `reasoning=max` は doctrine の
  適用範囲外。doctrine が max を留保するのは「最難の敵対検証・設計攻撃」であり、
  起草 (drafting) はそれに当たらない。[T-181] 実測では max は high 比で
  POS token +29.4% (591,173 → 765,335)、wall 中央値 1.52x、NEG token +29.8%、wall 1.92x、
  名指し正例の検出は両 arm 3/3 (劣化未観測)。**ただし replay 未認証・n=6** のため
  policy 根拠にできない (worklog (75) の射程どおり)。→ 本 wave では実装せず裁定パッケージ。
- **A6 (real / 小・段 8 候補)** — `DW-S06-A` は reasoning を明記しない唯一の子起動段。
  実運用は一貫して `high` (insight 実績複数)。契約の穴であり、明記すれば
  「未指定→起動者の癖」で max へ倒れる余地が消える。
- **A7 (real / 情報)** — 許可リストの実装は既に repo 内にある。dormant な adapter 経路
  (`launcher.py:355` = `{low,medium,high,xhigh}`、`spec.py:610` = `{medium,high}`) は検証するが、
  **live 経路 (`codex_worker_launch.py:2475` の `--reasoning`) は無検証**。
  [T-189] 択 (a) の実装には repo 内に参照実装がある。
- **A8 (refuted / 据置)** — named role 13 件の tier。前回監査の refuted 群
  (凍結実験契約 = `s6_proposal_rounds` / `selector-8b` / `coder-v4` 系、auditor の
  モデル階層方針例外、tool-less 1 shot の低コスト) は今回も成立。verifier は D61 で
  sonnet/medium 済み。**変更を要する role なし**。
- **A9 (refuted)** — codex adapter 13 role は `runtime_activation.status = "blocked"` で
  live token コスト 0。`spec.py` の sol/high 統一は D54 の意図的統一。**変更不要**。
- **A10 (観測 / 過小方向)** — 過小 (難しい仕事に低位) の不整合は発見しなかった。
  `coder` = sonnet に対し `auditor` = opus で「監査側 ≥ 被監査側」の階層方針を満たす。
  `verifier` の medium は判定が非 LLM の決定的処理である事実に整合。

## 反証を求める点

1. A1: 2026-07-19 以降に「xhigh を維持する」という別のユーザー裁定が存在しないか
2. A2: Agent tool に effort 相当の指定手段が本当に無いか (別名 param・agent 定義側の抜け道)
3. A3: 警告時の「default effort」が実際にセッション設定値 (xhigh) なのか CLI 内蔵既定なのか。
   親は warning 文言までしか実測していない — **この帰属は未証明**
4. A4: `allowed_models` は運用者が渡す必須引数であって固定許可リストではない。
   「model は許可リストで守られている」という表現が過大でないか
5. A5: 段 2 起草を「最難の敵対検証でない」と分類するのは妥当か。file:line 粒度の
   プラン起草は設計攻撃と同等の難度ではないか
6. A6: 実運用が一貫して high だったという主張の反例 (max でレビューした wave) がないか
7. 棚卸しの網羅性: 上表 C1〜C7 / X1〜X9 に含めていない child 起動面がないか
