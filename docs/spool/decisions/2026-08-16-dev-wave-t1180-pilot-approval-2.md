---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t1180-pilot-approval
seq: 2
---

## {{D:pilot-approval-argv-nonce}}. 床値 pilot の承認は投入引数で渡し、値を submission nonce に束縛する

**決定:** 標準投入経路における床値 pilot の不可逆承認は、投入器 `tools/pegasus/submit_floor.sh` の
zero-arity 引数 `--confirm-irreversible-pilot-holdout` で人間が明示的に渡す。承認時だけ
`qsub -v` へ `IZANAGI_CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT=<submission nonce>` を追加し、
job script は **submission nonce との exact 一致**を確認したときだけ driver argv の末尾へ既存 CLI flag
`--confirm-irreversible-pilot-holdout` を 1 個 append する。承認 env が設定済みで不一致 (空文字を含む)
なら、build と driver より前に既存 `write_failure` の `submit_binding` で停止する。
承認 env が未設定なら flag を渡さない。

**この決定が保証すること**は「標準投入経路で明示 token を要求する運用 gate」だけである。
**承認主体の人間性は保証しない** (D356)。raw `qsub`、driver 直接起動、Python API 直接呼出し、
投入器自身の hidden drift は保証範囲外であり、これらは非標準・非認証経路として扱う。

**理由:**

- 変更前は wrapper が driver へ `--mode pilot` と `--protocol` しか渡さず、driver 側の承認 gate に
  よって**標準投入経路から床値 pilot が 1 回も起動できなかった**。CLI flag は既に存在していたので、
  欠けていたのは投入経路の運び手だけである。
- 値を固定 literal にしないのは、投入者の shell 環境に同名の変数が残っているだけで全投入が
  承認済みになる事故を防ぐためである。scheduler が `-v` 指定外の環境を継承するかは未実測であり、
  nonce は投入器が実行時に生成するので ambient 環境には構造的に存在し得ない。
  この束縛は新しい artifact も schema も作らず、既存の submission nonce を再利用するだけである。
- 不一致を fail-closed にしたのは、承認の意図が壊れている投入で一回性 key を焼かないためである。
  安全側の availability 低下 (投入が止まる) は、未承認の不可逆消費より望ましい。

**却下した選択肢:**

- **submit receipt へ承認 field を足して env と一致を要求する** — D356 が「receipt を足せば
  人間承認を表現できる」を既に却下している。加えて receipt の exact key 集合は job 側と
  `certified_writer_admission` の 2 箇所にあり、後者は driver より前に走るため、
  field を足すと**承認付き job が driver 到達前に全滅する**。env を立てられる主体は driver を
  直接起動できるので、この束縛は弱い経路だけを塞ぎ強い経路を塞がない。
- **承認 receipt (repo 外) の実在を wrapper が確認する** — 新しい承認機構の新設に当たり、
  粗い provenance で足りるという既定方針と衝突する。
- **wrapper で無条件に承認 flag を渡す** — 一回性 key を既定で消費する。
- **driver 側の gate を緩める** — 規律 2 に直接違反する。gate は 1 byte も変更していない。
