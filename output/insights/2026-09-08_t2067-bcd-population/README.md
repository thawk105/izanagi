# [T-2067] (b)(c)(d) — load-only consumer の母集合を今日の main で数え直す

- 日付: 2026-09-08
- branch: `worktree-dev-wave-t2067-bcd-population`
- 着手時の local main: `cc9bba523` (乖離 0)、記録前に `c85f669d9` を ff で取り込み
- 正本: archive worklog `worklog-phase3-0908-1345-1347.md:311` の [T-2067] 本文、D1526、D1503、
  D1370、D1371、D1313、D1241、D65 決定 (5)、および `worklog-phase3-0903-1236.md:333`

## 依頼と結論

依頼は「(b)「load-only consumer 3 群」という母集合の再確定と、それに続く (c)(d)」であり、
「件数を書く前に権威ある閉包を確定する」ことが明示的な条件だった。

結論は 3 つある。

1. **carry の「3 群」は 1202 (2026-09-02) 当時の値で、1236 (2026-09-03) が既に 4 群へ訂正していた。**
   1345 の carry はその訂正前の文面を写しており、(c)(d) も 1236 で閉じたものを未完として再掲していた。
2. **(a) 着地後の今日の未強制は 2 群である。** C06 予算群 (D1371 が不実装と裁定済み) と、
   standalone gate の二読 fallback (`s8b_oracle_driver.py:496`) である。後者は 1236 が
   母集合から外していたもので、本 wave の独立検算でその除外が破れた。
3. **実装面の差分はゼロにした。** `:496` を閉じる案は段 2 が提案したが、DW-G04 / DW-G05 と
   ユーザーの scope 制約により本 wave では実装せず、裁定パッケージとしてユーザーへ返す。

## 母集合 — 9 callsite

批准床値 (`RatifiedFreeze`) を静的 loader (`load_ratified_freeze`) で得る production callsite は
**9 箇所 / 9 関数 / 7 module**。親の AST 走査、段 2 プラン子、段 3 レンズ A の 3 者が
独立に同じ 9 件へ到達した。

| callsite | 関数 | 強制状況 |
|---|---|---|
| `s8b_oracle_manifest.py:1205` | `build_approved_manifest` | `:1206` 狭い選択 API |
| `s8b_oracle_report.py:2547` | `main` | `:2548` 狭い選択 API |
| `s8b_oracle_judge.py:749` | `main` | `:750` 狭い選択 API |
| `s8b_verdict.py:828` | `main` | `:829` 狭い選択 API |
| `s8c_result_judge.py:2076` | `_load_selection_checked_ratified_floor` | `:2078` 狭い選択 API |
| `s8b_oracle_driver.py:644` | `gate_check` | `:664` full launch validation |
| `s8b_oracle_driver.py:1335` | `run_block` | `:1351` full launch validation |
| `p3_autonomous_workload_trial.py:4957` | `run_trial` | **未強制 — C06 予算群** |
| `s8b_oracle_driver.py:496` | `_gate_check_core` | **未強制 — 二読 fallback** |

強制済み 7 (狭い選択 API 5 + launch validation 2)、未強制 2。
`RatifiedFreeze` の構築点は loader 内の 1 箇所だけで、直接構築を禁じる負例が
`orchestrator/tests/test_s8b_ratified_freeze.py:2501` に実在する。

## この数の母集合と、除外したもの

- **母集合:** `orchestrator/**` と `tools/**` の Python 764 file を `ast.parse` し、
  そのうち path に `tests` / `__pycache__` を含まない 399 file を production とした。
- **除外:** test、docs、output、定義・docstring・annotation、loader 自身の構築。
- **射程の限界:** これは「直接呼出しと通常の alias」の inventory であって、
  **全動的 Python 実行の閉包ではない。** `getattr`・`importlib`・`partial`・
  三重引用符内の子 process script・package entry point の各盲点は段 3 レンズ A が
  個別に検査し、対象 API への production 呼出しは 0 件だった。

## 権威ある閉包の在否 — ここが依頼の条件だった

**`load_ratified_freeze` の caller を exact 一致で固定するメタテストは repo に実在しない。**
段 2 とレンズ A が独立に、切らない検索で確認した。したがって 9 件の正本は今回の AST 走査であり、
「repo の権威ある閉包に由来する」とは書けない。

