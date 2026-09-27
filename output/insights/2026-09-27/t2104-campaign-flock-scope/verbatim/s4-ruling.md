# 段 4 裁定 — [T-2104] campaign flock 範囲 (D1346)

入力: brief.md (v2)、out/s2-plan-2.md、out/s3-consult-sol-2.md、out/s3-consult-luna-2.md。v1 の段 2・3 は DW-O13 読了遅れで無効 (superseded/)。
裁定 inbox 再走査 (段 4 直前): main は wave 開始時 ad114fba0 から不動、T-2104 / D1346 の新裁定なし。

## 所見の裁定

| 所見 | 判定 | 採否・扱い |
|---|---|---|
| sol#1 path 不一致の拒否が B-4 認可の消費より後 | real (注入 layout 経路に限る) | **scope 外・不採用。** 本番経路では main() の drive_iteration 呼出し (p3_s4_loop.py:3932-3947) は layout を注入せず、driver の既定 layout と run_campaign の layout は式上同一 (環境契約の再 bind は冪等、layout.py:62-68 の式は共通)。不一致は test の注入 layout でしか起きず、そこでは run_campaign の照合が WAL 前に fail-closed。消費前の追加照合は依頼が除外する仮想リスク向け gate に当たる。insight に記録。 |
| sol#2・luna#6 53/53 は lock path 一致の実測でない | real | **採用 (test で直接測る)。** 負例 test で「driver が保持する path == `p3_b4_raw_record_producer._execution_lock_for_root(layout.root)`」を明示 assert し、run_campaign 側は受け渡し時の path 照合で一致を強制する。53/53 は同居の実例としてだけ記録する。追加の環境走査はしない。 |
| sol#3 handle の同一 process 性 | real | **採用 (最小)。** handle は取得 PID を持ち、run_campaign は `handle.pid == os.getpid()` を要求する。 |
| luna#1 fd・inode 照合は過剰 | real | **採用 (削除)。** 照合は exact 型・保持中 (context 内だけ真)・PID・path 一致の 4 項目に限る。 |
| luna#2 新例外型・互換層・共通枠組み不要 | real | **採用。** 不一致は既存の `ValueError` (型違いは `TypeError`)。 |
| luna#5 main() の B-4 事前認可窓 | real | **採用 (plan どおり)。** |
| sol#4 main の負例が保持の終端を示さない | real | **採用。** main 経由の test は、main から呼ばれた driver の checkpoint (実 save_loop_state) 中にも producer path が CampaignBusy であること、main 復帰後は取得できることを示す。 |
| sol#5・luna#3 変異表 | 一部 real | 変異の事前登録は DW-S04/DW-M01 上必須なので残す (luna の削除推奨は不採用)。赤理由の単一性は段 6 の probe で node ごとに確かめる (DW-M08)。 |
| luna#3 同期点を全部置くのは過剰 | refuted | 4 同期点 (認可・preflight・checkpoint・main 事前認可) は区間 D1346 の各点そのもの。維持する。新 test file と fd/inode 負例は作らない。 |
| sol#6 brief の lock dir 表記 | real | brief 訂正 (下記)。 |
| luna#7 hit 件数の断定 | real | 親が全件を再走査: 13 file すべて output/insights の歴史記録 (t1769 wiring probe 6・t2344 2・t2489 3・t2795 2)。t2341-eligibility/base.json は事前登録が sha 束縛する証拠だが、`p3_b4_wiring_probe.py:1966-1990` の検査は記録内の自己整合だけで現行 bytes と照合しない。規律 7 により更新しない。 |
| 候補: sort/trigger の同型窓、producer 非保証文の陳腐化 | real (現 B-4 母集合への影響なし) | 起票せず insight に記録 (DW-S04)。 |

## plan v3 (実装子への指示の正本)

1. `orchestrator/campaign/lock.py`: `campaign_lock` が取得後に保持 handle を yield する (exact な小 class: path・pid・保持中フラグ。context 退出時に保持中を偽にしてから unlock・close)。既存の `with campaign_lock(path):` の挙動と CampaignBusy 契約は不変。通常取得を再入可能にしない。
2. `orchestrator/campaign/loop.py` `run_campaign`: keyword-only の任意引数 (例 `held_campaign_lock=None`) を追加。None なら従来どおり自分で取得。指定時は lock path を従来の式で計算し、handle の exact 型・保持中・PID・path 一致を確かめて取得を省く。不一致は WAL 前に ValueError / TypeError。
3. `orchestrator/campaign/p3_s4_loop.py`:
   - `drive_iteration`: layout 解決直後 (`_load_provenance` より前) に `campaign_lock(campaign_lock_path(layout, DECLARED_USE_CLASS), blocking=False)` を取り、入口停止の save を含む checkpoint (`save_loop_state`) 完了まで保持して、critic digest の前に解放する。main から handle を受けた場合は取得せず、同じ path であることを確かめて使う。
   - `_run_one_iteration_resolved`: 任意の private keyword で handle を受け、`run_campaign` へ渡す (None のときは keyword 自体を渡さない)。
   - `main()` の `--run-iteration` で `--b4-reflux-ablation` のとき: 事前認可 (preflight_layout の state 読込) より前に同じ lock を非ブロッキングで取り、drive_iteration の復帰 (候補の終了・例外) まで保持して driver へ渡す。pair mode の stock control へ持ち越さない。B-4 以外の main 経路は main で取らない (driver が取る)。
   - 変えないもの: 公開 `run_one_iteration`、main の fixture 直呼び (:4001-4008)、stock control の `run_campaign` (:2387)、B-4 認可・消費関数の本体。
