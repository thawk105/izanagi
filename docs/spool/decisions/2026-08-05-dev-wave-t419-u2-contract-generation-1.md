---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-05
wave: dev-wave-t419-u2-contract-generation
seq: 1
---

## {{D:contract-generation-bootstrap-fuse}}. 契約世代機構は data 層だけ先に置き、2 世代目を fuse で拒否する

**決定:** 実行環境契約に immutable な世代列 (`GENERATIONS`)、`contract_sha256` の逆引き
(`resolve_by_contract_sha256`)、遷移述語 (`is_valid_successor`)、候補 mapping の純関数
validator (`validate_generations`) を置く。ただし**各 env の世代列の長さがちょうど 1 であること**を
production 初期化時に要求する bootstrap fuse を同時に課し、活性化権限
(activation record / activation receipt) が実装されるまで 2 世代目の登録を fail-closed で拒否する。

`ExecutionEnvironmentContract` と `_canonical_obj()` は変更せず、既存 env の `contract_sha256` を
1 bit も動かさない。`lookup()` と `REGISTRY` の公開挙動も現行のまま残し、production の消費者を
1 箇所も移行しない。

**理由:**
- 較正を再取得すると、旧 artifact が参照する契約 hash が `lookup()` から解決できなくなり、
  過去試行の proof chain が解決不能になる。その状態で再取得へ進むと、旧 evidence の binding を
  新 SHA へ貼り替える (虚偽の履歴を作る) 誘惑が生じる。受け皿を先に置いてこれを塞ぐ。
- 一方で「現行契約か履歴契約か」を**型で**分離する案 (`CurrentContract` / `HistoricalContract`) は、
  型を public な dataclass にする限り、履歴契約を包み直すだけで偽造できる。
  `type(x) is CurrentContract` は生成権限を証明しない。活性化 record と全入口 receipt が
  揃うまでは、型分離は権限 gate にならず、名ばかりの保証になる。
- 世代列の末尾を無条件に current とみなす実装も採らない。それでは source に 2 世代目を
  足しただけで全消費者が切り替わり、「正規の publish 経路を通っていない較正は活性化できない」
  という設計の眼目と矛盾する。fuse はこの窓を閉じたまま data 層だけを先行させる。
- 遷移述語の可変 pointer は calibration 参照の path と sha256 に限る。加えて
  **path が変わらないなら sha256 も変わってはならない**。同一 path のまま bytes を差し替えると、
  旧世代の calibration bytes が失われ、履歴側の検証が hash 不一致で成立しなくなる。

**射程 (この決定が保証しないこと):**
- 世代列が 1 本しかない間、隣接遷移の検査は production では一度も発火しない。
  純関数として test からのみ発火する。
- fuse は **source bootstrap の防壁**であって runtime の活性化権限ではない。
  逆引き index は module 属性として再束縛可能であり、authority として扱ってはならない。
- 履歴 resolver は production の消費者を持たない data 層の準備である。
  旧 proof chain を実際に再計算できるようにするのは versioned predicate dispatch の役目で、
  この決定には含まれない。

**却下した選択肢:**
- `CurrentContract` / `HistoricalContract` の型分離と消費者移行を同時に行う —
  偽造可能な型を権限と称することになり、活性化機構が無い間は純減になりうる。
- 現行 lookup API の削除 — 凍結済みの事前登録 evidence contract が当該 API 名を参照しており、
  参照互換が壊れる。加えて test 側の呼び出しが 84 箇所あり、移行規模が世代機構と無関係に膨らむ。
- 世代機構を別 module へ切り出す — registry と世代列で権威が割れ、env 固有 literal の
  単一定義領域 (AST 検査の免除 region) も増える。
