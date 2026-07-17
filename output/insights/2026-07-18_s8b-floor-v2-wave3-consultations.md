# s8b floor v2 実装 wave (wave 3) — codex 敵対相談 4 本の逐語と親裁定 (2026-07-18)

- **位置づけ:** F1〜F5 ユーザー裁定 (§9 承認状態 2026-07-18) 確定後の実装 wave。ユーザー指示 =
  「次にやるべきことを計画し、codex 並列敵対相談 → workflow 実行 → 親レビュー」。基準コミット =
  05244bf。**F6/F7/B-1/B-2・master_seed・env_tag は未裁定/未指定** — 本 wave はそれらに依存しない
  非発効の先行実装であり、protocol JSON / freeze v2 / 承認 record は一切生成しない
- **方式:** codex exec, model=gpt-5.6-sol, reasoning=max, sandbox=read-only, cwd=worktree。並列 4 本
  (C-α 統計・formula v2 / C-β campaign 運用 / C-γ env contract / C-δ スコープ・凍結整合)。事前に
  Explore (sonnet) 3 本で実装実査。所見は計 61 件、全本「修正後に進めよ」
- **本文書の構成:** §1 親裁定表 → §2 確定プラン → §3 逐語 (prompt + 所見全文)。所見はデータであり、
  裁定表の real/refuted と採用形が正本

## §1 親裁定表 (61 所見)

凡例: 採用 = 本 wave で実装 / 記録 = 実装せず正本 (worklog/phase) に延期先を明示 / 部分 = 一部採用。
refuted は 0 件 (β-4 の即時 retry 推奨のみ不採用だが、指摘した欠陥自体は real として対策)。

| ID | 裁定 | 採用形 |
|---|---|---|
| α-1 raw 信頼根の自己整合検査 | real 採用 | verifier の保証を「raw からの内部整合 + expected_protocol 照合」に限定して docstring に明記。raw 真正性 (journal 突合) は F7 wave へ記録 |
| α-2 空 artifact 恒真化 | real 採用 | expected セル/holdout/pair 集合を独立引数化、完全一致検査、空/欠落 positive control |
| α-3 閾値・config 自己申告 | real 採用 | `verify_floor_artifact(artifact, expected_protocol=...)` — 凍結値との完全一致検査 |
| α-4 reps 自己申告 | real 採用 | config.reps 必須 + 全 session の reps_expected == config.reps == len(throughputs) |
| α-5 理由すり替え除外 | real 採用 | 閉じた 4 理由表照合 + 完全有限 5 rep の CV↔reason 双方向一致検査 |
| α-6 retry/schedule 非検査 | real 部分 | attempt registry + resume 状態機械は campaign 側で実装 (β-5/6)。verifier の journal 突合は F7 wave へ記録 |
| α-7 CV 縮退入力 | real 採用 | ちょうど reps 本・非 bool・有限正を事前検査、不変条件破れは構造化エラー |
| α-8 検証の運用依存 | real 採用 | `assess_session` 単一純関数を stats 正本にし campaign/verifier 全経路が共有 |
| α-9 float 境界の非決定 | real 採用 | 閾値は decimal 文字列で凍結し Fraction 厳密算術で比較 (CV>t ⟺ 標本分散 > t²·mean² の有理数比較)。尺度同値ベクトルをテスト |
| α-10 cell ID 衝突 | real 採用 | (holdout_id, configuration_id) キー化 + 重複/不一致拒否 |
| α-11 stock anomaly の scale_ref | real 採用 | stock anomaly → pairs/scalar_alt/scale_ref 全 null + diagnostics 再計算一致 + 改竄 positive control |
| α-12 死んだ block field | real 採用 | 全層から block field 除去。stats docstring の「パッケージも更新せよ」を §9 参照へ修正 (凍結資料は不変) |
| α-13 between-run 主張過大 | real 採用 | 主張を「単一 campaign 内 session dispersion に基づく floor」に限定、名称/report/docstring 統一 |
| α-14 CV 条件付き標本 | real 採用 | 全 attempt の CV/median/除外数を report に併記 + 受理標本の条件付けを限定として明記 |
| β-1 protocol 数値の別実験化 | real 採用 | validate_protocol が承認数値 (n=8/reps=5/retry=2/閾値/理由 4 行固定順) を完全一致で pin |
| β-2 版名の交差受理 | real 採用 | PROTOCOL_SCHEMA/SCHEDULE_ALGORITHM/RESULT/MANIFEST/journal schema を一括 v2 改版 + 交差拒否テスト |
| β-3 「均衡」未定義 | real 採用 | 契約を明文化: 8 round × 正規化済み 12 cell_id の完全置換、seq=0..95、入力順非依存 (sort + 一意検査)。96 スロット一括置換は拒否 |
| β-4 retry 時間位置の偏り | real 部分 | round 末尾消化は維持 (裁定文言「block 末尾 = 時間窓を保つ」の最近傍。読み替えはユーザー追認事項として表出)。retry 順は schedule 順で事前決定 + 他セル性能値に対する metamorphic test |
| β-5 crash-resume で retry 枠超過 | real 採用 | retry 枠は authorization の fsync 時点で消費。attempt registry (attempt_id/cell_id/retry_ordinal) で再発行禁止 |
| β-6 resume の schedule 再計算 | real 採用 | resume は manifest.schedule を権威とし再導出列と byte 一致検査。journal 状態機械で duplicate start/cell 不一致/attempt 一意性を全件検証 |
| β-7 launch 経路の post-probe 欠落 | real 採用 | post-probe を finally 相当で全経路実行。precedence を probe→launch→partial→CV→valid で固定、5/5 失敗は launch_failure |
| β-8 reason 自己申告の恒真 | real 採用 | α-8 と同一対策 + verifier が raw から reason を再導出して一致検査 |
| β-9 cell_cv_max が式に届かない | real 採用 | holdout_floors API に閾値を必須入力化、machine_anomaly 状態を cell JSON に持たせ再計算検証、md は JSON からのみ描画 |
| β-10 attempt 時間の台帳欠落 | real 部分 | attempt 単位の同一 process monotonic duration を journal に記録。wall cap の実 consumer (F3) は数値凍結後と明示記録 (δ-8 と同一) |
| β-11 finalization crash | real 採用 | result.json/md/terminal の冪等 finalization 状態機械 (既存物は hash 検証 + 欠落分のみ補完、上書きなし) |
| β-12 golden の実装出力貼付 | real 採用 | stdlib-only reference calculator + 手導出 literal + property test + 意図的 mutant 実行 + crash-resume 行列 |
| γ-1 tag 検査は attestation でない | real 記録 | Pegasus 登録段の必須要件 (qualification artifact + 実測照合)。二段完了 (γ-17) で記録 |
| γ-2 calibration_note 自由文 | real 採用 | calibration_ref を {path, sha256} 構造化参照に。isolation_policy を field 化 |
| γ-3 宣言だけの field は恒真 | real 採用 | wal_root_policy/capture field を廃し、実 capture は driver 実装 + 強制系は登録段へ |
| γ-4 oracle 側 receipt 欠落 | real 記録 | F7 wave (oracle 結線) へ。floor/oracle 共通 receipt 設計をその際に |
| γ-5 cross-process resume と単一 process | real 部分 | isolation_policy {single_process, allow_resume} field + run_campaign が allow_resume を強制。process identity (pid+starttime+uuid) を journal に記録。Pegasus entry は False で登録 (登録段) |
| γ-6 walltime 無検査 | real 記録 | 登録段の必須要件 (NQSV adapter + 事前予約)。「全廃棄 = 全数値不採用 (WAL は保存)」の意味論も記録 |
| γ-7 PID 可視性 probe 不在 | real 記録 | sentinel canary 機構は登録段。B-2 未裁定に付記 |
| γ-8 /scr への WAL | real 記録 | 登録段: resolved path/mount の allowlist 検査 |
| γ-9 oracle clocks/env_tag 非束縛 | real 記録 | F7 wave: oracle env は ratified freeze から導出、clocks は contract 一致検査 |
| γ-10 S2 profile の hardcode | real 記録 | 「legacy は v2 経路外」の反例として採録。S2 verification profile の contract 束縛は F7/oracle wave |
| γ-11 build cache の env 非分離 | real 記録 | 登録段: cache root/key を contract_sha256 で namespace 分離 |
| γ-12 absolute monotonic の永続化 | real 採用 | artifact/journal から absolute monotonic を排し duration + UTC のみ記録 |
| γ-13 REGISTRY 可変性 | real 採用 | private MappingProxyType + register API なし + __post_init__ 検証 (slug/一致/重複) |
| γ-14 fixture の tag 戦略 | real 採用 | 実行系 fixture は linux-baremetal、構造単体テストは非実行 tag 可。未知 tag no-write 回帰 + closure ソース検査 → 実引数 spy 化 |
| γ-15 p2_2 逆転は不要 | real 採用 | p2_2 逆転を撤回。歴史的定数は不変、contract と p2_2 の値一致テストのみ追加 |
| γ-16 v2 境界の機械化 | real 採用 | v2 モジュール閉包に env literal (linux-baremetal/1800/interleave 等) を禁止する AST 検査テスト |
| γ-17 「F4 完了」の過大宣言 | real 採用 | 完了条件を二段に分離して記録: 今回 = core + floor 結線 + テスト、登録段 = qualification + tag + registry entry |
| δ-1 「全裁定完了後」との矛盾 | real 採用 | wave を非発効先行実装に限定し worklog に例外と理由を明記。protocol/freeze/approval 不生成。M 延期・E は core + floor 結線のみ |
| δ-2 版一括改版 | real 採用 | β-2 と同一 |
| δ-3 official 拒否の恒偽 | real 採用 | core run_campaign で無条件拒否 + 直接 API 呼び出しの no-write テスト |
| δ-4 retry 読み替えの無断性 | real 部分 | round 定義と retry 位置を worklog に実装解釈として明記しユーザー追認を求める (β-4 と同一実装) |
| δ-5 settle_timeout の第五理由 | real 部分 | floor 経路の settle 使用実態を実装時に確認。不使用なら「floor は settle を持たない」と記録、使用なら campaign abort (閉表 4 行は増やさない安全側) + ユーザー表出 |
| δ-6 S/C の CV 二重実装 | real 採用 | α-8/β-8 と同一 (assess_session 共有) |
| δ-7 scale-adequacy の脱落 | real 採用 | protocol v2 に scale_adequacy_rel_tolerance (decimal 文字列) を必須追加。consumer 結線は F7 wave と明示記録 (F1 完了と数えない) |
| δ-8 F3 レーン不在 | real 採用 | F3 runtime 実装は数値凍結後と明示記録。今回は attempt duration 台帳 (β-10) のみ |
| δ-9 Lane M の二度手間 | real 採用 | Lane M を F7 wave へ全面延期 (fixture 群不接触) |
| δ-10 pairs のキー不一致 | real 採用 | freeze-facing pairs = configuration_id、raw/diagnostics = cell ID と契約固定。S→C 結合テストを先行作成 |
| δ-11 G12 の capture 縮小 | real 部分 | γ-5/γ-17 と同一の二段記録。allow_resume 強制 + identity 記録のみ今回 |
| δ-12 registry 内容変更と tag 一致 | real 部分 | contract_sha256 を実装し protocol 凍結時に fingerprint 束縛する設計を記録。oracle 結線は F7。floor は lookup 置換 (同値 + 拒否強化) のみ |
| δ-13 contract の holdout 座標上書き | real 採用 | contract に records/threads を持たせない。登録段で calibration との適合検証を要件化 |
| δ-14 凍結不接触の手順依存 | real 採用 | 凍結 4 対象 (裁定資料 2 + holdout_freeze.json + s8b_holdout_freeze.py) の sha256 を commit 前後で機械照合。stats docstring 修正 (α-12) |
| δ-15 unknownness 汚染 | real 採用 | 新規テスト/golden は synthetic 軸のみ + 新規ファイルへの holdout 軸 literal 混入を検査 |
| δ-16 mutant の同時変異 | real 採用 | β-12 と同一 + 指定 mutant 集合 (median/mean、stdev/pstdev、>/>=、gate 除去、null skip、stock 伝播、key 混同) の機械実行 |
| δ-17 レーン間結合の中間赤 | real 採用 | S+C 原子 commit (E → S+C の順)。全 lane 合成後に結合レビュー段 + env mismatch no-write / direct official 拒否の通し検査 |
| δ-18 テスト設計の低枠化 | real 採用 | S/C/E のテスト設計・境界設計は opus。sonnet は fixture 一括置換・docs 整形・mutant 機械実行のみ |

