---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-07
wave: dev-wave-b4-paired-session-driver
seq: 1
---

## {{D:b4-paired-session-is-the-probe-bracket}}. B-4 の「1 つの低水準 session」は admission probe に挟まれた 1 区間とする

**決定:** D1699 が命じる「candidate と reference を 1 つの低水準 session で測る」の実体を、
**admission probe に挟まれた 1 区間**とする。1 pair-sample を独立した 2 つの side session とし、
各 side session は 1 区間の中で候補と参照を各 1 回測る。
`D = abs((median(candidate_1)/median(reference_1) - 1) - (median(candidate_2)/median(reference_2) - 1))`
とし、分母を side ごとに分ける。reference の測定は pair-sample あたり exact 2 件とする。

**理由:**

- `runner.measure_point` は `reps` 回の loop を回し**各 rep を別 process として spawn する**
  (`orchestrator/calibrator/runner.py:1122`、docstring も明記)。したがってこの repo で
  「1 低水準 session」が「1 process」を意味したことは一度も無く、現行の 1 role session ですら
  5 process の spawn 群である。「2 呼び出しは 1 session でない」という基準を適用すると
  「現行 driver には低水準 session が 1 つも存在しない」ことになり背理となる。
- D1699 が却下したのは**別々の session で測ったもの**を組だから同一と呼ぶ読み替えである。
  本決定は別々の session を作らず 1 区間 1 record へ統合するので、呼び名の変更ではなく
  実行構造の変更である。
- 低水準 API は binary を 1 個しか取らない (`measure_point` も `capture_measure_point` も同じ)。
  1 呼び出しで 2 binary を測る形は現行 API では構成できない。

**却下した選択肢:**

- 2 呼び出しを 1 session と呼ぶのは D1699 の再読み替えだとして実装を止める — 上の背理により、
  同じ基準が現行 driver の session 概念そのものを否定してしまう。
- runner へ対測定 API を足す — runner は全 campaign が使う共有の測定権威であり、
  本 wave の変更面 (driver とその test の 2 file) を超える。上の背理により必要でもない。

**残余として認めた点:** 区間内で候補の全 rep が参照の全 rep に先行するため、区間内ドリフトは
相殺されない。rep 単位で交互に測ればより強く相殺できるが、D1699 は要求しておらず、
D1641 §11.1 が測定手順の決定主体をユーザーに置いているため実装せずユーザー手番へ返す。

## {{D:b4-mid-probe-preserves-detection}}. session を 3 本から 2 本へ減らす際に中間 probe を残す

**決定:** side session の区間を `事前 probe -> 測定 -> 中間 probe -> 測定 -> 事後 probe` とし、
**3 つの probe がすべて clear のときだけ** complete とする。

**理由:**

- 3 session を 2 session へ減らすと probe 対が pair-sample あたり 3 対から 2 対へ減り、
  **競合を検出できない窓が広がる。** 現行なら候補と参照の境界で検出できた競合を取り逃す。
  これは既存の正しさゲートの弱体化であり規律 2 が禁じる。
- 中間 probe を残すと probe 総数は pair-sample あたり 6 個のままである
  (2 session x 3 probe = 6、変更前は 3 session x 2 probe = 6)。**検出力を維持するだけで
  新しい gate を足していない。** 既存の probe 呼び出し点を使うので subprocess 起動点の
  固定台帳にも影響しない。
- 中間 probe が clear でなければ 2 回目の測定を実行しない。実行時と finalizer の再導出の
  両方で発火することを変異走行で確認した。

**却下した選択肢:**

- 中間 probe を置かず「証明していないこと」へ未検出窓の拡大を書くだけにする —
  記述は弱体化を閉じない。既存の検出力を落とす変更になる。

## {{D:b4-freeze-binds-self-consistency-only}}. 凍結項目の一致検査が束縛する範囲を明記する

**決定:** reference の個数と D の式を spec の `statistics` へ必須 field として置き、
loader が module 定数との exact 一致を要求する。あわせて、この検査が束縛するのは
**同一 revision 内の自己整合**だけであり、定数が裁定値であることは証明しないことを
driver の「証明していないこと」へ明記する。

**理由:**

- 定数・spec・実装・テストを同じ commit で同期して変えれば、この検査は赤にならない。
  束縛しているのは「走行と事前登録済み spec の対応」であって「コードと裁定の対応」ではない。
  独立な pin も freeze receipt も無い。
- 謳っていない保証を謳わないのは T-2166 が採った形と同じである。新しい受領証や台帳を建てず、
  証明していないことを明記する方向で閉じる。
- 値の意味が変わるため spec / plan / window / summary の 4 schema を上げる。同じ識別子で
  意味の違う床値が流れると consumer が版を見分けられない。`candidate_floor` の field 名・
  値域・`status` の語彙は据え置く。

**却下した選択肢:**

- 凍結を事前登録文書側へ置く — `p3_b4_admission_record.py` の `_SECTION5_LABELS` が
  §5 の表を exact 10 label / 12 行に固定しており、欄を足す設計は実走前 admission を必ず赤にする。
  D1699 自身も §5 の値セルは sentinel のままだと述べている。
- 「凍結した」とだけ書き限界を書かない — 恒真に近い検査を保証として提示することになる。
