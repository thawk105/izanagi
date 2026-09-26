# 段 4 裁定 — [T-2797] B-5 v2 の投入準備 (2026-09-26 22:45 JST、親)

入力: brief `s1-brief.md`、plan `codex/plan-1.md`、相談 `codex/consult-a.md` (正しさ境界)・`codex/consult-b.md` (過剰・削除)。裁定 inbox は wave 開始後の新着なし。

## 所見の裁定

| 所見 | 判定 | 採否 |
|---|---|---|
| A1 stock の別 job 化は D2249 追加項の「同じ job で測る対照」と承認済み案 (1a)「job 1 = stock + 評価 1 (§5.4 どおり同 job)」に反する | real | 採用: (P2) を撤回し §5.4 を維持 (下記 J1) |
| B7 stock 別 job の全廃は (1a) を不成立にする | refuted (前提が変わる) | J1 で解消 |
| A2・A3 events だけでは途中死後の B・score が一意でない | real (経路は実在) | 縮小採用 (B1・B2 と合わせ J4): 自動回収せず系列を止める |
| B1 投入予約・scheduler 照会は後送 | real | 採用 (DW-G02) |
| B2 自動回収・計算側の二重判定は過剰 | real | 採用: 計算側は「要求 step = 台帳の次 step」の 1 回照合だけ (B3 の縮小形) |
| A4 正常終了で提案が無いものを無料 retry にしない | real | 採用 (J3) |
| A5 429 の文言判定は誤分類する | real | 採用 (J3) |
| A6 critic prompt の追加だけでは吸収状態を排除できない | real | 開示で採用 (機構は足さない)。検疫・役割文書は変えない |
| A7 親の (d) 内訳 | refuted (一致) | insight の「12 件すべて検疫」を 11 + 1 に訂正 |
| A8・A9・B9 3 arm 同時 active は「同時刻対照」ではない | real | 採用 (J5): 同時刻対照 = §5.4 の同 job stock。arm の対づけ・実行順の均衡は残し、同時進行は要求しない |
| A9 §7.3 の独立性の根拠から時間分離を外す | real | docs (親) で採用 |
| A10 870 job・無期限 429 の完走 | real (should) | 起動器を台帳から再開可能にし、暦時間のシナリオを発効束に書く |
| B4 v1 経路・互換 golden の並走は薄い | 部分採用 | v1 の既存コード・既存 test は残す (期待値を変えない)。v1 用の新 golden は足さない |
| B5 report を v2 専用に | 不採用 | 既存 v1 test の期待値を変えないため、版の分岐で v2 を足す |
| B6 LLM 親起動器は最小改修 | 部分採用 | repo に入れる (429 規則を test で固定するため) が、v1 driver の最小移植。apiKeyHelper の事前走査は入れない (v1 の禁止環境変数検査は保つ) |
| B8 15 session を 3 job × 5 に固定しない | 部分採用 | 既存の block-stock 構造 (batch ごと 5 session) をそのまま使い、CV と fallback は 15 session を pool する |
| B10 balanced 実測の後に採否 | refuted (維持) | 実測中 (vprobe chain) |
| B11 report の要否 | 維持 | 発効束が解析規則の bytes を固定するため本 wave に入れる (v2 分岐のみ) |

## 確定した設計 (plan v2)

- **J0 版:** v2 cohort `b5-registered-v2`、登録版 `b5-generator-contrast-v2`。cohort → 版の対応を単位 B・D の共有契約にする。v1 の `COHORT_*`・`PREREG_VERSION`・v1 の preimage・v1 の判定は bytes 不変の挙動を保つ。
  random の preimage は v2 の版文字列で作り直す (v1 の値は既知なので流用しない)。sweep 順序は系列番号からの決定で v1 と同じ。
  v2 の workload は write-heavy・balanced の 2 つ。n = 12、B = 10、A = 30、N_eval = 5、`MAX_MACHINE_RETRIES` = 2 は不変。