## §2 確定プラン (裁定反映後)

**commit 順序** (各 commit で全走緑 + 凍結 4 対象 sha256 不変を確認):

1. **本 insights 凍結** (この文書)
2. **Lane E (env contract core):** 新規 `orchestrator/campaign/env_contract.py` (stdlib leaf) —
   frozen dataclass `ExecutionEnvironmentContract` {env_tag, clocks_per_us, numactl: tuple,
   isolation_policy {single_process, allow_resume}, calibration_ref {path, sha256},
   contract_sha256 (canonical JSON の導出 property)}。private MappingProxyType registry
   (linux-baremetal のみ)、lookup() fail-closed。p2_2 は不変 + 値一致テスト。AST env-literal
   検査テスト。テスト設計 = opus、レーン内敵対レビュー opus×2
3. **Lane S+C (floor v2、原子 commit):** §1 の採用所見をすべて反映した
   `s8b_floor_stats.py` + `s8b_floor_campaign.py` + テスト全面改訂。核: assess_session 単一純関数 /
   Fraction 厳密閾値 / verify_floor_artifact(artifact, expected_protocol) / 8 round 置換 schedule /
   attempt registry + authorization 時点の枠消費 / resume 状態機械 + manifest.schedule 権威 /
   post-probe finally / core official 拒否 / 冪等 finalization / duration 台帳 / env_contract lookup
   結線 / pairs = configuration_id / stock anomaly 全 null / reference calculator + mutant 実行。
   実装・テスト設計 = opus、敵対レビュー opus×2 (fail-open/HARKing レンズ + 統計・境界レンズ) +
   結合レビュー
4. **docs:** worklog (δ-1 の例外明記 + β-4/δ-4/δ-5 のユーザー追認事項 + 二段完了・延期台帳) /
   phase3 進捗 / pegasus-runbook §7 に登録段要件 (γ-1/6/7/8/11 + D59) を追記

**wave から除外 (延期先明示):** Lane M (→ F7 wave) / oracle 結線・G12 oracle receipt・S2 profile
束縛 (→ F7 wave) / G12 強制系・attestation・cache namespace・Pegasus registry entry (→ Pegasus
登録段) / F3 runtime (→ protocol JSON 数値凍結後) / B-1/B-2 依存 (→ 各裁定後)

## §3 逐語 (prompt + 所見全文)

以下、C-α/C-β/C-γ/C-δ の依頼 prompt と所見全文を無編集で凍結する。

---

### C-α 依頼 prompt (逐語)

```markdown
# 敵対的検証依頼 C-α — floor formula v2 (統計・fail-closed 検査)

あなたは敵対的レビュアーである。以下の実装プランを攻撃し、欠陥を挙げよ。プランを褒める必要はない。
所見は番号付きで `[severity: must-fix|should|nit] [攻撃シナリオ] [根拠 file:line] [提案]` の形式。
最後に「総合判定: このまま進めよ / 修正後に進めよ / やめよ」を 1 行で。sandbox は read-only、
repo を自由に読んでよい。

## 所与 (再交渉不可のユーザー裁定、2026-07-18)

floor protocol パッケージ (output/insights/2026-07-16_s8b-floor-protocol-package.md、凍結済み裁定資料)
に対するユーザー裁定が確定している (正本 = docs/phase3-8b-descriptor-design.md §9 承認状態):

- **F1 (修正付き採用):** 2 block 構造・min_block_gap_s=1800・delta_c 項を**廃止** (トップ会議の CC 実験
  水準に合わせ温度/バックグラウンド微細変動は追わない)。式は `floor_pair(c) = max(u_noise(c),
  wired_min_rel_floor × m_stock)`。**異常検出 2 段を追加**: session 内 5 反復の CV (stdev n-1 / 算術
  平均) > 10% → session 無効 (`performance_anomaly`、F2 の閉じた除外理由表の 4 行目) / セル間 CV
  (`cv_c = s_c / fmean(有効 session medians)`) > 15% → 当該 pair floor = null (`machine_anomaly`)。
  閾値は protocol JSON に事前凍結、全セル同一適用、検出は無効化・判定不能方向にのみ使う。
  n_sessions=8 / reps=5 exact / per-pair table / fail-closed null / scale-adequacy ±10% / seed 均衡
  置換 / scalar_alt 併記 / 「記述的効果量 + noise gate、α・検定力未保証」の限定は維持
- F2〜F5 は承認済み (F2 = 閉じた除外表 + retry 通算 2 + append-only + forward-only resume + strict
  probe / F3 = 三層 budget / F4 = env contract 抽象採用 / F5 = per-pair freeze 形状)。
  **F6/F7 (承認束縛・v2 検証意味論) と B-1 (NaN strict 化)・B-2 (probe 子孫除外) は未裁定** — 本 wave
  はこれらに依存する実装をしない

裁定自体への異議は不要。ただし裁定が実装と矛盾・曖昧さを生む場合は所見として挙げよ。

## 対象ファイル (読め)

- `orchestrator/campaign/s8b_floor_stats.py` (formula v1 実装、430 行。改訂対象)
- `orchestrator/tests/test_s8b_floor_stats.py` (23 テスト)
- 参考: `orchestrator/campaign/s8b_floor_campaign.py` (呼び手。C-β が別途攻撃するので深追い不要)

## 私のプラン (これを攻撃せよ)

1. `FORMULA_ID = "s8b-floor-stats/v2"` に改版 (v1 は git 履歴に残る)。artifact の formula 欄も v2
2. `cell_stats()`: block_medians / block 有効性検査を削除。セル有効 ⇔ 有効 session 数 == n_sessions。
   `cv` 診断値 (s_c / fmean) は維持
3. `holdout_floors()`: d1/d2/delta_c と 2-block ValueError を削除。
   `floor_pair(c) = max(u_noise(c), wired_min_rel_floor × m_stock)`。
   **machine_anomaly**: セル c (stock 含む) が有効かつ `cv_c > cell_cv_max` (0.15) → stock なら当該
   holdout の全 pair null、非 stock なら当該 pair のみ null。diagnostics に
   `machine_anomaly: [cell_id...]` を明示記録。null 伝播で scalar_alt は従来どおり null
4. **session 内 CV**: 新設の純関数 `session_rep_cv(throughputs)` (stdev n-1 / fmean)。判定は厳密超過
   (`> session_cv_max`、0.10)。campaign 側が計測直後に判定して `excluded_reason=performance_anomaly`
   を付す。stats 側の `session_median()` は従来どおり excluded_reason is None を要求するので、
   anomaly session は自動的に median を作らない
5. `verify_floor_artifact()`: 双方向照合を追加 — (a) `excluded_reason == "performance_anomaly"` の
   session は記録された throughputs から CV を再計算して実際に閾値超過であること (偽除外の検出)、
   (b) 有効扱いの session は CV が閾値以下であること (異常隠蔽の検出)、(c) machine_anomaly の
   pair null / 非 null が cv_c 再計算と一致すること。閾値は artifact config から読む
   (`session_cv_max` / `cell_cv_max` を config 必須キーに追加、`blocks`/`replicates_per_block` を削除)
6. テスト: delta_c 支配テスト・2-block 防御テストは廃止。u_noise / wired 支配 golden は手計算値で
   再作成。新設: 閾値ちょうど (10.0% / 15.0%) は anomaly でないこと、僅かに超えると anomaly になる
   こと、verify の双方向照合が改竄 (偽除外 / 異常隠蔽 / pair null 改竄) を検出する positive control

## 特に攻撃してほしい観点

- 統計的整合: block 対比 (delta_c) を失った floor が between-run 変動の下限としてどの範囲を失うか。
  「限界として報告に明記」で足りるか、それとも s_c の定義側で拾えるドリフトがあるか
- fail-open 面: 異常ゲートを回避する artifact 改竄・driver 実装バグが verify_floor_artifact で
  必ず捕まるか。捕まらない改竄経路を具体的に構成してみよ
- 恒真検証 (F14 型): 発火し得ない検査・謳うだけの保証がプランに含まれていないか
- 数値境界: reps=5 の stdev n-1、fmean=0 / 負値 / 単一有効 session、cv 計算の除算、閾値の浮動小数
  比較 (0.1 の 2 進表現) による境界の非決定性
- cherry-pick 面: 性能値に基づく除外 (performance_anomaly) + retry (通算 2) の組合せが「良い値が
  出るまで測り直す」選択経路をどの程度開くか。閾値が事前凍結・全 attempt 記録という防御で十分か
- machine_anomaly の stock 特例 (全 pair null) は fail-closed として一貫か、過剰か
```

### C-α 所見 (逐語)

1. [severity: must-fix] [攻撃シナリオ] 全 throughput を都合のよい値へ書き換え、cells・floors・除外理由も同じ v2 関数で再生成すれば完全一致して通る。これは raw を信頼根にした自己整合検査であり、artifact 全体の改竄検出ではない。 [根拠 orchestrator/campaign/s8b_floor_stats.py:296-310, orchestrator/campaign/s8b_floor_stats.py:356-408] [提案] この wave では保証を「raw から導出値を再計算する内部整合検査」に限定する。別入力の manifest・journal・凍結 protocol との照合まで実装できないなら、raw 真正性の保証は F6/F7 裁定後まで明示的に保留する。

2. [severity: must-fix] [攻撃シナリオ] `sessions=[]`, `cells={}`, `floors={}` と必要 config だけを置くと、現行 verifier は実際に `[]` を返す。holdout または cell 一式を sessions・cells・floors から同時削除しても同じ恒真化が起きる。追加予定の CV 検査も空集合では発火しない。 [根拠 orchestrator/campaign/s8b_floor_stats.py:329-410, orchestrator/tests/test_s8b_floor_stats.py:311-338] [提案] 凍結 manifest 由来の期待 holdout・cell・pair 集合を独立引数にし、完全一致を先に検査する。空 artifact、holdout 丸ごと削除、cell 丸ごと削除を positive control に加える。

