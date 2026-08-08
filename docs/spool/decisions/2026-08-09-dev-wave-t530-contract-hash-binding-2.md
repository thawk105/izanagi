---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-09
wave: dev-wave-t530-contract-hash-binding
seq: 2
---

## {{D:contract-hash-identity-and-commit-binding}}. 実行契約 hash を campaign identity と WAL COMMIT の双方へ束縛し、lock 由来の期待値で照合する

**決定:** 認可済み実行契約の fingerprint (`contract_sha256`) を次の 2 箇所へ束縛し、
両者を独立に読み出して照合する。

1. campaign identity の正準 pre-image。`search_config.environment_contract_sha256` に
   64 lowercase hex の scalar として置く。`campaign.lock` の top-level は exact 5 key のまま
   変えない。env_tag・世代・receipt 属性・日時は入れない。
2. WAL の COMMIT record payload (`contract_sha256`)。`wal.log` 経由の 2 口だけに入れ、
   COMMIT 以外の stage と qualification event sink 経路には入れない。

照合は次の形とする。

- 期待値は **campaign.lock からだけ**読む。lock が hash を束縛していない campaign
  (legacy / guided の raw lane) では要求しない。
- **record の field 有無から必須性を推論しない。** 推論すると欠落 COMMIT が自動的に
  exempt になり、gate が恒真になる。
- hash は ever-active 解決を通し、解決した契約の env_tag と COMMIT record の env_tag を照合する。
  equality だけでは self-consistent な偽 hash を排除できない。
- **検証は tail repair の receipt 書込み・truncate と recovery の追記より前**に、
  同じ排他区間で完了する。拒否される campaign の bytes を 1 byte も変えない。

**理由:**
- 束縛前は認可の事実が成果物 bytes に残らず、proof chain が build admission receipt で切れていた。
  認可済みの再起動が無束縛 COMMIT を terminal とみなして skip でき、無認可の測定値が
  certified 選択の入力に残りうる。
- 期待値を lock からだけ取る形は、record が自分で自分を免除する経路を構造的に断つ。
  実測でも、この形にした変異 (必須性を record 由来へ倒す) は専用テストだけを赤にした。
- 検証を repair より前に置かないと、拒否する campaign の WAL bytes と repair receipt が
  先に書き換わる。「拒否したが成果物は変えた」という状態を作らないため順序を固定する。

**却下した選択肢:**
- **lock 隣接の別 record へ束縛して campaign identity を保存する案** — identity が同じまま
  異なる契約の記録を同一 campaign へ混ぜられる。構造的に分離しないと照合は後付けの検査に留まる。
- **COMMIT payload の hash 同士だけを比較する案** — 期待値の出所が record 側にあると、
  lock を持たない改竄でも自己整合してしまう。
- **qualification event sink 2 口へも同時に束縛する案** — その経路は campaign WAL ではなく
  T126 の evaluation event ledger であり、独自の receipt 連鎖を持つ。射程が別なので分離した。
- **世代 (generation) を identity 入力へ入れる案** — 別途裁定済みの独立課題であり先取りしない。
