# 段 1 brief — [T-2273] [T-2560] 受入 shard-0 律速の再同定 (第 4 回、診断のみ・実装差分ゼロ)

- **研究前進 (土台):** 受入全体 5 分の上限 (test-time-regression-rule) を refresh 後も shard-0 W_0 310.7〜344.9 秒で超えている。受入は全 wave の直列経路 (wave 所要の約 13 %) にあり、全研究 wave の周回を遅らせる。完了判定 = 現行 main の shard-0 律速を構成要素の実測で同定し、次の一手 1 つを実測の効果見込み付きで選ぶ。
- **確定済みユーザー裁定:** D1936 項 35 (最遅 worker を実測で選ぶ、prewarm 等は効果を先に測り未確認のまま実装しない)。D2219 項 4 / 第 31 回 4 (T-2845 Path.resolve 縮約は今は起こさない、T-2273 の律速対処が先)。依頼: 未実測の prewarm・共有 cache を先行実装しない、既存検査を削らない、診断 job は計算ノード、2 node 時間以上なら確認、scope 外の gate・検査・台帳・一般化を足さない。
- **起点の事実 (T-2825 §結論 6、T-2817 Job B):** B (現行台帳) では active_v2 系 8 node が t=0 から並び 209.7〜246.3 秒。A では同系 node が t≈55 秒から 189.98〜208.09 秒。T-2817 Job B (旧台帳、1 走) の key 別構築: t=62 秒に 5 key の builder が同時開始し copy 配置がどれも 100.4 秒 (構築 182 秒 = copy 100 + 発行 subprocess 69 + git 12)。t=116 秒開始の active_v2 key は copy 64.2 秒 (構築 145.8)、t=181 秒開始の fixture/active_v2 key は copy 33.0 秒 (構築 114.0)。
- **(P1) 親の provisional 仮説・攻撃対象:** 現行台帳では active_v2 key の base 構築が t=0 の他 key 構築と重なり、copy 配置が同時構築本数に応じて伸びる (IO 競合)。これが L の伸びと W_0 の床 (L + 後続 20〜31 秒 + F 73 秒) を決める。発行 subprocess 69 秒は本数に依らず一定 (仮説)。
- **(P2) 親の provisional 判断:** W_0 ≥ L + F なので、5 分未満には L の経路 (共有 base の構築 = copy・発行・git) を縮める必要がある。配置替えだけでは床は動かない。
- **実アンカー:** `orchestrator/tests/test_s8b_oracle_driver.py` の `_T080SharedBases.get` (key ごとに flock、未完なら builder)、`_t080_stub_free_e2e_repo` (key = 5 要素、base→test の copytree)、`_build_t080_stub_free_e2e_repo`、`_copy_git_visible_output` (実 repo `output/` の git 可視 file を Lustre から複製)、`_run_git`、発行 subprocess (`sys.executable -I -B -c`)、`migration.verify_receipt`。base 置き場は `tempfile.gettempdir()` (受入では計算ノードの /tmp)。
- **成果物:** insight `output/insights/2026-09-23/t2273-shard0-bottleneck-4/README.md` (実測表・判定・次の一手 1 つと効果見込み、probe は逐語 .md のみ)、worklog/decisions fragment。repo の実装面の差分ゼロ。
- **計測 (計算ノード、Pegasus generic dispatch、tip = wave 木 HEAD = main `3886a1fd3`、as-of = 2026-09-23T07:42:52+09:00):**
  - Job R ×3 (別 node 同時): T-2817 の replica runner + 観測 wrapper (Codex author 作、repo 外) を現行 tip へ合わせ、受入 shard-0 と同 argv の replica 1 走 + wrapper。出力 = W_0 / O_0 / L / F、最大占有 worker の item 列、key 別 builder の区間と構成 (copy / git / issue / residual)、builder の同時本数の時系列、各 consumer の flock 待ち・copytree・verify・本体残り。
  - Job C ×1: builder 同時本数 k ∈ {1, 2, 4, 6} (異なる key、各 2 反復) で実 builder を呼び、copy / git / issue の k 依存曲線を取る (他に負荷の無い node)。
  - 見積り: T-2817 Job B の実測 Elapse 425 秒 → R 3 本 ≈ 0.36 node 時間、C ≈ 0.4 node 時間 (上限)、受入 1 回 ≈ 0.25 → 合計 ≈ 1.0 node 時間 < 2 (確認不要)。
- **判定の読み方 (事前登録、段 4 で確定):** (a) R で L の worker の経路を「flock 待ち (= 他 builder の構築) / 自分の構築 / copytree / verify / 残り」に分解し、W_0 = O_0 + F の最大項を律速と呼ぶ。(b) C の k=1 と R の同時本数に対応する k の copy 差を「重なりを除いた場合の構築短縮の見込み」とする (測定値からの換算であり上下限ではない)。(c) A の 189.98〜208.09 秒との差は R の同時本数と C の曲線で説明できるかで答える (説明できなければそう書く)。
- **不変条件:** 受理集合・順序・既存検査・台帳に触れない。wrapper は実物へ委譲する観測のみ (DW-O14)。probe は repo に入れない (逐語 .md のみ)。数値は機械集計から。
- **分割:** 段 2 は省略 (本 brief にアンカー表)。段 3 = read-only 相談 1 本 (計測設計と P1/P2 を攻撃)。段 5 = Codex author 1 単位 (probe 3〜4 file、repo 外へ退避)。段 6 = read-only レビュー 1 本 (一次資料からの再抽出)。変異 matrix は実装面差分ゼロで免除、受入は 1 回。
