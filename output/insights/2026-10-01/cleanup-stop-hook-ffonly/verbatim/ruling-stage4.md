# 段 4 裁定 — md_6 cleanup Stop hook の ff-only 直後誤検出

段 2・3 は軽量版で省略 (brief の分割・段構成)。段 4 直前の裁定 inbox 再走査: worklog・failures に本 hook の未裁定項目なし
(T-2951・T-2957・F1081 だけ)。

## 採否
- (P1) 採用: branch reflog の最古項を除く全項の subject が `merge main: Fast-forward` / `merge refs/heads/main: Fast-forward` の
  どちらかと完全一致するとき通す。それ以外は従来の判定 (HEAD が `refs/heads/main` の祖先なら block) のまま。
  - 禁止の署名: 「最古項以外に 1 項でも非 ff (commit・commit (merge)・reset・rebase・cherry-pick・main 以外からの ff・非 ff merge)
    を持つ branch の block を、この変更で消してはならない」。
  - 通る正例: 作成 → `merge --ff-only main` だけの木 (commit 0) は通る。
  - 止まる正例: 作成 → ff main → commit → main へ ff-only land の木は block。land 後にさらに ff main した木も block。
    main 以外の branch から ff で commit を取り込み land した木も block。
- (P2) 採用: reflog 行の OID 不正・区切り欠落は fail-open (従来の OID 検査の延長)。
- scope 外 (実装しない): `reset --hard main` や sha 指定の ff (`merge <sha>: Fast-forward`) の免除。実測 25 branch で未観測、
  免除すると land 済みの木を通す余地が広がる。`hooks/README.md` の文言更新 (D427 の防護 dir、所有外) は持ち越し項目へ。

## 成果物影響 (DW-G05)
放置すると各 wave の初期段で turn 終了ごとに誤った撤去の促しが出て、指示どおり撤去すれば作業中の木 (未 commit の草稿・fragment) を消しうる
(F1081)。certified 選択・台帳の値は変わらない。

## 変異の事前登録 (DW-M01、位置は実装後に一意性を確認して確定)
- M1 免除を常に真: 免除述語を `True` に → 既存 `test_cleanup_stop_blocks_landed_linked_worktree` と新しい止まる正例が KILLED 期待。
- M2 免除を削除 (常に偽): → 新しい通る負例 (ff main だけの木) が KILLED 期待。
- M3 免除を `: Fast-forward` 末尾一致へ拡大: → 「main 以外から ff で取り込み land した木は block」が KILLED 期待。
- M4 最新項だけを見る: → 「land 後にさらに ff main した木は block」が KILLED 期待。
- M5 最古項も含めて全項を見る: → 通る負例が KILLED 期待 (最古項 `branch: Created` は非 ff)。
各変異の期待 node は実装後に login self-run (DW-M08) で完全集合を確定する。
