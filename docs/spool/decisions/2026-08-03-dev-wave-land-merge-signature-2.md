---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-03
wave: dev-wave-land-merge-signature
seq: 2
---

## {{D:land-signature-outside-trusted-cutoff}}. landed 区間の fold 署名は「trusted main cutoff の外側で加えた変更」に対して判定する

**決定**: `verify_declared_fold_commit` の fold 署名判定は、各 landed commit が
**trusted main cutoff の外側で加えた変更**を対象にする。parent が 2 以上の commit では、
tested main cutoff の祖先である parent がちょうど 1 つのときだけ、その parent との差分を
判定にかける。0 個または 2 個以上のとき、および cutoff が渡されない呼び出し経路では、
全 parent との差分を判定にかける (fail-closed)。署名 2 条件
(`M docs/spool/FOLDED.md` / spool fragment の削除・rename source) は変更しない。

**理由**: ff-only が main へ適用するのは「wave が trusted main の上に加えたもの」だけである。
それ以前の実装は `git diff-tree -m` で親ごとの差分を見ていたため、`DW-O23` が指示する
「land 前の wave 側 main 取り込み merge」が、wave 側の親との差分に main が既に取り込み済みの
fold 署名を必ず含み、常に拒否された。fold は 2026-08-02 以降すべての land が `FOLDED.md` を
変更するので、main が動いた後に取り込みが要る wave は正規手段では land できなかった。

**採らなかった案**:
- **累積差分** (`base..tip` の端点比較): hidden fold の後に protected tree を base へ戻す履歴を
  見逃す。fold の効果が消えても canonical 台帳の偽造内容だけが残る経路がある。
- **merge の署名を三 tree 等式で免除**: 免除が path 単位なので、protected 2 path を main 親から、
  canonical 台帳を wave 親から採る merge が通る。fold は複数 path を同時に動かす transaction
  であり、path を独立に証明しても transaction の由来は証明できない。加えて
  commit × parent × key × 候補で git subprocess が増え、共有 deadline で正規履歴を
  timeout 拒否しうる。

**この決定が保証しないこと**: 署名 2 条件は lock 外 fold の**十分条件ではない**。
canonical 台帳だけを書き換える履歴、`T` (gitlink) を経由する復元、同一 commit 内の A→D は
判定を通る。これは本決定の前から存在する性質で、本決定は受理集合をこの方向へ広げも狭めもしない。
閉じるには fold transaction の意味検証が要り、「legacy wave が canonical を直接編集する」
現行契約と衝突するため、独立の裁定を要する。

**射程**: land CLI 経路のみ。supervised runner (checker / daemon) は receipt の初期
`base_main_sha` に束縛されており cutoff の意味が違うため、正規 main merge を拒否したままである。
