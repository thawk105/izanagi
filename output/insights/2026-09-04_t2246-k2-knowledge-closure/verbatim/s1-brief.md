# 段 1 brief — [T-2246] / [T-2247] / [T-2248] K2 知識源の端から端までの束縛

対象 branch `worktree-dev-wave-t2246-k2-knowledge-closure` (起点 main `c7ed56589`)。

## scope (この 3 件を 1 単位として実装する)

1. **[T-2248] / D1570 (ユーザー裁定済み)** — `orchestrator/campaign/knowledge_manifest.py` の
   `_parse_value` が `$.sources` に 1 件以上を要求している行を、**取得結果が正当に空である場合に限って
   通す**形へ直す。K2 は宣言した外部取得と投入の範囲を指し、投入件数を条件にしない。
   宣言範囲・取得実績・空であるという事実を記録に残す。
   同じ非空要求が `orchestrator/campaign/wal.py` の `_knowledge_manifest_digest` と
   `orchestrator/campaign/layer3_schema.json` の `declared_sources` / `injected_sources`
   (`minItems: 1`) にもあり、3 箇所を揃えないと端から端まで通らない。
2. **[T-2247]** — `orchestrator/codex_roles/policy.py` の `validate_output_semantics` を
   K2 role の実出力経路へ接続する。実出力経路は
   `orchestrator/campaign/p3_s4_loop.py:1721 load_proposal_file` である
   (親が role 出力を `proposal.json` へ書き、harness がここで読む)。
3. **[T-2246]** — 上の 2 つが作る「参照を許した範囲」と「実際に投入した知識源」の差を、
   campaign (受領証 → campaign lock → 試行台帳) と材料レポートの proof chain へ端から端まで運ぶ。

## 確定済みユーザー裁定

- **D1570** — K2 = 宣言した範囲。件数を条件にしない。緩和は「取得結果が正当に空」に閉じ、記録を残す。
- **D1429** — 「参照を許した範囲」と「実際に投入した知識源」を分けて記録する。この閉包が閉じるまで
  K2 を条件とする certified な最終選択を主張しない。構造遮断 (`tools: []`、fresh context) は撤去しない。
- **D1493** — 知識源の実在検証は producer に置き、読み出し時に再検証しない。
- **D1494** — 受領証の分類は 3 literal の閉集合。呼び手が宣言する入力であり generator の定数にしない。

## 承認済み裁定の前提を覆す新事実 (段 4 で再裁定する)

- **D1559 の前提が D1570 で崩れる。** D1559 は「現行 producer では 2 段は必ず同じ集合になるので、
  一致を確かめる新しい検査は恒真であり足さない」と定めた。D1570 が取得結果ゼロを通す形にすると、
  **宣言範囲が非空で投入 source が空**という状態が初めて成立し、2 段は同じ集合でなくなる。
  D1559 の「独立に抽出した投入集合を作る案は既存の一致検査を迂回しなければ差が出せない」も同時に
  失効する。**ただし D1559 が却下した「emit された payload からの独立抽出」は、この wave でも採らない**
  — 迂回ではなく、producer 側の宣言を分けることで差を出す。
- **`knowledge_use` は実成果物に 1 件も存在しない (DW-O13 の値域実測)。** 唯一の実 K2 走行
  (T-2182、campaign `p3-s4-loop-s4-autonomous-b6dde2ef`) は K2 role 新設前の走行で、role は
  `coder-v4-autonomous`、出力は `proposal` 1 key だけだった。知識の利用は `justification` の散文中にある。
  したがって `knowledge_use` を必須にする述語は**実走行で到達したことがない**。この限界は成果物へ明記し、
  「発火した」と書かない。正例は K2 role が宣言した出力形 (`.claude/agents/coder-v4-autonomous-k2.md`) を
  実体として名指しして作る。
- **現行の閉じた proposal schema は `knowledge_use` を拒否する。**
  `orchestrator/campaign/projection_guard.py:32-33` の `_CODER_REQUIRED` / `_CODER_OPTIONAL` は
  `{axis, implementation}` + `{value, justification, confidence}` で閉じており、K2 role が宣言した
  出力を `proposal.json` へ写すと現状は落ちる。**T-2247 の「未配線」は consumer 不在だけでなく、
  入口の受理形が塞いでいることも含む。**

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1) 宣言範囲の表し方。** manifest へ「宣言した取得・投入の範囲」を表す欄を足し、
  `sources` を「実際に投入した知識源」に純化する。空は宣言範囲が非空で `sources` が空の形で表す。
