# 段 6 裁定 — 敵対レビュー A (正しさ境界)・B (過剰・削除) の所見

両レビューとも NO-GO。レビュー A は委任なし・書込みなし、差分は所有 2 file だけで既存 test・helper の変更なしと確認。

| 所見 | 裁定 | 理由 |
|---|---|---|
| A-1 / B-1 最古項が作成項でない (作成項の期限切れ・削除) と、実 commit 項を作成点として捨て免除してしまう | real・採用 (F1) | 依頼の「land 済みの木で促しが消える緩和はしない」に反する具体反例 |
| A-2 `splitlines()` が U+2028 等でも割り、commit subject の一部が「不正行」になって fail-open で通る | real・採用 (F2) | 旧 `%H` では起きない、新しい解析が作る退行 |
| A-3 / B-2 `run()` の `.strip()` が最古項の空 subject の区切り空白を消し、区切り欠落 fail-open で通る | real・採用 (F3) | 同上 |
| A-4 tag `refs/tags/main` (branch より優先) や `GIT_REFLOG_ACTION='merge main'` の commit でも subject が `merge main: Fast-forward` になり、自分の commit を取り込んで land した木が免除される | real・採用 (F4) | subject は来歴を証明しない。repo に tag main は無い (実測) が、依頼の非緩和条件に対する反例として塞ぐ。安い照合で足りる |
| A 付記: sha 指定 ff・`pull --ff-only`・`reset --hard main`・`merge -m` 付き ff は免除されない | 確認 (scope 外のまま) | 段 4 裁定どおり。報告では「DW-O20 の `merge --ff-only main` の誤検出を直した」と書き、ff 全般とは書かない |
| B-3 test の統合 (fixture・REASON 文言検査の重複) | nit・任意 | 検出範囲を落とさない範囲で統合してよい。統合しなくてもよい |
| B-4 最古 OID 比較を解析不能分岐と `or` で統合 | nit・任意 | 挙動不変なら可 |

## plan v2 (fix 子への指示の要点)
- F1: 免除は「最古項の subject が `branch: Created from ` で始まる」ときだけ。それ以外は従来判定。
- F2: レコード境界は LF (`\n`) だけ。`splitlines()` を使わない。
- F3: 区切り空白の欠落を fail-open にしない。OID が有効で subject が無い (空) 行は「空 subject」として扱う
  (= 免除対象でない、従来判定へ)。OID 不正は従来どおり fail-open。
- F4: 免除する各 ff 項 (OID X、reflog 時刻 t) について、`refs/heads/main` の reflog に OID X で時刻 ≤ t の項があることを要する。
  1 項でも満たさなければ免除しない (従来判定)。時刻は `git reflog show --date=unix --format=%H %gd …` の `@{<unix>}` から取る。
  main の reflog を読めない・解析不能なら免除しない (従来判定 = block しうる側)。git 呼び出しは 1 回増え、既存の 1 呼び出し 2 秒・
  合計 5 秒の予算内に収める (main reflog 3,732 項で実測 0.15 秒)。
- 既知の残余: main の更新と spoof の ff が同一秒に起きた場合の判別不能 (≤ を使う理由は、通常の ff で main の移動と wave の ff が
  同一秒になりうる test・実運用の負例を通すため)。報告に書く。

## 変異の追加事前登録 (fix 前、DW-M01)
- M6 作成項の要求を外す → 「作成項が消え最古項が commit の land 済み木は block」が KILLED 期待。
- M7 LF 分割を `splitlines()` へ戻す → 「U+2028 を subject に含む commit を land した木は block」が KILLED 期待。
- M8 区切り欠落を fail-open に戻す → 「最古項が空 subject の branch で commit を land した木は block」が KILLED 期待。
- M9 main 時刻照合を常に真にする → 「tag main から ff し land した木は block」(または GIT_REFLOG_ACTION 偽装) が KILLED 期待。
- M10 `≤` を `<` にする → 「main 前進と wave の ff が同一時刻の ff だけの木は通す」負例が KILLED 期待。
