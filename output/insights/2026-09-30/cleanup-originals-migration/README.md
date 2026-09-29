# 原本を抱えて残っていた古い worktree 91 本・branch 11 本 — 回収の判定、退避の所在、記録の付け替え (2026-09-30)

- 作成: 2026-09-30 JST。wave `dev-wave-cleanup-originals-migration` (背景 job、軽量版)、起点 local main `f0869d953`。
  依頼 (ユーザー、2026-09-30 01:0x JST) の逐語は `verbatim/request.md`、段 1 brief は `verbatim/s1-brief.md`、段 4 裁定は `verbatim/s4-ruling.md`。
- repo 外の作業 dir (job dir): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/`。退避は同 dir の `backup/`。
- **本 insight が、撤去した木・branch の判定と所在の正本である。** 名指し元の insight README には末尾に「所在の移動・撤去 (2026-09-30 追記)」節を足し、ここを指した (§5)。

## 0. 結論

1. **対象の worktree 91 本 (投入木など A 群 80 本、個別の木 B 群 11 本) と local branch 11 本は、全部「回収せずに消す」と判定した。回収 (恒久置き場への新しい写し) は 0 件。**
   判定基準 (ユーザー方針) は「(a) 論文の数値・図がその原本からしか得られない、(b) phase3 の現行タスクか worklog 末尾の次の一手が入力に取る、
   (c) 有効な事前登録・凍結が入力に取る、のどれかを一次資料で示せたものだけ回収する。名指しされているだけ (経緯・所在の記述) は回収理由にならない」。
   3 本の調査 (`materials/survey-{1,2,3}.md`) で (a)〜(c) に当たる系列は 0、コード・テストが木の path を読む箇所も 0 だった。
2. 論文が使う数値・図はすべて repo 内の派生物 (insight・結果稿) にある。campaign 原本のうち K2 3 組・B-5 試走・MOCC 疎通 21 本・T-2850 試走 v2 18 本・T-2865 段階 F は、
   既に `/work/1/SFC/tanab/izanagi-repro-archive/` に sha256 照合つきで写してあり、今回その写しを再照合した (§4)。
3. 判定が割れたのは 2 点で、Codex 2 役 (決定役・攻撃役) の相談を経て親が裁定した (§7)。
   T-2871 生死確認の WAL 2 本は回収しない (gen-opt 設計は未採用で内訳値は転記済み)。B-5 の発効 commit `6fce61d6e` は tag を作らず branch 束 bundle で保全する。
4. D2242 決定 1 の「branch `worktree-t2273-shard0-local-copy` は残す」は、本 wave の decisions fragment (`docs/spool/decisions/2026-09-30-dev-wave-cleanup-originals-migration-1.md`、D 番号は land 時の fold が付ける) の新しい決定で解いた。
5. 撤去 (mv → prune → 実体削除、branch 削除) は本 wave の land の後に行う。本 insight は撤去前の判定と退避の記録である。

## 1. 範囲と言わないこと

- 撤去の対象は登録された worktree の directory と local branch だけである。job dir の中の木以外の file (台帳・evidence・materials・`originals-copy-*`・`vprobe/runs/`・`consult-option/` 等) は動かさない。
- 「原本が要らない」は上の (a)〜(c) の基準での判定であり、記録された測定・判定を無効にするものではない (規律 7)。記録の本文は書き換えず、所在の移動を追記で示した。
- 退避 (tar・bundle) は撤去の前提条件にしていない (ユーザー方針「損失ゼロは要件ではない」)。取れた分の所在を §3 に書く。
- 到達不能 object 台帳 (`docs/unreachable-object-ledger.md`) への転記はしていない。削除する branch の commit は §3 の bundle から復元できる。

## 2. 系列ごとの判定

| 系列 | 木 (本数) | 名指しの主な目的 | 判定 | 撤去後に残るもの |
|---|---|---|---|---|
| T-1505 A-1 attempt-0001 | `dev-wave-jobs/dev-wave-t1505-a1-sized-submit/submit-tree` (1) | 投入元・公開 leaf の destination | 回収せず消す | 公開 leaf 4 file が repo に byte 一致、測定本体は durable base と archive `t2853-20260923/` |
| T-2489 A-2 nodes5 probe | `dev-wave-t2489-a2-nodes5-probe/submit-tree` (1) + branch `probe/t2489-a2-nodes5-submit` | 投入元・使い捨て commit `3f61c3408` | 回収せず消す | README が内容を記述、commit は branch 束 bundle |
| T-2792 A-1 attempt-0002 | `dev-wave-t2792-a1-sized-attempt2/submit-tree` (1) | 投入元 | 回収せず消す | 公開 leaf 4 file が repo に byte 一致 |
| T-2795 K2 pair・pair2・r4 | `dev-wave-t2795-k2-pair/submit-tree-pair`、`dev-wave-t2795-k2-pair-resubmit/submit-tree-{pair2,r4}` (3) | 原本の所在 (K2 4 巡稿 §5.1 の原本 path を含む) | 回収せず消す | archive `t2853-20260923/` の写し 3 組、job dir の `originals-copy-20260920/`・`originals-copy-20260922/`、T-2860 の `ao-root/` |
| T-2797 B-5 試走 | `dev-wave-t2797-b5-contrast/submit-tree` (1) | 投入元 (統合 commit `11d46a74a`) | 回収せず消す | archive `t2853-20260923/` の `b5-pilot-originals`、repo の insight `t2797-b5-contrast/` |
| T-2797 B-5 本走 | `dev-wave-t2797-b5-main-run/submit-trees/{calib,t01..t12,t15..t17}` (16) | 名指し 0 (台帳は job dir) | 回収せず消す | job dir の台帳・driver-state・materials。論文が使う費用値は `t2797-b5-cost-options/data/` |
| B-5 発効 | `.claude/worktrees/t2797-b5-effect` (1) + branch `worktree-dev-wave-t2797-b5-main-run` | 発効 commit `6fce61d6e` の唯一の ref | 回収せず消す (commit は bundle) | branch 束 bundle (復元: `git fetch <bundle> refs/heads/worktree-dev-wave-t2797-b5-main-run:<新しい名>`) |
| T-2273 shard-0 局所写し | (木なし) branch `worktree-t2273-shard0-local-copy` | 実装 `eb65d322f` の保存先 (D2242 決定 1) | 回収せず消す (新しい決定で D2242 を解く) | branch 束 bundle、insight `t2273-shard0-local-copy-ab/` §2 の記述 |
| T-2847 verifier-capacity | `dev-wave-t2847-verifier-capacity/submit-tree-{A,B}` (2) | 投入 commit (main の祖先) | 回収せず消す | 値は insight の `raw/`、verifier 出力全文は job dir `runs/` |
| T-2849 MOCC 差し込み | `dev-wave-t2849-mocc/submit-tree{,-b}` (2) | 投入元 | 回収せず消す | 値は insight §6、job dir `liveness/` |
| T-2849 MOCC 疎通 | `dev-wave-t2849-mocc-conn/trees/*` (22) | 投入形・原本の例示 | 回収せず消す | archive `t2853-20260927/` の `t2849-mocc-conn-originals` (21 本分) |
| T-2850 同時検査 | `dev-wave-t2850-trace-concurrent-verify/submit-tree{,-2}` (2) + `trial-v2/trees/*` (19) | 投入元・固定 commit | 回収せず消す | archive `t2853-20260927/` の `t2850-trial-v2-originals`、固定 commit `299aa022e` は main の祖先 |
| T-2850 試走 v1 | `dev-wave-t2850-trial-run/submit-tree`、`vprobe/submit-tree-vp` (2) | job dir 全体の所在 | 回収せず消す | job dir の `vprobe/runs/`・`estimate/`・`consult-option/`・台帳 (動かさない) |
| T-2865 系列 B・C・段階 F | `dev-wave-t2865-iter2/trees/b`、`dev-wave-t2865-series-c/trees/c`、`dev-wave-t2865-stage-f/trees/e2e` (3) | 投入元 | 回収せず消す | 値・proposal は insight に転記済み、`e2e` は archive `t2853-20260927/` |
| T-2871 生死確認 | `dev-wave-t2871-policy-loop-iter/trees/live` (1) | 投入元、gen-opt 設計 §6.1 の生データ | 回収せず消す | 前日退避 tar (WAL 2 本を含む 12 file、§3) |
| T-2868 MOCC G2 原因 | `tmp/t2868-mocc-g2-20260927/trees/sb1`〜`sb4` (4) + `.claude/worktrees/t2868-probe-author` (1) + branch 同名 | 投入元、probe の repo 側保存先 | 回収せず消す | job dir の `probe/`・`recheck-output/`、branch 束 bundle |
| T-2724 (取り下げ) | `.codex/worktrees/t2724-chain-scratch`・`t2724-g1-gen` (2) + branch 2 本 | 経緯・再現の作業場所 | 回収せず消す | G `32ba8cae4` は main の祖先、scratch branch は bundle |
| T-2853 R2 作図 | `.codex/worktrees/t2853-r2-plot-author`・`t2853-r2-plot-fix1`・`t2853-r2-plot-fix2`・`t2853-r2-fig6-author` (4) + branch 4 本 | 逐語の中の作業場所 | 回収せず消す | 最終 wrapper と図は archive `t2853-r2-fig6-20260929/` と `/work/1/SFC/tanab/b10-backoff-grid-t2853-r2-20260928/`、branch は bundle |
| VHash hot-block microbench | `.claude/worktrees/vhb-mw9`・`vhb-mw10` (2) | raw JSON の bench 実体 path | 回収せず消す | 値は insight `vhash-hot-block-microbench/`、HEAD `b42cba01e` は main の祖先 |
| VHash read-only share の変異 | `tmp/vhash-readonly-share-2026-09-29/mutation/scratch2/.izanagi-mutation-worktree/repo` (1) | 名指し 0 | 回収せず消す | 変異結果は insight、wave は land・撤去済み |
| md2 pack hint | (木なし) branch `md2-pack-hint-fix` | 名指し 0 | 回収せず消す | 内容は main (`tools/check_docs.py`)、branch は bundle |

木の本数の計は 91 (A 80 + B 11)。木ごとの path・HEAD・main 祖先か・未追跡件数・退避の所在は `materials/trees.tsv`。

## 3. 退避

退避は repo を変えずに job dir の `backup/` へ取った (script は同 dir の `backup4.py`、log は `backup4.log`)。撤去の条件にはしていない。

- **branch:** 対象 11 本 (§2) を 1 本の bundle `backup/branches.bundle` に入れた (`^main` で main の祖先を除く)。create rc=0・`git bundle verify` rc=0、
  `list-heads` の 10 本が main 非祖先 10 本の期待 tip (`backup/expected-tips.txt`) と一致した。main の祖先の `freeze-g1-gen-t2724` (`32ba8cae4`) は bundle に入らず、main から辿れる。
- **木:** 対象 91 本のうち 89 本を検査し、HEAD が記録から動いた木は 0。
  - 前日の退避 (`/work/1/SFC/tanab/dev-wave-jobs/cleanup-branches-20260929c/`・`…d/`) があり、HEAD・tracked の差分の大きさ・未追跡 file の件数と集合が今回と一致した 55 本は、その退避を流用した。
  - 残る 34 本 (MOCC 疎通 22・MOCC 差し込み 2・T-2868 の sb 4 と probe 木・vhb-mw9/10・scratch2・T-2853 作図 author と fig6) は新しく取った
    (未追跡 file のあった 29 本は list を `tar -C <木> --null -T <list>` で固め、list 件数と tar の非 directory entry 数が 29 本とも一致、新規 tar の計 631,004 B。
    残る 5 本は未追跡 file が 0 件)。不良 0。
  - `t2853-r2-plot-fix1`・`fix2` の 2 本は対象表への補い (段 4) が退避の後だったので木の退避は無い。中身は旧版の wrapper と途中の図で、branch は束 bundle に入っている。
  - HEAD が main の祖先でない木 22 本は、いずれも束 bundle の branch 先端から辿れる (B-5 本走の 16 本と発効木は発効 commit `6fce61d6e`)。
- 木ごとの path・HEAD・main 祖先か・未追跡件数・退避の所在は `materials/trees.tsv`。T-2871 の WAL 2 本は
  `/work/1/SFC/tanab/dev-wave-jobs/cleanup-branches-20260929c/trees/dev-wave-jobs_dev-wave-t2871-policy-loop-iter_trees_live/untracked.tar.gz` (12 file、tar の entry 数 12) に入っている。

## 4. 既存の写しの再照合

`izanagi-repro-archive` の写しのうち、撤去する木を元にした 7 組を、写し側の各 file の sha256 を読み直して manifest (`manifests/<組>.sha256`) と照合した (script `verify_archive.py`、log `verify-archive.log`)。

| 置き場 | 組 | file 数 | 一致 | 不一致 | 写しの欠け |
|---|---|---:|---:|---:|---:|
| `t2853-20260923/` | `k2-pair-first-originals` | 7 | 7 | 0 | 0 |
| `t2853-20260923/` | `k2-resubmit-pair2-originals` | 8 | 8 | 0 | 0 |
| `t2853-20260923/` | `k2-resubmit-r4-originals` | 8 | 8 | 0 | 0 |
| `t2853-20260923/` | `b5-pilot-originals` | 274 | 274 | 0 | 0 |
| `t2853-20260927/` | `t2849-mocc-conn-originals` | 555 | 555 | 0 | 0 |
| `t2853-20260927/` | `t2850-trial-v2-originals` | 1,728 | 1,728 | 0 | 0 |
| `t2853-20260927/` | `t2865-stage-f-originals` | 13 | 13 | 0 | 0 |

計 2,593 file すべて一致。あわせて、これらの木の未追跡 file のうち `output/exploration/` と `output/env/pegasus/claims/` の配下で manifest に載っていないもの
(写しの後に木へ増えた原本) を数え、0 件だった。

## 5. 記録の付け替え

- 名指し元の README 26 本の末尾に「所在の移動・撤去 (2026-09-30 追記)」節を足した (一覧は `materials/appended-files.txt`)。本文は変えていない。
- `docs/paper-story/README.md` の results 系列の追補の後に、K2 4 巡稿 §5.1 の原本 path と、版 3 本の B-5 発効 commit の所在の記述についての注記を足した (C14a の追記と同じ形)。
  結果稿・版・claim-evidence は append-only の凍結物なので変えていない。
- 追記の前に、追記先 30 file (候補) の現行 sha256 (先頭 16 桁) と path で repo 全体を 1 回の `git grep` で探し、sha256 の束縛は 0 件だった (`materials/pincheck.txt`)。
  path の出現は output-pruning の件数表・図の provenance の引数・逐語などの文字列で、内容の hash ではない。
- repo の外では、`izanagi-repro-archive/README.md` に撤去の日付と、写しが元の path に代わる控えになったこと (official の入力へは昇格させない) を注記する (撤去の後)。

## 6. 撤去の手順 (land の後)

1. land 調整役へ `CLEANUP-READY` を送り OK を待つ。他 wave の受入の走行中は、登録を外す操作 (prune) を控える (DW-O11)。
2. 木ごとに撤去直前の占有 (`tools/check_worktree_occupancy.py`)・HEAD 不変・施錠を再確認し、施錠は unlock、branch 付きは detach する。
3. 同じ file system のゴミ置き場 `/work/1/SFC/tanab/tmp/cleanup-trash-20260930/<元 path から作った一意の名>` へ `mv` する (既存の移動先は拒否)。
4. branch は期待 tip の表 (`backup/expected-tips.txt`) と一致するものだけ削除する (main 非祖先 10 本は `-D`、`freeze-g1-gen-t2724` は `-d`)。
5. `git worktree prune --dry-run --verbose` の候補の各管理 entry の `gitdir` が指す元の絶対 path の集合が、自分が移した集合と完全一致したときだけ `git worktree prune` を 1 回打つ
   (scratch2 の管理名が汎用の `repo` なので、名前でなく path で照合する)。
6. 実体はゴミ置き場から背景で 2 本ずつ `tools/cleanup_remove_dirs.py` で消す (Lustre で多並列にしない)。

## 7. 相談と裁定

- 決定役 (Codex sol、consult、reasoning high、read-only) と攻撃役 (Codex luna、同) の出力は `verbatim/s3-consult-sol.md`・`verbatim/s3-consult-luna.md`、親の裁定は `verbatim/s4-ruling.md`。
- 両者とも「残す」系列は 0。割れた点: T-2871 の WAL 回収 (決定役は回収、攻撃役は不要) → 攻撃役を採用。B-5 発効 commit (決定役は tag + bundle、攻撃役は bundle のみ) → 攻撃役を採用。
- 両者が指摘した brief の誤り (前日退避の本数「56 本」は誤りで木ごとの表を正とする、対象集合に fix1/fix2 が漏れていた、prune の照合を管理名だけで行うのは不足、
  「archive の写しが唯一の控え」は job dir の複製を落とした過大な表現) はすべて real として直した。

## 8. 名指しの逆引き

系列ごとの名指しの全数 (file:line・目的の分類・抜粋) は `materials/survey-1.md` (K2・B-5・A-1/A-2・T-2273)、`materials/survey-2.md` (T-2847・T-2849・T-2850・T-2865・T-2871・T-2868)、
`materials/survey-3.md` (T-2724・T-2853 作図・vhb-mw・scratch2・md2) にある。調査は Claude の調査子 3 本 (sonnet、read-only) で、親は判定に使った主な行を開いて照合した。