- **(P2) 既存 campaign identity の連続性。** 受領証 `canonical_manifest` の shape を変えると
  manifest digest が変わり、既存 K2 campaign `b6dde2ef`
  (digest `6d8674228d05e591a67047c4a098e077f427cb7dd6fdfa3b82d20da2000db406`) と識別子が分断される。
  親の provisional 裁定は**既存形の digest を保つ** (新欄を省略した既存 manifest は現行と同じ digest を
  導く) こと。保てない設計なら段 4 へ差し戻す。
- **(P3) 受領証の版。** T-2183 は受領証 v2 新設を「記録される identity が同じ」ことを理由に却下した。
  本 wave は記録内容が実際に増えるので、版を上げるかどうかは段 3 の攻撃対象にする。
- **(P4) 接続点。** `load_proposal_file` に K2 分岐を置くか、呼び手 (親) 側の別 consumer に置くか。
  `p3_s4_loop.py` は contract-loader 閉包の member ではないので変異帰属できる。

## 不変条件 (緩めない)

- **規律 2 を緩めない。** anomaly を検出した variant の即 reject、正しさ・identity・性能ゲートの定義・
  順序・閾値は一切変えない。`knowledge_use` の参照整合性検査は合成の受理集合を広げる方向へ使わない。
- **規律 6。** role 出力は未信頼データ。`knowledge_use` は自己申告であり、「本当にその source を
  使ったか」は検査しない・主張しない。親が受領証へ書く分類を role の申告で上書きしない。
- **D1493 の限界を維持する。** Git 解決を `wal.py` 閉包へ移さない。
- **既存テストの期待値を変えない。** K0 / K1 アームの受理・拒否挙動を 1 bit も変えない。
  `coder-v4-autonomous` / `-sort` / `-trigger-gating` の proposal 受理形を変えない。
- **本題の実装だけ。** 仮想リスク向けの gate・検査・台帳・一般化は足さない (ユーザー明示)。

## 成果物の形

- `knowledge_manifest.py` / `wal.py` / `layer3_schema.json` / `layer3_report.py` /
  `projection_guard.py` / `p3_s4_loop.py` / `codex_roles/policy.py` の実装差分と、
  対応する `orchestrator/tests/` のテスト。
- 段 7 の insight (`output/insights/2026-09-03_t2246-k2-knowledge-closure/`)、変異台帳、
  spool fragment (worklog / decisions)。

## 成果物影響 (DW-G05)

放置すると、K2 アームは取得結果が空のとき入口で拒否され走れず (D1570 と食い違う)、K2 role が宣言した
出力は proposal 入口で落ち、参照整合性検査は永久に発火しない。結果として **D1429 が要求する閉包が
閉じず、K2 を条件とする certified な最終選択を主張できない状態が続く**。

## 分割方針

編集面が `orchestrator/campaign/` と `orchestrator/codex_roles/` + `projection_guard.py` に割れるが、
manifest の欄の形が両者の contract を同時に決めるため **1 単位 (単一 Codex 実装子)** とする
(並行 fix が producer/consumer 契約を割る型を避ける)。段 6 の敵対レビューは 2 本並列。

## 運用上の注意 (実測済み)

- `orchestrator/campaign/wal.py` は `CONTRACT_LOADER_RELATIVE_PATHS` の member。
  **未 commit のままだと焦点走が contract-loader-drift で全赤になり、変異も帰属できない**
  (T-2183 の probe 1 で 109 / 111 node が赤。F357 と同機序)。変異は閉包外の file へ照準する。
- 稼働 wave `worktree-dev-wave-t2189-adaptive-serializability` が
  `orchestrator/tests/test_ccbench_spawn_sites.py` を所有する。同 file 117 行に
  `("campaign/knowledge_manifest.py", "<module>._git"): 1` の登録がある。
  **`knowledge_manifest.py` へ subprocess 起動点を増やさない** (増やすと同 file の編集が必要になり衝突する)。
- 触る file は `FROZEN_MANIFEST` (23 件) の member ではない。
