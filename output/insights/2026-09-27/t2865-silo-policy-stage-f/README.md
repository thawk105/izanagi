# silo-function-policy 軸の段階 F — 計算ノードの投入経路・同 job の stock・R2 の入口・trace 保全と、実 LLM の 1 iteration E2E (2026-09-27、[T-2865])

- 位置づけ: 軸オンボーディングの段階 F の記録。採用判断は D2214、段階 E は D2256 (記録 `output/insights/2026-09-26/t2865-silo-policy-stage-e/README.md`)、手順は `docs/phase3-silo-policy-runbook.md`。本段の設計判断は同じ wave の decisions fragment。可変状態の正本 (worklog 末尾) にはしない。
- wave: branch `worktree-dev-wave-t2865-stage-f`、起点 local main `ad114fba0` (開始 gate rc=0)。submodule pin `6810666` (= 方策軸の pin、不変)。
- 逐語 (`verbatim/`): 依頼 `request.md`、段 1 brief、段 2 plan、段 3 相談 A・B、段 4 裁定 `s4-ruling.md` と `interface.md`、段 5 実装子の報告、段 6 のレビュー A・B・裁定 1・2・fix 子の報告 4 本・焦点再レビュー 1、E2E の LLM 出力と proposal (`verbatim/e2e/`)。変異 matrix は `mutation/`。prompt と codex の受領証は wave の job dir (repo 外)。
- **firewall の記録:** coder に渡したのは driver の `--emit-coder-input` の出力 (5 key) そのもので、親は key を足さず値も書き換えていない。偵察・小比較・再測の点 ID・因子・比・順位は coder・planner・auditor のどの入力にも入っていない (planner はこの軸に無い)。codex 子の prompt では段階 D の §2.1 以降・`verbatim/`・`projection.json` 以外の偵察 file・小比較の insight・再測 insight の §2・§3 を読むなと指示した。親は再測 insight の §1.5・§4 (計算量) だけを読んだ。

## 0. 要約

1. **計算ノードの投入経路:** 既存の job body `tools/pegasus/p3_s4_loop_pegasus.sh` に方策 mode (`IZANAGI_S4_POLICY_MODE=stock|pair|replay`) を足した。gflags・glog・masstree の前処理と投入許可台帳の登録を共用し、CCBench は方策軸の pin と照合する。既存 mode (T-2849・B-5・K2・proposal・fixture・stock-control) とは排他で、受理・argv は変えていない。台帳と hooks は変更不要 (登録済み body の mode 追加)。
2. **方策 driver の計算ノード対応:** `--campaign-env pegasus` で login と計算ノードが同じ campaign を指す。計測する操作は実行 site の契約と一致しなければ拒否し、計算ノードでは契約の clocks・numactl・masstree 事前 build 受領証を `run_campaign` に渡す。
3. **同じ動作点の stock:** 原型 source (方策 patch なし) と方策 flag を除いた genome を、stock 用の build context で評価する。初回の baseline は別 campaign (`evaluation_purpose=bootstrap`)、以後は pair job が候補の後に同じ authorization session で stock を測る。`certified-stock` は同じ attempt の source token が STOCK のときだけ。
4. **R2 の入口:** `--replay-proposal` (job mode `replay`) が保存 proposal を実走と同じ gate に通し、別 campaign (`evaluation_purpose=r2`) で LLM なしに評価する。loop の状態と履歴は動かさない。
5. **trace 保全:** 方策 mode では `IZANAGI_TRACE_ARCHIVE_ROOT` (絶対 path・repo 外) を必須にした ([T-2853] (1''))。
6. **実 LLM の 1 iteration E2E (C++ 形) を通した:** coder の 1 候補が preview (検疫・型付き構文検査・単独 TU compile) を通り、auditor が pass、計算ノードで build・legacy verify・性能構成 verify・bench を経て certified (serializable)。同じ job の stock との 5 rep 中央値の比は 2.80 (1 回の観測、主張ではない)。R2 で同じ候補を別 job で再評価し certified、3.74M txn/s。
7. **E2E で見つけたこと:** auditor role の出力の形が driver の auditor gate の閉じた形と合わず、最初の proposal は読込みで拒否された (§3.3)。coder へ渡る固定のリーク防止文脈が backoff 軸用の旧文書のまま (§3.4)。