一方、隣接する 3 つには権威ある閉包が実在する。数える対象を 1 つ間違えると、
在るものを無いと書くことになるので併記する。

| 対象 | 閉包の在り処 | 固定内容 |
|---|---|---|
| `build_observations` | `orchestrator/tests/test_s8b_oracle_report.py:5812` | caller は `s8b_oracle_report.main` の 1 本 |
| `_gate_check_validated` | `orchestrator/tests/test_s8b_oracle_driver.py:5517` | caller は `run_block` の 1 本 |
| `verify_manifest` | `orchestrator/tests/test_s8b_oracle_manifest_contract.py:31,99` | production direct caller は exact 4 file |

## 未強制 2 群の帰属

### (1) C06 予算群 — D1371 の裁定が今日も成立する

`p3_autonomous_workload_trial.py:4957` は C06 予算経路で raw `RatifiedFreeze` を読む。
D1371 は「現時点では実装しない」と裁定し、再評価の発火条件を「C05 schedule authority の着地」と
定めていた。**この条件は未成立である。**

- `p3_autonomous_workload_trial.py:2074` の schedule authority resolver は `root` を捨てて
  無条件に `AutonomousTrialError` を送出する。`reserve_all_cells:4964` へ到達しない (レンズ B が確認)。
- [T-2159] (C05) の台帳も「裁定済み (D1567) → 上流待ち」のままである。

よって D1371 の前提 —「gate を置いても変わるのは error の順序だけで、成果物の値・受理集合・
参照は変わらない」— は今日も成立する。本 wave では触らない。

### (2) standalone gate の二読 fallback — 除外が破れた

1236 は `s8b_oracle_driver.py:496` を「private core 内の self-load であり public v2 wrapper は
この形で到達させない」として母集合から外していた。**この除外は成立しない。** ただし到達条件は狭い。

- `gate_check:615` と `_gate_check_core:459` は同じ `_load_verified_freeze` を同じ引数で呼ぶ。
  leaf loader (`s8b_freeze_io.py:41-68`) は file の bytes だけで結果が決まる純関数で、
  両読の間に driver 自身の書き換えは無い (親が実物で確認)。
- したがって発火には「初回 read が失敗し、直後の再 read が成功する」外部要因の状態変化が要る。
  レンズ A が示した具体 trace: `:615` が ENOENT で失敗 → 別 process が active 世代と**完全に同じ
  bytes** をその path へ配置 → `:459` が成功 → `:487` の v2 枝 → `:496` の loader →
  `:503` の sha256 一致で拒否されず → `:589` から allowed を返しうる。公開入口は CLI `main:2055`。
- **受理されうる freeze は active 世代そのものに限られる** (`:503` が sha256 完全一致を要求する)。
  別の freeze が混入する経路ではない。欠けるのは active 世代自身の選択 identity 検査である。
- 公開 signature の `gate_check(ratified=...)` 注入 seam は、production の呼び手が 0 件である
  (唯一の production caller `main:2055` は `freeze_path` / `manifest_path` / `root` しか渡さない)。
  独立した群としては数えない。

## (c) — 元の内容は閉鎖、library 非対称は production 到達 0 件

1236 が閉じた内容 (public builder / writer の private 化) は今日も成立する。
`s8b_oracle_manifest.py:818` 以降の定義は `_build_manifest` / `_build_manifest_from_ratified` /
`_write_manifest` の private 名で、旧 3 名が public attribute として解決できないことを固定する負例
`test_ungated_manifest_apis_are_not_public` が `orchestrator/tests/test_s8b_oracle_manifest.py:1248`
に実在する。

1345 が挙げた library 経路 (`verify_manifest` → `build_observations` / `judge_oracle` /
`verify_oracle_verdict` → `judge_combined`) は、**repo 内の production 到達経路が 0 件**である。
official artifact を生む continuation は 3 CLI だけで、いずれも先に選択強制を通す。

- report: `assert:2548` → `verify_manifest:2553` → `build_observations:2561` → write `:2565`
- judge: `assert:750` → `verify_manifest:753` → `judge_oracle:761`
- verdict: `assert:829` → `verify_manifest:832` → `verify_oracle_verdict:857` → `judge_combined:864`

