# 段 1 brief — [T-1769] B-4 事前登録 §5.1 (ii) の非標本 probe

基準 commit: dd66213978d3d30eed567484ec013216bff6926b (local main と同一)
branch: worktree-dev-wave-t1769-b4-wiring-probe

## scope (作るもの)

新しい **sanctioned CLI** を 1 本作る。`docs/phase3-b4-reflux-ablation-preregistration.md`
§5.1 (ii) が要求する 4 検査を、**next synthesis と primary / secondary outcome を
生成も閲覧もせずに**実行し、証拠 JSON を出す。生成しないことは、謳うだけの assert でなく
**生成しようとした負例で実際に発火する**機構で保証する。

4 検査 (§5.1 (ii) 逐語):
1. sanctioned CLI 経路が §3.1 の切替点 (`p3_s4_loop.make_critic_digest(reflux=)`) を通ること
2. on で赤詳細が出現すること
3. off で §8 の項目 1・2 が成立すること (4 loader が一度も呼ばれない / off が緑 digest と byte 一致)
4. on/off の campaign identity が分離すること

候補 driver は 3 本: `p3_s4_loop` (base)、`p3_s4_loop_sort`、`p3_s4_loop_trigger_gating`。

## 確定済みユーザー裁定 (不変。攻撃対象ではない)

- **D1083**: 適格性は「結果を生成も閲覧もしない配線調査」で測ってよい。生成しないことは
  **出力経路を構造的に持たせない設計**で保証する。別プロセス / 別権限の実行主体は要求しない (却下済み)。
- **D95**: 実装面は Codex `role=author` が書く。親は直接編集しない。
- 記録は **T-1769** に寄せる。台帳の [T-1909] は同一主題で別採番しない。

## 実測した前提 (brief 前、DW-S01)

- `docs/phase3-b4-reflux-ablation-preregistration.md:389` は「§5.1 (ii) を満たす非標本 probe。
  現時点で、その条件を満たす sanctioned CLI は存在しない」と明記。**実在を確認した。**
- 既存被覆の走査 (性質で検索、archive worklog を含む): 該当 CLI は現存しない。
  `output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py` は別主題 (liveness)。
  `orchestrator/campaign/reflux_ir.py` 族は trigger-gating wire の IR であり B-4 還流とは別語義。
  **純増である。**
- **DW-G01 (生死実験先行) は既存 driver で済ませた。** `orchestrator/tests/test_p3_s4_loop.py -k
  "make_critic_digest or reflux"` を実走 → **10 passed / 6.70s** (計算ノード dispatch、
  request 951477.nqsv)。検査 2・3・4 は build 無し・fixture の記録ログで in-process に
  観測可能であることが実測で確定した。専用機構を作る前の最安確認はこれで足りる。
- 切替点の呼び手 (実測、grep): `p3_s4_loop.py:1514,1722`、`p3_s4_loop_sort.py:506,695`、
  `p3_s4_loop_trigger_gating.py:1036`、`p3_b4_closed_critic.py:876,1736`、
  `p3_autonomous_workload_trial.py:3100`。
- 既存 CLI が probe にならない理由も実測: `p3_s4_loop.main` の `--no-build` は
  digest 生成へ到達する経路を build 経路と共有し、`--b4-reflux-ablation` は `--no-build` を
  明示禁止する (`B4ProtocolError`、`p3_s4_loop.py:1576`)。
- 編集面重複: 稼働 7 worktree の未 commit + branch tip に `p3_s4_loop` / `b4-reflux` / `p3_b4` /
  `closed_critic` の hit **0 件**。t1805 は s8b 系、t1629 は ratification broker 系で重ならない。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** probe は `orchestrator/campaign/` 配下の新規 module 1 本 + `main(argv)` とし、
  driver は `--driver {base,sort,trigger}` で選ぶ。既存 driver の `main` へ flag を足す形は採らない
  (既存 CLI は build 経路と gate を共有しており、構造的遮断を後付けすると恒真化しやすい)。
- **(P2)** 検査 1 (切替点通過) は **静的到達可能性 + 動的呼出しの 2 本**で立てる。静的は driver の
  `main` から `make_critic_digest` への呼出し閉包を AST で導出する。動的は probe 自身が
  **実体 `p3_s4_loop.make_critic_digest`** を呼び、call ledger で観測する。
  検査 2・3・4 は fixture の記録ログから作った policy-admitted な view 上で動的に測る。