## 1. 依頼と裁定

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = `verbatim/request.md`): 段階 F として実 LLM の 1 iteration E2E まで。(1) 方策 driver 用の計算ノード投入経路 (driver 選択か兄弟 job body、契約 test と投入許可台帳)、(2) 同じ動作点の stock baseline を同じ job で測る形、(3) job Elapse の実測単価で見積もり検査込みで 2 node 時間以上ならユーザー確認、(4) runbook どおり 1 iteration、firewall 厳守、(5) 新しい job body で [T-2853] (1'') の保全口 opt-in を有効にし、(4) R2 の入口も置く。`p3_s4_loop.py` (flock、並走 T-2104 の担当) は触らない。本題の実装だけ。
- 段 3 相談 2 本 (A 正しさ境界・整合、B 過剰・削除) を受けた段 4 の主な裁定 (`verbatim/s4-ruling.md`):
  - 投入経路は既存 job body の mode 追加 (B-5・T-2849 と同じ先例)。兄弟 body は前処理 600 行の複製になる。
  - 共有 campaign base の配線は作らず、AI worktree 容器外の submit checkout 1 本で stock job・login 側操作・pair job を直列に行う (相談 B)。
  - 初回 stock を loop campaign に入れると pair の同じ stock variant が terminal skip になるので、bootstrap は別 campaign (plan・相談 A・B が一致)。
  - R2 は run id を置かず、job mode は `stock|pair|replay` の 3 値 (相談 B)。
  - login の record-reject が loop_state を先に作ると walltime 予算 (`MAX_WALLTIME_S`) の起点が早まる点はコードを変えず runbook の投入前確認にした (停止条件は D2256 項 3・D39)。
- 計算の確認線 (D2212 項 4): 実験 job の合計への線はユーザー裁定、検査 (焦点走・変異・受入) を足して数えるのは /rulings 第 31 回でユーザーが確定した運用。新種の job は walltime 上限で見積もり、stock job を walltime 1 時間で先に出して単価を測った。上限込みでも検査込み合計が 2 node 時間の下と見積もれたので、ユーザー確認なしで投入した (§4)。

## 2. 実装 (commit)

| commit | 内容 | 作者 |
|---|---|---|
| `4acd5fddf` | 方策 driver (campaign env・site 契約・stock・pair・replay・eval-exception の履歴行) と job body の方策 mode、両 test | Codex author 2 本 (単位 A・B) |
| `6b4100077` | runbook と `tools/pegasus/README.md` §7 | 親 (docs) |
| `a5a7ca2ea` | fix-1 (段 6 レビュー 2 本の所見: 依存 prefix を環境から明示引数に写さない、stock の source token 照合、stock 不成立で rc=1、候補未実走の pair は stock を測らない、log を stderr へ、原型 source 分類 test の compiler 選択) | Codex fix |
| `d2810f773`・`9138194a0`・`9962246ee` | README の pin 読み替えと完全な qsub 例、runbook §1(d) の auditor 出力形 | 親 (docs) |
| `b815183af` | fix-2 (焦点走 1 回目の本 wave 帰属の赤 32 件: resolver の未定義変数、共有の偽 driver の記録形式、新 test の期待、spawn site の define sink) | Codex fix 2 本 |
| `a9cc7dbe3` | fix-3 (`run_campaign` 呼出し 2 箇所を certified writer の caller inventory と namespace の driver 契約へ登録) | Codex fix |
| `8945ca941` | local main `80a3b8e42` の取り込み (競合なし) | 親 |

## 3. 実 LLM の 1 iteration (E2E)

submit checkout: job dir の `trees/e2e` (HEAD `b815183af`、以後の commit は test・docs だけで driver・job body の bytes は同じ)。全操作をこの checkout で直列に行った。保全先は repo 外の `/work/1/SFC/tanab/izanagi-repro-archive/t2865-stage-f-20260927/`。

### 3.1 経過

