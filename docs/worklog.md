# Izanagi 作業ログ (worklog)

セッションごとの進捗を時系列で記録する。git 履歴や各正本に入らない協議・異常・持ち越しを束ねる
「作業の索引」であり、commit 内容の再説明はしない。役割分担:

- 設計判断と却下案 → `docs/decisions.md`
- CCBench の構造的事実 → `docs/ccbench-anatomy.md`
- CCBench のバグ等の知見 → `output/insights/`
- タスク分解 → `docs/phaseN.md`
- **このファイル = それらを束ねる日誌 (各セッションの索引)**

## 新規エントリの書式 (D35)

過去エントリは凍結し、次の規約は新規エントリに適用する。

- 本文化するのは、ユーザー承認・協議の決着、棄却 finding (refuted)、未コミット事象・セッション異常と
  救出、エージェント工数、人間判断待ち・持ち越し、次の一手など **git に入り得ない情報だけ**
- commit は「hash + 件名 (+ 位置づけ 1 行)」まで。連続群は「先頭..末尾 (N 本)」で表し、内容を再掲しない
- 監査の finding 全文と裁定は insight / audit JSON に凍結する。worklog はレンズ数、real/refuted 数、
  最重要 1〜3 件、一次資料ポインタの 10〜15 行に留める
- 論文素材になる段落は行頭に「素材:」を付ける。持ち越しは逐語再掲せず「変わらず (前エントリ参照)」
  とする
- docs(worklog) だけの commit は prose の body を付けず、件名 + 必須 trailer だけにする

### 次の一手の ID 規約 (D70)

「次の一手」の項目が黙って落ちる経路を塞ぐため、各項目に安定 ID を付け、`tools/check_docs.py` が
保存則を機械検査する。ID は角括弧で囲んだ `T-` + 連番で、**表記は 1 つに正規化する** —
1〜999 は 3 桁ゼロ埋め、1000 以上は先頭ゼロなしで書く。冗長なゼロ埋め (4 桁で 1 を表す等) は
同じ数値の二表記になるため**不正形式として赤にする**。

- **位置**: トップレベル list item (インデント無しの `1. ` または `- `) の**先頭**に置く。
  インデントされた子項目は原子として扱わない — **1 原子 = 1 トップレベル項目 = 1 ID** に平坦化する
  (子項目 `(a)(b)(c)` に原子を詰めると、その分は機械検査の網から外れる)
- **採番**: 現行 worklog (「ローテーション」節より後) + `docs/archive/worklog-*.md` + 見送り台帳に
  現存する有効 ID の最大値 + 1。並行セッションは番号を予約したとみなさず、統合直前に再走査して
  未統合側を振り直す (`landed` = main へ統合された時点)
- **不変性**: 一度 land した ID は変更・再利用しない
- **保存則 (機械検査)**: あるエントリの「次の一手」に現れた ID は、後続エントリのトップレベル項目
  (消化または継続) か、見送り台帳のトップレベル項目 (理由付き見送り) に現れなければ赤になる。
  ローテーション境界 (アーカイブ最新の末尾エントリ → 現行の先頭エントリ) も検査対象
- **この節と決定記録には有効 ID を書かない** (採番母集団と sink の自己汚染を避けるため、
  例示は `T-NNN` のようなプレースホルダで書く)

## ローテーション

Phase 境界または現行ファイルの肥大時 (`tools/check_docs.py` の閾値超過が
知らせる) に、過去分を `docs/archive/worklog-<範囲>.md` へ**移動**し、現行ファイルを軽く保つ
(ブート時に読むのは末尾エントリのみ、の運用を軽く保つため。2026-07-05 導入、D35)。
アーカイブは凍結 (訂正注記のみ追記可)。既存アーカイブの一覧は `docs/archive/README.md`。

