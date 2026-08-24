---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-24
wave: dev-wave-t1611-terminal-reason-match
seq: 2
---

## {{D:s8c-forward-only-strict-formal-boundary}}. 8c の理由一致検査は前向きの formal 経路 3 本だけで締め、互換 facade は据え置く

**決定:** D741 が要求する分類理由と terminal 理由の一致検査を、次の 3 つの前向き関門に限って必須化する。

1. slot 予約 (`reserve_formal_attempt_slot`)
2. terminal 追記 (`record_formal_attempt_terminal`)
3. 正式 acceptance 発行 (`assert_formal_attempt_registry_acceptance`)

strict 側の profile は互換 profile と遷移 policy の理由一致 bool 1 個だけが異なるものとし、他の field は
同一 object を共有する。既存の互換 facade 6 本は signature、例外順、出力 bytes を変えない。strict 化の
適用先は上の 3 関門と、それを呼ぶ registered mode の予約 sink・terminal sink・acceptance receipt
producer の sink に限る。exploratory 経路は attempt slot を取らないため対象外とする。

strict profile を名乗る identity は実行と acceptance の前向き関門にだけ置き、artifact へ永続化しない。

**理由:**

- terminal 入口だけを strict にしても、既存の理由不一致 prefix が slot 予約に使われ、正式 acceptance も
  互換のまま通る。締めたつもりで受理集合が変わらない。
- 互換 profile 自体を反転させると D735 が定めた「8c は今日の挙動を保つ」を破り、既存の等価性 golden と
  凍結成果物を遡及変更する。D741 の「遡及変更しない」とも矛盾する。
- 差分を bool 1 個に閉じ込めると、strict と互換の違いが「渡す profile だけ」であることをテストで
  exact に固定でき、将来の facade 追加で差が広がるのを検出できる。
- identity を artifact へ永続化すると、凍結世代を跨ぐ新しい互換要求が生まれる。前向き関門に限れば
  既存成果物の再解釈が要らない。

**却下した選択肢:**

- 互換 profile の理由一致 bool を反転する — 既存の等価性 golden と凍結成果物を遡及変更する。
- terminal 入口だけを strict にする — 予約と acceptance が互換のまま残り、reward-hacking 経路が閉じない。
- 分類が空のときの partial terminal を新しい field や status で救済する — 値を見た後の理由付替えを
  別の名前で残すことになる。不一致は fail-closed で拒否する。
- 事前登録条件の評価器を編集して現行の判定を緑へ戻す — 受理集合を変えずに見た目だけを直す変更であり、
  絶対規律 2 に反する。判定の変化は状態として報告するに留める。
