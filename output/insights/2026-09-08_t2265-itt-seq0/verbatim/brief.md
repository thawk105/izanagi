# 段 1 brief — dev-wave t2265-itt-seq0

worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0`
branch: `worktree-dev-wave-t2265-itt-seq0` / base main `c5754d1f4b3d915f2e55615e69674190f48c69a8`

## 0. 目的 (ユーザー確定)

反実仮想 ITT の主判定を確認的に出す。「`seq = 0` を位置だけで除く」規則を**結果より先に**事前登録へ
凍結し、**既存の 12 成果物をそのまま再解析**して確認的判定を出す。計算ノードへの再投入はしない。
除外規則は解析を回す前に凍結し、凍結したことを成果物で示す (規律 3)。

余力があれば副題として、driver の共通 `not_certified` 文言が診断成果物と矛盾している件を直す。

## 1. 一次資料 (すべて main c5754d1f4 の現物で確認済み)

- `output/insights/2026-09-07_t2265-backoff-itt/README.md` §3・§4・§10 (前 wave の凍結記録)
- `docs/backoff-counterfactual-preregistration.md` — **v1、sha256
  `ee7617f57bf6816fd8bfb42b5830926be1174ebcca617ed122c3fbca62f127a6`** (実測)
- `orchestrator/campaign/backoff_counterfactual_analysis.py` — sha256 `90f616eab1e0…` (実測)
- `orchestrator/tests/test_backoff_counterfactual_analysis.py` — sha256 `36ebfca5a837…` (実測)
- `docs/archive/worklog-phase3-0908-1328.md` (entry 1328)
- 成果物 12 件: `/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-itt/stage2-rep0-0_98*.nqsv.json`
  (実在を `ls` で確認、12 file + 12 journal)

**着手前の済み照合:** main 上の事前登録は今も v1、解析器・テストも前 wave の bytes のまま。
別 session が本件を着地させてはいない。

## 2. scope (やること)

1. **事前登録を v2 へ改訂して凍結する。** 文書自身の §0 が定める改訂手続き (旧版を Git 履歴に残し、
   新しい commit で行い、変更理由と時点を §0 に明記) に従い、in-place で編集する。
   加える規則はユーザーが名指しした 1 つだけ: **`seq = 0` の event を位置だけで除く。**
2. **解析器を v2 規則へ合わせる。** 位置除外と、`window_commits = 0` 判定の適用範囲を、
   除外後に残る event へ限定する。層別の index 基準も残存集合で数え直す。
3. **12 成果物をそのまま再解析し、`analysis-result.json` を新しい insight dir へ出す。**
4. **凍結の順序を成果物で示す。** commit 順 (事前登録 v2 → 解析器 → 結果) と、前 wave が
   「seq 0 を除いた推定値は計算していない」と main へ着地済みである事実を insight に書く。

副題 (余力があれば、段 4 で採否を裁定): 5. `not_certified` 文言の是正。

## 3. scope 外 (実装しない)

- 計算ノードへの再投入・新規測定。12 成果物は凍結済みで束縛も揃っている。
- **`seq = 0` 以外の除外規則の追加。** 特に `seq = 10 / 11` の `window_commits = 0` 2 件は
  処置後の outcome による除外にあたるため、v1 の「残れば主判定を inconclusive にする」を維持する。
- policy≠0 の直列性認証、trace 無効の性能測定 (前 wave が scope 外と裁定済み)。
- 仮想リスク向けの gate・検査・台帳・一般化の新設 (ユーザー明示)。

## 4. 割れうる前提 — 親の provisional 裁定・攻撃対象

- **(P1) 事前登録は in-place で v2 へ改訂する。** 別 file の addendum ではなく、文書 §0 が自ら
  定めた改訂手続きに従う。→ 文書の bytes が変わり sha256 も変わる。
- **(P2) 解析器は事前登録 sha を 2 つに割る。** 12 成果物が `counterfactual_preregistration` に
  記録しているのは **v1 の sha** であり、これは測定時点の事実として動かない。一方、解析規則の
  正本は v2 である。したがって「成果物が記録している値 (v1 literal)」と「渡された事前登録 file に
  要求する値 (v2 literal)」を別の module 定数として pin する。現行は
  `_load_artifact(path, expected_hash=preregistration_sha256)` で同一視しており、そのままでは
  12 件すべてが不適格になる。
- **(P3) 位置除外は event 0 を完全に外す。** 分子・分母どちらとしても使わない。よって最初の
  outcome 対は `(event1, event2)` になる。
- **(P4) `window_commits = 0` の判定は残存 event に限る。** ここを直さないと 55 件の seq 0 が
  そのまま発火し、規則を凍結した意味が消える。
- **(P5) 副題の `not_certified` は診断用と性能用で文言を分ける。** 既存の凍結済み性能成果物は
  現行文言を記録しており、`_performance_artifact_identity` (probe:1770) が exact 一致を要求する。
  性能側の文言は 1 byte も変えず、診断側 (`backoff_trace` 真) にだけ新しい文言を使う。
- **(P6) 主判定は inconclusive のまま出る可能性がある。** `seq = 10 / 11` の 0 commit 2 件が
  主層に落ちていれば、規則どおり判定不能になる。**どちらに転んでも規則を変えない。**
  親はこの 2 件がどの層にあるかを、規則を凍結するまで調べない。

## 5. 不変条件 (破ってはいけない)

- **規律 3。** 規則の凍結は解析の実行より前。commit 順で示す。結果を見てから規則を触らない。
- **規律 2。** 認証の受理集合を広げない。判定結果を variant 採用・fitness・選択結果へ昇格させない。
- **規律 7。** 12 成果物は測定時点の事実であり、現行コードとの差だけを理由に無効化しない。
  v1 sha の記録はそのまま束縛として使う。
- **凍結成果物を書き換えない。** `output/insights/2026-09-07_t2265-backoff-itt/` は前 wave の
  歴史記録であり、1 byte も変えない。新しい結果は新しい insight dir へ出す。
- 事前登録 §9 の「exact な 3 腕・exact な軸で走った成果物にだけ束縛を付ける」を維持する。

## 6. DW-O09 pin 閉包 (実測。`git grep` の全 hit を分類した)

事前登録 file の bytes を pin する箇所:

| # | 場所 | 種別 | 扱い |
| --- | --- | --- | --- |
| 1 | `orchestrator/campaign/backoff_counterfactual_analysis.py:17-19` | live 定数 | v2 へ更新 + v1 を別定数で保持 |
| 2 | `orchestrator/tests/test_backoff_counterfactual_analysis.py:22` | 独立 golden (逐語) | v2 へ更新、v1 側も逐語で pin |
| 3 | `tools/pegasus/probes/t2187_adaptive_const_probe.py:82` | producer (実行時に sha を計算) | **コード変更なし**。DW-O10 参照 |
| 4 | `patches/README.md:319` | 手順記述 (値を書いていない) | 変更不要 |
| 5 | `docs/README.md:32` | 索引 1 行 | 変更不要 |
| 6 | `output/insights/2026-09-07_t2265-backoff-itt/**` | 歴史記録 | **不可触** |
| 7 | `docs/archive/worklog-phase3-0908-1328.md` | 歴史記録 | 不可触 |

`tools/check_docs.py` の whole-file SHA-256 pin は codex 用 cleanup-branches skill だけを対象と
しており、本 file は対象外 (実測)。path 以外を key にする pin は見つからなかった。

## 7. DW-O10 producer write-path

事前登録の bytes を読む producer は `tools/pegasus/probes/t2187_adaptive_const_probe.py` だけで、
`COUNTERFACTUAL_PREREGISTRATION` の sha を実行時に計算して成果物 JSON の
`counterfactual_preregistration` へ書く。本 wave は**この producer を起動しない**ので新しい成果物は
生まれない。将来の走行が v2 の sha を記録することは、v2 が発効した後の測定として正しい。
producer が書く file 種は診断 JSON (`stage2-rep0-*.json`) と同名 journal (`*.journal.jsonl`) の 2 種。

## 8. 成果物の形

- `docs/backoff-counterfactual-preregistration.md` (v2)
- `orchestrator/campaign/backoff_counterfactual_analysis.py`、同テスト
- `output/insights/2026-09-08_t2265-itt-seq0/README.md`、`analysis-result.json`、変異一式、`verbatim/`
- worklog / decisions / failures は `docs/spool/` の fragment として書く (段 9 の land が fold)

## 9. 受入・実測環境

login node での親の焦点走 + 受入全走。計算ノードは使わない。解析の実走は親が
`python3 -c` の inline 呼出しで行う (解析器は公開 CLI を持たない設計を維持する)。

## 10. 分割方針

実装面は 1 単位。事前登録 docs は親が書く (docs-only は親の担当)。実装子 (Codex `role=author`) が
解析器とテストを書く。段 2・3・6 の子は起動する — 本 wave は解析器の**受理集合**を変える
(P2 の 2 定数分割) ため、DW-C00 の軽量版条件に当たらない。
