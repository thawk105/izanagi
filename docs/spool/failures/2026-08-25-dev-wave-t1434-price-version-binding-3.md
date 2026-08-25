---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1434-price-version-binding
seq: 3
---

## 新規

### {{F:numeric-type-confusion-widens-acceptance}}. Python の数値型混同で、受理集合が宣言より広がった 3 箇所 [恒真ゲート] [テスト代表性]

- 事象: 新しい受理形を「`schema_version` が**明示的に 3**」と裁定して実装したが、
  JSON の `3.0` が通った。同型の穴が同じ wave の中で計 3 箇所見つかった。
  - `schema_version: 3.0` — `3.0 == 3` が真。段 6 レビューが発見、親が再現。
  - `block_order: true` / `2.0` — `True in {1, 2}` も `[True, 2.0] == [1, 2]` も真。
    焦点再レビューが発見、親が再現。
  - slot の `stage` — 合成 manifest が数値 stage を持つと `!=` 比較で同じ混同が起きる。
    fix 子が自己列挙で発見。
  いずれも「値は等しいが型が違う」入力で、`==` / `in` による定数比較を素通りする。
- 根本原因: **受理条件を自然言語で「明示的に 3」と書き、コードでは値比較だけを行った。**
  Python では `bool` が `int` の派生であり、`int` と `float` が値で等価比較できるため、
  値の集合だけを見た検査は型の分だけ受理集合が広い。裁定文の「明示的に」は
  実装上の型検査に翻訳されていなかった。
  静的レビュー 1 本目 (整合・実効性レンズ) はこれを見つけられず、正しさ境界レンズと
  焦点再レビューが見つけた。**受理集合を広げる wave では、境界を型の側からも攻める
  レンズが要る**という被覆の教訓でもある。
- 恒久対応: {{D:bind-path-only-hardening}} が修正経路を定める。
  新しい受理形の中でだけ発火する条件へ `type(x) is int` 相当の exact 型検査を置き、
  共通経路は触らない (触ると既存の受理集合が縮む)。
  実装は `tools/codex_reasoning_ab.py` の 3 箇所で、いずれも
  「価格束縛が発行されたときだけ」を表す条件の内側にある。
  負例は `orchestrator/tests/test_codex_reasoning_ab.py` に fails-closed で常駐する
  (`3.0` 束縛、`block_order` の `true` / `2.0`、数値 `stage`)。
  **旧受理集合が縮んでいないことの control も対で常駐させた** — 同じ型混同値を持つ
  全 null schedule が従来どおり受理されることを検査する。
- 再発検知: 受理集合を広げる裁定を書くときは、「明示的に N」のような自然言語の限定を
  **型検査として実装したか**を段 4 の gate 署名で確認する。
  変異事前登録では、対象 gate を恒真化する変異と対に、
  **型混同値を通す正例が拒否されること**を負例として登録する。

### {{F:mutation-worktree-skips-nested-submodule}}. 変異の使い捨て worktree が入れ子 submodule を初期化せず、baseline を 3 回止めた [手順漏れ]

- 事象: `tools/mutation_worktree.py` の使い捨て worktree で baseline が `PARSE_ERROR` になり、
  変異を 1 件も走らせないまま 3 回連続で中止した。実体は 20 件の
  `submodule is not initialized: external/ccbench/third_party/shirakami` である。
  親の worktree では**同じ test file が 505 passed で緑**であり、実装の赤ではない。
- 根本原因: 同 tool は worktree 生成後に外部 benchmark の submodule を **1 段だけ**初期化し、
  入れ子の submodule を初期化しない。`git worktree add` 由来の worktree は submodule が
  未初期化で生まれるため、入れ子を要求する fixture に依存する test は必ず setup で error になる。
  この wave 固有ではなく、submodule 依存 test を変異対象に含む全 wave で再現する。
- 復旧を 2 回失敗した理由も記録する。(a) 後から submodule を初期化して `--resume` しても、
  **resume は記録済みの baseline 判定を再利用する**ため赤のまま (計画上も `baseline=0 run`)。
  (b) runner に初期化を前置する案は、harness が runner の入口を `python -m pytest` か
  固定 HEAD の `tools/run_tests.py` に限定するため構造的に不可能で、
  `bash -c` は `-rf` が独立トークンでなくなる点でも拒否される。
- 恒久対応: `DW-M05` の「既存赤は `--deselect` で外し根拠を台帳へ書く」をこの型にも適用する。
  外す前に、外す test 群が変異対象の gate を通らないことを確認する
  (通るなら検出力が落ちるので外してはならない)。本 wave は 18 件を外し、
  10 変異すべてが残った test だけで KILLED になることを実測した。
  根拠と全件名は `output/insights/2026-08-25_t1434-price-version-binding.md`。
  tool 自体を再帰初期化へ直す作業は {{T:mutation-worktree-recursive-submodule}} が持つ。
- 再発検知: 変異 baseline が `PARSE_ERROR` で、job stdout に
  `submodule is not initialized` が出ている場合。digest には node が残らないので
  一次資料は job stdout の全文である。

## 再発

### F300

- **再発: 2026-08-25** — 本走は 10/10 KILLED で完了したが wrapper が `rc=125`
  (`共有木の事後検査に失敗`) を返した。**ただし原因が F300 本文と異なる。**
  親の worktree は走行前後とも `git status --porcelain` が空で、repo 内での作業はしていない。
  変化したのは**別 session が走行中に local main を進めた**ことによる共有木側である
  (`6d1d43ac` → `06bb563e`)。測定自体は固定 commit の隔離 worktree で完走しており実体は健全。

## supersede 追記

- F300 **supersede: 2026-08-25** — 恒久対応の「repo 内で作業しない」は必要だが十分ではない。同じ `rc=125` は並行 session が local main を進めるだけでも起きる。待ち時間の使い方を正しても防げない型が存在する。
