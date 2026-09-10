# 段 1 brief — [T-2009] 検査器の弱体化を挙動で捕まえられているかの実測

base main = `28ebff456b9f57a927854950b5030fa77aec6529` / branch = `worktree-dev-wave-t2009-checker-mutation-power`

## scope

D799 決定 (2) は「現行の緑赤対が排除するのは定数 verdict 実装 2 種だけで、次の 5 つは通る」と
**予測だけ**を記録している。本 wave はこの 5 つを実際の変異として書き、既存テストが落ちるかを
実測する。落ちなければ規律 7 が開けた穴として特定し、**塞がずに** insight + 裁定へ返す。
D387 (同一権限主体の共謀改変は repo 内の検査で塞げない) は前提。対象は事故的退行の検出力に限る。

## 確定済みユーザー裁定・前提

- 規律 2 を緩めない。既存テストの期待値・受理集合を一切変更しない。
- 仮想リスク向けの gate・検査・台帳・一般化を足さない (`DW-G05`)。本題の実測だけ。
- 変異は `tools/mutation_worktree.py` + `tools/mutation_harness.py` の固定 commit 隔離走行で行い、
  repo の tracked file は 1 byte も変えない。
- 実装面 (D95) が生じる場合は Codex `role=author` が書く。親は docs 本文だけ書く。

## 実測した新事実 (brief 時点、裁定へ影響する)

**(F-new1) verifier の 7 source file はすべて `CONTRACT_LOADER_RELATIVE_PATHS`
(`orchestrator/campaign/campaign_lock.py:49`) に載っている** — `core.py` / `dsg.py` / `model.py` /
`parse.py` / `__init__.py` / `report.py` / `commit_receipt.py`。これは HEAD blob の**同一性 pin**
であり、verifier を触る変異はすべて数百件の contract-loader drift 赤を引く (実測前例: `pipeline.py`
で 384 件)。**この層は「変わったか」しか言えず「効いたか」を言えない**ので、規律 7 が要求する
挙動検出とは別物である。測定では drift 群を分母から外し、外したこと自体を結果として書く。

**(F-new2) `orchestrator/tests/fixtures/README.md` (145-190) は 5 件のうち 2 件について
「別のテストが担う」と既に注記している** — 分類器の定数 `G2` は `test_verifier.py:1374`
`test_classify_branches`、epoch 無視は `r6_epoch_version_order` / `r7_epoch_rw_successor`
(同 1798 / 1809) が担い、長さ 4 以上の巡回は「どの fixture も担っていない」と明記する。
D799 決定 (2) の 5 件は **g6/r8 の対**の射程の話であって、既存スイート全体の射程ではない。
よって本 wave は「穴探し」ではなく、**この注記が実測で成立するかの検証**になる。
期待は M1・M2 が KILLED、M3 が SURVIVED、M4・M5 は未知。**外れた向きこそが所見である。**

**(F-new3) 起票時の「唯一の穴」という表現は成立しない。** 起票正本は「落ちなければ、そこが
規律 7 が開けた**唯一の**穴として特定される」と書くが、D799 は候補を 5 つ挙げており、
実測結果は最大 5 箇所になりうる。command 引数側は既に「穴」と直されている。引数を採る。

## 不変条件

- repo の tracked file を変更しない (変異は scratch worktree の固定 commit 上だけ)。
- 変異走行中は親も worktree へ書かない (`mutation_worktree.py` の共有木前後照合が落ちる)。
- `--source-repo` は独立 clone にする (並行 wave の churn で rc=125 になるため)。

## 成果物

1. 変異 matrix: 5 予測 + 正例対照 + 等価対照 について、`KILLED` / `SURVIVED` と失敗 node 完全集合。
2. insight (`docs/insights/`): 実測表と、同一性 pin 層と挙動検出層の分離。
3. worklog / decisions fragment (`docs/spool/`)。穴は塞がず裁定パッケージへ返す。

## 変異の実アンカー (段 2 で file:line 粒度へ確定させる)

| id | D799 の予測 | アンカー |
|---|---|---|
| M1 | 分類器が常に `G2` を返す | `orchestrator/verifier/dsg.py` `DSG._classify` (232-250 付近) |
| M2 | 版比較が epoch を無視する | `dsg.py` の版順序 (`self.versions` の構築と `bisect_left/right`) |
| M3 | 長さ 4 以上の巡回を無視する | `dsg.py` `anomalies` (252-) の `sccs` |
| M4 | framing violation を常に 0 にする | `orchestrator/verifier/core.py:65` |
| M5 | fixture の hash で結果を返す | `core.py` `verify_trace_dir` 入口 |
| P1 | (正例対照) rw 辺を落とす | `dsg.py` `_add_read_edges` の anti-dependency |
| E1 | (等価対照) 意味を変えない置換 | 段 2 で選ぶ |

P1 は D799 決定 (1) の `r8_silo_broken_norw` が殺すはずの向きで、**harness と分母に検出力が
あること自体の正例**である。E1 は harness が `SURVIVED` を報告できることの正例。

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1-A) 分母の取り方。** 親案は「verifier を behavioral に叩く test file の参照閉包」
  (`test_verifier.py` + verifier を import する 11 file + mocc 系) で、contract-loader drift 群は
  同一性層として分母外。**分母を狭く取れば穴を過大に、広く取れば同一性層で全件 KILLED に見える。**
- **(P1-B) M5 (hash で答えを返す) は定義上必ず生存するのではないか。** 生存しても情報量が
  あるのか、対照として書き方をどう決めるか。
- **(P1-C) kill の意味 (`DW-M03`)。** 受理集合が期待方向へ変わった赤だけを kill と数える。
  診断文字列だけの赤、golden bytes 照合だけの赤 (D799 決定 4 の node 分離) は kill にしない。
- **(P1-D) 分類器 (M1) は verdict に効かない。** `_classify` の docstring 自身が「verdict は
  cycle の有無だけで決まり分類に依存しない」と書く。これが真なら M1 の生存は穴ではなく
  設計どおりであり、「穴」と記録するのは誤りになる。段 2 で受理集合への影響を確定させる。

## 分割方針

段 2 (plan 1 本) → 段 3 (敵対 2 本、レンズ = 分母の誠実さ / 変異の帰属と kill 意味論) → 段 4 裁定
→ 実装面が spec (repo 外 JSON) だけなら段 5・6 の実装子は不要、親が変異を走らせる。repo 内へ
入る実装面が生じたら Codex author を立てる。
