---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: dev-wave-t1621-suite-order-dependence
seq: 1
title: [T-1621] 受入 suite の順序依存を grouped 連鎖 3 本の完全反転で測り、positive control 付きで差ゼロを確認した (docs のみ、branch worktree-dev-wave-t1621-suite-order-dependence、実装差分ゼロ)
---

## 本文

- 依頼は「D746 で受入 work unit 順序を大きく変更したことを受け、suite の順序依存を能動的に調べる
  record-first wave」。実測記録は `output/insights/2026-08-24_t1621-suite-order-dependence.md`。
  設計判断は {{D:order-dependence-control-uses-grouped-unit-reversal}}、
  失敗は {{F:grep-counts-code-inside-string-literals}} と F270 の再発。

- **最大の発見は「D746 は直列連鎖の内部順を 1 つも変えていない」ことだった。**
  受入の並べ替えは work unit 単位で、unit 内の item は連続かつ元の相対順のまま動く。
  `--dist loadgroup` では ungrouped node が 1 件 = 1 unit なので、**「unit 内順序」が存在するのは
  `xdist_group` を持つ node だけ**である。権威ある group は `real-repo` / `s8c-preregistration-candidate`
  / `dev-waves-runtime` の 3 つで、合計 89 node。**D746 の受入緑は、この 3 連鎖の順序依存について
  証拠になっていない。** しかも `real-repo` こそが、suite で唯一「親 repo status と共有 submodule」
  という可変共有状態を触る集合である。事前確率が最も高い場所がそのまま唯一の未検査面だった。

- **grouped 連鎖 3 本すべてを反転し、outcome 差はいずれもゼロだった。** 実行順の逆転は仮定にせず
  junit の testcase 順で毎回検証した。`real-repo` は優先 2 node を除く 70 node が完全逆転
  (位置ずれ平均 35.3、完全逆順の理論値 35.0)、他 2 本は完全逆転。実行は 48 / 89 node
  (`real-repo` の 72 node のうち 41 が skip)。`real-repo` の正順は計算ノードと login node で
  2 回走らせ、同一 outcome を得た。

- **positive control が成功した。** 「全部緑」に意味を持たせるには検出網が実在する順序依存を
  捕まえる証明が要るという段 3 レンズ A の指摘を採り、`s8c-preregistration-candidate` group の
  2 node へ module global を一時注入した。A 単独=緑、A→B=緑、**B→A=A が赤**。
  tracked file の一時変異は同 wave 内で復元し、`git hash-object` が commit の blob と一致することを
  確認した。証明できたのは「同一 group・同一 worker 内の module global 漏れの検出」だけである。

- **親の主張が 3 回誤り、そのうち 1 つは段 2 plan 子、2 つは段 3 レンズ A が反証した。**
  (1) 「D746 の並べ替えは real-repo 連鎖の内部順も変えた」→ 実装は unit 単位で内部順を保存する。
  (2) 「D746 の land 時の受入全走がほぼ最大の負の対照として成立していた」→ 撤回した。
  根拠にした距離 0.315 は `--collect-only` (D746 が無効化される) 上の item 粒度 offline proxy で、
  正規化平均絶対変位は完全逆順が約 0.5・ランダム置換が約 0.333 なので「ほぼ最大」は導けない。
  (3) 「module import 時に env を直書きするテストが 2 件ある」→ どちらも生成子スクリプトの
  文字列リテラル内だった。

- **段 3 の敵対 2 レンズが独立に同じ最重要欠陥を突いた。** plan が提案した targeted の AB/BA 対照は、
  runner が targeted 走にも既定で loadgroup を付けるため、ungrouped pair では所要降順へ潰されて
  「逆順のつもりが同じ順」になる。**この指摘がなければ、同じ順序を 2 回測って「順序非依存」と
  記録していた。** 親は grouped unit 内の反転だけを対照に採る裁定へ変更した。

