# 段 4 裁定 — dev-wave-t692-r3-xdist-walltime

段 3 の 2 本はいずれも **NO-GO** (レンズ A: Critical 1 / Major 5、レンズ B: Critical 3 / Major 5 / Minor 1)。
親は全 15 所見を real / refuted と採否で裁定し、プラン v2 を確定する。

## 1. 所見の裁定

| # | 所見 (要旨) | 判定 | 採否 |
|---|---|---|---|
| A1 | ungrouped payer が実 repo (untracked + submodule) を読むのに D63 閉包の外 | **real** | **本 wave では実装しない → 裁定パッケージ** |
| A2 | 収集順に依存した gate は脆く、memo の fail-open 分岐を発火させない | **real** | 採用 (案 1 の cross-worker 前提を落とす) |
| A3 | s8c の marker 変更は並行 wave t553 の所有物 | **real** | **採用 — s8c を scope から外す** |
| A4 | T-438 の helper 置換は受理集合を**強化**する (不変ではない) | **real** | 採用 — 不変条件を書き換えて明示記録 |
| A5 | 親の `-n 0` 実測はログインノードで、baseline と機体が違う | **real (親の誤り)** | 採用 — `s1-measurement.md` を訂正済み |
| A6 | `max(C,M)` は未測定の外挿。16/24 worker も未検討 | **real** | 採用 (projection を採用根拠にしない) |
| B1 | 875.67 秒は同時開始を仮定した条件付き値。非重複なら 1529.17 秒 | **real** | 採用 |
| B2 | junit の `time` は待ちと仕事を区別しない | **real** | 採用 (下界の意味を限定して記録) |
| B3 | measure2 は 670 秒帯の正体を分離できていない | **real** | 採用 (A5 と同根) |
| B4 | `δ=19.17` は単一走の残差で定数ではない | **real** | 採用 |
| B5 | 案 1 は増加率を変えない = 恒久策ではない | **real** | **採用 — 依頼への回答の中核** |
| B6 | 並行 wave との合成効果は加算できない | **real** | 採用 |
| B7 | M7 の留保が不足 | **real** | 採用 (留保を追記) |
| B8 | prewarm は `C` を消さない | **real** | 採用 (案 2 を不採用の根拠に) |
| B9 | 残り node 合計 17.03 は誤り (正 18.03) | **real** | 採用 — 訂正済み |

refuted は 0 件。**親 brief の (P4)「律速は real-repo group の直列和」は実測で支持された**が、
(P1) の「両立不能なら競合除去を優先」と、M4 の機序断定は上記のとおり修正した。

## 2. 実装する / しないの裁定

### 実装する (プラン v2)

- **(A) [T-438] の閉鎖** — `test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight`
  の `@pytest.mark.xdist_group(name="real_repo")` を削除し、canonical の
  `REAL_REPO_SERIAL_NODES` へ登録して conftest の hook に付けさせる。
  D63 の競合閉包に開いていた穴を塞ぐ**正しさの修理**であり、wall は実測 +69.45 秒。
  **速さのために見送らない (規律 2)。**
- **(B) 収集監査の強化** — 現行 `test_real_repo_serialization.py` は
  `mark.args` しか見ず `kwargs={"name": ...}` 形を見逃す。全 collected item の
  `xdist_group` marker を対象に、(i) marker は 1 node につき最大 1 個、
  (ii) 名前は positional 1 個で与える、(iii) group 名は独立 golden の集合に完全一致、
  を検査する。**合成負例 (kwargs 形・underscore 名・二重 marker・未登録名) が
  必ず赤になる positive control を同時に入れる** (恒真ゲートにしない)。
- **(D) canonical group 内の実行順の固定** — group 内は collection 順の FIFO で
  1 worker が順に処理する。`test_cli_subprocess_returns_rc_2_on_gate_refused`
  (独立解決 653.50 秒) を group の先頭へ、
  `test_run_block_broken_binding_manifest_refuses_and_writes_nothing` (cache 待ち) を
  その次へ固定する。**writer 群は従来どおり barrier の後**に置く。
  順序を meta-test で固定し、反転で赤になる負対照を付ける。

### 実装しない (裁定パッケージへ返す)

- **(A1) ungrouped payer の D63 閉包漏れ。** real かつ Critical だが、閉じ方が設計択一
  (閉包へ寄せる / prewarm + fail-closed / reader-writer lock) であり、いずれも
  受入 wall と正しさ防壁の機構に同時に触る。**親が単独で決める範囲を超える。**
- **(案 3) reader/writer flock 化。** 理論下界は最良 (約 691 秒) だが D63 の保証機構
  そのものの置換で、分類漏れ 1 件で偽緑になる。
