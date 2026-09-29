# [T-2273] [T-2560] 受入 shard-0 の律速 (b) = 発行 subprocess を縮めた — 発行 child の CPU の 99 % を占めていた三軸走査の正規表現照合を、軸 literal の出現近傍の窓に局所化した (report の bytes は不変)。発行 child は約 86 秒 → 約 32 秒。実受入の隣接 3 対で W_0 は 16.5〜40.5 秒 (対率中央値 9.1 %) 縮み、事前登録の区分 (ii) 小さい改善として land する。5 分上限は B の W_max 中央値 276.1 秒で達成 (2026-09-29)

wave `dev-wave-t2273-issue-subprocess` (branch `worktree-dev-wave-t2273-issue-subprocess`)。依頼の逐語は `verbatim/T-2273-origin.md`、判断は本 wave の決定 (decisions fragment)。段 1 brief・段 4 / 6 裁定・Codex 子の prompt と出力・開始 gate・E1 の賛否相談は `verbatim/`、計測の集計は `analysis/`、変異は `mutation/`、投入台帳と計測 tip は `runs/`。
標本の時点 = 開始 gate 2026-09-28 07:53 JST (HEAD = local main `51f896352`)。Pegasus の保守 (9/28 09:00〜21:00) を挟み、計測は 9/29 に行った。

## 結論 (最初に読む)

1. **律速の実測:** 受入の L node の単独走を py-spy で採ると、発行 child (約 86 秒) の CPU の 99 % が `s8b_holdout_freeze.search_repository` で、その 54 % が `_scan_one` の正規表現 search 1 行、19 % が共通 literal の `in` 判定だった (§2)。
2. **実装:** D512 (report の canonical bytes を 1 bit も変えない係数削減) の枠内で、軸 literal の各出現の近傍の窓だけを同じ compiled 式で search し、共通 literal の判定を 1 走査内で text ごとに 1 回にした (§3)。受理集合・report・走査回数 (観測点) は不変。再 profile で発行 child は 4,313 → 1,583 sample (約 86 → 約 32 秒、36.7 %)。
3. **事前登録の land 判定: 区分 (ii) = 小さい改善として land。** 有効 3 対の shard-0 W_0 の対差は +32.333 / +40.457 / +16.512 秒 (3 対すべて正)、対率 9.1 / 13.5 / 5.6 %、中央値 9.1 % (< 10 %)。E1 は系列途中で erratum E1' (shard-0 の割付一致に限定) にした (§6、W を見る前に固定)。旧 E1 (3 shard 全一致) での判定は `undetermined`。
4. **5 分上限 (別判定): 達成。** B の W_max 3 走は 349.375 / 259.260 / 276.108 秒で中央値 276.108 秒 ≤ 300。ただし 02-B は shard-1 が 349.4 秒で最遅になり 300 秒を超えた (§7)。
5. **縮みの中身:** B では shard-0 の最長 test (`test_t080_failed_launch_preserves_receipt_refusal`、共有発行 key の builder を待つ) が A 185〜189 秒 → B 104〜112 秒と約 80 秒縮んだが、最も長く占有された worker がその test 以外で決まるようになり (O_max − L が A 21〜30 秒 → B 36〜74 秒)、W_0 の縮みは 16〜40 秒に留まった。
6. **正しさの側は閉じている。** 変異 final は 8 件すべて期待と一致 (M1・M2・M3・M5・M7 KILLED、M4・M6 は出力等価な性能変異の診断 pin、P0 SURVIVED)。焦点走 4,058 passed / 失敗 0。凍結の再発行は不要 (DW-O09、§3)。

## 1. 依頼と不変条件

依頼 (逐語 `verbatim/T-2273-origin.md`): 受入 shard-0 の次の律速 (b) 発行 subprocess を縮める。対象は D2253 項 4 の診断で共有発行 key の builder に残る発行 child 約 87 秒 (CPU 支配)。land 条件は (a) と同じ隣接対の形で測る前に事前登録し、W_1 と pre も補助量として見る。受領証の検査内容は緩めない (規律 2)。実装は Codex author (D95)。計算は job Elapse の実測単価で見積もり、検査込み 2 node 時間以上ならユーザー確認。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化は scope 外。

守ったこと: 受領証・holdout 検査の受理集合と report の canonical bytes は不変 (D512)。発行 child 内の `search_repository` の呼出し回数と順序 (観測点) は変えていない。呼出しを跨ぐ cache・production の最適化無効化 knob・環境変数・gate・台帳は足していない。

