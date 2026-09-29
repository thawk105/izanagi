# 段 4 裁定 — cleanup-originals-migration (2026-09-30 02:10 JST 頃、date 実測)

材料: brief.md、s1-survey-{1,2,3}.md、consult-sol-out.md (決定役)、consult-luna-out.md (攻撃役)。両出力とも check_codex_output rc=0。
裁定 inbox の再走査: 2026-09-30-rulings-full40-verdicts.md (01:22) が新着。項 2 (T-2850 本比較は投入しない、入力は commit) と項 9 (T-2853 の fig2c・fig10 は別投入) は対象木を入力に取らず、衝突なし。

## 所見の裁定

| # | 所見 (出所) | real/refuted | 採否 | 処置 |
|---|---|---|---|---|
| 1 | P2 の T-2871 回収は基準外 (luna)。gen-opt 設計は未採用・本走未承認 (`gen-opt-evolution-design/README.md:3`)、内訳値は同 :224 に転記済み | real | 採用 | 回収しない。WAL 2 本は前日退避 `cleanup-branches-20260929c` の tar に入っている (backup4 で流用確認) ので、その所在を集約 insight と gen-opt README の追記に書く |
| 2 | P2 の回収は WAL 2 file に絞るべき (sol) | real だが #1 で回収自体を不採用 | — | — |
| 3 | P3 の tag は ref を増やすだけ、bundle で足りる (luna) / tag+bundle (sol) | luna を採る | 採用 | tag を作らない。B-5 発効 commit `6fce61d6e` は branch bundle (tip `b3eb51327` から到達) で保全し、復元方法を所在注記に書く。論文の主張は粗い provenance で足り (ユーザー方針 2026-08-12)、SHA の解決可能性を恒久 ref で保つ根拠が一次資料に無い |
| 4 | P4 の新 D は過剰ではない (luna 不成立、sol 採用) | refuted (攻撃) | P4 維持 | D2242 決定 1 を新しい D (fragment) で改める |
| 5 | P6 の新規 tar は依頼者方針に合わない (sol) | real | 採用 | 退避の有無を撤去の条件にしない。ただし走行中の backup4 は安価で既に回っているので、取れた分は記録する (条件にはしない) |
| 6 | brief の前日退避「56 本」は誤り。A 群は backup=c 52 本・backup_ok 47 本 (sol・luna) | real | 採用 | 木ごとの対応表 (backup/trees-backup.json) を正とし、集約 insight に木ごとの退避の所在を書く |
| 7 | 対象集合に t2853-r2-plot-fix1/fix2 が無い (sol) | real | 採用 | 撤去集合を 91 本 (A 80 + B 11) に補う。fix1/fix2 の branch は bundle 済み |
| 8 | 「有効な事前登録が入力に取る系列 0」は一般化しすぎ (sol)。T-2850 追補 3 は commit `299aa022e` を入力に取る | real (表現) | 採用 | 「木の path を入力に取る事前登録は 0。追補 3 が取るのは main 祖先の commit で、撤去の影響なし」と書く |
| 9 | 「archive の写しが撤去後の唯一の控え」は過大 (sol・luna)。K2 は job dir の `originals-copy-2026092{0,2}/` も残る | real | 採用 | 系列ごとに「撤去される原本 / 残る job dir 複製 / archive の写し / 前日退避 tar」を区別して書く |
| 10 | prune の照合を admin 名だけで行うのは不足 (sol・luna)。scratch2 の admin 名は汎用の `repo` | real | 採用 | prune 直前に dry-run 候補の各 admin entry の `gitdir` file が指す元の絶対 path を読み、自分が移した集合と完全一致したときだけ prune |
| 11 | mv は登録木の絶対 path だけ、移動先は一意で上書き拒否、vprobe は `submit-tree-vp` だけ (sol) | real | 採用 | P8 に加える |
| 12 | P7 に ComSys README の「branch にだけあり」、paper-methods-ja、archive README 冒頭の正本規約への注記が漏れている (sol) | real | 採用 | ComSys README・paper-methods-ja README に追記節、archive README に日付付き注記 (写しを official 入力へ昇格させない旨を保つ) |
| 13 | 到達不能 object 台帳への追記 (sol「必要なら」) | — | 不採用 (scope 外) | 台帳の entry は人間の喪失受容を要する期限つき台帳で、cleanup-branches §5 も転記を別 wave へ引き渡す。branch bundle の所在を集約 insight に書き、最終報告で転記未実施を明記する |
| 14 | P1 の一律撤去で論文数値が再導出不能になる (luna) | refuted | — | 攻撃役自身が不成立と判定。数値は repo 内派生物にある |

## plan v2 (確定)

1. **判定:** A・B の全 91 本・branch 11 本を「回収せず消す」。回収 (archive への新しい写し) は 0 件。残す対象 0 件 (ただし撤去直前の占有・HEAD・lock の再確認で稼働が判明したものは外す)。
2. **退避の記録:** branch 11 本は `backup/branches.bundle` (create/verify rc=0、main 非祖先 10 本の heads 一致、`freeze-g1-gen-t2724` は main 祖先)。木は `backup/trees-backup.json` (流用/新規) を集約 insight に木ごとに書く。既存 archive の写しの再照合 (verify_archive.py) の結果も書く。
3. **記録 (段 7):** 集約 insight `output/insights/2026-09-30/cleanup-originals-migration/README.md` + materials (対象表・名指し逆引き)。
   pin されていない insight README に「所在の移動・撤去 (2026-09-30 追記)」節。`docs/paper-story/README.md` に C14a 前例と同形の所在注記 (K2 結果稿 §5.1 の原本 path、B-5 発効 commit の branch 所在)。
   decisions fragment 1 本 (方針と D2242 の改め)、worklog fragment 1 本。repo 外: archive README に日付付き注記。凍結物 (結果稿・版・claim-evidence・receipt・MANIFEST・verbatim・raw) は変えない。
4. **段 6:** read-only review 1 本 (docs-only で一次資料から事実を書き起こすため)。実装面の差分 0 なので変異 matrix は免除。受入全走は land 前。
5. **段 9 (land 後):** 占有・HEAD・lock を再確認 → unlock → branch 付きは detach → `/work/1/SFC/tanab/tmp/cleanup-trash-20260930/<safe名>` へ mv (既存 destination は拒否) → branch 11 本を期待 tip 表で削除 (-D 10、-d 1) →
   prune は dry-run 候補の gitdir が指す path 集合 = 移した集合のときだけ 1 回 (land 調整役の OK 後) → 実体は背景で 2 並列削除。
   rescue gate (`check_branch_rescue.py`) は撤去前に 1 回試し、完走すれば JSON を job dir に置く (時間切れなら記録して進む — 2026-09-29 に 216 本で完走不能だった前例)。

## 変異の事前登録

実装面 (D95 決定 2) の差分 0 の wave なので変異 matrix は免除 (DW-S04)。
