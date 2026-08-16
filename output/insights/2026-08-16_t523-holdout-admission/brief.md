# 段 1 brief — [T-523] freeze 由来 holdout を実測へ渡す共通下位境界に admission と一回性台帳を置く

基準 commit: 330f67d0 / branch: worktree-dev-wave-t523-holdout-admission / 2026-08-15 22:30 JST

## 1. 何が壊れているか (親が本 worktree で実測した事実のみ)

- `orchestrator/campaign/s8b_floor_campaign.py` は文字列 `trial_registry` を 0 箇所、
  `lifecycle` を 0 箇所しか含まない。保持している admission は `s8b_binary_admission`
  (build/binary 由来) だけで、trial 側の admission ではない。
- 実 freeze (`output/s8b-freeze/holdout_freeze.json`, sha256
  315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688) と実 protocol
  (`output/s8b-freeze/floor_protocol.json`, stock_configuration=stock_common) から
  `enumerate_cells` を実行すると 12 セルが出て、`holdout_id` は exact {rr20, rr80}。
  これは `trial_registry.HOLDOUT_WORKLOADS` = {rr20, rr80} と同一集合である。
  → 8c launcher が `u4-holdout-workload` で拒否する対象を、8b は無検査で実測できる。
- `main()` の pilot 経路は load_protocol → validate_protocol → _load_verified_freeze →
  `run_campaign` で、途中に trial admission も一回性台帳も無い。
- 実測の最下層は `orchestrator/calibrator/runner.measure_point`。floor campaign は
  `_run_campaign_core` 内の closure `measure_fn` からこれを呼ぶ (s8b_floor_campaign.py:4531-4543)。
- `output/s8c-trial-registry/` は未作成、floor run の実績もゼロ。壊す既存 artifact は無い。
- production コードで rratio 80/20 を直書きするのは `trial_registry.HOLDOUT_BINDINGS` だけ。
  テストにも holdout 相当の workload dict は無い (= 現行の合法な非 holdout 測定は 1 件も
  巻き込まれない)。
- `s8b_floor_campaign.py` / `trial_registry.py` の bytes を pin する台帳・test・trust root は
  不在 (DW-O09 の閉包検索: py/json/md、insight の言及のみ)。
- 同機構の見送り裁定は無い。[T-523] は archive entry 231 から文面不変で持ち越されている。

## 2. 確定済みユーザー裁定 (本 wave が従うもの)

- 族一般化として「freeze 由来 holdout を実測へ渡す共通下位境界に admission と一回性台帳を
  置く」設計を起票し、**少なくとも 8b 側の実結線までを本 wave で行う**。
- **pilot だから緩めてよい方向の実装を採らない** (規律 2 の直接の防壁)。
- 受理集合を変えるなら D96 手続 (新 D + 境界テスト同時更新) に従い、事前登録変異を回す。
- best-of-N を閉じる実験単位の再定義は [T-524] の scope。本 wave では触らず台帳へ返す。
- 実装面は Codex author (D95)。

DW-G03 (族一般化には独立 2 例) は充足済み: 8c launcher (`p3_autonomous_workload_trial`) と
8b floor campaign が独立に同型欠陥を出している。これは親の判断ではなく起票時の確定事実。

## 3. 不変条件 (実装がこれを破ったら赤)

- I1. freeze 由来 holdout セルの実測は、sealed admission が無ければ **fail-closed で拒否**される。
  `mode == "pilot"` は緩和理由にならない。CLI flag・環境変数・引数での bypass を作らない。
- I2. admission の発行は一回性台帳への durable な行追記と不可分である。台帳へ書けなければ
  admission は発行されない (書込み失敗を「観測しなかった」ことにできない)。
- I3. 同一 key の二重観測は拒否される。key の単位は §5 (P3) で決める。
- I4. admission は caller が構築できない (`_seal` 方式、trial_registry の
  `assert_issued_trial_launch_admission` と同型)。
- I5. 既存テストの期待値を変えない。非 holdout の測定 (calibrator/p2_2/backoff 系など) の
  受理集合は 1 件も変えない。
- I6. 8c 側 (`trial_registry` の U-4 経路) の受理集合を変えない。本 wave は 8c を触らない。
- I7. 凍結領域 (`output/s8b-freeze/`, `output/env/`) へ書かない。台帳の書込み先は既存の
  guard を尊重する。

## 4. 成果物影響 (DW-G05 — 実装しなかった場合に何がどう変わるか)