## 2. 律速の実測 (段 1 前、`analysis/profile-summary.md`)

計算ノードで `test_t080_failed_launch_preserves_receipt_refusal` (受入の L node、active_v2 key の builder を待つ) を単独走し、`py-spy record --subprocesses` で発行 child を含めて採取した (request 32525.nqsv、tree = local main `51f896352`)。

- 発行 child 4,313 sample (50 Hz ≈ 86 秒、D2253 の約 87 秒と一致) の **99 % が `s8b_holdout_freeze.search_repository`**。draft 3・validate 3・finalize 4 (validate を内包)・verify 1・gate_check 2 の約 13 回の走査が、1 回 ≈ 6.6 秒ずつ積み上がっていた (回数は call graph と総時間からの見込みで、profile は呼出し回数を数えていない)。
- 走査の 76 % が `_scan_one`。行別の自己時間は正規表現 search 1 行 (2,311 sample、54 %)、共通 literal の `in` 判定 (806、19 %)、軸 literal の `in` 判定 (154、4 %)。file の読込み・decode は 11 %。
- fixture は計算ノードの /tmp 上なので、D512 が実 repo で測った律速 (共有 FS の metadata 遅延) ではなく正規表現照合が支配していた。

## 3. 実装 (commit `56f8e97c0` + fix `ad8c91ecf`、変更 2 file)

`orchestrator/campaign/s8b_holdout_freeze.py` の `_scan_one` だけを D512 の枠内で係数削減した (Codex author、子 branch `author-t2273is-impl` / `fix-t2273is-impl-1` から所有 path 限定 patch で統合)。

- **局所化 search:** 軸の literal L (既存 `_derive_required_literal` の 1 要素 mapping 導出、非 None のときだけ) の各出現 p を `find(L, p + 1)` で重なりも含めて列挙し、同じ compiled 式を窓 `[max(0, p + len(L) − W), min(len, p + W))` で search する。W は stdlib `sre_parse.parse(expr).getwidth()` の最大値。helper が非 None を返す文法 (key は literal、値は `.` 以外のメタ文字なし) では全 match が L を含み長さ ≤ W で、anchor・lookaround が無いので、真偽は全文 search と同じ。L が None・非 exact str の式は従来の全文 search。
- **共通 literal の判定:** 1 回の `search_repository` 内で (literal, rel) ごとに 1 回。cache は既存の `_ScanMemo` (texts の identity 束縛と内容変化拒否) の後でだけ再利用し、値に判定した text object を持って `is` で一致するときだけ使う (段 6 A1 の fix)。
- **変えていないもの:** 列挙・open・read・decode・免除・例外の型と文言・report の全 field。`_derive_required_literal` の呼出し回数 (1 走査 12 回)。t080_freeze_migration.py・発行 fixture・driver。
- **凍結との関係 (DW-O09):** `holdout_freeze.v2.g1.json` は generator として変更前の sha256 `5a8798d4…` を記録するが、v2 の照合は frozen_at_head の blob (s8b_ratified_freeze.py の V1b) で worktree を見ない。v1 の worktree 照合は HELD 中で、記録値 `1910fff…` は既に現物と不一致。再凍結・再発行は要らない (`verbatim/pin-closure.md`)。
- **test (`orchestrator/tests/test_s8b_holdout_freeze.py`、新設 8 node):** 単軸の等価性 5 parametrize (plain 形式が末尾で終わる・JSON 形式で match 開始が L より前・自己重なり・値側の任意 1 文字・8192 byte 以降、それぞれ独立な全文 `re.search` と `_reference_scan_one` の report bytes に一致)、共通判定 memo の key (literal と rel)、proxy の背後書換え後の再判定、共通判定の発火回数。既存の発火回数の番人 (:427 の 5 回、三段分離 fixture の 0 / 5 / 9 回と reference 3 回) は数える単位を「局所化 helper に届いた (軸, text) 候補数」に移して数値を保ち、三段分離 fixture に「局所化だけを外した段」を足した (D513)。

## 4. 段 2〜6

