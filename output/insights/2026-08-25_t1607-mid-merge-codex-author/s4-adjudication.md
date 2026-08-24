# 段 4 裁定 — [T-1607] mid-merge の作業木を Codex `role=author` へ委任する

親が段 2 プラン、段 3 レンズ A (正しさ境界) / レンズ B (整合・実効性)、および親自身の実測を
突き合わせて裁定する。裁定 inbox は wave 開始時から変化なし (`docs/handoff/` の残 9 file は同一)。

## 0. 裁定の骨子

1. **受理集合の緩和は `stage=author` かつ `sandbox=workspace-write` に限定する** (A1 / B2 採用)。
   受理集合を実際に狭めるのは path 方向ではなく stage 方向だった。
2. **merge 進行中は authority docs の working bytes 比較を行わない** (段 2 の (P4) 採用)。
   ただし 1. の限定下でのみ。親の対案 (案 Q) は A4 で反証されたので取り下げる。
3. **merge 判定は複合 sentinel を厳格版で実装する。octopus は fail-closed で拒否する。**
4. **段 2 が提案した negative control 5 本は全て差し替える。** 案 P のまま緑になり、
   ユーザー必須指定の「承認外の受理を検出する」を満たさないため。
5. **本 wave では目的を完全には閉じられない。** 第 2 の HEAD-byte gate (B1) が残る。
   これは正しさ防壁なので緩めず、限界を明記して裁定パッケージへ送る。

## 1. 所見の裁定

### 採用 (real、scope 内)

| 所見 | 裁定 | 理由 |
|---|---|---|
| A1 / B2 | **real・採用** | `snapshot_authority` は stage を受け取らないため、緩和が plan/consult/author/review/fix/focus の全 6 stage へ開く。T-1607 が要るのは author だけ。**受理集合の縮小として最大の効き。** |
| A4 | **real・採用 (親の対案を撤回)** | 実測確認。wave 側だけが変更した file でも `HEAD != MERGE_HEAD` が真になり、incoming 無変更なのに手編集を素通しする (HEAD `f86b8e88` / MERGE_HEAD `d71b8c26` / base `d71b8c26`)。案 Q の利得は「両側とも無変更」の場合だけで、複雑性に見合わない。 |
| A11 / B5 / B12 | **real・採用** | 複合 sentinel を厳格化: `lstat` で no-follow、通常 file、全行が hex40、重複なし、各 OID が commit object。 |
| A6 / B14 (octopus) | **real・採用 (fail-closed 側)** | MERGE_HEAD が 2 行以上なら**拒否**する。dev-wave の main 取り込みは 2 親のみ。 |
| A9 / A10 / A12 / A13 / B12 | **real・採用** | 段 2 の control 5 本は案 P (無条件 skip) のままで全部緑。恒真に近く、検出力が無い。差し替える。 |
| B6 / B7 / B11 | **real・採用** | 変異 M1 / M2 / M6 は mutant 形が不明確または複合。分割・具体化して登録する。 |
| A14-(1) | **real・採用** | A1 の実装に `tools/codex_worker_launch.py` の改訂が必須なので、同 file と `orchestrator/tests/test_codex_worker_launch.py` を scope へ入れる。 |
| B3 / B4 | **real・部分採用 (手順として)** | receipt は「著者セッションの証拠」であって「競合解決完了の証拠」ではない。親の commit 前検査手順として採用する。機械化は scope 外。 |
| B15 | **real・採用 (手順として)** | docs 是正を採る場合の author 順序と trailer scope を段 6/7 の手順で固定する。 |

### refuted (実測で反証)

| 所見 | 裁定 | 実測 |
|---|---|---|
| A7 (rebase-merges / am / stash で MERGE_HEAD が共存し案 P が任意 bytes を受理する) | **refuted** | 競合させて実測: `rebase --rebase-merges` の merge 再生 = MERGE_HEAD **不在** (REBASE_HEAD + `rebase-merge/`)、`git am --3way` = **不在**、`stash apply` 競合 = **不在**。緩和は `git merge` に限局する。 |
| A7 / B12 の `ls-files -u` 併用案 | **不採用 (追加根拠)** | stash 競合は MERGE_HEAD 無しで unmerged index を残す。`ls-files -u` を sentinel にすると merge でない状態で発火する。 |

### real だが scope 外 → 裁定パッケージ (§5)

B1、A2、A3、A14-(2)、B13 の一部。

### nit

