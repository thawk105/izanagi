---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-24
wave: dev-wave-codex-skill-parity
seq: 1
---

## {{D:codex-skill-agents-yaml-is-docs}}. `.agents/**/agents/*.yaml` を docs 面とし、Codex author 必須の対象から外す

**決定 (2026-08-24 ユーザー裁定):** repo-scoped Codex Skill の interface metadata
(`.agents/**/agents/*.yaml`) は docs 面とする。D95 決定 (1) の「実装面は Codex `role=author`
実装子が書き、親は直接編集しない」の対象に含めず、親が直接編集してよい。
`.agents/**/SKILL.md` も従来どおり docs 面である。`tools/check_ai_provenance.py` の
`_is_implementation_path()` は既にこの分類と一致しており、変更しない。

**理由:**

- **sandbox 化された Codex 子は `.agents/` へ物理的に書けない。** 本 wave で 2 経路とも拒否された。
  Bash 経由の `apply_patch <<'PATCH'` は `guard_bash` が「防護ツリーのパスと不透明構文の同居」で拒否し、
  native `apply_patch` tool は `patch rejected: writing outside of the project; rejected by user
  approval settings` で拒否した。同じ sandbox・同じ worktree で `tools/` と
  `orchestrator/` へは書けているため、`.agents/` 固有の制約である。
  Codex が自分の skill 定義を書き換えられないのは、製品側の自己改変防止として整合的である。
- したがって当該 path を Codex author 必須にすると、**dev-wave では永久に保守できない面**が生まれる。
  D95 が塞ぎたかったのは「親が実装を代筆して Codex 帰属を空洞化させること」であり、
  子が構造的に到達できない path を親が保守することはその型ではない。
- 分類の実体は既に `_is_implementation_path()` が持っている
  (`.agents/` は所在の列挙になく `.yaml` は拡張子の列挙にない)。本決定はその分類を明文化し、
  D95 本文の「機械設定も実装面である」という一般記述との食い違いを、この path に限って解消する。
- 内容の設計判断そのものは Codex 実装子が担っている。同子が `tools/check_docs.py` の期待値定数を
  書き、親はその定数へ byte 単位で一致させるだけである。著者性の実体は失われない。

**射程の限定:**

- 本決定は `.agents/**/agents/*.yaml` と `.agents/**/SKILL.md` に閉じる。
  `.codex/` 配下、`tools/`、`orchestrator/`、`hooks/` の機械設定は従来どおり実装面である。
- 「子が書けないから親が書く」を一般の免除理由にしない。他の path で同種の主張をするときは、
  拒否の逐語と再現手順を添えて改めてユーザー裁定を取る。

**却下した選択肢:**

- **親が代筆せず停止する (D95 の既定)** — 該当 path を dev-wave から永久に保守不能にする。
  暗黙起動の防壁のような、実際に運用事故へ直結する修正が入らなくなる。
- **`AI-Agent` trailer だけを書き換えて Codex author を主張する** — 実作業帰属を偽る。
- **`_is_implementation_path()` を広げて `.agents/` を実装面にする** — 子が書けない以上、
  検査を通せる主体がいなくなる。

## {{D:codex-cleanup-skill-safety-delta}}. Codex cleanup-branches の安全縮退を「一致の裁定済み例外」として全数記録する

**決定:** Codex 側 `cleanup-branches` skill が Claude command に対して持つ意図的な差分は、
共通 dispatcher の不一致ではなく **Codex 固有の安全縮退**である。両者の一致は
「共通 dispatcher の手順が一致し、そのうえで下表の縮退だけが Codex 側に上乗せされる」と定義する。
以後この skill について「完全一致」とは書かず、下表を参照する。

| 面 | Claude command | Codex overlay | 向き |
|---|---|---|---|
| `git worktree prune` | 実行する | preview のみ、実 prune は人間へ引き渡す | 縮退 |
| local `main` / primary worktree | 一般の eligibility 判定に従う | 無条件に保持する | 縮退 |
| foreign / locked worktree | eligibility 判定に従う | inventory と report のみ、unlock・削除・prune をしない | 縮退 |
| eligibility の再評価 | 削除直前の占有検査 | 各破壊操作の直前に全条件を再評価する | 縮退 |
| 権限不足時 | — | 権限を拡大せず、実行できた操作と残作業を人間へ返す | 縮退 |
| overlay 衝突時の優先順位 | — | 削除範囲が狭くなる安全側へ縮退する | 縮退 |
| `ExitWorktree` | 使える前提 | 使える前提を置かず、cwd を対象外へ固定できなければ停止 | 翻訳 |

**理由:**

- これらは 2026-07-30 の Codex adapter 移植時に意図して入れた縮退であり、退行ではない。
  しかし「依頼上の一致に対する裁定済みの例外である」という権威と全数一覧が repo に無かったため、
  一致検査のたびに未解決の不一致として再発見される。
- 縮退はすべて**削除範囲を狭める向き**にそろっており、正しさ防壁を緩める向きの差は無い。
- 差を残すか解消するかは設計択一であり、本決定は現況の明文化に留める。解消の可否は別途裁定する。

**却下した選択肢:**

- **縮退を外して Claude と同じ結果へ揃える** — 破壊操作の安全弁を自動的に外すことになる。
  実施するならユーザー裁定を要する。
- **記録せず現況のまま置く** — 次の一致検査が同じ不一致を再発見し、
  「一致した」と報告できない状態が恒久化する。