3. [severity: must-fix] [攻撃シナリオ] `session_cv_max` と `cell_cv_max` を 1.0 に改竄し、derived fields を再生成すれば異常ゲートを停止できる。formula・`n_sessions`・wired floor も artifact 内の自己申告値だけなら同様である。現行 verifier は top-level `formula` を読まず、config は必須キーの存在しか検査しない。 [根拠 orchestrator/campaign/s8b_floor_stats.py:268-327, orchestrator/campaign/s8b_floor_campaign.py:1013-1040] [提案] `verify_floor_artifact(artifact, expected_protocol=...)` とし、外から渡した凍結値との完全一致、formula v2、config の厳密なキー集合・型・有限性を検査する。artifact 自身の protocol hash は信頼根にしない。

4. [severity: must-fix] [攻撃シナリオ] 4 rep しかない session の `reps_expected` も 4 に変えれば有効になる。現行 verifier は top-level `reps=5` を無視し、各 session の自己申告 `reps_expected` をそのまま採用する。新しい CV 関数も長さを固定しなければ同じ穴を残す。 [根拠 orchestrator/campaign/s8b_floor_stats.py:59-81, orchestrator/campaign/s8b_floor_stats.py:268-287, orchestrator/campaign/s8b_floor_campaign.py:1025-1037, docs/phase3-8b-descriptor-design.md:342-345] [提案] config に `reps=5` を必須化し、全 record について `reps_expected == config.reps == len(throughputs) == 5` を検査する。4/5 と、8 個の 1-rep session を使う改竄テストを追加する。

5. [severity: must-fix] [攻撃シナリオ] CV 20% の session を `performance_anomaly` ではなく `nonfinite_or_partial_output` や `competing_process` と記録すれば、計画中の (a) にも (b) にも入らず除外できる。さらに任意の非空文字列でも `session_median()` は無効扱いする。 [根拠 orchestrator/campaign/s8b_floor_stats.py:66-67, orchestrator/campaign/s8b_floor_stats.py:270-287, docs/phase3-8b-descriptor-design.md:350-355] [提案] 全 excluded session を閉じた4理由表と必須証拠まで検査する。完全・有限な5 rep については、より優先する probe/launch 証拠がない限り、CV と `performance_anomaly` の双方向一致を要求する。

6. [severity: must-fix] [攻撃シナリオ] 悪い planned attempt を削除し、良い retry を複製して有効 session を8件にすれば `n_valid == n_sessions` を満たせる。`seq` の一意性、予定 schedule、retry 通算2、first-authorized-valid、全 attempt 記録は stats verifier の検査対象になっていない。 [根拠 orchestrator/campaign/s8b_floor_stats.py:126-130, orchestrator/campaign/s8b_floor_stats.py:346-361, orchestrator/campaign/s8b_floor_stats.py:275-288, docs/phase3-8b-descriptor-design.md:350-354] [提案] manifest と append-only journal を突合し、planned seq の完全性・重複禁止・開始済み attempt の終端・retry 上限・最初の有効 retry 以後の再測定禁止を検査する。`bool("false") is True` になる coercion も廃止し厳密型にする。

7. [severity: must-fix] [攻撃シナリオ] `session_rep_cv()` に空列・1件・0/負値・NaN/Inf・bool を渡すと、`StatisticsError`、ゼロ除算、NaN 比較の偽、または意図しない数値受理になり得る。さらに `n_sessions=1` なら cell は valid なのに `s=cv=None` となり、floor 合成で `None ** 2` が発生する。 [根拠 orchestrator/campaign/s8b_floor_stats.py:71-80, orchestrator/campaign/s8b_floor_stats.py:142-150, orchestrator/campaign/s8b_floor_stats.py:243-247] [提案] CV 計算前に「ちょうど5件・非 bool の有限正数」を検査し、不正値は明示的な protocol error とする。`n_sessions == 8`、有限正の平均、有限非負の `s/cv` を固定し、`holdout_floors()` でも不変条件破れを例外漏出ではなく null/error に倒す。

8. [severity: should] [攻撃シナリオ] anomaly 判定を campaign のラベル付与だけに置くと、`cell_stats()` を直接呼ぶ経路は CV 超過 session を有効化できる。verifier を必ず後段で呼ぶという運用依存になり、stats モジュールが式と有効性の正本であるという契約を満たさない。 [根拠 orchestrator/campaign/s8b_floor_stats.py:4-7, orchestrator/campaign/s8b_floor_stats.py:14-25, orchestrator/campaign/s8b_floor_campaign.py:709-724] [提案] raw・reps・閾値から validity/CV/理由を返す単一の純関数を stats 側の正本にし、campaign、`session_median()`、`cell_stats()`、verifier の全経路から必ず呼ぶ。

9. [severity: must-fix] [攻撃シナリオ] 数学的には CV=10% の `[0.9, 0.9, 1.0, 1.1, 1.1]` が、Python float では約 `0.10000000000000003` となり異常扱いされる。一方 `[90,90,100,110,110]` はちょうど `0.1` になり、単一の境界テストでは欠陥を隠せる。15% 境界も同型である。 [根拠 orchestrator/campaign/s8b_floor_stats.py:142-147, docs/phase3-8b-descriptor-design.md:336-340] [提案] JSON 数値の表現と比較意味論を凍結し、Decimal/Fraction による分散と閾値二乗の厳密比較などで境界を定義する。任意 epsilon は「僅かに超過」を通すため不可。尺度だけ変えた数学的同値ベクトルもテストする。

10. [severity: must-fix] [攻撃シナリオ] 同じ `cell_id` に複数 `configuration_id` を混ぜると検出されず、stock 判定は先頭 record の configuration だけで決まる。さらに別 holdout で同一 `cell_id` を再利用すると、global な `recomputed_cells[cid]` が後勝ちで上書きされる。 [根拠 orchestrator/campaign/s8b_floor_stats.py:119-122, orchestrator/campaign/s8b_floor_stats.py:346-361, orchestrator/campaign/s8b_floor_stats.py:391-400] [提案] 各 cell 内の holdout/configuration 一致、canonical cell ID、manifest との対応を検査する。内部キーは少なくとも `(holdout_id, configuration_id)` にし、global ID 重複を拒否する。

11. [severity: must-fix] [攻撃シナリオ] stock が machine anomaly でも `scale_ref=m_stock` を残す実装になれば、全 pair は null なのに異常 stock 値だけが消費可能になる。また plan の照合対象は pair の null/non-null だけで、`diagnostics.machine_anomaly` は削除・偽造しても検出されない。 [根拠 orchestrator/campaign/s8b_floor_stats.py:216-220, orchestrator/campaign/s8b_floor_stats.py:254-262, orchestrator/campaign/s8b_floor_stats.py:406-408, orchestrator/campaign/s8b_floor_campaign.py:932-938] [提案] stock anomaly は全 pairs・`scalar_alt`・`scale_ref` をすべて null にする。全 pair null 自体は stock が全式の共通入力なので一貫する。diagnostics も再計算結果との完全一致を検査し、改竄 positive control を置く。

12. [severity: should] [攻撃シナリオ] config の block keys だけを削り、`SessionRecord.block`、`CellStats.block_medians`、artifact schema、verifier 比較を残すと、任意値を入れても判定に効かない F14 型の死んだ保証になる。また現行 docstring は凍結パッケージ本文も同時更新せよと命じ、裁定正本の「パッケージは不変」と矛盾する。 [根拠 orchestrator/campaign/s8b_floor_stats.py:15-17, orchestrator/campaign/s8b_floor_stats.py:50-52, orchestrator/campaign/s8b_floor_stats.py:91-101, orchestrator/campaign/s8b_floor_stats.py:268-272, docs/phase3-8b-descriptor-design.md:325-335, docs/phase3-8b-descriptor-design.md:381-389] [提案] block 関連 field を全層から除去するか、one-pass schedule と照合する実 consumer を明記する。formula v2 の正本参照先を phase §9 に変更し、凍結済み裁定資料は編集しない。

13. [severity: should] [攻撃シナリオ] 連続1パス中に各 cell が実際に踏んだ時点の散らばりは `s_c` が一部拾うが、別 run・cold boot・未観測温度状態・pair contrast の時間変化は拾わない。seed schedule は各反復で単に shuffle するだけで、cell の時刻位置を均衡させる設計ではないため、時間と構成が交絡しても `s_c=0` が成立し得る。 [根拠 orchestrator/campaign/s8b_floor_stats.py:4-12, orchestrator/campaign/s8b_floor_campaign.py:402-421, docs/phase3-8b-descriptor-design.md:330-345] [提案] `between-run variation の下限` という主張をやめ、「単一 campaign 内で観測された session dispersion に基づく floor」と限定する。限界記載は失われた変動を回復しないが、裁定どおり delta を戻さないなら、名称・report・consumer の主張範囲をこの意味へ統一する。

14. [severity: should] [攻撃シナリオ] 低 throughput と高 CV が相関する熱 throttling では、低く不安定な session が機械的に除外され、高く安定した retry だけで `s_c` が計算される。事前閾値・全 attempt 記録・上限2は裁量的な「良い値まで再測」を抑えるだけで、CV 条件付き標本への構造的選択を消さない。 [根拠 docs/phase3-8b-descriptor-design.md:336-342, docs/phase3-8b-descriptor-design.md:350-354, orchestrator/campaign/s8b_floor_stats.py:66-67] [提案] #6 の履歴検査を必須化した上で、全 attempt の CV・median・除外数を報告し、受理標本が `CV≤10%` に条件付けられていることを限定に明記する。除外値を floor 改善へ再利用せず、感度表は記述用途だけにする。

総合判定: 修正後に進めよ

---

### C-β 依頼 prompt (逐語)