A8 の「clean case A も filter / CRLF / sparse checkout では blob と working bytes が食い違いうる」は
正しいが、**現行実装でも同じように落ちる**ので本 wave の新規拡大ではない。
A8 の「main が触れば落ちる」という親表現の不正確さは受け入れる。正しくは
**「merge 後の working bytes が HEAD blob と異なれば落ちる」**であり、
incoming が最終的に同一 bytes なら通る。§4 の記述をこの形に直す。

## 2. プラン v2 (確定設計)

### 2.1 受理述語

記号: `L` = live 呼出し (`commit is None`)、`C` = 束縛先 commit、`W` = working bytes、
`E(C,W)` = authority docs 2 file の working bytes が `C` の blob と全一致、
`A(C)` = `C` の blob が節・規範行・model mapping として妥当、`V2(C)` = model authority version が v2、
`M` = **健全な 2 親 merge 進行中** (下の署名)、`Cap` = 呼び手が mid-merge 許可 capability を渡した。

```text
ACCEPT = A(C) ∧ (¬L ∨ V2(C)) ∧ (¬L ∨ (M ∧ Cap) ∨ E(C,W))
```

**禁止の署名 (gate の禁止は署名で書く):**

```text
REJECT if  L ∧ ¬E(C,W) ∧ ¬(M ∧ Cap)
```

- **受理する形**: live 起動で、健全な 2 親 merge が進行中であり、かつ呼び手が
  `stage=author` として mid-merge 許可を明示的に渡したとき、authority docs の working bytes が
  HEAD と異なっていても受理する。導出値は常に HEAD blob 由来である。
- **拒否する形**: live 起動で working bytes が HEAD と異なり、かつ
  「健全な 2 親 merge 進行中」と「author capability」の**両方が揃っていない**とき拒否する。

**通る正例 (1 つ)**: wave branch で `git merge --no-commit --no-ff main` を実行して
`docs/dev-wave/operations.md` に競合マーカーが残っている作業木から、`--stage author` で
`tools/dev_wave_codex.py` を起動する。snapshot は成功し、`authority_commit` は wave tip、
model / effort は HEAD blob 由来になる。

### 2.2 `M` (健全な 2 親 merge) の署名

```text
M = let gd = git rev-parse --absolute-git-dir           # worktree 固有
    in  lstat(gd/"MERGE_HEAD") is a regular file        # no-follow。symlink は False
        ∧ 全行が hex40 かつ重複なし
        ∧ 行数 == 1                                    # octopus は fail-closed で拒否
        ∧ その OID が commit object として実在
```

`git rev-parse --verify MERGE_HEAD` **単独を判定に使ってはならない** (同名 branch へ DWIM
解決する。親が実測確認済み)。file 不在だけを正常な `False` とし、file はあるのに内容が
不正なら壊れた merge state として `AuthorityError` で fail-closed にする。

### 2.3 capability の渡し方

`snapshot_authority(repo_root, *, commit=None, allow_mid_merge=False)` を追加する。
既定は `False` で**現行と完全に同じ挙動**。`tools/codex_worker_launch.py` の `_preflight_run`
だけが `allow_mid_merge=(args.stage == "author" and args.sandbox == "workspace-write")` を渡す。
historical 経路 (`commit` 指定) は `allow_mid_merge` を無視する。

### 2.4 不変条件

`AuthoritySnapshot.as_dict()`、digest 定義、receipt schema V4、historical 再構成の一致検査は
**1 bit も変えない** (I1 / I2)。merge 状態を receipt へ記録しない ((P2) 採用) のは、
記録すると closed schema と digest pin を同時に破るためである。

## 3. 変異事前登録 (DW-M01 / B-057)

受理集合を**広げる** wave なので、承認外の受理を検出する変異を主軸に置く。
各変異は「同じ入力を拒否する層が前後に無いこと」「無効化時の赤理由が一つに絞れること」を
段 5 実装後にコードで確認してから本走する。

