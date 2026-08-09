# [T-139]/[T-659] F37 の機械強制化 — land の ff-only に全史 provenance 監査を課す

2026-08-09、branch `worktree-dev-wave-t139-provenance-known-violation`。
統合 commit `6b85c0fd` (実装) / `46ce4d6c` (変異 spec)。

## 何をしたか

ユーザー裁定 (`dev-wave-jobs/rulings-inbox/2026-08-09-t659-provenance-and-f37-rulings.md` の項目 2、
発話「推奨通りで」) に従い、`tools/dev_wave_land.py` が provenance 全史監査を自ら走らせて rc を
確認し、赤なら land を拒否する形にした。F37 (検査 rc をパイプで喪失) を文章の注意喚起から
機械強制へ移す。

同日 3 wave・3 親で独立 3 例が出ており、実害は 22 commit / 1 commit / 検出は偶然だった。
`DW-G03` の「族一般化には独立 2 例」を大きく超える。

## 確定した設計 (段 4 と段 6 で 2 度組み直した)

- **二相化。** lock を先に取り、busy なら checker を 1 度も起動せず即座に `lock-busy`。
- **監査を要するのは `locked_main != tested_tip`** = これから ff-only を行う場合だけ。
  `already-landed` の no-op と active fold recovery は監査を起動しない。
- **監査は lock を解放してから実行**し、取り直して全検査をやり直す。
- 監査前後で main/wave の HEAD・collision path 集合・control-plane identity を照合する。
- receipt は `tip_sha` / `checker_blob_sha` / `executed_bytes_sha` / `returncode` を束縛する。
- timeout は 480 秒。受入 lease の TTL 2400 秒と親の前景 600 秒上限の内側。
- 新 reject rc は `RC_PROVENANCE = 29`。逃がし道は作らない。

## 敵対検証の経過 — 4 本すべてが親案を否定した

段 3 の 2 レンズと段 6 の 2 レビューは、いずれも NO-GO または blocker を返した。
**親の当初案 (lock 内監査 / 38 秒受容 / recovery 免除の署名) は 3 点とも誤りだった。**

| 段 | レンズ | 結論 | 親の処置 |
|---|---|---|---|
| 3 | A 正しさ境界 | blocker 3、B 推奨 | 停止理由としては refuted、別 scope の課題としては採用 |
| 3 | B 整合・実効性 | blocker 1 / must-fix 5 | lock 外監査へ全面採用 |
| 6 | A 関門は発火するか | NO-GO、blocker 3 | 全採用。**親の署名の偽を検出** |
| 6 | B 波及と回帰 | NO-GO、blocker 4 | 全採用 |

**段 3 の B 推奨を採らなかった理由。** 両レンズは「関門が tip 側コード実行という新しい信頼面を
作る」を前提に「止めて immutable trust root を別 scope で設計せよ」と推した。親が実測で反証した
— `docs/pegasus-runbook.md` の land 手順は worktree の cwd から相対 path で
`dev_wave_land.py` を起動するので、**親は既に tip 側 helper を実行している。**
関門は信頼面を増やさない。閉じるのは「親が rc を読み違える事故」で、F37 の 3 例はすべて事故である。
immutable trust root の不在は land helper 全体に及ぶ既存課題であり、裁定パッケージへ回した。

**親の署名の偽 (段 6 レビュー A が検出)。** 段 4 で「active fold recovery は新規 commit を
1 つも admit しない」と署名で書いたが、`_fold_main_locked()` は実際に commit する。
新テスト自身が `main_after != tip` と断言していた。線引きを
「新規 commit を作るか」から「wave の commit を main へ新たに入れるか (ff-only を行うか)」へ
引き直した。これで段 6 レビュー A と B の対立も同時に解けた。

## 親自身の実測の誤り 2 件 (段 3 の両レンズが独立に指摘、撤回済み)

1. **「`pipefail`・「パイプ」で hit ゼロ、純増検出力 100%」は誤り。**
   `tools/*.py` しか検索しておらず `tools/**/*.sh` を落としていた。実際には
   `tools/strip_claude_session_trailers.sh` や `tools/pegasus/*.sh` 多数に `set -euo pipefail` がある。
   訂正後の主張: それらは各 script 内部の fail-fast であり、
   「親が対話 Bash で検査 rc をパイプへ流す」F37 の vector は覆わない。
