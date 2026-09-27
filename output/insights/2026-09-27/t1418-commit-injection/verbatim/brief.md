# 段 1 brief — [T-1418] 変異 harness の閉包 member 変異経路 (2026-09-27 JST、base ad114fba0)

## 研究前進
CC 合成ループの正しさ gate を持つ file (loop.py・pipeline.py・p3_s4_loop.py・wal.py・ident.py・verifier/* など、
campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS の 96 path) を変える wave の変異 matrix が、現状は contract-loader-drift
(disk≠HEAD blob) に覆われて「値の層が見えない KILLED」になる。実例: T-2850 の M8 (p3_s4_loop.py) は final で drift 139 node の一致で
KILLED、commit 注入で狙いの test を走らせると 2 passed = 生存 (memory mutation-discipline 補足 2026-09-26)。各 wave は DW-M05 同等検査を
毎回事前登録した自作 commit harness (T-2632 run-commit-group.sh、T-2849、T-2850) で回避している。
完了判定: `tools/mutation_harness.py` の opt-in モードで閉包 member の変異を「変異を commit した detached HEAD」で走らせ、
(a) 閉包 member のコメント変異 (等価) が drift で落ちず SURVIVED、(b) 同 file の値変異が所有 test だけで KILLED、を実 dispatch で示す。

## scope
- harness 側に「変異を commit した木で runner を走らせる」経路を足す。既定の file-swap は不変。
- 必要なら wrapper (tools/mutation_worktree.py、tools/mutation_fanout.py) の引数中継だけ。
- docs: decisions / failures (F424 の恒久対応追記) は spool fragment。dev-wave mutation.md への 1 文は予算を見て段 4 で裁定。
- scope 外: T-458・T-626 (D2172 項 10 の相乗り指定) はユーザー指示「本題の実装だけ」により相乗りしない。仮想リスク向け gate・検査・台帳・一般化も足さない。

## 確定済み裁定・既存資料
- D1712: 「変異中だけ contract loader 束縛を無効化」は規律 2 違反で却下済み。
- `ratified_enforcement_source` fixture は b4ff38f6b (2026-08-27) で no-op 化済み。F424 の根本原因の記述は古い。現行の drift 源は
  orchestrator/campaign/ident.py (_capture_current_loader_binding / verify_against_lock) → contract_loader_binding.capture_contract_loader_binding
  (現 HEAD の 96 path blob と disk bytes の一致)。HEAD 以外に束縛された層は現存しない (調査子の報告、段 2 で再確認)。
- dispatch (tools/pegasus/dispatch_compute.py) は request に repo_root の path 文字列を入れ、計算ノードが同じ path へ cd して走るだけ。commit/tree の snapshot は送らない。
- git hook は未設定 (core.hooksPath なし、hooks dir は sample のみ)。

## 親の provisional 裁定 (攻撃対象)
- (P1) 変更は harness 側。fixture / ident / contract_loader_binding / campaign_lock は 1 byte も変えない (D1712)。
- (P2) commit モードは repo の HEAD が detached のときだけ動き、branch ref を一切動かさない (on-branch は起動前 fail-closed)。
  置き場は mutation_worktree.py の使い捨て detached 木か、DW-M07 の独立 clone を detach したもの。
- (P3) 1 変異 = 固定 HEAD H から: 注入 → 既存検査 → `git -c user.name=… -c user.email=… commit` (touched file だけ) → 変異 commit M の親 == H・
  `git diff --name-only H M` == touched 集合・作業木 clean を検査 → runner → HEAD を H へ戻し bytes を HEAD blob と照合 (既存 _verify_originals) → HEAD == H。
  signal・例外でも HEAD を H へ戻す (既存 _defer_cleanup_signals の内側)。
- (P4) ledger に注入モードと変異ごとの M の sha を記録し、--resume はモード一致を束縛する。schema 版の要否は段 2 で既存 reader を見て決める。
- (P5) baseline は H のまま (commit しない)。commit モード固有の mask (HEAD commit の metadata を読む test 等) は、等価変異の対照で測る (DW-M03 の作法)。
- (P6) dispatch の orphan hold (rc=16) 時の HEAD の扱いは既存 hold 契約を壊さない形を段 2 で起草させる。

## 不変条件
- 閉包 drift 検査を弱めない。規律 2 を緩めない。既存テストの期待値を変えない。
- 既定モード (file-swap) の挙動・ledger は bytes 互換。DW-M05 の保証 (固定 HEAD 束縛・起動/復元時の内容比較・flock・逐次 flush・HEAD/spec 束縛 resume・signal 復元) を commit モードでも保つ。
- 変異 commit は canonical history・branch へ残さない。

## 成果物
- tools/mutation_harness.py の opt-in モード + orchestrator/tests/test_mutation_harness.py の test (必要なら wrapper 中継と test)。
- 実 dispatch の dogfood 2 本 (完了判定 (a)(b))、変異 matrix (本 wave の harness 変更自体への変異)、受入全走。
- insight・decisions/failures fragment・worklog fragment。

## 分割方針・子の数
- 実装単位は 1 (harness + test、wrapper 中継は同単位)。所有が一枚岩のため並列分割しない。
- 軽量版ではなく段 2 plan 1 本 + 段 3 相談 2 本 + 段 6 review 2 本: harness は正しさ gate の歯を示す計器で、誤った KILLED/SURVIVED を
  出す改変は成果物 (変異台帳) の値を変えるため (DW-C00「正しさ防壁に触る」に当たると判断)。

## 受入・実測環境
- Pegasus login node + `tools/run_tests.py --force-dispatch` (計算ノード)。受入は `tools/dev_wave_wait.py acceptance`。
- 成果物影響 (DW-G05): 放置すると閉包 member を変える wave の変異台帳で、値の層を検査していない KILLED が正しさ gate の歯の証拠として数えられ続ける (T-2850 M8 は実例)。
