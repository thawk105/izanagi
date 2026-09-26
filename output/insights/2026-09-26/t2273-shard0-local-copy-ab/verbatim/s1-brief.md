# 段 1 brief — [T-2273][T-2560] t080 共有 base の可視 output 複製元を計算ノード局所の写しへ

wave worktree: /work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy (branch worktree-t2273-shard0-local-copy、起点 local main 65fd1422f)。

## 研究前進 (1 行)
土台: 受入 shard-0 の W_0 は T-2825 の B 条件 3 走で 310.7〜344.9 秒と 5 分上限 (test-time 規律) を超え、全 wave の受入・land を律速している。第 4 回診断 (一次資料 output/insights/2026-09-23/t2273-shard0-bottleneck-4/README.md) で律速は t080 共有 base builder 8 本 (共有 7 key + 非共有検査 1) が t≈130 秒に同時に Lustre の output/ 可視集合 (除外前の可視 path 29,885) を複製する成分 (builder あたり copytree 90〜111 秒、待ち支配) と同定、複製元を node-local に差し替えた対照 1 対で W_0 −123.9 秒 (−27.3 %)。完了判定 = 実装 tip で隣接対の実受入 (3 対、D357) を測り、段 4 で事前登録した land 条件を満たしたときだけ land する (測ってから land)。−123.9 秒は事前 staging 済みの対照値で、今回方式の期待値ではない。

## scope (本題の実装だけ)
- `orchestrator/tests/test_s8b_oracle_driver.py` の builder (`_build_t080_stub_free_e2e_repo` 内の `_copy_git_visible_output(ROOT, root / "output")`、1458 行) の複製元を、xdist session ごとに 1 回だけ作る計算ノード局所の写しに差し替える。
- (P1) 親の provisional 裁定・攻撃対象 — 時期と担い手: 写しは session の共有 base 置き場 (`_T080SharedBases.parent`、`tempfile.gettempdir()` 配下 = 計算ノードの /tmp) に、**最初に builder に入った worker が flock 下で 1 回だけ**作る (遅延生成)。他の builder はその完成を flock で待ち、写しから局所 copytree する。collection 時の先行生成 (prewarm) はしない。
- (P2) 写しの作り方: 写しは現行の実関数 `_copy_git_visible_output(ROOT, <写し>/output)` を実 repo に対して 1 回呼んで作る (列挙・除外・regular file 検査を含め 1 byte も変えない)。builder はその写しを `shutil.copytree` で自分の root/output へ複製する。git clone / checkout は使わない。
- (P3) 未 commit の可視 file: 写しは作業木から作るので、modified tracked / untracked の可視 file は現行と同じく含まれる (clean tree を要求しない)。変わるのは「読む時刻」が builder ごと → session で 1 回になる点だけ (現行も共有 7 key の builder は約 t=130 秒にほぼ同時に始まる — 段 4 で A5 により ±0.3 秒の断定を撤回)。
- (P4) session 間の再利用はしない (写しは session の共有置き場と一緒に最後の worker が消す)。xdist session が無い単独走 (`_T080_SHARED_BASES is None`) は現行の直接複製のまま。
- (P5) 非共有 builder (gw20 の `test_t080_shared_base_builds_real_builder_once_across_processes`) は fixture が `_T080_SHARED_BASES` を test 局所の bases に差し替えるので、その局所の写しを作る (1 本の Lustre 複製が残る)。これを session の写しへ寄せるかは段 3 の攻撃対象。
- test: 新しい経路の正例 1〜2 本 (写し経由の複製結果が直接複製と同じ集合・bytes、写しは session で 1 回だけ作られる) だけ。

## 確定済みユーザー裁定・不変条件
- D2068 の却下 3 案 (whitelist / alternates / 独立 index) と圧縮設定変更に触れない。複製する集合・object store・index は不変。
- D2044 項 15: 全件複製を絞らない、全件性の検査 2 か所を維持する。2 か所 = T-2618 起票文 (docs/archive/worklog-phase3-0914-1493.md) の「1302 行・1328 行」で、現 HEAD では `test_t080_output_copy_visibility_matches_production_enumeration` (1899 行) 内の (A) 1983〜1984 行 `fixture_visible == expected_visible` / `== production_visible` (複製関数の集合 = 本番列挙 `s8b_holdout_freeze.enumerate_repository_files` の output 配下) と (B) 1994〜1998 行 (可視 tracked file 欠落で複製関数が AssertionError)。本 wave は `_copy_git_visible_output` / `_git_visible_output_paths` と上記 test を 1 byte も変えない。ただしこの 2 検査は関数単体の検査であり、builder が写し経由で同じ集合を受け取ることは検査しない → 写し経由の等価性の正例 test を足す (新機構の正例であって新 gate ではない)。
- 規律 2: 受理集合を変えない。発行 subprocess の production scan が見る fixture の output/ は現行と同じ集合・同じ bytes。
- 仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外 (依頼)。T-2845 (Path.resolve 縮約) は起こさない (D2219 項 4)。
- 実装は Codex author (D95)。親は実装面を直接編集しない。

## 成果物の形
- 実装 commit (Codex author)、test、変異台帳、insight (隣接対の測定結果)、worklog / decisions の fragment。

## 受入・実測環境
- 計算ノード Pegasus gen_S。隣接対: A = 測定時 local main の clean worktree、B = wave tip (A + 実装)。T-2825 の形 (固定 2 tree、`IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py` 直接投入、A/B 交互 3 対、D357 の中央値)。判定量 = shard-0 W_0 の対差、補助 O_max・L・builder 待ち。
- 計算量見積り: 受入 1 回 ≈ 0.25 node 時間 (実測単価) × 6 走 = 1.5、最終受入 0.25、変異 matrix 少数 → 合計 2 node 時間未満に収める。超えるならユーザー確認。

## 並列分割
- 実装は 1 単位 (1 file の局所変更) で子 1 本。