**閉じていない範囲 (絶対規律 7 に従い明記する):** `verify_manifest` は選択 token を要求しない。
`build_observations` も token を要求せず `reverified_freeze` が optional である。
`_write_approved_manifest` は任意の exact `OfficialManifest` を candidate directory へ保存できる。
これらは「呼び手を新しく書けば通る」形であり、repo 内に production の呼び手が無いという事実だけが
今日それを塞いでいる。ユーザーの scope 制約 (仮想リスク向けの gate・検査の追加は scope 外) により
本 wave では実装しない。

## (d) — 閉鎖を維持

genuine な正例・負例 4 node (`orchestrator/tests/test_s8b_ratified_verify.py:1031/1046/1060/1075`) は
今日も実在し、**stub を使っていない**。実 admission 台帳を設置する helper (`:858` 以降) を通し、
実 `load_ratified_freeze` で取り直し、launch 経路 (`launch_validate`) と consumer 経路
(`assert_g1_floor_selection_identity`) の両方へ通す。各 node 内に monkeypatch は無い。
D1504 が却下した「loader と選択 assert の両方 stub」の形ではない (旧 stub 版 2 本は別 node として併存)。
再実装しない。

## letter の drift — 台帳を読むときの注意

carry の letter は entry ごとに指す内容が変わっている。同じ letter を根拠に「まだ残っている」と
読むと、既に閉じた作業をやり直す。

| letter | 1202 (09-02) | 1236 (09-03) | 1345 (09-08) |
|---|---|---|---|
| (b) | 「3 群」の母集合を再確定する | **4 群で確定**と記録 | 再び「3 群」の文面へ戻る |
| (c) | 旧 public builder / writer の迂回口 | private 化で**完了**と記録 | 別内容 (`verify_manifest` の library 経路) を同じ letter に載せる |
| (d) | 実導出の被覆の穴 | genuine 正負 4 node で**完了**と記録 | 未完として再掲 |

**「1345 が (a) 着地後の再監査を意図して (b) を再開した」可能性は否定できない** (レンズ B の指摘)。
本 wave は意図を断定せず、「数は stale・letter の意味が drift している」とだけ記録する。

## 裁定パッケージ — ユーザーへ返す 1 件

段 2 は `_gate_check_core` の v2 authority を exact `LaunchValidatedFreeze` に限定し、
`:496` の self-load と raw 注入を authority から外すことを推奨した。**本 wave では実装しない。**

不実装の根拠は 3 つある。

- **DW-G04:** 発火条件を満たす既存 artifact path も計測 ID も brief に書けない。同節はこの場合
  「設計メモに留める」と定める。
- **DW-G05:** 放置時に成果物の値・受理集合・参照が安定入力でどう変わるかを示せない。
  示せない must-fix は nit / backlog とする。
- **ユーザーの scope 制約:** 仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
  段 3 レンズ B も独立に同じ判定を出した。段 2 が併せて提案した「初回失敗→二回目成功」の
  regression node は、既存入力の回帰ではなく mock による仮想遷移の新設に当たる。

**ただし新事実がある。** D65 決定 (5) は「public gate_check は v2 で必ず自己検証」と裁定しているが、
この分岐ではその不変条件が成立していない。承認済み裁定に対する新事実なので、DW-S04 に従い
親が不採用で閉じず、択一をユーザーへ返す — (i) 現状維持のまま台帳へ記録する、
(ii) exact `LaunchValidatedFreeze` 必須へ縮めて D65 決定 (5) の不変条件を全分岐で成立させる。
(ii) を採る場合は実装面のため Codex `role=author` と変異事前登録が要る。

## 段 3 の 2 レンズが割れた点と、その裁き方

レンズ A は `:496` を must-fix とし、レンズ B は「安定した production 入力の穴ではない」として
コード変更案の撤回を must-fix とした。**両者の事実認定は一致している** — 到達には二読の状態変化が
要る、という点で同じ。割れたのは「その到達可能性を must-fix と数えるか」だけである。
親は DW-G04 / DW-G05 の基準 (発火条件を artifact path か計測 ID で書けるか、成果物影響を示せるか) で
裁き、実装は不採用、分類の訂正 (母集合へ載せる) は採用とした。

## 変異について

**実装面の差分がゼロのため、DW-S04 により変異 matrix を免除する。** 受入全走は免除していない。

## 子の実走状況

段 2 と段 3 の 3 子はいずれも read-only sandbox のため pytest を実走していない (prompt でその旨を
明示した)。すべて静的検査であり、緑とは申告していない。テストの実測は親が行った。