- 段 2 plan (`verbatim/s2-plan-*`)、段 3 相談 2 本 (レンズ A 正しさ・等価性・既裁定との整合、レンズ B 過剰・効果・計測設計、どちらも修正後 GO)。A は窓式の等価性に反例を構成できず、右端 off-by-one を確実に殺すには単一 alternative の単軸 fixture が要る、共通判定を外す変異は候補数では殺せない、`rel` だけの cache は「literal A 不在 → literal B 存在」の順で殺す、を指摘。B は MAXREPEAT の分岐と注入 test は現行 helper の受理文法では到達しないので削れる、効果見込みは上限であって実測ではない、実装後に同じ単独 profile を取り直してから系列へ、を指摘。
- 段 4 裁定 (`verbatim/s4-ruling.md`): MAXREPEAT の分岐は置かない (幅が飽和しても窓は全文に広がるだけで正しい)、共通判定の発火回数の番人を足す、局所化を独立 helper にして test だけが全文 search に差し替える (production に knob を足さない)、走査回数を減らす案 (validate の内包重複・draft の verifier 走査の共有) は観測点を減らすので採らない。変異 M1〜M6 と P0、計測の事前登録 (再 profile の 70 % 条件、隣接 3 対、land 区分 i / ii / iii、補助量、計算量) を固定。
- 段 5: 実装子 1 本 (所有 2 file) と、計測 probe の移植子 1 本 (前 wave の Codex author 製 probe の job dir・slug・land 区分の差し替え。前 wave の系列を読み取り専用で集計し直して値と区分 `land` を再現)。
- 段 6 (`verbatim/s6-ruling.md`): レビュー 2 本。B (過剰・削除) は所見なし GO。A は修正後 GO で 3 件 — A1 (must-fix): `MappingProxyType` の背後 dict が書き換わると、新しい共通判定 cache が別の式の走査へ古い判定を再利用して hit を落とす (production の `search_repository` は背後 dict を外へ出さないので到達しないが、D512 の内容変化拒否の契約を別の式へ広げていた) → text object の identity で再利用を絞る fix と正例 test、変異 M7 を追加登録。A2 (str subclass の text で `find` と `in` が食い違いうる) は旧実装の軸 prefilter も subclass の `__contains__` に依存しており同型、production の text は decode 由来の exact str なので refuted。A3 (`sre_parse` は 3.11 から非推奨) は実行環境が 3.10 固定で、壊れても import 失敗の fail-closed なので scope 外。
- 焦点走 (tip `ad8c91ecf`、34 file = 変更 test file 1 + 変更 module を参照する consumer test 30 + DW-O26 の inventory 4 群のうち consumer に含まれない 3): 4,058 passed / 24 skipped、失敗 0 (skip は既存の growth hold・toolchain 前提・Python 3.11 前提)。Elapse 313 秒。
- 全史 provenance: 13,125 件 (実装後) / 13,126 件 (fix 後)、新規違反なし。
- 自己汚染 (growth hold を迂回せず `search_repository(root, files=...)` で): 変更 2 file の rr80 / rr20 conjunction 0 件。既知陽性 file `orchestrator/campaign/backoff_sweep.py` を加えた別走で陽性対照 1 hit。

## 5. 変異 (`mutation/`)

独立 clone (D1009) の固定 commit `ad8c91ecf`、`tools/mutation_worktree.py --runner-mode dispatch`、対象 `orchestrator/tests/test_s8b_holdout_freeze.py`。期待 node は初回 dispatch probe (全件 SURVIVED 期待) で観測し、登録と照合してから final を走らせた。final は baseline PASSED、8 件すべて期待と完全一致。

| ID | 変異 | 赤になった node (final = probe の観測) | 分類 |
|---|---|---|---|
| P0 | docstring の 1 語 | — | SURVIVED (期待どおり) |
| M1 | 窓右端 `p + W` → `p + W − 1` | 単軸 plain 形式 4 parametrize を含む 10 node (最長 alternative で一致する既存 fixture も落ちる) | KILLED |
| M2 | 窓左端 → `p` | 単軸 JSON 形式と既存 `test_all_three_canonical_encodings_are_detected` の 2 node | KILLED |
| M3 | 次の出現 `find(L, p + 1)` → `find(L, p + len(L))` | 自己重なりの単軸 1 node | KILLED |
| M4 | 局所化 helper を全文 search にする | 三段分離 fixture 5 parametrize と :427 の番人 (6 node) | 診断 pin (出力等価、DW-M03 により kill に数えない) |
| M5 | 共通判定 cache の key を rel だけにする | memo key の test 1 node | KILLED |
| M6 | 共通判定 cache を外す (軸 pass ごとに判定) | 共通判定の発火回数の test 1 node | 診断 pin (出力等価) |
| M7 | cache 再利用の identity 照合を外す | proxy 背後書換えの test 1 node | KILLED |

