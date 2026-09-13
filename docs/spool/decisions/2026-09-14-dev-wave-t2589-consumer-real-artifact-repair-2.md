---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-14
wave: dev-wave-t2589-consumer-real-artifact-repair
seq: 2
---

## {{D:t1998-consumer-artifact-truth}}. 成果物から再導出できない等式は撤去し、保証しない範囲として明記する

**決定:** T-1998 の対 consumer が持っていた「記録された `toolchain_record_sha256` は、記録された
toolchain の identity 射影を canonical JSON 化した hash と等しい」という腕内の等式を**撤去する**。
残すのは manifest の非空性、digest の形式、**腕間の digest 一致**、腕間の manifest 一致、
`result.toolchain` との一致である。検証しない範囲は consumer の module docstring に明記し、
**両腕の digest を同じ別値へ置換した改竄はこの層では拒否できない**と書く。
この穴を塞ぐ新しい検査は足さない。

あわせて、実行 wrapper の前置を module 定数の literal で持つのをやめ、成果物と照合済みの
環境契約 digest から `env_contract.resolve_by_contract_sha256(...)` で hash 束縛のまま解決する。
`lookup(env_tag)` は使わない。

**理由:**

- producer は `--version` 全文を含む manifest から digest を作り、WAL には
  `requested` / `realpath` / `version_first_line` の identity 射影だけを記録する。
  回収成果物にその全文は無く (実測: 対象成果物 23 file に 0 件)、**どの実成果物でも
  この等式は成立しない。** 恒偽の述語は認証を止めるだけで何も守らない。
- 前置の literal は別環境の契約値の写しだった。D924 は「env contract の値を計測側へ literal で
  写す」形を却下し `env_contract` から引くよう既に定めている。D144 は当該環境の空 prefix に
  実測の根拠があることを確定している。
- **受理集合は広がる。** 事前登録の判定規則が動かないことだけを根拠にはしない。撤去したのは
  producer の証拠の意味を取り違えた等式であり、anomaly を出した variant や非直列化実行を
  通す変更ではない。認証 admission、全記録の anomaly / verdict 検査、abort 拒否は残る。
- 全文を成果物へ記録させる案と、producer の hash 対象を identity 射影へ揃える案は、いずれも
  producer を変えるため既存の測定が無効になり再測定を要する。得られる束縛に見合わない。

**却下した選択肢:**

- **producer に全文 manifest を記録させて digest を検証可能にする** — 束縛は保てるが、
  全 campaign の記録 bytes が動き、既に完走した測定をやり直すことになる。
- **producer が hash する対象を identity 射影へ揃える** — 同じく再測定を要し、加えて
  「全文を含む実行証跡用 hash」という意図された区別を失う。
- **恒偽の等式を残したまま運用する** — 認証経路が永久に閉じない。
- **撤去の代わりに別の検査を新設して穴を塞ぐ** — 成果物に無い証拠は何を足しても復元できない。
  ユーザーの立っている指示 (過剰なガードレールを足さない) にも反する。
- **前置を空 tuple の literal へ差し替える** — literal 写しという同じ誤りを向きだけ変えて残す。
