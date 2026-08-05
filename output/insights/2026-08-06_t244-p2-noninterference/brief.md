# 段 1 brief — [T-244] P2 非干渉検査の実装 wave (U-1〜U-3 裁定済み)

起点 main = `cfda4abe`。wave branch = `worktree-dev-wave-t244-p2-noninterference`。
scope 正本 = `output/insights/2026-08-05_t244-p2-noninterference/s4-adjudication.md`。

## scope

確定済みユーザー裁定 U-1 (i) / U-2 (ii) / U-3 を **D96 の同一変更単位**で実装し、
同文書の決定 (4) が推奨する indistinguishability 検査を新設する。

1. **U-1 (i)**: critic が観測する候補識別子を、origin scope の**不透明 ID** へ置換する。
2. **U-2 (ii)**: auditor への `working_diff` + `diff_digest` 開示を**明示的 declassification**
   として会計し、reflux-control 実装時に (i) (raw から独立再生成した diff のみ・digest は渡さない)
   へ戻す条件を同時に固定する。
3. **U-3**: 「IR schema identity」の preimage を **emitter source + 32 golden の複合**と定義する。
4. **決定 (4)**: secret `S` = 候補 wire、公開入力 `P` を固定して `S` を変えたとき、
   provider へ渡る serialized payload bytes が role ごとに同一かを検査する。
   planner / coder = PASS 必須、auditor = 明示 declassification として例外、critic = U-1 実装後に PASS 必須。
5. **D96 手続**: 新しい設計判断 (新 D) の記録と、受理集合を固定している境界テストの同時更新。

## 段 1 前提実測 (現行 tip `cfda4abe`、`.../s1/probe_codebook.py` とソース読取)

- **(M1) 裁定の中心前提は現行 tip でも成立する。** 32 点 universe で
  `diffq_variant_id` は 32/32 一意・wire 字面を含むもの 0/32。build 経路の `variant_id` も
  src_token を predicate の関数と置いたモデルで 32/32 一意・字面 0/32。
- **(M2) critic の候補チャネルは 1 本ではない (射程の拡大、裁定は覆らない)。**
  `harness_result.variant` に加えて `critic_digest` が `variant=` / `src_token=` を
  `orchestrator/critic/digest.py` の 4 節 (rejections 584 / liveness 625 / diff-quarantine 643 /
  screening 683) で描画する。`src_token` は編集後 source の digest なので同じく 32 点で可逆。
  U-1 の実装面は payload の 1 field より広い。
- **(M3) 既存被覆は key-set 固定だけである。**
  `orchestrator/tests/test_p3_autonomous_workload_trial.py:814-829` が planner / coder / critic の
  payload key 集合を固定するが、値の情報依存は拘束しない (段 3 所見 A-B4 と同じ)。
  **本 wave の純増検出力 = 既存の許可 field の「値」へ符号化された漏洩の検出**である。
- **(M4) 生死は既存 driver で確認済み (DW-G01)。** `_RecordingFixture` +
  `run_trial(provider_kind="fixture", do_build=False, drive/preview 注入)` が role ごとの payload を
  既に捕捉しており (同 test:800-829)、`FixtureRoleProvider` は generation で wire を
  `"11111"` / `"10000"` と変える。新規 driver も専用機構も不要。
- **(M5) 凍結 bytes の pin 閉包 (DW-O09)。** `FROZEN_MANIFEST` 23 件は s1 / s8b 成果物のみで、
  8c の critic payload・attempt journal・critic digest を pin しない。`make_critic_digest` の
  consumer は production 3 + test 2 で、test 2 本は構造 assert であり digest 本文の bytes golden は無い。
  → **DW-O09 / DW-O10 は成立しない方向**。段 4 で再評価する。
- **(M6) 本番 origin authority は `origins: []` で U-10 未決のため entry を発行できない** (worklog (241))。
  よって「origin scope の不透明 ID」を実 `origin_id` へ束縛する実装は現時点で不能である。

## 不変条件

1. 現行の受理集合を狭めない。既存の payload key assert を弱体化しない (段 3 所見 B-N1)。
2. WAL / provenance の variant key は変えない (D51)。射影は critic 境界に限る。
3. **恒真な検査を作らない。** 検査は現行 baseline の実漏洩に対して発火しなければならない
   (字面部分一致 tripwire に退化させない)。
4. auditor の diff 開示は塞がない (U-2 (ii))。ただし declassification として明示会計する。
5. production は 32 golden を import しない (`orchestrator/tests/test_reflux_ir.py:216` の独立性検査)。
   U-3 の identity は検証層で組む。
6. `_invoke` 冒頭に無条件の fail-closed raise を置かない (段 3 決定 3 の terminal report 欠落経路)。

## provisional 裁定 — 親の暫定であり攻撃対象

- **(P1)** U-1 の実装形は「WAL キーは不変のまま、critic 境界で **campaign 内の出現順に振る
  不透明ラベル**へ射影する」。keyed hash も WAL キー変更も採らない。
- **(P2)** 非干渉検査は**テスト層の oracle** として置き、production の runtime gate にはしない。
- **(P3)** U-3 の identity は「emitter source bytes の sha256 + 32 golden 行の sha256」の 2 要素とし、
  検証層の定数として固定する。
- **(P4)** `critic_digest` 側の射影 (M2) も本 wave の scope 内とする。

## 成果物の形

- コード: critic 向け不透明ラベル射影 (`p3_autonomous_workload_trial.py`, `critic/digest.py`)。
- テスト: 非干渉検査 (4 role) + 負例 + 既存境界テストの追随 + U-3 identity 固定。
- docs: 新 D 1 本 (D96 手続)、worklog fragment、insights 逐語。

## 成果物影響 (DW-G05)

実装しない場合、critic は毎世代 5 bit の候補 wire を観測し続け、D121 が謳う「機序を漏らさずに
失敗理由だけを還流させる」と実装が乖離したままになる。実装で変わる値は、critic へ渡る
`harness_result.variant` と `critic_digest` 内の variant / src_token 文字列、および attempt journal の
`input_payload_sha256` である。**certified 選択・材料レポート・proof chain・凍結 bytes の現在値は
変わらない** (8c は official 受理集合を持たない)。

## 並列分割

- 所有 A: critic 境界の射影 (`orchestrator/campaign/p3_autonomous_workload_trial.py`,
  `orchestrator/critic/digest.py`)
- 所有 B: 非干渉検査と U-3 identity (`orchestrator/tests/`)

## 環境

受入・実測は Pegasus 計算ノードへ `python3 tools/run_tests.py` 経由で dispatch する。
ログインノードで pytest を走らせない (前 wave 決定 (6) の是正を反映)。