---
## 2026-07-28 (33) — [T-088] 段階 1 を実機で閉じた — 初走 rc=1 の環境乖離を interpreter 版数 gate で修正し、再走で official guard の実機拒否 rc=2 を確認 (コード + docs、branch worktree-dev-wave-t088-python-gate、計測 = Pegasus job 873200/873213/873225 の rc・attempt artifact と受入全走の rc)

- **段階 1 の完了条件が成立**: job `0:873225.nqsv` (bnode002) が `driver_rc=2` +
  `failure.json.stage="floor_driver"` + driver stdout の明示 refused JSON を記録。**rc=2 は
  official guard 生存の正常 failure であり「ジョブ失敗」ではない。** D87(1) が OPEN 条件とした
  実 submit artifact ID を DW-G04 として充足。official の受理集合は空のまま (driver は 1 byte も
  変更していない)
- **初走 `0:873200.nqsv` (bnode018) は rc=1・guard 未到達**: 計算ノードは module
  intelpython/2022.3.1 既定ロードで python3 = 3.9.13、driver は import 段の `dataclass kw_only`
  (3.10+) TypeError で死んだ。事前の rc=2 実測はログインノード 3.10.12 のもの (材料レポート
  §5-6 の限界が実体化)。**F46 として台帳化** — python3.version を「記録するが assert しない」
  値にしたことが死角。fix = 候補列 (`python3` → `python3.10` → `python3.11` → `python3.12`) +
  実行前版数 gate、全滅で `stage=interpreter` fail-closed (commit `419d59b`)。再走の
  `python3.realpath` = `/usr/bin/python3.10` で gate の fallback 動作も実機確認
- **セッション内 shell (`!`) からの submit は無効だった** (request 873213): qsub は ID を返した
  が receipt が実 FS に不永続、qstat は Not permitted、attempt dir・spool・課金なし。**F47 として
  台帳化**し、runbook §8 に「投入はユーザー自身の端末から」を追記。D86(8) (認可の実体 = 明示
  指示) は不変で、実行環境の定義を足す材料
- 検査: 焦点 = `test_pegasus_floor_tools.py` **52 passed** (新規 3 = gate 拒否の記録 / 版付き名
  fallback / 第一候補優先、既存 2 本を新構造へ追随)。受入全走 = **3136 passed / 18 skipped /
  赤 0** (51.5 秒、worktree `dev-wave-t088-python-gate`、`external/ccbench` submodule 初期化後)。
  `check_docs` 違反なし、`check_ai_provenance` 442 件違反なし
- **worktree の submodule 未初期化で偽赤 42 本を実測** (known-axes freeze 系: `ccbench_current`
  照合が実体不在で refused)。差分が到達し得ないファイルの赤だったため DW-O18 に従い環境要因を
  先に実測し、`git submodule update --init external/ccbench` で全緑。機械化を [T-158] に起票
- 変異: 軽量版のため変異本走なし (実装差分は shell の interpreter 選択のみで、既存変異台帳の
  対象層に差分なし)。gate の生死は新規テスト 3 本が直接束縛する (gate 撤去 → 拒否記録テストが
  赤、候補順入替 → 第一候補優先テストが赤)
- 課金の実測: 873200 = Elapse 25S ≈ 0.01 pt (434.72 → 434.71)、873225 = 実行 12 秒、873213 = 0。
  課金は要求 walltime (36000 秒) でなく実使用ベースであることを残高差分で確認
- **裁定パッケージ (段階 3 の入力、実装しない)**: (1) D86(3) の文言 vs 実体は **D86(8) erratum
  (2026-07-25、[T-095]) で既決着** — 残る裁定は「明示 qsub の実行環境をユーザー端末に限る」旨を
  D86(8) へ追補するか (材料 = F47)。(2) driver 予算定数の hard cap 化 — 独立 prerequisite wave で
  driver 側を直すか、walltime 厚取り (36000、余裕 7200 秒) を恒久方針とするかの択一。(3) 実行
  revision 束縛と spool bytes の独立照合 — 段階 3 (単一 admission predicate) の設計 scope に
  含めるかの確認。材料 = `output/insights/2026-07-25_t088-floor-wrapper.md` §7 + §9