4. test (既存 file に追記。新 test file は作らない):
   - `orchestrator/tests/test_p3_s4_loop.py`: base の 3 同期点 (実 `require_b4_iteration_authorization` を呼ぶ wrapper 中、実 `validate_backoff_preflight` 中、実 `save_loop_state` 中 — 通常と入口停止) と main の事前認可中・main 経由の checkpoint 中で、producer の `_execution_lock_for_root(layout.root)` の path を実 `campaign_lock(path, blocking=False)` で取りに行き CampaignBusy を要求する。各 probe の到達回数を assert し、driver 保持 path と producer path の一致を明示 assert し、scope 退出後は取得できることを確かめる。競合時 (別 process が保持) に B-4 消費 record が作られないことも 1 本。
   - `orchestrator/tests/test_campaign.py`: 受け渡し契約 — 正しい handle で run_campaign が再取得しない (CampaignBusy にならない) 正例、別 path・解放済み・PID 不一致の handle を WAL 前に拒否する負例、引数なしは従来どおり取得する正例。既存の再入拒否・競合 process・別 campaign 並行 test は変更しない。
5. 規模上限: production の追加・変更は indentation の付け替えを除き約 150 行まで、test は約 300 行まで。超えそうなら止めて理由を報告する。

## 変異の事前登録 (DW-M01、期待 node 集合は段 6 の probe で完全集合として確定)

| ID | 変異 (位置) | 殺すべき test | 期待する赤 |
|---|---|---|---|
| M1 | drive_iteration の取得を B-4 認可消費の後 (_run_one_iteration_resolved の直前) へ移す | base 認可 probe | 認可中に producer path を取得できる |
| M2 | drive_iteration の保持を _run_one_iteration_resolved の復帰直後で解放 (provenance・save の前) | base checkpoint probe (通常) | checkpoint 中に取得できる |
| M3 | 入口停止経路の save_loop_state を保持区間の外へ出す | base checkpoint probe (入口停止) | 入口停止の save 中に取得できる |
| M4 | main の事前取得を削除 (driver が自分で取る) | main 事前認可 probe | 事前認可中に取得できる |
| M5 | run_campaign が handle を無視して常に自分で取得 | 受け渡し正例、実 run_campaign を通す drive test | 自分の外側 lock に対し CampaignBusy |
| M6 | run_campaign の path 一致検査を削除 | 別 path handle の負例 | 拒否されず実行へ進む |
| M7 | run_campaign の PID 検査を削除 | PID 不一致 handle の負例 | 拒否されず実行へ進む |
| M8 | run_campaign の保持中検査を削除 | 解放済み handle の負例 | 拒否されず実行へ進む |

赤理由の単一性: 各変異は位置が 1 箇所、同じ入力を拒否する別層が前後・内側にないことを実装後に確かめる。確かめられない変異は登録を外して実効 gate へ再照準する (F28/F820)。

### 追補 (段 6、変異 spec 作成時の再照準・erratum)

- M1 「取得を B-4 認可消費の後へ移す」は with 区画の字下げを伴い単一置換で表せないため、同じ窓を開ける
  「driver の外側取得を無効化 (`lock_cm = contextlib.nullcontext(None)`)」へ再照準した。窓は認可より広くなる (preflight・checkpoint も開く)。
- M2 / M3 「checkpoint を保持区間の外へ出す」は、checkpoint 直前で保持中の lock を `lock_cm.__exit__(None, None, None)` で明示解放する置換で表した。
- 対照 M0a (p3_s4_loop.py のコメントだけ)・M0b (loop.py のコメントだけ) を足した。閉包 file の drift 層を測るため。
- 期待 node は dispatch probe (全件 SURVIVED 期待) の観測集合をそのまま登録した (DW-M08)。

## 旧コードでの負例の赤 (完了判定の一部)

親が段 6 で、新 test を旧 production (ad114fba0) に当てた木で焦点走し、4 同期点の負例が「取得できてしまう」理由で赤になることを node ごとに記録する (誤判定の再現)。