- scope 1 (下位境界 gate): 実装しないと、freeze 由来 holdout セルの throughput が台帳外で
  何度でも観測でき、H1/H2 の holdout 性が失われる。**certified 選択の 8c 実験は
  「未観測 holdout での予測」という主張を失い、selector 検証結果の受理集合が
  「事前観測済みの点での事後検証」へ静かに変質する。**
- scope 2 (一回性台帳): 実装しないと、同じ holdout セルを複数回測って良い結果だけを
  下流へ渡せる。**proof chain に「何回観測したか」の参照先が存在しないため、
  レポートの floor 値・selector 判定が再現不能になる。**
- scope 3 (設計 D の起票): 実装しないと、3 番目の producer が同じ穴を再生産する。
  族一般化の正本が無く、**次の producer で同じ欠陥が受理集合を再び変える。**

## 5. 親の provisional 裁定 (攻撃対象)

以下は親の暫定判断であり、段 3 の敵対レンズは**これ自体を攻撃してよい**。

- **(P1) 共通下位境界 = `orchestrator/calibrator/runner.measure_point`。**
  根拠: 8b floor campaign も他の campaign driver も実測はここへ落ちる。producer ごとに
  gate を置く方式は「独立 2 producer で片方だけ塞がれた」という本件の失敗そのものなので、
  producer 側だけに 3 番目の gate を足す案は既定で採らない。
  リスク: calibrator が campaign 層へ依存する層反転。中立 leaf module を挟んで回避する想定。
  代案 (段 2/3 が評価すべき): (a) `_run_campaign_core` だけに置く producer 側 gate、
  (b) freeze loader (`s8b_freeze_io.load_verified_freeze`) に置く入口側 gate。
- **(P2) admission の発行根拠 = 人間が `freeze-protocol --confirm-user-freeze` で凍結した
  floor protocol + freeze bytes pin。** 8c 側と違い 8b には trial manifest が無いため、
  既存の人間承認 artifact をそのまま authority にする。新しい承認儀式を発明しない。
  リスク: pilot 実行を実質的に止めてしまう可能性 (floor run 実績はゼロなので現時点の実害は無い)。
- **(P3) 一回性の単位 = (freeze_sha256, protocol_sha256, holdout_id, configuration_id)。**
  1 セルにつき 1 つの admitted campaign run だけが観測できる。session/rep/retry は
  同一 admission の内側で消費し、`--resume` は既存行を再利用して二重消費しない。
  **[T-524] の実験単位 (prereg_generation, holdout, arm, replicate_slot) へは踏み込まない。**
- **(P4) 台帳の所在 = `output/s8b-holdout-observations/ledger.jsonl` (新規、append-only、
  exclusive-create セマンティクス)。** 凍結領域の外に置く。
- **(P5) 分割方針 = 実装単位 1 本 (Codex author 1 子)。** 新規 leaf module + `measure_point`
  への hook + floor campaign 結線 + テストは相互依存が強く、所有を素集合に割れない。

## 6. 成果物の形

1. 新規 leaf module (env 中立、名称は段 2 が決める) — holdout 署名の判定、sealed admission の
   発行、一回性台帳の append-only 書込み、`assert_issued_*` の 4 責務。
2. `orchestrator/calibrator/runner.measure_point` への fail-closed hook (P1 が生き残った場合)。
3. `orchestrator/campaign/s8b_floor_campaign.py` の結線 (admission 取得 → runner 実走)。
4. 新規テストファイル + 既存境界テストの追随 (D96)。
5. 新しい D (D96 の手続義務。族一般化の設計正本)。
6. 事前登録変異 spec (DW-M01) と本走結果。

## 7. 環境

- 実測環境: 本 worktree (Pegasus login node)。pytest / check_docs / 変異 harness は login で走る。
- ccbench 実測 (計算ノード) は本 wave では**行わない** — 本 wave の変更は測定を拒否する側の
  gate であり、実測値を生まない。受入全走は login node の既定経路で行う。

## 8. 本 wave が触らないもの

- [T-524] 実験単位の再定義 / best-of-N の閉塞 → 台帳へ返す。
- [T-525] holdout 束縛への skew/rmw/records/threads 追加 → 本 wave は「holdout をどう識別するか」
  を実装するので接触しうる。段 2 は **T-525 を実装せずに識別を成立させる最小形**を出すこと。
  はみ出す所見は裁定パッケージへ。
- 8c launcher (`p3_autonomous_workload_trial`, `trial_registry`) の受理集合。
- official mode の解禁 (§8 未裁定)。
