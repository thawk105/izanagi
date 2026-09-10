# 段 4 裁定 — [T-235] network 境界で campaign ループを 2 つに割る

- 入力: 段 1 brief (`s1-brief.md`)、段 2 plan (SHA-256 `0fda6705d84f63d2a0ada3b5c048120471c7ed3dad82162e7d90265e611af6e4`)、
  段 3 レンズ A (`795e4b77af4977f9cc04d809e56725b193b2050756c64c4f4a1972921b5676c2`)、
  段 3 レンズ B (`99d5378844dee53eaa3e2f6890d8642184c07a8468777ec03bc4a923b8875b2b`)
- 段 3 の判定: **A = NO-GO (BLOCKER 5)、B = NO-GO (BLOCKER 3)**。両レンズは独立に同じ核心へ到達した
- 逐語は `.codex/dev-wave-network-split-jobs/s3-review-{a,b}/output.md` (job 領域)

## 裁定 (P1 改め): **実装しない。`4→7→8→9` とする**

`campaign` task を `TASKS` へ足す差分は、本 wave では**実装しない**。理由は下の R-1〜R-3 であり、
いずれも親が段 3 の指摘を**自分で実物を読んで確認した**ものだけを採用している。

実装差分が無いため、**変異 matrix と受入全走は本 wave の対象外**である (DW-S04)。
成果物は decisions 1 件・runbook 1 行・worklog・裁定パッケージに限る。

---

## R-1 (BLOCKER・real・採用) — reject / abort が login 側で rc=0 の成功になる

- 由来: レンズ A-1、レンズ B-2 (独立に同一所見へ到達)
- **親による裏取り (実物)**:
  - `orchestrator/campaign/p3_s4_loop.py:827-831` — `ok` は
    `out["stop_reason"] in (...)` と checkpoint の存在だけで決まり、**`out["outcome"]` を見ない**。
    `return 0 if ok else 1`
  - `orchestrator/campaign/p3_s4_loop_trigger_gating.py:582-586` — 同型
    (checkpoint + provenance の存在を足しただけで、やはり `outcome` を見ない)
- **帰結**: `outcome="rejected"` (diff 検疫 reject) や `"aborted"` (build-error を含む) でも
  child rc=0 になる。`dispatch_compute` は child rc をそのまま返し、receipt は
  `{"kind":"child","rc":0}` を保存する。**login 側の supervisor は「拒否された試行」と
  「成功した試行」を rc から区別できない**
- **成果物影響 (DW-G05)**: 試行台帳の dispatch receipt が拒否試行を成功として記録する。
  材料レポートと次 iteration の LLM 入力へ WAL path・構造化 anomaly が戻らない。
  これは **CLAUDE.md 絶対規律 3 (正しさシグナルを後付けにしない。なぜ壊れたかを構造化して次手へ返す)
  が network 境界で片肺になる**ことを意味する
- **なぜ今 blocker か**: 分割前は同一 process / 同一 FS でメインセッションが stdout と WAL を
  直接読めるため実害が出ない。**分割した瞬間に rc が唯一の帰還路になる**ため、この既存の緩さが
  正しさシグナルの欠落へ昇格する。つまり**分割は transport の追加だけでは成立せず、
  domain result 契約 (outcome を rc または構造化 result へ写す層) を必要とする**

## R-2 (BLOCKER・real・採用) — 宣言した `env_allowlist` が子側で強制されない (恒真な保証)

- 由来: レンズ A-3、レンズ B-4
- **親による裏取り (実物)**: `tools/pegasus/dispatch_compute.py:474-481` は `environment` の
  **型だけ**を検査し、`set(environment) <= spec.env_allowlist` を再検査しない。
  その後 `:486-487` で `child_env = os.environ.copy()` → `.update(requested_env)`
- **帰結**: 親側 (`:983-986`) の allowlist 濾過は submit 時点の一度きりで、
  共有 FS 上の `request.json` を後から書き換えれば任意 key が子へ届く。
  したがって `env_allowlist=frozenset()` と宣言しても、**子側にその保証を発火させる検査が無い**
- **なぜ採用するか**: これは `docs/failures.md` が型として持つ「**恒真な保証 (謳うだけで発火しない
  assert)**」そのものである。campaign task を「env を一切渡さない」と称して land すると、
  検査されない宣言を成果物へ焼くことになる。**未知 task は親子二層で拒否されるのに、
  environment の受理集合は二層になっていない**という非対称が実体である
