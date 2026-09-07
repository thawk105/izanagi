---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t2412-frozen-spec-fixpoint
seq: 2
---

## {{D:frozen-spec-ancestor-binding}}. 凍結 spec の commit 束縛は真の祖先関係とし、tree の同値は主張しない

**決定:** D1774 の実装として、`load_frozen_spec` は `provenance.source_commit` が
`loaded_head` の**真の祖先**であることを要求する (`git merge-base --is-ancestor`、等値は拒否)。
`loaded_head` は loader の冒頭で 1 回だけ解決し、spec・calibration・build receipt の全 blob 比較を
その OID に対して行う。実行時と finalizer の期待 header も `loaded_head` に統一する。
**保証するのは「spec の bytes が `loaded_head` の tracked blob と一致する」と
「`source_commit` が `loaded_head` の真の祖先である」の 2 つだけで、その間に何の変更が入ったかは
制限しない。** commit OID の同値も、実行中 module bytes が記録 commit に対応することも保証しない。

**理由:**

- 従来の「spec bytes == HEAD blob」と「source_commit == HEAD」の同時要求は hash の不動点であり、
  追跡 file である spec を一度も作れない。実 git で再現した。
- 等値を許すと不動点が戻る。真の祖先を要求することで、`source_commit` は spec を著した時点の
  commit という意味を保つ。
- 全 blob 比較を 1 回だけ解決した OID に束ねるのは、symbolic `HEAD:` を使うと blob 検査と
  後から解決する HEAD が別 commit を指しうるためである。共通親から spec だけが異なる兄弟
  commit を作り、blob 読取りと HEAD 解決の間に HEAD を動かすと、成果物が「検証していない
  spec を検証したことにする」記録を残す。

**却下した選択肢:**

- **唯一の親 + spec 1 path 差分を要求する** — 保証は強く (tree が spec path を除いて同値)、
  敵対レビュー 2 本と変異 9 件で検証もした。しかし freeze commit の後に 1 つでも commit が
  乗ると spec が二度と load できない。閉じようとしている失敗を作り直す。D1774 の理由欄も
  緩める方向を明示している。再裁定を求めて材料ごと返す。
- **`source_commit` field を廃し `loaded_head` だけに束縛する** — 事前に「どの code state 向けの
  spec か」を宣言する能力を失い、schema の exact key 集合も変わる。
- **HEAD 完全一致を残す** — D1774 が却下済み。不動点そのものである。

## {{D:mock-vcs-cannot-adjudicate-self-referential-binding}}. 自己参照する VCS 束縛を模擬 git で裁定しない

**決定:** commit hash・blob・祖先関係のように **spec 自身の内容が VCS の状態を指す**束縛は、
`subprocess.run` を差し替えた模擬 git だけで正しさを主張しない。実 repository を作り、実際に
commit した上で正例と負例を通す。模擬は schema・型・単発の分岐の高速検査に限る。

**理由:**

- `floor_pair_driver` の loader は 209 件のテストが緑だったが、production では spec を 1 度も
  作れなかった。模擬が `rev-parse HEAD` を定数に、`SOURCE_COMMIT = HEAD` に固定していたため、
  不動点が構造的に見えなかった。
- 模擬は「呼び出し側が何を尋ねたか」は検査できるが、「その問いに実 VCS がどう答えるか」を
  検査できない。自己参照する束縛では後者が本体である。

**却下した選択肢:**

- **模擬に不動点を再現させる** — 不動点は「commit すると hash が変わる」という VCS の性質から
  来る。模擬でそれを再現するには実質 git を書くことになる。
- **実 git のテストだけにする** — 型・schema の負例は模擬の方が速く、数も多い。両方を持つ。