```markdown
# 敵対的検証依頼 C-β — floor campaign 運用意味論 (block 廃止後の driver 設計)

あなたは敵対的レビュアーである。以下の実装プランを攻撃し、欠陥を挙げよ。プランを褒める必要はない。
所見は番号付きで `[severity: must-fix|should|nit] [攻撃シナリオ] [根拠 file:line] [提案]` の形式。
最後に「総合判定: このまま進めよ / 修正後に進めよ / やめよ」を 1 行で。sandbox は read-only、
repo を自由に読んでよい。

## 所与 (再交渉不可のユーザー裁定、2026-07-18)

正本 = docs/phase3-8b-descriptor-design.md §9 承認状態。要点:

- **F1 (修正付き採用):** 2 block 構造・min_block_gap_s・delta_c 項を廃止。session 内 5 反復の
  CV > 10% → `performance_anomaly` (除外理由表の 4 行目、証拠 = 全反復値、retry は既存スロット内、
  実時間は持ち時間の消費として計上) / セル間 cv_c > 15% → `machine_anomaly` (pair null)。seed 均衡
  置換は維持。n_sessions=8 / reps=5 exact
- **F2 (承認):** 閉じた除外理由表 (competing_process / launch_failure / nonfinite_or_partial_output
  + 新 performance_anomaly)。retry_slots_per_cell=2 (campaign 通算、first-authorized-valid のみ採用、
  全 attempt 計上)。journal append-only + fsync、manifest/result create-only。resume は同一
  protocol/freeze/manifest/binary hash 限定 forward-only + binary 再ハッシュ。単独性臨界区間 =
  probe→measure→post-probe→journal、strict probe (rc=1 のみ競合なし、検査不能は campaign abort)。
  correctness-red は floor に存在しない
- **F4 (修正付き):** env contract 抽象を採用 (C-γ が別途攻撃。本依頼では「env_tag 等価比較が
  contract registry の fail-closed lookup に置き換わる」ことだけ前提にせよ)
- **F6/F7 未裁定**: official mode の一律拒否 (`main` の rc=2) は維持。**B-2 (probe の自己子孫除外を
  自 PID のみに狭めるか) も未裁定**: strict_probe の admission 意味論は今回変えない

## 対象ファイル (読め)

- `orchestrator/campaign/s8b_floor_campaign.py` (1397 行。改訂対象)
- `orchestrator/tests/test_s8b_floor_campaign.py` (24 テスト、_protocol() ヘルパ 122-147)
- 参考: `orchestrator/campaign/s8b_floor_stats.py` (formula は C-α が攻撃。境界だけ見よ)

## 私のプラン (これを攻撃せよ)

1. `_PROTOCOL_KEYS`: `blocks` / `replicates_per_block` / `min_block_gap_s` を削除、
   `session_cv_max` / `cell_cv_max` を追加 (厳密一致検査は維持)。`validate_protocol` の
   blocks×replicates 検査 (260-272) を `n_sessions` 単独検査へ。閾値は (0,1] 域検査
2. schedule: `build_schedule` を「round r = 1..n_sessions ごとに 12 セルを seed 置換」に再設計。
   seed 導出 = `sha256(f"{master_seed}/{r}")` 先頭 8 byte。エントリは `{seq, round, cell_id}`
   (block/replicate 廃止)。`SCHEDULE_ALGORITHM` 定数を v2 名に改版。golden pin テストは手計算で再作成
3. `_Runner`: block 走査 (874-908) を round 単一パスに。`_wait_gap` / `min_gap` 削除。
   **retry は「失敗が起きた round の末尾で消化」** (campaign 通算 2/cell は不変、_retries_used の
   意味論維持)。`_block_deficit` → `_round_deficit` 相当に改名・再定義
4. `performance_anomaly` 検出: `_session_record` (705-750) で計測直後に、reps が exact に揃い全値
   有限正の場合のみ `session_rep_cv(throughputs) > session_cv_max` を判定して
   `excluded_reason="performance_anomaly"` を設定。**precedence**: launch_failure →
   nonfinite_or_partial_output → performance_anomaly (CV は完全な計測にしか定義されない)。
   証拠 = journal に全 throughputs (既存記録) + cv 値を明示追記。`_REASON_PERFORMANCE_ANOMALY`
   定数を閉じた表 (102-104) の 4 行目に追加
5. `assemble_manifest` / `assemble_result`: blocks 系フィールド (638, 641-642, 950-952) を除去、
   config (1031-1037) に `session_cv_max` / `cell_cv_max` を追加。`_render_result_md` に除外理由別
   件数 + machine_anomaly セル一覧を追記
6. resume/journal: schedule schema が変わるため、旧 schema の journal/manifest は
   `_load_resume_manifest` の protocol_sha256 一致検査で自然に拒否される (実走履歴はまだ無い)。
   forward-only / binary 再ハッシュ / create-only は不変
7. env_tag 検査 (1150-1154): p2_2.ENV_TAG 等価比較 → env contract registry lookup (C-γ 詳細)
8. official mode 拒否 (1365-1372) は byte も変えない

## 特に攻撃してほしい観点

- **均衡置換の設計**: round ごと 12 セル置換 vs 96 スロット全体置換 vs その他。裁定は「seed 均衡
  置換の維持」— round 構造を保つ私の案が「均衡」の意味を正しく保存しているか。retry を round 末尾に
  置くことがセルの時間局所性・置換の均衡性をどう歪めるか
- **retry 消化タイミングの選択経路性**: round 末尾消化は「その round の他セルの結果を見てから retry
  する」情報経路を作らないか (attempt は機械発火・性能値非参照だが、壁時計上の位置が変わる)。
  即時 retry / campaign 末尾 retry との比較で fail-closed 上の優劣
- **performance_anomaly の precedence と閉じた表**: 部分欠測と CV 異常が同時に起きる系列、CV が
  計算不能 (fmean=0 等) な系列で reason が一意に決まるか。`_check_reason` の閉じた表照合と新 reason
  の整合。probe 臨界区間 (probe_after) と CV 判定の順序
- **HARKing/cherry-pick 面**: CV 閾値超過 session の retry が「静かになるまで測る」をどの程度許すか。
  F1 裁定 (retry 既存スロット内) の枠内で最も選択経路が狭い設計はどれか
- **journal/resume 整合**: 新旧 schema 混在・crash 途中再開・retry と forward-only の相互作用で、
  「同一 session の二重実行」「retry の複数回消化」が構造的に排除されているか
- **テスト戦略**: _protocol() ヘルパ改訂で 24 テスト全数に触る際、golden 再計算が「実装を走らせて
  出力を貼る」堕落 (バグごと golden 化) に落ちない具体的手順。mutation-killing の保存
```

### C-β 所見 (逐語)

1. `[severity: must-fix] [攻撃シナリオ: n_sessions=1、reps=1、retry_slots=0、CV 閾値=100%、allowed reasons に correctness-red を追加した protocol が通り、承認済み標本設計を別実験へ変質させる。現プランの「(0,1] 検査」と reason 定数追加だけでは閉じた表にならない] [根拠 docs/phase3-8b-descriptor-design.md:336-355, orchestrator/campaign/s8b_floor_campaign.py:254-315] [提案: validator で n_sessions==8、reps==5、retry_slots_per_cell==2、session_cv_max==0.10、cell_cv_max==0.15 を必須化する。allowed_excluded_reasons も4理由の完全一致・固定順へ正規化し、欠落・余分・並べ替えを開始前に拒否する]`

2. `[severity: must-fix] [攻撃シナリオ: protocol・manifest・result の意味と形を壊しても全て v1 を名乗り続ける。resume loader は manifest schema を検査しないため、旧形または部分的に新しい manifest を protocol hash だけで受け入れ得る。「protocol hash で自然拒否」は schema 境界の代替にならない] [根拠 orchestrator/campaign/s8b_floor_campaign.py:84-88, orchestrator/campaign/s8b_floor_campaign.py:1263-1283] [提案: PROTOCOL_SCHEMA、MANIFEST_SCHEMA、RESULT_SCHEMA、FORMULA_ID、journal schema を一括改版する。resume 時は schema と全必須キーを strict 検証し、旧版を明示拒否する。SCHEDULE_ALGORITHM だけの改版で済ませない]`

3. `[severity: should] [攻撃シナリオ: 8個の独立 shuffle は「各 round に各セル1回」は保証するが、同一セルが毎回先頭付近になるような位置偏りは許す。一方、96スロット全体の multiset shuffle は連続出現と長い空白まで許し、さらに弱い。現プランは何を「均衡」と呼ぶか未定義なので、どちらも実装者が正当化できる] [根拠 docs/phase3-8b-descriptor-design.md:330-344, orchestrator/campaign/s8b_floor_campaign.py:397-422, orchestrator/tests/test_s8b_floor_campaign.py:260-294] [提案: 最低契約を「8 round、各roundが正規化済み12 cell_idの完全置換、各セルplanned 8回、seq=0..95」と明記する。この意味ならround方式を採り、96スロット一括置換は拒否する。位置まで均衡させるなら seeded Latin/cyclic rotation を別 algorithm ID として裁定する。build_schedule は入力順に依存せず cell_id を sort・一意検査する]`

4. `[severity: must-fix] [攻撃シナリオ: round先頭で失敗したセルは最大11セッション待ってretryされ、末尾セルは直後にretryされる。retry成功率がplanned位置と一過性外乱に依存する。さらに複数失敗時の lexicographic retry順は、異常が多いセル群へ固定の時間順位を与える。round末尾までに他11セルの結果も journal に露出する] [根拠 orchestrator/campaign/s8b_floor_campaign.py:855-873, docs/phase3-8b-descriptor-design.md:330-344] [提案: retry timing を新たな凍結意味論として明文化する。選択経路が最も狭いのは、現在attemptの無効理由だけで機械発火する即時retryである。round-tailを維持するならretry優先順もmanifestへ事前凍結し、他セルの性能値を変えてもvalid/invalidが不変ならretry列が変わらないmetamorphic testを置く。campaign-tailは全96結果を見た後かつ全retryが末期時間帯へ偏るため採らない]`

5. `[severity: must-fix] [攻撃シナリオ: retryのsession-start後、session完了記録前にcrashすると、そのattemptは_started_seqsには残るが_retries_usedには数えられない。resumeを繰り返せば retry_slots_per_cell=2 を超えて何度でも新しいretryを発行でき、「静かになるまで測る」経路になる] [根拠 orchestrator/campaign/s8b_floor_campaign.py:809-844, orchestrator/campaign/s8b_floor_campaign.py:855-873] [提案: retry枠はsession完了時ではなくauthorization/session-startのfsync時点で消費する。attempt_id、cell_id、retry_ordinal、trigger_attempt_idを持つ事前定義attempt registryを導入し、(cell_id,retry_ordinal) を再発行しない。first-authorized-valid の採用もregistry replayから一意に導出し、全attemptは別列で保持する]`

6. `[severity: must-fix] [攻撃シナリオ: fresh時のscheduleはmanifestへ書くが、resume時はmanifest.scheduleを無視してコードで再計算する。shuffle実装やcell順が変わると、同じseqが別セルを指す一方、journalはseq集合だけでskipするため、セルの二重実行・未実行が生じる。またduplicate start、cell/round不一致、偽のround-completeを現状のresume検査は拒否しない] [根拠 orchestrator/campaign/s8b_floor_campaign.py:809-815, orchestrator/campaign/s8b_floor_campaign.py:1168-1171, orchestrator/campaign/s8b_floor_campaign.py:1207-1221, orchestrator/campaign/s8b_floor_campaign.py:1317-1323] [提案: resumeではmanifest.scheduleを権威として使うか、再導出列とbyte単位で一致しなければ拒否する。campaign-startにjournal schema・protocol/freeze/manifest hashを記録し、start→terminal attempt、round start→complete、attempt ID一意性、scheduleとのcell/round一致を状態機械で全件検証する。set化してduplicateを隠さない]`

7. `[severity: must-fix] [攻撃シナリオ: launch例外経路ではpost-probeを実行せずjournalへ進むため、起動途中に残ったbenchや同時発生した競合を見逃して次attemptへ進む。またmeasure_pointが「5/5 reps failed」をScalePointで返すとexec_failures=5でもlaunch_failureではなくpartialへ落ちる。プランのprecedenceにはcompeting_process自体がない] [根拠 orchestrator/campaign/s8b_floor_campaign.py:532-554, orchestrator/campaign/s8b_floor_campaign.py:763-805, docs/phase3-8b-descriptor-design.md:350-355] [提案: measureを試みた全経路でpost-probeをfinally相当で実行する。順序を pre-probe競合→competing、post-probe検査不能→campaign abort、post-probe競合→competing、全rep起動不能→launch_failure、部分・非有限→nonfinite_or_partial_output、完全値のCV超過→performance_anomaly、その他valid と固定する。B-2のPID除外意味論には触れない]`

8. `[severity: must-fix] [攻撃シナリオ: high-CVのthroughputsからperformance_anomalyを付け忘れても、verifierはexcluded_reasonを生値から再導出せず、その自己申告値をそのままSessionRecordへ入れる。逆にreasonを書き換えてfloorを変えても、cells/floorsを同じ自己申告reasonから再計算すれば検証を通せる。cv値をjournalへ足すだけでは恒真ゲートである] [根拠 orchestrator/campaign/s8b_floor_campaign.py:705-750, orchestrator/campaign/s8b_floor_stats.py:59-81, orchestrator/campaign/s8b_floor_stats.py:275-288, orchestrator/campaign/s8b_floor_stats.py:296-410] [提案: raw throughputsとsession_cv_maxからCV・reasonを再導出する純関数をstats側に置き、生成側とverifierの双方で使う。session_cvを必須証拠として再計算値と一致検査する。exact有限正値なら平均0は起こらないため、そこでCV計算不能・非有限になればperformance扱いにせず内部不変条件破れとしてcampaign abortし、生値をjournalへ残す]`

