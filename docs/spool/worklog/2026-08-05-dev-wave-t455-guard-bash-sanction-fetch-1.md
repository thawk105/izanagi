---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t455-guard-bash-sanction-fetch
seq: 1
title: [T-455] third-party 取得ツールを guard_bash の sanctioned 実行体に加えた — 敵対 2 レンズが land 済み login 手順の 2 例目を掘り当て、族一般化に DW-G03 の根拠が揃った (コード + docs、branch worktree-dev-wave-t455-guard-bash-sanction-fetch)
---

## 本文

- **ユーザー裁定 (2026-08-04 /rulings = 択 (a)) をそのまま実装した。** 2026-08-04 の [T-340] wave
  段 9 直後に見つかりながら起動されずにいた依頼で、一次控えは rulings-inbox の
  `2026-08-04-t340-guard-bash-sanctioned-path.md`。`_SANCTIONED_PATHS` へ 1 件足し、
  判定分岐は変更していない。
- **段 1 で裁定の 3 前提を実物で測った。** 模擬を使わず、hook を実 subprocess として起動し
  実 stdin を与えた (pegasus02 = login node)。(a) 当該綴りが rc=2 で拒否されること、
  (b) 資源分類が runbook §7.0 の実測表で 4 経路とも local-ok であること、
  (c) 同型先例が既に sanctioned であること。3 つとも成立した。
- **軽量版で走らせた。** `hooks/README.md` が本層 (Pegasus 重量処理層) を明示的に
  「正しさ防壁ではない」と分類しており、成果物の受理集合も動かないため、段 2・3 を省いた。
  ただし allowlist 拡大なので段 6 の敵対レビュー 2 本は残した。**この判断が当たった** —
  レビューが下記の独立 2 例目を掘り当てたのは段 6 だけである。
- **段 6 で real 4 件・refuted 5 件。うち scope 内 fix は 1 件。** 実装子が置いた
  「非 sanctioned 兄弟は拒否のまま」の positive control が `collect_receipt.py` を選んでおり、
  それは `tools/pegasus/README.md` §3 が**ログインノードで実行すると定める手順の実行体**だった。
  未裁定の拒否を「守るべき性質」として pin してしまうため、control を計算ノード側 job script
  (`certify_calibration.sh`) へ差し替えた。`hooks/guard_bash.py` の受理集合は 1 bit も変えていない。
- **{{T:pegasus-login-procedure-blocked-family}} は本 wave 最大の発見である。** 上記の
  `collect_receipt.py` は [T-455] (`fetch_third_party.py`) と**独立同型の 2 例目**であり、
  `DW-G03` の「族全体への制度一般化は同型欠陥が異なる producer/consumer で独立に 2 件
  再現したときだけ許す」が充足された。裁定時に「射程が広い」として退けられた択 (b)
  (一律 `tools/pegasus/` 判定を実測済み分類に基づく allowlist / denylist へ変える) に、
  制度化の根拠が揃ったことになる。
- **レンズ間で scope 判定が割れ、親は B を採った。** 「sanctioned は path 粒度なので
  未計測 argv (`--repo-root` 等) まで開く」をレンズ A は scope 内 must-fix、レンズ B は
  scope 外と判定した。親は B を採用した。A の提案する対処 (comment での限定) は受理集合を
  1 bit も閉じず、`DW-G05` の「実装しなければ成果物のどの値が変わるか」に対する有効な対処に
  なっていないためである。実効修正は択 (b) の領域なので {{T:sanctioned-path-argv-granularity}}
  として返す。
- **裁定の前提を覆す新事実ではないと判定した。** runbook 自身が「分類は現 pin 限定」「入力上限の
  ない経路は unknown = dispatch-required」を land 済みで明記しており、裁定文はその runbook を
  根拠に引いている。よって `DW-STOP` の停止条件には当たらないと判断し、実装を進めた。
- **変異は初回 M2 が MISMATCH になり、erratum を残して v2 で閉じた。** M1 (sanctioned 1 行削除) は
  事前登録どおり 2 node ちょうどが赤で KILLED、**単一理由性が実測で成立**した。M2
  (pegasus 配下を一律許可へ退行) は事前登録で「冗長 gate」と宣言していたが、実際の赤は 5 node で
  冗長の幅を過小に登録していた。初回結果は消さず、期待 node を実測どおりに直した v2 を走らせて
  KILLED を得た (`DW-M02`)。M2 は宣言どおり単独変異の検出力証拠からは外す。
- **段 6 の焦点再レビューは行っていない。** fix が control 名の差し替え 1 点で、
  `hooks/guard_bash.py` に触れず受理集合を変えないため、追加の codex 巡回でなく
  親の変異 matrix と受入全走で裏取りした。
