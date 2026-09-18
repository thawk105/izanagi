# 段 1 brief — [T-2686] 救出検査の子 `tools/check_branch_landed.py` の律速を同一判定のまま下げる

wave `dev-wave-t2686-exact-state-union-walk` / branch `worktree-dev-wave-t2686-exact-state-union-walk` / base local main `1809e6663` / 2026-09-18 15:20 JST / 受入・実測環境: login node pegasus02 (道具の実運用場所。受入全走は `tools/dev_wave_wait.py acceptance` で計算ノード)。

## 研究前進 (土台)
掃除 (`/cleanup-branches`) の救出検査 `check_branch_rescue.py` は子 `check_branch_landed.py` を commit ごとに既定予算 8 秒で起動し、本 repo の規模では `checker-timeout` が残る (entry 1542、7 件中 3 件)。止めている研究: 削除で失われる commit の可視化 (D1231/D2055) が「見終えていない」で止まり、未証明理由が人へ届かない。最小差分: 子の unit ごとの全履歴走査を 1 走査へ束ねる。完了判定: 固定 OID `559bcbc29cfa27412f103b608e8ac708dcfae6b9` で (i) 候補列が全 path 一致、(ii) payload の判定・unit・evidence・summary が timing 系 field (`elapsed_seconds`、`timing.*`) 以外で byte 一致、(iii) git 子 process 数が減る (現行 244)、(iv) 同時刻交互 A/B (旧/新/旧/新) で wall が短い。checker-timeout の解消は完了判定にしない (Lustre の 1 走査 4〜25 秒 > 予算 8 秒の日がある)。

## 実測で覆した依頼の前提 (段 4 で再裁定)
- 依頼文の file 名 `tools/audit_dangling_commits.py` は誤り。closure 列挙 `_enumerate_closure` と `_introduced_states` は `tools/check_branch_landed.py` にある。
- 現行 main で closure 列挙 1.4〜1.5 秒、`_introduced_states` 0.6〜0.75 秒 (diff-tree 10 本)。「残り約 16 秒」は entry 1542 の差し引き推定で、実測は約 2 秒。
- 真の律速は exact-tree-state 層 `_find_exact_state` の unit ごとの `git log --full-history --format=%H --max-count=1025 <main> -- <path>`。全 41 unit 走 (予算 900 秒、load 40): 総所要 372 秒中 `_find_exact_state` 267 秒、`git log` 57 本 323 秒。判定は 09-16 と同じ `indeterminate / one-or-more-states-unproven`。D2106 も「unit 数 × path log の合計が律速」と記録済み。
- 1 本の `git log` は CPU 0.35 秒・実時間 4〜25 秒 (Lustre: loose object 1273 個の open + pack の page fault 待ち)。分散が大きいので前後比較は同時刻交互 + 決定的な process 数で示す。
- T-2691 は未 land・別 wave が起動中。対象は親側 `check_branch_rescue.py`、本 wave は子側 → 「同 file」は不成立。

## scope (実アンカー)
- `tools/check_branch_landed.py`
  - `_find_exact_state` (767〜): `git.run(["log","--full-history","--format=%H",f"--max-count={limit+1}", main_oid,"--",path])` を、assess 内で 1 回だけ走る union 走査から派生した per-path 候補列 (memo) に置き換える。tip 一致の早期 return、`_batch_check_path_candidates`、`_tree_entry` 再確認、`SearchResult` の outcome/reason/candidate_count/candidate_limit は不変。
  - union 走査: `git -c log.showRoot=true log --full-history --diff-merges=separate --name-only -z --format=%x1e%H <main> -- <非 spool の distinct path…> (+ spool fallback が要る path)`。派生規則: 走査順を保ち、commit c は path p の候補 ⇔ c のいずれかの親 entry の name に p が literal pathspec 一致 (name == p または name が `p/` で始まる); 上限 limit+1 で切る。
  - `assess` (1680〜): proof 段で union 走査を 1 回行い `_proof_unit` へ渡す (`_proof_unit` の signature に候補供給を足す)。spool unit の exact fallback (`_find_exact_state` 2 回目呼び出し) も同じ供給を使う。
  - `SearchResult.elapsed_seconds` は per-unit の照合時間に、union 走査の秒数と process 数は `timing` へ別記 (情報 field)。
