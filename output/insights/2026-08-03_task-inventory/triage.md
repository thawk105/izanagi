# 次の一手 293 件の棚卸し — 逐語の裁定表 (2026-08-03)

worklog エントリ (139) の「次の一手」293 件を 1 件ずつ裁定した記録。
`出所` は各 ID の**最終実体テキスト**が書かれたエントリ番号で、
`変わらず` / `同上` を遡って解決した結果である (抽出は機械、裁定は親)。

方針:

- **完了**: 記録自身が完了・解消・閉鎖・却下を宣言しており、以後に再開の記録が無いもの。
  実装の実在を疑う余地があるものは実測してから落とした。
- **見送り**: 実施しないと裁定済み、発火条件つきで未成立、または別 ID が所有すると
  **記録に書かれている**もの。`docs/phase3.md` の見送り台帳へ理由つきで移した。
- **継続**: 上記に当たらないもの。とくに「裁定済み → 実装待ち」は
  ユーザーが実施を決めた作業なので落としていない。

内訳: 完了 65 / 見送り 46 / 継続 189。

## 完了として落とした項目

| ID | 出所 | 最終実体テキスト (先頭 150 字) | 落とした根拠 |
| --- | --- | --- | --- |
| T-243 | (113) | **完了 (本エントリ)**: 6 driver の新規 campaign と 8c journal を exploration namespace へ 前向きに移し、hooks と marker を追随させた (D123)。歴史成果物は不動。残余は [T-318]〜[T-323] へ分離した | (113) で完了と記録済み。残余は [T-318]〜[T-323] へ分離済み |
| T-276 | (145) | **完了 (D122) + 運用・設計の束縛を追加**: ユーザー裁定 = 分割線を維持する。 計算ノードでの role 実行は行わず、LLM は login、build / verify / bench だけ dispatch する。 壁 1 の恒久実装はこの分割線を前提に設計する。**D122  | (113) で完了と記録済み (D122)。(145) の追加裁定で分割線が確定し、opt-in 経路の撤去は [T-390] が所有する |
| T-291 | (108) | **完了 (本エントリ)**: 機械化 (D119) と予算再校正で closure。残余は下記 4 件へ分割した | (108) で完了と記録済み (D119)。残余は 4 件へ分割済み |
| T-297 | (103) | **P3・新規 (本エントリ)**: 見送り台帳 [T-059] (差分 mutation 標準化) の**発火記録が 3 wave ぶん欠けている** — (98) [T-247] の予約 envelope 拒否、(99) [T-244] の generation 予算 + freshness v | 本 wave の見送り追記で [T-059] へ 3 wave 分の発火記録を書き戻し、欠落を解消した |
| T-288 | (106) | **消化 (本エントリ)**: 択 (a) を実装。単位換算を role-facing 射影 1 箇所へ閉じ、 recipient matrix を D118 で追認。(b) 移行は多世代開放の前提条件として D118 決定 (6) に記録 | (106) で消化と記録済み (D118) |
| T-247 | (98) | **完了 ((98))**: 恒真な予約 envelope 検査を実発火させ、個別 cap を個別値 + 型で凍結した。 射程は実消費層 (`validate_protocol`) まで広げた (D113)。変異 35/35 全 kill、全走 4747 passed。 **射程拡張は裁定文の li | (98) で完了と記録済み (D113、変異 35/35 kill) |
| T-277 | (117) | **P2・消化 (本エントリ)**: ユーザー裁定 (a) の 4 項目のうち受理集合・env 契約解決・build identity・attestation/no-resume を実装した (D125)。`/scr` と `single_process` 強制は [T-330] へ、兄弟 driv | (117) で消化と記録済み (D125)。残余は [T-330] / [T-331] へ分離済み |
| T-209 | (92) | **完了 (本エントリ)**: 第 1 節 (凍結解除条件を「[T-088] の実行」→「[T-193] の閉鎖」へ 付替え) は 2026-07-31 の `/rulings` commit `27b2813` で phase3 へ既着地だったため再実装しなかった。 第 2 節は、記録直前のユーザ | (92) で完了と記録済み (D111 = プロセス系 freeze 廃止) |
| T-193 | (92) | **閉鎖 (本エントリ、ユーザー裁定)**: (80) の「main を正本にする」裁定の執行をもって 閉鎖とした。`tools/pegasus/dispatch_compute.py` が正本であり、`dev-wave-improve` の 3 ファイルは main に存在しない (branch  | (92) でユーザー裁定により閉鎖済み。残務は [T-222] へ分離済み |
| T-140 | (92) | **完了済み ((29)) を本エントリで再確認**: 「変異軸をデータ構造水準へ」は 2026-07-28 に 実測済みで、択 (c) (軸の廃止) が適用されている (走査長は平均 5 / 上限 10 で重尾機序が構造的に無い)。 **再開条件は `max_ope` の大きい workload  | (29) 完了・(92) 再確認。記録は新規起票を明示的に禁じている |
| T-225 | (130) | **P1・裁定を改訂 → 一致済み**: (90) の「`effortLevel` を `high` へ戻す」を撤回し、 **`xhigh` を承認値とする**。2026-08-03 にユーザーが `/effort xhigh` を既定保存した判断による。 承認値と現物は一致しており、追加の適用作業 | (130) で承認値と現物が一致済みと確認され、適用作業は無いと記録済み |
| T-260 | (89) | 解消済み (本エントリで実装・land) | (89) で解消と記録済み |
| T-220 | (88) | **完了 (本エントリ、D108)**: land の control-plane を衝突軸へ一本化し、handoff 書式の阻害力を意図的にゼロへ降格した。裁定済み択 (a) の実装 | (88) で完了と記録済み (D108) |
| T-207 | (86) | **完了 (本エントリ)**: `codex/p3-autonomous-trial` の 5 ファイルを監査・訂正のうえ | (86) で完了と記録済み |
| T-229 | (82) | **本エントリで解消**: conftest の `/dev/shm` 誘導を撤去し、tmpfs 消費を 7.39 GiB → 0 にした。回帰ガード 5 node つきで land 済み | (82) で解消と記録済み (tmpfs 消費 7.39 GiB → 0、回帰ガード付き) |
| T-194 | (79) | 解消済み ((78) で実装・land 済み) | (78) で解消と記録済み |
| T-200 | (73) | **完了 (本エントリ、D104、実装差分なし)**: 受入全走の下限は in-scope のテスト側施策では 動かないと 4 走の実測で確定し、共有 cache 1909 行を破棄した。真の律速は base 構築 90 秒のうち 約 80 秒を占める本番 `_history_touches_pat | (73) で完了と記録済み (D104、実装差分なし) |
| T-205 | (77) | **完了 (本エントリ、D105、local main へ land 済み)**: Pegasus の provenance 履歴監査を計算ノードへ移し、 `_audit_history` を site 由来の並列度 (上限 32) の thread pool + 祖先 bitset にした。 あわ | (77) で完了と記録済み (D105、local main へ land 済み) |
| T-206 | (76) | **本 wave で解消 ((75))**: land の control-plane 検査が無関係な実体で止まる件を、 危険な名前と実衝突だけの拒否へ是正し回帰を追加した | (75) で解消と記録済み |
| T-192 | (73) | **完了 ((72)、D103)** | (72) で完了と記録済み (D103) |
| T-195 | (78) | **P2・裁定済み ((74))・追加実装なしで充足**: build 並列度は環境任せ。`-j 16` と `-j 48` の バイナリは izanagi として同一扱いとの裁定により manifest schema 変更は不要。campaign driver は 既に `site_policy. | (74) の裁定により追加実装なしで充足すると記録済み |
| T-191 | (73) | **完了 (本エントリ、実装 `b5f0460`、記録 `d80ab4b`)** | (73) で完了と記録済み (実装 b5f0460 / 記録 d80ab4b) |
| T-188 | (73) | **完了 ((67)、D102、F55)** | (67) で完了と記録済み (D102、F55) |
| T-187 | (73) | **完了 ((66)、D101)** | (66) で完了と記録済み (D101) |
| T-180 | (73) | **完了 ((65)、`24d2672` + `de0a9ad` + rewrite `677c32a`)**: job 単位の resource envelope と fail-closed receipt を `tools/codex_worker_launch.py` として正本化。wave  | (65) で完了と記録済み。残余は [T-183] / [T-184] / [T-186] へ分離済み |
| T-182 | (73) | **完了 ((68)、実装差分なし)**: 段 3 レンズ B を同一凍結入力で sol / luna / mini の 3 arm へ投入し、被覆・誤検出・token/wall と receipt を凍結した。専用ツールは独立 3 レンズの NO-GO を受けて実装しない裁定 | (68) で完了と記録済み (実装差分なし)。設計は [T-189] へ分離済み |
| T-179 | (73) | **完了 ((64)、`72f8858`)** | (64) で完了と記録済み (72f8858) |
| T-149 | (39) | **完了 (2026-07-29 (39))**: 編集面 hard-code は literal 正本 + 機械検査テスト 7 本で 封鎖。導出化は 3 経路で棄却 (詳細 = insight)。coder.md の stale 列挙は正本ポインタへ訂正 (review_ledger closur | (39) で完了と記録済み |
| T-152 | (50) | **実装・実証完了 (本エントリ、afa7325)**: certified pipeline での有効化は [T-167] の pin bump 裁定待ち (それまで dormant — insight に明記) | (50) で実装・実証完了と記録済み。certified pipeline での有効化は [T-167] の pin bump 裁定が所有 |
| T-153 | (73) | **完了 ((60))** | (60) で完了と記録済み |
| T-158 | (50) | **完了 (2026-07-29 (47))**: submodule 実体検査 + cache 限定自動 init (D97) | (47) で完了と記録済み (D97) |
| T-141 | (50) | **完了 (2026-07-29 (49))**: CLI 化・運用配線・閾値校正 (据え置き裁定) で残 3 点を消化 | (49) で完了と記録済み |
| T-143 | (73) | **完了 ((63)、D99)** | (63) で完了と記録済み (D99) |
| T-145 | (73) | **完了 ((70)、`64ddf5c` + merge `d5825c5`)** | (70) で完了と記録済み |
| T-146 | (73) | **完了 ((69))** | (69) で完了と記録済み |
| T-110 | (46) | **完了 (2026-07-29 (46))**: D96 として規約化 (本エントリ) | (46) で完了と記録済み (D96 として規約化) |
| T-154 | (73) | **完了 ((60))** | (60) で完了と記録済み |
| T-157 | (36) | **完了 (2026-07-28 (34))**: 重複提案の解決を summary 確定済み id へ置き換え、3 driver を 単一実装化。変異 5/5 KILLED、受入全走緑。遡及救済は [T-159] へ分離 | (34) で完了と記録済み。遡及救済は [T-159] へ分離済み |
| T-148 | (36) | **完了 (2026-07-28 (32))**: digest 環境を実 TU の写しにし、未知文脈と computed include を fails-closed 化。D93。insight §5 の critic digest 記述は (34) で訂正。変わらず | (32) で完了と記録済み (D93) |
| T-155 | (33) | **完了 (2026-07-28 (30))**: n\* crossover を実測 — 反転帯 80〜98 (build)、 hit 経路は 2〜5、compact 側索引 32。休眠裁定の定量裏付け。変わらず | (30) で完了と記録済み |
| T-147 | (28) | **完了 (2026-07-28 (28))**: 予算内再配分 + 受け皿 + C00 再評価義務。本エントリ | (28) で完了と記録済み |
| T-127 | (28) | **完了 (2026-07-28 (28))**: byte 予算の使い方管理 — 裁定済み方針を [T-147] で実行、 削除候補監査済み (O07 のみ、裁定は [T-154] (1)) | (28) で完了と記録済み (byte 予算の使い方管理) |
| T-137 | (26) | **完了 (2026-07-27 (26))**: serve thread の偽緑。生存 assertion + serve 例外の主スレッド 回収で塞いだ。**非 daemon 化は M-D の実測で撤回** | (26) で完了と記録済み |
| T-138 | (26) | **完了 (2026-07-27 (26))**: 恒真ゲート。capability probe を本番と同じ basename・同じ syscall 列の生 AF_UNIX へ置き換え、両方向を固定する正例テストを新設した | (26) で完了と記録済み |
| T-132 | (24) | **完了 (本エントリ)**: group 分割。1 file 1 group を外し runtime 資源を掴む 8 node だけを直列に残した。全走 wall 71.7 → 60.8 秒 (−15%)。D91 決定 (2) を D92 で上書き | (24) で完了と記録済み (D92) |
| T-128 | (21) | **完了 (本エントリ) = scope を差し替えて達成**。名指しの node は律速でなく、 真因は fixture の scan 膨張だった。fixture 構築 121.72 → 22.13 秒 (同一 source 比較) | (21) で完了と記録済み |
| T-120 | (36) | **完了 (2026-07-27 (20)) だが (24) で結論を上書き**: group 分割の棄却は `-n 16` 限定。変わらず | (20) で完了と記録済み。結論は (24) が上書き済み |
| T-125 | (19) | **完了 (本エントリ)**: `seq-stop-spec` の取り込み漏れを価値判断のうえ救出し、 local main へ取り込んだうえで対象 worktree 2 件を畳んだ (ユーザー裁定 4 点すべて実行)。 `origin/main` への push もユーザー指示で実行済み (df2 | (19) で完了と記録済み |
| T-116 | (14) | **完了 (本エントリ)**: 本番 git 畳み込みを実施。25.0 秒 → 9.1 秒・byte 同一 | (14) で完了と記録済み |
| T-057 | (16) | **完了 (2026-07-26 (13)(14) + 2026-07-27 (15))**: 全走 69 秒。台帳行も裁定済みへ更新 | (13)(14)(15) で完了と記録済み。以後の所有は [T-201]、見送り台帳にも記録済み |
| T-117 | (16) | **完了 (2026-07-27 (15))**: 律速の内訳を実測し gate 解決の重複を畳んだ。残りは [T-119] / [T-120] / [T-121] / [T-122] へ分割済み | (15) で完了と記録済み。残りは [T-119]〜[T-122] へ分割済み |
| T-119 | (17) | **完了 (本エントリ)**: SIGSTOP/SIGCONT 競合を塞いだ。全走 flake は 4 走連続 0 件 | (17) で完了と記録済み |
| T-105 | (17) | **完了 (本エントリ)**: `_run_artifact_bytes` の `FileNotFoundError` 素通しを塞いだ | (17) で完了と記録済み |
| T-104 | (18) | **完了 (本エントリ)**: reference 再編。予算値を上げずに余裕 81 bytes を作った | (18) で完了と記録済み |
| T-101 | (18) | **完了 (本エントリ)**: 作法 2 件を `DW-O20` / `DW-O16` へ入れた | (18) で完了と記録済み |
| T-124 | (18) | **完了 (本エントリ)**: ユーザー裁定 (b) どおり、再編で場所を作って 3 件を入れた | (18) で完了と記録済み |
| T-108 | (18) | **完了 (本エントリ)**: 作法 2 件を `DW-O18` / `DW-M01` へ入れた | (18) で完了と記録済み |
| T-111 | (36) | **完了 (2026-07-27 (18))**: 作法 2 件を `DW-S01`+`DW-O19` / `DW-S03` へ入れた。変わらず | (18) で完了と記録済み |
| T-162 | (45) | **完了 (2026-07-29、commit 166dd6f)**: 裁定 = 採用を記録 (本エントリ)。台帳同期は (43) 済み | (45) で完了と記録済み (166dd6f) |
| T-165 | (41) | **完了 (2026-07-29 (41))**: dev-wave の実装面を Codex author 必須にし、 軽量版・親直接 edit/fix・review 代替を command/reference/checker/test の各面で封鎖 (D95) | (41) で完了と記録済み (D95) |
| T-171 | (73) | **完了 ((60))** | (60) で完了と記録済み (Codex dev-wave Skill と drift 検査) |
| T-172 | (73) | **完了 ((60))** | (60) で完了と記録済み (Codex rulings Skill と drift 検査) |
| T-173 | (73) | **P3 ((60))** | [T-205] (D105) の実装で達成済み — 祖先 bitset は `tools/check_ai_provenance.py:715-798`、thread pool は同 `833-853` を読んで静的に確認した (計測記録の正本は [T-205] の worklog (77)) |
| T-221 | (80) | **完了 (本エントリ)**: R5 closure と T-193 決着。実装は `codex/dev-wave-improve` (tip `77db32c`) に保存し land しない | (80) で完了と記録済み (R5 closure と [T-193] 決着) |
| T-356 | (125) | **P3・裁定済み → 実装待ち**: 重複 12 件を一覧化して 1 回で仕分ける小作業を立てる。 active / 見送りの一括採用はしない | 本 wave が重複 12 件を仕分けて消化した (下記 4 件を終端、8 件を active として維持) |

## 見送り台帳へ移した項目

| ID | 出所 | 最終実体テキスト (先頭 150 字) | 見送りの理由 (category つき) |
| --- | --- | --- | --- |
| T-326 | (124) | **P2・裁定済み → 記録に留める**: 択 (b) 採用 — 新 verifier 経由の強化のみとし、 `layer3_report` 本体の深い一致強化は独立 wave へ送る。既存レポートが値の改変を受理する事実は 所見として残す | `layer3_report` 本体の深い一致強化 — 理由: (124) の裁定 (b) により**実施しない**。強化は新 verifier 経由だけとし、既存レポートが値の改変を受理する事実は所見として記録に残す。本体側へ着手するには択 (a) の再裁定が要る  〔正しさ・防壁系〕 |
| T-323 | (113) | **P3・新規 (本エントリ)**: 8c の raw role 出力 (`raw/raw_*.txt`) を追跡するかの方針。 D123 決定 (8) は「exploration campaign は official と同じく tracked」までしか決めておらず、 生 role 出力の耐久性は | 8c の raw role 出力を追跡するかの方針 — 理由: [T-241] の裁定事項として記録済みで、単独では起票しない  〔正しさ・防壁系〕 |
| T-314 | (130) | **P3・裁定を改訂 → [T-294] の補助へ降格**: 2026-08-03 の裁定 (目印を 1 語へ正規化し 機械検査) は [T-294] の既裁定と逆方向だった。**目印の正規化は人間可読性のための補助**とし、 検出の主経路にしない。`check_docs.py` での機械検査は [ | 裁定待ちの目印の正規化 — 理由: (130) の再裁定で [T-294] の補助へ降格し、機械検査に持つかは実装 wave が決める  〔プロセス文書系〕 |
| T-302 | (105) | **P3・新規 (本エントリ)**: `dispatch_compute._job_run` が子側で `env_allowlist` を強制していない (型検査だけで `child_env.update`)。D108 が既知の 恒真保証として記録済み。**task enum 拡張を選ぶ場合の前提条 | `_job_run` が子側で env_allowlist を強制していない件 — 理由: [T-250] と同一所見の重複であり、所有を [T-250] に一本化する  〔正しさ・防壁系〕 |
| T-259 | (101) | **P3・裁定済み ((101)、現状維持)**: repo 側への除外追記はしない。別マシンで作業を始める 時点で runbook に 1 行足す運用にする | 他マシン作業時の除外設定 — 理由: (101) の裁定で repo 側へは追記せず、別マシンで作業を始める時点で runbook に 1 行足す運用と決まった  〔外部環境系〕 |
| T-228 | (101) | **P3・裁定済み ((101)) → 本番開放の前提条件へ**: effort 値域検査と receipt 側 effort 記録を D74 (6) の real 開放前ユーザー裁定へ併合する | effort 値域検査と receipt 側 effort 記録 — 理由: (101) の裁定で D74 (6) の real 開放前ユーザー裁定へ併合済み  〔プロセス文書系〕 |
| T-290 | (103) | **P3・裁定済み ((103))**: 択 (b) 維持 — `run_trial(drive=/providers=/preview=)` の注入 seam と `drive_iteration()` の直接反復は D114 どおり保証対象外のまま残し、**多世代開放と同時に (c)** (8c | `run_trial` の注入 seam の保証 — 理由: (103) の裁定 (b) で現状維持とし、多世代開放と同時に (c) を入れると決まった  〔正しさ・防壁系〕 |
| T-283 | (125) | **P2・裁定済み → 本番開放の前提条件へ**: 単独着手はせず [T-246] と同じ束へ入れる | 本番開放の前提条件 — 理由: (125) の裁定で [T-246] と同じ束へ入れ、単独では着手しないと決まった  〔正しさ・防壁系〕 |
| T-285 | (98) | **P3・新規 (本エントリ)**: 予約 block 以外の 7 個の `readarray < <(...)` も producer の 終了状態を失う。「必要行を全部出し切った後の producer failure」を受理し続ける。同型欠陥 (print が raise より前) は 1 件だ | 予約 block 以外の 7 個の `readarray < <(...)` — 理由: [T-292] と同族で、同じ独立 wave が所有する  〔正しさ・防壁系〕 |
| T-271 | (95) | **P2・新規 (本エントリ)**: closure wave (2026-07-31) の T-126 submitter 赤の原因究明。 「偽赤」「3.9 fallback」の断定は撤回し、原因不明・再現不能・追跡不能として扱う。再発を観測したら request ID・ノード・生ログを添えて起票 | closure wave の T-126 submitter 赤の原因究明 — 理由: 原因不明・再現不能・追跡不能として扱うと記録済み。再発を観測した時点で request ID・ノード・生ログを添えて新規起票する  〔テスト衛生〕 |
| T-272 | (125) | **P3・裁定済み → 実装待ち**: Pegasus shell 3 本の裸 `python3` に版数 gate を入れる。 [T-248] の実装と同じ wave に含める | Pegasus shell 3 本の裸 python3 の版数 gate — 理由: (125) の裁定で [T-248] の実装と同じ wave に含めると決まった  〔正しさ・防壁系〕 |
| T-236 | (94) | **P2・裁定済み ((94)、保留)**: 択 (b) 採用 — 実装せず設計を凍結する。分割に必要なのは transport でなく domain result 契約の新設 (D108 決定 3)。分割の必要が実際に生じた時点で再評価する | transport と domain result の分割 — 理由: (94) の裁定 (b) で実装せず設計を凍結した。分割の必要が実際に生じた時点で再評価する  〔プロセス文書系〕 |
| T-246 | (94) | **P2・裁定済み ((94)) → 本番開放の前提条件へ**: 択 (b) 採用 — T-126 scope 外の real 所見 4 件を、逐次停止を production gate へ昇格させる際の前提条件として束ねる | T-126 scope 外の real 所見 4 件 — 理由: (94) の裁定 (b) で、逐次停止を production gate へ昇格させる際の前提条件として束ねると決まった  〔正しさ・防壁系〕 |
| T-226 | (90) | **P2・裁定済み ((90)、据え置き)**: 段 2 (`DW-S02`) の `reasoning=max` は変更しない。 段 2 限定の測定が得られた時点で再評価してよい | 段 2 (`DW-S02`) の reasoning 見直し — 理由: (90) の据え置き裁定。段 2 限定の測定が得られた時点で再評価する  〔プロセス文書系〕 |
| T-253 | (88) | **P3・新規 (本エントリ、観測)**: `dev_waves` の `main-dirty` gate が共有 checkout で 恒常発火している (実測 `main_dirty=True` / 16 エントリ、すべて他 session の worktree・handoff・ `settin | `dev_waves` の main-dirty gate の恒常発火 — 理由: 実害未確認の観測にとどまる。daemon 経路の運用が始まった時点で再評価する  〔プロセス文書系〕 |
| T-242 | (103) | **P2・裁定済み ((103)) → 本番開放の前提条件へ**: 択 (c) 採用 — `claude_executable_sha256` の 記録は継続し、**成果物が主張に使われる run (正式系列) でだけ承認 hash allowlist を発火**させる。 常時 allowlist  | `claude_executable_sha256` の allowlist 発火 — 理由: (103) の裁定 (c) で正式系列でだけ発火させると決まり、[T-246] / [T-228] と同じ束に置く  〔正しさ・防壁系〕 |
| T-237 | (84) | **P3・新規 (本エントリ)**: role ごとの実所要時間を計測する。既存 8c dry-run は 12/12 valid だが role 別の所要秒を記録していない。[T-236] の role_cap 裁定はこの実測なしには決められない | role ごとの実所要時間の計測 — 理由: 目的である [T-236] の role_cap 裁定が設計凍結となったため、発火条件が成立しない  〔研究・計測系〕 |
| T-240 | (88) | **(87) で 2 例目が独立再現。`DW-G03` の独立 2 例が揃った**: (84) は「段 1 前の | 段 1 前の所在・所有確認と族横断要求の `DW-S01` 追記 — 理由: (88) の裁定で予算配分の束として [T-208] / [T-219] と扱うと決まり、単独では着手しない  〔プロセス文書系〕 |
| T-230 | (82) | **P2・新規 (本エントリ)**: 受入全走のフレーク率が本変更後に上がった可能性。 親は 2/2 緑、変更後は 2/3 で赤 (落ちる node は移動、単独再走は緑、wall 差なし)。 `DW-O18` により差分へ帰属させていないが、1 走ずつの比較では交絡しうる。 再発時は `outpu | 受入全走のフレーク率が上がった可能性 — 理由: `DW-O18` により差分へ帰属させず、再発時に insight §8 を一次資料として起票すると記録済み  〔テスト衛生〕 |
| T-210 | (76) | **P3・裁定済み ((74)、据え置き)**: git のリポジトリ整理 (`gc` / `commit-graph write`) の恒久化は優先度低。Pegasus では静穏条件を要さないとのユーザー判断で、 履歴監査の根本解決は [T-205] の高速化 (計算ノード実測 25.24 → 4 | git リポジトリ整理の恒久化 — 理由: (74) の据え置き裁定で優先度低。履歴監査の根本解決は完了済みの [T-205] が担った  〔プロセス文書系〕 |
| T-197 | (78) | **P3・裁定済み ((74)、据え置き)**: 択 (b) 採用 — sanctioned exact path 列挙のまま置く | `exec_calibrate.py` の汎用トランポリン — 理由: (74) の裁定 (b) で sanctioned exact path 列挙のまま置くと決まった  〔正しさ・防壁系〕 |
| T-198 | (78) | **P3・裁定済み ((74)、見送り)**: 択 (b) 採用 — lease / heartbeat は入れず、ジョブの 上限 wall (現行 30 分) で取り残しの被害を限定する | scheduler-side lease と heartbeat — 理由: (74) の裁定 (b) で入れないと決まり、上限 wall で被害を限定する  〔正しさ・防壁系〕 |
| T-142 | (73) | **close ((62) のユーザー再裁定)**: formal selector と live campaign が 揃った場合のみ新タスクとして再起票 | 旧 headline 候補の再起票 — 理由: (62) のユーザー再裁定で close 済み。formal selector と live campaign が揃った場合だけ新規に起票する  〔研究・計測系〕 |
| T-136 | (36) | **完了 (2026-07-28 (35))**: 受入テストの timing 依存フレークを除去。baseline 10/10 赤 → fix 40/40 緑 (paired、既知 node 照合)。残余は insight §7 (新規タスク化せず) | 受入テストの timing 依存フレーク除去の残余 — 理由: 機序自体は (35) で完了 (baseline 10/10 赤 → fix 40/40 緑)。insight §7 の残余リスク (固定短窓・無界 WAL/fsync・0.5 秒 durability 窓) は当時「新規タスク化せず」と裁定されており、再観測した時点で起票する  〔テスト衛生〕 |
| T-150 | (73) | **P3・裁定済み ((60))** | CCBench 上流への還元 — 理由: (54) の裁定で [T-167] wave へ束ね、上流 PR / push は人間が行う  〔プロセス文書系〕 |
| T-151 | (73) | **P3・裁定済み ((60))** | CCBench 上流への還元 — 理由: (54) の裁定で [T-167] wave へ束ね、上流 PR / push は人間が行う  〔プロセス文書系〕 |
| T-135 | (36) | **却下 (2026-07-28)**: T-080 E2E の key C/D を amend で導出する案 (stub-free 契約を 弱めるため不採用、規律 2)。変わらず | T-080 E2E の key C/D を amend で導出する案 — 理由: (36) で却下済み (stub-free 契約を弱めるため、規律 2)  〔テスト衛生〕 |
| T-102 | (24) | **裁定済み → [T-096] と同じ wave**: production `_run_git` 2 箇所の ambient env 継承。変わらず | production `_run_git` 2 箇所の ambient env 継承 — 理由: (24) の裁定で [T-096] と同じ wave が所有する  〔正しさ・防壁系〕 |
| T-122 | (24) | **裁定済み → 測定後 ([T-011] の後)**: `verify_receipt` の `search_repository` 重複。変わらず | `verify_receipt` の `search_repository` 重複 — 理由: (24) の裁定で [T-011] の測定後に着手すると決まった  〔正しさ・防壁系〕 |
| T-103 | (12) | **裁定済み → 1 cycle 後**: never-issued 検査は先送り | never-issued 検査 — 理由: (12) の裁定で 1 cycle 後へ先送りと決まった  〔正しさ・防壁系〕 |
| T-089 | (7) | **測定後の hardening と裁定** (前倒し対象外): 二重 reason-tag 描画。修正時に exact 期待値を 同時更新する | 二重 reason-tag 描画 — 理由: (7) の裁定で測定後の hardening と決まり、前倒し対象外である  〔正しさ・防壁系〕 |
| T-090 | (11) | **測定後の hardening と裁定 (real 確認済み)**: `VerifiedFreeze.document` が mutable。変わらず | `VerifiedFreeze.document` が mutable — 理由: (11) の裁定で測定後の hardening と決まった  〔正しさ・防壁系〕 |
| T-112 | (9) | **裁定済み → 床値実測の後**: `s1_known_axes_freeze` の root 束縛が不完全 | `s1_known_axes_freeze` の root 束縛が不完全 — 理由: (9) の裁定で床値実測の後と決まった  〔正しさ・防壁系〕 |
| T-114 | (9) | **裁定済み → 一巡後**: never-issued の全層 scope 漏れを統合テストで塞ぐ | never-issued の全層 scope 漏れ — 理由: (9) の裁定で一巡後と決まった  〔正しさ・防壁系〕 |
| T-085 | (6) | PKG-1 採用裁定済 (ユーザー) → floor 実測後の hardening wave で実装 | PKG-1 の実装 — 理由: (6) の裁定で floor 実測後の hardening wave と決まった  〔正しさ・防壁系〕 |
| T-087 | (5) | **裁定パッケージ (新規)**: post-seal FROZEN_MANIFEST 23 件 vs 恒久設計 12 件 (D75 W-e = 旧 8 + 新 4) の未整合。将来期待集合 (12/27/他) と暫定 pin (`FROZEN_KEYSET_PROVISIONAL_82803D6D | post-seal FROZEN_MANIFEST 23 件と恒久設計 12 件の未整合 — 理由: 恒久形 (D75 W-e) の実装時に暫定 pin を撤去して再整合すると記録済みで、それまで発火しない  〔正しさ・防壁系〕 |
| T-012 | (33) | **裁定済み (2026-07-28 = 解除しない)**: task-run pilot の凍結解除可否。[T-154] (1) の `DW-O07` 削除で「解除しない」側に確定。pilot を復活させる場合は新規に裁定を起こす | task-run pilot の凍結解除可否 — 理由: (33) の裁定で解除しないと確定した。復活させる場合は新規に裁定を起こす  〔プロセス文書系〕 |
| T-010 | (16) | 延期: B-008 再試験。**本エントリで実照合し未発火と確定** (daemon 2.1.220 は major/minor 同一) | B-008 (guard_agent) の再試験 — 理由: (16) の実照合で daemon の major/minor が同一のため未発火と確定した。次に major/minor が上がった新規 background session で再試験する (手順の正本は hooks/README.md)  〔テスト衛生〕 |
| T-082 | (10) | 延期 (同): 公式 consumer の必要分は本 wave で充足、全 caller 移行は 1 cycle 後 | 全 caller の移行 — 理由: (10) の裁定で公式 consumer の必要分は充足済み、残りは 1 cycle 後と決まった  〔正しさ・防壁系〕 |
| T-121 | (22) | **[T-120] と同じ理由で優先度低**: real-repo group の reader/writer 分離。 **本エントリで実質不要と判明** — `real-repo` group の直列和は [T-117] の memo 化以降 0.1 秒しかなく、もはや制約ではない | real-repo group の reader/writer 分離 — 理由: (22) で実質不要と判明した (直列和 0.1 秒でもはや制約でない)  〔テスト衛生〕 |
| T-156 | (36) | **P3 (条件成立まで保留)**: selector-8b workload descriptor へ set-size 条件を反映する。 変わらず | selector-8b workload descriptor への set-size 条件反映 — 理由: (36) で条件成立まで保留と裁定済み。発火条件は「8b descriptor の拡張を設計するとき」または「TPC-C 級 workload corpus を採るとき」で、着手前に workload 別の set-size 分布を測る順序も決まっている  〔研究・計測系〕 |
| T-131 | (23) | **却下 (本エントリ)**: worker 間 fixture 共有。2 方式・敵対レビュー 6 本を経て、 効果が「CPU work −13.9%、wall ゼロ」に対し正しさ基盤へ偽緑経路を持ち込むと判明したため 実装しない。**代替は [T-135] (共有機構なしで build 合計を半減 | worker 間 fixture 共有 — 理由: (23) で却下済み (効果は CPU work −13.9% / wall ゼロなのに、正しさ基盤へ偽緑経路を持ち込むため)。当時の代替 2 件のうち [T-132] は完了済み、[T-135] は (36) で別途却下された  〔テスト衛生〕 |
| T-161 | (37) | **P3 (nit/backlog、段 3 B-8)**: check_docs の positive control に「段 5 operation 行 削除」の focused ケースがない。変異 matrix の手動検証と literal pin で当面代替済み。 G05 成果物影響なしのため | check_docs の positive control に段 5 operation 行削除の focused ケースが無い件 — 理由: `DW-G05` の成果物影響を書けない nit/backlog であり、追加 review wave を起動しないと記録済み  〔テスト衛生〕 |
| T-164 | (39) | **P3 (nit/backlog、T-149 段 6 RA-3 残余)**: s6 freshness テストの fake ls-tree の 引数完全 pin と opened の int/bool 型境界。G05 成果物影響を書けないため review wave は 起動しない | s6 freshness テストの fake ls-tree 引数 pin と型境界 — 理由: `DW-G05` の成果物影響を書けない nit/backlog であり、追加 review wave を起動しないと記録済み  〔テスト衛生〕 |
| T-170 | (73) | **P3・裁定済み ((60))** | CCBench 上流への還元 — 理由: (54) の裁定で [T-167] wave へ束ね、上流 PR / push は人間が行う  〔プロセス文書系〕 |
| T-176 | (73) | **P3・backlog ((60))** | raw evidence bundle の保存形 (trace 圧縮) — 理由: (60) の裁定で driver 変更を伴うため次回 characterization に合流すると決まった  〔研究・計測系〕 |

## 継続 (次の一手に残した項目)

| ID | 出所 | 最終実体テキスト (先頭 150 字) |
| --- | --- | --- |
| T-316 | (119) | **完了 (本エントリ)**: 分類されていない source の build を、`buildcache.build()` / `build_v2()` / `pipeline.evaluate()` / `loop.run_campaign()` の 4 面で既定拒否にした (D127)。 `C |
| T-345 | (119) | **P3・新規 (本エントリ)**: **敵対レンズの prompt が上流の安全分類器に拒否される。** 段 3 レンズ A の初回投入 (rc=1、出力 0 byte) は、prompt が「gate を迂回する payload 文字列を 具体的に書け」と exploit 構築を求めたため拒否さ |
| T-346 | (119) | **P3・新規 (本エントリ)**: **`/dev-wave` の引数が完了済みタスクだった場合の作法が無い。** 本 wave は引数 [T-276] で起動されたが、worklog 末尾で完了済み (D122) と判明した。入口にも reference にも扱いが書かれておらず、親が即興でユー |
| T-317 | (119) | **候補が 1 件増えた (本エントリ)**: 段 1 の前提実測を親が行う手段が probe script になると 凍結境界と衝突する件。本 wave では**ファイルを書かず** stdin heredoc で既存モジュールを呼ぶ形で 回避した。「ファイルを書かない実行」が前提実測として足りる |
| T-139 | (134) | **P1・裁定済み → 着手条件を更新**: 択 (a) (O(1) stripe 計算 + cache line padding を備えた 代替 X で probe 再走) は不変。ただし着手条件は「[T-338] の floor 裁定の後」から **「[T-338] の Q1〜Q5 の裁定の後」 |
| T-337 | (134) | **P1・裁定済み → 着手条件を更新**: 択 (a) (新 D で権威境界を定義し正例 artifact を `artifact_role=qualification` として置く) は不変。着手は [T-338] の Q1〜Q5 の後へ改める。 加えて本項は [T-338] Q11 (gate |
| T-338 | (142) | **P1・裁定完了 (11/11) → 実装待ち**: Q5 = 標準化効果 `d ≈ 1.0` (約 11 cluster) を 正例の目標とする。**目標効果量は study ごとに事前登録で決め直す**が、**結果を見てから J を 足すことは禁止** (D126 決定 (4) の型。足りなけ |
| T-339 | (134) | **P2・裁定済み → scope が具体化**: 択 (b) (consumer は後続へ) は不変。本 wave の Q11 が中身を確定した — 計測 producer / attempt registry / schedule validator / RF calculator / [T-3 |
| T-340 | (145) | **P2・裁定済み → 実装待ち**: 択 (a) 採用 — `tools/pegasus/` に pin 検証つきの取得経路を 置く。規約化のみに留めない。対象は masstree / mimalloc / googletest。 `gflags_source_path` / `glog_sour |
| T-341 | (134) | **P3・候補 2 件と実測値を追加**: 本 wave の段 8 候補も同じ byte 予算に阻まれた。 (c) **`DW-O01` に子 process の切り離し方法が無い** — wrapper の形は規定するが「親の呼び出しが 終わっても生き残る経路で起動する」が無く、F77 の恒久対応 |
| T-213 | (116) | **P2・裁定済み ((116)) → 実装待ち**: 択 (a) 採用 — 検査用隔離 clone の置き場を共有 FS へ 移す。同じ clone で走る `orchestrator` check (`tools/run_tests.py`) も同時に解消する |
| T-318 | (116) | **P2・裁定済み ((116)) → 実装待ち**: 択 (a) 採用 — producer ごとに `artifact_role={official,exploration,qualification,dry}` を宣言させ閉表化する。 新規 producer は宣言なしでは通らない形にし、族の |
| T-309 | (116) | **P3・裁定済み ((116)) → 実装待ち**: 択 (a) 採用 — 8c report の形テストを実在 4 outcome へ 広げる |
| T-307 | (116) | **P3・裁定済み ((116)) → 実装待ち**: 択 (a) 採用 — recipient matrix へ last valid measured baseline を載せ、**経過試行数を同送**して古さの誤認を防ぐ |
| T-308 | (116) | **P3・裁定済み ((116)) → 実装待ち**: 択 (a) 採用 — 百分率は固定桁 round を role 契約にする |
| T-329 | (115) | **P1・裁定済み ((115)) → 実装待ち**: 択 (a) 採用 — 参照先エントリの実在照合と archive の 主張範囲・実体の一致検査を `check_docs.py` へ入れる。受理集合を変えるので事前登録変異で 実発火を実証する |
| T-244 | (126) | **P1・択一 7 件すべて裁定済み → 実装待ち**: §8 の択一 1・2・3・5・6・7 は推奨どおり採用。 **択一 3 = 候補 batch の事前凍結を多世代開放の必須前提にする** (batch cardinality・全候補の 事前 commit・seal までの結果非公開をセットで |
| T-327 | (115) | **P2・裁定済み ((115)、推奨を蹴って (b))**: 8c 正式系列の事前登録は**条件充足の機械確認で 自動発効**とし、都度の明示承認は求めない (ユーザー理由 = 定型コマンドの手間を排除)。 実装要件として**条件文自体の凍結** (変更は事前登録の改訂扱い) を伴わせる |
| T-287 | (115) | **P2・裁定済み ((115)) → 実装待ち**: 択 (a) 採用 — checkpoint 由来の値を閉じた値域と形式で 検証してから planner / coder payload へ渡す |
| T-295 | (125) | **P2・裁定済み → 実装待ち (裁定待ちから除外)**: 依存 4 件が全て決着したため判断は残って いない。残作業は事前登録文書 §5 の数値欄と §6 前提条件 12 件の実装 |
| T-324 | (122) | **P1・裁定済み → [T-244] の裁定待ち**: 択 (a) 採用 — 8c 正式系列 H1/H2 を generation budget=1 で走らせない。[T-244] の裁定 → 複数世代・還流・標本設計の事前登録 → 実走の順とし、 budget=1 の結果を workload 特化 |
| T-325 | (122) | **P1・裁定済み → 実装待ち**: 択 (b) 採用 — trial registry は [T-295] の拡大でなく独立 タスクとして実装する。実走前 6 cell manifest + append-only trial registry + launcher / acceptance g |
| T-328 | (146) | **P1・ユーザー再裁定要 (前回裁定の前提が不成立)**: 外出しは実装しなかった。D94 却下案 (a) が 同じ scope を「読了削減 0 で総量予算と checker 改修だけ増える」として却下済みで、 dev-wave の読み込み契約が leaf 節単位である以上その実測は今も成立する |
| T-319 | (113) | **P2・新規 (本エントリ)**: official report の marker **allowlist 必須化**と祖先 marker 検査 (D65 P-A1(a) Stage 1、D65 が個別承認を要求)。marker 不在 root を official として受理する現行の blo |
| T-320 | (113) | **P3・新規 (本エントリ)**: 8c `--no-build` の trial-local layout (`<run-root>/campaigns/<id>`) を campaign と別型にし、Layer3 report に formal / exploration / dry の受理境 |
| T-321 | (113) | **P3・新規 (本エントリ)**: `guard_bash` の realpath 非解決・`cd` 追跡なし・hardlink alias・ 別 worktree の硬化と、`authorize_output_root()` の実行経路への必須化。official tree にも同型で 存在する |
| T-322 | (113) | **P3・新規 (本エントリ)**: campaign-id / lock preimage への namespace 束縛。D123 決定 (3) で ID は namespace 非依存にしたため、歴史 official campaign と新 exploration campaign が同じ  |
| T-279 | (113) | **候補が 1 件増えた ((111))**: 段 8 で「子がテストを実走できない環境ではその旨と静的検査で 足りることを明記させ、緑を主張させない」を `DW-S05-C` へ統合しようとしたが、 `docs/dev-wave/**` の合計 hard ceiling に阻まれて撤回した。本 w |
| T-305 | (109) | **P2・裁定済み ((109)) → 実装待ち**: 択 (a) 採用 — live role 定義の記述 drift 3 種を実物へ 合わせる。pin 閉包 (`SOURCE_FILE_SHA256` + role-adapters 再生成) を通し、受理集合の変更手続を守る |
| T-304 | (109) | **P2・裁定済み ((109)) → 実装待ち**: 択 (a) 採用 — `throughput_ops_sec` を実体 (transactions/sec) に合わせて rename する。[T-305] と同一 wave で扱う |
| T-313 | (140) | **P3・裁定完了 → 実装待ち**: 択 (1) 3 層 gate を現在値で凍結。常に読む層は固定上限を 維持し、ノウハウ全体の固定文字数上限は撤廃する ([T-127] の合計上限方針を改める。増枠ではなく 「常に読まない部分を予算対象から外す」構造変更)。**剪定は byte 数でなく発火実 |
| T-311 | (109) | **P2・裁定済み ((109)) → 実装待ち**: 択 (a) 採用 — 変異 harness の自己申告 2 件を 外側 supervisor の receipt 要求で機械検証する |
| T-310 | (108) | **P2・新規 (本エントリ)**: `DW-O09` の**ファイル集合 pin digest** (F39) が未解決。 `failures.md` が「現行実体: なし」と明記している。新規 file の追加は特定 file の bytes pin では なく `repository_file |
| T-312 | (108) | **P2・新規 (本エントリ)**: 新 gate 群への**事前登録変異の本走**を、新設した `tools/mutation_harness.py` 自身で行う (dogfood)。本 wave は負例テストの静的単一理由判定に 留めた。あわせて `DW-M08` / `DW-O11` / `D |
| T-298 | (105) | **P2・本エントリで一部完了 (105)**: 閾値ルールの明文化と drift 検査は入ったが、 **依頼のうち「閾値超過を自動で計算ノードへ投げる」は未実装**である。D105 supersede を含む 4 条件が揃うまで開けておく。第 3 task の最有力候補は `codex_worke |
| T-299 | (105) | **P1・新規 (本エントリ)**: `test_s8b_oracle_driver.py` の 40 件が local main で赤い。 `d2ac13e` で再現し、本 wave の差分とは無関係。症状は `result["status"]` が `error` であるべき箇所で `refus |
| T-300 | (124) | **P1・裁定済み → 実装待ち**: login 側 LLM 子の admission gate を実装する。上限は **16 GiB (利用者 tanab、login ノード)**、目標上限 **12 GiB**。算入対象はプロセスのメモリ使用量に 加え `/dev/shm` 等も含む。**計算 |
| T-301 | (105) | **P2・新規 (本エントリ)**: 開発 harness (`codex_worker_launch.py` / `codex_reasoning_ab.py` / `dev_waves/*` / `dev_waves/checker.py` / `check_docs.py` の login 実 |
| T-303 | (105) | **P3・新規 (本エントリ)**: `t152_write_intent_coverage.py` と `silo_ladder_rung1.py` の 直接 CMake 経路に site gate が無い。受理集合とテストを伴う別パッケージ |
| T-296 | (145) | **P2・裁定済み → 実装待ち (floor 側の待ちを解除)**: Pegasus 専用 env-tag の新設は 従前どおり。あわせて **floor 側の待ちが解除された** — floor 実測に着手してよい。 順序は env-tag 新設 → floor 実測 → env タグ付き登録 |
| T-294 | (130) | **P2・裁定済み (再確認) → 実装待ち・検出の正本**: 択 (a) 維持 — `/rulings` の収集を land 直前に再走させ、**語ベース判定をやめて「次の一手」の全項 × 裁定パッケージの有無で判定する**。 [T-314] は本項の補助として位置づける |
| T-248 | (101) | **P2・再裁定済み ((101)) → 実装待ち**: 択 (b) 採用 — child PATH 確定後に `python3` の版数 だけを検査し 3.10 未満で `stage="interpreter"` rc=16 で止める最小 assert。full shim は作らない。 受理集合を |
| T-219 | (101) | **P2・裁定済み ((101)) → 実装待ち**: [T-291] と同じ手 ((a) + (b)) で枠を作り、滞留していた dev-wave 改善候補 4 件を入れる。AI が候補を洗い出し、削除・外出しの選択はユーザーが行う |
| T-227 | (101) | **P2・裁定済み ((101)) → 実装待ち**: 択 (a) 採用 — `DW-S06-A` / `DW-S06-C` の reasoning を `max` として `docs/dev-wave/workers.md` に明記する。引き下げ判断は [T-181] 再走後 |
| T-184 | (138) | **P1・裁定済み ((101)) → [T-181] 再走待ち (scope から 1 点を除外)**: 工程別 policy の 採用は認証再走の後という裁定は変えない。**model×reasoning 非対応組の事前検査は [T-371] の 裁定により [T-189] 系が所有**し、本項 |
| T-249 | (100) | **P2・本エントリで一部完了 ((100))**: 裁定 (b) のうち**凍結 bytes を変えずに動かせる範囲**を 実装した (task 固有 7 key の移設 + 所在索引 + 閉集合 gate、D115)。**完了ではない** — 共有・サイト値は 凍結 file に残っており、その |
| T-292 | (100) | **P3・新規 (本エントリ)**: certify 経路 shell (`certify_calibration.sh` / `submit_certify.sh`) の `readarray < <(...)` が producer の終了状態を失い、厳密型検査も無い。 数字文字列や key 欠 |
| T-293 | (144) | **P2・本エントリで実測完了 ((本エントリ))**: 「まず計算ノード側の実測を取る」を完了した。 **起票時の前提 (値が stale) は誤りで、3 因 (login に候補が無い / 候補が symlink で `_executable` が 拒否する / `gcc-13` 不在で `cc |
| T-289 | (99) | **P3・新規 (本エントリ)**: 8c の freshness 検査と state 生成の **TOCTOU (並行 race)**。 同じ trial/config の 2 supervisor が同時に検査を通過しうる。原子的 campaign reservation (stale lock |
| T-284 | (98) | **P3・新規 (本エントリ)**: 重複 key の扱いが非対称。submit は `no_dups` で拒否するが job は 素の `json.load` で last-wins。最終出現値だけ canonical な重複 policy を job が受理し submit が拒否する。 別軸の |
| T-286 | (125) | **P4・裁定済み → 実装待ち**: 未参照の予約 policy key を削除する |
| T-241 | (96) | **P2・再スコープ ((96))**: 「Pegasus 計算ノードで再開する」は前提が誤りだった。live pilot の 実体は [T-276] (実行場所契約の再裁定) と [T-277] (Pegasus 実行の受理集合と build identity) に 分解される。両者が閉じるまで  |
| T-278 | (96) | **P3・新規 (本エントリ)**: transport 断の同型経路の棚卸し。`s6_proposal_rounds.py` は `claude -p` に env を渡さず親環境を全継承し、`tools/dev_waves/daemon.py` は子環境を再構成して proxy を捨てる。all |
| T-118 | (97) | **P2・部分解消 ((97))**: provider neutral tree の lifecycle を実装し、 `s8b-selector-*` / `izanagi-projected-*` の**新規残留を止めた**。元観測の残留全体は [T-280] (例外経路の production |
| T-280 | (97) | **P2・新規 (本エントリ、scope 外 real)**: 例外経路で漏れる production callsite。 親が裏取り済み = `s3_lock_coverage.py:75` `_run_trace` (`subprocess.run(timeout=RUN_TIMEOUT_S)` |
| T-281 | (97) | **P3・新規 (本エントリ、scope 外 real)**: テスト側の素の `mkdtemp` 60 箇所 / 18 ファイル (`test_p3_s4_loop.py` 15、`test_s8a_trigger_sweep.py` 8 ほか)。TMPDIR 一括 redirect は採らない  |
| T-270 | (96) | **P3・追加データ ((96))**: 同じフレークを本 wave の全走 2 回で観測した。3・4 例目である。 `876837` は `test_s8b_floor_campaign.py` 6 件 + `test_ruleops.py::test_real_checkout_...@real |
| T-273 | (95) | **P3・新規 (本エントリ)**: `orchestrator/qualification/submission.py:73,107` は toolchain の version を記録するだけで floor を課さない (F46 の「記録するだけで発火しない値」型) |
| T-274 | (95) | **P3・新規 (本エントリ)**: `tools/pegasus/dispatch_compute.py` の `_job_run` 版数 gate は 単独削除しても既存 M5 (両層同時変異) でしか捕まらない。冗長 gate の片側 sensitivity pin が無い |
| T-275 | (95) | **P3・新規 (本エントリ)**: `output/pegasus-dispatch/` root の owner / mode / symlink を 誰も検査していない。dispatch 成果物の脅威モデルが未定義 (敵対レンズ A-5) |
| T-265 | (93) | **P3・新規 (本エントリ)**: campaign identity と WAL replay が env 非依存である。 `campaign_id` は `(spec_slug, search_tag, cfg_hash8)` だけで `campaign.lock` の正準 pre-image |
| T-266 | (93) | **P3・新規 (本エントリ)**: 同型の偽タグ穴が兄弟 driver と共通経路に残る (`p3_s4_loop` / `p3_s4_loop_sort` / `s8a_trigger_sweep` ほか、repo 内の `run_campaign` caller と `screening_dr |
| T-267 | (93) | **P3・新規 (本エントリ)**: `linux-baremetal` の正の machine attestation が無い。 `site_policy` は Pegasus を否定できるが cygnus を積極同定できず、`pegasus0N` でも `qsub`/`qstat` が PATH |
| T-268 | (93) | **P3・新規 (本エントリ)**: pegasus を本軸の runnable env にするか。D59 の 4 条件、 env スコープ付き campaign identity、attestation、isolation、noise floor 配線が要る |
| T-269 | (93) | **P3・新規 (本エントリ)**: guard 拒否が材料レポート生成**後**に起きると、 provenance header は書き換わるが既存レポートは上書きされず、その `artifact_refs` の SHA が 現 header bytes と一致しなくなる。proof chain  |
| T-222 | (92) | **P1・実施待ち ((80))、本エントリで位置づけを確定**: main の `_accounting_present` が Request ID と Started/Ended/Elapse しか束縛せず scheduler group を見ていない件。**[T-193] の 閉鎖条件から外し |
| T-144 | (134) | **P1・従属先を更新**: [T-139] への従属は不変。加えて**スペクトル補間の物差しが RF である 以上、[T-338] Q1 (推定量) に直接従属する** — `E[N]/E[D]` と `E[N/D]` では「既知解までの距離」の 定義自体が変わる |
| T-257 | (91) | **P1・裁定済み ((91)) → 実装待ち**: 択 (a) + (d) 採用 — 検査は省かず、land の排他 lock を 待機可能にする。段順入替 (b) と再走免除 (c) は採らない |
| T-255 | (91) | **P2・裁定済み ((91)) → 実装待ち**: 択 (a) 採用 — mid-flight の handoff 検査を非対称化し、 追加された名前だけ拒否・protected は前後の和集合とする |
| T-254 | (91) | **P2・裁定済み ((91)) → 実装待ち**: 択 (b) 採用 — 共有 `.git` 面は一律に緩めず、経路ごとに 「incoming と無関係と言い切れるか」を判定する。検査自体を無効化しうる経路は緩めない |
| T-258 | (91) | **P2・裁定済み ((91)) → 実装待ち**: 択 (a) 採用・**新規のみ必須**。`output/insights/` の wave 専用ディレクトリを新規から必須化し、既存 151 件の平置きは移動しない |
| T-231 | (90) | **P2・裁定済み ((90)) → 実測待ち**: `orchestrator/codex_roles/launcher.py` の login ノード `--tmpfs /tmp` の実消費を (82) と同じ手順で測り、その結果を見てディスク側へ向け直すかを決める。 測定前に隔離契約を緩めない |
| T-214 | (90) | **P2・裁定済み ((90)) → 実装待ち**: 分割 commit の順序決定時に各 commit 時点の gate 通過を 確認する義務を `docs/dev-wave/**` へ加える。**[T-219] / [T-204] の予算解消が前提**で、 空け方は D110 の外出し方式を第一 |
| T-261 | (89) | provenance の scope / Codex-author epoch を CAB と同じ per-lineage 判定にする。現在は HEAD 基準の 単一 epoch で、公表契約が実装より強い (別 lineage で実装の受理集合が広がる)。D110 既知限界 (i) |
| T-262 | (89) | `--message-file` の correction preflight に exact waiver 排他を入れる。commit 後の history 監査には あるが preflight に無いため、承認された message が commit 後に担い手失格になりうる。D110 既知限界 |
| T-263 | (89) | provenance dispatch の data row を header 直後の table へ束縛し、複数行 inline code span を 追跡する fail-closed 化。`DW-O16` 3 巡上限で本 wave では閉じなかった残余。D110 既知限界 (iii)(iv) |
| T-264 | (146) | **P3・(a) の stale 判定を撤回**: 段 1 brief が (a)「実装子 prompt に最初から 『テスト実走は親』と書く」を `DW-O05` で充足済みと判定したのは誤りである。`DW-O05` の発火条件は 「read-only codex に相談・レビューさせる直前」で、 |
| T-256 | (88) | **P3・新規 (本エントリ、F68)**: `_read_regular_at` の `os.read` が未捕捉 `OSError` を 素通しし、rc 契約の外で terminate しうる。handoff 経路からは D108 で到達不能になったが、 worktree admin metad |
| T-129 | (88) | **部分完了 (本エントリ)**: F41 射程拡大分 (赤の有無が checkout に依存する) は `pytest.ini` の `testpaths` / `norecursedirs` で閉じた。**本体 (測定値が checkout に依存する) は未解決のまま** |
| T-250 | (87) | **P2・新規 (本エントリ)**: `_job_run` が `set(environment) <= spec.env_allowlist` を 再検査しないため、宣言した allowlist が子側で強制されない (`dispatch_compute.py:474-481`)。 既存 `tes |
| T-251 | (87) | **P2・新規 (本エントリ)**: legacy `buildcache.cache_key` の pre-image が compiler realpath・ version・CMake 版・dependency prefix・site・env contract を束縛しないため、**別環境で作 |
| T-252 | (87) | **P3・新規 (本エントリ)**: dispatcher の receipt が request SHA・repo commit・driver SHA・ proposal SHA を束縛しないため、queue 待ち中に入力が変わると receipt と実際に走った内容が食い違う |
| T-245 | (86) | **P3・新規 (本エントリ)**: 取り込み済みとなった `codex/p3-autonomous-trial` の |
| T-235 | (84) | **P2・新規 (本エントリ)**: 8c supervisor のマシン非依存な予算機構 — `--max-wall-seconds` の hard wall 化 (role subprocess の timeout を残 wall で clamp)、 `drive()` 前の bench env |
| T-238 | (84) | **P3・新規 (本エントリ)**: driver 族 (`p3_s4_loop.py` / `p3_s4_loop_trigger_gating.py` / 同 sort・trigger 版) の `ENV_TAG`/`CLK`/`NUMA` ハードコードを `env_contract` regi |
| T-239 | (84) | **P3・新規 (本エントリ)・別裁定**: floor 凍結式 `_FLOOR_RESERVATION_FORMULA` の bench 項が 名目 `extime × reps` である件。実測上界との乖離は 8b consultations の B4' と本エントリの n=51 で 独立 2  |
| T-234 | (83) | **P3・新規 (本エントリ)**: `docs/handoff/` に完了 wave の handoff が 3 件残っている (`2026-07-29-t126-...`・`2026-07-30-dev-wave-improve`・`2026-07-30-dev-wave-skill-clean |
| T-208 | (83) | **P3・実施待ち ((79))、本エントリで 2 件目が合流**: `.claude/commands/cleanup-branches.md` §3 へ反映すべき運用則が F26 の半削除事象に加えて **F63 (防護パス + 不透明構文の同居拒否)** の 2 件になった。 同ファイルは実測 |
| T-232 | (82) | **P3・新規 (本エントリ)**: `patchharness.py` の apply 排他 lock が TMPDIR 由来で、 置き場を動かすと共有 submodule の排他 scope が変わる。node 固定にすべきか |
| T-233 | (82) | **P3・新規 (本エントリ)**: `tools/pegasus/README.md` の `TMPDIR=/scr/$PBS_JOBID` が `certify_calibration.sh` の `${PBS_JOBID//:/_}` と矛盾する (colon sanitize の記述漏れ) |
| T-215 | (78) | **P2・実施待ち (本エントリ、A-6)**: 中継は親・人間が読む一次資料を確保するだけで、試行台帳 (`output/task-runs`) の `collected_node_digest` は `tools/run_tests.py` が `sidecar=None` を渡すため 空のまま |
| T-216 | (78) | **P3・実施待ち (本エントリ、A-9/B-12)**: `_bounded_log` の省略注記が改行でなくリテラルの 2 文字で連結されている既存欠陥 (HEAD 以前から存在)。中継がこれを親の画面へ露出させた。併せて 切り詰め経路 (`omitted_bytes > 0`) を通る中継テス |
| T-217 | (78) | **P3・実施待ち (本エントリ、R2/N5)**: 中継中にシグナルが来たときの複合副作用 (receipt が `kind: child` と `kind: infra` の 2 通に割れる / 同じログを二度中継する / 原因が setup failure と ラベルされる) を通すテストが  |
| T-218 | (78) | **P3・実施待ち (本エントリ、F11 退行 / R6・N3 / A-10)**: テスト衛生 3 件 — 順序 assert の 導入で infra テストが再び stream 対応表へ結合した (G2 と F11 は構造的に両立しない)、`os` モジュール 実体を process 全体で差し |
| T-212 | (77) | **P2・新規 (本エントリ)**: `hooks/guard_bash.py` の `_script_target` が `-m` の第 1 非 option 引数を sanctioned 候補へ昇格させるため、`python3 -mpytest tools/run_tests.py` が今も許可 |
| T-211 | (78) | **P2・裁定済み ((74)) → 実装待ち**: 択 (c) 採用 — 保存則に**確定済み ID の再利用の 検出**だけを足す。文言の推敲は通す。本日 3 度目の同型再発 ([T-220] / [T-213] の衝突) が根拠 |
| T-201 | (76) | **P1・裁定済み ((74)) → 実装待ち**: 択 (a) + (b) 採用 — 本番 `t080_freeze_migration._history_touches_path` の走査置換 (90 秒中 80 秒に直接効く唯一の案) と `output/` の tracked bytes 削 |
| T-202 | (73) | **P1・新規 (本エントリ)**: `real_repo_receipt_memo` に現存する 2 欠陥を閉じる。 (a) `--testrunuid` は呼出し側が固定でき `run_tests.py` が素通しするため、同一 UID・HEAD で 6 時間以内に 2 回走らせると実 rece |
| T-204 | (76) | **P2・裁定済み ((74)) → 実装待ち**: `docs/dev-wave/**` の 24000 bytes 上限は 上げず、未使用の L2 節を削って空ける。削除候補の洗い出しは AI、選択はユーザー |
| T-203 | (73) | **P2・backlog (本エントリ)**: 性能施策の一次証拠を duration にしない仕組み。 builder と waiter が同じ duration を出すため代理にならない。同一 allocation 内の paired 比較 (A-B / B-A) と機構の実発火回数の直接観測を |
| T-196 | (78) | **P3・裁定済み ((74)) → 実装待ち**: 択 (a) 採用 — `silo_ladder_rung1.py` と `t152_write_intent_coverage.py` を `refuses_heavy_work()` gate と `default_build_jobs()`  |
| T-199 | (73) | **P3・backlog**: dev-wave 改善候補 3 件 — (a) 親が書ける「実装面」の境界 (DW-G01 の 生死 driver と親の変異 harness) を reference 節へ 1 行で明示、(b) DW-S01 の brief 10〜30 行が 条件 dispatch |
| T-189 | (135) | **許可リスト部分は実装完了 → 残りは比較実験の設計**: 3 面 (codex worker launcher の `--reasoning`、dev-waves serve の `--effort`、worker spec / child argv) に値域検査が入り、 正本は `tools/ |
| T-190 | (73) | **P2・新規 ((70)、F57)**: launcher normal fakeの32-worker負荷フレークを 失敗artifact保存つきで原因分離し、production gateを緩めずfixtureをhardenする |
| T-181 | (81) | **実装完了・結果は replay 未認証 ((75))、(80) で台帳を再集計**: 残件は最終版装置での 10 run 再走。(80) が `aggregate-uncertified.json` の `resource_ledger` を arm 別に再集計し、 **推論出力トークン hig |
| T-183 | (138) | **P1・着手可 (scope から 1 点を除外)**: F43/F45 型の断片出力 / safety-filter 終了の 早期分類・retry 上限・fail-closed 回復は従前どおり本項が持つ。ただし **model×reasoning 非対応組の事前検査は [T-371] の裁定に |
| T-186 | (78) | **P3・裁定済み ((74)) → 実装待ち**: 択 (b) 採用 — `max_artifact_bytes` だけ入れる。 seal ceremony と `setsid()` 脱出子の完全封じ込めは見送る |
| T-185 | (73) | **P3・RuleOps hardening ((63) R3R-1)**: receipt range の commit 数と path-union stdout bytes/cardinality を streaming 上限で fail-closed にし、安定 reason と over-l |
| T-126 | (86) | **完了 ((86) で実装・main 統合・land)**: 逐次停止 v2 の attempt staging 回収順序を是正。live qualification は本 wave の scope 外で未実施 |
| T-059 | (73) | **裁定済み ((62) = bounded な事後 mutation audit) → 実施待ち**: 事前登録不能だった逸脱を明記し、T-172のdrift拒否検査を事後検証する |
| T-134 | (22) | **新規・着手可能 (衛生)**: 並列度の再最適化。既定 32 は 2026-07-19 に約 1946 テストで 測った値だが、現在 3103 テストで構成も変わった。`-n 8` の work 534.5 秒に対し `-n 32` は 685.4 秒で、既に競合領域に入っている |
| T-123 | (17) | **新規 (衛生・裁定不要)**: `daemon.py` の `_atomic_json` は呼び出し 0 件のデッドコード。 本 wave の棚卸しで確認した。削除は scope 外なので触っていない |
| T-109 | (9) | **着手可能 (裁定完了)**: `/dev-wave クロスプロトコル対応` を新セッションで実行する。 (a) = patch 例外は裁定済み (D16 の一回限り例外欄)。残る (c)〜(i) は同 wave の段 1 で scope 化する |
| T-113 | (14) | **裁定済み → 着手可能**: root-isolation 変異の control を新設する |
| T-097 | (14) | **裁定済み → 着手可能**: 変異台帳 JSON を placeholder 検出の対象族へ足す |
| T-100 | (14) | **裁定済み → 着手可能**: 検出語彙へ表記ゆれ・HTML entity を足す |
| T-099 | (14) | **裁定済み → 着手可能**: 凍結成果物の placeholder は止める仕様を明記する |
| T-009 | (17) | **ユーザー裁定待ち (本 wave の裁定パッケージ、real)**: dev-wave の実装子が負う規律の所在。実装子は docs と commit を禁じられる一方、`AGENTS.md` のクラス 2/3 規律は handoff とセッション末 worklog を求める。現状は親が射影して |
| T-060 | (14) | **着手可能**: WAL 用語運用の明文化 |
| T-130 | (73) | **裁定済み・実装待ち ((60))** |
| T-133 | (36) | **P2・裁定済み (2026-07-28 = fsync 無効化案) → 実装待ち**: テスト用 git の fsync を切る。 変わらず |
| T-088 | (145) | **裁定済み・実装待ち + floor 着手の裁定**: floor 実測に着手する。**1 wave (ジョブ束 1 回) 規模に収め、足りなければ拡大せず裁定へ返す。** レコード数は calibrator が飽和最小で決め、 計測前に単独性を確認し、env タグ付きで登録する。**段階 3・4 |
| T-096 | (20) | **裁定済み → 着手可能**: driver 側 timeout を予約式と整合させる。**[T-088] の前提**。 [T-120] が閉じたので前提の順序待ちは解けた |
| T-011 | (145) | **floor 着手の裁定を反映**: between-run floor の取得に着手してよい ([T-088] と同一裁定)。 1 wave 規模の束縛と、拡大せず裁定へ返す規定は本項にも掛かる |
| T-159 | (36) | **P3・裁定済み (2026-07-28 (36) = (b) 注釈のみ) → 実装待ち**: 過去 campaign へ 「この期間の trigger provenance は誤 id の可能性あり」の注釈を付ける (材料 = `output/insights/2026-07-28_t157-r |
| T-160 | (37) | **完了 (2026-07-28 (37))**: 読了トリガ層の定義 (D94) + DW-O07 削除 + 削除 gate。 陳腐化候補 7 節の裁定パッケージは insight §5 (削除実施はユーザー裁定待ち)。CTX ポインタ統合は refuted で撤回 |
| T-163 | (45) | **P3・裁定済み (2026-07-29 (45) = 採用) → 実装待ち**: 束縛追加は凍結実験の検証設計 変更のセレモニー付きで別 wave |
| T-166 | (47) | **P3・新規 ((47) 起票、dev_waves 側の残余束)**: 隔離 checkout への submodule modules cache 複製 (fixed check `orchestrator` は submodule 不在で従来から赤 — 非悪化を (47) で確認)、rc=13 |
| T-167 | (73) | **P3・裁定済み・実装待ち ((60))** |
| T-168 | (50) | **P3・新規 (T-152 の族)**: read_set_ の intent shadow。R 行も同じ container 再走査で、 read 喪失は G2 検出力を沈黙劣化させる (段 3 P6 裁定で本 wave scope 外) |
| T-169 | (50) | **P3・新規 (trace 層全体)**: trace stream (ofstream) の I/O fail-open を fail-closed 化 (段 3 BG-A12。C/R/W/X/P/I 全行が同罪、trace.hh 変更を伴うため別 wave) |
| T-174 | (78) | **P3・裁定済み ((74)) → 実装待ち**: 択 (c) 採用 — 渡した prompt bytes を保存し事後監査を 可能にする。mediated launcher / provider receipt による因果束縛は見送る |
| T-175 | (78) | **P3・裁定済み ((74)、[T-174] と同 wave) → 実装待ち**: 択 (c) 採用 — 射影入力を人可読で 記録する。trusted registry の artifact ID 起点への再設計は対外主張の直前が着手時期 |
| T-177 | (76) | **P3・裁定済み ((74)、[T-204] と同根) → 実装待ち**: 上限を上げずに未使用 L2 節の 削除で空け、F53 恒久対応の DW-O02 統合を通す |
| T-223 | (80) | **P3・新規 (本エントリ)**: `env -u PYTHONPATH` と `git submodule update --init --recursive` の運用手順を Pegasus runbook へ書くか `DW-O08` を改めるか。 どちらも正しい fail-closed である |
| T-224 | (80) | **P3・新規 (本エントリ)**: dev-wave 改善候補 3 件 — (a) `DW-S06-A` にも 「親自身の実測主張をレンズへ入れる」義務を書く (**`docs/dev-wave/**` の予算余裕が 7 bytes しか なく入らない**。上限は上げない)、(b) `DW-G05 |
| T-306 | (106) | **P3・新規 (本エントリ)**: 非有限な raw metrics が `generation_record["harness"]` に残ると `allow_nan=False` の report 書込みが失敗する一方、`run-finish` は report 書込みより先に journal  |
| T-315 | (110) | **P2・新規 (本エントリ)**: `_validate_generation_budget()` と campaign freshness の エラーメッセージが今も「D106 残余 1 の裁定まで」と出す。裁定は済んで前提条件 P1〜P10 の未充足へ 移ったので、停止理由の文言が実態とずれて |
| T-330 | (122) | **P1・裁定済み → 実装待ち**: 択 (a) 採用 — `/scr` fresh namespace と `single_process` 強制は、使用権を供給する wrapper の新設とセットで独立タスクとして実装する。発火 caller を持たない 強制だけの部分実装は採らない |
| T-331 | (124) | **P2・裁定済み → 実装待ち**: 択 (a) 採用 — 兄弟 driver / legacy caller の COMPUTE 閉鎖を、 凍結ソース閉包の再 pin を含む独立タスクとして立てる。閉鎖のみの部分実装は採らない |
| T-332 | (117) | **P3・新規 (本エントリ)**: `site_policy` の fail-open。Pegasus login は PATH から `qsub`/`qstat` が消えるだけで `OTHER` に分類され heavy-work 許可側へ落ちる。既存挙動で本 wave は悪化させないが、「LOG |
| T-333 | (117) | **P3・新規 (本エントリ)**: critic digest と screening に env 次元が無い。`GenomeLI` / `WorkloadDigest` は env を持たず loader も `env_tag` を読まない。D125 決定 (2) の campaign env  |
| T-334 | (117) | **P3・新規 (本エントリ)**: 依存 bytes の content hash 束縛。D125 決定 (3) は dependency prefix を path 要素の配列として identity に束縛するが、**依存ライブラリの bytes 自体は hash していない**。trace/ |
| T-335 | (117) | **P2・新規 (本エントリ)**: `DW-O09` の pin 閉包列挙が**凍結文書のソース sha256 pin**を拾えない。同節は「成果物パスの grep」を指示するが、`output/s1-freeze/known_axes_freeze.json` の 63 source recor |
| T-336 | (125) | **P3・裁定済み → 実装待ち**: 候補 2 件の現行版での有効性確認を先に置き、有効なら現行版 前提で書き直して取り込む。確認を飛ばさない |
| T-347 | (138) | **P2・所有を確定 → 実装待ち**: [T-365] の裁定 (b) により、fold の意味検証 (FoldPlan delta の保存または決定的 replay) は**本項が単独所有**する。checker の read-only 軽量性との衝突は本項で解く |
| T-348 | (120) | **P3・新規 (本エントリ)**: fold 適用後・`git add` 前の SIGKILL は fail-closed で止まる (false green にはならない) が、transaction state が消えているため 自動 rollback / resume ができず手動回復が要る |
| T-349 | (120) | **P3・新規 (本エントリ)**: 事前登録した変異のうち N12 (冪等性)・N24 (fold rc 無視)・N25 (pending 0 件 postcondition) は、 **単独理由で赤くなる anchor が実装に存在しない**ため本走から除外した。 N12 は GC 後の 2 回 |
| T-350 | (120) | **P1・新規 (本エントリ)**: 「wave は canonical を編集しない」を 機械強制する。land が incoming audited range に canonical 3 台帳・archive・`FOLDED.md` の変更を 含む場合を拒否し、導入 migration だけ  |
| T-351 | (120) | **P2・新規 (本エントリ)**: `/rulings` の収集経路に、現 branch の valid pending fragment を加える。記録先は spool へ変えたが収集側が canonical しか読まない。 |
| T-353 | (120) | **P2・新規 (本エントリ)**: `FOLDED.md` receipt が frontmatter 込み raw bytes の hash なので、同じ本文を別 `seq` で再投入すると replay を素通りする。 metadata と独立した canonicalized body dig |
| T-354 | (120) | **P2・新規 (本エントリ)**: `base:` の 64 桁 digest を人が再現する手順が docs にない (item 境界と末尾 LF 正規化が実装内だけ)。`spool new` / `spool base` / `spool check --plan` を提供する。 |
| T-355 | (120) | **P3・新規 (本エントリ)**: 事前登録変異の一部が production 配線を 検査していない。N09 は helper を直接呼ぶため呼出し行の削除を検知せず、land の N23〜N25 は fake fold module だけで real state/GC/resume 契約を通ら |
| T-359 | (130) | **P3・裁定済み → [T-328] へ相乗り**: 択 (a) 採用 — 運用の穴 3 件は [T-328] の 外出し枠へ載せる。予算値の独立審査は行わない |
| T-360 | (130) | **P1・裁定済み → 実装待ち ([T-361] / [T-362] が前提)**: 択 (a) 採用 — `dispatch_compute.TASKS` へ `mutation` task を足す。D105 supersede + D117 の 4 契約を通す。 専用 shell を足す (b |
| T-361 | (128) | **P1・新規**: Lustre (`/work`・`/home` は `flock` mount option 付き) の flock が bnode 間で効くかを最小 probe で実測する。**silent fail-open なら二重注入で 変異台帳の verdict と復元後 bytes |
| T-362 | (128) | **P1・新規**: NQSV が walltime 超過時に SIGTERM を送るか、 grace が何秒かを最小 probe で実測する。SIGKILL なら harness の `finally` 復元が走らず F32 の再発になる。[T-360] の前提 |
| T-364 | (128) | **P2・新規**: `_collection_command` (`tools/mutation_harness.py:928-942`) が dispatch のときだけ `-n 0` を足し、local 経路は 既定 48 になる非対称を解消する。生死確認では収集列が一致したが、`_obser |
| T-365 | (138) | **P2・裁定済み → 明記のみ**: 択 (b) 採用 — fold 署名 2 条件は heuristic と明記して 現状維持する。意味検証は [T-347] の単独所有とし本項では実装しない |
| T-366 | (138) | **P2・裁定済み → 実装待ち**: 択 (a) 採用 — receipt schema へ tested main cutoff を 別 field で永続化・binding し、supervised runner を land CLI と揃える |
| T-367 | (138) | **P1・裁定済み → 実装待ち**: 択 (b) 採用 — fresh な rc=0 qstat が QUE/HLD/STG を 示したときだけ取り消しを許し、UNKNOWN・error では走行中ジョブを殺さない。[T-360] の前提 |
| T-368 | (133) | **P2・新規**: UNKNOWN のまま実際は走行中のジョブを保護する。 任意の UNKNOWN を RUN 扱いする案は採らない (scheduler の schema drift と malformed 出力を 長時間受理するため)。scheduler の権威ある証拠 (started ti |
| T-369 | (141) | **P3・裁定済み → 実装待ち (前提を組み替え)**: 旧選択肢 (縮約 / 再配分 / 見送り) は [T-313] の裁定で前提が消えたため破棄。**2 件とも条件読み層へ入れる**。発火実績があるため 新しい剪定基準の対象外 |
| T-370 | (133) | **P2・新規**: `queue_wait_timeout_s` / `overall_grace_s` / `accounting_grace_s` / `poll_interval_s` が `NaN` / `inf` / 巨大有限値を 受理し、監視ループの上界が消える。CLI は `type |
| T-371 | (138) | **P2・裁定済み → [T-189] 系が所有**: model×reasoning 非対応組の事前検査は許可リスト 機構が所有する。組み合わせ表の追加が最小変更であり、[T-183] / [T-184] は本件について参照へ降格 |
| T-372 | (135) | **P2・裁定パッケージ**: reasoning / effort の値が `orchestrator/codex_roles/manifest.json`、`.claude/agents/*.md` の frontmatter 13 件、 `docs/dev-wave/workers.md` の |
| T-373 | (141) | **P3・裁定済み → 実装待ち**: 択 (b) 採用 — `--reasoning` は拒否せず `requested_reasoning` と validity を分離して記録する。観測台帳は失敗した起動も残す必要があり、 CLI 拒否は「不正値で起動を試みた」事実を消してしまう |
| T-374 | (135) | **P3・裁定パッケージ**: 永続 profile 経由で不正な effort を渡すと、 worktree / worker spec artifact を作った後に child argv 構築で拒否される。fail-closed は 成立しているが「不正値が artifact に一切入らない」 |
| T-375 | (135) | **P2・新規**: `DW-M01` の事前登録契約へ 「受理集合を縮小する変異は、削除する値のリテラルを runner scope 全体へ機械検索してから 期待 node を確定する」を足す。F87 の手順側恒久対応であり、 `docs/dev-wave/` が本 wave の no-touch |
| T-376 | (139) | **P3・裁定済み → 実装待ち**: `(Pn)` を立てるとき「その P を反証しうる最も安い実測」を 1 つ併記する義務を `DW-S01` へ足す。`DW-G03` の独立 2 例は未充足だがユーザー判断で制度化する |
| T-377 | (135) | **P3・新規**: 変異本走 V9 で `test_codex_worker_launch.py::test_all_repo_policy_reasoning_values_are_accepted[xhigh]` が 変異と無関係に赤になった (rc=1、`invalid choice` の  |
| T-378 | (136) | **P2・新規**: capability の発行器が同一 process 内 caller から 隔離されていない。sealed 型と closed registry は偽 object を拒むが、正規 factory の無権限利用は 拒めない。別 process / OS capability  |
| T-379 | (136) | **P2・新規**: Python materializer は registry で閉じたが、 `tools/pegasus/*.sh` の 3 本と calibrator の任意 binary path、S8b content-addressed store の resume 取得が閉じていない |
| T-380 | (136) | **P2・新規**: 旧 campaign 値を内包する freeze を経由した laundering が閉じていない。`s1_known_axes_freeze.py` が編集禁止 (sha が 4 ファイル 7 field に pin) のため本 wave では閉じられなかった。 |
| T-381 | (136) | **P2・新規**: 全 receiptless 歴史成果物の遡及再分類。 本 wave は 3 campaign を明示 deny し、positive receipt 要求を新 schema 以後に限定した。 全 artifact と全 consumer の inventory は別 wave  |
| T-382 | (136) | **P2・新規**: T126 の control が receiptless な旧 P2-2 campaign を pin している。新しい admitted source の実測と新 protocol/pin が要る。本 wave では series identity と control pin |
| T-383 | (136) | **P3・新規**: `eligible_for_refreeze` が receipt chain でなく `mode == "official"` から決まる。本 wave では official mode への materializer 注入を core で 拒否する最小閉包に留めた。 |
| T-384 | (136) | **P3・新規**: evidence 発行と build の間に working tree が動いて 戻る ABA / 混在 snapshot が閉じていない。本 wave は evidence と build の source root を同一に 束縛して記録するに留めた。 |
| T-385 | (136) | **P3・新規**: 変異 M02 / M08 の帰属不成立と M11 の未説明 2 node を 閉じる。M02 は repo 正本 pin の照合を外すと受理集合が開く方向でなく閉じる方向へ動くため、 gate の歯を示す証拠にならない。M08 は campaign preimage から po |
| T-386 | (141) | **P3・裁定済み → 実装待ち (前提を組み替え)**: 旧選択肢 (縮約 / 陳腐化節削除 / 見送り) は [T-313] の裁定で前提が消えたため破棄。**2 件とも条件読み層へ入れる**。発火実績があるため 新しい剪定基準の対象外 |
| T-387 | (139) | **P2・裁定済み → 実装待ち**: receiptless な no-build 成功試行の正規形を受理集合へ 加える。受理集合の拡大なので既存の変更手続きを通す。孤児 `VERIFY_DONE` / `BENCH_DONE` の variant identity 束縛も同じ scope で扱う |
| T-388 | (144) | **P3・新規 (本エントリ)**: `test_pilot_resume_rejects_launch_certificate_contamination` が実 `output/` ツリーの before/after スナップショット一致を検査するため、**全走 (xdist 多並列) では他  |
| T-389 | (144) | **P3・新規 (本エントリ)**: land は「main 取り込み → 受入全走 → `dev_wave_land.py`」を要求するが、受入全走は約 5 分かかり、 2026-08-03 実測の local main の land 間隔は 3〜16 分である。並行 wave が 4 本とユーザ |
| T-390 | (145) | **P2・新規・裁定待ち**: D122 が実装した計算ノード role 実行の opt-in 経路 (`--allow-pegasus-compute-transport`、既定拒否) を撤去するか。[T-276] の 分割線維持の裁定は「使わない・それを前提に設計する」までであり、経路の撤去は含 |
| T-391 | (146) | **P1・新規 (本エントリ、段 3 A-3 / B-2)**: 条件 dispatch 表の**発火条件の逐語**と列所有を `check_docs` が検査していない。path・節 ID・ 最遅期限・row 数・allowlist を保ったまま、条件 09 の発火条件を「可能性が判明」から 「変 |
| T-392 | (146) | **P2・新規 (本エントリ、段 3 A-5 / B-3)**: 登録 reference の H1 と最初の必須 H2 の間に置いた規範 prose は、予算にも H2 検査にも 三面一致にも掛からないが、入口が exact 節を読む経路からは**到達できない**。 現に `docs/dev-wa |
| T-393 | (146) | **P1・新規 (本エントリ、段 3 A-8)**: `tools/dev_wave_land.py` は LandRequest に test / check の receipt を要求せず、 spool fold が no-op なら `check_docs` を呼ばずに ff-only lan |
| T-394 | (146) | **P3・新規 (本エントリ、段 3 B-6)**: 入口は外部 supervisor 自身へ「最初の `claude -p` spawn 前に `DW-CTX` を読む」と課すが、 `tools/dev_waves/daemon.py` / `worker.py` に読取処理は無く、prompt  |
| T-395 | (146) | **P3・新規 (本エントリ、実測。マシン固有部分は本 wave で解消)**: 生 `qsub` から計算ノードで pytest を走らせる経路に interpreter 契約が無く、 既定 `python3` が 3.10 未満のため偽赤が出る (F84 の再発)。 **マシン固有事実 (既定  |