9. `[severity: must-fix] [攻撃シナリオ: cell_cv_maxをconfigとMarkdownへ追加しても、現在のcell_stats/holdout_floors呼出しは閾値を受け取らず、CV>15%のセルにも通常のfloorを生成する。Markdownのmachine_anomaly一覧だけが赤くてもJSONのpairは非nullになり得る] [根拠 docs/phase3-8b-descriptor-design.md:339-341, orchestrator/campaign/s8b_floor_campaign.py:973-999, orchestrator/campaign/s8b_floor_campaign.py:1031-1037, orchestrator/campaign/s8b_floor_stats.py:268-327] [提案: C-α側のformula v2 APIへcell_cv_maxを必須入力として渡し、cell JSONに再計算可能なmachine_anomaly状態を持たせ、pair null伝播までstats/verifierが検証する。stockセル異常時の全pair・scale_ref伝播もAPI契約で一意化する。Markdown一覧はそのJSONからのみ描画する]`

10. `[severity: must-fix] [攻撃シナリオ: 「全attemptの実時間を課金」と謳っても、session-startはISO時刻だけ、session終端にmonotonic/durationはなく、wall_ledgerはcampaign/block markerだけである。block削除後に同様のmarkerも消せばretry・失敗・crashの消費時間を機械集計できず、予算保証が発火しない] [根拠 docs/phase3-8b-descriptor-design.md:338-359, orchestrator/campaign/s8b_floor_campaign.py:519-525, orchestrator/campaign/s8b_floor_campaign.py:755-759, orchestrator/campaign/s8b_floor_campaign.py:1008-1011] [提案: 各attemptのstart/endに同一process内monotonic値とdurationを記録し、campaign wall capの実consumerを置く。start-only crashも枠消費済みattemptとして台帳へ残す。round markerは説明用で、attempt課金の代替にしない]`

11. `[severity: must-fix] [攻撃シナリオ: result.json作成後、result.mdまたはterminal journal前にcrashすると、resumeはcompleted扱いせず再組立てし、create-onlyの既存result.jsonで永久に失敗する。さらにresult.mdはwrite_textで上書き可能なので「result create-only」と不整合である] [根拠 orchestrator/campaign/s8b_floor_campaign.py:1231-1248, orchestrator/campaign/s8b_floor_campaign.py:1317-1323, docs/phase3-8b-descriptor-design.md:350-354] [提案: result.json・result.md・terminal hashを持つ冪等なfinalization状態機械を設ける。resume時は既存artifactを再計算・hash検証し、欠けたcreate-only成果物だけを補完してterminalを追記する。既存内容は決して上書きしない]`

12. `[severity: must-fix] [攻撃シナリオ: _protocol()を一括更新し、改訂実装を走らせて出たscheduleをexpectedへ貼れば、round off-by-one、区切り、endian、slice、同一seed再利用のバグまでgolden化される。現行コメントも「実際に実行して得た」値を基礎にしており、独立oracleが見えない。planned中crashしか試さないためretry-start crashやfinalization crashも生存する] [根拠 orchestrator/tests/test_s8b_floor_campaign.py:122-147, orchestrator/tests/test_s8b_floor_campaign.py:296-341, orchestrator/tests/test_s8b_floor_campaign.py:646-760, docs/failures.md:88-100] [提案: production変更前に小セル集合の各roundについて、完全SHA-256、先頭8 byte big-endian整数、最終置換を独立手段で固定し、そのliteralは実装出力から再生成しない。per-round完全置換・8回出現・canonical input順のproperty testに加え、rの0/1-origin、区切り、endian、global shuffle、seed再利用の各意図的mutantを殺すpositive controlを置く。CVは `[90,90,100,110,110]` が境界10%、`[89,89,100,111,111]` が超過、4/5本の高分散はpartial優先として固定し、retry-start／retry-record後／round-complete後／result.json後の各crash-resumeも追加する]`

総合判定: 修正後に進めよ

---

### C-γ 依頼 prompt (逐語)

```markdown
# 敵対的検証依頼 C-γ — ExecutionEnvironmentContract 設計 (F4 裁定の実装)

あなたは敵対的レビュアーである。以下の実装プランを攻撃し、欠陥を挙げよ。プランを褒める必要はない。
所見は番号付きで `[severity: must-fix|should|nit] [攻撃シナリオ] [根拠 file:line] [提案]` の形式。
最後に「総合判定: このまま進めよ / 修正後に進めよ / やめよ」を 1 行で。sandbox は read-only、
repo を自由に読んでよい。

## 所与 (再交渉不可のユーザー裁定、2026-07-18)

- **F4 (修正付き採用、正本 = docs/phase3-8b-descriptor-design.md §9):** 「env_tag 一致検査のみ・
  env contract は Pegasus 差分に据え置き」を破棄し、`ExecutionEnvironmentContract` の抽象化を実装
  対象へ昇格 (ユーザーはしばらくスパコン Pegasus を多用)。driver の cygnus 固有値 (48 threads /
  1M records / CLK1800 / numactl --interleave=all) ハードコードを contract で解消。**所見 G12 の
  Pegasus 制約は実装要件へ昇格**: campaign を単一 allocation/node/process で完遂 / walltime 不足時
  全廃棄 / hostname・boot id・job id・cpuset・UTC 記録 / PID 可視性の事前 probe / WAL は永続領域
  (/scr 不可) / module・toolchain・job script hash / monotonic は同一 process 内 duration 限定
- protocol JSON の env_tag が v2 数値を束縛する唯一の env-tag。env_tag の値は floor 実測開始時に
  ユーザーが確定 (未指定)
- 関連正本: docs/decisions.md D59 (別 env 正式採用の 4 条件)、docs/pegasus-runbook.md §6/§7
- F6/F7・B-1/B-2 は未裁定 — 依存する実装はしない

## 実査で確定している事実 (自分でも確認せよ)

- 正本定数 = `orchestrator/campaign/p2_2.py:36-47` (ENV_TAG/CLK/NUMA/RECORDS/THREADS/EXTIME/REPS)。
  `_assert_matches_calibration` (:93-112) が calibration JSON と records/threads のみ照合
  (CLK・NUMA は無検査)
- p2_2 直 import 消費者 = campaign 層 19 本 + テスト 6 本。**p2_2 を経由しない同値ハードコードが
  別に 14 本前後** (ENV_TAG/NUMACTL/CLK)。CLK は 1800 系と 2100 系が混在
- floor: `s8b_floor_campaign.py:76-77` が CLK/ENV_TAG/NUMA を直 import、env_tag 検査 (:1150-1154)
  は `p2_2.ENV_TAG` との等価比較 = **Pegasus では本走が構造的に通らない**。measure_fn 既定実装
  (:1174-1182) が CLK と NUMACTL を埋め込む。records/threads は freeze holdout 由来 (env 非依存で良)
- oracle: `s8b_oracle_driver.py:41` が NUMACTL を独自再定義 (p2_2 と二重実装)。CLK は run_contract
  経由で既にパラメタ化済み。env_tag は非空検査のみ (`s8b_oracle_manifest.py:301`)
- calibrator (`orchestrator/calibrator/cli.py` / `runner.py:268 measure_point`) は既に完全引数駆動で
  env 中立
- `orchestrator/tests/test_s8b_freeze_io.py:197-218` が `floor.NUMACTL is p2_2.NUMA` の identity と
  measure_fn closure ソース文字列を固定 (契約導入で書き換え要)

## 私のプラン (これを攻撃せよ)

1. **新規 leaf module `orchestrator/campaign/env_contract.py`** (stdlib のみ、campaign 内 import
   なし): frozen dataclass `ExecutionEnvironmentContract` — fields:
   `env_tag: str` / `clocks_per_us: int` / `numactl: tuple[str, ...]` /
   `wal_root_policy: str` ("persistent" 固定の宣言) / `capture: tuple[str, ...]`
   (G12 記録フィールドの宣言: hostname, boot_id, job_id, cpuset, utc) /
   `calibration_note: str` (calibration binding の来歴 1 行)。
   `REGISTRY: dict[str, ExecutionEnvironmentContract]` は同 module 内で静的に定義し、当面
   `linux-baremetal` (cygnus 値) の 1 エントリのみ。`lookup(env_tag)` は未登録 env_tag に対し
   例外 (fail-closed)。**Pegasus エントリは D59 の 4 条件 (専用 calibration 取り直し等) が満たされる
   まで登録しない** — 登録手順を pegasus-runbook §7 に追記 (docs レーン)
2. **p2_2 の逆転**: `p2_2.py` の `ENV_TAG/CLK/NUMA` を env_contract の linux-baremetal インスタンス
   からの再 export に置換 (`CLK = _C.clocks_per_us` 等、値は不変)。RECORDS/THREADS/EXTIME/REPS は
   workload 側パラメタなので contract に入れず p2_2 に残す。`_assert_matches_calibration` は不変
3. **floor 結線**: `s8b_floor_campaign.run_campaign` の env_tag 等価比較 (:1150-1154) を
   `env_contract.lookup(protocol["env_tag"])` に置換 (未登録 = fail-closed 拒否)。measure_fn 既定
   実装は contract.clocks_per_us / contract.numactl を使う。**G12 capture の実装**: journal /
   manifest に hostname・boot_id (既存)・job_id (PBS_JOBID/SLURM_JOB_ID env var、無ければ null)・
   cpuset (/proc/self/status の Cpus_allowed_list)・UTC を記録
4. **oracle 結線 (最小)**: `s8b_oracle_driver.py:41` の独自 NUMACTL を
   `env_contract.lookup(run_contract["env_tag"]).numactl` に置換。これにより oracle も未登録
   env_tag を拒否するようになる (挙動強化)
5. **スコープ外 (今回触らない)**: legacy sweep 群の直 import 19 本と重複ハードコード 14 本、
   `loop.run_campaign` / `pipeline.evaluate` のシグネチャ変更 (20+ 呼び出し元)、CLK 1800/2100 の
   使い分け整理。これらは v2 計測経路 (floor/oracle) の外であり、F4 の目的 (Pegasus で floor/oracle
   を回せる) に不要と判断

## 特に攻撃してほしい観点

- **contract のフィールド選定**: G5' 所見の想定 (isolation policy / toolchain fingerprint /
  calibration binding) から落としたものは正当か。逆に wal_root_policy / capture のような「宣言だけの
  フィールド」は恒真 (F14 型: 何も強制しない) にならないか — 強制点をどこに置くべきか
- **G12 実装の最小十分性**: 「campaign 単一 allocation 完遂」「walltime 不足時全廃棄」「monotonic
  同一 process 限定」をコードでどう強制するか、私のプランには欠けている。何が今必要で何が Pegasus
  エントリ登録時でよいか
- **fail-closed lookup の抜け道**: テストが registry に注入する経路、env_tag typo で cygnus 値が
  暗黙適用される経路、oracle の挙動強化 (非空 → 登録済み要求) が既存テスト/manifest fixture を
  壊す範囲
- **p2_2 逆転の整合**: import cycle (env_contract は leaf を保てるか)、`_assert_matches_calibration`
  が CLK/NUMA を無検査のまま残る問題を contract 導入時に是正すべきか
- **スコープ判断**: legacy 14 重複ハードコードを残す判断が「env-neutral を名乗りながら旧経路が
  cygnus 値で走る」誤用面を残さないか。v2 経路との境界をどう機械的に明示するか
- **過剰設計批判**: 逆に、このプランのうち今やる必要がない部分はどれか (F4 裁定の趣旨 = Pegasus で
  floor を回せること、に照らして)
```