- **J1 job の切り方 (全 arm 共通):** job 1 = 系列開始 stock 1 session + 評価 1、job 2〜10 = 評価 1 回ずつ、最終 job = score 5 session。
  - LLM の原提案 1 は stock の current_perf を要するので、**job 1 の中でだけ** v1 と同じ handshake で最初の採用提案を待つ (期限は v1 の 2,700 s/原提案)。却下された原提案 (A 消費) の後も同 job で次の原提案を待つ。
  - job 1 の待ちの間に login 側が 429 (J3) を検知したら、`handshake/outage-<a>.json` を公開し、job 1 はそれを見て評価せずに終了する (A・B 不消費、系列を終えない)。解除後の次の job 1 は stock を測り直し、同じ a の request を新しい stock の current_perf で公開し直す。
    測った stock は台帳に残るが、次の job 1 の stock が以後の current_perf になる (`expected_inputs` の「最後の certified stock/評価」の規則のまま)。
  - job 1 の待ちが 429 以外で期限切れ: v1 と同じ `proposal-wait-timeout` で系列を終える (親の故障の retry は J3 のとおり login 側で先に尽くす)。
  - a ≥ 2 の提案待ちは node の外 (login の起動器)。次の評価 job は、提案が公開され継承検査 (`assert_inherited_inputs`) を通ってから投入する。
  - random / sweep も同じ job 境界 (提案は待たずに決まる)。
- **J2 記帳の分担:** 評価・stock・score の event は計算 job が append。job が走っていない間の handshake 記帳 (`proposal-opportunity`・login で確定した `proposal-rejected`、request の公開) は起動器が append。
  同じ系列に同時に 2 つの書き手が出ないことは、起動器が「1 系列に active job は 1 つ」を守ることで担う (単一の起動器 process、pid/lock file 1 個)。
  A の計上点は「原提案が確定した時点 (採用 or 却下 or 空出力)」。429 の保留中は A を増やさない。
- **J3 LLM 親の起動と 429:** v1 `llm_parent_driver.py` の役割を repo の小 module (`tools/pegasus/b5_llm_parent.py` 程度) へ最小移植し、起動器から使う。
  - 429 = 親の終了記録 (`out.json`) が JSON として読め、`is_error == true` かつ `api_error_status == 429`。文言だけでは判定しない。読めない JSON は 429 と推定しない。
    429 は期限なしで保留し、同じ session を同じ a で再開する (週上限の解除時刻は記録するが判定に使わない。再開は周期的な再試行でよい)。A・B・retry 回数を増やさない。
  - 正常終了 (`is_error == false`、rc 0) で proposal も rejected も公開されない = 空出力: 起動器が `proposal-rejected` (理由 empty-output) を記帳し A を消費。
  - それ以外の異常終了 (rc ≠ 0、429 以外の is_error、process 消失): 同じ a で追加 2 回まで再起動。尽きたら系列を `unclassified-missing` で終える (§3.3 の機械故障上限と同じ扱い)。
  - 従量課金経路は作らない: v1 の禁止環境変数 (`ANTHROPIC_API_KEY` 等) 検査を保つ。apiKeyHelper の事前走査は足さない。
- **J4 途中死・二重投入:** 投入予約・scheduler 照会・自動回収は入れない。起動器は、系列の台帳に結果の無い `slot-attempt-start` (job が途中で死んだ跡) を見つけたら、その系列を止めて (他系列は続ける)
  状態を報告する。qsub が失敗・無応答なら起動器を fail-closed で止める。計算 job は起動時に「要求された step が台帳から導いた次の step と一致する」ことを 1 回だけ確かめ、違えば session を始めずに rc ≠ 0 で終わる。
- **J5 対づけと実行順:** 各 workload の同じ系列番号の 3 arm を対にし、arm の実行順 (6 通り × 2) を v1 と同じ均衡割当で発効前に固定する。起動器は対を系列番号順に開き、対の中は固定順で系列を開始する。
  同時に進める系列数の上限は起動器の引数 (発効束に固定)。LLM だけが 429 で止まっても相方は進めてよい (時間の揃えは要求しない、D2249 追加項)。
  batch (旧 block、系列 1〜4 / 5〜8 / 9〜12) は実行 batch の名札として残し、batch 間の時間規則と batch ごとの判定条件は持たない。workload stock は batch ごと 5 session (旧 block stock と同じ job 構造)。
- **J6 (c2) 同時検査:** write-heavy の v2 slot に `--verify-performance-concurrent` を付ける。balanced は vprobe の実測を見て段 5 の単位 C で決める (付けない場合も v2 に理由を書く)。静定上限 120 s は実測を見るまで変えない。
- **J7 report:** v2 分岐 = 比較族 4 (2 workload × 2 baseline、Holm 初段 0.05/4)、batch ごとの median(d) > 0 と「batch に 1 対以上」の条件を判定から外す (記述として残すのは可)、
  `CV_stock(w)` = workload の 15 session の session median の標本 CV (batch 内 CV との最大は取らない)、fallback score = 同 15 session の median。v1 の判定は変えない。