- kill に数えるのは report と受理集合が変わる M1・M2・M3・M5・M7 (5 件)。M4・M6 は D513 の発火回数の番人の検出力として別枠 (段 6 裁定の erratum)。
- 走行の経緯: 保守明けの queue 滞留で probe の M2 が 2 回 queue 待ち打ち切り (rc=16、未起動) → `--resume` で完走。final は待ち上限の整合検査・evidence 不在の resume 不可・Lustre の EINTR で 3 回止まり、4 回目 (新しい scratch・出力 path) で完走。どれも変異の結果ではない。

## 6. 隣接対の実受入

測定形 (段 4 事前登録、`verbatim/s4-ruling.md`): A = `51f896352` (測定準備時の local main、clean worktree `t2273is-base-a`)、B = `ad8c91ecf` (A + 実装 2 commit、wave 木)。`IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py` の直接投入、順序 A,B / B,A / A,B、門番 = 他 session の受入 leader ≤ 1 ∧ load1 ≤ 60。集計器は前 wave の Codex author 製 probe の移植 (`verbatim/probe-source.md`)。E1 の入力: 受入と同じ関数で取った login collection は A 27,971 / B 27,979 件、B only = 新設 8 node ちょうど、A only = 0 (`runs/expected-added-nodes.json`)。

- **erratum E1' (2026-09-29 07:29 JST、01-A・02-B 完了後、W を親が閲覧する前に固定):** 03-B の投入前検査が旧 E1 「A/B 共通 node の 3 shard 割付の完全一致」の不成立で止まった。shard-0 の共通 node 4,302 件は完全一致、新設 8 node はすべて B の shard-1 で、shard-1 / 2 の間で分割が変わった (A 11,427 / 12,242 件、B 10,849 / 12,820 件)。A/B の木で決まる決定的な性質で、残る対も同じ理由で不成立になる。codex に賛否 2 立場で諮り (`verbatim/s6-e1-*`)、E1 の割付一致を「shard-0 の共通 node 集合の完全一致」に限定し、旧 E1 の判定を並記、各走の 3 shard の host 重なりを報告、W_1・W_2・pre の対差を実装効果と呼ばない、を付帯条件として採った。集計器の改訂は Codex author (sha256 `b8a0f097…` → `50e1cc79…`)。反対側の論拠 (系列開始後の基準変更、shard-1 / 2 の構成差が共有 FS 等を通じて W_0 に間接的に効きうる) は §8 の限界に残す。
- **待ち上限の延長 (運用):** Pegasus 保守明けの queue 滞留 (gen_S QUE 70〜88) で温め B が 2 回 queue 待ち打ち切り (child 未起動) になったため、温め B と系列の全走に `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE` / `..._OVERALL_GRACE_OVERRIDE` = 14,400 秒を付けた。W_i は job 内の worker 占有なので判定量は変わらず、A/B の全走に同じ値 (各走の `env.txt`)。
- **赤の分類:** 04-A (対 2 の後半) が 1 failed / 27,896 passed。赤は `test_env_contract_activation.py::test_historical_calibration_is_verified_only_when_resolved_in_source_stage[modified]` の実 repo `git archive` が 30 秒 timeout を超えた `TimeoutExpired` (shard-1)。A 木は本 wave の変更を含まず、赤の test は変更 file を参照しないので infra と分類し (`runs/04-A/classification.json`)、集計器の文法どおり対 2 を対ごと取り直した (05-B / 06-A)。取り直し 2 走 (上限 4)。

**投入 8 走、有効 3 対。** 系列 2026-09-29 06:32:46 → 09:10:00 JST (`runs/series.log`)。同じ host に 2 shard 以上が載った走は 0 件。

| 対 | W_0 A | W_0 B | Δ = A − B | r | W_max B | O_max A / B | L (最長 test) A / B |
|---|---:|---:|---:|---:|---:|---|---|
| 1 (01-A / 02-B) | 353.909 | 321.576 | +32.333 | 9.1 % | 349.375 (shard-1) | 247.393 / 228.106 | 217.321 / 156.197 |
| 2 (06-A / 05-B) | 299.717 | 259.260 | +40.457 | 13.5 % | 259.260 | 212.352 / 180.565 | 189.286 / 107.043 |
| 3 (07-A / 08-B) | 292.620 | 276.108 | +16.512 | 5.6 % | 276.108 | 205.973 / 165.891 | 185.454 / 104.060 |

