# 裁定パッケージ — [T-987] 8b oracle reviewed spec の設置形・contract test 改訂・事前登録値

```text
状態: 設計完了。実装差分ゼロ。durable artifact 0 件。APPROVED_SPEC_SHA256 は None のまま。
authority: 親 (dev-wave-t987-oracle-spec-design) の実測 + 段 2 プラン子 + 段 3 敵対 2 本。
起点: 2026-08-12 第 6 束ユーザー裁定 [T-499] Q1 = (b) の先行タスク [T-987]。
検証: 段 2 プラン (codex sol/max) + 段 3 敵対 2 本 (sol / luna、いずれも max) + 親の独立実測
  (子出力を読む前に固定、verbatim/s1-parent-independent-view.md)。
branch: worktree-dev-wave-t987-oracle-spec-design (docs + insights のみ)
実測基準: local main 330f67d0
```

## この控えを読む前に — 本 wave は承認を求めていない

段 3 敵対 2 本が独立に、**今ユーザーへ最終承認を求めるべきでない**と結論した。
親はこれを採用した。よって本控えが返すのは次の 3 種類だけである。

1. **今決める価値のある問が 1 件**だけある (§1)。これはデッドロックの結び目である。
2. **別の裁定へ合流させるべき項が 1 件**ある (§2)。独立に 2 例が揃った。
3. あとはすべて**記録** — 機構の欠陥 3 件と、承認できない理由 (§3〜§6)。

**前提が揃っていない値を「承認済み」にしてはならない。**
`APPROVED_SPEC_SHA256` は `None` のままであり、本控えのどの値も未承認である。

## §1 主問 — 8b oracle 本走の目的を先に決める (これだけが今決められる)

`run_contract.ccbench_pin` には**正しい値が 2 つある**。

- `d706650cdb31e442bef45b9b4216951d4fb40969` — 現凍結 floor を測った pin
  (`output/s8b-freeze/floor_protocol.json` の `ccbench_pin`)。
- `511c9538e4e8efa54b45cda62e72389ed3b706ec` — 現 submodule gitlink かつ
  `orchestrator/campaign/s8b_approved.py:65-67` の `CCBENCH_FULL_SHA`。

混ぜると実行時に binary receipt との照合で止まる
(`orchestrator/campaign/s8b_oracle_driver.py:949-958`)。**spec 単独では決まらない。**

**そしてこれはデッドロックになっている。**
[T-750] (floor v2 の実凍結) は「candidate spec の生成経路 ([T-987]) と事前登録値の確定を待つ」
と裁定されている (2026-08-12 第 6 束 Q1 = (b))。
一方 [T-987] の `ccbench_pin` は「floor を再測定するかどうか」で決まる。
**T-750 は T-987 を待ち、T-987 の値は T-750 の目的で決まる。**

- **(a)** 現凍結 floor をそのまま使って比較する本走にする。
  → `ccbench_pin = d706650c…`。floor 再測定は不要。既存 floor artifact の
  ccbench 版と oracle 本走の ccbench 版が一致する。
- **(b)** 現 gitlink で floor を再測定して v2 を作ってから本走する。
  → `ccbench_pin = 511c9538…`。[T-750] の floor 再測定が先行タスクになる。
- **親推奨 = (b)。** 理由: `s8b_approved.CCBENCH_FULL_SHA` が既に `511c9538…` を
  authority として持ち、`test_s8b_approved` が現 gitlink との一致を検査している。
  (a) を選ぶと oracle 本走だけが 2 世代前の ccbench に固定され、以後の submodule 更新の
  たびに「floor は旧 pin・repo は新 pin」の乖離を管理し続けることになる。
  ただし (b) は floor 再測定の計算コストを先に払う。**コストを避けたいなら (a) が正しい。**

## §2 合流 — 承認の trust root は [T-1116] と 1 回で決める

entry 511 の Q2 (人間承認の trust root) を、**独立の問として再提示しない。**

親は次を実測した。

- `verify_external_authority` / `AuthenticatedApproval` に相当する実装は
  `orchestrator/` 配下に 0 件。
- 署名の trust root も不在 — `gpg.format`、`user.signingkey`、
  `gpg.ssh.allowedSignersFile` はいずれも未設定。
- production loader が見るのは pin と disk bytes の SHA 一致だけである
  (`orchestrator/campaign/s8b_oracle_spec.py:182-200`)。
  test fixture も file を書いた直後に同じ hash を monkeypatch する
  (`orchestrator/tests/s8b_oracle_spec_fixture.py:102-112`)。

**同じ欠陥が、同日に別 wave でも独立に実測されている。**
[T-1116] wave (2026-08-15 23:16) が「批准済み既知赤 registry は trust root が無く成立しない」
として同型の欠陥を報告し、問 1 に (α) 外部 trust root 導入 / (β) 弱く再定義 /
(γ) 別択へ戻る、の 3 択を出している。