### C-γ 所見 (逐語)

1. [severity: must-fix] [攻撃シナリオ] Pegasus 上で protocol の `env_tag` に `linux-baremetal` を指定すると、`lookup()` は正常に cygnus 契約を返す。hostname 等を記録しても照合しなければ、Pegasus の値を cygnus 測定として採用できる。登録済みタグ検査は実環境の attestation ではない。 [根拠 docs/decisions.md:2276-2293; output/env/linux-baremetal/calibration/calibration_t48_skew0p9_rr50_rmw0.json:10-15] [提案] contract に hash 済み qualification artifact と `assert_current_environment()` を持たせ、host/topology/cpuset/scheduler/toolchain を実測照合する。lookup・attestation・出力 root 検査を、build・manifest・WAL のどの書込みよりも前に通す。

2. [severity: must-fix] [攻撃シナリオ] `calibration_note` は自由文なので、Pegasus 専用 calibration/noise floor が存在しなくても「取得済み」と書ける。isolation policy と toolchain fingerprint も欠落しており、D59 の四条件を contract が表現できない。 [根拠 docs/decisions.md:2282-2285; output/insights/2026-07-16_s8b-floor-protocol-consultations.md:326-334] [提案] `calibration_ref`、`noise_floor_ref` を `{path, sha256, schema}` の構造化参照にし、`isolation_policy`、`toolchain_contract`、`contract_sha256` を追加する。records/threads は freeze 所有のままでよいが、参照 calibration と利用可能 cpuset に適合することを検証する。

3. [severity: must-fix] [攻撃シナリオ] `wal_root_policy="persistent"` と `capture=("hostname",...)` は値を書くだけの恒真保証になる。フィールドを欠落・null・改竄しても、現行 floor verifier は `config/sessions/cells/floors` しか再検証しないため結果が通る。 [根拠 docs/failures.md:10-14; docs/phase3-8b-descriptor-design.md:388-389; orchestrator/campaign/s8b_floor_stats.py:296-410] [提案] 一択しかない宣言フィールドは削り、固定 schema の `ExecutionReceipt` と実検証コードへ置き換える。開始・終了 snapshot、contract hash、必須値の非 null、安定性を検証し、各フィールド削除・改竄 mutation が失敗するテストを置く。

4. [severity: must-fix] [攻撃シナリオ] G12 capture が floor にしか結線されない。oracle の `campaign-start` は manifest/block/campaign ID しか持たず、oracle report も hostname・boot ID・job ID・cpuset を要求しないため、別 node/allocation で走っても検出できない。 [根拠 orchestrator/campaign/s8b_oracle_driver.py:257-261; orchestrator/campaign/s8b_oracle_driver.py:462-470; orchestrator/campaign/s8b_oracle_report.py:35-45] [提案] floor/oracle 共通の execution guard と receipt verifier を実装し、両 driver が同じ開始・終了検査を必ず通るようにする。静的 plan manifest と、job ID 等を持つ動的 execution receipt は分離する。

5. [severity: must-fix] [攻撃シナリオ] floor は新 process からの `--resume` を正式に許しており、実クラッシュ後に残りを完走するテストまである。hostname・boot ID・job ID が同じでも process は別なので、「単一 allocation/node/process 完遂」を満たさない。 [根拠 docs/phase3-8b-descriptor-design.md:373-377; orchestrator/campaign/s8b_floor_campaign.py:1201-1222; orchestrator/tests/test_s8b_floor_campaign.py:646-707] [提案] isolation policy に `single_process` と `allow_resume` を持たせ、Pegasus contract では `allow_resume=False` にする。PIDだけでなく `/proc/self/stat` の start time と execution UUID を記録し、途中 WAL は証拠として保存するが全数値を refreeze 不適格にする。

6. [severity: must-fix] [攻撃シナリオ] scheduler の残 walltime を一度も調べないため、終盤で強制終了され、別 allocation で部分値を再利用できる。oracle の `reserved_bench_s` は bench 名目時間だけで、build・verify・待機を含む allocation walltime ではない。 [根拠 docs/phase3-8b-descriptor-design.md:375; docs/pegasus-runbook.md:83-113; orchestrator/campaign/s8b_oracle_driver.py:478-499] [提案] NQSV adapter/launch receipt から allocation deadline を取得し、承認済み `B_campaign_wall` と安全余白を開始前に予約する。不足時は一行も測らず、途中 kill は terminal 欠落により campaign 全体を不適格化する。「全廃棄」はWAL削除ではなく全数値不採用とする。

7. [severity: must-fix] [攻撃シナリオ] `pgrep` の rc=1 は「競合なし」と「他 job の PID が namespace から不可視」を区別できない。また oracle は `settled=False` を記録するだけで測定値を採用する。これは PID 可視性 probe と静定確認ではない。 [根拠 orchestrator/campaign/s8b_floor_campaign.py:472-505; orchestrator/campaign/pipeline.py:241-300; docs/decisions.md:2290-2293] [提案] 通常の競合検査とは別に、job wrapper が作る sibling sentinel を検出する能力 probeを実装し、不可視なら開始拒否する。isolation policy に静定閾値・timeout・失敗時拒否を持たせる。汎用機構とテストは今回実装し、実際のNQSV変数・可視性 canary はPegasus登録時に確定する。

8. [severity: must-fix] [攻撃シナリオ] repo を `/scr` に置けば、floor はその直下の `output/` に WAL を書く。oracle はさらに任意の `--output-root` を受ける。`wal_root_policy` が何を宣言しても、この経路は止まらない。 [根拠 orchestrator/campaign/layout.py:27-33; orchestrator/campaign/s8b_floor_campaign.py:1374-1383; orchestrator/campaign/s8b_oracle_driver.py:729-740; docs/pegasus-runbook.md:221-231] [提案] Pegasus policy に永続領域の allowlist を持たせ、symlink 解決後の run_dir、WAL、manifest、result、budget、marker、cache 全てを mkdir 前に検査する。単純な文字列 `/scr` 拒否ではなく resolved path/mount を検査する。

9. [severity: must-fix] [攻撃シナリオ] oracle は `run_contract.clocks` を任意の正整数として受理し、そのまま実行する。NUMACTL だけ contract から取れば、`env_tag=linux-baremetal, clocks=2100` が合法なままで、env_tag が数値を束縛しない。さらに run_contract の env_tag は floor protocol/freeze 由来と照合されない。 [根拠 docs/phase3-8b-descriptor-design.md:363-366; orchestrator/campaign/s8b_oracle_manifest.py:293-306; orchestrator/campaign/s8b_oracle_driver.py:445-457; orchestrator/campaign/s8b_oracle_driver.py:570-574] [提案] oracle の env_tag は v2 freeze が束縛する floor protocol の値から導出し、コピーを残すなら完全一致を要求する。`clocks` は contract から導出するか一致検査する。contract lookup・digest照合・attestationは `_ensure_campaign` より前に行い、失敗は no-write の `refused` とする。

10. [severity: must-fix] [攻撃シナリオ] 「legacy hardcode は v2 経路外」というスコープ判定が既に偽である。oracle は `pipeline.s2_correctness_workload()` を呼び、その中には linux-baremetal calibration 由来の 1M records/48 threads が固定されている。さらに空の `numactl` policy は明示的に拒否されるため、単一 NUMA の Pegasus contract を表現できない。 [根拠 orchestrator/campaign/pipeline.py:60-83; orchestrator/campaign/pipeline.py:378-385; orchestrator/campaign/s8b_oracle_driver.py:570-578; docs/pegasus-runbook.md:45-50] [提案] S2 verification profile も contract/qualification artifact に束縛する。「policy 未解決」と「解決済みで launch prefix は空」を区別する。既定互換の optional 引数追加で足りるため、pipeline 結線をスコープ外にしてはならない。

11. [severity: must-fix] [攻撃シナリオ] floor/oracle の cache root は env 非分離で、cache key は compiler 名しか含まず version・module・architecture・contract hash を含まない。同じ共有 `/work` で cygnus/Pegasus を走らせると別 toolchain の binary を再利用できる。 [根拠 orchestrator/campaign/buildcache.py:102-118; orchestrator/campaign/s8b_floor_campaign.py:578-603; orchestrator/campaign/s8b_oracle_driver.py:560-565] [提案] v2 cache root/keyを `contract_sha256` で namespace 分離し、実測した compiler path/versionまたは executable hash と module fingerprint を照合する。floor と oracle は同じ contract namespace を使う。

12. [severity: must-fix] [攻撃シナリオ] floor は absolute `time.monotonic()` を journal/result に永続化し、resume では別 process の値が同じ `wall_ledger` に混ざる。G12 の「同一 process 内 duration 限定」に正面から反する。 [根拠 orchestrator/campaign/s8b_floor_campaign.py:519-525; orchestrator/campaign/s8b_floor_campaign.py:1008-1042; orchestrator/campaign/s8b_floor_campaign.py:1201-1222] [提案] absolute monotonic 値を artifact から除き、同一 execution UUID 内の `elapsed_s` または開始・終了差だけを記録する。process を跨ぐ値は UTC 順序情報としてのみ扱う。

13. [severity: should] [攻撃シナリオ] 公開された mutable `REGISTRY: dict` にテストが `fixture-env` を注入すると、その状態漏れで本来未知の env が正式実行可能になる。悪性キー `../../x` を入れれば、現在の `env_scope_dir` はそのまま path に連結する。 [根拠 orchestrator/campaign/s8b_floor_campaign.py:202-205; orchestrator/campaign/layout.py:87-90; orchestrator/tests/test_s8b_oracle_driver.py:127-164] [提案] registry は privateな `MappingProxyType` とし、register APIを作らない。dataclassの `__post_init__` でslug、正整数、keyと`contract.env_tag`の一致、重複を検査する。driver 正常系テストは登録済み tag を使い、fake contract は純粋な validator 単体テストへ渡す。

14. [severity: should] [攻撃シナリオ] oracle driver の中央 fixture は全て `fixture-env`、manifest テストは `test-env` を使う。安易に registry へ両者を登録すると production lookup の fail-closed 性をテスト都合で破る。一方、登録しなければ driver 正常系の大半が一斉に壊れる。 [根拠 orchestrator/tests/test_s8b_oracle_driver.py:127-164; orchestrator/tests/test_s8b_oracle_manifest.py:81-105; orchestrator/tests/test_s8b_freeze_io.py:197-218] [提案] 実行 driver の中央 fixture だけを `linux-baremetal` と real contract digest に更新し、manifest の構造単体テストは非実行 tag を許してよい。未知 tag が marker/WAL/budget を一切作らない回帰を追加し、closure ソース文字列検査は `measure_point` への実引数を spy する挙動テストへ置換する。

