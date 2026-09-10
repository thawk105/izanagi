# 段 1 brief — [T-1607] mid-merge の作業木を Codex `role=author` へ委任できるようにする

wave: `dev-wave-t1607-mid-merge-codex-author` / branch: `worktree-dev-wave-t1607-mid-merge-codex-author`
base: `16086f12` (main) / 実行環境: login node (計算ノード不要、pytest のみ)

## 0. 実測で判明した前提の訂正 (段 4 で明示的に再裁定する)

起票文と台帳 note は「authority-snapshot 検査が **mid-merge・conflict マーカーありの**
working tree を拒否する」と述べる。実装 (`tools/dev_waves/launch_authority.py:419-434`) に
mid-merge も conflict マーカーも判定材料として**存在しない**。独立 clone での実測 5 ケース:

| # | tree 状態 | 結果 |
|---|---|---|
| A | clean | OK |
| B | mid-merge・authority doc に競合マーカーあり | `AuthorityError: ... working tree が authority commit と異なる` |
| C | mid-merge・authority doc をどちらの側も触っていない | **OK** (`MERGE_HEAD` あり、merge rc=0) |
| D | mid-merge・authority doc が競合なく自動 merge された | `AuthorityError` (B と同一メッセージ) |
| E | merge を commit 済みで clean | OK |

実際の拒否述語は「`commit is None` の live 呼出しでは authority docs 2 file
(`docs/dev-wave/operations.md`, `docs/dev-wave/workers.md`) の working tree bytes が
HEAD blob と一致すること」だけである。main 取り込み中は HEAD が wave tip のままなので、
main 側がこの 2 file を触っていれば**競合の有無に関わらず**落ちる。逆に 2 file を誰も
触っていない mid-merge tree は今日でも委任できる (ケース C)。launcher 側に他の clean-tree
gate は無い (`tools/codex_worker_launch.py` に `porcelain` / `MERGE_HEAD` 検査 0 件)。

台帳件数も訂正する。起票文の「11 件」に対し、note に `親作成 merge のため Codex 著者とは
記さない` を持つ entry は**実測 7 件** (`KNOWN_PROVENANCE_VIOLATIONS` 全体 53 件、
`python3 -c` で tuple を実 import して計数)。

`MERGE_HEAD` の到達可能性 (DW-O13) も実測した。linked worktree では
`git rev-parse --git-dir` = `<common>/worktrees/<name>` 側にだけ `MERGE_HEAD` が存在し、
common-dir 側には存在せず、親 checkout からは見えない (`fatal: Needed a single revision`)。
`git rev-parse --verify MERGE_HEAD` は worktree scope で正しく効く。
**`(repo_root / ".git" / "MERGE_HEAD")` の直接 path 判定は linked worktree で必ず偽になる**
(`.git` は file)。

## 1. scope と成果物影響 (DW-G05)

- **S1.** `snapshot_authority` の live 経路に、merge 進行中の受理条件を足す。
  成果物影響: 受入前 local main 取り込みの競合解決が Codex `role=author` として記録できるようになり、
  取り込み 1 回ごとに known-violation 台帳へ 1 entry 増える現行の生成器が止まる (実測 7 件の増分源)。
- **S2.** 受理集合の拡大を固定する negative control をテストへ登録する (ユーザー必須指定)。
  成果物影響: 承認外の受理が緑のまま通ると、launch 値が commit 由来でない docs から導出され、
  receipt の `authority_commit` が実際に適用された規範と乖離して provenance 監査が無意味になる。
- **S3.** docs 正本の是正要否は段 4 で裁定する (現時点では scope 内・未確定)。
  成果物影響: 是正しない場合、台帳 note と `DW-C01` が誤った因果 (「conflict マーカーが原因」) を
  述べ続け、次の wave が同じ誤診断から出発する。

## 2. 不変条件

- **I1.** `AuthoritySnapshot.as_dict()` の shape と digest 定義を変えない。pin は
  `orchestrator/tests/test_dev_wave_launch_authority.py::test_authority_snapshot_serialized_contract_and_digest_are_unchanged`、
  再導出は `tools/codex_worker_launch.py:4243-4253` の historical 一致検査、消費は
  `tools/dev_wave_land.py` (7 hit) と `tools/codex_worker_ledger.py` (8 hit)。
