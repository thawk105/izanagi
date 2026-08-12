# 凍結チェーン保留の残余執行と、保留の統合一覧 (2026-08-12)

wave = `dev-wave-freeze-hold-residual` / branch `worktree-dev-wave-freeze-hold-residual`。
ユーザー依頼は「[T-917] 凍結チェーン検証の保留執行」だったが、**着手前の実測で land 済みと確定**し、
scope を同じ裁定下の未実施残余へ移した。

## 1. 依頼の前提を実測で覆した (再実装の回避)

| 主張 | 実測 |
|---|---|
| [T-917] は未執行 | **執行済み。** 裁定 D328 は cherry-pick `68c83c2d` で main へ入り採番済み |
| 実装は無い | `orchestrator/campaign/freeze_verification_hold.py` が実在。`HELD=True` / 保留 check_id 21 件 / `HELD_CHECK_IDS_SHA256` 自己 pin / 機械可読 `REASON` |
| 受入が赤のまま | `54018867` (18:24 JST) で残り 4 件も解消 |
| 台帳機構が要る | growth-tests wave が land 済み (30 entry、`provenance-chain` 軸の枠も用意済み) |

## 2. 敵対 2 本が [T-913] を止め、親が一次資料で裏を取った

段 3 sol は **STOP 推奨**、luna は同じ点を BLOCKER。段 6 レビュー B が再攻撃しても覆らなかった。

| 根拠 | 一次資料 |
|---|---|
| 4 function は成長比例ではない | `test_t793_publication_ledger.py:31-41` の `_init_repo` は `tmp_path` に固定サイズ repo を作る。実 repo を走査しない |
| D335 (成長比例保留) の対象外 | 上記より |
| D328 (凍結検証保留) の対象外 | 4 件は `ledger.py:228-252,311-361` の fail-closed 拒否境界の唯一検出者。D328 は正しさゲートと防壁の自己完全性を対象外と明記 |
| 起票根拠の D320 は授権でない | D320 本文に「live な検査を黙って外す授権ではない」「既存機構の撤去・緩和は個別裁定で行う」。個別裁定は不在 |
| 取引が成立しない | 保留の利得 0.14 秒 (4 件とも直列鎖の外)。失うのは唯一検出者 |

**非 test caller ゼロは親が独立に検算した** — `read_publication_ledger` /
`canonical_publication_ledger_path` / `from orchestrator.publication.ledger` の全 hit は
同 file 内定義と当該 test file のみ。`tools/spool_fold.py:1288` は同 package の別 module
`approval_guard` を import しており、`approval_guard` は `ledger` を import しない。
`tools/task_runs/ledger.py` と `tools/dev_waves/ledger.py` は同名の別 module。

第 4 束の「判定に迷う項は保留せず一覧でユーザーへ返す」に従い**据置**とした。

## 3. 親の provisional 裁定 (P1) は refuted された

親は `correctness_gate: false` で入れる予定だった。両レンズが独立に否定 —
`conftest.py:359-369` は flag の値を見ずに skip するため、`False` は**検出力を残さず
ユーザー向け一覧から隠すだけ**になる。

## 4. 焦点走が緑でも全走が赤になる欠陥は、レビューだけが捕まえた

新規 test file に自走経路が無く、
`test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted` が
**1 failed** (実測 `907714.nqsv`)。**親の焦点走 4 passed はこの検査を含んでいなかった。**
素の script 起動も `rc=1` (`ModuleNotFoundError`)、module 起動のみ rc=0 だった。

## 5. blacklist は保証手段にならない (実証)

段 6 レビュー A は、禁止語に当たらない完全性主張文を実際に書いて素通りを実証した。

```text
This inventory enumerates every hold layer, including layers unknown to the registry.
```

fix で human は独立な期待 line sequence との exact 比較、JSON は key 集合の exact 固定へ変えた。
焦点再レビューは更に「入れ子の `reason` へ 1 対足せば human も JSON も同じ値へ追随する」を
突き、全 nested object の key と非 source-derived 値を canonical literal で固定して閉じた。

## 6. 変異 — 初回 3 件 MISMATCH → 再導出して 6/6

| # | 変異 | 最終 |
|---|---|---|
| M1 | json dispatch を破壊 | KILLED (3 node) |
| M2 | completeness literal を弱体化 | KILLED (3 node) |
| M3 | 解除 token を誤らせる | KILLED (1 node) |
| M4 | 解除条件を `automatic` へ緩和 | KILLED (1 node) |
| M5 | 素の runner bypass 記載を除去 | KILLED (1 node) |
| M6 | `effective_status` を恒真固定 | KILLED (2 node) |

初回走は `mutation-out-probe1.json` に保存した。M1 と M2 は**期待より多くの node を発火**
(検出力が想定超過)、M5 は逆に 1 node だった。

**M5 の縮小は構造の発見。** human 検査は inventory から期待値を作るため source の改竄に追随して
発火しない。捕まえるのは source 集合比較の側だけ。**human 比較は renderer の壊れ方を見る道具**で
あり (M1 が実証)、source projection の oracle ではない。

## 7. 受入 wall

| 走行 | 値 |
|---|---|
| 保留導入**前** (worklog 478、tip `7b6f91a8`、別日) | 186.38 秒 |
| **本 wave before** (tip `ff97b574`、nproc 96、ccbench `511c9538`) | **9994 passed / 65 skipped / 129.50 秒 / rc=0** |
| **本 wave after** (最終 tip) | 下記「after」参照 |

before/after は同一機体・同一 worker 数・同一 runner 引数で測る。
本 wave の追加は 4 node (最終 6 node) でいずれも `@real-repo` 直列鎖の外。
**1 走の差を効果と断じない** — 同 repo の並列走では共有資源を先に掴んだ node が
コストを全計上するため per-node 秒が入れ替わる実測がある (worklog 478)。

## 8. 待ち手の偽完了を 2 度観測した

背景待ち手が `exit 0` を返したのに成果物も `.done` も無く producer が生存している事象が
段 6 の review A と fix で 1 度ずつ。待ち手自身の出力は 0 bytes。
**3 点照合 (成果物実在 + `.done` + producer 死) で偽と判定し、破壊的操作をせず再武装**した。
fix では前景待機へ切り替えて解決した。

## 逐語

`verbatim/` に段 2 プラン、段 3 敵対 2 本、段 4 裁定、段 5 実装報告、段 6 レビュー 2 本・
fix 2 巡・焦点再レビューを凍結した。変異 spec と結果 (初回 probe を含む) は同 directory 直下。
