# 段 1 brief — md_6: cleanup Stop hook の ff-only 直後誤検出 (T-2951 P2 / T-2957 P3、F1081)

- 研究前進 (土台): 背景 job の dev-wave は開始時に DW-O20 の `--ff-only` で main へ揃えるため、自分の commit 0 の間の turn 終了ごとに
  Stop hook が「land 済みの可能性、撤去せよ」を出し 1 往復を足す (実測: md_34 で 3 回・md_37 で 6 回、F1081)。最小差分は hook の判定 1 箇所。
  完了判定: ff-only 直後・commit 0 の木で block しない + 本当に land 済みの木では従来どおり block (test と実物再現の両方)。
- 実物再現 (段 1、job dir の repro-before.log): 使い捨て repo で「origin 相当の遅れた起点から branch → `merge --ff-only main`」した木に
  現行 hook script を通すと block。commit してから main へ ff-only land した木も block (こちらは正しい)。
- 実 repo の reflog 実測 (25 branch): 項目は `branch: Created …`・`commit: …`・`commit (merge): …`・`merge main: Fast-forward`・
  `merge <sha>: Merge made by the 'ort' strategy.` の 5 種だけ。`merge main: Fast-forward` は実在 3 branch (dev-wave-p5-s3-prereg・
  dev-wave-vhash-c2-motivation・dev-wave-vhash-story-v4) で観測 (DW-O13: 判定に使う field の値は実環境で到達可能)。
  land 済み 2 branch (worktree-dev-wave-cicada-promotion-uaf-fix・worktree-md22-auditor-types) は必ず `commit` 系の項を持つ。
  `tools/dev_wave_land.py` は wave branch を動かさず (replay は別 repo)、受入の取り込みは `merge --no-ff --no-commit main` + commit で `commit (merge)` になる。

## scope
- `tools/dev_wave_cleanup_stop_hook.py` の `decide()` の判定だけを直す。test は `orchestrator/tests/test_hooks.py` の `test_cleanup_stop_*` 群へ追加。
- (P1) 親の provisional 裁定・攻撃対象: branch reflog の最古項 (作成点) を除く**全項**の subject (`%gs`) が
  `merge main: Fast-forward` または `merge refs/heads/main: Fast-forward` と完全一致するなら「自分の commit 0」として通す。
  それ以外の項が 1 つでもあれば従来どおり (HEAD が main の祖先なら block)。main 以外からの ff・`reset`・`pull` は免除しない
  (land 済みの木で促しが消える方向の緩和をしないため)。subject の取得は既存の reflog 呼び出しを `--format=%H %gs` に変えて 1 回で取る。
- (P2) 解析不能 (OID 不正・区切り欠落) は従来どおり fail-open (通す)。

## 確定済みの制約 (依頼・D2314 項 4・hooks/README.md hook 5)
- 注意喚起 hook であって正しさ防壁ではない。fail-open・`stop_hook_active` で 1 回だけ・timeout 予算・入力上限は不変。
- 本当に land 済みの木で促しが消える方向の緩和はしない。hook の一般化・新しい検査は足さない。
- 実装面は Codex `role=author` (D95)。親は実装面を直接編集しない。
- `hooks/README.md` は guard_write の自己保護 (D427) で AI が直接書けず、所有外でもある。hook 5 の「既知の限界」の
  「main を fast-forward で取り込んだだけの未 land wave は誤って促しうる」の 1 文が古くなるので、その更新を持ち越し項目として記録する。
- 判定の変更は D2314 項 4 の判定文の改訂なので、decisions fragment を書く。failures F1081 の恒久対応と T-2951・T-2957 を閉じる。

## 成果物
- 実装 + test (Codex author)、変異 matrix、受入全走、spool fragment (worklog・decisions・failures)、insight
  `output/insights/2026-10-01/cleanup-stop-hook-ffonly/` (brief・裁定・再現 log・変異台帳)。

## 分割・段構成
- 所有 path は 2 file で 1 単位、実装子 1 本。軽量版: 変更は小さく設計択一は (P1) の 1 点なので段 2・3 を省き、
  受理集合 (block する状態の集合) が変わるので段 6 の敵対レビュー 2 本 (うち 1 本は過剰・削除レンズ) を残す (DW-C00)。
- 受入・実測環境: 変異と受入は Pegasus の dispatch 経路 (docs/pegasus-runbook.md)。login で重い test を回さない。