`DW-G03` の「族一般化には独立 2 例」がこれで成立した。
**oracle spec の承認 pin は、この決定の第 2 の consumer である。**
T-1116 問 1 を決めれば oracle 側も同時に決まる。承認手番を 2 回に割る必要はない。

**この決定が付くまで、oracle spec の承認 branch は有効化できない。**
pin と bytes と receipt を同じ手が書ける限り、どんな検査を足しても
「人間が承認した」ことは証明されない。書けるのは「人間が staged diff を review した」までである。

## §3 記録 — contract test 改訂の設計 (実装は承認後)

詳細は `contract-test-revision.md`。要旨だけ記す。

- 現行 `test_schema_v1_has_no_durable_manifest_candidate_or_reviewed_spec` は
  2 directory 配下の file が 0 件のときだけ緑になる。
- 改訂は **pin 状態で分岐する 2 状態設計**とする。分岐入力は `APPROVED_SPEC_SHA256` ただ 1 つ。
  pin が `None` の間、受理集合は 1 byte も広がらない。
- **案を 2 つに分けた。** 段 3 が「no-follow 全 entry 比較への置換は、拡大と同時に
  **縮小**を含む (空 subdirectory・directory symlink・FIFO を新たに拒否する)」と指摘したためである。
  - **B1 (純拡大):** 走査規則は現行のまま。`X0 ⊊ X1` が literal に成立する。
  - **B2 (拡大 + 安全側縮小):** 走査を no-follow 全 entry 比較へ置換。受理集合は交差になる。
  - **親推奨 = B1 を先に、B2 は別裁定。** 規律 2 が要求するのは広げる範囲の明示であり、
    同じ変更に未裁定の縮小を混ぜると承認された範囲が事後に判別できなくなる。
- **恒真化は B1/B2 のどちらでも解けない。** §2 の trust root が付くまで、
  この gate は「自分が書いた 2 つが一致する」ことしか証明しない。
  したがって **§2 と対で裁定されるべきである。**

## §4 記録 — 機構の欠陥 3 件 (C1〜C6 は変えていない)

**N1. 事前登録の判定式と、配線されている judge の判定式が別物である。**
`judge_oracle` の集約は各 trial の bench rep 中央値をさらに中央値へ畳む
**median of medians** で、configuration 間は float 完全一致による argmax である
(`orchestrator/campaign/s8b_oracle_judge.py:159-345`)。
同関数の docstring 自身が「この集約規則はまだ再凍結されておらず、実測開始前に
明示的な再凍結が必要である」と書いている。
一方 a12 stress-check が模擬しているのは `mean - q*sqrt(s/J) > 0`、
すなわち標本平均・標本分散・`q(J)` による下側信頼限界である。
さらに a12 の `J` は t139/a11 study の cluster 数であって oracle の replicate 数ではなく、
その選択規則は `J = min{ j in {4..13} : L_j^cert >= 0.80 }` という当該 study の検出力基準である。
下流 `s8b_verdict.py` の条件 3 も `median(on) - median(off) > floor` という
**点推定値の閾値判定**であり、統計的不確実性の gate ではない。
**帰結: a12 を oracle の `n` の根拠として提示してはならない。** proof chain の参照が誤る。

**N2. spec 層が単一 block 契約 (A3-3) を検査しない。**
`validate_reviewed_spec` は `build_schedule` を呼ぶだけで `_validate_schedule` を通さない
(`orchestrator/campaign/s8b_oracle_spec.py:123-137`)。
`build_schedule` は複数 block を許し (`s8b_oracle_manifest.py:221-270`)、
exact 1 件の検査は `_validate_schedule` にしかない (同 `:302-305`)。
**帰結: 複数 block の spec は承認を通過し、manifest 生成で初めて落ちる。**
承認手番と durable pin/receipt を消費した後に失敗する。
下流が fail-closed なので誤選択には至らず、欠陥は**承認整合性と可用性**に限定される。
**別 wave で schedule validator を共有公開関数化し、spec 承認前に発火させることを推奨する。**

**N3. `contract_sha256` は activation 世代の進行で失効する。**
`orchestrator/campaign/env_contract.py` には pegasus の generation 2 が存在し
その `contract_sha256` は `1346c20b…` だが、
`env_contract_activations/00000001.json` が active としているのは generation 1 の
`e576e9cd…` だけである。spec はこの値を pin し、driver が
`env_contract.lookup` の実値との完全一致を検査する
(`orchestrator/campaign/s8b_oracle_driver.py:882-885`)。
**帰結: activation serial が進むと、承認済み spec が実行時に止まる。**

## §5 記録 — `n` について書けること・書けないこと

**親は当初 `n = 8` を推奨値として起草したが、段 3 の反証を受けて撤回した。**

