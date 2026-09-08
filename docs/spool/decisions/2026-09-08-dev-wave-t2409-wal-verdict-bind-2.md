---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t2409-wal-verdict-bind
seq: 2
---

## {{D:wal-verdict-realization}}. D1772 の実施形は WAL 3 field の値述語とし、projection digest は採らない

**決定:** D1772 が命じた「WAL の `anomalies` / `certified` / `verdict` を既存の内容 digest へ
含めて閉じる」の実施形として、**B-10 legacy 受理経路の `verify_done` ループへ 3 field の exact
値述語を足す**形を採る。系列別の WAL digest literal (whole-WAL も projection も) は**新設しない。**
射程は legacy 3 系列に限り、live campaign と trial campaign の受理集合は変えない。

**理由:**

- **既存の内容 digest の対象を字義どおり広げることは構造的にできない。** その digest は block
  record 本体の canonical JSON の sha256 で、**同じ値が現物 file 内に `record_sha256` として
  書かれている**。対象を広げるには 3 系列 135 個の凍結 file を書き換えるしかなく、それは literal の
  再発行ではなく凍結証拠そのものの改竄で、規律 7 と D1597 に反する。
- **D1772 自身が逃げ道を指定していた。** 同決定は「着手前に、既存 2 系列の literal を再発行せずに
  **追加 exact 条件として重ねられるか**を実測する」と命じている。実測の答えは「重ねられる、
  再発行 0 個」だった。よって値述語は代替案ではなく、決定が名指しした第一候補の実施である。
- **projection digest (`variant` + tag + 3 field に限定した digest) は第三の形として実在するが
  採らない。** 凍結 record を変えずに済み、timestamp や余分な key も固定しない点で whole-WAL digest
  より優れるが、新しい digest producer・期待値・対応規則を要する。これは D1772 の
  「新しい gate 機構は作らず、既存 digest を広げる局所修正とする」から遠く、D1769 とも逆向きである。
- 現物 3 系列は 3 field とも各 90/90 が正常値で field 欠落は 0 件のため、述語は達成可能であり
  既存の report 発行を壊さない。系列間の唯一の形の差 (read-heavy だけ `proof_surfaces` を持つ) は、
  述語が名指しの 3 field しか見ないため影響しない。

**却下した選択肢:**

- **凍結 block record を書き換えて digest の preimage を広げる** — 凍結証拠の改竄。
- **系列別の whole-WAL digest literal を新設する** — 判定対象でない timestamp・commit 数・
  `proof_surfaces` まで固定し、系列ごとに別 literal を要する。新機構の新設に当たる。
- **projection digest を新設する** — 上記のとおり、局所修正の範囲を超える。
- **gate を作らず限界を明記するだけにする** — D1772 が D1744 の誤引用として既に却下している。

## {{D:wal-verdict-claim-scope}}. WAL 判定の束縛が主張できる範囲を、記録値と終端済み frame に限る

**決定:** 本束縛が主張してよいのは「**WAL に記録された** 3 値が正常であること」だけとする。
WAL の真正性、値の生成主体、verifier が実際に走ったこと、block record との attempt 対応は
**主張しない。** 検査の母集合は「WAL reader が例外なく返した**終端済みで parse 可能な** record の
うち `stage == "verify_done"` のもの」と定義し、WAL 欠落・読取例外・未終端 tail は母集合に含めない。
collector の test は「WAL 述語との結線を通した」とだけ言い、「3 validator を通した」とは言わない。

**理由:**

- WAL に hash chain は無く、真正性を保証する仕組みが実装に無いことは WAL module 自身が明記している。
  3 field を正常値で自己申告した偽 WAL は述語を通る。閉じるには暗号学的束縛 = 新しい gate 機構が
  必要で、D1772 が却下している。**塞げていないものを塞いだと書かないために射程を先に固定する。**
- WAL 欠落・読取例外・未終端 tail では、`incomplete_slots > 0` か `wal_read_error` が立った
  **見て分かる別物の report** になる (completeness の集計関数は一度も送出せず開示するだけである)。
  D1772 が名指しした穴は「件数と tag が揃って**同じ判定の** report が出る」ことなので、
  これらはその穴に当たらない。fail-closed 化は受理集合をさらに狭める別の裁定事項である。
- **collector の正例で 3 validator を production のまま通すことは repository 内では不可能である。**
  validator は各 record の `submission_receipt` を実 path として開き bytes の sha256 を照合するが、
  現物の receipt は repository 外にある。receipt path を書き換えると record 内容が変わって
  自己 hash が凍結 literal と一致しなくなるため逃げ道が無い。先行 wave が同じことを実測して
  記録済みの構造的限界である。validator 側の証拠は系列別の専用 test が別に担う。
  **限界を書かずに「統合を通した」と記録することを禁じる。**

**却下した選択肢:**

- **「現物 verifier 判定へ束縛した」と書く** — 束縛しているのは記録値であり、実行ではない。
  規律 3 が求めるのは正しさシグナルの構造化であって、主張の水増しではない。
- **母集合を「全 verify_done」とだけ書く** — 実装が見るのは reader が返した終端済み frame だけで、
  散文が実装より広くなる。
- **collector の正例を「統合 test」と記録する** — 上流 3 gate が stub である事実を隠す。
