---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t1179-publish-seam
seq: 2
---

## {{D:floor-publish-eligibility-from-seams}}. floor の publish 適格性を mode でなく実引数の seam 集合から導く

**決定:** `s8b_floor_campaign` の `eligible_for_refreeze` は `mode` 一語から導かない。
`_run_campaign_core` の入口で raw 実引数から非既定 seam 集合を算出し、
「canonical plain str の `"official"` **かつ** `resume_dir is None` **かつ** 非既定 seam ゼロ」
のときだけ真とする。判定値は caller が渡せる引数にせず、`assemble_result` は常に偽を生成し、
core 内の引数を取らない finalizer だけが上書きする。
seam 集合の定義は public wrapper の拒否表と同じ helper を単一源とする。

**理由:**

- 従来は private core へ外部 measure を注入した実行でも、通常の `result.json` が
  refreeze 適格として発行できた。外部 measure は attempt marker を 1 件消費するだけで
  callback 内の spawn 回数を数えられず、選別した値を載せられる。
  下流 (`s8b_ratified_freeze` / `s8b_holdout_freeze`) はこの 1 bit しか検査しない。
  これは規律 2 の直接の攻撃面である。
- 旧式に条件を追加するだけなので、今まで偽だったものが真になることはない。
  受理集合は縮小方向にしか動かない。
- 判定を caller 引数から外したので、`assemble_result` を直接呼ぶ経路から
  真の artifact を作れない。

**却下した選択肢:**

- **gateway 観測証跡の in-process 台帳を publish の必須条件にする** — 段 2 プランの中核だったが、
  外部 measure を使う実行は seam 集合だけで必ず偽になるため純増検出力がゼロで、
  既定 measure では `run_once` が subprocess より前に allowance を消費し rep 失敗でも
  残 rep を回すため事実上つねに真になる。恒真に近い保証であり、
  module 属性差し替えには seam 集合と同様に耐えられない。
  台帳を artifact へ載せない以上、下流も再検証できない。
- **result へ証跡 field を足す** — 下流が result の key 集合を exact に検査しており、
  field 追加は consumer 変更なしでは拒否される。durable で下流が検証できる証跡は別タスクの所有。
- **警告を出して通す・flag や環境変数で無効化できる形** — 受理集合を緩める方向であり、
  攻撃面そのものなので採らない。

## {{D:floor-authority-artifact-published-last}}. 権威 artifact を補助 artifact より後に publish する

**決定:** floor campaign の二相 finalize では、補助の `result.md` を先に、
consumer の権威である `result.json` を最後に publish する。

**理由:**

- publish 適格性を fresh・seam ゼロへ束縛した結果、二つの publish の間で停止すると、
  真の `result.json` が残る一方で resume は偽を再構成して bytes 不一致で停止するため、
  真を撤回できなくなる。下流の ratified consumer は `result.md` を閉包に含めないので、
  この取り残しをそのまま受理できてしまう。
- 権威ファイルを最後にすれば、中断で可視になるのは補助ファイルだけになる。
  一般に、閉包に入る権威 artifact は閉包外の補助 artifact より後に可視化するのが安全側である。

**却下した選択肢:**

- **resume 側で取り残しを回収して撤回する** — 撤回のために既 publish の権威 bytes を
  書き換える経路を作ることになり、create-only の不変条件を壊す。
- **下流の閉包へ `result.md` を足す** — consumer の受理条件を増やす変更であり、
  producer 側の順序 1 行で閉じるものに対して過大である。

## {{D:in-process-argument-gate-scope}}. 同一 interpreter 内の argument 境界に monkeypatch 耐性を主張しない

**決定:** 実引数から導く publish gate は、**supported API 経由の経路**を閉じるものとして記録する。
同一 interpreter 内での module 属性差し替えに対する耐性は主張しない。
docstring と台帳へ既知限界として明記する。

**理由:**

- 同一 interpreter 内の module 属性差し替えは任意コード実行と同値であり、
  引数を検査するどんな gate でも防げない。防げると書けば、謳うだけで発火しない保証になる。
- 実際に、既定 callable を module 属性経由で差し替えてから同じ実体を引数に渡すと
  identity 比較を迂回できた。import 時の private sentinel で この経路は塞いだが、
  これは限界を縮めただけであり、耐性の証明ではない。

**却下した選択肢:**

- **「publish 経路を閉じた」と無条件に記録する** — 実態より強い主張になり、
  後続が耐性を前提に設計してしまう。
