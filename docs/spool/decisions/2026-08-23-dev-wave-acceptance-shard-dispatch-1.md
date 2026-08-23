---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-23
wave: dev-wave-acceptance-shard-dispatch
seq: 1
---

## {{D:acceptance-shard-dispatch-optin}}. 受入全走の shard 分割は runner の内側に置き、既定無効の opt-in にする

**決定:** 受入全走を K 個の shard へ分けて計算ノードへ同時投入する経路を
`tools/run_tests.py` の**内側**へ置く。`IZANAGI_ACCEPTANCE_SHARDS` が `2` または `3` の
ときだけ有効になり、unset / 空 / `1` は従来どおりの単一走である。**既定は無効のままとする。**

有効化には受入形・`PYTEST_ADDOPTS` と `PYTEST_PLUGINS` が空・site が Pegasus LOGIN・
positional target が空か `--force-dispatch` だけ・裁定済み恒久除外表が gate を通る、
の全成立を要求する。条件不一致は K=1 へ黙って丸めず rc=16 で止める。

**理由:**
- 受入 command は `tools/dev_wave_land.py` が argv 完全一致で pin しており、
  呼び手側で分割を指示する余地がない。runner の内側が唯一の seam である。
- 実測で **テスト実行そのものは縮む**。同一 tip・受入形で、単一走の pytest wall
  157.43〜187.35 秒に対し、K=2 の最遅 shard は 134.13〜138.57 秒だった。
- しかし **総所要は queue の空き次第で、混雑時は分割が不利**である。実測で
  外側 wall は K=1 が 218 / 326 秒、K=2 が 476 秒、K=3 が 291 秒だった。
  毎回どれか 1 本だけが 157〜330 秒の queue 待ちを引き、最遅 shard が全体を決める。
  K 本ぶんの空きが同時に要ることが新しい費用である。
- したがって「常に速くなる機構」ではない。**空きがある時間帯に運用者が選ぶ道具**として置く。
- **K=3 は K=2 より速くならない。** K=3 の最遅 shard は 143.92 秒で K=2 の 138.57 秒を下回らない。
  排他鎖 103.0 秒 + 固定費 12.86 秒の床に当たっている。K を上げても床は動かない。

**却下した選択肢:**
- 既定を K=2 にする — 混雑時に不利で、queue 待ちの分布を運用者しか判断できない。
- 呼び手の argv や環境で分割を指示する — land の受理条件を変えることになる。
- K の上限を 4 以上へ広げる — 床が動かないのに request 数・queue skew・故障面だけ増える。

## {{D:acceptance-shard-exact-preservation}}. 分割の正しさは「全 shard 同一 collection + 決定的再導出 + 6 段 gate」で守り、manifest と barrier を持たない

**決定:** shard は pytest の positional target を常に既定 suite root のままにし、
**各 shard が同一の全 collection を行ってから担当外を deselect する。**
割付けは collection 結果から**決定的に再導出**する。共有 manifest file も、
shard 0 が collection して他が待つ barrier も持たない。

併合は次の 6 段を**その順で**満たしたときだけ rc を確定する。

1. report index が `set(range(K))` と完全一致
2. 全 shard の `observed_universe` が互いに完全一致 (これを `U` とする)
3. login 側が独立に走らせた `--collect-only` の集合が `U` と一致
4. `Σ selected_i == U`、各 count = 1、file と `xdist_group` の閉包が保たれている
5. 全 shard で `finished_i == selected_i`
6. 全 shard の effective scheduler が `loadgroup` / `serial` で一致

gate の前に、report の診断 payload (worker 占有・group 割付け・collection digest・
JUnit path・terminal 件数) を実データから再計算して照合する。
**gate 通過前に緑 summary・scheduler marker・task-run record を確定せず、
gate 失敗後に単一走へ fallback しない。**

**理由:**
- **file を positional target へ渡す形は使えない。** 実測で `sys.path` の確立が
  `orchestrator/tests` 指定時と変わり、`test_s8b_approved.py` の `from tests.skiputil import` と
  `test_profiler_directive.py` の `from codex_roles import policy` が
  `ModuleNotFoundError` になった。単一走では両方緑である。
- **authoritative な集合を 1 か所の manifest に置くと自己証明になる。** 敵対相談が、
  collection plugin が singleton file を 1 件落とせば割付け・deselect・併合が
  すべて同じ縮小集合に同意して緑になる経路を構成した。
  gate 2 と gate 3 の二重化はこれを断つためである。
