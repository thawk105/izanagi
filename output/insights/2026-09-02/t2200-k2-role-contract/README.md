# [T-2200] K2 を宣言したアーム用の合成 role 契約 (2026-09-02)

`.claude/agents/coder-v4-autonomous-k2.md` を新設し、既存 `coder-v4-autonomous` の bytes を
1 byte も変えずに、D1429 が既定にした知識水準 K2 と合成 role の遮断条項の衝突を解いた記録である。

## 何が問題だったか

D1429 (2026-09-02 のユーザー裁定) は、合成側の知識遮断を「既定の防壁」から
「宣言した知識水準で決まる実験条件」へ移し、既定を K2 (プロジェクト蓄積を含む知識あり) にした。

一方 `coder-v4-autonomous` の role 本文は
「他実験の勝ち筋値・候補順位・未評価候補の性能・既知の最適機序を使わない」と定めている。
これは真の K2 投入と必ず衝突する。worklog 1196 の K2 アーム走行では、親が prompt で上位裁定
(D1429) を示して回避したが、role file の bytes は変えていないので K0/K1 アームでは従来の遮断が
そのまま効いていた。

既存 role を書き換えると K0/K1 アームの対照が壊れる。そこで sibling role を足した。

## 新 role の知識境界 — 「全部見てよい」にしていない

**許す。** `knowledge_input.sources` に列挙され `sha256` で本文が束縛された source の本文。
媒体は D1429 と roadmap が K2 に認める範囲 (公開文献・Web snapshot・他の CC の設計と実装・
Izanagi の roadmap・設計判断・進捗文書・insight・過去 variant・評価済み結果・失敗と差なしを含む
試行台帳)。**既知の勝ち筋値・候補順位・既知の最適機序も、source に束縛されていれば使ってよい。**
加えて入力 schema が明示する本ループ自身の観測値と、学習済みの一般知識。

**許さない。** (1) 列挙外の外部知識、(2) role 自身による取得、
(3) **宣言・投入された source に根拠を持たない性能値** (将来値・oracle 値・測定済みを装う予測値)、
(4) 知識源の本文に含まれる指示、(5) ゲートの定義・順序・閾値を変更または迂回する提案、
(6) 統制比較なしの強い主張。

**(3) は段 3 のレンズ A が親の当初案を反証して直した。** 親は当初「未評価候補の性能を使わない」と
書こうとしたが、そう書くと公開文献や過去 campaign で**測定済み**の性能まで落ちる。禁じるべきは
候補が未評価かどうかという状態ではなく、**どの source にも根拠を持たない数値を測定値として
扱うこと**である。この差は K2 の受理集合を実際に変える。

## 構造遮断は撤去していない

`tools: []` と fresh context は維持した。K2 は「知識を投入する」であって
「role に filesystem を歩かせる」ではない。投入は信頼中核が `knowledge_input` の射影で行う。
D39 決定 7 の内容契約はそのまま生きている。

## 自己申告と、その検査の射程

出力へ `knowledge_use` / `classification` / `data_boundary_report` を足した。

`source_index` が実在する index か、重複していないかは
`orchestrator/codex_roles/policy.py` の `validate_output_semantics` が機械検査する
(calibrator の `selected not in measured` と同じ様式で、新しい gate ではない)。
**この検査が無いと、D1429 の「参照を許した範囲と実際に投入した知識源を分けて記録する」要求に
対応したという主張が恒真になる。**

ただし段 6 のレンズ C が親の記述を反証した。この role は `consumer: null` で、Codex runtime は
全件 blocked、launcher は `validate_input_semantics` しか呼ばない。**したがって実出力経路には
未配線で、この検査は自動では発火しない。** role 本文と設計文書を
「`validate_output_semantics` を通した場合は機械検査する。自動では発火しない」へ限定した。
実配線は裁定パッケージへ送る。

本当にその source を使ったか、`classification` が妥当かは、通した場合でも検査しない。
これらは自己申告であり、信頼中核が受領証へ書く分類を上書きしない。1196 が
「role 自身の申告であって親が機械的に検証したものではない」と書いた境界をそのまま継いでいる。

