---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2249-role-example-delta
seq: 3
title: [T-2249] role 入力例の固定 delta 値を段 4 の None 契約へ揃えた — 段 3 が親の裁定 2 件 (削除案・pin 閉包件数) を実測で反証した (コード + docs、branch worktree-dev-wave-t2249-role-example-delta、変異 7/7 KILLED・期待 node 完全一致・初回は probe で 6 件 MISMATCH・単独帰属は 1 件だけ)
---

## 本文

- **段 3 の敵対相談が親の裁定を 2 件反証し、いずれも親が独立に検算して確認した。** 詳細は
  {{D:planner-last-delta-pct-is-live}} と insight。
  - (P1) の「`last_delta_pct` を field ごと削除する」を撤回した。`docs/phase3-s4b-runbook.md` と
    `docs/phase3-s5-sort-runbook.md` が同 field を `null` として live に手作業射影しており、
    D118 残余 (b) の「存在しない `last_delta_pct`」は現在は誤りである。**親の段 1 の検索が `docs/` を
    範囲外にしていたため同じ誤りを継いだ。**
  - 「bytes を pin する箇所は 3 系統 6 hit」も誤りだった。`git grep -c` は物理 1 行の巨大 JSON を
    1 hit としか数えないため、凍結 baseline 内の旧 planner sha 7 件を見落としていた。literal 出現の
    実数は 13 件である。あわせて「この凍結 baseline は保存済み `output/` の値なので動かない」も誤りで、
    同 test は試行を実走して journal を作るため live な role bytes が届く。F169 の再発として記録した。
  - この撤回により段 2 plan と段 3 レンズが計算した planner 側 hash 5 値は無効になった。実装子には
    「他文書の 16 進値を写すな」と明記し、親も独立に検算した。
- **Codex 実装子は `.codex/**` へ書けない (実測)。** 2 つの作業 root で `test -w` rc=1 と
  `patch rejected: writing outside of the project` を再現した。path 依存ではない構造的制約である。
  迂回は禁じ、生成物 adapter 2 件は親が repo 自身の renderer の出力で render して
  `role=integrator; scope=patch-and-render` で記録した。段 5 は実装子 2 本を消費した。
  詳細と残す問いは {{D:codex-cannot-write-dot-codex}}。
- **dispatch 混雑で子は pytest を 1 件も走れなかった** (`run_tests.py` rc=16、`child_started=false`)。
  親が実走した。親側でも 1 回 `queue-wait-timeout` に当たり、D612 の opt-in 上書きで通した。
- **`tools/mutation_worktree.py` の共有木不変検査がこの環境では通らない。** 主 checkout の
  `git status --porcelain=v1 --untracked-files=all` は `.codex/worktrees/` を 171 行含み、
  並行 session が worktree を作り消しするたび bytes が変わる。2 分の走行で破れた。
  `tools/mutation_harness.py` を job dir 内の専用 detached worktree に対して直接使う経路へ切り替えた。
- **変異の事前登録が実測で反証された。** 段 3 のレンズ B の静的読解を採って M4/M5 を 1 node、
  M2 を 2 node で登録したが、初回走行は 7 件中 6 件が MISMATCH で、実測はいずれも期待より**多く**
  赤になった。`test_codex_agents.py` の 4 つの test が checker 全体を呼ぶため、adapter のどの field が
  drift しても同じ 4 本が赤になる。**adapter 側の単一 field 変異に DW-M01 の単一理由は構造的に
  成立しない。** 初回を probe と明記し観測集合で再登録して本走し、7/7 KILLED・完全一致を得た。
  単独帰属できる KILLED は originless 追随 helper の除去 1 件だけで、残る 6 件は冗長 gate 記録である。
- 棄却した案: 段 2 の「2 行を消して trailing comma も除く」(裁定 1 で不要になった)、
  段 3 レンズ B の「例の値を独立に pin する semantic test 2 本を新設する」(依頼が仮想リスク向けの
  gate 追加を scope 外と指定したため real 所見として裁定パッケージへ返した)。
- 段 6 のレビュー 2 本は must-fix 1 件だけを出した。`test_claude_transport.py` が
  `FixtureRoleProvider` 経由で `planner-v4.md` の bytes を読むのに焦点走から漏れていた
  (コード修正は不要、実走の追加のみ)。レンズ B は親の render した adapter bytes を独立に再計算し、
  期待 bytes との byte 一致・変更 4 pointer・key set 不変を確認した。
- 段 8 の自己改善は候補 4 件を routing した。1 件 (`.codex/**` の実装子権限) は契約どおり
  裁定パッケージへ送り、3 件は failures 新規 F + 既存 F169 の再発追記で閉じた。
  `docs/dev-wave/**` は byte 予算に空きがないため入口・reference は編集していない。

## 次の一手差分

### 完了

- [T-2249] 入力例の固定 delta 値を両 role で `null` へ揃え、source sha pin・生成物 adapter 2 件・
  originless 互換 baseline を追随させた。planner は削除ではなく `null`
  (runbook 2 本が live に `null` を射影しているため)。
  remaining: none
  base: 751efe6d201a878072b6b14d62ab72f280b174c5de5361a2213219a554bd5b19

### 新規

- {{T:role-input-example-field-parity}} **P3・新規**: role 入力例の whiteboard field 数を実射影と
  揃える。`coder-v4-autonomous.md` / `-sort` / `-trigger-gating` の例は 3 field だが、
  `whiteboard_for_planner` と `s8c_generation_projection.validate_whiteboard` は 5 field を要求する。
  `planner-v4.md` の「leading-indicators だけ」という記述と `current_perf` の食い違いも同じ族。
  受理集合は変わらず文書読者の誤解だけが対象。
- {{T:role-example-semantic-pin}} **P3・新規・ユーザー裁定待ち**: role 入力例の値を独立に pin する
  semantic 検査を作るか。現在は role 本文・ledger pin・生成物 adapter の全 surface を協調して
  旧 bytes へ戻す変異が既存検査を通る。作れば KILLED にできるが、本 wave は依頼の scope 指定に
  従って追加しなかった。
- {{T:codex-dot-codex-author-contract}} **P2・新規・ユーザー裁定待ち**: `.codex/**` の生成物を
  D95 の Codex author 契約の適用外と明文化するか、D105 の `AI-Agent-Waiver` を要求するか。
  Codex 実装子が構造的に書けないことは本 wave で実測した。現状は integrator の先例に従っている。
- {{T:s8c-runbook-generation-metrics}} **P3・新規**: `docs/phase3-s8c-autonomous-trial-runbook.md` の
  「前世代から更新した current_metrics を次世代へ渡す」という記述が実装と食い違う。実装は
  初期 metrics を workload ごとに凍結して後続世代へ同じ snapshot を返す。別 erratum。
- {{T:mutation-worktree-shared-observation}} **P3・新規**: `tools/mutation_worktree.py` の共有木不変
  検査を、並行 session が `.codex/worktrees/` を作り消しする環境で通る形にするか。現行の
  `--untracked-files=all` 観測は主 checkout で 171 行になり、数分で bytes が変わる。