| 段 | 内容 | 結果 |
|---|---|---|
| (0) stock job | `31468.nqsv`、job Elapse 300 秒 | `certified-stock`、5 rep 中央値 1,377,953 txn/s、abort 12.18%、serializable。trace 保全 340 MB (inventory 6 本 complete) |
| (a) coder 入力 | `--emit-coder-input --campaign-env pegasus` (上の 2 値) | 5 key (`leakproof_context`・`policy_spec`・`baseline`・`recon_projection` = `binary`・`scope` の 2 field・`self_history` = 空) |
| (b) coder | `coder-v4-autonomous-policy` (C++ 形)、1 回 | 1 候補 (confidence low)。abort 後は commit 以降 2 回目の abort から 1〜64 µs の窓を倍々に広げて乱数で散らし、commit ごとに半減。lock 衝突は 4 回まで即再試行、12 回まで 1 µs、以後 2 µs、20 回で abort (`verbatim/e2e/coder-output-1.json`) |
| (c) preview | 検疫・型付き構文検査・単独 TU compile | 通過、diff_digest `0def2b39…` (`verbatim/e2e/preview-1.json`) |
| (d) auditor 1 回目 | 入力 4 key | verdict pass、digest は echo。**出力の形が gate の閉じた形と合わず、(e) の読込みで `AuditorGateFailure`** (§3.3) |
| (d) auditor 2 回目 | 同じ入力 + gate の出力形を prompt に明記 | verdict pass、違反 0、digest は echo (`verbatim/e2e/auditor-output-2.json`)。driver の loader が受理 |
| (f) pair job | `31531.nqsv`、job Elapse 765 秒 | 候補 `certified` (serializable)、同じ job の stock `certified-stock` |
| R2 | `31584.nqsv`、job Elapse 491 秒 | 同じ proposal を別 campaign で再評価し `certified` (serializable) |

### 3.2 値 (5 rep、txn/s)

| attempt | job | 中央値 | 5 rep | abort 率 |
|---|---|---|---|---|
| stock (bootstrap campaign) | 31468 | 1,377,953 | 1,344,093・1,339,185・1,379,157・1,377,953・1,378,925 | 12.18% |
| 候補 (loop campaign) | 31531 | 3,815,265 | 3,887,767・3,803,039・3,815,265・3,779,559・3,830,005 | 20.93% |
| stock (loop campaign、同じ job) | 31531 | 1,361,984 | 1,353,788・1,381,136・1,380,773・1,361,984・1,345,684 | 12.16% |
| 候補の R2 (r2 campaign) | 31584 | 3,741,220 | 3,823,900・3,767,114・3,741,220・3,726,521・3,705,154 | 21.15% |

- 同じ job の比 (候補 ÷ stock の 5 rep 中央値) = 3,815,265 ÷ 1,361,984 = 2.80。**1 iteration・1 候補の観測であり、性能主張ではない。** 同時刻の対照 (同じ job の stock) は取れているが、反復と事前登録の判定規則は無い。
- 候補の verify 中の abort 率は 26.06% (critic digest の verify 統計)。lock 方策が verify 中に発火した証拠は v1 に無い (候補ごとの hook 計数は置いていない、runbook §4)。auditor も「発火証拠なし」として静的構造だけで pass とした。
- loop campaign は iteration 1・履歴 1 行 (outcome `certified`)。bootstrap と r2 の campaign には loop_state も履歴も無い (設計どおり)。
- trace 保全: pair 1.1 GB (2 variant × 6 inventory、すべて complete)、R2 684 MB。見積り稿 §7 の write-heavy 約 0.75 GiB / 評価と同程度。

### 3.3 auditor role の出力形と auditor gate の食い違い (E2E で観測)

1 回目の auditor は `uncertainty` を文字列の配列で、`nits` を文字列の配列で、`proposed_tests` を独自の key (`id`・`red_assert`・`expected_verdict`・`machine_judgement`) で返した。driver の auditor gate (`orchestrator/campaign/auditor_gate.py` の `parse_auditor_dict`) は、`uncertainty` を文字列 1 つ、`nits` を `{"finding"|"note": 文字列}` の配列、`proposed_tests` をちょうど `{mutation, expected_gate, machine_judgment}` の配列に限る閉じた形で、読込みが `AuditorGateFailure: auditor.uncertainty は string のみ` で止まった。`.claude/agents/auditor.md` の出力節は各 field の型を定めていない。runbook の「値を転記し直さない」に従い、親は値を直さず、同じ入力に gate の形を明記して再審査させた (2 回目は gate が受理)。role の改訂はユーザー承認事項なので本 wave では変えず、runbook §1(d) に「prompt に gate の形を明記する」手順を足した。

### 3.4 その他の観測