- **repo が唯一明示的に認めている順序依存は、既定では発火していない。**
  `REAL_REPO_EXECUTION_PRIORITY` の 2 node は両方とも growth hold で skip される。
  `real-repo` 連鎖 72 node のうち実行は 31 件 (43%) で、34 件が growth hold、
  4 件が条件付き未実走、3 件が slow real-build canary である。

- **順序独立性は偶然ではなく設計されていた。** 既知の共有状態を隔離する機構が 4 つある
  (実 repo 利用 node の 1 unit 化、実行優先順、receipt memo の scheduling 前 prewarm、
  production の process pin を毎テスト前後で戻す autouse 隔離 3 本)。
  ただしこれらは隔離機構であって順序独立性の証明ではなく、各機構に発火しない条件がある。
  共有 receipt memo の読み手は一切書かず `cache-missing` で fail-closed するので、
  依頼が挙げた「共有 output tree の first-writer 判定」はこの経路については実在しなかった。

- **実装差分ゼロで閉じた。** 恒久的な順序 shuffle 機構、実行列 receipt、実 repo 利用 node の
  完全性を checkout 以外まで機械強制する設計は、いずれも受入面 (`conftest.py` /
  `test_acceptance_schedule_order.py` / runner の許可表) を触るため、ユーザー指示に従い
  実装せず次の一手へ返した。段 5・6 を飛ばし 4→7→8→9 とした。変異 matrix は実装差分ゼロで免除、
  受入全走は免除していない。

- **子の工数:** codex 子 3 本 (plan 1 / consult 2)。全て `gpt-5.6-sol`、`reasoning=xhigh`、
  `check_codex_output.py` rc=0。実装子・fix 子は裁定により 0 本。実走はすべて親が行った。
  背景 job で `nohup setsid` を harness の背景実行の中で使うと、harness が wrapper の即時終了を
  「完了」と通知する事象を再現した (F518 の型)。現物照合で救えた。

## 次の一手差分

### 完了

- [T-1621] 受入 suite の順序依存を静的棚卸し + 負の対照で測った。grouped 連鎖 3 本 (89 node、
  実行 48 node) を完全反転して outcome 差ゼロ、positive control 成功。依頼が名指しした 3 vector
  (scope fixture / `tmp_path_factory` の連番 / 共有 output tree の first-writer) はいずれも
  実在しないか無害と判定した。未測定面は新規項目へ分けた。
  remaining: none
  base: 5e255198cd7653c84a963a9efab8f7266b6c647dc5d01676ee1387326fb4ac19

### 新規

- {{T:ungrouped-order-dependence-probe}} **P2・新規**: ungrouped node (1 件 = 1 work unit) の
  順序依存を測れるようにする。現状 targeted の AB/BA は受入並べ替えに所要降順へ潰されるため、
  実装ゼロでは任意順序を作れない。診断専用の実行列 receipt か順序固定の seam が要る。
  編集面が受入の並べ替え面と runner の許可表に掛かるので、並行 wave との所有調整を先に決める。
- {{T:real-repo-serial-completeness-enforcement}} **P2・新規**: 実 repo 利用 node の直列集合への
  登録漏れを、共有 submodule の checkout 経路以外でも機械強制する。現行 guard は 1 callsite だけを
  守り、collection / import 時・子 process・新 thread・直接 git・親 repo status の読み書きは射程外である。
- {{T:real-repo-chain-detection-power}} **P2・新規**: 実 repo 直列連鎖の検査力が 43% (31/72) まで
  落ちている件を裁定する。34 件が correctness gate 付きの growth hold で、release は明示ユーザー
  指示のみ。最高リスク面の過半が既定で走らない状態を許容するか、コストを下げて戻すかを決める。
- {{T:worker-crossing-order-dependence}} **P2・新規**: worker を跨ぐ overlap 依存を測る設計を立てる。
  共有 submodule の apply 窓、patch lock、tmp 上の memo 2 種、外部 process / socket が対象で、
  直列対照では原理的に踏めない。既存の flaky hold 1 件がこの型の実例である。