| ID | mutant (具体形) | KILL する予定のテスト | 単一理由性の懸念 |
|---|---|---|---|
| M1 | `M` の判定から**行数 == 1** の検査だけを外す (他は維持) | `test_octopus_merge_head_is_rejected` | 他層に octopus を拒否する検査は無い |
| M2a | `gd` を `repo_root / ".git"` に置換 | `test_merge_detection_is_worktree_local` | linked worktree では `.git` が file。**path 構築例外で死ぬ可能性**があるため、実装後に「不在扱いで False になる」形かを確認してから登録する (B7) |
| M2b | `gd` を `git rev-parse --git-common-dir` に置換 | `test_merge_detection_is_worktree_local` | common-dir は正常な dir なので False になり、理由が一意 |
| M3 | `M` の判定から **physical file の lstat 検査**を外し、`rev-parse --verify MERGE_HEAD` の成否だけにする | `test_same_named_merge_head_branch_is_not_merge_state` | B6 の指摘に従い「verify 非ゼロは False へ写す」形の mutant として登録し、非 merge live テストが巻き添えで落ちないようにする |
| M4 | `allow_mid_merge` を無視して常に `True` として扱う | `test_non_author_stage_in_mid_merge_is_rejected` | **A1 の中核**。この変異が生きると全 stage へ開く |
| M5 | `(M ∧ Cap)` の分岐を常に `True` にする (= 全 live で bytes 比較を省く) | `test_dirty_working_tree_authority_is_rejected` | 既存テストが一意な理由で殺す (B10 で帰属良好と確認) |
| M6 | `M` が真のとき `resolved` と `raw_documents` を **MERGE_HEAD から**再取得する | `test_mid_merge_binding_target_is_head` | B11 に従い「merge 時だけ差し替える」形に具体化。単に `_resolve_commit` を差し替えると非 merge live 全件が巻き添えで落ちて帰属が壊れる |
| M7 | `M` の判定から **symlink 拒否 (no-follow)** を外す | `test_merge_head_symlink_is_rejected` | A11 / B5 |

M1〜M7 の全件に KILL 予定テストがある。**検出力の穴は現時点で無い**が、実走で SURVIVED が
出た場合は `DW-M02` に従い他層の mask を疑い、実効 gate へ再照準する。

## 4. negative control 登録 (ユーザー必須指定)

段 2 の 5 本は**全て差し替える**。判定基準は「その control が緑でも案 P の無条件 skip 実装が
通ってしまうなら、control として無効」である。

| # | control | 固定する述語 | これが無いと通る誤実装 |
|---|---|---|---|
| N1 | `test_non_author_stage_in_mid_merge_is_rejected` | mid-merge + dirty authority docs で `allow_mid_merge=False` (= plan/consult/review/fix/focus) なら**拒否** | 全 stage へ緩和を開く実装 (= 段 2 の案 P そのもの) |
| N2 | `test_dirty_working_tree_authority_is_rejected` (既存を強化) | 非 merge + dirty なら拒否。例外文言 `working tree が authority commit と異なる` まで固定 | merge 判定と無関係に bytes 比較を消す実装 |
| N3 | `test_same_named_merge_head_branch_is_not_merge_state` | branch `MERGE_HEAD` が在り physical file が**不在**のとき `M=False`。control 内で「`rev-parse --verify` は成功する」「physical file は無い」を先に assert する | `rev-parse --verify` の成功だけを sentinel にする実装 |
| N4 | `test_octopus_merge_head_is_rejected` | MERGE_HEAD が 2 行なら、author capability があっても**拒否** | 先頭 1 行だけ読む実装 |
| N5 | `test_merge_head_symlink_is_rejected` | MERGE_HEAD が symlink なら拒否 | `stat` (follow) を使う実装 |
| N6 | `test_malformed_merge_head_is_rejected` | 1 行目が有効 OID・2 行目が不正文字列、空 file、非 hex、実在しない OID のいずれも拒否 | 先頭行だけ検証する実装 |
| N7 | `test_merge_detection_is_worktree_local` | sibling linked worktree が merge 中でも親 checkout は `M=False`。同一 worktree で before / during / after abort を連続検査する | common-dir を見る実装、状態を cache する実装 |
| N8 | `test_mid_merge_binding_target_is_head` | HEAD / MERGE_HEAD / working に**異なる有効な** model・effort を置き、live snapshot が HEAD の historical snapshot と完全一致する | 束縛先を MERGE_HEAD へ移す実装 |

**N1 が本 wave の要石である。** ユーザー指定の「承認外の受理を検出する negative control」は
第一に N1 が担い、N3〜N7 が sentinel の偽陽性側を塞ぐ。

正例 (positive) は 2 本置く。`test_mid_merge_conflicted_authority_author_is_accepted` と
`test_mid_merge_clean_auto_merged_authority_author_is_accepted` (ケース B / ケース D)。
後者は `ls-files -u` を sentinel にする誤実装も殺す。

## 5. 裁定パッケージ (ユーザーへ返す。本 wave では実装しない)

### 5.1 【重要】B1 — 第 2 の HEAD-byte gate が残るため、目的は完全には閉じない

