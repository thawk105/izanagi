---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-27
wave: dev-wave-b10-balanced-profile
seq: 2
---

## {{D:balanced-profile-preregistered-band}}. balanced 機序 profile の評価帯と判定式を実走前に凍結する

**決定:** balanced の機序 profile では、評価帯 S を `backoff_us <= 10`、散布を
`(max - min) / mean`、replication bar を `0.044` として**実走前に凍結**し、成果物 JSON の
`preregistered_decision` へ機械可読に埋める。判定は 3 段階に固定する。

- 有用 IPC の散布を total IPC の散布と並べて報告する (数値がいくつでも達成される)。
- `spread(useful_ipc,S) <= spread(total_ipc,S)` かつ `spread(useful_ipc,S) <= 0.044` のときだけ
  「balanced でも total IPC の低下は spin 希釈で説明できる」と書いてよい。
- 条件を満たさない場合は「反証」ではなく inconclusive とする。

**帯の根拠は既存 write-heavy 成果物が同じ帯を使っていることであり、balanced の結果を
1 つも見ずに決めた。** 実測後に `EXPECTED_BACKOFF` の balanced ピーク (5us) が帯の内側だと
判明したが、これは後から得た独立の corroboration であって帯の選択根拠ではない。
記録では必ずこの順序で書く。

**理由:**
- 帯や閾値を結果に合わせて動かせると、同じ rows から「説明済み」と「未説明」の両方を作れる。
  B-10 の受理集合が事後に動くのを塞ぐには、帯・定義・bar を実走前に固定するしかない。
- 4.4% は新規に選んだ値ではなく、既存 write-heavy 成果物の実測値をそのまま prospective な
  replication bar として使う。新しい閾値を導入すると、それ自体が事後選択になる。
- headline 利得の説明は**この走では主張しない**と事前に決めた。理由 3 点 (別環境・別 source /
  診断 build のため D20 で headline 非適格 / 同一 env・同一 source の stock-inline 対照が未取得)
  はいずれも実走前に確定していた。

**却下した選択肢:**
- 実測の tps から sweet-spot を選ぶ — 診断 build の throughput から帯を決めることになり、
  D20 が headline 非適格とした値に受理集合を依存させる。
- 同一 env / 同一 source の独立 stock-inline sweep を判定条件に含める — 計測量が倍以上になり、
  この wave の scope を外れる。取得していないことを限界として明記する側を採る。

## {{D:diagnostic-artifact-machine-readable-limits}}. 診断成果物は限界を機械可読 field で持つ

**決定:** 診断専用 build の成果物は、断り書きを散文だけに置かず、JSON と MD の両方へ
条件分岐なしで機械可読な field として埋める。この wave では
`diagnostic_only` / `headline_eligible` / `comparison_confounds` /
`backoff_time_live_verified` / `dependency_prefix_cache_identity_bound` /
`remaining_limitations` を採用した。

**理由:**
- 散文の断り書きは、成果物を読む下流 (レポート・選択器・別 wave) が落としうる。
  値で持てば、落とすには明示的に無視する必要がある。
- 限界の一部は「この wave では取らないと決めた」もの (実効 TSC の live 検証、
  dependency prefix の cache identity 束縛) であり、未取得であることを成果物自身が
  主張できる形にしておかないと、後から「検証済み」と誤読される。

**却下した選択肢:**
- insight にだけ書く — 成果物と insight が別 file である以上、参照が落ちれば限界も落ちる。
- 検査を足して下流に強制する — 下流の受理集合を変える話であり、この wave の scope 外。
