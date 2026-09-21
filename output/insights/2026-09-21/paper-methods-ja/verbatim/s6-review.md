VERDICT: GO

[should-fix] 2026-09-21/paper-methods-ja/methods.md:76-77 (同型の箇所: :91) — 本文は「この投入は CCBench pin の前進後の main から新しい campaign ID で行われ」と書く。これは superproject についてだけ真である。実際には CCBench を driver の PIN `511c9538` へ checkout して build しており (候補の `ccbench_commit` = `511c9538`、gitlink は `e9e477ca` のまま。D1777 の手順)、pin 前進段落の「新しい pin の main からそれらを再開・再投入するには…ドライバの pin…の整合が要る」と :91 の括弧書きが並ぶと、pair が新 pin の source で走り、driver の pin の整合も済んでいたと読める / 根拠: output/insights/2026-09-20/t2795-k2-pair-attempt/README.md §1 l.45-46 と「候補 admission」行 l.56、docs/archive/worklog-phase3-0920-1754.md l.10、orchestrator/campaign/p3_s4_loop.py:116 (`PIN = "511c9538…"`、36fb14a3d で不変)、worklog-phase3-0921-1790.md l.5 (「D1777 の手順 (gitlink を変えず submodule だけ系列の PIN へ checkout) では通る」) / 直し方: :76-77 を「この投入は pin 前進後の superproject (submit-tree `6a3e15809`) から、CCBench を driver の PIN `511c9538` へ checkout する手順 (D1777。gitlink は `e9e477ca` のまま) で行った。campaign ID は admission policy epoch の移動により新しくなり、前進前の巡の campaign を再開したものではない」とする。:91 の括弧も「前進後の superproject から driver の旧 PIN を checkout して、新しい campaign として投入された」に揃える。

[should-fix] 2026-09-21/paper-methods-ja/methods.md:162-164, :173-174 — bench 失敗の規則が本走段の段落にしか無く、校正段は「その extime 以上を打ち切る」だけである。pass の定義 (:186) は本走 24 枠しか見ないため、配置どおりに読むと「校正で bench が失敗しても本走 24 枠が揃えば pass」という緩い読みが成り立つ。一次資料は、bench 失敗は校正・本走を問わず pass を妨げ、校正で出れば本走を投入しない、と固定している / 根拠: docs/decisions.md D2190 項 3 (b) (l.69501〜)、docs/paper-story/results/2026-09-21-b8-final-candidate-longrun-verify.md §2 項 4 (l.99)、docs/b8-final-candidate-longrun-verify-preregistration.md §5 (l.327-329) / 直し方: 校正段に「bench の失敗は校正・本走を問わず pass を妨げ、校正で出れば本走を投入しない (§5、D2190 項 3 (b))」を 1 文足す。本走段の「bench の失敗が 1 件でもあれば pass にならない」には「(校正・本走を問わない)」を添える。

[should-fix] 2026-09-21/paper-methods-ja/methods.md:198 — 実施結果 (判定集合 30 枠と 3 値判定 `pass`) の出所を「(D2202、worklog entry 1791)」としている。D2202 の本文は「3 値判定まで実施した」と手順を書くだけで、判定値 `pass` を含まない。依頼の出所規則 (完走・件数・日時は実施記録、D は認可と手順) からも外れる / 根拠: docs/decisions.md D2202 (l.70248〜) の決定文に `pass` が無い。verbatim/request.md l.7-9。結果稿 §3.3、output/insights/2026-09-21/t2807-b8-effective/README.md §5 / 直し方: 「(結果稿 §3、発効記録 §3〜§5、worklog entry 1791。実施手順は D2202)」へ置き換える。

[should-fix] 2026-09-21/paper-methods-ja/implementation.md:210 — 継承節の「段 6 の独立レビュー (read-only、[README](README.md) §5) の must-fix 4 件…」は前稿 dir から複製した文である。新 dir では新 README を指すが、新 README の §5 は「限界」で、must-fix 4 件の表は無い。リンク自体は解決するので、親の相対リンク検査では捕まらない / 根拠: output/insights/2026-09-20/paper-methods-ja/README.md §5 (l.86〜、must-fix 4 / should 3 の表)、output/insights/2026-09-21/paper-methods-ja/README.md l.69 (§5 = 限界) / 直し方: `[前稿 README](../../2026-09-20/paper-methods-ja/README.md) §5` へ張り替える。

[nit] 2026-09-21/paper-methods-ja/methods.md:127-128 — 「対象、…を結果を見る前に固定した (D2175)」とあるが、D2175 と事前登録 v1 が固定したのは「対象の 2 案と推奨 (案 A)」で、択一は D2186 項 1 である。次文で D2186 項 1 に触れているので偽ではない / 根拠: D2175 の表題と第 1 bullet、事前登録 §2 / 直し方: 「対象の 2 案 (推奨は案 A)」とする。

