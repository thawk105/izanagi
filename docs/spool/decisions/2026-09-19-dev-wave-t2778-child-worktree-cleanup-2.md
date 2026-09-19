---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-19
wave: dev-wave-t2778-child-worktree-cleanup
seq: 2
---

## {{D:child-worktree-manifest-cleanup}}. D703 の例外を manifest 登録済みの子 worktree へ広げ、段 9 で wave 自身が撤去する

**決定 (ユーザー裁定、2026-09-19):** 「ワークツリーが残って next-tasks / cleanup-branches のたびに費用が増え続けている。
恒久対策が要る」に基づき、D703 の自動撤去の対象を「同一 invocation の wave worktree と wave branch」から、
**wave が作成時に job dir の manifest へ exact path で登録した子 worktree (Codex author・fix・変異 container・probe)** まで広げる。
D2148 項 9 (iii) のうち「子 worktree・変異 container の自動撤去は採らない」の部分を supersede する。
同項の「stale lock の自動判定は採らない」と、周期的な自動 sweep を作らないことは維持する。

- 対象: manifest に exact path (絶対・正規) で登録された子木だけ。位置 (`.codex/worktrees/` 等) や名前で子と判定しない。
  manifest は親 (同一 principal) が書く信頼済み入力で署名を持たない。旧 wave の子木は、回収 wave が旧 manifest を明示して渡したときだけ対象になる。
- 条件: 非占有 (判定不能は拒否)、かつ「子の HEAD reflog の全 commit が `refs/heads/main` から到達可能」または
  「manifest の所有 path の内容が main と一致 (所有 path が空のときは前者だけ)」。所有外の差分・未追跡・dirty は job dir の証拠 dir へ
  退避してから撤去する。退避できない状態 (assume-unchanged / skip-worktree、未解決 stage、dirty または pin 外の submodule、
  main にも子 branch にも無い reflog 履歴) は撤去せず理由を報告する。
- 子 branch は削除しない。wave 本体の branch 削除は D703 のまま (`git branch -d` のみ)。
- 発火点は段 9 の正常終了 (`DW-O28`)。前提として当該 wave の子 producer は終端し再投入しない。撤去できない子木は親が unlock して
  理由を報告し、次 wave の worklog へ記録する。
- 手順の正本: 作成時登録と fix 巡の author 木再利用は `docs/dev-wave/workers.md` の `DW-S05-A`、撤去と回収 wave は
  `docs/dev-wave/operations.md` の `DW-O28`。tool は `tools/dev_wave_cleanup.py` の `remove-child`。
- 残余の限界: exact path は作成世代を証明しない (同じ path・branch 名で作り直した木を旧 manifest で扱う余地が残る。
  証拠 dir の受領証と実 branch 一致で狭める)。撤去中の再起動を排他する lease は持たず、前提は producer の終端に置く。
- 対象外: 変異 tool の自己登録、container の外側 directory、占有判定の変更、`/cleanup-branches` の改訂、起動器の改訂、
  過去 wave の manifest の無い残骸 (D204 のまま個別指示)。

**理由:**
- 2026-09-19 19:59 JST の実測で残骸 worktree 194 本 (dirty 117 本、branch 無し container と未統合 fix / probe branch を含む) を
  ユーザー指示で一括撤去した。同型の残骸は wave ごとに流入し、`/next-tasks` は起動時に 212 本の handoff を走査していた。
  D703 の例外は wave 本体だけを対象とし、子は `/cleanup-branches` も触らない (F51、D1991) ため、所有グラフに穴があった。
- 「main から到達可能なものだけ捨ててよい」は D703 の理由節が批准した原理である。所有 path の内容一致は、`DW-S05-A` の patch 中心の
  統合 (子 commit を祖先にしない) で採用された内容へ同じ原理を広げるものであり、新しい原理を導入しない。
- 実測 (2026-09-19、稼働中の author / fix 子木のうち親祖先性を確認できた 3 本) で、子 HEAD は親 wave tip の祖先でなく、
  所有 path の blob は親 tip と一致し、不一致は子が repo 内へ書いた報告 file だけだった。所有契約を固定した author / fix の観測に基づく限定方式であり、
  probe・scratch・変異 container への成立は未確認である。
- 段 2 起草と段 3 敵対相談 (正しさ境界・過剰) の逐語は `output/insights/2026-09-19/t2778-child-worktree-cleanup/`。

**却下した選択肢:**
- 周期的な自動 sweep、stale lock の推定判定 — D2148 項 9 の維持部分。
- 位置・名称・lock 理由文字列による包括削除 — 対象を特定しない削除権限になる (D204)。
- 親が author branch を `-s ours` merge で祖先化し祖先性だけで撤去する — 内容採用を証明せず、不採用履歴を main に残す。
- path 一覧 + 祖先性だけにし、非祖先は退避して撤去する — 「統合済み」を条件とする裁定を緩める。
- 記録した (D2044 項 16) だけで撤去可能と扱う — 記録と統合は別条件 (同項の限定)。
- 統合参照を caller 指定にする — 子 HEAD 自身を渡すと恒真になる (段 3 所見)。
- 登録専用 CLI、履歴 pack、子 branch の `-d` — 固定費削減に不要 (段 3 所見)。
