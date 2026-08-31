---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t1814-c10-satisfaction
seq: 3
title: [T-1814] 完了証明層を C10 で開き、条件 id 追加の手続きを先例ごと固めた (code + docs + insight、branch worktree-dev-wave-t1814-c10-satisfaction、変異 4/4 KILLED)
---

## 本文

D1026 の実装。8c 事前登録の 12 条件のうち充足を返せる条件が 1 つも無い状態
(D959 が最上流と定めた閉塞) を、C10 1 件で開いた。設計判断は
{{D:c10-static-readiness-precedent}} と {{D:satisfiable-condition-admission-procedure}}。

**着手前の実測が設計を決めた。** 親が合成 repo 4 本へ評価器を実走したところ、正直な実装と、
検証呼び出しを到達しない枝へ入れた実装・例外を握り潰す実装・受入側の呼び出しを殺した実装が
**すべて同じ終端に到達**していた。したがって終端を充足へ差し替えるだけでは、D438 が規律 2 違反と
して却下した「静的検査を通るだけの実体のない実装を充足と認定する」形になる。実装の本体は
終端の差し替えではなく検査そのものの強化だと段 4 で裁定した。

**段 2 プランの中心的な提案を実測で覆した。** プランは reader 内のデータフロー
(読取 → digest 照合 → 不一致で raise) まで静的に追跡する案だったが、本番の受入経路にある
verifier 呼び出しに対して既存の到達可能使用判定が偽を返すことを親が実測した。追跡を課すと
**正しい実装を偽赤にする**。代わりに「実 repository で当該条件が充足を返すこと」を必達の関門に置き、
恒真性と偽赤を 1 つの関門で同時に塞いだ。

**段 3 レンズ A が、強化後の検査でも空の実装を構成できることを実証した。** 関数の実行時再束縛
1 行で静的検査を素通りする。これは静的判定器の原理的な限界であり、塞げないものを塞いだと
書かない方針を取った。条件本文へ限界 6 項を列挙し、条件 12 が同じ様式で機械検査対象になっている
先例に倣った。

**段 6 レビューが 2 つの穴を追加で出した。** `contextlib.suppress` による握り潰しは、正本が
非握り潰しを明示的に主張している以上、主張を弱めるより塞ぐ方が正しいと裁定して塞いだ
(3 綴りすべてを拒否し、例外を握り潰さない普通の `with` は通すことを親が実測)。
`return b""` だけの reader が通る件はデータフロー追跡を要するため限界として宣言した。
負例 2 件が過剰決定だった件は、放置すると変異が生存して matrix が証拠にならないため、
単一理由の負例を追加させた。

**ユーザーへ返す裁定パッケージ 2 件。** (a) 旧 campaign の live-resume 互換のため
enforcement source binding を緩めるか — 受理を緩める方向のため本 wave では実装しない。
(b) 完了証明層の証拠に AST 以外の実行可能な証明を含めるか — 静的解析だけでは実行時の再束縛を
塞げないことが実証されたため、2 件目以降で条件ごとに問い直す設計択一が残る。

**並行 wave との衝突。** `worktree-dev-wave-t1806-prereg-c10-fieldpaths` が同じ条件 10 を対象に
判定器版 v7 と条件凍結 g12 を取ろうとしていた。主題は補完的 (向こうは証拠契約の field を広げ、
こちらは充足可能集合を開く) だが番号が衝突するため、着地順で後になった側が寄せ直す。
本 wave の commit 直前と受入投入の直前に着地状況を確認した。

**セッション異常。** 段 5・段 6 とも実装子側で `tools/run_tests.py` が
`rc=16 / child_started=false` (`qstat -Q preflight rc=1`) となり、**pytest node が 1 件も
実行されなかった**。テストの緑はすべて親が取り直した。子の「回帰なし」は実走に裏づけられて
いなかった。変異 harness の node 形式の食い違いは F71 への再発として記録した。

**エージェント工数.** codex 子 7 本 (plan 1、consult 2、review 2、author 1、fix 1)。
変異本走は 3 回 (1 回目は起動前中止、2 回目は node 形式の不一致、3 回目で 4/4 KILLED)。

## 次の一手差分

### 完了

- [T-1814] 完了証明層を C10 1 件で開き、条件 id 追加の手続きを事前登録正本へ固定した。
  判定器版を v7 へ上げ、D1026 を引く第 12 世代の条件凍結 record を同じ commit で発行した。
  remaining: none
  base: ed5bf049043c80979d3403e2e14be0d4b74adf12af8fe2ef9e27010c7a171b2b

### 新規

- {{T:enforcement-source-binding-resume-compat}} **P2・ユーザー裁定待ち**: 判定器・評価器の
  bytes 変更で enforcement source closure の epoch が変わり、旧 commit を束縛した campaign の
  live resume が drift になる。互換のため source binding を緩めるかを問う。受理を緩める方向の
  ため AI は実装しない。
- {{T:completion-proof-executable-evidence}} **P1・ユーザー裁定待ち**: 完了証明層の証拠に
  AST 以外の実行可能な証明を含めるか。静的解析だけでは実行時の再束縛を塞げないことが
  実証済みで、2 件目以降の条件ごとに問い直す必要がある。
- {{T:mutation-harness-node-normalization}} **P2・新規**: 変異 harness の比較器が
  `DW-M08` の要求する「同形式へ正規化した記録 node との完全一致」を満たしていない。
  記録側の xdist group 接尾辞を正規化し、group 付きテストを期待 node に書けるようにする。
  正例は group 付き node を含む spec が KILLED 一致すること。詳細は F71 の 2026-09-01 再発。