- 対差の中央値 32.333 秒、対率の中央値 9.136 % → 区分 (ii)。無効になった対 2 の 1 回目の 03-B (W_0 250.212 秒) は採用していない。
- 補助量 (shard の test 集合が A/B で違うので実装効果として読まない): W_1 は A 301.5 / 238.9 / 238.7、B 349.4 / 229.2 / 233.4 秒。W_2 は A 231.2 / 229.1 / 239.0、B 271.9 / 246.6 / 239.9 秒。shard-0 の pre は A 74.1〜75.6、B 68.2〜69.4 秒。post は全走 10.0〜10.3 秒。
- L は 01-A / 02-B では `test_s1_known_axes_freeze.py::test_historical_oracle_nonadapter_reaches_current_semantics`、他の 6 走では `test_s8b_oracle_driver.py::test_t080_failed_launch_preserves_receipt_refusal`。
- 01-A の W_0 353.9 秒は他の A 2 走 (292.6 / 299.7 秒) より大きく、系列の最初 (保守明けの queue 滞留が引いた直後) だった。対は隣接投入なので対差で比べる。

## 7. 5 分上限と次の律速

- B の W_max 中央値 276.108 秒で 5 分上限を満たした (事前登録の判定)。前 wave (a) の B は 317.194 秒。
- ただし 02-B は shard-1 が 349.4 秒で最遅 shard になり、その走だけ 300 秒を超えた。A でも 01-A の shard-1 が 301.5 秒。shard-1 の伸びの原因は計器が無く分けていない (前 wave でも B の W_1 313.0 秒の走があった)。
- shard-0 では、最長 test の縮みより W_0 の縮みが小さい (結論 5)。W_0 をさらに縮めるなら、B の最大占有 worker の item 列 (`analysis/analysis.md` の走別の節) が次の手掛かりになる。

## 8. 計算量

ユーザー確認: 再 profile の結果 (child 36.7 %) と見積り 合計約 2.35 node 時間 (取り直しで最大 +1.0) を示し、2026-09-29 02:4x JST に「3 対で投入 (推奨)」の回答を得た。実績 (dispatch 受領証の NQSV Elapse、request ID で重複除去、`runs/elapse-summary.txt`): 系列 8 走 24 job 7,031 秒 (1.95 node 時間)、変異 20 job 287 秒、単独 profile・焦点走・provenance・温め B 9 job 764 秒、温め A 55 秒、計 8,137 秒 = 2.26 node 時間。記録後の受入 1 回が別に加わる (worklog に記す)。

## 9. 限界・言わないこと

- land 判定は erratum E1' の下での判定で、事前登録の当初の E1 では `undetermined`。E1' は W を見る前に固定したが、系列開始後 (対 1 の E1 不成立を知った後) の基準変更である。shard-1 / 2 の構成差が共有 FS・controller 等を通じて W_0 に間接的に効きうる経路は排除していない (反対側の相談)。
- 3 対は同一 node・同一 allocation ではない (固定 2 tree の隣接逐次投入)。有意差判定ではない。
- 走査の効果の推定 (約 13 回 × 6.6 秒) は call graph と総時間からの見込みで、profile は呼出し回数を数えていない。単独走の profile は計算ノード /tmp 上の fixture で、実 repo を走査する他の test (shard-1 / 2) への効果は測っていない。
- 局所化の等価性は、`_derive_required_literal` が非 None を返す文法 (key は literal、値は `.` 以外のメタ文字なし) に依存する。helper の文法が広がれば、その時点で等価性の論証と test を見直す必要がある (幅が飽和する式でも窓が全文に広がるだけで結果は正しい)。
- `sre_parse` は Python 3.11 から非推奨。実行環境は 3.10 で、将来の版で import に失敗すれば走査全体が止まる (fail-closed)。

## 10. この dir の中身

`verbatim/` 依頼・段 1 brief・段 2 plan・段 3 相談 2 本・段 4 / 6 裁定 (erratum E1' を含む)・段 5 author 2 本・段 6 レビュー 2 本・fix 2 本・E1 の賛否相談 2 本の prompt と出力・開始 gate・pin 閉包・probe 逐語 (`probe-source.md`)。`analysis/` profile の集計 (`profile-summary.md`)、系列の集計 (`analysis.md`、集計器の出力そのまま)、集計 JSON の要約。`mutation/` probe / final の spec と結果の要約。`runs/` 投入台帳・系列 log・計測 tip・E1 の追加 node・04-A の分類・計算量の集計。job dir は `/work/1/SFC/tanab/tmp/t2273-issue-subprocess-20260928/` (repo 外)。
