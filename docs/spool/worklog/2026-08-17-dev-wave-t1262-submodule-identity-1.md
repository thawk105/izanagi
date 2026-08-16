---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t1262-submodule-identity
seq: 1
title: submodule の initialization 判定が内容の実在を保証していなかった穴を塞ぎ、契約を生 bytes 同一性として宣言した (コード + テスト + docs、branch worktree-dev-wave-t1262-submodule-identity、変異 matrix = 12/12 KILLED)
---

## 本文

[T-1223] が scope 外に置いた三者照合の本体。`_submodule_worktree_state` は
「submodule path が Git top-level」かつ「HEAD == gitlink」で `initialized` を返すだけで、
**worktree の内容を一度も見ていなかった。**

**親が段 1 で受理形を 4 つ再現した。** 合成 snapshot を封緘したのち、`git_object_closure: true`
(production の既定値) で `verify_snapshot` を呼んだ結果である。空 CCBench (index 0 行・worktree は
`.git` のみ)、worktree bytes の差し替え、`HEAD^{tree}` に無い index entry の追加、
`.git` marker の rogue admin dir 差し替え — 4 つとも受理された。いずれも封緘後に設定できる
`submodule.<name>.ignore=all` に依存する。封緘処理は seal 時に `submodule.*` を消すが、
`verify_snapshot` は不在を再検査していなかった。

**契約を「生 bytes の同一性」として宣言した** ({{D:submodule-raw-bytes-identity}})。
段 2 のプランが推した clean filter 適用後の hash 比較を親が覆している。理由は
(a) 測るべきは試行が実際に読んだ bytes、(b) filter 経由だと改行コードの一括変換を受理する、
(c) filter 経由だと封緘済み snapshot の中で外部 clean driver を起動しうる、
(d) 検証側の config で結果が変わり同じ木が環境により受理・拒否に割れる。
段 3 の敵対レンズ B が (d) を独立に指摘し、レンズ A も
「exact-byte 契約なら raw が正しい」と裁定候補を整理して支持した。

**敵対検証 4 本が親の主張を 6 件倒した。** 最も重いのは、親の「実 CCBench で偽の拒否 0 件」という
実測が**作業木の pin を測っており実 snapshot が使う pin ではなかった**という指摘である。
実 pin を `--no-local` clone して測り直し、404 非 gitlink entry で不一致 0 件・mode 不一致 0 件・
object format `sha1`・全件 0.124 秒を確認して結論を維持した。
次に重いのは凍結 pin の閉包の数え違いで、親は repo 内の 2 件だけを数えていたが、
実際には repo 外の wave 成果物配下に 293 件あった。これが {{D:submodule-gate-oracle-bytes-unchanged}}
(oracle の bytes を変えない) を確定させている。
ほかに `apparatus-pin.json` の tool 全体 hash の見落とし ([T-1223] が既に歴史記録と裁定済みで
実装影響なし)、`copy2` が index stat cache を必ず無効化するという断定の誤り (本裁定は stat に
依存しないので設計影響なし)、検出 vector の数え方 (独立述語は 3 系統、本 wave の追加を含め 8 系統)、
費用「1 秒未満」の未確定を倒された。

**敵対レビュー 2 本が真っ向から衝突し、実測で裁いた。** レンズ A は
「source root repository にも config allowlist を掛けよ」を must-fix としたが、
レンズ B は実測で「実 source root には `user.*` と `extensions.worktreeconfig` がある」と示した。
掛ければ worktree ベースの build がすべて落ちる。**A の指摘は real だが実装しない**とし、
信頼境界を明示して裁定パッケージへ回した ({{D:submodule-config-allowlist-seal-boundary}})。

**fix が 2 度、実装の順序を誤った。** 1 巡目は認証の境界を封緘処理と取り違えて
計算ノードで 66 node を落とし ({{F:seal-time-inventory-hits-post-seal-allowlist}})、
2 巡目は「単一理由」の exact equality を統合 node にも適用して 9 node を落とした。
後者は仕様の誤解ではなく親の裁定の適用先の誤りで、段 4 裁定は
「helper 直呼びが単一理由、end-to-end は統合証拠 (包含)」と定めていた。
実測でも空 index の submodule は目的の理由に加えて `git fsck` の unreachable を併記する。
66 → 9 → 1 → 0 と収束させた。