[nit] 2026-09-21/paper-methods-ja/methods.md:142-143 — 「承認の記録 (決定、…、校正 walltime、判定器の強制停止時間など)」とあるが、校正 walltime と hard timeout は承認の記録ではなく `effective` 節の値である。D2202 項 1 が挙げる「D 番号を振った fold」も抜けている / 根拠: D2202 項 1 (l.70253〜)、発効束 JSON の `effective` (`decision_numbering_fold_commit`、`verifier_hard_timeout_s`) / 直し方: 「`effective` 節 (承認の記録 = 決定・承認日・承認の対象・記録 commit・D 番号を振った fold、draft の出所と sha256、校正 walltime、判定器の強制停止時間)」とする。

[nit] 2026-09-21/paper-methods-ja/methods.md:152-154, :188 — 「集計は受理する sha256 を各 1 値で明示して照合する」が段落末の D2190 項 2 に帰属しているが、D2190 項 2 は「許可集合で照合」と書くだけで、「各 1 値」は D2202 項 2 と発効記録 §1.1 にある。また D2190 項 3 (c) の「sha 不一致・判定集合外 record の混入は pass を妨げ未確定」が、未確定の列挙 (:188) に無い / 直し方: 「(D2202 項 2)」を足し、未確定の括弧に「sha 不一致、判定集合外 record の混入」を足す。

[nit] 2026-09-21/paper-methods-ja/methods.md:81-82 と 2026-09-21/paper-methods-ja/implementation.md:128 — 結合検査は build / trace / bench / attestation 観測 / condition gate / patch 適用 / checkout / SourceEvidence / perf preflight を stub にしている。「評価する経路が、結合検査で通る」は、実 build・bench を含むと読める余地がある / 根拠: D2205 の再訪条件、output/insights/2026-09-21/t2795-pair-repair/README.md §0「主張しない」1 / 直し方: 「(build・trace・bench・checkout 等は stub。実 compiler による STOCK 成立は未測定)」を添える。

[nit] 2026-09-21/paper-methods-ja/methods.md:195-199 — 事前登録 §13 は、校正の未完走件数と規約不適合件数を数値主張に必ず添えると定める。本段は判定集合・extime・反復・workload・再検証 0 回は書いているが、規約不適合と bench 失敗の件数 (0) が無い / 根拠: 事前登録 §13 (l.531〜)、結果稿 §3.3 の表 / 直し方: 「校正の未完走・bench 失敗・規約不適合はいずれも 0 件」を足す。

[nit] 2026-09-21/paper-methods-ja/methods.md:186-187 — 事前登録 §6.1 項 2 の「校正の未完走 (indeterminate) は pass を妨げないが、件数と保全先を必ず開示する」が無い。規則を緩めてはいないが、pass との関係が規則として欠けている / 根拠: 事前登録 §6.1 項 2 / 直し方: 項 2 に 1 句足す。

[nit] 2026-09-21/paper-methods-ja/methods.md:76 と 2026-09-21/paper-methods-ja/implementation.md:142 — 実施事実 (13339 の 1 job・certified・ClaimError、校正・本走・判定の完了) の出所として、methods は D2187 だけを挙げ、implementation は D2202 を先頭に置いている / 根拠: request.md l.7-9 (出所は一次資料) / 直し方: methods:76 に「entry 1754、pair-attempt insight §1」を足す。implementation:142 は「結果稿 §3・発効記録 §3〜§5、entry 1791 (手順は D2202)」の順にする。

[nit] 2026-09-21/paper-methods-ja/README.md:58-67 — §3 の表に載っていない書換えがある。implementation の l.3-12 (「現行 main」→「照合した main」)、l.25-26・l.30 (「本稿の基準」→「前稿の基準」、出所を制限する 1 文)、l.39-49 (正本 3 bullet)、l.51-54・l.83 (表見出し)、l.154 (「と修復」)、l.173-182 (揃えた着地の段落と「飛躍しない」の拡張)、l.184-200 (確認点節) である。§2 項 3 が概括しているので偽ではないが、「型」判定の網羅性が落ちる / 直し方: 表に「implementation 冒頭・正本・表見出し・境界節末 | (P1) 型の表記修正 / 追加」の 1〜2 行を足す。

[nit] 2026-09-21/paper-methods-ja/methods.md:141-144 — 発効束 JSON の作り方 (draft 値不変・status 置換・承認情報の追加・自己参照禁止) は実装メモの B-8 行と重複し、論文の方法節としては手順の細目である / 直し方: 1 文へ圧縮して詳細は implementation へ寄せる。:157-158 (runner が status を見ない) は限定文なので削らない。

