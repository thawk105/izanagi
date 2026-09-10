# 段 4 裁定 — [T-598] wave 単位の前向き収集

段 3 は 2 レンズとも NO-GO。親は所見を real / refuted に裁定し、プラン v2 を確定する。

## 0. 最重要 — 親自身の規約違反を 1 件確定した

**B5 は real で、親の (P8) は撤回する。** `docs/pegasus-runbook.md` §7.0 は
「**AI セッション・子エージェント・自動化は分類の実測を自分で行わない**」「hook が未配線または
解析できない実行面を測定の抜け道に使うことも同じく禁止」と明記する。

親は段 1 で `/usr/bin/time -v` により 143.7 MiB を、段 3 待機中に `systemd-run --user --scope` の
正規手順で 140.0 MiB (3 回、certified 268.0 MiB) を測った。**どちらも分類根拠に使えない。**
正規手順で測ったこと自体が、AI が測ってはならないと明記された手番の実行である。
数値は記録として残すが、`local-ok` の導出には使わない。

さらに親は段 1 で `tools/claude_session_ledger.py` を pegasus02 上で 6 回実行した。
同 tool は未分類 = `unknown` であり、`unknown` は `dispatch-required` と同じに扱う規範に照らして
**ログインノードで走らせてはならなかった**。前 wave (288) も同じ tool を同じ面で走らせており、
**異なるセッションでの独立 2 例**である (`DW-G03` の族一般化条件を満たす)。

**帰結:** 本 wave は収集を実走しない。tool は `unknown` のまま land し、
Pegasus ログインノードでは fail-closed で自ら停止する。分類の測定依頼はユーザーへ返す。

## 1. 所見の裁定

| # | 所見 | 裁定 | 対応 |
|---|---|---|---|
| A1 | `files_scanned` は一致件数でないので誤 selector が complete zero になる | **real** | R2 で解消 |
| A2 | `files_scanned==0` 優先で resource failure が missing に化ける | **real** | R2 の順序で解消 |
| A3 | 空時間窓・offset 無し ISO8601 が偽ゼロを作る | **real** | R3 で時間窓を必須から外し解消 |
| A4 | wave/session lineage が無く cwd 部分一致が漏れ・混入を作る | **real** | R3 の path 境界一致で prefix 誤認だけ解消。残る近似は artifact に明記 |
| A5 | 無関係な collision が incomplete にする | **real・受容** | `--strict` を使わず issues を全記録。honest degradation |
| A6 | root/sidechain の同一 ID 二重計上 | **refuted** | 対応なし |
| A7 | ID を振り直した論理 duplicate | **見送り** | 実 transcript 未確認。レンズ A 自身が見送り可と明記 |
| A8 | max-files 25/200 の一致は一般化不可 | **real** | R6。`--max-files` を大きく取り `limit_reached` を incomplete に |
| A9 | rc=0 だけでは非 gate にならない | **real** | R5 |
| A10 | create-only は完全性・一意性を保証しない | **real** | R5 |
| A11 | 同一 session 内収集では wave 末尾が取れない | **real・受容** | cutoff を固定して artifact に記録 |
| A12 | exposure・層別・正規化子が無く前後比較に使えない | **real だが scope 外** | D220 決定 5 が既に裁定済み。U-1 はそれを承知で貯め始める裁定である |
| B1 | 957 bytes の手順を `docs/README.md` へ逃がすのは予算迂回 | **real** | R1 |
| B2 | 段 9 pointer では開始時刻と selector の供給元が無く死文 | **real** | R1 + R3 |
| B3 | 一致 0 件を消費 0 として保存する | **real** | R2 |
| B4 | `argparse` の `SystemExit(2)` が非 gate 契約と未接続 | **real** | R5 |
| B5 | P8 の実行場所推論は誤り | **real** | 節 0 |
| B6 | U-2 の漏洩面は手動境界に残る | **限定付き real** | 段 7 の commit 前に実値監査。新規 lint は作らない |
| B7 | 新 schema は U-3 違反ではない / import は fork ではない | **refuted (安全側)** | 対応なし |
| B8 | 新 test file に自走 harness が無い | **real** | R7 |

## 2. プラン v2 (確定)

### R1 — 契約行と手順の置き場所

- **手順本体を `docs/README.md` へ移さない** (B1 採用)。D110 却下案 (b)「reference を予算外に置く」に
  該当する。
- 契約行は `docs/dev-wave/core.md` の `DW-S09` 末尾へ 1 行:

  ```text
  段 9 後に `tools/collect_wave_usage.py` を実行する。
  ```

  改行込み **62 bytes**。合計 25,134 + 62 = **25,196 / 25,200** (残り 4)。`core.md` 単体 8,646 / 9,600。
- **手順の teeth は prose でなく tool の必須引数に置く** (機械強制)。repo 外・create-only・非 gate・
  ログインノード停止はすべて tool が強制する。散文で書かない。
- `docs/README.md` は既存の tools 地図 1 行の更新だけとする — 「production consumer は未結線 —
  結線先の裁定は T-598」を実際の結線先へ書き換え、新 tool を 1 行足す。これは既存 inventory の
  更新であって規範 detail の逃がしではない。

### R2 — 欠測判定 (D220 決定 3 の充足)

段 2 案の `files_scanned` 判定と `observed_zero` field を**両方とも廃止**する。判定は次の順:

1. collector を呼べなかった / 例外 → `error`
2. **`root.model_calls + sidechains.model_calls == 0` → `missing`**
3. `population.limit_reached` が真、または `issues` が非空 → `incomplete`
4. それ以外 → `complete`