15. [severity: should] [攻撃シナリオ] p2_2 の逆転は F4 の v2 実行には不要なのに、歴史的 pin を持つ driver と多数の legacy consumer を registry へ結合する。さらに `_assert_matches_calibration` は records/threads しか見ないため、contract の CLK/NUMA が calibration からずれても通る。 [根拠 orchestrator/campaign/p2_2.py:2-10; orchestrator/campaign/p2_2.py:36-47; orchestrator/campaign/p2_2.py:93-112; output/env/linux-baremetal/calibration/calibration_t48_skew0p9_rr50_rmw0.json:2-18] [提案] 最小案は p2_2 の歴史的定数を触らず、v2 driver だけを contract consumer にして値一致テストを置く。逆転を残すなら list→tuple の互換性を明示し、calibration の env_tag/clocks と構造化参照hashまで検査する。

16. [severity: should] [攻撃シナリオ] legacy の重複 hardcode を残したまま「env-neutral」と呼べる境界がコード上存在しない。新しい v2 consumer が誤って旧 driver/pipeline 定数を importしても検知されず、今回の S2 hardcodeと同じ取り残しが再発する。 [根拠 orchestrator/campaign/p3_s4_loop.py:65-67; orchestrator/campaign/s5_permutation_coverage.py:43-44; orchestrator/campaign/s8a_trigger_coverage.py:59-60] [提案] legacy 全移行は行わず、v2実行 closureで `p2_2` の環境定数、`linux-baremetal`、CLK literal、`--interleave=all` を禁止するAST/lintを追加する。旧entrypointは明示的に legacy/cygnus-only と分類する。

17. [severity: should] [攻撃シナリオ] Pegasus entry を登録しない状態では、新 contract 実装後も Pegasus floor/oracle は意図どおり拒否される。それを「F4完了＝Pegasus実行可能」と扱うと、未取得のenv_tag・校正・NQSV変数を後から手作業で埋める抜け道になる。 [根拠 docs/phase3-8b-descriptor-design.md:378-379; docs/decisions.md:2295-2296] [提案] 完了条件を「共通 enforcement・artifact consumer・mutation tests 完了」と「Pegasus qualification artifact作成＋ユーザー確定tag＋registry登録」の二段に分ける。前者は今回、実値・job変数・許可root・calibration/toolchain/job-script hash は登録時に確定する。

総合判定: 修正後に進めよ

---

### C-δ 依頼 prompt (逐語)

```markdown
# 敵対的検証依頼 C-δ — wave スコープ・凍結整合・テスト戦略 (メタレビュー)

あなたは敵対的レビュアーである。以下の wave 全体計画を攻撃し、欠陥を挙げよ。プランを褒める必要は
ない。所見は番号付きで `[severity: must-fix|should|nit] [攻撃シナリオ] [根拠 file:line] [提案]` の
形式。最後に「総合判定: このまま進めよ / 修正後に進めよ / やめよ」を 1 行で。sandbox は read-only、
repo を自由に読んでよい。

## 状況

floor protocol パッケージ (output/insights/2026-07-16_s8b-floor-protocol-package.md、凍結済み) の
F1〜F5 についてユーザー裁定が確定 (正本 = docs/phase3-8b-descriptor-design.md §9 の承認状態 4 ブロック、
worklog 2026-07-18 (2)〜(4))。F1 = 修正付き (block/gap/delta_c 廃止 + performance_anomaly
session CV>10% / machine_anomaly セル間 CV>15%)、F2/F3/F5 = 推奨どおり、F4 = 修正付き
(env contract 抽象を採用)。**F6 (承認束縛)・F7 (v2 検証意味論)・B-1 (manifest NaN strict 化)・
B-2 (probe 自己子孫除外の縮小) は未裁定。** master_seed / env_tag も未指定。

ユーザーは「次にやるべきことを計画し実行せよ」と指示した。私は「裁定済み分の実装 wave」を計画した。

## 私の wave 計画 (これを攻撃せよ)

**実装レーン 4 本:**
- Lane S: `s8b_floor_stats.py` formula v2 (delta_c/2-block 廃止、異常ゲート 2 段、
  verify_floor_artifact の双方向照合、FORMULA_ID 改版) + テスト改訂
- Lane C: `s8b_floor_campaign.py` 追随 (protocol キー 3 削除 + 閾値 2 追加、round 単一パス
  schedule、retry を round 末尾消化に読み替え、performance_anomaly を閉じた表 4 行目 + 検出実装、
  official mode 拒否は不変) + テスト改訂 (24 本、golden pin 再計算)
- Lane E: `env_contract.py` 新設 (leaf + registry fail-closed lookup、linux-baremetal のみ登録) +
  p2_2 逆転 + floor/oracle の v2 経路結線 + G12 capture (hostname/boot_id/job_id/cpuset/UTC)。
  legacy sweep 群・重複ハードコード 14 本・loop/pipeline シグネチャは触らない
- Lane M: `s8b_oracle_manifest.py::_validate_execution_snapshot` (:402-434) の per-pair floor 形状
  追随 (F5 承認形状) + テスト fixture 4 ヘルパ改訂 (影響 ~40 テスト)

**wave から除外 (理由付き):**
- oracle 消費配線 (expected_perf_sha256 の driver 結線): `s8b_oracle_driver.py:145-151` の
  `freeze-v2-verifier-not-implemented` refusal が F6/F7 依存の構造ブロックで、配線しても到達不能。
  strict v2 verifier wave (F6/F7 裁定後) に統合
- protocol JSON の凍結・budget 三層の数値凍結・実行計画: F6/F7 + master_seed/env_tag 待ち
- `s8b_holdout_freeze.py`: F7 裁定まで編集禁止 (裁定資料の実測 drift hash 保全) — 全レーン不接触を
  検証済み
- B-1 (canonicalizer NaN)・B-2 (probe admission): 未裁定のため現状維持。B-2 は共有 probe だけで
  なく floor の strict_probe (:472-505) にも同型の子孫除外があると判明 — 裁定適用時の対象として
  worklog に記録するだけに留める

**手順:** codex 敵対相談 4 本 (本依頼含む) → 所見の real/refuted 親裁定 → 逐語を output/insights へ
凍結 → Workflow (実装 = opus、機械修正/テスト = sonnet、レーン内敵対レビュー = opus 2 レンズ →
修正 → 再レビュー) → 親の独立検算 (全テスト + 手計算 golden 照合 + diff 精読) → commit (レーン別) →
main ff。docs レーン: worklog 1 エントリ + phase3 進捗 + pegasus-runbook §7 に contract 登録手順 +
handoff 削除

## 特に攻撃してほしい観点

1. **前倒しの正当性**: §9 の F1 記録には「実装・テストの改訂は全裁定完了後」と書いた (F2〜F7 裁定
   継続中だった時点の記録)。F6/F7/B-1/B-2 が未裁定のまま実装 wave を回す本計画は、その記録と表面上
   矛盾する。F6/F7 の裁定結果が Lane S/C/E/M の実装を手戻りさせる具体的経路はあるか (あるなら
   どのレーンをブロックすべきか)。worklog にどう記録すれば正直か
2. **F1〜F5 裁定の取りこぼし**: 裁定済みで実装可能なのに wave に入っていない項目はないか。例:
   F1 の scale-adequacy ±10% は現行 `_PROTOCOL_KEYS` に対応キーがない (どこに凍結するのか)。
   F3 の三層 budget は今コードが要るか。F2 の「retry は失敗 block の末尾」を round 末尾に読み替える
   判断は裁定の範囲内か
3. **Lane M の二度手間リスク**: manifest fixture ~40 テストを今 per-pair 形に書き換えた後、F7 裁定
   (load_ratified_freeze 統一) で再度書き換えになる経路はないか。今やる価値 vs v2 verifier wave に
   同梱する価値
4. **凍結整合**: 裁定資料 (凍結族) と s8b_holdout_freeze.py に 1 byte も触れないことが全レーンで
   本当に保証されるか。テスト fixture が holdout_freeze.json (実物) を読む経路の有無
5. **テスト戦略の堕落面**: golden 再計算を「実装を走らせて出力を貼る」でやるとバグごと固定される。
   親検算・レビューで機械的に防ぐ具体策。既存 mutation-killing テストの保存確認方法
6. **commit/レビュー構造**: レーン別 commit + レーン内敵対レビュー 2 レンズで、レーン間結合
   (S↔C の formula/config キー、E↔C の env_tag 検査置換) の整合は誰が検証するのか。結合バグの
   具体的シナリオ
7. **モデル配分**: 実装 = opus (high)、テスト/機械修正 = sonnet、レビュー = opus。この難易度配分の
   誤りがあるレーンはどれか
```

### C-δ 所見 (逐語)

1. [severity: must-fix] [攻撃シナリオ] 「全裁定完了後」という正本の順序を、現在のユーザー指示が黙示的に撤回したと解釈して main へ入れると、後から F7 先取り実装として否認される。F6 は主に official activation、F7 は Lane M と Lane E の consumer 結線へ具体的な手戻りを生む。 [根拠 `docs/phase3-8b-descriptor-design.md:325-328`; `docs/worklog.md:349-353,371-374,385-388`; `docs/handoff/2026-07-18-ruled-wave-f1-f5.md:18-25`] [提案] 実装前に順序変更を明示承認させる。worklog には「従来の全裁定待ちからの例外」「非発効の先行実装で完了扱いしない」「protocol/freeze/approval は生成しない」「F6/F7/B-1/B-2/seed/tag は未裁定」と記す。許せるのは S の純粋計算、C の ratification 非依存部分、E の contract core まで。M と E consumer 結線は止める。

2. [severity: must-fix] [攻撃シナリオ] formula だけ v2 にして、互換性のない protocol・schedule・result・floor manifest を `/v1` のまま出すと、旧 reader が新 artifact を同じ版として誤解する。resume hash や golden の意味も版名と一致しない。 [根拠 `orchestrator/campaign/s8b_floor_campaign.py:84-96,397-422`; `docs/phase3-8b-descriptor-design.md:330-340`] [提案] `FORMULA_ID` だけでなく `PROTOCOL_SCHEMA`、`SCHEDULE_ALGORITHM`、`RESULT_SCHEMA`、`MANIFEST_SCHEMA` を一括改版し、v1/v2 の交差受理を拒否するテストを置く。

3. [severity: must-fix] [攻撃シナリオ] official 拒否は CLI にしかない。Python から `run_campaign(..., mode="official")` を直接呼べば、未承認でも `eligible_for_refreeze=true` の artifact を生成できる。計画の「official mode 拒否は不変」は現状でも恒偽である。 [根拠 `orchestrator/campaign/s8b_floor_campaign.py:1013-1018,1123-1148,1365-1372`; `orchestrator/tests/test_s8b_floor_campaign.py:443-450`] [提案] F6 までは core の `run_campaign` 自体で official を無条件拒否し、build・measure・ファイル生成が 0 回である直接 API テストを追加する。将来は文字列 mode でなく ratified 型を要求する。

4. [severity: must-fix] [攻撃シナリオ] F2 の裁定文言は「失敗した block の末尾」だが、F1 で block は消えた。「round 末尾」を各 12 セル置換の末尾と解すると、従来の四置換後より早く retry が入り、時間位置と first-authorized-valid が変わる。「全 planned session 後」と解した場合とも結果が異なる。 [根拠 `output/insights/2026-07-16_s8b-floor-protocol-package.md:158-162`; `docs/phase3-8b-descriptor-design.md:330-332,348-356`] [提案] round の定義と retry 位置を正本へ明記する。確認なしに読み替えない。選択した順序、retry の決定的並び、campaign 通算 slot、resume 後の扱いを golden 化する。

