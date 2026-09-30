# 段 1 brief — dev-wave-land-cleanup-enforce (2026-09-29)

依頼 (ユーザー逐語): 「dev-waveをした後に、local mainにland成功しつつワークツリーやブランチを掃除せずに終了するやつが多いせいで、ワークツリーやブランチのごみが溜まりやすい。改善してくれ」

## 研究前進 (土台)
worktree 167 本・branch 228 本 (2026-09-29 21:3x JST 実測) で `git worktree list` 7 秒、rescue gate は 216 本で完走不能 (8 秒上限)、
`/cleanup-branches` は 1 回 1.5 時間。全 wave の起動・受入・掃除が遅くなり研究 wave の回転を止めている。完了判定: 下の 3 経路の流入を
tool / hook の正例・負例テストで固定し、本 wave 自身の段 9 で自分の子木・wave 木を撤去できること。

## 実測 (一次資料: 9/29 land 済み wave 約 35 本の transcript、調査子の集計を親が tool 現物で照合)
- wave 本体の木は多くが撤去済み。残骸の主成分は Codex 子木と補助木。`.claude/worktrees/` の未取込 branch 付き木 39 本の大半が fix 巡ごとの子木 (vhash-fwd-fix..fix8、vhb-fix1..fix10)。
- 原因 A (約 10 wave): `tools/dev_wave_cleanup.py:1577-1591` `_assert_child_integration` が「履歴が全部 main 祖先」か「所有 path 一致 (空なら不成立)」を要求。fix 途中版の木 (mismatched paths) と repo に入れない probe/plot 木 (empty owned_paths) は構造的に rc=20。
- 原因 B (4 wave): 撤去中に他 wave の land で main が進むと `:1580` / `:1933` の "main changed since integration proof" で rc=30。木の dir は消え登録と branch が残る。
- 原因 C (2 wave): land 後 `result:` を書いて撤去を呼ばず終了 (vhash-related-work、paper-story-vhash-setup — 後者の木は現存)。land tool は撤去を案内しない。Stop 時の検査 hook は無い (`.claude/settings.json` は PreToolUse 4 本のみ)。
- 原因 D (2 wave): 並走調整役の `CLEANUP OK` 待ちで停止。約束は repo 外の運用なので本 wave の scope 外 (報告のみ)。
- 原因 E: manifest 外の補助木 (integ/run/smoke/verify、1 wave で 14 本)、amend による wave 本体 reflog rc=20 (3 wave)。

## 変更面 (親の provisional 裁定・攻撃対象)
- (P1) `remove-child`: 統合証明が不成立でも、子の未取込内容 (branch/HEAD reflog の main 非到達 commit、tracked 差分、未追跡) を証拠 dir へ全部退避・検証できたら撤去し、子 branch を `-D` する。退避できない状態は現行どおり rc=20。D2163 却下案「非祖先は退避して撤去」の再裁定になる。根拠: ユーザー 2026-09-29 指示「main へ持ち込む価値が小さいものは退避してから消せ、報告止まりにしない」(memory、repo 未記録)。
- (P2) integration proof 後に main が**前進しただけ** (proof 時の main tip が現 main の祖先) なら続行し rc=30 にしない。非前進 (巻戻し・分岐) は現行どおり拒否。wave 本体経路 `:1933` も同様か検討。
- (P3) Stop hook 新設: session の cwd が linked worktree で、その branch が作成点から前進し tip が `refs/heads/main` の祖先 (=land 済み) かつ木が現存なら、終了を 1 回 block し DW-O28 撤去か撤去不能理由の報告を促す。`stop_hook_active` なら通す (無限ループ防止)。判定不能・git 失敗・timeout は通す (注意喚起 hook で正しさ防壁ではない)。
- (P4) docs: DW-O28 / DW-S05-A に「wave が作る全 linked worktree (補助・計測・probe を含む) を作成時に manifest 登録」「fix は同じ子木を再利用」を統合 (exact pin・byte 予算の影響を実測)。

## 確定済みユーザー裁定 (repo 未記録、memory が一次資料)
- 2026-09-29 md_14 (memory `clean-up-own-worktrees-and-branches`、逐語は job dir の ruling-memory-*.md): 「自分で出したゴミは自分で掃除しろよワークツリーとブランチ」「早く掃除せぇ」。
  段 9 で自分の子 branch (途中の fix branch を含む) は bundle 退避・verify してから `-D`。撤去 tool が統合証明不成立で拒否しても残置報告で止めず手動撤去
  (clean と占有 0 を確認 → detach → 同 FS へ mv → 自分の `.git/worktrees/<name>` だけ除く)。`git worktree prune` は他 wave を巻き込むなら打たない。
- 2026-09-29 (memory `cleanup-delete-stale-garbage-not-just-report`): 価値の小さい残骸は bundle・tar 退避後に削除、報告止まりにしない。
- 本 wave の (P1) はこの手動手順を tool に取り込み、退避の検証付きで毎回同じに回すもの。D2163 の却下案の再裁定は段 4 でこの裁定を根拠に行う。

## 不変条件
- 退避の完全性を下げない (F1034: 退避 tar が空のまま撤去して計測原本を失った)。未退避・検証失敗は撤去しない。wave 本体 branch は `-d` のみ (D703)。
- 占有・lock・submodule・admin dir の既存検査は緩めない。`git worktree remove`/`submodule deinit` を使わない (F26)。
- テスト全体 5 分上限。既存テスト期待値を変えない (受理集合を広げる箇所だけ新テストで固定)。

## 成果物の形
tool 変更 + テスト、hook + settings + テスト、docs (hooks/README、DW-O28 等)、decisions/failures fragment、insight。

## 分割方針
実装単位 2 つ (所有素集合): U1 = `tools/dev_wave_cleanup.py` + そのテスト、U2 = 新 hook + `.claude/settings.json` + hook テスト。
受入: login node の `tools/dev_wave_wait.py acceptance`。
