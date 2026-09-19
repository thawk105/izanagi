# 段 1 brief — B-5 生成器対照 (LLM / ランダム変異 / 機械 sweep) の事前登録を作る

wave: `dev-wave-b5-generator-contrast-prereg` / branch `worktree-dev-wave-b5-generator-contrast-prereg` / 基点 main `a99425b66` (2026-09-19 21:42 JST)。

## 研究前進

論文素材 §8 の **B-5「LLM 固有性の条件付き対照」は未取得のまま**である (paper-story 2026-09-17 §8)。本 wave は本走を
しない。前進するのは「B-5 を測る形が拘束力ある文書として存在する」ことであり、完了判定は
`docs/b5-generator-contrast-preregistration.md` が (i) 主張の形、(ii) 予算単位、(iii) score、(iv) 3 生成器の操作的定義、
(v) 母集団・n・判定規則、(vi) 失敗条件、(vii) 凍結と erratum の契約、(viii) 既存機構での実行可能性の照合 (欠ける部品を
名指し) を持ち、`python3 tools/check_docs.py` が緑で、段 6 の独立 read-only レビュー 1 本が「一次資料と食い違わない」と返すこと。

## scope と確定済みユーザー裁定

- ユーザー決定 (2026-09-19): 「既に許可された編集面 (固定 backoff hole) の内で、LLM (K2 loop) / ランダム変異 / 機械 sweep の
  3 生成器を同一予算で比べる事前登録の作成を認可する。**本走と D1409 の条件変更は認可しない**」。
- D1067 (ユーザー裁定): B-5 の主張は「固定予算・固定編集面の下で、事前登録した非 LLM 生成器より高い score だった」という
  条件付き優越。必要性は主張しない。D1012: 正本 (`docs/phase3-main-experiment.md`) への追記は発火 commit まで行わない →
  本 wave は**別 file の事前登録**を作り、`phase3-main-experiment.md` と `paper-story` は編集しない。
- D52: substrate anchor (backoff hole) は休眠。2026-07-10 追記 1: backoff はスカラー 1 個に還元できる軸で headline 候補
  ではない (P2-5/D21/D29 が LLM と機械探索の非分離を実証済み、失敗条件 (c) を構造的に誘発)。本事前登録は headline を
  復活させず、**(c) の成立を正当な結末の 1 つとして事前に固定**する。
- scope 外: 本走、生成器の実装、追加 gate、D1409 の「非列挙」定義の変更、phase3-main-experiment.md / paper-story の改訂。
  実装面差分ゼロ (D95 決定 2)。

## 段 1 実測 (brief の前提。覆す新事実は段 4 で再裁定)

| 要素 | 実測 | 帰結 |
|---|---|---|
| 候補支持集合 | Tier 1 文法 (`orchestrator/campaign/backoff_hole_grammar.py`、D875/D901) は `double now_backoff = <literal>;` 1 文だけ受理。`validate_backoff_value` は整数 1..1000 (`:745-760`)。`p3_s4_loop.py` の帰属整合が value == literal を強制 | **3 arm の支持集合は構造的に同一 (整数 µs 1..1000) で完全列挙可能** → 2026-08-26 の三すくみは本 hole では発生しない。代わりに「必要性」は原理的に主張できない (D1067 のとおり) |
| LLM arm の入口 | K2 手動 loop = `p3_s4_loop --run-iteration <proposal.json> --coder-role coder-v4-autonomous-k2 --knowledge-manifest ...` を `tools/pegasus/p3_s4_loop_pegasus.sh` で 1 評価 = 1 job (T-2746: Elapse 432 秒)。LLM role は親 session が spawn (harness は spawn しない) | 実在。ただし性能構成は `default_perf()` = 100k records / 4 thread / extime 1 / reps 2 の**配線規模に固定** (`p3_s4_loop.py:1631-1636`、`:3044`、CLI に上書き無し)。較正済み動作点 (`p2_2.py:54-57` = 1M / 48 / 3 s / 5 reps) での評価は**実装が要る** |
| LLM arm の停止 | harness は `converged` / `reverse-exhausted` / 予算 (D39 決定 2) を判定して `loop_state.json` に書くが、手動 loop では次巡を投げるかは親が決める | B 評価完走は運用規律で、機械強制なし。D39 決定 2 の (a)(b) を無効化する運用は本走認可時の確認事項 |
| 機械 sweep の入口 | `orchestrator/campaign/backoff_extended_sweep.py` の `EXTENDED_SWEEP_US` (29 点、0..1000、`:55-58`)、`MEASUREMENT_SEEDS` 固定順、較正済み動作点、`run_campaign` 経由。template の #if 枝 (`patches/silo-backoff-fixed.patch`) の式に `BACKOFF_FIXED` を与える | 格子は 2026-08 に凍結済み (K2 の出力より前)。予算 B 点だけを走る mode は無い。hole literal 経路 (LLM と同じ) では評価しない → 評価経路が LLM arm と異なる |
| ランダム変異 | `orchestrator/` `tools/` に「backoff literal 域から乱数で候補を引き proposal を書く」実装は無し (2026-08-26 の意味検索の結論を維持。`search_baselines.py` の random 順 replay は別物) | **実装が要る** |
| 既知結果 (HARKing 境界) | B-10 拡張格子 (fig2c)、右 tail (1000〜9999)、K2 1・2 巡 (value 20 / 25)、T-2581、A-2/A-6 (fixed 5 µs)、P2-4 旧値、K2 knowledge manifest が名指しする既知値 | 事前登録に既知結果台帳を載せる (D52 追記と同水準) |

