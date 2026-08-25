---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-t360-mutation-transport-task
seq: 1
---

## {{D:dispatch-task-enum-mutation-generic}}. 投入表の task 閉集合を 4 値へ広げ、汎用 task は compute 限定契約で受理する

**決定:** `tools/pegasus/dispatch_compute.py` の `TASKS` を
`{tests, provenance, mutation, generic}` とする。**D105 決定 3 の閉集合 2 値を supersede する。**

- `mutation` は `tools/mutation_worktree.py` を子とし、変異 wrapper 1 呼び出しを 1 job へ束ねる。
  既存の `--runner-mode dispatch` 経路は置き換えず並存する。
- `generic` は固定の子 script を持たず、渡された argv 自体を `shell=False` で実行する。
  受理するのは非空の string list だけで、shell 文字列は受理しない。

汎用 task の安全性は次の閉じた契約が担う。**hook は担わない。**

1. compute 限定 — `_job_script` と `_job_run` の二重 bnode gate を通る
2. request からの環境値をゼロにする (clean env)
3. stdin を `DEVNULL` にする
4. cwd を repo root に固定する
5. 子 rc をそのまま伝播し、transport の infra rc と混ぜない

**D103 決定 5 との関係:** 同決定が守る性質は「**login で**任意 argv を実行しない」である。
`exec_calibrate.py` は呼ばれた process 上で直ちに `os.execv` するため login で任意実行になるが、
汎用 task は二重 bnode gate により compute でしか子を起動しない。よって一次層の性質は保たれる。
**ただし同決定の「exact path に任意 trampoline を載せない」という文言の射程は本決定が変える。**

**理由:**
- 変異本走を計算ノードの 1 ジョブへ束ねる恒久実装と、任意コマンドを計算ノードへ送る汎用 task は、
  どちらも同じ投入表の話であり、分けると 2 度設計になる。
- 専用の投入 script を足す案は環境正規化を手で写す形になり、生死確認で
  「手で写すと内側の suite が別物になる」ことを実測済みである。既知の失敗モードを作り込む。

**却下した選択肢:**
- 汎用 task を作らない — 後発のユーザー裁定が明示的に追加を決めており、親が不採用にできない。
- 専用の投入 script — 上記のとおり実測済みの失敗モードを再現する。
- 汎用 task に任意の executable path を持たせる registry 化 — `TASKS` を literal source 定義から
  外すと、公表 inventory の drift 検査が静的に成立しなくなる。

## {{D:dispatch-request-bytes-binding}}. 投入 request の bytes を job script の hash へ束縛する

**決定:** 親が canonical request の SHA-256 を job script へ埋め、計算ノード側が実際に読んだ
bytes の hash と照合し、result と受領証へ同じ hash を結ぶ。照合が合わない request では
子を起動しない。公開の `--job-run` 分岐も、束縛の無い request では新規 task を起動しない。

**queue 待ち中の in-flight job を殺さない。** 束縛 marker を持たない既存 envelope は、
`tests` / `provenance` に限り従来どおり受理する。

**理由:**
- 従来は親が書いた request の hash がどこにも束縛されず、queue 待ち中に中身を差し替えても
  親子の task 名照合は両方通り、受領証は元の内容を記録していた。
- 汎用 task では request の差し替えが実行コマンドの差し替えそのものになる。
  汎用 task を足す変更単位でこの穴を開けたままにしない。

**却下した選択肢:**
- 一方向の schema bump — queue 待ち中の job を殺す退行になる。
- 呼び出し側が hash を自己申告する形 — 束縛が job script 由来の証拠にならず、
  受領証の `sha256-job-script` という意味が偽になる。

## {{D:mutation-bundled-path-scope}}. 束ね経路の射程を実測の範囲へ限定し、attempt 証拠の扱いは裁定へ返す

**決定:** 変異 task による束ね経路について、成果物の主張を次へ限定する。

- **queue 回数の削減は条件付きである。** 従来経路は収集 1 + baseline 1 + 変異 N 件 = N+2 回の
  投入を要し、束ね経路は 1 回で済む。ただし削減が成立するのは、変異対象が runner 実行経路
  (`tools/run_tests.py` / `tools/pegasus/dispatch_compute.py`) を含まず、selector を要さず、
  attempt 対応証拠を要さない入力に限る。**「変異本走を 1 ジョブへ束ねた」と無条件に書かない。**
- **attempt 対応の永続証拠は束ね経路では成立しない。** 束ねた job の内側は local 実行になるが、
  wrapper と harness は local と attempt pair の同時指定を無条件に拒否する。
  attempt pair を残すと wrapper が停止し、落とすと attempt 対応を失う。
  したがって本決定が納めるのは「束ねて走る transport」であって
  「attempt 対応証拠を備えた恒久 transport」ではない。
- **共有 lock の移行は task 経路についてだけ閉じる。** 束ね経路は wrapper が共有 lock を持つが、
  harness の直接起動は現行どおり許しており、その経路は共有 lock を通らない。

**この 2 つの未充足を閉じる設計 (task 内部からだけ立つ marker を設け、compute site と marker の
双方が真のときだけ local の attempt recorder を許す形) は、変異 harness の受理集合を変えるため
ユーザー裁定へ返す。**

**理由:**
- 束ね経路が dispatch mode を置き換えられないのは、dispatch mode の存在理由が
  「収集段を変異させられた runner から隔離すること」だからである。束ねた内側は local になるため、
  runner 実行経路を変異させると収集段が自壊する。この性質は変えられない。
- 実測は 1 job で baseline + 変異 1 件を完走することを示したが、その走行は attempt 証拠を持たない。
  持たない走行を「恒久 transport が完成した」と記録すると、証拠契約の水準を偽ることになる。

**却下した選択肢:**
- 束ね経路を既定にして dispatch mode を置き換える — runner 経路の変異が検査不能になる。
- attempt 契約を本 wave で緩める — 変異 harness の受理集合を変える改修であり、
  「変異 harness / runner の契約を変えない」という本 wave の不変条件に触れる。
- 未充足を書かずに「実装した」とだけ記録する — 証拠の水準を偽る。