- **(案 2) runner prewarm。** `C=653.50` を消さないため利得が小さく、
  runner・環境伝播面を増やす。
- **s8c candidate 3 node の canonical 化。** R3 の射程内だが t553 が同ファイルを編集所有中 (A3)。
- **`DEFAULT_WALLTIME` の引き上げ・並列度の変更。** 前者は期限を延ばすだけ、後者は
  下界が最大 group で決まるため効かない。

## 3. wall について主張すること / しないこと

- **主張する**: (D) の効果は projection では確定できない。**実測して数値で報告する。**
  実装後に baseline と同形の計測全走を 1 回行い、`real-repo` group の直列和と wall を比べる。
- **主張しない**: 875.67 秒という期待値。`max(C,M)` の重なり。`δ` の再現。
- **依頼への回答 (B5)**: xdist 分配側の変更は **恒久策にならない**。
  受入 wall は「実 repo T-080 receipt 解決 `q`」に支配され、`q` は commit 数と
  output ファイル数に比例して増える。しかも解決は 1 走で**構造的に 2 回**要る
  (共有 memo 1 回 + production CLI 子プロセス 1 回) ため wall ≈ `2q + tail`。
  分配をどう変えても `2q` は消えない。恒久策は `q` を下げること
  (`dev-wave-suite-floor-recheck` の所有) か、2 回目を無くす設計変更である。
  **後者は production CLI の受理経路を変えるので裁定が要る。**

## 4. 変異事前登録 (DW-M01)

実装後に `tools/mutation_harness.py` で走らせる。各変異は「無効化すると赤になる理由が
1 つに絞れる」ことを実装後にコードで確認してから確定する。

| ID | 変異位置 | 変異内容 | 期待して落ちる node (単一理由) |
|---|---|---|---|
| MT1 | `test_ruleops.py` | canonical 化した node を `REAL_REPO_SERIAL_NODES` から外す | 収集監査の node golden 一致検査 |
| MT2 | `test_ruleops.py` | `@pytest.mark.xdist_group(name="real_repo")` を復活させる | 監査の「marker は hook 由来のみ / 未登録 group 名」検査 |
| MT3 | `conftest.py` の hook | 既存 marker があれば skip する分岐を削る (二重 marker を許す) | 監査の「marker 最大 1 個」検査 |
| MT4 | 監査 helper | `kwargs` を見る経路を消して `args` だけに戻す | kwargs 形の合成負例 (positive control) |
| MT5 | 監査 helper | group 名 golden を「部分一致」へ緩める | underscore 名の合成負例 |
| MT6 | 収集順の定数 | CLI と binding の優先順を入れ替える | 実行順の meta-test |
| MT7 | 収集順の定数 | 優先順の定数を空にする (順序固定を無効化) | 実行順の meta-test |

**過剰拒否を検出する正例 (DW-M01 後段)**: 本 wave は受理集合を**強化**する ((A) の helper 置換)。
正当な collection が誤って赤にならないことを、変異なしの baseline 全走が緑であることと、
`test_ruleops.py` の対象 node が全走で緑のままであることで担保する。

## 5. 不変条件の訂正 (A4 を受けて)

段 1 brief の「受理集合を変えない」を次へ差し替える。

> **受理集合は狭まる方向にだけ変わってよい。** (A) の helper 置換は
> `--untracked-files=all` の raw bytes 比較へ強化するため、既存 untracked directory 内への
> 2 個目のファイル追加を**新たに**捕捉する。これは D63 の snapshot 契約に合わせる強化であり、
> 緩和ではない。強化であることを worklog に明記する。緩和方向の変更は一切採らない。

## 6. 成果物影響 (DW-G05)

- (A) を実装しない場合: 実 submodule を patch する writer と ruleops の実 checkout reader が
  同時に走りうる。受入の赤/緑が実行順で変わり、producer / pilot / 本走の受入結果を
  certified 選択・材料レポート・試行台帳の proof chain の根拠に使えなくなる。
- (B) を実装しない場合: 同型の表記ゆれが再発しても検査が緑のままになる ([T-438] は
  2026-08-04 に起票され、今日まで検出されなかった)。
- (D) を実装しない場合: 受入 wall が 1408 秒のまま残り、試験数の増加で 2400 秒上限に達したとき
  受入結果が「赤」ではなく「取得不能」になる。

## 7. 段 5 の分割

- 実装単位は 1 本 (編集ファイルが `orchestrator/tests/` 内で相互に依存するため分割しない)。
  codex `role=author`、`reasoning=high`、`sandbox=workspace-write`。
- 親は brief・裁定・統合 commit・変異 matrix・計測全走・受入全走・記録・land を担う。
