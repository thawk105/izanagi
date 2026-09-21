##### 赤 precursor の母集合 (適格性述語・順序・選択関数)

**台帳を 2 つに分ける。1 つの台帳に 3 つの役割を負わせない。**

- **`scheduled_attempt_registry`** — 予定した attempt を**全件**残す append-only の台帳。
  生成失敗・赤の非再現・重複・破損・screening のみの赤も、除外理由にせず固定 enum の理由を
  付けて残す。成功した attempt だけを載せる経路を禁じる。§7.1 の全件報告はこの台帳が担う。
- **`analysis_manifest`** — 上の台帳から適格性述語で選んだ分析対象。母集合はこの**全行**である。

**適格性述語** (結果を見る前に固定する。これ以外の理由で行を落とさない):

- `whiteboard.result` が `rejected` であり、かつ §3.1 が digest へ載せる 4 クラス
  (verify-red / liveness / other / diff-quarantine) の少なくとも 1 件を持つ。
  **screening だけの赤は適格でない。** §3.2 のとおり screening は**両アームとも** digest に
  載らず treatment の差分ではないため、構造的に treatment が発火しえない。
  これは結果を見る前の定義上の除外であり、事後の間引きではない。
- workload が、その driver の校正済み `PerfConfig` が定める workload に属する。
  **その workload を全件使う。** 結果を見てからの部分集合化を禁じる。
- 初期 proposal が、事前に固定した bootstrap 集合に属する。実走開始後に足さない。
- 後述の共通参照点 (`reference`) が一意に定まる。
- precursor を作った走行が**どちらのアームの digest も受けていない**。
  片アームの digest を受けた precursor から作った block は pair として成立しないので、
  適格でないとし、`scheduled_attempt_registry` には protocol violation の理由で残す。

**順序と選択関数:**

- `analysis_manifest` の行は、`scheduled_attempt_registry` の canonical 順序 (registry へ
  追記された順。同着は attempt id の辞書順) を保って並べる。
- 適格行が n 未満なら `design_not_feasible` とし、実走しない。**n を予算へ合わせて切り下げない。**
- 適格行が n を超える場合は、上の順序で**先頭 n 行**を採る。結果を見てから選び直さない。

**割当の無作為化 (帰無分布の前提):**

- 各 block について、on / off を実行 slot へ割り当てる 2 通りのうち 1 つを、**確率 `1/2` ずつ、
  block ごとに独立に**、**実走前に**選び、その schedule を `analysis_manifest` へ固定する。
  この無作為化が、後述の検定が使う「block 内でアーム label を交換してよい」という
  sharp な帰無仮説を成立させる。無作為化なしでは帰無分布は二項分布にならない。
- schedule を実走後に変えた block、および schedule どおりに実行されなかった block は
  protocol violation とする。**遵守の結果を verdict 関数の入力に含める。**
- この無作為化は測定順序の効果も同時に扱う。**逆順 1 本による順序効果の否定は行わない** (D1095)。

**完全性:**

- `analysis_manifest` は生成器と `scheduled_attempt_registry` から再生成でき、
  行集合と順序が exact に一致することを確かめられなければならない。
  **hash を記録するだけでは完全性の証明にならない。**
- 生成後の**追加・削除・並べ替え・driver の差替え**は `design_not_feasible` とし、実走しない。
- **registry 側の protocol violation を manifest から外して洗い落とせない。**
  `scheduled_attempt_registry` に protocol violation の理由を持つ行が 1 件でもあれば、
  その件数を verdict 関数の入力に渡し、実験全体を protocol violation とする。
  違反 attempt を後続の適格行で置き換えて成立を得る経路を、この規則が塞ぐ。
