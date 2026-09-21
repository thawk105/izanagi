# dev-wave 1 本が login で回す検査の回数と wall — 義務イベント・出力痕跡・対応候補の 3 層と、全史監査の warm/cold の再構成 (diag-login-check-wall、2026-09-21)

台帳 ID 未起票 (ユーザー依頼文に ID なし、主題 slug)。軽量版 + 診断 wave の最小 (段 3 相談 1 本、段 5 Codex author 1 本 + 親の実機 blocker による fix 2 巡、段 6 独立 read-only レビュー 1 本、repo の実装面差分 0 = 変異 matrix 免除 (DW-S04))。
branch `worktree-diag-login-check-wall`、起点 local main `5efd69367` (開始 gate rc 0 = 2026-09-21 07:36:51 JST)、
job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-login-check-wall` (brief `s1-brief.md`、裁定 `s4-ruling.md`、codex の prompt と報告 `codex/`、probe `probe/`、実走出力 `probe-out/`)。
probe と親の解析 script は実装面 (D95) なので repo へ入れず、`verbatim/scripts.sha256` で束縛する。逐語の defang は `verbatim/NORMALIZATION.md`。

## 1. 依頼 (逐語は `verbatim/origin.md`)

login で回す 5 種の検査 (`tools/check_docs.py`、三軸語走査の権威 CLI、`tools/check_ai_provenance.py` の全史監査、fold dry-run、`find-fold-owned.py`) の実行回数と wall を、直近 landed wave 12 本の job dir から再構成し、wave あたりの合計と「契約で必須の回数」「習慣で増えた回数」を分ける。全史監査は warm 22 秒 / cold 58 秒 (T-2803 後) を前提に、実 wave 内で cold になった回数と原因 (checker sha 変更・`.gitattributes`・partition) を数える。結果は効果見積り付きの裁定パッケージ (回数を減らせる契約上の余地、順序の入替え) として insight に置き、検査の受理集合・判定・5 分上限 (D690) は変えない。診断のみ、実装 0 行。

## 2. 標本と資料

- **標本 (時点固定):** land 出力 (`land*.json` / `land-*.stdout` / `land*.log`) に `status=landed` を持つ wave のうち、**開始 gate の時刻 2026-09-21T07:36:51+09:00 以前**に着地した直近 12 本 = t2797 / branch-residue / t2817 / t2810 / t2814 / wall-decomp / paper-story-20260921 / paper-abstract / t2344 / t2803 / t2804 / t2243 (着地 09-20 23:13 〜 09-21 05:26 JST)。選択規則は「wave 内で land 出力の mtime が最大のものを代表とし、wave 間はその mtime の新しい順」。母集団 = as-of 以前に着地した landed wave 524 本、as-of 後の着地で母集団から外した wave 2 本、land 名 file 2,116 件 (landed 記録あり 651 / なし 1,465)。
- **時点固定は必須だった。** 固定前の実走では、本 wave の走行中に着地した並走 wave (`dev-wave-waiter-collect-latency` ほか) が標本に入り、走らせる時刻で標本が変わった。同じ依頼の再走が別の答えを出すため `--as-of` を足した (`verbatim/s6-fix2-A.md`)。**標本の固定時刻と、受領証 store の採取時刻 (09:27 JST) は別である** — store には as-of 後に発行された受領証も含まれ、それらは `after_as_of` で印を付けて残している (候補選択では切らない)。
- **資料:** (a) 各 wave の job dir の file (名前 + 内容の一致行で出力痕跡を判定。script 内の文字列は実走証拠にしない)、(b) 全史監査の受領証 store (`<common git dir>/provenance-audit-receipts/`、D2045 / D2192) 全 524 件 (読取 ok 524 / 不正 0。収支は「対象 5 + 対象外 433 + 曖昧 86 = 524」)、(c) commit の committer 時刻と変更 path、(d) handoff / README の記述 (実行数ではなく「記述件数」の別列)。
- **読めないもの:** 12 wave の session transcript は wave 撤去と同時に消えている。親が job dir に log を残さなかった wave では、親の走は受領証か記述でしか見えない。
- **走査の刈り込み:** job dir には repo の丸ごと複製 (`rate-source/`、`submit-tree/`、`merge3/` など) があり全走査は終わらない (親の実走で 10 分無出力 → 選別を先にして選ばれた 12 本だけ歩く形に直した、`verbatim/s6-fix1-A.md`)。`.git` を持つ dir と既定の複製 dir 名を刈るので、観測窓の開始時刻は**下界**である (`probe-ledger.md` の `pruned_dirs`)。

## 3. 契約 — 義務の発火場面と履行主体 (逐語は `verbatim/` の各 file)

回数を分けるため、検査ごとに**義務が発火するイベント**と**履行主体**を並べた。1 つの実行が複数の義務を満たすことはある (同じ検査入力なら共有可)。

| 検査 | 発火イベント | 根拠 | 主体 | 機械強制 |
|---|---|---|---|---|
| 全史 provenance 監査 | 通常 commit の後 | DW-O17 (`message → --message-file 検査 rc=0 → commit -F → full 監査`)、`docs/ai-provenance.md`「commit 前の確認」、PR-A02 | 親 | なし |
| 〃 | 親が行う merge の後 (ff / 非 ff とも) | DW-O17 | 親 | なし |
| 〃 | 受入 attempt の claim 前 | D908 (ユーザー裁定「削らず現状維持」)、`tools/dev_wave_wait.py` の `preclaim-history-provenance` | 受入 tool | あり |
| 〃 | 受入 attempt で main を取り込んだ後 (`behind > 0` のときだけ) | D908、D2129、同 `merge-history-provenance` | 受入 tool | あり |
| 〃 | land の ff-only 前 (`locked_main != 着地 tip` のときだけ) | D254、DW-O25 (480 秒) | land | あり |
| `--message-file` preflight (付帯) | commit・merge commit ごと | DW-O17 | 親 / 受入 tool / land | 受入・land 内はあり |
| check_docs | クラス 2 / 3 の完了変更 | CLAUDE.md 作業の進め方 6(c) | 親 | なし |
| 〃 | spool fragment を書いた後の commit 前 | `docs/spool/README.md` 運用 | 親 | なし |
| 〃 | land の fold 後 (生成 canonical の検査) | `tools/dev_wave_land.py` の `_validate_generated_docs` | land | あり |
| 三軸語走査 CLI | 凍結 (insight 逐語の記録 commit) の前 | DW-S07 (走査器も同節が指名) | 親 | なし |
| fold dry-run | fragment を書いた後 | `docs/spool/README.md` 運用 | 親 | なし |
| 〃 | land へ入る前 (rc=0 まで) | 同 README「land へ入る前に rc=0 まで通すこと」 | 親 | なし |
| find-fold-owned.py | **文書上の義務なし** | docs に記述なし。memory の「wave 木で別 branch を merge したときは受入前に 1 回」だけ | 親 | なし |
| (参考) repo scan invariant と影響テスト | docs commit の後 | DW-S07 (F34) | 親 | なし — login 検査ではなく焦点走 |

**D908 は受入前の全史監査 (claim 前 + 取り込み後) を「削らず現状維持」と定めている。** 本 wave の裁定パッケージは受入 tool 内の 2 本を削減候補にしない。
DW-S07 の「docs commit 後の再走」は check_docs ではなく repo scan invariant と影響テストなので、login 検査の回数に入れず別 kind (`repo_scan`) で数える。

## 4. 結果 — 3 層 (モデル上の義務イベント / 出力痕跡 / 対応候補) で数える

**この 3 層は別物である。** 義務イベントは契約文から機械的に発火させたモデルの数、出力痕跡は job dir に残った file から読めた実行の数 (下界)、対応候補は時刻近傍 (before は直前 30 分、after は直後 30 分の最近傍、未使用のものから順に割り当て) で結んだ候補である。**対応候補は履行の証明ではなく、対応が付かない義務は「未対応」、対応が付かない実行は「理由未同定」と呼ぶ。**

| 義務イベント (モデル) | 発火数 | うち対応候補あり | 主体 | 機械強制 |
|---|---:|---:|---|---|
| `check_docs_before_commit` | 93 | 17 | 親 | なし |
| `full_audit_after_commit` (通常 65 + 親 merge 22) | 87 | 23 | 親 | なし |
| `repo_scan_rerun_after_docs_commit` (参考・login 検査ではない) | 77 | 16 | 親 (焦点走) | なし |
| `axis3_before_freeze` | 50 | 9 | 親 | なし |
| `fold_dry_before_fragment_commit` | 50 | 10 | 親 | なし |
| `full_audit_acceptance_preclaim` | 23 | 22 | 受入 tool | あり |
| `full_audit_land` (確定 12 + 到達不明 1) | 13 | 12 | land | あり |
| `check_docs_land` (確定 12 + 到達不明 1) | 13 | 0 | land | あり |
| `fold_dry_before_land` (wave ごと 1、attempt ごとではない) | 12 | 3 | 親 | なし |
| `check_docs_after_acceptance_merge` | 6 | 0 | 親 | なし |
| `full_audit_acceptance_merge` | 6 | 6 | 受入 tool | あり |

- `check_docs_land` の対応 0 は**実行 0 ではない**。`tools/dev_wave_land.py:5047-5073` は check_docs の stdout / stderr を PIPE で回収し、非 0 のときだけ例外へ載せるので、成功時の出力は job dir に残らない。一方 `check_docs_after_acceptance_merge` (6 件) は**親**の義務で、この説明を流用できない — 未対応のまま残る。
- `check_docs_before_commit` を「完了変更 commit 全件 (93)」に発火させるのは段 4 裁定 #2 のモデル前提である。CLAUDE.md 6(c) の「完了変更」を commit 単位と読んだ結果で、契約文が commit 単位と明言しているわけではない。
- 出力痕跡の下界 (12 wave 合計): 全史監査 23、`--range` 監査 1、`--message-file` preflight 11、check_docs 17、三軸語 10、fold dry-run 14、**find-fold-owned 0 (文書上の義務 0・痕跡 0・wall 未観測)**、(参考) 焦点走 27。
- handoff / README の記述件数 (実行数ではない): 全史監査 20、preflight 19、check_docs 40、三軸語 10、fold dry-run 13。
- 理由未同定の実行 (義務に対応候補が付かなかった痕跡): 三軸語 1、fold dry-run 1、`--range` 監査 1、(参考) 焦点走 11。**これは「習慣で増えた回数」の上限ではない** — 対応付けは時刻条件を満たす実行を義務へ吸収するので、習慣的な追加走は義務側に吸収されうる。

**依頼の「契約で必須の回数」と「習慣で増えた回数」について、確定できたこと / できないこと。**

- **モデル上の義務イベントは 12 wave 合計 353 件 = 1 wave あたり 29.4 件** (全史 129 = 10.75/wave、check_docs 112 = 9.33/wave、三軸語 50 = 4.17/wave、fold dry-run 62 = 5.17/wave)。**これは現行モデルのイベント数であり、必要な独立実行数ではない** (共有可の義務、到達不明の条件付き 2 件、wave 単位の義務が混じる)。
- **観測できた実行は 12 wave 合計 98 = 1 wave あたり 8.2** (全史は対応候補を持つ現存受領証 57 件 = 4.75/wave、check_docs の log 17 = 1.42/wave、三軸語 10 = 0.83/wave、fold dry-run 14 = 1.17/wave)。**単位が混在している** (受領証と log)。check_docs・三軸語・fold dry-run は log を残した wave でしか見えない下界である (いずれかの検査 log を残した wave は 11、check_docs の log を残した wave は 4)。
- **「習慣で増えた回数」は本資料では確定できない。** 理由未同定の実行 3 件が上限にならないこと (上記)、log を残さない wave の痕跡欠落を実行なしと読めないこと、受領証が同 tip・同 partition で上書きされること、の 3 つが効いている。
- **同様に「実行が契約に届いていない」とも確定できない。** 全史監査は義務 87 件に対し親の痕跡 23 件・親に対応した受領証 18 件だが、上書き・非保存・対応付けの制限を排除できていない。**したがって本 wave は「commit 群の後に 1 回にまとめている」という運用実態を主張しない。** 契約文 (DW-O17 の通常列) を commit ごとと読むか commit 群の後に 1 回と読むかは、実態の証明とは別に**明文化すべき論点**である (§9 の択 G)。

## 5. 全史監査の warm / cold の再構成 (`verbatim/probe-receipts.md`)

- 受領証 store 524 件 / 20 partition (partition = checker sha + config + 継承 env + schema)。partition 5 つが上限 64 件に達している (剪定の可能性の印。剪定は祖先優先 → mtime 順なので「直近 64 件」ではない)。
- **何らかの対応候補を持つ現存受領証は全 wave 横断で 57 件 (unique)。wave 別の行は 62、延べ対応は 63 (親 22 / 受入 claim 前 23 / 取り込み後 6 / land 12)。これは排他的な主体別実行回数ではない** — 1 受領証が複数の対応候補を持つ (例: 受入の取り込み後監査と次 attempt の claim 前監査に同じ受領証が対応する、`probe-ledger.md:2753`)。**親に対応した unique 受領証は 18 件 (再構成 warm 12 / cold 5 / 不能 1)。**
- unique 57 件の再構成は **warm 42 / cold 13 / 再構成不能 2**。1 wave あたり 4.75 件。**これは実行時点の warm/cold ではなく、現存 store からの再構成である** (§12)。
- **wave 帰属は確定ではない。** 対応付けは tip が log に現れない場合 ±120 秒だけで親の log に結ぶ (`probe/login_check_event_ledger.py:602`)。実測の衝突例: t2814 の同じ log に 2 件の受領証 (`3934e292…` と `6dae18be…`) が対応し、branch-residue 側でも同じ log に両方が対応する (`probe-ledger.md:1483,1488`)。paper-abstract の land 受領証 `b5c85a8d…` が wall-decomp の親 log にも対応する。wave を跨ぐ曖昧さは行ごとの `ambiguous` では捕まらない。
- **T-2803 (受領証の属性 fingerprint の改訂) の着地 09-21 00:12 が境界である。**

| 区間 | 対応候補を持つ受領証 | warm | cold | 再構成不能 |
|---|---:|---:|---:|---:|
| 00:12 より前 | 17 | 3 | 12 | 2 |
| 00:12 以降 | 40 | 39 | **1** | 0 |

- 00:12 以降の唯一の cold は t2797 の 04:11:50 (tip `a6ac2c54c`、親の記録 commit 後の監査)。**観測条件**: この受領証の partition の checker は旧版 `7c02fb2d` であり、同 wave は 04:15:24 に main を取り込んで以後 (04:21:51、04:40:50) は warm。**仮説**: wave 木が main 未取り込みで旧 checker のまま走ったこと。**ただし cold の比較差分は `attributes` / `config` / `inherited` で checker 差ではないので、「旧 checker だから cold」という因果は本資料では証明していない。**
- **cold の比較差分 (原因の材料、帰属ではない。1 件が複数 key を持つ)**: 00:12 前の cold 12 件では `attributes` (`.gitattributes` 由来の指紋 = T-2803 が直した項目) 8 件、`environment.checker` 5 件、`environment.schema` 1 件、`environment.config` 8 件、`environment.inherited.*` 9 key × 8 件 = 72 key。00:12 以降の 1 件は `attributes` 1 + `config` 1 + `inherited` 9 key。**比較相手は「直近の祖先受領証 1 件 (partition 不問)」なので、相手が land 環境や別 shell なら config / inherited に差が出るのは当然である。** D2192 が束縛する他の key (`cab_hits`、`registry_manifest`、`policy`、`scope_epoch`、`implementation_epoch`、`object_format`、`repository`) はいずれも差 0 件だった。
- 直接計測 (`/usr/bin/time -v`、t2803 の job dir、3 測定): cold 112.51 秒 (12,061 件、実装 commit 後)、47.41 秒、54.09 秒。**前提値の cold 58 秒は、混雑した login では 112 秒まで伸びた実測がある。**

## 6. wall の出所 (`verbatim/probe-ledger.md` の wall 表。**件数は出力行数であり測定回数ではない**)

| 出所 | 出力行数 | 値 (最小 / 中央 / 最大) | 注 |
|---|---:|---|---|
| 直接計測 (`/usr/bin/time -v` / start-end stamp) | 6 | 47.41 / 54.09 / 112.51 秒 | **実体は 3 測定** (`.time` と `.stdout` の 2 行ずつ)。すべて t2803 の全史監査 |
| 開始・終了が別 file で裏付けられた区間 | 43 | 4 / 75 / 1,165 秒 | 親の全史監査 41 / 46 / 50 / 63 / 75 秒 (5 件)、fold dry-run 4〜11 秒 (11 件、中央 5 秒)、焦点走 57〜1,165 秒 |
| mtime 代理区間 (間に他の処理を含みうる) | 69 | 0 / 38 / 1,070 秒 | 区間の両端 file 名は出力に併記 |
| 前提値 (warm 22 / cold 58) | 366 | 22 / 22 / 58 秒 | **未対応の受領証と wave 窓の重複を含む**。実行回数として足せない |
| 未観測 | 112 | — | 義務に対応候補が無く痕跡も無い分 |

検査ごとの wall の出所:

| 検査 | 直接計測 (本 wave、login 1 回ずつ) | job dir の区間 | 未観測の理由 |
|---|---|---|---|
| 全史監査 | — (t2803 の 3 測定 = 47.41 / 54.09 / 112.51 秒) | 親 41〜75 秒 (5 件)、受入内は started → 受領証 mtime の代理区間 | 受領証は発行完了時刻で、開始時刻が残らない |
| check_docs | **30.30 秒** (user 28.02、RSS 288,496 kB = 約 295 MB、load 3.50 → 18.25) | なし (log に所要が出ない) | log は判定結果だけを持つ |
| 三軸語走査 CLI | **45.27 秒** (user 6.25 / sys 10.17、RSS 1,183,384 kB = 約 1.21 GB、load 23.77 → 34.70) | なし | 同上 |
| fold dry-run | **0.33 秒** | 4〜11 秒 (中央 5 秒、`.err` が空の 11 件) | 区間には process 起動が入り、直接計測と一致しない |
| find-fold-owned | — | なし | 痕跡 0 |

三軸語走査の rc=1 は main に着地済みの既存 4 file の hit による (D2120 項 2 (d) の既知の帰結)。この帰属は本 wave の走査 report (`verbatim/axis-scan-*.log`、job dir) の `conjunction_hits` の path で確認した。

## 7. 検査 log の出力間隔 (束ねの材料。`call 間隔` 表)

12 wave 合計 53 区間 (20 分以内のものだけ): 最小 0 / 中央 88 / 最大 1,156 秒。20 秒未満 9 件、60 秒以上 31 件。

| 群 | 区間数 | 最小 / 中央 / 最大 |
|---|---:|---|
| 続けて呼んでいる 2 wave (t2810 + t2814) | 22 | 0 / 44 / 848 秒 |
| 残り 10 wave | 31 | — / 95 / — |

- **この間隔は親の手番の測定ではない** (親の思考・子の起動・待ちが混ざる)。平均や「親手番 N 分」は出さない。
- **同一実行の別出力を含む。** t2810 の 0 秒は `three-axis-scan-1.log → three-axis-scan-1.stderr` で、検査どうしの境界ではない。

## 8. 効果の見積り (すべて条件付きモデル。実測の前後比較ではない)

前提 model = `22 × warm + 58 × cold` (出所 = T-2803 entry 1769 の E-2)。fold dry-run は job dir の区間の中央値 5 秒、check_docs は 30.30 秒、三軸語は 45.27 秒 (いずれも本 wave の login 1 回ずつの測定)。

- **現行 (T-2803 後) の全史監査、全 warm を仮定**: 1 wave あたり 4.75 回 × 22 秒 = **104.5 秒 (1.74 分)**。
- **標本の観測 mix (warm 42 / cold 13、不能 2 は除外) を使うと**: (42 × 22 + 13 × 58) / 12 = **139.8 秒 (2.33 分) / wave**。
- **00:12 前の regime を同じ回数に当てると**: 判定可能 15 件のうち cold 12 件 = 80 % → 4.75 × (0.2 × 22 + 0.8 × 58) = **241.3 秒 (4.02 分)**。全 warm との差は **136.8 秒 (2.3 分)**。不能 2 件を warm と数える別モデルでは 224.2 秒 (3.74 分)、差 119.7 秒 (2.0 分)。**T-2803 の効果は「同じ回数を仮定したモデルの差」であり、前後の実測比較ではない。**
- **モデル上の義務イベントを全部独立に実行した場合**: 10.75 × 22 + 9.33 × 30.30 + 4.17 × 45.27 + 5.17 × 5 = **733.7 秒 (12.2 分) / wave**。
- **観測できた実行を全 warm で換算すると**: 4.75 × 22 + 1.42 × 30.30 + 0.83 × 45.27 + 1.17 × 5 = **190.9 秒 (3.18 分) / wave** (比 3.8 倍)。観測 mix を使うと 226.2 秒 (3.77 分)。
- 1 wave の所要は平均 154 分 (entry 1776) なので、上の換算値は **2.1 % (190.9 秒 / 154 分) 〜 2.4 % (226.2 秒 / 154 分)** に当たる。**ただし 154 分は別標本の平均 (共通 wave は t2344 / t2803 / t2804 の 3 本) なので、この比はモデル上の目安であり、現状比率の実測ではない。**
- 効くのは (a) cold を作らないこと (T-2803 で済んだ、上記の差 2.0〜2.3 分 / wave)、(b) log 出力の間隔を詰めること (§9 の A)、(c) 契約文の読みを明文化すること (§9 の G) である。回数そのものを削る余地はモデル上でも数分に留まる。

## 9. 裁定パッケージ (実装しない。択一と推奨)

**D690 (5 分) と DW-O25 (480 秒) はいずれの択でも変えない。規律 2 を緩めない。** ただし**「受理集合不変」と言えるのは A / C / D / H だけ**である — B と G は DW-O17 の停止位置と義務そのものに触るので、解釈確認では済まない別裁定になる。

| # | 択一 | 推奨 | 契約・規律への触り方 | 効果 (条件付き) |
|---|---|---|---|---|
| A | 記録 commit の前後の検査 (check_docs → 三軸語 → fold dry-run → `--message-file` → commit → 全史監査) を **1 本の shell script に束ねる** / 1 検査 1 call | **束ねる** (reference への手順化) | DW-O17 が既に許容 (「複数 preflight と commit を同じ shell で行うなら先頭を `set -e`」)。検査 rc を pipe へ渡さない (F37) を守れば受理集合は不変 | 続けて呼んでいる t2810 + t2814 の 22 区間は中央 44 秒、残り 10 wave の 31 区間は中央 95 秒。**削減できるのは log 出力の間隔だけで、検査の wall は減らない。区間には親の思考・子の起動・待ちが混ざるので削減量は確定していない** |
| B | 親の commit 後全史監査を **中間 commit では省き**、受入 tool の claim 前監査を権威とする | **現行維持** | DW-O17 の通常列の**停止位置と義務**を変える (受理集合不変とは言えない)。D908 は受入側の 2 本を守る裁定で親側は射程外だが、同じ論点 (取り込みが履歴を新設する) に触れる。親の受領証が受入 claim 前監査を warm にする連鎖 (§5) も壊しうる | 省ける回数は中間 commit 数 − 1。全 warm なら 22 秒 × その数 (1 wave 2〜4 分未満) |
| C | fold dry-run を **fragment commit 前と land 前で共有** (検査入力が同じと確認できる場合だけ) / 別走 | どちらでもよい | `docs/spool/README.md` の 2 義務。入力が変わった後の省略は不可 | 1 走 5 秒 (区間中央)。**観測データからは削減回数が確定していない** |
| D | 三軸語走査の発火を **凍結イベントの定義として明文化**する (回数の削減案ではない) | 記述の明確化のみ | DW-S07「凍結前」 | 1 走 45.27 秒 (RSS 約 1.21 GB)。観測は 1 wave 0.83 回 |
| E | land 実行時の env を login と揃えて受領証 partition を共有するか | **並走 wave `dev-wave-provenance-cold-diag` へ参照** | Git の config・attributes 入力を変えるため正しさ防壁に触れる | T-2803 後は land 側も warm (12 件中 9 warm) |
| G | **契約文の読みを明文化する** — DW-O17 の通常列を「commit ごと」と読むか「commit 群の後に 1 回 (受入前に必ず 1 回)」と読むか | **ユーザー裁定へ** (B と一体で扱う) | **義務の数え方の確定であって受理集合不変ではない。** 後者の読みを採ると停止位置と被覆が変わるため、B と同じ裁定の一部として扱う。本 wave は運用実態 (どちらで運用されてきたか) を証明していない (§4) | 明文化そのものの wall 効果は 0 |
| H | wave 撤去後も検査の回数・wall を再構成できるよう、**検査 log を job dir に残す**扱いを記録に残す | 観測限界の記録で足りる (新契約は提案しない) | 新しい検査・手順の追加は依頼の scope 外 | 12 wave のうち、いずれかの検査 log を残したのは 11 wave、check_docs の log を残したのは 4 wave。診断の再現性だけに効く |

**削除した択:** `find-fold-owned.py` を契約に載せる案は、痕跡 0 (文書上の義務も 0) から新契約を提案する形になり材料不足のため取り下げた (DW-G03 の独立 2 例にも足りない)。

## 10. 段 3 相談・段 4 裁定・段 6 レビューの対応 (`verbatim/s3-consult-A.md`、`verbatim/s4-ruling.md`、`verbatim/s6-review-A.md`)

- 段 3 相談 A (read-only codex 1 本): 所見 18 件 (must-fix 14 / should 1 / refuted 1 / 判定不能 2)。段 4 で全件採用し、親の当初の枠 (P1 固定回数・P2 親手番の平均・P3 cold 原因 3 分類) を撤回した。
- 段 5 の Codex author 1 本が probe 2 本を実装し、**親の実機で 2 件の blocker を踏んで fix 2 巡** (DW-O16 の「親の実機 blocker は別枠」): (a) 全 landed wave 527 本の job dir を走査して終わらない → 選別を先に、複製木を刈る、(b) 走行中に並走 wave が着地して標本が動く → `--as-of` で時点固定。
- 段 6 レビュー A (read-only codex 1 本): 所見 16 件 (must-fix 12 / should 1 / nit 1 / refuted 2)。**全件を本 v2 へ反映した。** 主な反映: cold 7 割の算術 (250 秒 → 241.3 秒 / 224.2 秒の 2 モデル)、受領証の単位 (unique 57 / wave 別行 62 / 延べ 63、親 unique 18)、wave 跨ぎの対応の曖昧さ、「習慣増ほぼ無い」「commit 群の後に 1 回」の撤回、条件付き義務 2 件と wave 単位義務の明示、旧 checker の観測と仮説の分離、wall の件数 = 出力行数 (直接計測は 3 測定)、call 間隔の群比較の訂正 (0〜29 秒 → 22 区間 0 / 44 / 848 秒、他群中央 95 秒)、効果見積りの条件付き化と 2 % の異標本注記、RSS の単位 (288,496 kB = 約 295 MB、1,183,384 kB = 約 1.21 GB)、fold 7 秒 → 区間中央 5 秒、択 F の削除と D / E / H の位置づけ変更、相談所見の内訳 (19 → 18)。

## 11. 検査と受入 (実施状況)

- 記録 commit 前 (この節を書いた時点): 三軸語走査 = defang 前 hit 5 件 (うち本 wave の `verbatim/probe-ledger.md` 1 件) → 可逆 defang 9 箇所 (`verbatim/NORMALIZATION.md`) → 再走で hit 4 件 (main 既存のみ、rc=1 は既知の帰結)。`git diff --check` rc=0。
- check_docs / fold dry-run / 全史監査 / 受入全走 / land: **未実施** (記録 commit の直前・直後に実走し、結果はこの節へ追記する)。

## 12. 言わないこと (限界)

- **受領証の件数は実行回数ではない。** 同じ tip・同じ partition の再走は同じ file を上書きし (実測例: t2243 は親の log 終端 22:49:39 の後、同じ tip の受領証が受入の 22:54:10 に対応する)、`--range` 監査は受領証を発行しない (別 kind として数え、full へ足さない)。件数は下界である。
- **warm / cold は現存 store からの再構成**であり、実行時点の判定ではない。「その時点で候補が存在した」は候補受領証の mtime でしか近似できず、剪定 (partition あたり 64 件、祖先優先 → mtime 順) で消えた候補は復元できない。3 値 (候補あり / 候補なし / 再構成不能) で出し、cold を確定値と書かない。**旧 checker の版で走った監査も現行の `_receipt_prefix` 条件で再構成しており、旧実装そのものの挙動は証明しない。**
- **cold の「原因」は比較差分**であって帰属ではない。比較相手は直近の祖先受領証 1 件 (partition 不問) で、相手が別環境なら config / inherited に差が出る。D2192 の他の束縛 key は差 0 件だった。
- **wave 帰属と主体は確定ではない。** 対応付けは時刻近傍 (±120 秒 / 30 分窓) で、同じ log に 2 件の受領証が対応する例、別 wave の親 log に対応する例が実測で出ている。commit 所属 (tip がどの wave の commit 集合にあるか) と、監査を呼んだ主体は別の列で持つ。既存 main tip を監査する受入 ref 走や amend で到達不能になった tip は「対応不明」に残る。t2817 は受入の 8 監査すべてに対応が付いた (親の当初の仮集計では 7 件の受領証しか見えていなかった)。
- **受入 attempt の到達判定は proxy である。** claim 前監査の到達は `started.txt` の存在、取り込み後監査の到達は `tip-after ≠ tip-before` で近似しており、投入前の失敗や tool 外の merge を排除できない。
- **義務と実行の対応は候補**である。対応が付かない義務は「未対応」、付かない実行は「理由未同定」であり、いずれも習慣・不履行の証明ではない。
- **env の特徴 (`env_kind`) は主体・実行ノードの確定ではない。** land 環境の override 全 key 一致を `land-like`、`GIT_*` override 無しを `login-like` と呼んでいるだけで、どの process が走らせたかは決めていない。
- **親の手番の平均は出さない。** log 出力間隔には親の思考・子の起動・待ちが混ざり、同一実行の stdout / stderr の対も含む。
- 観測窓は複製木を刈った下界である。刈った木に古い file があれば開始時刻は実際より新しくなる。
- entry 1776 の未分類残差 28 % と本 wave の換算値は重なりうるが、「うち」とは言えない (標本の共通 wave は 3 本)。同じ理由で「login 検査は全体の 2 %」もモデル上の目安である。