- `orchestrator/tests/test_check_branch_landed.py`: 合成 repo で正例 (派生列 == per-path 列: 通常 commit、片親だけで変わる merge、両親で変わる merge、root commit に在る path、削除→再追加、file→directory、gitlink、上限 limit+1 超) と負例 (派生規則を壊す変異で赤)。既存 test の期待値は変えない。
- insight `output/insights/2026-09-18/t2686-exact-state-union-walk/` (計時・一致検証・逐語)。

## scope 外
並列化、予算 (rescue 8 秒 / 全体 60 秒 / per-command 45 秒) の変更、any-path `--find-object`、`cherry`、ledger probe、closure/`_introduced_states` の一括化 (実測 2 秒で収益なし)、rescue 親、T-2691、raw diff の new side を ls-tree 再確認の代替にすること (証拠の出所を変える)。

## provisional 裁定 (攻撃対象)
- (P1) 依頼が名指した closure/`_introduced_states` は律速でない。scope を同 file の実測律速 `_find_exact_state` へ移す。「同じ判定のまま所要を下げる局所改善」「検査範囲を削らない」の制約は不変。
- (P2) T-2691 の land を待たない (別 file・未着手)。land 前に main を再取り込みし衝突は `DW-O23` で扱う。
- (P3) union 走査は受理集合に触れない。D2106 が却下した `--first-parent` は候補を落とすが、本案は候補列 (集合・順序・上限の切り方) が完全一致 — 実 repo 33/33 path で実測 (union 30.9 秒 vs per-path 合計 195.6 秒)。D2142 (同日) の「同じ規則のまま少数 process へ再構成」と同型。
- (P4) 派生規則の根拠: `--full-history` (parent rewriting なし) は merge を「いずれかの親に対して path が変わる」とき含める (実測: 4a614a49 は親 1 側だけで変わり per-path 走査に含まれた)。`--diff-merges=separate` は差分の無い親 entry を省くので「いずれかの entry に在る」= ∃親。走査順は pathspec に依らない (全親を辿るのは --full-history の定義)。root は `log.showRoot=true` で名前を出す。
- (P5) union 走査 1 本が per-command 上限 45 秒を超えると proof 段全体が `assessment-timeout` (indeterminate) になる。現行も unit 合計が全体予算 60 秒を超え同じ verdict に落ちるので受理集合は変わらない。
- (P6) `SearchResult.elapsed_seconds` の意味が「候補列挙を含む」→「照合のみ」に変わる (情報 field、verdict 非依存)。

## 不変条件
判定 3 値と受理述語 (D922 項 2・4、D2123)、rc、`indeterminate` への倒し方、evidence layer 名と構造、候補上限 (`--max-count=limit+1` と `> limit` で truncated)、`GIT_LITERAL_PATHSPECS=1`、実装面は Codex author (親は直接編集しない)、probe は repo に入れない、規律 2 (正しさゲート) を緩めない。

## 成果物
実装 commit (check_branch_landed.py + test)、insight dir、worklog / decisions fragment (D: 採用理由・却下案・前後計時)、変異 matrix (baseline 緑・派生規則の各条件を壊す変異が全 KILLED)。

## 分割
段 2 plan 1 (read-only codex)。段 3 consult 2 並列: レンズ A = git 意味論の同一性 (包含規則・順序・上限・pathspec 一致・root・gitlink・-m が walk を変えないか)、レンズ B = 予算/timeout/deadline・evidence field・process 数契約・test の正例負例・D2106/D922 との整合。段 5 author 1。段 6 review 2 並列 (同じ 2 レンズ) + fix。