- commit: `419d59b` (gate + テスト + runbook §4)。docs (本エントリ + insight §9 + F46/F47 +
  runbook §8 + §4 の実測確定) = 本エントリと同 commit
- エージェント工数: 子なし (軽量版、親直接。DW-C00 の子起動条件 — 設計択一・防壁変更・受理集合
  変更 — に非該当。gate は受理集合を「3.10 未満の interpreter を拒否する」方向へ狭めるだけで、
  admission・digest の受理集合には触れない)
- ユーザー手番: push (AI からは行わない)
- 段 8 自己改善: dev-wave prose への追記なし (T-127 裁定「prose よりテスト/機械検査」に従い、
  恒久対応は F46/F47 + runbook + [T-158] の機械化起票へ routing)

### 次の一手

**優先度ラベルは (25) から継続** (P1 = 本サイクル、P2 = P1 の後、P3 = 裁定・条件成立まで保留)。

1. [T-157] **P1・新規 (identity の誤参照、本 wave scope 外の real 所見)**: `p3_s4_loop._resolve_duplicate`
   が `with applied(...)` の外・`ccbench_dir` 引数なしで `source_digest.resolve()` を呼ぶため、patch を
   revert した共有 tree の **stock** id を引く (`p3_s4_loop_sort` / `p3_s4_loop_trigger_gating` も同型)。
   重複提案の解決が別 variant の WAL を参照し、whiteboard・trigger provenance・checkpoint・critic
   digest に誤った variant 参照が永続化する。材料 = `output/insights/2026-07-28_t148-macro-context.md` §5
2. [T-139] **P1 (外部相談、独立到達)**: 劣化版 Silo の梯子。**[T-140] 択 (c) の移し先**。変わらず
3. [T-142] **P1 (裁定 (3))**: テストの価値による二層化。変わらず
4. [T-136] **P1 (実害・受入判定を汚す)**: `dev-waves-integration` の timing 依存フレーク。変わらず
5. [T-129] **P1 (F41 の残り)**: 全走の作法の明文化。作法本文 (runbook 側) が残り。変わらず
6. [T-149] **P2・ドリフト**: 編集面の独立 hard-code 4 箇所。本 wave が足した `_PROTOCOL_CMAKE`
   (protocol → CMakeLists パス) も同族として数える
7. [T-152] **P2 (どの軸でも効く死角)**: trace 生成と lock 被覆検査の同一 container 再走査。変わらず
8. [T-153] **P2 (T-127 の機械化群)**: (a) run_tests cwd 強制 (b) 未 stage 削除検出 (c) O20
   スクリプト化 (d) F43 検収機械化 (e) CAB 連続配置 (裁定 (3) 条件付き)。変わらず
9. [T-158] **P2・新規 (T-153 の族)**: worktree の `external/ccbench` submodule 未初期化で
   known-axes freeze 系 42 本が偽赤になる (2026-07-28 (33) で実測)。`tools/run_tests.py` に
   submodule 実体検査 (fail-fast または自動 init) を足して機械化する