[refuted] 判定集合 30 枠を「独立 8 反復 × 3 workload・extime 10 s」へ丸ごと帰属させる文 — 3 file と phase3 の新項を全数 grep した。methods:197-198、implementation:92・123・190-191、phase3 l.23-24 はいずれも「本走 24 枠 (条件) + 校正の完走 6 枠」の形だった。
[refuted] 校正の運用上 indeterminate と、判定器が完走して返す indeterminate verdict の混同 — methods:163 と :184 (D2190 項 3 (a))、implementation:192-193 で区別されている。
[refuted] 適格条件 8 項・打ち切り条件・共通部分の最大値と丸め禁止・予算 14,400 s と段下げ・反復削減の禁止・§12 の記録時点の誤写 — 事前登録 §4.2 / §7 / §12、D2175、D2190 項 1 と一致した。
[refuted] 3 値の評価順と各条件 — §6.1、D2190 項 3 (c)(e) と一致した。失格は再実行しない、未確定を pass に丸めない、pass ≠ 研究成功 (D12)、の各文も保たれている。
[refuted] 本走未完走の 2 分岐と、anomaly 枠の再検証禁止 — D2202 項 3、結果稿 §2 項 5 と一致した。
[refuted] hard timeout の 3 値 — D2190 項 4 と発効束 JSON の `effective.verifier_hard_timeout_s` (3600 / 1800 / 3600) に一致した。
[refuted] 発効束 JSON — schema `b8-effective-bundle/v1`、status `effective` を実 file で確認し、sha256 `059536a7…807c1b` を再計算して一致した。事前登録 `6ccb18c7…` と patch `31316713…` も再計算で一致した。
[refuted] runner v5 の所在 (repo 外の job dir)・2103 行・sha256 `4ff6652a…`・D95 — 発効記録 §1 の表、D2190 項 1 と一致した。
[refuted] 束縛の掛け方 — 発効 commit の固定 checkout、tracked path の `--bundle`、投入直前の照合、accept sha を各 1 値で渡すことは D2202 項 2 と発効記録 §1.1 / §3 に一致した。「1 job に 1 本の木」は発効記録の 6 本 (校正の 3 本を本走で再利用) と数が違って見えるが、D2202 項 2 の規則 (並行する job は木を共有しない) の写しなので偽ではない。
[refuted] request・日時・件数 — 14640〜14642 / 14686〜14691、08:45〜09:11 / 09:17〜10:13、各 job 4 反復、発効 commit 624c84986 (git で 2026-09-21 08:42:12)、D2194 項 1 のいずれも、結果稿 §3・発効記録 §3〜§5・git と一致した。
[refuted] 一次資料に無い強い主張の追加 (serializable の証明、乱数列の独立性、同一 binary、S-1 (iv) の充足、検証相との比較、「取得」) — methods:203-210 と implementation:123・181-182 はすべて否定形で書かれ、結果稿 §4 の 11 項と整合した。性能値の転載も無い。
[refuted] 規律 2 系の文の弱化 — 校正で anomaly が出たら即失格・本走不投入、再検証しない、pass に丸めない、の各文は一次資料より弱くない。弱いのは bench 失敗の配置だけで、上の should-fix に挙げた。
[refuted] K2 で D2187 と D2205 を混ぜる、または修復の緑を対照の成立と読ませる文 — methods:73-83 は 2 段落に分かれ、implementation:95・127-128・179-180 も別の行・否定形である。
[refuted] 「前進前の巡の campaign を再開したものではない」に根拠が無い — pair-attempt insight §0 の主張 1 と §1 の表 (campaign `…b24749ae` = 新 ID・新 policy epoch・新規 WAL、round 3 は `409e13f8`) に根拠がある。
[refuted] pair mode の実装アンカーの不一致 — loop.py:103 `_AuthorizationSession`、:129 `authorization_session()`、:327-342 と :522-537 の keyword-only `authorization_session`、p3_s4_loop.py:2019-2032 (`authorization_session=None`)、:3205-3248 (pair_mode = run_iteration ∧ stock_control、`--isolate-worktree` 必須、stock 単独は従来どおり)、p3_s4_loop_pegasus.sh l.147-156 (`=1` は `IZANAGI_S4_PROPOSAL_PATH` を要求し、`--stock-control` を 1 起動へ足す) で、いずれも本文と一致した。campaign_claim.py の sha256 `2e9c0932…` も不変だった。
[refuted] 「本稿の採用時点で pair の再投入なし」「B-5 の本走は未認可」 — D2206〜D2210 と entry 1792〜1808 (worklog.md の 1804〜1808 を含む) に反例は無い。entry 1807 l.2028 は「B-5 本走は未認可のまま」、D2206 の索引外節は「項 1 (B-5 の発効束の完成) は AI 手番で進行中」と書いている。
[refuted] B-5 の過大記述 — 未発効 (B-5 事前登録 §0)、試走 4 job・53 論理 session・主標本外 (entry 1779、D2172 項 4 (β) の上限 60 以内)、D2200 項 1 は段階認可、のいずれも一次資料と一致した。driver と共有部品の着地は D2172 項 4 (α) の範囲で、それを越える記述は無い。
[refuted] README §3 の「型」と commit・時刻 — git で確かめた。482f19b88 (09-20 17:56) は 6a3e15809 (19:03) の祖先で、D2187 の初出 fold は 7baf3f375 (20:42)、D2190 の初出 fold は 7c0a1c63a (22:54)、b5_generator_contrast.py の追加 c41cfb09f (20:34) は 482f19b88 の祖先ではない。runner について「実装されていない」も、D2186 (提示時点の main = 482f19b88) が runner の改版を認可した順序から真である。
[refuted] 前稿 bytes の変更 — `git diff 36fb14a3d HEAD` の変更は前稿 README・新規 file・phase3 だけで、前稿 methods / implementation は不変だった。
[refuted] (P1) による誤読と継承文の偽化 — 冒頭の太字と implementation:173-176 が継承範囲を明示している。A-1 attempt-0002 (entry 1755) を本文に書かず README §5 で開示したのは scope 判断として整合し、「その後は再照合していない」は偽ではない。methods:113 の「現行 policy は 5 node」や :259 の床値 w1 などの現在形の継承文も、36fb14a3d で偽になった例は見つからなかった (pin は e9e477ca のまま、w2 は未走)。
[refuted] (P2)・(P3) より小さい変更で足りる — §6 の B-8 は §3 を指す 1 文だけで 6 節構成は保たれており、(P3) の変更も括弧書き 1 つで最小である。ただし (P3) の中身の精度は should-fix 1 のとおり。
[refuted] 論文ストーリーの版や entry 1801 を三つの対象の出所にしている — そうした文は無く、implementation:26・43-44 で明示的に除外している。
[refuted] 仮想リスク向けの gate・検査・台帳・一般化の追加 — 無い。「本稿で足した確認点」は記録であって gate ではない。
[refuted] 前稿 README の前方 pointer と phase3 の [x] 項の誤り — 事実・件数とも一次資料と一致した。

