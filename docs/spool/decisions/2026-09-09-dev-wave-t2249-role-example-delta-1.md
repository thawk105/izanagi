---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-09
wave: dev-wave-t2249-role-example-delta
seq: 1
---

## {{D:planner-last-delta-pct-is-live}}. planner 入力例の `last_delta_pct` は削除せず `null` へ揃える — D118 残余の「存在しない field」は現在は誤り

**決定:** `.claude/agents/planner-v4.md` の入力例に残っていた `"last_delta_pct": -1.2` は、
field ごと削除せず **`"last_delta_pct": null`** にする。同時に
`.claude/agents/coder-v4-autonomous.md` の whiteboard 例の `"delta_pct": -1.2` も `null` にする。

**理由:**

- `last_delta_pct` は**存在する field** である。`docs/phase3-s4b-runbook.md` と
  `docs/phase3-s5-sort-runbook.md` が `"current_perf"` の一部として
  `"last_delta_pct": null` をメインセッションに手作業射影させている。段 8a の runbook は段 5 を継承する。
  D118 残余 (b) が「存在しない `last_delta_pct`」と書いた時点より後に runbook 側へ入ったため、
  **その記述は現在は誤り**である。
- したがって field を削除すると role が 2 本の live runbook と乖離する。是正のために runbook 2 本を
  同時に書き換えるのは、`-1.2` を除くという本題より広い変更になる。
- `null` は (a) 本題の固定値を除き、(b) runbook の実射影形と一致し、(c) 例を有効な JSON に保ち
  (`tools/check_codex_agents.py` の `_source_json_example` が `json.loads` する)、
  (d) 既に `null` である兄弟 role と対称になる。

**主張の限定:** これは「runtime leak を閉じた」変更ではない。`-1.2` は固定の説明例であって
ある試行の実測 delta ではなく、`delta_pct≡None` の防壁は whiteboard 射影経路の `delta_pct` field
だけを守る (D118 決定 3)。`current_perf.last_delta_pct` はその関所を通らない。言えるのは、
段 4 の `delta_pct≡None` 不変と食い違う固定例を role の入力契約から除いたことまでである。

**既知の限界:** role 本文・ledger pin・生成物 adapter の**全 surface を協調して旧 bytes へ戻す**変異を
独立に拒否する semantic gate は無い。既存検査は例の値を独立 literal として pin しておらず
(`tools/check_codex_agents.py` の shape 検査は open object の内部を見ず、coder の `whiteboard` schema は
items 定義を持たない)、この協調 rollback は
`SURVIVED / non-equivalent / semantic guard absent` である。wave 開始時に未変更の worktree で
`tools/check_codex_agents.py` が rc=0 だったことがその観測にあたる。例の値は人間 review pin に
依存しており、durable に certify されたとは主張しない。新規検査の追加は本 wave の scope 外とした。

**却下した選択肢:**

- **field ごと削除する** — 親の当初の provisional 裁定。段 3 の敵対相談が runbook 2 本の live 射影を
  実測して反証した。削除は role と runbook の乖離を生む。
- **planner を触らない** — `current_perf.last_delta_pct` は防壁対象外だから対象外という読み。
  防壁対象でないことは正しいが、固定値 `-1.2` を残す理由にはならない。
- **例を実射影と同じ 5 field へ拡張する** — 実際の射影は
  `iteration/direction/magnitude/result/delta_pct` の 5 field だが、例は 3 field である。
  これは兄弟 role にも共通する別の記述 drift であり、本題ではないので裁定パッケージへ返す。
- **例の値を独立に pin する semantic test を新設する** — 依頼が仮想リスク向けの gate 追加を
  scope 外と明示した。real な所見として裁定パッケージへ返す。

## {{D:codex-cannot-write-dot-codex}}. Codex 実装子は `.codex/**` へ書けない — 生成物 adapter は親が render し `role=integrator; scope=patch-and-render` で記録する

**決定:** `.codex/role-adapters/*.json` のように `.codex/` 配下にある生成物は、Codex 実装子に
書かせることを期待しない。Codex 実装子が repo 自身の renderer を読取り oracle として使い、
**親が生成物を render** して `docs/ai-provenance.md` の
`AI-Agent: product=claude; ...; role=integrator; scope=patch-and-render` で記録する。
親は書く前に、旧版との field 単位比較で変わる pointer 集合と key set 不変を検算する。

**理由:**

- 実測した。`codex exec --sandbox workspace-write` の子は、作業 root が
  `.codex/worktrees/<name>` のときも `.claude/worktrees/<name>` のときも、
  `<root>/.codex/role-adapters/*.json` への書込みを
  `patch rejected: writing outside of the project; rejected by user approval settings` で拒否し、
  `test -w` も rc=1 を返した。**2 つの異なる作業 root で再現したので path 依存ではなく、
  codex が `.codex/` を自身の設定領域として書込禁止にしている構造的制約である。**
- 迂回 (別 path へ書いて移す、sandbox 設定を変える) は禁じた。実装子には「書けないなら報告して
  次へ進め」と指示し、実際にそう報告させた。
- adapter の bytes は `orchestrator.codex_roles.spec.expected_adapters()` が完全に決める。
  設計判断は入らないので、親の作業は著作ではなく render である。同じ file 群を更新した
  先行 wave の commit も `role=integrator; scope=patch-and-render` を持つ。
- D95 の実装面 Codex author 契約は満たされる。同じ commit に Codex `role=author` の行があり、
  実装面の残り (ledger pin、テスト) は Codex 実装子が書いている。
- レビューが著作の代替にならないよう、段 6 の敵対レビュー 1 本に
  「親が書いた bytes が renderer の出力そのもので人手の判断が 1 bit も混じっていないこと」を
  独立に再計算させ、byte 一致と 4 pointer・key set 不変を確認させた。

**残す問い (裁定パッケージへ返す):** `.codex/**` の生成物を Codex author 契約の適用外と明文化するか、
D105 の `AI-Agent-Waiver` (ユーザー裁定つき) を要求するかは決めていない。本 wave は先例と
`docs/ai-provenance.md` の `integrator` 規定に従った。

**却下した選択肢:**

- **親が「実装子が書けないので代筆した」として `role=author` で記録する** — 生成物の render と
  著作を混同する。`docs/ai-provenance.md` は親を `manager` / `integrator` / `reviewer` で記録すると
  定めている。
- **`tools/check_codex_agents.py --write` を使う** — 同 tool が native profile 生成と誤認される
  として明示的に禁止している。
- **adapter を実装子が書ける path へ移す** — 生成物の所在は adapter renderer と checker の契約であり、
  本題の外にある大きな設計変更になる。