**根拠:** wave は Claude が駆動するので、model call 0 の wave は存在しない。したがって集計 0 は
常に欠測 (誤 selector・消えた保存先・窓外) であり、観測値 0 ではない。この規則なら collector の
schema を一切変えずに D220 決定 3 を満たす。`observed_zero` を作らないので A1/B3 の
「complete かつ zero」という状態自体が消える。順序 1 が 2 に先行するので A2 も解消する。

### R3 — selector

- `--project` を**繰り返し可・1 個以上必須**とする。base/wave の区別を作らない (段 2 案の
  `--base-project` / `--wave-project` 必須化は、消えがちな wave slug を必須にして
  ほぼ全 wave を `incomplete` にする — 親が実測済み)。
- **時間窓は必須にしない** (B2)。段 9 に開始時刻の権威ある供給元は無い。worktree は wave 専用に
  生成・破棄されるので、worktree path 自体が wave の identity である。
- `tools/claude_session_ledger.py` へ **`--cwd-under <絶対 path>`** を追加する。
  一致条件は `cwd == p` または `cwd.startswith(p + "/")` の **path 境界一致**。
  既存 `--cwd-contains` は変更しない。
  **実測根拠:** 本 wave の該当 record 215 件は cwd がちょうど worktree root の 1 種類だった。
  部分一致だと `...-fix` / `...-2` を誤って取り込む (A4)。
- `--strict` は使わない (`missing_project` が fatal 化して rc=2 を招くだけ。親が実測)。
- `--include-sidechains` は helper が常に付ける (付け忘れ経路を作らない)。

### R4 — 実行場所の fail-closed

- helper は `orchestrator/campaign/site_policy.current_site()` を使い、
  Pegasus ログインノードなら **collector を呼ばずに** `status: "blocked"` の artifact を書いて rc=0 で終える。
- 理由は artifact の `reasons` に残す。これは §7.0 の「実測が無い実行体は `unknown` に倒して止める」
  の機械化であって、迂回ではない。
- 分類が済めば同じ contract のまま収集が始まる。**U-1 の発効はこの形で満たす** — 機構は live で、
  ユーザーの測定手番が済んだ瞬間に baseline が貯まり始める。

### R5 — 非 gate と出力

- `main()` は `SystemExit` を捕捉して常に 0 を返す。`KeyboardInterrupt` は握り潰さない。
- 出力は temp file へ完全に書いてから `os.link(tmp, out)` で公開し、temp を消す。
  `os.link` は宛先が存在すれば失敗するので create-only と atomic publish を同時に満たす。
- `--out` は絶対 path・repo 外を機械検査する。親 directory は作らない。

### R6 — 打切り

`--max-files` は必須にせず既定を大きく (collector の hard limit 1000) 取る。
`limit_reached` は `incomplete` にする。値が不変という一般化はしない (A8)。

### R7 — テスト

新 test file に `if __name__ == "__main__": pytest.main([__file__, "-x"])` を付ける (B8)。
allowlist は変更しない。

### R8 — scope 外として実装しないもの

task-run 台帳 v2、定期実行、A/B、gate 化、admission registry 登録、privacy lint、
exposure/層別 field の設計、content-hash dedupe、`tools/README.md` の編集。

## 3. 変異事前登録 (DW-M01)

| # | 変異 | 赤くなるべき node (単一理由) |
|---|---|---|
| M1 | `missing` 判定を `model_calls == 0` から `files_scanned == 0` へ差し替え | 偽ゼロ test |
| M2 | `limit_reached` の分岐を削除 | 打切り test |
| M3 | helper が `--cwd-under` を collector へ渡さない | selector test |
| M4 | `collect_report()` の import 呼出を subprocess + `json.loads` へ置換 | 第 2 parser 禁止 test |
| M5 | helper の rc を collector の rc へ差し替え | 非 gate test |
| M6 | `os.link` を `open(out, "w")` へ差し替え | create-only test |
| M7 | ログインノードの fail-closed を削除 | `blocked` test |
| M8 | `--project` 未指定を許して全 project 走査へ fallback | fallback 禁止 test |
| M9 | `--cwd-under` の境界判定を `startswith(p)` へ緩める | prefix 誤認 test |

各変異は helper / collector の 1 箇所だけを変え、前後に同じ入力を拒否する層は無い。

## 4. 成果物影響 (DW-G05)

本 wave は CC 合成の成果物 (certified 選択、レポート、試行台帳) の値・受理集合・参照を
**一切変えない**。must-fix の基準は「保存される観測値が偽になる」「規約違反が land する」
「非 gate を破って wave が止まる」の 3 つに限り、上表はすべてこの基準で裁定した。

## 5. ユーザーへ返す裁定パッケージ

1. **`tools/claude_session_ledger.py` と `tools/collect_wave_usage.py` の分類測定**
   (§7.0 の手番)。これが済むまで前向き収集は `blocked` を記録し続ける。
   測定は runbook §7.0 の `systemd-run --user --scope` 手順で、記録項目は
   commit / argv / 入力の総 bytes と件数 / `memory.max` / 観測ピーク / 繰り返し数 / 測定日。
   参考として親が測った値 (分類根拠にはできない): 観測ピーク 140.0 MiB (3 回最大)、
   certified 268.0 MiB、入力 128 files / 291.2 MB、wall 3.16 s、argv は本 wave の handoff に記録。
2. **AI が §7.0 の測定手番を実行してしまった件**と、**未分類 tool をログインノードで走らせた
   独立 2 例** (前 wave 288 と本 wave) の扱い。恒久対応を制度化するか。