- **I2.** receipt の top-level schema は closed frozenset (`_RECEIPT_FIELDS_V4`、`schema_version: 4`)。
  top-level field 追加は validator・land・ledger の全消費者を同時に変える。
- **I3.** 導出値 (model / effort) は現行どおり**常に commit 由来 blob** から parse する。
  working tree を parse する経路を作らない。
- **I4.** merge 進行中でないときの挙動を 1 bit も変えない
  (`test_dirty_working_tree_authority_is_rejected` は緑のまま)。
- **I5.** D721 を覆さない。手で競合解決した merge を実装面から除外する免除は作らない。
  本 wave は逆に Codex author を**可能にする**方向であり、D721 の却下理由と整合する。
- **I6.** D95: 実装面は Codex `role=author` が書く。親は brief・裁定・統合 commit・全走・記録だけ。
- **I7.** 迂回禁止 (ユーザー確定裁定)。既存 `commit is not None` の historical 経路へ live 起動を
  流し込む形は、working tree 比較と v2 必須を同時に外すため採らない。

## 3. 親の provisional 裁定 (攻撃対象)

- **(P1)** merge 進行中の binding 先は **HEAD (wave tip)** とする。理由: wave はその規範の下で
  走ってきており、merge はまだ採用されていない transaction である。
  代替は MERGE_HEAD 側、または {HEAD, MERGE_HEAD} のうち working tree bytes と一致する側を選ぶ形。
- **(P2)** merge 進行中であった事実を receipt へ**記録しない**。理由: I1/I2 を守るため。
  受理集合の可視化は negative control 側で担う。代替は schema V5 を起こして記録する形。
- **(P3)** 検出 sentinel は `git rev-parse --verify MERGE_HEAD` の成否とする (path 直読みは不可、§0 実測)。
  代替は unmerged index entry (`git ls-files -u`) の有無だが、これはケース D を取り逃す。
- **(P4)** merge 進行中は authority docs の working tree bytes 比較を**行わない** (bytes を無視する)。
  導出は I3 により HEAD blob からなので launch 値は汚染されない。
  代替は「HEAD と一致するか、または MERGE_HEAD と一致するときだけ通す」狭い形 (ケース B を取り逃す)。

## 4. 成果物の形

`tools/dev_waves/launch_authority.py` の live 分岐 1 箇所の改訂と、
`orchestrator/tests/test_dev_wave_launch_authority.py` への正例 1 + negative control 群。
docs 是正は段 4 の裁定次第。実装面は 1 単位 = 段 5 の Codex author 1 本で足りる。

## 5. 変更面アンカー

| anchor | 役割 |
|---|---|
| `tools/dev_waves/launch_authority.py:419-434` | live 分岐と working tree 比較 (唯一の改訂点候補) |
| `tools/dev_waves/launch_authority.py:363-379` | `_git` helper (`rev-parse` 追加の受け皿) |
| `tools/dev_waves/launch_authority.py:381-389` | `_resolve_commit` (binding 先の決定点) |
| `orchestrator/tests/test_dev_wave_launch_authority.py:104-132` | `_prepare_repo` fixture (mid-merge fixture の土台) |
| `orchestrator/tests/test_dev_wave_launch_authority.py:397-403` | `test_dirty_working_tree_authority_is_rejected` (I4 の番人) |
| `orchestrator/tests/test_dev_wave_launch_authority.py:174-191` | as_dict / digest pin (I1 の番人) |
| `tools/codex_worker_launch.py:2632` | live 呼出し点 (`_preflight_run`) |
| `tools/codex_worker_launch.py:4243-4253` | historical 再構成一致検査 (I1 の消費者) |

## 6. 並列分割

段 2 プラン 1 本 → 段 3 敵対相談 2 レンズ (sol / luna) → 段 4 裁定 → 段 5 author 1 本 →
段 6 敵対レビュー 2 本 + fix + 変異 matrix + 受入。
本 wave は**受理集合を変え、正しさ防壁に触る**ため `DW-C00` の軽量版に該当せず、
段 2・3 と段 6 review 子を省略しない。
