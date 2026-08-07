---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-07
wave: dev-wave-t624-activation-noop
seq: 1
---

## {{D:activation-transition-rejects-no-op}}. activation record の世代遷移は全 env 据置の no-op を拒否する

**決定:** 契約世代の activation record 間の遷移規則を、次の条件へ明文化する。

- **全 env の generation delta が `0` または `1` であり、かつ少なくとも 1 つの env の delta が `1`。**

D176 の世代機構に対する先行裁定は「各 env は据置または +1」とだけ書かれていたため、
全 env 据置の record も条件を満たしていた。この決定は後半の存在条件を足し、contract が
1 つも変わらないまま activation 状態だけが進む no-op record を受理集合から外す。
skip (delta ≥ 2) と downgrade (delta < 0) は前半の条件が引き続き拒否する。

規則は**遷移の必要条件**であり、単独で活性化を正当化しない。実装形 (述語の署名、入力粒度、
`is_valid_successor` との合成、env 集合変化の扱い) は本決定では固定せず、
実 activation record schema と併せて別途裁定する。

**理由:**
- no-op record を受理すると、`activation_serial` と `activation_state_sha256` が進む一方で
  全 env の contract が同一のままになる。レポートと試行台帳の activation 参照は、
  同じ契約集合に対して意味なく分岐した値を指すことになり、参照から契約集合を一意に読み戻せない。
- 元の裁定の意図は skip / downgrade / no-op の 3 つを拒否することだったが、確定文言は前 2 者しか
  拒否していなかった。文言と意図の差を残したまま述語を実装すると、「no-op を拒否する保証がある」と
  読める弱い gate が台帳に残る。
- 少なくとも 1 env が進むことを求めても、複数 env の同時 +1 や、一部据置・一部 +1 は受理される。
  過剰拒否にならない最小の強化である。

**射程 (この決定が保証しないこと):**
- **今日この規則を強制する production consumer は存在しない。** activation record 自体が未実装であり、
  規則は将来の実装に対する受理条件の宣言である。
- **contract 実体の rollback を防がない。** 規則は世代番号の関係だけを述べる。番号が単調に進んでも、
  その番号が指す contract が旧較正へ戻る経路 (世代列の再定義、逆引き index の再束縛) は
  この規則の外にある。D176 が「逆引き index は module 属性として再束縛可能であり authority として
  扱ってはならない」と定めたのと同じ理由で、番号射影を authority と見なしてはならない。
- **活性化権限を与えない。** issuer、trust root、record の非偽造性、入口 receipt、
  bootstrap fuse の除去、後継世代の登録、current 切替のいずれも本決定には含まれない (D196 を維持)。
- **env 集合の追加・削除を伴う遷移の扱いを定めない。** 「全 env の delta」は同じ env 集合の間でしか
  定義できないため、集合が変わる遷移は本規則の適用外であり、別途裁定する。

**却下した選択肢:**
- delta ∈ {0,1} だけを残す — 全 env 据置を受理し、元の裁定が問題とした no-op を拒否できない。
- 全 env が必ず +1 — 較正を再取得していない env の据置まで拒否する過剰縮小になる。
- ちょうど 1 つの env だけが +1 — 複数 env を同時に活性化する運用を、裁定なしに禁止する。
- 規則と同時に純 data-layer の判定述語を実装する — 発火条件を満たす実 artifact も計測 ID も
  無いまま公開 API を置くことになり (`DW-G04`)、番号だけを見る述語は上記の rollback を
  塞がないため、名ばかりの保証を台帳へ残す。実装形は実 record schema と併せて裁定する。