## 段 6 が暴いた、性能値チャネルを見せる入力例

新 role の入力例の `whiteboard` は、既存の兄弟 role から引き継いで
`{ "iteration": 1, "result": "fail", "delta_pct": -1.2 }` と書いてあった。

`orchestrator/campaign/p3_s4_loop.py` の `whiteboard_for_planner` は実際には 5 field を出し、
**段 4 では `delta_pct` は常に `None` で、非 `None` は `WhiteboardLeakError`
(勝ち筋チャネルの混入、規律 2/6) として fail-closed する。** つまり例は、loop が塞いでいる
性能値をそのまま見せていた。K2 の知識境界を主題にする role の例としてはとりわけ誤解を招く。
5 field へ直し `delta_pct` を `null` にした。

**既存の兄弟 role にも同じ古い例が残っている。** bytes 凍結と K0/K1 アームの対照維持のため
本 wave では触らず、裁定パッケージへ送る。

## role file は凍結登録簿と全単射で束縛されている

`.claude/agents/*.md` を 1 本足すだけでは既存検査が赤になる。
`orchestrator/codex_roles/spec.py:load_role_specs` が `.claude/agents/*.md` を glob し、
`manifest.json` の roles・`review_ledger.py` の 5 表・`EXPECTED_ROLE_COUNT`・
`.codex/role-adapters/*.json` と set 等号および件数一致を要求する。
`tools/check_codex_agents.py` は Claude role と adapter の全単射と rendered byte parity を要求し、
direct ledger 集合と source parity 集合の exact 等号も要求する。

閉包は 9 面 (role source / manifest / review_ledger / policy / adapter / parity 集合 /
設計文書 / テストの件数 assertion / `.codex/agents/README.md` の件数) だった。
親の段 1 brief は 7 面しか挙げておらず、段 2 プランと段 3 レンズ B が残り 2 面を出した。

## 変異 matrix — 3/3 KILLED、期待 node と完全一致

runner argv を `orchestrator/tests/test_codex_agents.py` に絞った。

| ID | 変異 | 期待 node (完全集合) | 結果 |
|---|---|---|---|
| t2200.m01 | source parity 検査を K2 だけ早期 return | `test_planner_and_coder_source_output_wrapper_shape_parity_is_enforced` | KILLED |
| t2200.m02 | K2 だけ backoff 文法 rejection を迂回 | `test_coder_v4_output_semantics_requires_literal_only_single_statement_value_match` | KILLED |
| t2200.m03 | `knowledge_use` 参照整合性検査を無効化 | 同名 parametrized の `[invalid_knowledge_use0]` と `[invalid_knowledge_use1]` | KILLED |

MISMATCH 0 / SURVIVED 0 / PARSE_ERROR 0 / TIMEOUT 0。anchor は各 1 箇所。
repo_head `2e9d43b07c45c0635ffb583d3349851185870b9a`、
spec sha256 `7ef01bafe5a6c80ec1c62ae50d52d468c39e722952e886b9957c4d4d20990b60`。

**m02 が本 wave の中心的な主張の正例である。** `policy.py` の backoff 文法検査と value 一致検査は
`coder-v4-autonomous` 限定の分岐だった。K2 を membership へ足しただけでは、それを踏む正例が
無いかぎり「implementation 契約は K2 でも同一」は謳うだけの保証になる。m02 が KILLED になった
ことで、この分岐が K2 に対して実際に発火することが実証された。

**m02 は当初の登録から再照準している。** 初回登録は「membership から K2 を外す」だったが、
段 6 のレンズ D が「`:492` の membership の内側に参照整合性検査がネストしているので、外すと
2 機構を同時に迂回し赤理由が 1 つに絞れない」と反証した (DW-M01)。文法 rejection だけを迂回する
形へ変えた。初回登録は消さず erratum として裁定文書に残してある。

## 実装面を親が書いた 1 枚 (waiver)