2. **「既存 2 本の子検査と同型だから足せる」は誤り。**
   共通なのは `subprocess.run` + `returncode` 直読みの構文だけである。既存 2 本は短時間・
   login 完結・手元入力で、`_fold_main_locked()` の広い例外捕捉と rollback の内側にある。
   全史監査だけが login admission・bounded scope・Pegasus dispatch・queue 待ちを通る。

`38.3 秒` は `time` の実測だが `prov-baseline.txt` には含まれず、かつ上限でもない。
lock 予算の根拠には使わない (lock 外設計により上限依存を解消した)。

## 変異 matrix の実測

`tools/mutation_harness.py --runner-mode dispatch --detached`、統合 commit 後に本走。
台帳は `mutation-ledger.json` (11 変異) と `mutation-ledger-m10b.json` (両層同時変異 1 件)。

**12 変異で SURVIVED 0。** 内訳は次のとおり。

- 期待 node がちょうど発火: M1 / M2 / M4 / M5 / M6 / M8a / M9 の 7 件
- 期待 node は発火したが他 node も落ちた **過剰決定**: M3 (56 node) / M7 / M8b / M10b の 4 件。
  `DW-M03` に従い冗長と明記し、単独変異の証拠からは外す
- **M10 は期待 node が発火しなかった (erratum、初回結果は消さない)**

### M10 の erratum と両層裏取り

M10 は `refreshed_fingerprint != initial_fingerprint` の照合を無効化する変異だった。
期待した `test_provenance_audit_detects_removed_ignored_collision` は落ちず、別 node が殺した。
原因は fingerprint 照合が **2 箇所**あることで、片方だけの変異はもう一方に mask される。

`DW-M02` に従い両層同時変異 M10b を追加登録して本走した。結果、**collision テストが発火した**。
したがって「このテストが監査窓 fingerprint gate を守っている」という主張は、
**両層が同時に失われた場合について成立する**。単層についてはもう一方の層が冗長に守る。

### 変異走行の切り詰め (silent cap にしない)

runner の対象から `test_exploration_external_root_keeps_wave_clean` を
`-k "not ..."` で **1 件だけ除外した**。harness は緑の baseline を要求するが、このテストは
本 wave の差分と無関係の環境要因で赤になるためである (下記)。除外したテストは変異対象
`tools/dev_wave_land.py` から到達不能で、どの変異の期待 node にも含まれない。

## 本 wave の差分と無関係な赤 1 件

`test_exploration_external_root_keeps_wave_clean` は両ノードで、**別々の理由で**落ちる。

- **ログインノード**: `/tmp/.git` (空ディレクトリ、2026-07-28 作成) が存在するため
  `orchestrator/campaign/layout.py` の `_has_git_ancestor` が `/tmp` 配下のあらゆる一時
  ディレクトリを「repository 内」と判定する。
  `layout._has_git_ancestor(tempfile.mkdtemp())` → `True` を直接検算した。
- **計算ノード**: `campaign.execution_guard.CertifiedWriterAuthorizationError`
  (「Pegasus compute では receipt state 内で一意な required authorization_contract だけを受理する」)。

帰属の根拠 4 点: (i) 本 wave の差分は当該テスト本体に触れていない、
(ii) `tools/dev_wave_land.py` は campaign モジュールを import しない、
(iii) 同テストは base commit `bcda1c02` に存在し、直近の受入全走 (7570 passed) で緑だった、
(iv) 両ノードで原因が異なり、いずれも campaign 側の大域状態である。

計算ノード側の要因は [T-657]/[T-660] の G2 活性化と、未実行のユーザー手番
(floor protocol 再発行) に関係する可能性がある。本 wave は調査も手当もしていない。

## 残余 risk (関門では閉じない)

- checker の pathname を実行中だけ差し替えて終了前に復元する race は検出できない。
- tip 側の land helper と checker が可変であるという協調境界そのものは解消しない。
  `tools/dev_wave_land.py` 自身が「悪意ある writer に対する sandbox ではない」と宣言している
  既存の境界であり、本変更は悪化させないが解消もしない。
- land 経路を通らない main 更新 (直接 commit、`update-ref` 等) は覆わない。

## 逐語

`verbatim/` に親 brief v2、段 2 プラン、段 3 レンズ 2 本、段 4 裁定、段 5 実装報告、
段 6 レビュー 2 本、段 6 fix 2 本を凍結した。段 1 の旧 brief (`parent-brief.md`) は
scope 変更で invalidate したため凍結しない。