- **射程の訂正**: これは campaign task 固有ではなく、既存 `tests` / `provenance` にも当たる
  **既存の欠陥**である。単発事故なので DW-G03 に従い局所修復が既定であり、族一般化はしない

## R-3 (BLOCKER・real・採用) — 選定 driver が今日 completion しない / 4 役を捨てる

- 由来: レンズ B-1 (PIN)、レンズ A-2 (auditor)、親の段 1 訂正
- **親による裏取り (実物)**:
  - `p3_s4_loop.py:67` `PIN = "028f34d"` ≠ 現行 submodule `d706650`。
    `main()` は flag 分岐前に `assert_pinned_clean` を通るので `--no-build` でも停止する
  - `p3_s4_loop.py:686,699` — `load_proposal_file` は
    `assert_closed_proposal_schema(d, require_auditor=False, ...)` を呼び、返り値は
    `Tuple[PlannerProposal, CoderProposal, Optional[bool]]` = **auditor を optional key として
    受理し、検証も消費もせず捨てる**
  - 対して `p3_s4_loop_trigger_gating.py:421` と `p3_s4_loop_sort.py:267` は
    `require_auditor=True`。**ユーザーが挙げた 4 役 (planner/coder/auditor/critic) に対応するのは
    こちらであり、段 2 plan が初回 driver に選んだ `p3_s4_loop.py` ではない**
- **成果物影響**: plan どおり `p3_s4_loop.py` を指すと、auditor が reject した variant が
  auditor 判定を素通りして build へ進み、certified 集合へ入りうる。
  材料レポートは「4 役を通した proposal」と誤認する
- **B-1 の過大表現を親が訂正**: レンズ B は「全 flag で失敗」は過剰で `--help` は rc=0 と指摘した。
  正しい。機能発火ではないので判定は変わらないが、**親 brief の「どの flag でも起動しない」は
  `--help` を反例として不正確**である

## R-4 (BLOCKER・real・scope 外へ) — 移設先が build identity に束縛されない

- 由来: レンズ A-4
- **親による裏取り**: `pipeline.py:398` の注記どおり、**未指定 caller (p3 loop を含む) は
  legacy `buildcache.build` を通る** (`pipeline.py:476,480`)。legacy `cache_key`
  (`buildcache.py:121-135`) の pre-image は genome / ccbench_commit / trace / src_token /
  cc・cxx の**名前文字列**だけで、**compiler の realpath・version、CMake 版、dependency prefix、
  site、env contract を含まない**。v2 (`_v2_identity:219-234`) は
  `toolchain_manifest_sha256` を持つので同じ穴ではない
- **帰結**: linux-baremetal で作った legacy cache が共有 FS にあると、計算ノードで同じ
  genome/pin/src/compiler 名を使った瞬間に **cache hit して旧 binary を返す**
- **親 brief の誤りを訂正**: brief は「pre-image を変えないから自明に不変」と書いた。**逆である。**
  移設差が pre-image に入らないこと自体が偽 hit の条件であり、レンズ A の反証が正しい
- **scope 外とする理由**: cache identity の拡張は `cache_key` の pre-image を変える =
  既存 cache 全件の無効化と、`s8b_floor_campaign.py` / `s8b_ratified_freeze.py` へ流れる
  provenance の変更を伴う (`DW-O09`/`DW-O10` 発火)。本 wave の scope で扱える規模ではない

## R-5 (real・scope 外へ) — receipt が実行入力の bytes を束縛しない

- 由来: レンズ A-5。queue 待ち中に repo HEAD / driver / `request.json` / proposal が変わっても
  receipt は submit 時の task と args しか持たず、request SHA・repo commit・driver SHA・
  proposal SHA を照合しない
- dispatcher の provenance 強化であり campaign task の前提ではないため scope 外。裁定パッケージへ

## R-6 (real・scope 外へ) — mux に site gate が無い / D105 の task set 記述と衝突する

- 由来: レンズ A-7、レンズ B-5
- **親による裏取り**: `docs/decisions.md` D105 決定 (3) は task 集合を
  **`{"tests", "provenance"}` の閉集合**と明記している。`campaign` を足す差分は
  **D105 を supersede する decision を要する**。段 2 plan はこの docs consumer を挙げていない
