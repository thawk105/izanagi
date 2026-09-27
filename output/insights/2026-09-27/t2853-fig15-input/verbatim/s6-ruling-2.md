# 段 6 裁定 2 — 焦点再レビュー 1 巡目 (NO-GO) への裁定 (2026-09-27)

検算 (leaf 差 9 / 8 と内訳、leaf 差 0 の 11 key、sha256、変異 3 / 3 KILLED・C0 生存、Elapse 191 s ≈ 0.053 node 時間、焦点走 142 / 1 と赤の帰属、三軸語走査、時刻・commit) は全項目一致。
前回所見は S1・S2・N1 が closed、M1 が partial。所見はすべて docs と insight の記述で、親が直す (実装面の fix は無し)。

| 所見 | 裁定 | 対応 |
|---|---|---|
| M1 partial / F-M1 `tools/plotting/README.md` が `validate_external_sources` を「外部原本の閉包」と書く | real・採用 | 「入力の 5 file を読まない閉包 `validate_repo_closure` と、入力の 5 file (既定は追跡下の逐語写し) から再導出する閉包 `validate_external_sources`」に直した |
| F-S1 insight §2.2 の「写しだけから」は、生成器が追跡下の稿を `caption_source` として読む限定を落とす | real・採用 | 「観測の入力 5 file を追跡下の写しから読み (caption の言い方は追跡下の稿を `caption_source` として読む)、repo 外の job dir なしで」に直した |
| F-S2 insight §2.2 の「本番との違いは `--evidence-root` の 1 leaf だけ」は各 leaf の値まで同じと読める | real・採用 | 「着地図に対して差の出た leaf の path の集合は、本番より 1 path 少ないだけ (生成器 sha256・出力 path・PDF の値は本番と対照で別)」に直した |

焦点再レビュー 2 巡目 (DW-O16 の 3 巡の内) で閉じたかを確かめる。
