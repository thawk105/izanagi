---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-04
wave: wave-t419-attestation-clock
seq: 2
---

## {{D:effective-clock-self-consistency-gate}}. 較正は自分自身の実行時述語を通るときだけ登録できる — probe の観測者効果は再裁定へ返す

**決定 (1): 取得時に自己整合 gate を置く。**
`--certify` 経路が `registered/` へ publish する候補 artifact は、**自分自身を観測値として
実行時 consumer 述語にかけて受理されるとき**にだけ publish する。満たさなければ
`effective-clock-self-comparison-failed` を品質 reason に積んで rejected とし、publish しない。
発火位置は publish (rename) より必ず手前である。ユーザー裁定 (2026-08-04) が求めた
「取得時に全要素が帯内であることの受入検査」の実体はこれである。

**決定 (2): 述語は consumer 側を正本とし、publisher はそれを共有する。**
純関数 `effective_clock_comparison_passes` を canonical とし、consumer (実行時 guard) と
publisher (較正取得 CLI) の両方が同じ実装を使う。issuer (attestation receipt の判定) は
**従来どおり独立実装のまま**とし、consumer が issuer の判定を再計算で裏取りする設計を壊さない。
独立 2 実装は drift するが、issuer が独立に残る限り相互裏取りは失われないためである。

**決定 (3): この gate が守る範囲は CLI publish 経路だけである。**
git 直接追加、旧 worktree からの持ち込み、attempt からの複製、pin 更新のいずれも
loader も hook も拒否しない。したがって「登録済み較正を守る」とは書けない。
機械的な補償として、契約 registry が参照する全 calibration を走査し、
**自己整合を満たさない entry の集合が既知例外と厳密に一致する**ことをテストで検査する。
既知例外は現 Pegasus 較正 1 件で、これが直ったときにもテストは赤くなる (反転の強制)。

**決定 (4): probe の観測者効果の是正は実装せず、ユーザー再裁定へ返す。**
attestation probe は `/proc/cpuinfo` を読むが、**読み取っているプロセス自身が走るコアが
turbo にいる**ため必ず帯外サンプルを生む ({{F:attestation-probe-observer-effect}})。
これは較正側にも実行時観測側にも乗るため、**較正を取り直しても実行時述語は通らない**。
是正案 (K 回読んで論理 CPU ごとに最小値を採る / 走行 CPU を記録して除外する /
帯外を 1 個まで許容する) はいずれも受理集合か凍結 bytes に触れ、
かつ計算ノードでの因果が未立証である。先に走行 CPU・cpufreq driver・boost 設定・同居プロセスを
束縛した probe 実験を置く。

**決定 (5): この wave は Pegasus の campaign を開かない。**
封じ込め (再発 publish の阻止と検出) だけを行い、較正の再取得・凍結 bytes の更新・
pin の更新はしない。

**理由:**
- ユーザー裁定は「述語を正とする」と定めた。述語を緩める案は規律 2 に反するため採らない。
- F97 の恒久対応が求めた positive control (参照が自分の判定を通ることの検査) は、
  gate と registry 不変条件の形で実体を持たせられる。
- 一方、裁定が同時に求めた「較正を取り直す」は、観測者効果が残る限り**取得時 gate が
  必ず落とす**ため実行できない。裁定時点で未見の事実であり、親が独断で読み替えない。

**却下した選択肢:**
- **述語を「中央値どうしの比較」や「帯外 1 個まで許容」へ緩める** — 受理集合が広がり、
  緩める根拠 (なぜ 1 個か) を持たない。裁定が「述語を正とする」と定めた方向にも反する。
- **attestation を campaign から外す** — 規律 2 に反する。通らないことを理由に検査を外さない。
- **gate を schema や loader の受理条件に入れる** — 現登録 artifact が即座に読めなくなり、
  再取得の道が塞がる前に proof chain の参照が壊れる。producer 側だけを狭める形を採った。
- **`tolerance_pct` の権威束縛をこの wave で決める** — 権威の出所 (policy 値か smoke 分布か) は
  設計択一であり、再登録前の blocker として裁定へ返す。
