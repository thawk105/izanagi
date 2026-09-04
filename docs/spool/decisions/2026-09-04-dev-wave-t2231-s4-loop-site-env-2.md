---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-04
wave: dev-wave-t2231-s4-loop-site-env
seq: 2
---

## {{D:s4-loop-site-guarantee-scope}}. 段 4 loop の site 対応が保証する範囲を driver 入口までとする

**決定:** `p3_s4_loop` の site 対応が保証するのは、driver 自身の入口 (`main` /
`drive_iteration` / 公開 `run_one_iteration`) を通る経路だけである。同 module が再 export する
`run_campaign` への直接呼出しは保証しない。この境界を塞ぐ新しい gate は作らない。

**理由:**
- 移植元 `p3_s4_loop_trigger_gating` の `default_cfg` も環境契約を bind せずに返しており、
  同じ性質を持つ。移植先だけに新しい防壁を足すと、移植であるという前提から外れる。
- 一方で「移植元にもあるから本 wave 起因ではない」は不正確である。移植前の
  `p3_s4_loop.default_cfg` は契約を bind 済みで、異なる契約の再 bind を `ident.py` の
  `bind_environment_contract` が拒否していた。未束縛化によりその拒否は消えた。
  **base に対しては実際の受理拡大である。** 隠さず境界として書く。
- 拡大が実害になるのは、未束縛 cfg を再 export された `run_campaign` へ直接渡す caller が
  存在する場合に限る。repo 内の caller を実測したところ production には存在せず、
  hit はテストと `loop.run_campaign` 自身だけだった。要求外の仮想リスクに対して
  framework・gate・検査を足さない方針に従い、gate は作らない。
- 事前登録した変異表はこの拡大を捕まえない。捕まえないことを台帳に書くことで、
  「変異が全部 KILLED だから安全」という過大な読みを防ぐ。

**却下した選択肢:**
- 公開 `run_campaign` を wrapper で包んで admission を強制する — 移植の scope を超え、
  呼び手が実在しない仮想リスクに対する防壁になる。
- `default_cfg` の bind を戻す — compute 経路で異なる契約の再 bind になり必ず例外で止まる。
  site 対応そのものが成立しない。
- 保証範囲を書かずに済ませる — 変異表が捕まえない拡大を黙って残すことになる。