- **coder の固定リーク防止文脈が backoff 軸用の旧文書:** driver が `leakproof_context` に載せる `src/coder-leakproof-context.md` は段 4 の backoff 軸の説明 (planner・`silo-backoff-magnitude`・値 1 個の提案形式) で、方策軸の入力としては内容が合っていない。coder は `policy_spec` に従って方策を書いた。段階 E の設計どおりの値なので本 wave では変えていない。
- **骨格の乱数の初期値がスレッド間で同じ:** 2 回目の auditor の note。`patches/silo-function-policy-variant.patch` の `thread_local` 乱数状態の初期値が全スレッドで同じなので、`ctx.rand` の系列がスレッド間で揃い、乱数で待ち時間を散らす方策の効果が弱まる。正しさには影響しない。
- **pair の出力 JSON に候補の throughput が無い:** 候補の値は critic digest と WAL の BENCH_DONE から読んだ。stock の値は JSON に出る。

## 4. 計算ノードの使用 (job Elapse)

| 用途 | request | Elapse |
|---|---|---|
| 焦点走 1〜3 | 31353・31451・31470 | 87・138・140 秒 |
| 変異対象 2 file の単独走 (単価測定) | (dispatch) | 17 秒 |
| stock job | 31468 | 300 秒 |
| pair job | 31531 | 765 秒 |
| R2 job | 31584 | 491 秒 |
| 変異 probe 12 本・probe 1 本・final 12 本 | (dispatch、使い捨て木) | harness の所要合計 1,644 秒 (待ち行列込みの上限。使い捨て木ごと受領証が消えるので Elapse は取れていない) |

受入を除く合計は 3,582 秒以下 (約 1.0 node 時間以下)。受入は §6 に書く。LLM の直列時間: coder 1 回 約 2 分、auditor 2 回 約 2 分 + 約 1.5 分。

## 5. 変異 matrix (段 4・段 6 の事前登録)

final 12 / 12 KILLED (独立 clone、main = `9138194a0`、runner `tools/run_tests.py --force-dispatch test_p3_s4_loop_policy.py test_p3_s4_loop_job_contract.py`)。spec と結果は `mutation/`。

| id | 壊す箇所 | kill した test |
|---|---|---|
| M-F1 | stock genome に方策 flag を残す | stock genome と baseline の test |
| M-F2 | baseline の × 100 を落とす | 同上 |
| M-F3 | baseline が別 attempt を読む | 同上と stock source 照合の test |
| M-F4 | R2 が loop を進める | R2 の gate 再照合と loop 非進行の test |
| M-F5 | R2 で auditor を渡さない | 同上 |
| M-F6 | `pegasus` の env marker を焼かない | campaign identity の test |
| M-F7 | job body の方策 pin を旧 pin に戻す | 方策 mode の実 shell test 群と既存の fragment mutant test |
| M-F8 | job body の保全 root 検査を消す | 保全 root 拒否の test 群 |
| M-F9 | stock の source token 照合を外す | stock source 照合の test |
| M-F10 | `--stock-baseline` の rc を常に 0 | stock 不成立の rc test と stock CLI の test |
| M-F11 | 候補未実走でも stock を測る | 候補未実走の pair の test |
| M-F12b | 依存 prefix を環境から写す + `pegasus` guard を開く (2 層) | stock CLI の prefix と stderr log の test |

**erratum (probe 1):** M-F12 (依存 prefix を環境から写すだけ) は SURVIVED。test は `linux-baremetal` 契約で走り、`pegasus` のときだけ prefix を付ける guard に隠される (mask)。DW-M02 に従い guard も開く 2 層変異 M-F12b に照準し直し、意図した test が kill した。計算ノードの `pegasus` 契約の下で prefix を写さないことの直接の検査は無い (本番の経路は焦点走でなく E2E の job で通った)。

## 6. 受入

記録時点では未実施。

## 7. scope 外と次の一手

- 2 iteration 目以降 (critic の spawn と `--critic-output`) は本 wave で回していない。runbook §1(g) の手順はそのまま使える。
- LLM 対 非 LLM の対照 ([T-2867]、事前登録草稿 `docs/silo-policy-generator-contrast-preregistration.md`) が要る driver 側の口は本 wave の対象外。
- auditor role の出力節に gate の閉じた形を書く改訂と、coder の固定リーク防止文脈を方策軸用にする改訂は、role・固定入力の変更でユーザー承認事項。持ち越しに起票した。
- 骨格の乱数初期値の問題 (§3.4) は性能上の指摘で、正しさ・受理集合を変えない。記録に留める。