書けないこと:
- a12 からの導出 (§4 N1)。
- 較正からの導出。親が使った `1.253*sigma/sqrt(n)` は iid な**単一標本中央値**の漸近式であり、
  実際の estimator は reps=5 の内側 median の外側 median という二段推定である。
  certified 条件が使うのは on と off の**差**であり、2 推定量の共分散が要る。
  さらに Pegasus 登録済み較正は rr50・120 秒 noise run での within-run CV であって、
  対象 (rr20/rr80・extime=5) の between-run 分布ではない。
  between-run の実測は linux-baremetal の rr5/rr50/rr95・extime=3 しか存在しない。
  per-pair floor の実値も未確定である (`holdout_freeze.json` の `floor` は `null`)。
- **同じ仮定の変奏で必要な n が 7 から 14 まで振れる。** 段 3 がこれを算術で示した。
  結論が倍以上変わること自体が、現時点の導出が同定されていないことの証拠である。

書けること:
- **費用点の実測**: 純測定時間 = 12 cell × n × 5 rep × 5 秒。n=8 なら 2400 秒 = 40 分
  (retry・build・queue 待ちは別)。
- **`n` を導出可能にするために要る pilot の仕様**: Pegasus・rr20/rr80・extime=5・
  対象 configuration で outer trial median の between-run および paired 差の分布を取得し、
  誤選択率または検出力の目標を**事前固定**してから再導出する。

## §6 記録 — 事前登録値の段階別分類

詳細は `preregistration-values.md`。要旨は次のとおり。

- **ユーザーが選ぶ余地があるのは 4 項目だけ** — `n`、`master_seed`、block ID、`campaign_ids`。
  ただし §5 のとおり `n` には導出根拠が無く、他 3 件も今決める必要がない。
- **`clocks` と `env_tag` はユーザー承認項目ではない。** 親が当初そう分類したのは誤りで、
  `clocks` は env 契約が固定し (`env_contract.py` の pegasus generation、driver が完全一致要求)、
  `env_tag` は ratified freeze から継承される (`s8b_oracle_driver.py:862-869`)。
- **`holdout_ids` と `configuration_ids` は自由度ゼロ。** manifest 構築時に
  `sorted(freeze_holdouts)` との完全一致と、各 holdout の構成集合との一致が強制される
  (`s8b_oracle_manifest.py:1192-1213`)。
- **`binding_identity` は現時点で導出不能。** authority は
  `LaunchValidatedFreeze.binaries_by_cell` であり、これは ratified freeze の
  `launch_validate` からしか出ない (`s8b_ratified_freeze.py:766-794`)。
- **floor の除外理由 4 件の oracle への流用は未承認。** oracle validator は形式検査しかせず
  (`s8b_oracle_spec.py:171-177`)、oracle 固有の failure event との対応表が無い。
  **流用を既定にせず別裁定とする。**
- **`master_seed` の ISO-8601 JST は floor の先例であって oracle の要件ではない。**
  validator は非空文字列しか要求しない。形式を必須として提示すると先例を code contract と
  誤認させる。

## §7 先行 blocker (承認しても今は効かない理由)

- **active ratified freeze が不在。** `output/s8b-freeze/` に approval / active / revocation の
  世代 file が 1 件も無い。`build_approved_manifest` は spec より先に active freeze を読む。
- **`holdout_freeze.json` の `floor` と `budget` がともに `null`。**
- **承認の trust root が不在** (§2)。

**この 3 つが揃うまで、`APPROVED_SPEC_SHA256` に何を書いても本走には近づかない。**

## §8 本 wave が行っていないこと

`output/s8b-oracle-spec/` と `output/s8b-oracle-manifest-candidates/` への書込 (0 byte)、
`APPROVED_SPEC_SHA256` の設定、contract test の変更、`SCHEMA_VERSION` の変更、
機構 C1〜C6 の変更、実装差分。すべてゼロである。

## §9 先行 wave との関係

[T-499] 後継 wave (archive worklog entry 511) が同じ射程の設計を既に納品しており
(`output/insights/2026-08-12_t499-spec-producer-design/`)、その Q1〜Q4 は未裁定のままである。
**本 wave の新規差分は 3 点に限られる** (段 3 luna の指摘を採用)。

1. 受理集合の形式化と、拡大／縮小の分離 (§3)。
2. a12 と配線 judge の不整合、および `n` の導出不能性 (§4 N1、§5)。
3. spec 層の A3-3 未接続 (§4 N2) と contract_sha256 の世代失効 (§4 N3)。

entry 511 の producer 設計 (canonical path への設置形) は、現 HEAD の一次資料と照合して
**意味は一致**していた。file:line anchor の陳腐化のみが差分である
(`verbatim/s2-plan.md` の A 節に対照表がある)。
