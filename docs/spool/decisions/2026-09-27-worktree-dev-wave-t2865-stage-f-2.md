---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-27
wave: worktree-dev-wave-t2865-stage-f
seq: 2
---

## {{D:silo-policy-stage-f}}. silo-function-policy 軸の段階 F — 既存 job body に方策 mode を足して計算ノードで回し、初回 stock は別 campaign、以後は候補の後に同じ job で stock を測り、R2 は別 campaign の保存 proposal 再評価、trace 保全は方策 mode で必須にする

**決定:** D2214・D2256 に従い、軸 `silo-function-policy` の段階 F を次の形で実装し、実 LLM (C++ 形) の 1 iteration を E2E で通した。記録は `output/insights/2026-09-27/t2865-silo-policy-stage-f/README.md`、手順は `docs/phase3-silo-policy-runbook.md`。

1. **投入経路は既存の job body `tools/pegasus/p3_s4_loop_pegasus.sh` への方策 mode (`IZANAGI_S4_POLICY_MODE=stock|pair|replay`、`IZANAGI_S4_POLICY_FORM=cpp|ir`) の追加。** gflags・glog・masstree の前処理と投入許可台帳の登録を共用する。方策 mode は T-2849・B-5・K2・`IZANAGI_S4_PROPOSAL_PATH`・fixture・`IZANAGI_S4_STOCK_CONTROL` と排他で、CCBench は方策軸の pin を 40 桁へ解決して照合する。既存 mode の受理・argv は変えない。台帳と hooks は変更しない (登録済み body の mode 追加)。
2. **方策 driver の campaign 環境は `--campaign-env` で選ぶ。** 既定 `linux-baremetal` の identity は不変、`pegasus` は `p3_s4_loop` と同じ `measurement_env` 束縛で、login の emit・preview・record-reject と計算ノードの評価が同じ campaign を指す。計測する操作は実行 site の契約と一致しなければ実行前に拒否する。計算ノードでは契約の clocks・numactl・masstree 事前 build 受領証を `run_campaign` に渡し、依存 prefix は `p3_s4_loop` と同じく明示引数に写さない (job body が export した環境変数を build が読む)。
3. **stock は原型 source (方策 patch なし) と方策 flag を除いた genome を、coder authority の無い stock 用 build context と stock capability resolver で評価する。** `certified-stock` は同じ attempt の BUILD_START の source token が STOCK のときだけで、baseline の abort 率は同じ attempt の bench の `abort_rate` × 100。初回の baseline は別 campaign (`evaluation_purpose=bootstrap`) で測り、以後は `--run-iteration --stock-control` (pair) が候補の後に同じ authorization session で stock を測る。stock が不成立なら rc=1、候補が走らなかった pair は stock を測らず rc=1。
4. **R2 の入口は `--replay-proposal` (job mode `replay`)。** 保存 proposal (`{coder, auditor}`) を実走と同じ gate (検疫・構文・単独 TU・auditor の digest 照合と veto・書込後の digest 再照合) に通し、別 campaign (`evaluation_purpose=r2`) で LLM なしに評価する。loop の状態と履歴は作らない。
5. **trace 保全は方策 mode で必須。** `IZANAGI_TRACE_ARCHIVE_ROOT` (絶対 path・repo と git common repo の外) を driver 起動前に検査する (再現パッケージの持ち越し項目 (1'')、保全の実体は D2233・D2247、qsub の env で渡す運用は D2261 項 3)。他 mode の挙動は変えない。
6. **評価が例外で終わった iteration は履歴に `eval-exception` の行を残す。** loop_state の iteration と履歴の行が食い違わないため (規律 3)。
7. **login 側の操作と計算ノードの job は、AI worktree 容器の外の submit checkout 1 本で直列に行う。** campaign dir はその checkout の `output/` にでき、共有の出力先の配線は置かない。

**理由:**
- 兄弟 job body は前処理と reservation・receipt・pin 検査の約 600 行を複製する。B-5・T-2849 も同じ body の mode として足した先例がある。
- 初回 stock を loop campaign に入れると、pair で測る同じ stock variant が terminal skip になり、同じ job の対照が取れない (段 2 plan、段 3 相談 A・B が一致)。
- 同じ job の stock があれば、1 回の候補評価に同時刻の対照が付く。
- 方策 driver の `run_campaign` 呼出しを共通 helper にまとめると、spawn site 台帳の define sink 検査 (T-2155) が方策 flag に到達しうる未登録の build 入口として拒否した。stock と候補の各関数に置けば base と同じく全 define が proven-unreachable になる。登録簿 (certified writer の caller inventory と exploration namespace の driver 契約) は `p3_s4_loop` と同じく 2 箇所で登録した。

**却下した選択肢:**
- 兄弟 job body — 上記。
- 共有 campaign base (`IZANAGI_EXPLORATION_OUTPUT_ROOT` を login と job で揃える) — 逐次運用なら submit checkout 1 本の既定 `output/` で足り、指定漏れで履歴が別 campaign に割れる危険だけが増える (段 3 相談 B)。
- R2 の run id と `replay-pair` mode — 今回の入口に要らない。同じ候補を同じ checkout で繰り返す必要が出たときに足す。
- login の record-reject で loop の walltime 起点が早まる点をコードで直す — 停止条件は D2256 項 3・D39 の予算で、runbook の投入前確認で足りる。
- 依存 prefix を環境から明示引数に写す (段 5 の初版) — build の明示引数はセミコロン区切りで解釈され、コロン区切りの環境値が 1 つの不正 path になる (段 6 レビュー A)。