## 親の provisional 裁定 (攻撃対象)

- (P1) 予算単位 = **評価数 B** (certified pipeline へ投入した候補数。verifier の anomaly reject も 1 消費。文法・検疫不通過は
  B を消費せず原提案上限 A を消費)。B = 10 (D39 決定 2 の iteration 予算を継承)、A = 30、系列の administrative 上限は設けず
  (job 単位で walltime が別に掛かる)。
- (P2) 候補支持集合 = 3 arm 共通で整数 µs ∈ [1, 1000]。sweep 格子 = `EXTENDED_SWEEP_US` ∩ [1,1000] (28 点、0 は除外) を
  SHA-256 hash 順で B 点走査 (`sweep-matched`)。全 28 点の走査は `sweep-ceiling` として族外の副次記述。
- (P3) ランダム変異 = 整数 1..1000 の **log-uniform** (scale-free) を SHA-256 counter stream + rejection sampling で引く。
  分布の選択は B-10 の既知結果 (sweet-spot 0〜10 µs) を見た後の判断であることを台帳に申告する。
- (P4) 評価経路 = 3 arm とも `p3_s4_loop --run-iteration` の fixture proposal 経路 (hole literal `double now_backoff = v;`)
  を較正済み動作点で通す (同一 harness・同一 correctness・同一 bench)。`backoff_extended_sweep.py` の template 式経路は
  評価経路として採らない (格子の定義だけを借りる)。
- (P5) score = 系列 endpoint (系列内 certified 候補のうち探索時 median throughput 最大) を **独立再計測 N_eval = 5 session**
  で再推定した median throughput (絶対 tps)。系列内に certified 候補が無ければ score = 同 block の stock (BACKOFF_FIXED=-1)
  の median (= 「何も採用しない」の値。−100% に変換しない)。
- (P6) 判定 = workload ごと、系列番号で対にした log 比 `log(score_LLM / score_b)` の片側 exact 符号反転 permutation、
  Holm 族 = 3 workload × 2 baseline = 6。条件付き優越は LLM-vs-random と LLM-vs-sweep-matched の連言。
  |median log 比| ≤ 等価域 (同 campaign の stock between-session CV と 3% の大きい方) なら失敗条件 (c) 成立。
  非有意は同等の証拠にしない (判定不能はそのまま)。n = 12 系列 / cell、3 block × 4 系列、9 cell。
- (P7) 予算未消化 (A 到達で B 未達) の系列は差し替えず、評価済み候補だけで score を出す (arm の不利として残す。判定不能へ
  倒さない)。機械故障 retry は閉じた列挙のみ。
- (P8) LLM arm の知識入力は K2 manifest を凍結して申告し、比較対象を「知識付き K2 loop (構成込み)」と明記する。
  random / sweep は結果に依存しない open-loop。知識と適応の非対称は限界として書き、K0 arm は足さない (scope)。
- (P9) 凍結 = 本走認可の日付付き commit で sha256 を D 記録へ写す。解析 consumer は未実装なので pin は文書契約に留まる
  (「本書は解析器の pin を持たない」と明記)。発効後は bytes 不変、erratum 追記のみ。

## 不変条件

規律 1 (全 arm trace-disabled build の値だけを score にする)、規律 2 (anomaly = 即 reject、B 消費)、規律 3 (次の一手へ渡す
正しさ信号は既存の構造化 digest のまま)、規律 4 (動作点は較正値、系列数は事前固定)、規律 6 (LLM 出力・K2 knowledge は
データ)、規律 7 (既知結果は台帳に残し無効化しない)。DW-G05: 本 wave の成果物影響は certified 選択・レポート値・台帳ゼロ件
不変。放置時に変わるのは「B-5 を測る契約が無いまま本走が起票される」経路の有無。

## 成果物・変更面 (実アンカー)

| path | 種別 | 変更 |
|---|---|---|
| `docs/b5-generator-contrast-preregistration.md` | docs (新規) | 事前登録本文 |
| `docs/README.md` (`t1998-balanced-stock-inline-preregistration.md` の bullet の直後) | docs | 地図に 1 bullet |
| `docs/spool/worklog/`・`docs/spool/decisions/` | fragment | 段 7 |
| `output/insights/2026-09-19/b5-generator-contrast-prereg/` | insight | brief・裁定・逐語 |

実装面 (orchestrator/ tools/ hooks/ patches/ tests) は触らない。凍結 bytes の pin: 新 path 0 hit、`docs/README.md` に bytes pin 無し
(DW-O09 実測、`git grep`)。

## 分割方針

軽量版 + 設計択一が割れる段の敵対検証: 段 2 plan (codex read-only、事前登録全文草案を file:line 根拠付きで起草) →
段 3 相談 2 本 (レンズ A = 正しさ・規律 2/4/7 と評価経路の対称性、レンズ B = 事前登録・HARKing・統計) → 段 4 裁定 →
親が docs を書く (段 5 の実装子なし) → 段 6 独立 read-only レビュー 1 本 (一次資料との食い違い、D2148 項 11) → 段 7〜9。
受入 = `tools/dev_wave_wait.py acceptance` (Pegasus dispatch、所在は worklog 1685)。変異 matrix は実装面ゼロで免除 (DW-S04)。