- **(P3)** 「生成しない」の機械保証は **interdiction 窓**とする。probe process 全体で、
  outcome を生む実体 callable を発火する差し替えに置き換え、呼ばれたら `OutcomeGenerationError` で
  即時 fail-closed し証拠を書かない。遮断対象集合は **driver module の AST 目録から導出**し、
  新しい producer が足されたら probe が落ちる (取りこぼしでなく fail-closed) 側へ倒す。
- **(P4)** 非恒真の裏取りは、**実体を名指しした負例**で行う。stub でなく実 `drive_iteration` /
  `run_one_iteration` / `pipeline.evaluate` を窓の中で呼ぶ負例テストを置き、発火を示す。
  「候補集合に含意されて恒真」(述語が自分の候補集合から導かれる形) にしない。
- **(P5)** probe は実 campaign の配置へ書かない。隔離した根を使い、
  実験の記録ログ・checkpoint・digest を 1 byte も触らない。
- **(P6)** 本 wave では **§5 の「対象 driver と軸」欄を埋めない。** §5.1 (i) が要求する先行 freeze
  (候補集合・exact command・証拠 path と hash・0 件/複数件の決定規則・**記入者とレビュー者**) は
  人間の指名を含み、別 commit で先に固定すると §5.1 が定める。本 wave の probe 実走は
  **道具の実データ dogfood であって §5.1 (ii) の採用証拠ではない**と明記する。
- **(P7)** docs 側は `docs/phase3-b4-reflux-ablation-preregistration.md` の §10 最上位項目
  (「条件を満たす sanctioned CLI は存在しない」) と §5.1 の当該記述を、CLI 実在後の状態へ改める。
  **発効しない理由は残す** — 残るのは §5.1 (i) の先行 freeze と人間の指名である。

## 不変条件 (破ってはいけない)

- 規律 2 / 3: probe は正しさゲートを 1 つも緩めない。既存の §8 テスト群の受理集合を変えない。
- probe は LLM role を起動しない。build / verify / bench を起動しない。
- probe は実 campaign の記録ログ・checkpoint・digest・成果物ツリーを読まない・書かない。
- 恒真禁止: 「outcome を生成しない」保証は、生成する負例で発火することを実走で示す。
- 凍結 bytes: `orchestrator/tests/test_frozen_artifacts.py` の `FROZEN_MANIFEST` (23 件) は変えない。
  新規成果物 path が既存 pin と衝突しないことを実装子が確認する。

## 成果物影響 (DW-G05)

- probe が無い間、B-4 事前登録 §5 の「対象 driver と軸」は**永久に空欄**であり、
  文書は発効せず、B-4 の certified 選択結果はレポートに載らない。本 wave はその唯一の blocker を外す。
- (P3) の機械保証を欠くと、probe が outcome を生成しても誰も気づかず、
  §5.1 (ii) の「非標本」条件が破れる。そのとき B-4 の estimand は「未知結果に対する confirmatory」を
  名乗れなくなり、§9 の HARKing 境界の記述が偽になる。

## 成果物の形

- `orchestrator/campaign/<probe module>.py` — sanctioned CLI 1 本
- `orchestrator/tests/test_<probe>.py` — 正例 + **実体名指しの負例**
- 証拠 JSON (probe の出力、sha256 つき) — dogfood 走の実データ
- 変異 matrix (段 4 で事前登録、段 6 で実走)
- docs: 事前登録 §10 / §5.1 の該当記述、spool fragment (worklog / decisions)

## 並列分割方針

- 段 2: read-only codex 1 本で file:line 粒度のプラン。
- 段 3: 敵対 2 本。レンズ A = 「この保証は恒真ではないか」(候補集合による含意、
  遮断集合の取りこぼし、負例が実体を名指ししているか)。レンズ B = 「probe が outcome を
  生成・閲覧する残経路はないか」(fixture の由来、配置の注入、import 副作用、
  静的閉包が別名束縛を落とす面)。
- 段 5: Codex author 1 本 (probe module + test は同一編集面で分けない方が整合が取れる)。
- 段 6: 敵対レビュー 2 本 + fix + 変異 matrix + 受入全走。
