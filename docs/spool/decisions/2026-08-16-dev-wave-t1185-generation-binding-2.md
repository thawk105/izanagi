---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t1185-generation-binding
seq: 2
---

## {{D:generation-binding}}. 8c 正式系列の世代数は manifest が宣言し、受入は宣言と実行の矛盾だけを拒否し、実効的な閂は起動側に置く

**決定 (1): 世代数の正本は `manifest.trials[].generations` とし、値は整数 2 に閉じる。**
manifest / registration schema を `p3-8c-trial-manifest/v2` / `p3-8c-trial-registration/v2` へ上げ、
trial 行の exact key へ `generations` を足す。`type(value) is int and value == 2` を要求して
`bool` を通さない。拒否 message は `trials[<index>].generations` の位置を含め、6 cell の
どれが不正かを運用者が特定できるようにする。top-level ではなく trial 単位に置く理由は、
registry・binding・admission・receipt がいずれも `trial_id` 単位の capability であり、
選択された 1 trial の起動条件を自己完結させる必要があるためである。

**決定 (2): 受入は 6 report 全件について、manifest の宣言値と report の
`generation_budget_per_workload` の一致を要求する。不一致は `[generation-binding]` で拒否する。**
これは「判定不能」ではなく**証拠と事前登録の矛盾**である。manifest が 2 世代の試行として
登録したものが budget 1 で実行された report は、決定 (3) の起動 gate を通っていないことを
意味する。したがって拒否されるのは「正当に起動できなかったはずの実行」であり、欠測でも
crash でもない。先頭 1 件での早期 return や `zip` の暗黙短縮に頼らず、全件を回ることが
構造的に保証される形で書く。負の対照は**末尾**の cell に不一致を置く。

**決定 (3): registered 起動は runtime の generations が manifest 宣言値と一致しなければ、
campaign identity 導出と run root 作成より前に fail-closed で拒否する。**
ここが実効的な閂であり、**落とす対象がそもそも生成されない**。CLI 既定値 1 を manifest の
2 へ自動補正することはしない — 事前登録文書が「世代数を明示的に指定しない起動を本系列の試行として
数えない」と規範化しており、補正は明示の要求を骨抜きにする。

**決定 (4): 実走世代数が宣言に届かなかった cell は、従来どおり partial として receipt に記録し、
拒否しない。** crash・supervisor-error・early-stop で 2 世代に届かなかった cell の扱いは変えない。
`stop_reason == "fixed-generation-budget"` のときに実走長 == budget を要求する既存規則
(`autonomous_trial_completeness.py`) をそのまま使う。全件報告・判定不能の契約を破らない。

**決定 (5): 世代数を `TrialBinding` / launch admission / lifecycle / 受入 receipt へ伝播しない。
run/report schema に v4 を作らない。** 起動時検査は manifest を再読して等価性を得るため、
封印値を binding に持たせなくても同じ保証が立つ。伝播すると launch admission の exact key 契約と
originless 互換 golden の bytes が変わり、等価な保証に対して影響半径だけが大きくなる。

**理由:**

- 承認上限 `MAX_APPROVED_GENERATIONS = 2` は上限しか強制せず、予算 validator は 1 以上を受理し、
  CLI 既定値は 1 である。budget=1 の 6 cell は manifest 登録・launch binding・完全性検査・
  受入 gate をすべて通過できた。上限を下限へ流用せず、宣言と実行の間に別の束縛を置く。
- **「拒否」だけでも「記録」だけでも成立しない。** 正式受入で partial report を拒否する案は、
  file-drawer を受入側で開け直す (走らせた試行が receipt に一切残らない経路ができる)。
  一方、受入 receipt の `certifying` は literal `False` に固定されているため、
  「exact 2 でなければ non-certifying にする」だけの案は受理集合を 1 bit も変えず**恒真**になる。
  budget (宣言・起動意図) と actual (実際に起きたこと) の間に線を引くことで両方を避ける。
- 決定 (2) の比較は恒真ではない。manifest 側は parse 時点で 2 に閉じているが、report 側の
  budget は 1 を取りうるので分岐が生きている。変異で裏取りした
  (比較の無効化が末尾 cell の負例だけを赤にする)。

**却下した選択肢:**

- **正式受入で partial を拒否し `report.cells` を 1 個へ狭める** — 欠測・crash・不一致を
  「判定不能として残す」でなく「台帳から落とす」に変える。file-drawer を塞ぐために積み上げた
  registry・lifecycle・全件報告の設計と正面から矛盾する。
- **manifest を触らず定数だけで exact 2 を検査する** — 事前登録 artifact に宣言が残らず、
  「何世代の試行として登録されたか」を後から証拠で辿れない。
- **CLI 既定値を 2 へ変える** — 「明示しない起動を数えない」という規範に反する。
  既定値が literal 1 であることは AST で意図的に釘付けされている。
- **`MAX_APPROVED_GENERATIONS` を exact 下限として流用する** — 上限と下限は別の概念であり、
  上限の引き上げ (多世代開放) と正式系列の固定予算を同じ定数へ縛ると両方を動かせなくなる。
- **run/report を exploratory v3 / registered v4 の tagged union へ割る** — 正式系列だけを
  狭めるには有効だが、本決定の目的 (宣言と実行の突き合わせ) は既存の
  `generation_budget_per_workload` と `cells[].generations` で足りる。schema を割ると
  verifier の検査順序変更まで必要になり、pilot の受理集合へ波及する危険が増える。
