---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-11
wave: dev-wave-t8b-restart-residue
seq: 2
---

## {{D:toolchain-binding-and-unlock-are-inseparable}}. 床値 compiler の site 依存化は toolchain 束縛検査と同じ commit でしか入れない

**決定:** 床値 campaign の compiler 解決を `buildcache.DEFAULT_CC/DEFAULT_CXX` の固定要求から
`buildcache.compilers_for_current_site()` へ寄せる変更は、**calibration 由来の toolchain 束縛検査が
同時に入る場合にだけ** land してよい。片方だけの land を禁じる。
同じ理由で、official mode の解禁 (床値 campaign の無条件拒否の撤去) も、束縛検査が
既に入っているか同じ wave で入る場合にだけ行う。

**理由:**

- 固定要求は事故ではなく**現に効いている fail-closed 障壁**である。Pegasus には `g++-13` が
  無いため、`buildcache._tool_version` が
  `toolchain cxx が PATH に存在しない: 'g++-13' (fails-closed)` で倒れる。
- site 依存化だけを入れると Pegasus compute で system compiler (実測 gcc 11.4.0) が解決され、
  build が通るようになる。束縛検査が無ければ、これは
  **「認可されていない compiler で床値を測れるようにする」だけの変更**である。
  再開手順書 §1.2 が「既定 compiler へ黙って倒すのは選択肢にしない」と定めた当のものになる。
- 床値は freeze v2 の `floor` / `budget` を埋め、oracle gate の受理判定を動かす。
  どの compiler で測ったかが契約に紐付かないまま値が入ると、certified 選択の判定境界が
  提示できない根拠に依存する。compiler 差は backoff 級の差を容易に上回る
  (`buildcache` 自身の記述)。
- 束縛と解禁は同じ受理集合の表裏である。別 wave に割ると
  「解禁したが束縛が入っていない」窓が構造的に開き、その窓は解禁の瞬間に
  認可外 compiler の床値が通る形で顕在化する。

**却下した選択肢:**

- **site 依存化だけを先に land する** — 障壁を外して代わりを置かない。単調に悪化する。
- **束縛検査だけを先に land する** — 発火経路が無い (`DW-G04`)。official は拒否され、
  投入 script に pilot 経路が無く、pilot 実測は再凍結適格から除外されるため、
  本番で一度も走らないコードが増える。
- **固定要求のまま `g++-13` を Pegasus へ用意する** — 用意経路は root 権限か
  コンテナに限られ、計測条件を変える点は同じで、変更が計測機の外に出る。