- **受入・監査の実測値。** `tools/run_tests.py` 全走 = **5904 passed / 19 skipped** (662.47s、
  計算ノード dispatch、rc=0)。`tools/check_ai_provenance.py` 全履歴 = **1193 件、違反なし**。
  `tools/check_docs.py` = 違反なし。main 取り込み (4fbd890、13 commit) は事前に incoming 監査を
  通してから merge commit にした。
- **段 8 の dev-wave 改善候補 3 件は、いずれも実装せず記録に留めた。** (a) 冗長 gate と明記する
  変異でも `expected_nodes` は全層を列挙する必要がある (本 wave の M2 MISMATCH の直接原因。
  `DW-M03` は期待 node の書き方に触れていない)。(b) positive control に land 済み手順の実行体を
  選ばない (本 wave が踏み、段 6 で fix した)。(c) `tools/run_tests.py` が `--overall-grace` を
  通す口を持たず、並行 wave で gen_S が滞留すると受入が infra rc=16 で落ちうる (今回は
  落ちなかったので near miss、実測 1 例なので failures へは送らない)。いずれも
  `docs/dev-wave/` への追記が要るが集計予算が **25,196 / 25,200 = 残り 4 bytes** で入らない。
  **上限引き上げは提案しない。** (191) の V5、(181) の `DW-O18` 追記、(192) の候補 (a) に続く
  **4 例目**であり、解放は [T-454] が所有する。

## 次の一手差分

### 完了

- [T-455] guard_bash の `_SANCTIONED_PATHS` へ `tools/pegasus/fetch_third_party.py` を足した。
  段 1 で裁定 3 前提を実測、段 6 で敵対 2 レンズ、変異 M1 = KILLED (単一理由) /
  M2-v2 = KILLED (冗長 gate 5 層)。scope 外の real 所見 3 件は新規項目として返した。
  remaining: none
  base: 888dee3379464cf3e4683850e062db0de8f37c57ea21fa79e62c230743f6c965

### 新規

- {{T:pegasus-login-procedure-blocked-family}} **P2・新規 (ユーザー裁定待ち)**:
  land 済みの login 手順が `hooks/guard_bash.py` に機械拒否される欠陥の**族一般化**を裁定する。
  [T-455] (`fetch_third_party.py`) に加え、`tools/pegasus/README.md` §3 が
  「job 終了後、ログインノードで」実行すると定める `collect_receipt.py` でも同型が再現した
  (親が実 hook subprocess で rc=2 を確認)。**独立 2 例が揃ったので `DW-G03` は充足**しており、
  [T-455] 裁定時に射程の広さを理由に退けられた択 (b) — 一律 `tools/pegasus/` 判定を
  実測済み資源分類に基づく allowlist / denylist へ変える — を再提示する。
  現状維持なら `collect_receipt.py` は 1 件ずつ sanctioned 化するか、README §3 に
  hook 拒否の注記が要る。逐語は `output/insights/2026-08-05_t455-guard-bash-sanction/`
- {{T:sanctioned-path-argv-granularity}} **P2・新規 (ユーザー裁定待ち)**:
  sanctioned 判定は **path 粒度**であり、entry が受ける全 argv を測定 tuple へ束縛しない。
  実測: `python3 tools/pegasus/fetch_third_party.py fetch --repo-root /work/alternate
  --cache-root /work/cache` は rc=0 で通るが、`--repo-root` は別 repo の policy / pin を読んで
  未計測の repository を clone しうる。runbook は入力上限のない経路を
  `unknown` = `dispatch-required` と定める。これは既存 5 entry すべてに成立する機構の性質で、
  [T-455] の追加が新設したものではない。択は (a) 現状維持 + 分類根拠に「測定 argv 限定」を
  明記、(b) argv / env を含む admission、(c) CLI 自身に site gate と入力 cap を持たせる。
  (b)(c) は {{T:pegasus-login-procedure-blocked-family}} と同じ面なので同時に裁定してよい
- {{T:guard-bash-module-borrow-family}} **P3・新規 (ユーザー裁定待ち)**:
  `python3 -m <他 module> <sanctioned path>` が sanctioned 判定を借用する。実測:
  `python3 -mpytest tools/pegasus/submit_certify.sh` は **[T-455] の追加前から** rc=0 で通る。
  借用抑止 `_provenance_script_borrow` は `check_ai_provenance.py` の basename にしか効かない。
  非 sanctioned path (`exec_calibrate.py`) では rc=2 で借用できないので、穴は sanctioned 集合の
  大きさに比例する。族修正は `python3 -m py_compile tools/pegasus/...` の過剰拒否リスクを伴うため
  設計裁定が要る。P3 とするのは、hook が原理的に閉じられない経路 (script file 越し・
  `python3 -c`・Codex 子・ユーザー端末) が D103 / D105 で既に明示されており、
  この借用だけを閉じても防壁の実効射程が大きく変わらないため