5. [severity: must-fix] [攻撃シナリオ] F2 は `settled=False` を session 無効とする一方、承認済み閉表は三理由＋`performance_anomaly` の四行で、settle failure の code がない。現 driver は settled を取得せず、launch 例外時には post-probe も実行しない。 [根拠 `output/insights/2026-07-16_s8b-floor-protocol-package.md:146-179`; `orchestrator/campaign/s8b_floor_campaign.py:546-554,763-805`] [提案] `settle_timeout` を第五理由にするのか campaign abort にするのかを追加裁定する。C はそれまでブロックする。post-probe は例外経路でも実行し、B-2 未裁定中は official activation の前提未達と記録する。

6. [severity: must-fix] [攻撃シナリオ] S で CV 超過を `session_median=None` として実装すると、C はそれを `nonfinite_or_partial_output` と誤分類する。C 側でも CV を再計算すれば、生成側と verifier で式が二重化する。また現 validator は任意の理由文字列を閉表として受理する。 [根拠 `orchestrator/campaign/s8b_floor_stats.py:59-81`; `orchestrator/campaign/s8b_floor_campaign.py:288-296,697-725`] [提案] S に `SessionAssessment(median, cv, reason)` の単一純関数を置き、C と verifier が共有する。理由集合は四行との完全一致を要求する。閾値直下・ちょうど・直上、bool/string 数値拒否、全反復値保存を独立テストする。

7. [severity: must-fix] [攻撃シナリオ] F1 で維持された scale-adequacy ±10% が wave に存在しない。`scale_ref` は記録されるだけで oracle consumer がなく、全 TPS が 25% 上振れしても古い絶対 floor で肯定判定できる。 [根拠 `docs/phase3-8b-descriptor-design.md:342-345`; `output/insights/2026-07-16_s8b-floor-protocol-package.md:93-96`; `orchestrator/campaign/s8b_floor_stats.py:174-181`; `orchestrator/campaign/s8b_oracle_driver.py:284-302`] [提案] protocol v2 に default なしの `scale_adequacy_rel_tolerance` を置く。消費配線を F7 後へ送るなら、明示的な除外項目として記録し、F1 実装完了とは数えない。

8. [severity: must-fix] [攻撃シナリオ] F3 は承認済みなのに実装レーンがない。floor は build・retry・wall を無制限に消費でき、既存 budget ledger も wall を記録するだけで cap は bench にしかない。`bench_max_rounds` も任意の正整数を受理する。 [根拠 `docs/phase3-8b-descriptor-design.md:357-360`; `orchestrator/campaign/s8b_budget.py:25-35,74-93,377-399`; `orchestrator/campaign/s8b_oracle_manifest.py:293-306`; `orchestrator/campaign/s8b_floor_campaign.py:1186-1224`] [提案] 三層 namespace、子枠移転禁止、親 `B_campaign_wall`、pilot/floor の事前予約を別 Lane B として設計する。数値凍結を待つなら runtime 実装も明示延期し、F3 完了と書かない。v2 では `bench_max_rounds == 1` を版付きで強制する。

9. [severity: must-fix] [攻撃シナリオ] Lane M は `/v1` manifest の raw freeze readerだけを per-pair に変える。F7 後は `load_ratified_freeze` と approval/active fixture が必要になり、約40テストを再度書き換える。現在は v2 driver が構造的に到達不能なので実行価値もない。 [根拠 `orchestrator/campaign/s8b_oracle_manifest.py:20,402-434,471-477,586-617`; `orchestrator/campaign/s8b_oracle_driver.py:145-151`; `orchestrator/tests/test_s8b_oracle_manifest.py:108-123`; `output/insights/2026-07-16_s8b-floor-protocol-package.md:466-468`] [提案] M は F7 wave へ統合する。先に価値を残すなら、呼出し配線なしの versioned `validate_v2_floor_shape` と直接単体テストだけに限定し、既存 fixture 群は触らない。

10. [severity: must-fix] [攻撃シナリオ] F5 の `pairs` は構成 ID をキーにするが、現 S/C は `rr80::構成` という cell ID を出す。M が schedule の `configuration_id` 集合を要求すれば、各 lane 単体は緑でも結合時に全件拒否される。 [根拠 `output/insights/2026-07-16_s8b-floor-protocol-package.md:74-88,330-335`; `orchestrator/campaign/s8b_floor_stats.py:179,203-208`; `orchestrator/campaign/s8b_floor_campaign.py:989-999`; `orchestrator/tests/test_s8b_floor_campaign.py:851-861`] [提案] freeze-facing `pairs` は構成 ID、raw/diagnostics のみ cell ID と固定する。exact key set は全構成−stock とし、S→C→v2 shape の結合テストを先に書く。

11. [severity: must-fix] [攻撃シナリオ] G12 を hostname等の「capture」に縮めると、別 PBS job・別 node・別 process で resume しても記録が増えるだけで拒否されない。module/toolchain/job script hash、PID 可視性、永続 WAL、残 walltime 全廃棄も落ちている。F4 の単一 process と現行 cross-process resume も衝突する。 [根拠 `docs/phase3-8b-descriptor-design.md:368-377`; `orchestrator/campaign/s8b_floor_campaign.py:519-525,1201-1221`; `docs/pegasus-runbook.md:245-257`] [提案] contract に capture ではなく preflight・identity固定・各境界再照合を持たせる。Pegasus では PID、job/node/boot/cpuset、module/toolchain/job script hash、WAL path、残 walltimeを必須にし、process を跨ぐ resume は拒否する。linux-baremetal だけの登録は「F4 core 部分実装」であり Pegasus 対応完了と数えない。

12. [severity: must-fix] [攻撃シナリオ] 同じ `env_tag` の registry 内容を後から変更すると、floor と oracle が別 CLK/NUMA/toolchain を使っても tag 一致は通る。さらに F7 前の protocol/run_contract 文字列から adapter を選べば、未承認入力が実行環境を選択する。 [根拠 `docs/phase3-8b-descriptor-design.md:363-372`; `output/insights/2026-07-16_s8b-floor-protocol-package.md:466-473`; `orchestrator/campaign/s8b_floor_campaign.py:1150-1182`; `orchestrator/campaign/s8b_oracle_driver.py:456-457,566-586`] [提案] protocol に canonical env-contract fingerprint/version を凍結し、registry contract と完全一致させる。E は immutable contract core まで先行可、floor/oracle consumer 結線は ratified object から protocol を得る F7 後に行う。

13. [severity: must-fix] [攻撃シナリオ] contract が records/threads を上書きすれば frozen holdout 座標を無断変更し、無視すれば F4 の「1M/48 hardcode 解消」が名目だけになる。F5 は holdout fields の世代差分を許していない。 [根拠 `output/s8b-freeze/holdout_freeze.json:40-48,307-315`; `orchestrator/campaign/s8b_floor_campaign.py:323-342`; `orchestrator/campaign/s8b_oracle_driver.py:284-302`; `docs/phase3-8b-descriptor-design.md:381-389`] [提案] contract は freeze の records/threads を上書きせず、要求動作点との一致を fail-closed 検証する。Pegasus calibration が異なる値を要求するなら、別 freeze/追加裁定へ戻す。

14. [severity: must-fix] [攻撃シナリオ] 「全レーン不接触を確認」は手順であって防壁ではない。実 fixture は正本 `holdout_freeze.json` を読む。ただし現状の書込み先は tmp copy で、正本への直接 write は見当たらない。workflow では前 wave に実ファイル消失事故も起きている。 [根拠 `orchestrator/tests/test_s8b_oracle_manifest.py:108-123`; `orchestrator/tests/test_s8b_budget.py:70-73`; `docs/worklog.md:313-319`; `output/insights/2026-07-18_s8b-v2-prereqs-wave2-consultations.md:661`] [提案] 開始時と各 commit 前後に frozen insights、freeze JSON、`s8b_holdout_freeze.py` の HEAD hash・作業木 hashを照合し、既存 `output/insights/` は追加1ファイル以外 M/D/R=0を要求する。staging は明示 path のみ。なお stats の「package も同時更新せよ」という記述は、packageを触らず §9/protocol JSON を指すようコード側だけ直す (`s8b_floor_stats.py:14-17`; package:3-5)。

15. [severity: should] [攻撃シナリオ] 新しい golden や runbook に rr80/rr20 の三軸 literal を同一ファイルで書くと、実測前なのに unknownness の新規 conjunction hit となり、F7 closure を汚染する。 [根拠 `orchestrator/tests/test_s8b_floor_campaign.py:6-10,54-63`; `output/insights/2026-07-16_s8b-floor-protocol-package.md:461-465`; `output/s8b-freeze/holdout_freeze.json:34-37`] [提案] floor テストは現行どおり synthetic 軸を使い、wave 前後で unknownness hit 集合が増えていないことを機械比較する。

16. [severity: must-fix] [攻撃シナリオ] 現 golden は実装出力を得て貼ったことを自認し、`verify_floor_artifact` も生成側と同じ関数を呼ぶ。median→mean、sample→population、`>`→`>=`、pair-key誤りをコードと期待値へ同時に入れれば全部緑になる。 [根拠 `orchestrator/tests/test_s8b_floor_campaign.py:296-303`; `orchestrator/tests/test_s8b_floor_stats.py:2-8`; `orchestrator/campaign/s8b_floor_stats.py:6-7`; `docs/phase3-8b-descriptor-design.md:363-365`] [提案] production を import しない stdlib-only reference calculator と、手計算可能な小標本を用意する。必須 mutation は median/mean、stdev/pstdev、10%・15% の境界演算子、各 anomaly gate 除去、null skip、stock anomaly の全 pair 伝播、cell/config key混同、scale ±10%。各 mutantで少なくとも1テストが赤になることを機械実行し、test 名・collect case の削除差分も監査する。

17. [severity: must-fix] [攻撃シナリオ] レーン別 commit は S と C のような同時変更必須境界で中間赤 commitを作る。レーン内レビューだけでは、threshold key 名の不一致、E contract 未適用、S/C の cell key と M の config key不一致を捕捉しない。 [根拠 `orchestrator/campaign/s8b_floor_campaign.py:231-236,978-998,1150-1154`; `orchestrator/campaign/s8b_oracle_driver.py:456-457`; `CLAUDE.md:92-93,153`] [提案] S+C は一つの原子的 commit、または各 commit が全走緑になる additive migration にする。全 lane 合成後に専任の結合レビューと、protocol→schedule→result→reference verify→v2 shape、env mismatch時の実行0回、direct official拒否を通す。phase 完了チェックは該当実装と同じ commit に置く。

18. [severity: should] [攻撃シナリオ] 「テスト＝機械修正」として sonnet にまとめると、最も難しい独立 oracle・閾値境界・scheduler resume・G12 fail-closed の設計判断が低い検討枠へ落ちる。 [根拠 `docs/handoff/2026-07-18-ruled-wave-f1-f5.md:23-25`; `orchestrator/tests/test_s8b_floor_stats.py:2-8`; `docs/phase3-8b-descriptor-design.md:373-377`] [提案] S/C/E のテスト設計と M の schema/negative test は実装と同じ high 枠で扱う。sonnet は契約確定後の fixture 一括置換、名称変更、docs 整形だけに限定する。

総合判定: 修正後に進めよ