10. [T-141] **P2 (一部完了)**: profiler → axis-proposer 結線の残り。変わらず
11. [T-143] **P2 (裁定 (4))**: RuleOps。変わらず
12. [T-126] **P2 (裁定済み = 採用)**: 逐次停止 設計 v2 の実装。変わらず
13. [T-145] **P2 (レビュー B-2、nit)**: `join(30)` の二律背反。変わらず
14. [T-146] **P2 (レビュー B-3、nit)**: capability probe の cleanup の fault injection 経路。変わらず
15. [T-134] **P2 (衛生)**: 並列度の再最適化。変わらず
16. [T-123] **P2 (衛生)**: `daemon.py` の `_atomic_json` はデッドコード。変わらず
17. [T-118] **P2 (衛生)**: `/dev/shm` の残留 temp dir。変わらず
18. [T-109] **P2 (裁定完了)**: `/dev-wave クロスプロトコル対応`。変わらず
19. [T-113] **P2 (裁定済み)**: root-isolation 変異の control を新設する。変わらず
20. [T-110] **P2 (裁定済み)**: 受理集合を変える改修の手続義務を規約化する。変わらず
21. [T-097] **P2 (裁定済み)**: 変異台帳 JSON を placeholder 検出の対象族へ足す。変わらず
22. [T-100] **P2 (裁定済み)**: 検出語彙へ表記ゆれ・HTML entity を足す。変わらず
23. [T-099] **P2 (裁定済み)**: 凍結成果物の placeholder は止める仕様を明記する。変わらず
24. [T-009] **P2**: dev-wave 実装子の規律の所在を AGENTS.md へ明文化する。変わらず
25. [T-060] **P2**: WAL 用語運用の明文化。変わらず
26. [T-150] **P3 (CCBench・上流判断は人間)**: 同一 trx 内二重 update の first-write-wins。変わらず
27. [T-151] **P3 (CCBench・上流判断は人間)**: insert→delete の ghost tuple。変わらず
28. [T-154] **P2・裁定済み (2026-07-28 = 3 項とも採用) → 実装待ち**: (1) `DW-O07` 削除 (426 bytes
    が空く。予算逼迫の直接の解消手) (2) `docs/ai-provenance.md` へ byte 上限 (8,000〜9,000)
    (3) CAB 連続配置検査 = [T-153] (e) の条件解除。(3) は受理集合を狭めるので [T-110] の手続義務に従う。
    材料 = `output/insights/2026-07-28_t147-budget-restructure-package.md` §4
29. [T-130] **P3 (裁定要・未裁定)**: `..._uses_real_build_v2` (46.7 秒) の短縮。wall には効かず
    work 総和と低並列環境にのみ効く。`/rulings` では詳説せず推奨も出していない
30. [T-135] **却下 (2026-07-28)**: T-080 E2E の key C/D を amend で導出する案。build 合計は
    87.2 → 45.8 秒になるが stub-free 契約を弱めるため不採用 (規律 2)
31. [T-133] **P2・裁定済み (2026-07-28 = fsync 無効化案) → 実装待ち**: テスト用 git の fsync を切る
    (work −17.1%)。TMPDIR を tmpfs にする案は不採用 (共有ノードの物理メモリを奪う判断は消費量の
    実測が前提)。テストが `GIT_*` を除去するため実装が要る (未実証)
32. [T-144] **P3 (外部相談、野心的)**: Shirakami-LTX との中間のスペクトル補間。
    **[T-140] 択 (c) の移し先**。変わらず
33. [T-088] **段階 1 完了 (2026-07-28 (33))**: wrapper 配線を実機確認 (873225 = rc=2、official
    guard 生存)。段階 3 (単一 admission predicate) は本エントリの裁定パッケージ 3 項の裁定後。
    床値実測そのものは official 解禁後であり、条件待ち 8 件 ([T-085]/[T-112]/[T-114]/[T-011]/
    [T-122]/[T-103]/[T-089]/[T-090]) は塞がったまま
34. [T-096] **P3 (裁定済み)**: driver 側 timeout を予約式と整合させる。変わらず
35. [T-102] **P3 (裁定済み)**: production `_run_git` 2 箇所の ambient env 継承。変わらず
36. [T-122] **P3 (裁定済み → 測定後)**: `verify_receipt` の `search_repository` 重複。変わらず
37. [T-103] **P3 (裁定済み → 1 cycle 後)**: never-issued 検査は先送り。変わらず
38. [T-089] **P3 (裁定済み → 測定後)**: 二重 reason-tag 描画。変わらず
39. [T-090] **P3 (裁定済み → 測定後)**: `VerifiedFreeze.document` が mutable。変わらず
40. [T-112] **P3 (裁定済み → 床値実測の後)**: `s1_known_axes_freeze` の root 束縛が不完全。変わらず
41. [T-114] **P3 (裁定済み → 一巡後)**: never-issued の全層 scope 漏れ。変わらず
42. [T-011] **P3 (裁定済み = 前提の鎖を短縮せず維持)**: 科学レーン floor 実測。変わらず
43. [T-085] **P3**: PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
44. [T-087] **P3**: W-e 着手時に整合を決める裁定済 (延期)。変わらず
45. [T-012] **裁定済み (2026-07-28 = 解除しない)**: task-run pilot の凍結解除可否。[T-154] (1) の
    `DW-O07` 削除で「解除しない」側に確定。pilot を復活させる場合は新規に裁定を起こす