**実測環境の落とし穴を 2 つ踏んだ。どちらも差分に帰属しない。** 1 つは submodule の
再帰初期化不足で、非再帰の `--init` では実 repo fixture の 3 node が error になる。
もう 1 つは親セッションの `FORCE_COLOR` が子 process へ継承されて無関係な node を落とすもので、
これは {{F:force-color-leaks-into-test-subprocess}} に記録した。

**子の工数。** codex 子は 10 回 (plan 1 / consult 2 / author 1 / review 2 / fix 4)。
親の測定は焦点走 8 回 (うち 2 回は bounded local の基盤失敗 rc=16、3 回は環境不足による赤)。
**codex 子は本 wave でも pytest を 1 度も実走できていない** — dispatch preflight が rc=16 になり、
測定はすべて親が計算ノードで引き受けた。

**段 8 の自己改善 2 件が L2 単節予算に入らず、実装せずユーザー裁定へ返した。**
どちらも今回の実測に裏付けられた既存命令の是正である。`DW-O20` の
`git submodule update --init` は非再帰では入れ子が未初期化のまま残り、実 repo fixture が
setup error になる — 是正は `--recursive` の 12 bytes だが、同節は現行 996 bytes で
単節予算 1000 bytes に対し 4 bytes しか空いていない。`DW-O18` への
`env -u FORCE_COLOR -u COLORTERM` 前置も同様に入らない (同節は約 930 bytes)。
既存文の圧縮は exact pin を壊すため取らなかった。両者は次の一手へ立てた。

材料レポートは `output/insights/2026-08-17_t1262-submodule-identity-gate/`。

## 次の一手差分

### 完了

- [T-1262] snapshot oracle に submodule の内容同一性 gate を入れ、契約を生 bytes 同一性として
  宣言した。受理集合は単調に縮み、正常 snapshot の oracle canonical bytes は変更前と
  917 bytes で完全一致することを実測した。
  remaining: none
  base: 6356b2d168e0a8f1000a6312c7b2cd922d785e14f6dbe0b36cc72673374f47ac

### 新規

- {{T:submodule-gate-source-root-config}} **P2・新規**: source root repository の local config を
  gate の信頼境界に入れるかを裁定する。段 6 の敵対レビュー A は allowlist の適用を要求したが、
  同じ段のレビュー B の実測が「実 source root には `user.*` と `extensions.worktreeconfig` が
  あり、掛ければ worktree ベースの build がすべて落ちる」と反証した。本 wave は
  {{D:submodule-config-allowlist-seal-boundary}} で適用外と裁定したが、
  builder が読む source repository の config で外部 program が起動しうる面は残る。
- {{T:dev-wave-l2-budget-blocks-measured-corrections}} **P2・ユーザー裁定待ち**: dev-wave の
  L2 単節予算 1000 bytes が、実測で誤りと判明した既存命令の是正を拒んでいる。
  `DW-O20` の `git submodule update --init` は非再帰では入れ子が未初期化で残り実 repo fixture が
  setup error になるが、`--recursive` の 12 bytes が入らない (同節 996 bytes、空き 4 bytes)。
  `DW-O18` へのテスト走行時の色指定除去も同様。既存文の圧縮は exact pin を壊すため取れない。
  予算の扱い (据え置き / 個別引き上げ / 節の再配置) はユーザー裁定に属する。
- {{T:submodule-gate-hardlink-toctou}} **P3・新規**: snapshot 外の hardlink alias で
  pre/post oracle の間だけ bytes を変える時間差改変は、内容同一性 gate では塞がらない。
  root repository にも同型に存在する既存の境界であり、pre/post oracle という現行機構の射程を
  どこまで広げるかを裁定する。
