# 段 6 レビュー裁定 — [T-1279]

親 / 2026-08-17 10:15 JST

## must-fix (実装する)

### MF-1 — certifying 入口の受理集合を wave 前へ固定する (レンズ A [重大] の核)

レビュー A は `campaign_dir.is_relative_to(_DEFAULT_OUTPUT_ROOT.parent)` が
「official か exploration か」の権威ある区別ではなく、現在の source worktree の物理 path 判定に
すぎないと指摘した。**real と裁定する。**

ただし判定の作り直しは採らない。裁定 (ユーザー) は「repo 外 campaign でも失敗しない形にする」
ことを**要求している**ので、非 certifying の `build_report` が repo 外で成功するようになるのは
指示どおりの変更である。問題は、その緩和が `build_accepted_report` (certifying 入口) へも
自動的に漏れることである。ここは指示されていない。規律 2 に従い、certifying 入口だけ
wave 前と同じ受理集合へ固定する。

親が独立に確認した事実: `build_accepted_report` は `_resolve_campaign_dir` で resolve した
campaign を `build_report` へ渡す。wave 前はその `build_report` が `_git_head(resolved_campaign)`
を呼んでいた。したがって `build_accepted_report` 側で `generated_from_head is None` のときに
`_git_head(resolved_campaign)` を呼んで確定させれば、**値も例外型も wave 前と同一**になる。

### MF-2 — 新規テストの検出力不足 (レンズ B [重大] 2 件、レンズ A [低])

`_campaign` fixture が作る v2 lock の `contract_loader_commit` は現在の source HEAD から
作られているため、fallback を「lock pin を返す」から「source repo の HEAD を返す」へ壊しても
新規テストが全部通る。**real と裁定する。**

修正:
- repo 外 v2 テストの lock pin を、**現在の source repo HEAD とは異なる固定 hex40** にする。
- 同テストと v1 負例テストに、campaign directory が (a) source repo の外側であり、
  (b) git 祖先を持たないことの前提 assert を足す。前提が崩れた環境では緑ではなく赤にする。

### MF-3 — 変異事前登録の期待 node が不完全 (レンズ A [中]、レンズ B [重大] 2 件)

M-2 と M-4 の期待 node に、8c E2E node と repo 内 fail-closed node が漏れている。**real。**
期待 node は完全集合でなければならない (DW-M08)。fix 後に全件 SURVIVED 期待の probe を走らせ、
観測 node から完全集合を再導出して本走する。

### MF-4 — 変異 M-7 の追加 (レンズ B の提案)

「lock pin の代わりに source repo HEAD を返す」変異を M-7 として登録する。MF-2 の fixture 修正が
入って初めて KILLED になる。MF-2 が本当に効いたことの証拠になる。

## nit / 不採用

- レンズ A [低] `_git_head` の `UnicodeDecodeError` 素通り: `_git_head` は本 wave で未変更であり、
  既存の性質。新しい防御を足すのは「厳密化しない」裁定に反する。**backlog**。
- レンズ B の M-8 (`except Exception` への拡大変異): 上と同じ理由で production を変えないため、
  変異としても登録しない。**不採用**。
- レンズ B [中] monkeypatch 除去による git-success full-chain 被覆の消失: 焦点テスト
  `test_git_backed_campaign_head_precedes_v2_lock_authority` が git-success 優先を pin しており、
  成果物影響を 1 行で書けない。**nit のまま**。
- レンズ B [低] 同一 node 内で build_report と render を続けて呼ぶ件: 診断の粒度の話であり
  受理集合を変えない。**nit のまま**。

## scope 外の real 所見 (ユーザーへ返す裁定パッケージ候補)

1. **CLI から repo 外 campaign を render できない** (レンズ A [高]、`layer3_report.py` の CLI)。
   `_resolve_campaign_dir` が `output_root` の親の外を拒否し、CLI には `--output-root` が無い。
   これは `_git_head` とは別の層の制限で、本 wave の scope (rc=128 で必ず失敗する件) の外。
   直すには CLI に新 option を足す = 受理集合の設計判断が要る。
2. **8c E2E が標準 producer でなく test helper で v2 lock を直接書いている**
   (レンズ B [高]、`test_p3_autonomous_workload_trial.py:157,209-211`)。標準 8c producer が
   v1 lock を作る退行をこの E2E は検出しない。既存のテスト構成の問題であり本 wave が作った穴ではない。

## 親 brief の訂正 (両レンズが独立に反証)

brief の「探索 campaign は機械的に必ず repo 外に置かれる」は**過大**である。
`layout._resolve_exploration_output_root` は、探索用 output root の環境変数が未設定なら
`repo_output_root()` (repo 内 `output/`) を返す。repo 外強制が働くのは環境変数を設定した経路だけ。

正しい記述: **探索用 output root を repo 外へ設定した構成 (8c の意図された運用形態) では、
`_has_git_ancestor` により repo 外が強制され、layer3 レポート生成が必ず rc=128 で倒れる。**
環境変数未設定なら repo 内へ落ちるので git HEAD が取れて倒れない。

この訂正は修正の方向を変えない (repo 外構成で倒れることは worklog 622 の裁定前提そのもの) が、
worklog へはこの訂正済みの記述で残す。