`tools/check_codex_hooks.py` の `_validate_pinned_guard_bytes` は、次の 5 file の working bytes を
**HEAD blob と比較**し、drift があれば子を spawn しない (`.codex/hooks.json` も exact 構造検査)。

`hooks/codex_guard.sh` / `hooks/guard_write.py` / `hooks/guard_bash.py` /
`tools/pegasus_admission_registry.py` / `tools/pegasus/admission_registry.json`

**したがって、main 取り込みがこれらの file を触る merge では、本 wave の修正後も
Codex へ委任できない。** 親 brief §0 の「launcher 側に他の clean-tree gate は無い」は**誤り**で、
撤回する (grep を `codex_worker_launch.py` 内に限ったため、別 module の gate を見落とした)。

**残余の大きさを実測した** (2026-08-01 以降、main の 4991 commit のうち):

- authority docs 2 file を触る commit: **83 件**
- pinned guard 5 file + `.codex/hooks.json` を触る commit: **30 件**

本 wave は支配的な原因 (83 件側) を閉じ、30 件側は残る。

**この gate は緩めてはならない。** guard 自体の byte 同一性を守る正しさ防壁であり、
mid-merge を理由に緩めることは絶対規律 2 に抵触する。閉じるなら「working guard を信用せず
HEAD-pinned guard を実行する」別設計が要り、本 wave の 2 file 変更へ混ぜられない。

**ユーザー裁定を求める点:** 30 件側も閉じる別 wave を起こすか、fail-closed のまま運用するか。

### 5.2 A2 — 子が読む規範は working tree であり、凍結されていない

snapshot が全文比較しているのは authority docs 2 file だけで、導出しているのはその 4 節だけである。
merge 中に比較を外すと、`DW-S05-B` のような**同じ file の非導出節**を書き換えた working tree を
子が読む余地が残る (他の docs は元から比較外)。恒久対応は「HEAD blob から作った凍結規範を
子の governing input にし、working docs は編集対象データとして分離する」設計。scope 外。

### 5.3 A3 — snapshot と spawn の間の TOCTOU

snapshot 後、prompt 読取り・hook 検査・`codex --version` を経て spawn する。この窓で
authority docs を書き換えられる。**現行でも同じ窓がある**ので本 wave の新規欠陥ではないが、
merge 中は bytes 比較が無くなるぶん影響が見えにくくなる。恒久対応は 5.2 と同じ凍結入力設計。

### 5.4 A14-(2) — 起動時 admission の provenance が receipt に残らない

receipt は HEAD snapshot しか持たないため、後日「どの merge admission で通ったか」を再検証できない。
記録するには receipt schema V5 か closed な sidecar が要り、I1 / I2 と正面衝突する。scope 外。

### 5.5 B3 / B4 の機械化

receipt の accepted は「競合解決が完了した」ことを証明しない。本 wave では親の手順として
採用する (§6) が、機械化 (親の `add` 前後の検査を tool 化する) は scope 外。

## 6. 本 wave で親が守る手順 (B3 / B4 / B15 の手順部分)

1. author 子が accepted かつ `stage=author` の receipt を返したことを確認する。
2. 親が `git ls-files -u` が空、conflict marker 不在、`git diff --cached` が意図した解決、
   所有対象外に予期しない差分が無いことを確認する。
3. HEAD と MERGE_HEAD が子の起動時から不変であることを確認する。
4. merge commit message に Codex `role=author` と親 `role=integrator` の `AI-Agent:` 行を置く。
5. docs 是正を行う場合は docs author を**最後**に置き、親が commit して authority を新 HEAD へ
   固定してから段 6 の review 子を起動する (B15。さもないと review 子が working-vs-HEAD gate で落ちる)。

## 7. 段 5 の所有分割

実装単位は 1 つ。1 author 子が次を一括所有する (file 集合は素集合)。

- `tools/dev_waves/launch_authority.py` — `M` の署名、capability 引数、live 受理述語
- `tools/codex_worker_launch.py` — `_preflight_run` から capability を渡す 1 箇所のみ
- `orchestrator/tests/test_dev_wave_launch_authority.py` — mid-merge fixture、正例 2 本、N1〜N8
- `orchestrator/tests/test_codex_worker_launch.py` — stage 限定の統合検査

docs 是正は本 wave では**行わない** (§5.1 の撤回内容は worklog と insight に記録し、
`DW-C01` / 台帳 note の誤った因果の是正は段 8 で routing 先を裁定する)。