- **J8 (d):** critic prompt `output_format_request` へ plan-1 §1 の 1 節を足す。v2 cohort の critic の `parent_disclosures` と planner/coder 向けの事実文面 (「1 job で系列全体」) を v2 の job 構成に合わせる。v1 の文面・golden は変えない。

## 単位と所有 (素集合)

- **A** `tools/b5_llm_round.py`、`orchestrator/tests/test_b5_llm_round.py`。規模上限: 変更 150 行。
- **B** `orchestrator/campaign/b5_generator_contrast.py`、`tools/pegasus/b5_contrast_launch.py`、新 `tools/pegasus/b5_llm_parent.py`、`tools/pegasus/p3_s4_loop_pegasus.sh`、
  `orchestrator/tests/test_b5_generator_contrast.py`、`orchestrator/tests/test_b5_contrast_launch.py`、新 `orchestrator/tests/test_b5_llm_parent.py`、job body の既存 consumer test (名指しは実装子が列挙)。規模上限: 変更 1,400 行 (test 込み)。
- **C** (vprobe の後) `orchestrator/campaign/p3_s4_loop.py`、`orchestrator/tests/test_p3_s4_loop.py`。規模上限: 80 行。
- **D** `orchestrator/campaign/b5_generator_contrast_report.py`、`orchestrator/tests/test_b5_generator_contrast_report.py`。規模上限: 500 行。
- docs (v1 閉鎖節、v2 事前登録、発効束、insight、fragment) は親。

既存 test の期待値は変えない。例外は単位 C の `test_concurrent_verify_cli_rejects_missing_requirements` の balanced 拒否例 (balanced を許す裁定になった場合だけ read-heavy 拒否例へ替える)。

## 変異の事前登録 (段 6 で走らせる。位置は実装後に確定)

| ID | 単位 | 変異 | 殺すべき test の性質 |
|---|---|---|---|
| M-A1 | A | critic prompt の追加節を削る | critic-prompt.md の bytes に節があることを見る test |
| M-A2 | A | v2 の parent_disclosures を v1 の「1 job で系列全体」に戻す | v2 の critic prompt の文面 test |
| M-B1 | B | 429 を通常の親異常終了として retry 回数に数える | 429 を 3 回挟んでも同じ a が採用され A・B・欠測が変わらない test |
| M-B2 | B | 429 判定を文言一致だけにする (is_error / status を見ない) | 成功応答が文言を含んでも 429 扱いしない負例 |
| M-B3 | B | `proposal-opportunity` (A の計上) を提案待ちの前に戻す | 429 保留中に A が増えない test |
| M-B4 | B | 空出力 (正常終了・提案なし) を retry 扱いにする | 空出力で A が 1 増え rejected が記帳される test |
| M-B5 | B | job 1 で stock の後に評価 1 を行わず終える (stock を別 job にする) | job 1 の実行単位が stock + 評価 1 である test (全 arm) |
| M-B6 | B | 評価 job が 2 回以上の評価を行う | 1 step = 評価 1 回の test |
| M-B7 | B | 計算 job の step 照合を外す | 台帳と違う step の job が session を始めない test |
| M-C1 | C | balanced を拒否したまま (C で許す場合) | balanced 受理 test |
| M-C2 | C | read-heavy まで許す | read-heavy 拒否 test |
| M-D1 | D | v2 の Holm を 6 比較で計算 | v2 fixture の補正 p |
| M-D2 | D | v2 に batch ごとの median(d) > 0 条件を残す | batch 条件だけが崩れる v2 fixture で優越が成立する test |
| M-D3 | D | v2 の CV を batch 内 CV との最大に戻す | pooled CV と max が違う v2 fixture |
| M-D4 | D | v2 の fallback を batch の 5 session median に戻す | pooled 15 median と違う v2 fixture |

各変異は実装後に、同じ入力を拒否する層が他に無いこと (単一理由性) を確かめてから走らせる。確かめられない変異は登録を外し、理由を台帳に書く。

## 追補 1 (2026-09-26 23:00 JST、親)

- J0 の「sweep 順序は v1 と同じ」を改め、**sweep の順序も v2 の版文字列 (`b5-generator-contrast-v2|sweep|w|r|v`) で作り直す**。random と同じく preimage は登録版を含むことで一貫させ、
  v1 の sweep 系列で一部を閲覧済みの順序を流用しない。段 6 の fix で単位 B に反映する (v1 の preimage は不変)。