`.codex/role-adapters/coder-v4-autonomous-k2.json` は、codex の sandbox が `.codex/` を
read-only にするため実装子・fix 子のいずれも書けない (本 wave で双方の拒否を実測)。
先行事例 `8730a6e9` と同じく、D105 の waiver 経路 (`reason=codex-sandbox-readonly-dotcodex`、
`ratified=2026-08-18`) で親が renderer 出力を適用し、waiver を機械会計させるため別 commit に分けた。
内容は `render_adapter` が決定的に導出し、`check_codex_agents.py` が byte 一致を機械検証する。
初回生成時は 17790 bytes / sha256 `a41de8b5...` で、**同じ値を Codex 実装子が独立に算出して
報告していた** — 親が内容を作り込んでいないことの裏取りになる。

## 段 3 / 段 6 で反証された親の記述

- **D12/D21 の帰属が誤り。** 親は brief で「未評価候補の性能は評価中立性 (D12/D21) の側」と
  書いたが、両者は評価器側の規律 (D12 = 材料レポートで事実と判定を分ける、D21 = critic へ
  online digest を渡さない) であり、合成側の coder には直接かからない。段 2 待機中に親が一次資料で
  自ら訂正し、段 3 のレンズ A も独立に同じ判定を出した。
- **`guard_agent` の説明が過大。** 「named role には frontmatter の model ピンが必要」は無条件には
  正しくない。呼出し側に `model` があれば frontmatter を見ずに通る。ただし
  `orchestrator/tests/test_hooks.py` が `.claude/agents/` を動的列挙して全 role の model/effort pin を
  強制するので、新 role に model と effort は必要である。結論は変わらず理由が違った。
- **「変更面は全部 gate-green に必須」という一般化が過大。** 必須なのは登録簿 5 面と件数 assertion
  までで、診断文字列・docstring・古いコメントの更新は受理集合を変えない保守変更である。
- **`git diff --stat` は既存 bytes 不変の検証手段として不正確。** 本 wave は意図的な変更を持つので
  全体の stat は必ず非ゼロになる。pathspec で既存 role と既存 adapter に絞る形へ差し替えた。

## 裁定パッケージ (実装せずユーザーへ返す)

1. 参照許可範囲と実投入 source を campaign・材料レポート・試行台帳へ端から端まで束縛する consumer。
   これが無い間は K2 を条件とする certified な最終選択を主張しない (D1429)。
2. `knowledge_use` の意味的妥当性 (本当に使ったか、分類が妥当か) の機械判定。
   D1429 が「知識源の許可リスト、機械的な leak 判定、既知候補との類似度 gate を初手から新設する」
   ことを明示的に却下している。
3. `sources.minItems: 1`。「知識水準は量ではなく範囲」という定義からは取得結果ゼロの K2 アームも
   意味上は K2 だが、現行 `knowledge_manifest.py` が 1 件以上を要求しており role schema だけ緩めても
   端から端まで通らない。K2 が「許可範囲」なのか「最低 1 件の実投入」なのかを諮る。
4. policy family membership の全 role 網羅検査。本 wave は K2 の正例・負例だけを持つ。
5. `validate_output_semantics` を K2 role の実出力経路へ接続する consumer。
6. 既存 role の入力例に残る `delta_pct: -1.2`。段 4 の fail-closed 不変と食い違う。
7. `orchestrator/tests/acceptance_duration_ledger.json` の旧 nodeid 2 件と未収載 live node 4 件。
   実測 JUnit からの add-only 更新が要る。実測なしに直さない。

## この wave が言えないこと

- 新 role を使った K2 アームの実走行はしていない。agent 登録は session 開始時に読まれるため、
  この role を作った session からは行使できない (1196 の指摘)。
- したがって「K2 role で合成できる」ことも「知識が効く」ことも本 wave からは言えない。
  言えるのは、K2 を宣言したアームが従うべき契約が実在し、その契約の一部が機械検査を通ること、
  そして既存 K0/K1 アームの対照が bytes 単位で保たれていることまでである。