- 固定費が実測 12.86 秒 (48 worker 起動 + 全 collection + 集約、テスト 0 件) しかないので、
  全 collection を K 回払っても費用はほぼ増えない。barrier を置くほうが臨界路に直列区間を足す。
- 実測で全 session が `selected == finished`、shard の和が collection 14479 と厳密一致、
  `14383 passed / 96 skipped`、marker ちょうど 1 本、rc=0 だった。
- 変異 8 件 (各 gate の恒真化、両層同時、過剰拒否の正例) がすべて KILLED である。

**却下した選択肢:**
- 共有 manifest + barrier — 自己証明を作り、臨界路に直列区間を足す。
- 記録された割付けを信用する — 偽の割付けを report へ書けば通る。親が再導出する。
- 受入 receipt へ shard 情報を足して land で検査する — 3 tool の受理条件を変える
  変更であり独立の裁定が要る。本 wave では実装しない。**したがって gate は runner の内側にあり、
  receipt は shard の完全性を証明しない。**

## {{D:artifact-root-outside-control-container}}. 成果物の置き場は「別機構が所有を仮定している場所」を fail-closed で避ける

**決定:** shard の artifact 置き場は、対象 repo の外であることに加えて
**`tools/dev_wave_land.py` の `_CONTROL_CONTAINERS` (`.claude/worktrees`、`.codex/worktrees`) の
直下・配下でないこと**を要求し、違反すれば `ShardError` で停止する。
guard は land の定数を **import して参照**し、複製しない。
置き場の導出は `git rev-parse --path-format=absolute --git-common-dir` から
main repository root を求め、その parent とする。

**理由:**
- 「repo の外」だけを条件にすると、repo が git worktree のとき `repo.parent` が
  ちょうど `.claude/worktrees/` になる。land はそこの子を**すべて git worktree と見なして**
  `.git` の実在を要求するため、`.git` を持たない artifact directory を置くと
  **同じ checkout の全 wave の land が rc=21 で止まる。** 並行 wave の land が実際に拒否された。
- 置き場の導出は将来また変わりうるが、
  **「別機構が所有を仮定している場所へ書かない」という不変条件は変わらない。**
  だから guard を第一級にして導出をその下に置く。
- 定数を複製すると、container が 3 つ目に増えた日に片方だけ古くなる。
  import して参照し、将来値でも guard が発火するテストを置く。

**却下した選択肢:**
- `_CONTROL_CONTAINERS` を複製する — 同期が切れる。
- `/tmp` を使う — 計算ノード間で共有される保証がない。
- 置き場の導出だけ直して guard を足さない — 導出が変わったとき同じ事故が再発する。

## {{D:acceptance-cost-four-layers}}. 受入の所要は 4 層に分けて計上し、`直列総和 / (48K)` を下界と呼ばない

**決定:** 受入の所要を論じるときは **queue 待ち / job Elapse / pytest wall / 外側 wall** の
4 層を別々に記録する。`直列総和 / (48 x K)` は下界ではなく
**「K=1 の duration を固定した仮想 capacity 指標」**と呼ぶ。
排他鎖の長さと最長単体の値も、将来走の硬い床ではなく当該走の観測値として扱う。

**理由:**
- junit の duration は共走の競合を含む (D531)。K を変えると duration 自体が変わるので、
  ある K の観測から別の K の下界を導けない。
- 3 層を混ぜると誤診する。同一 tip・同一テスト集合でも pytest wall は 157.43〜187.35 秒、
  外側 wall は 218〜476 秒とばらつき、差の大半は queue 待ちである。
- **測定のために受入形を外すと、受入形だけに効く gate も同時に外れる。**
  `--junit-xml` を足すと `_is_acceptance_run` が偽になり恒久除外が適用されず、
  除外表の破れと誤診しかけた。あわせて 2.3 MB の XML 出力自体が wall を押し上げる
  (受入形でない測定 229.41 秒 対 受入形 157.43〜187.35 秒)。
- **単発 probe の値を全走への寄与として読み替えない。** ある関数の cold 実測 329.75 秒が
  「直列総和の約 6%」と読まれかけたが、全走 junit では当該 module 全 367 件の合計が 74.0 秒、
  最長単体 22.77 秒であり、330 秒級の単体は 1 件も存在しなかった。