照合した資料: 決定は D2158 (冒頭)、D2172 項 3・4、D2175 (冒頭)、D2183 (表題)、D2186 (窓と収集・項 1)、D2187 (全文)、D2190 (全文)、D2194 (窓と収集・項 1・項 2)、D2200 (窓と収集・項 1)、D2202 (全文)、D2205 (全文)、D2206 (窓と収集・索引外節)、D2207〜D2210 (B-5 / K2 / 発効に関する記述の grep、D2209 の本文要所)。worklog entry は 1746・1749・1754・1755・1779・1790・1791・1795・1801 の先頭 20 行、1792〜1803 の表題、worklog.md の 1804〜1808 の表題と 1807 の本文、を読んだ。一次資料は、B-8 結果稿 (全文)、t2807-b8-effective README (全文)、B-8 事前登録 v1 の §0・§1・§3・§4・§5・§6・§7・§8・§9・§12〜§14、B-5 事前登録 §0、t2795-k2-pair-attempt README §0〜§2、t2795-pair-repair README §0〜§4、発効束 JSON (schema・status・effective 節)、前稿 methods / implementation (新稿との diff) と前稿 README (前方 pointer・§5)、docs/phase3.md 先頭 30 行、コード (orchestrator/campaign/loop.py の authorization session 周辺、p3_s4_loop.py の `_run_stock_control_resolved`・`main` の pair_mode 分岐・`PIN`、tools/pegasus/p3_s4_loop_pegasus.sh の `IZANAGI_S4_STOCK_CONTROL`) を読んだ。git は read-only の log / merge-base / ls-tree / diff だけを使い、sha256 は発効束・事前登録・patch・campaign_claim.py・前稿 2 file について再計算した。所見の file 名は、どれも W/output/insights/ 以下の path である。

### Critical Files for Implementation
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-b8/output/insights/2026-09-21/paper-methods-ja/methods.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-b8/output/insights/2026-09-21/paper-methods-ja/implementation.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-b8/output/insights/2026-09-21/paper-methods-ja/README.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-b8/output/insights/2026-09-20/t2795-k2-pair-attempt/README.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-methods-ja-b8/docs/decisions.md (D2190 項 3 (b)、D2202)