46. [T-010] **P3・延期**: B-008 再試験。変わらず
47. [T-082] **P3・延期**: prefix 容認 reader の用途別移行。変わらず
48. [T-121] **P3・実質不要と判明済み**: real-repo group の reader/writer 分離。変わらず
49. [T-156] **P3 (条件成立まで保留)**: selector-8b workload descriptor へ set-size 条件を反映する。
    変わらず
50. [T-148] **完了 (2026-07-28 (32))**: digest 環境を実 TU の写しにし、未知文脈と computed include を
    fails-closed 化。D93。変わらず
51. [T-155] **完了 (2026-07-28 (30))**: n\* crossover を実測 — 反転帯 80〜98 (build)、
    hit 経路は 2〜5、compact 側索引 32。休眠裁定の定量裏付け。変わらず
52. [T-140] **完了 (2026-07-28 (29)、(30) で記録訂正)**: 実 set-size 分布を実測、条件成立で
    択 (c) 適用 = データ構造軸の **workload 条件付き休眠 (max_ope=10 動作点では地形なし)**。
    移し先 = [T-139]/[T-144]。変わらず
53. [T-147] **完了 (2026-07-28 (28))**: 予算内再配分 + 受け皿 + C00 再評価義務。変わらず
54. [T-127] **完了 (2026-07-28 (28))**: byte 予算の使い方管理。変わらず
55. [T-137] **完了 (2026-07-27 (26))**: serve thread の偽緑。変わらず
56. [T-138] **完了 (2026-07-27 (26))**: 恒真ゲート。変わらず
57. [T-132] **完了 (2026-07-27 (24))**: group 分割。変わらず
58. [T-131] **却下 (2026-07-27 (23))**: worker 間 fixture 共有。変わらず
59. [T-128] **完了 (2026-07-27 (21))**: fixture の scan 膨張。変わらず
60. [T-120] **完了 (2026-07-27 (20)) だが (24) で結論を上書き**: group 分割の棄却は `-n 16` 限定。変わらず
61. [T-125] **完了 (2026-07-27 (19))**: 取り込み漏れの救出と worktree 掃除。変わらず
62. [T-116] **完了 (2026-07-26 (14))**: 本番 git 畳み込み。変わらず
63. [T-057] **完了**: 全走 69 秒 (worktree 測定。checkout 依存は F41 参照)。変わらず
64. [T-117] **完了 (2026-07-27 (15))**: 律速の内訳を実測。変わらず
65. [T-119] **完了 (2026-07-27 (17))**: SIGSTOP/SIGCONT 競合。変わらず
66. [T-105] **完了 (2026-07-27 (17))**: `_run_artifact_bytes` の素通し。変わらず
67. [T-104] **完了 (2026-07-27 (18))**: reference 再編。変わらず
68. [T-101] **完了 (2026-07-27 (18))**: 作法 2 件を `DW-O20` / `DW-O16` へ入れた。変わらず
69. [T-124] **完了 (2026-07-27 (18))**: 再編で場所を作って 3 件を入れた。変わらず
70. [T-108] **完了 (2026-07-27 (18))**: 作法 2 件を `DW-O18` / `DW-M01` へ入れた。変わらず
71. [T-111] **完了 (2026-07-27 (18))**: 作法 2 件を `DW-S01`+`DW-O19` / `DW-S03` へ入れた。変わらず