- `tools/run_campaign.py` を login から直接呼ぶ entry とするなら
  `hooks/guard_bash.py:161-169` と `orchestrator/tests/test_hooks.py:767` も追随が要る。
  内部 mux に限るなら hooks 差分は不要だが、その場合 **mux 自身が非 compute を拒否する
  site gate を持たねば「sanctioned entry」と呼べない** (レンズ A-7)

## refuted / 減格した所見

- **レンズ B-3 の前半は refuted**: 「dispatch すると単独性確認が login でしか行われない」は成立しない。
  driver は計算ノード上で `_assert_single_tenant` を呼び、bench ごとに `pgrep` する。
  レンズ B 自身が正直に refuted と書いた。**後半 (`ENV_TAG="linux-baremetal"` 固定で
  Pegasus 環境契約に結び付かない) は real** であり B3 として維持する
- **レンズ A-6 は real だが「実装せよ」の根拠にならない**: 今日到達可能な最小 argv
  (`p3_s4_loop_trigger_gating.py --no-build`) は存在する。しかしレンズ A 自身が
  「build/verify/bench をしないので full split の発火証拠にはできない」と書き、
  レンズ B が「checkpoint/provenance を書くので無害な liveness probe でもない」と補強した。
  **non-certifying transport-liveness task に限定して実装する案は設計択一であり、ユーザー裁定へ返す**
- **段 2 plan の file:line ずれ 2 件 (nit)**: `MAX_WALLTIME_S=3600` は `p3_s4_loop.py:80` (plan は `:79`)、
  silo walltime `"02:00:00"` は `policy.json:26-27` (plan は `:22`)。**値と主張は正しい**。
  段 7 で docs へ写す際は plan の記載を使わず親が実物で再照合する (F1)
- **import closure の数値**: 親の「16 module」は AST 走査の対象を 16 file に限った母数であり、
  closure の大きさではない。plan の「import-time 29 / lexical 33」が正しい。
  **結論 (third-party import 0 → `probe_imports=()`) は両者一致**

## 変異事前登録 (DW-M01)

**実装差分が無いため登録しない。** 変異 matrix・受入全走は本 wave の対象外である。
この射程は worklog へ明記する。

## 成果物 (段 7 で親が書く)

1. `docs/decisions.md` — **D106**: network 境界の分割設計、transport の目標形、
   および「実装しない」の射程と発火 gate
2. `docs/pegasus-runbook.md` §8 チェックリスト — 1 bullet
3. `docs/worklog.md` — 本エントリ + 次の一手 (T-235 と派生)
4. 裁定パッケージ (下記) を worklog の「次の一手」へ

## ユーザーへ返す裁定パッケージ

両レンズが独立に同じ二択を提示した。**親は択一を決めず返す** (DW-S04)。

- **択 (a) 契約ごと scope を広げて full 実装する**: domain result 契約 (outcome → rc / 構造化 result)、
  子側 env allowlist 強制、mux の site gate、build identity への site/toolchain/dependency 束縛、
  Pegasus env_tag と calibration、依存 staging、compiler 解決までを 1 つの射程に入れる。
  `DW-O09`/`DW-O10` が発火し、複数 wave になる
- **択 (b) non-certifying transport-liveness task だけ実装し、T-235 本体は未完のまま残す**:
  `p3_s4_loop_trigger_gating.py --no-build` を「certified を作らない liveness 確認」と明示して
  配線する。**ただし checkpoint / provenance を書くので副作用ゼロではない** (レンズ B)
- **択 (c) 本 wave の裁定どおり docs だけ land し、実装は blocker 解消後の別 wave にする** (親の推奨)

**親の推奨は (c)。** 理由: R-1 が示すとおり、分割は transport の追加ではなく
**domain result 契約の新設**であり、それ無しに配線だけ land すると
絶対規律 3 が network 境界で片肺になったまま「分割済み」と記録されてしまう。
R-4 の cache 偽 hit も、実装より先にユーザー裁定が要る研究状態の問題である。

## 独立に確定した条件 dispatch の判定

- `DW-O09` / `DW-O10`: **本 wave では発火しない** (`buildcache` を触らないため
  `configure_argv` が変わらない)。R-4 の恒久対応では発火する
- `DW-O13`: gate 新設なし (実装しないため)
- `DW-O11` / `DW-O14` / `DW-O19`: 該当なし
- `DW-O17` (commit trailer) / `DW-O20` (clean-tree gate) / `DW-O23` (local main): 段 7〜9 で適用
