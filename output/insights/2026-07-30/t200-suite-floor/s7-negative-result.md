# [T-200] 受入全走の下限短縮は in-scope の施策では動かない — 実装を破棄した negative result

2026-07-30〜31 / Pegasus gen_S 計算ノード / worktree `.claude/worktrees/dev-wave-t200-suite-floor`
(branch `worktree-dev-wave-t200-suite-floor`、基準 `ee45a07`)

**本 wave は実装を land しない。** 段 5 で書いた共有 cache は受入実測で効果を示せず、
一部指標を悪化させたため段 6 で不採用と裁定した。成果物は計測・帰属・真の律速の特定・
裁定パッケージである。

測定はすべて本 worktree で親が実走した。**worktree には ignored な生成物が無いため、
main checkout の値とは系統的に異なる** (F41 / [T-128] §2)。

## 1. 前提が覆った — 材料の 3 数値はいずれも現状と不一致

材料 `output/insights/2026-07-30_dev-wave-gate-cost-and-suite-floor.md` §3.2 / §4.3 に対し、
本 checkout の実測は次のとおりだった。

| 項目 | 材料 | 本 wave の実測 |
|---|---|---|
| real-repo group 直列和 | 145.2 秒 | 98.1〜122.6 秒 |
| 最長 ungrouped node | 107.8 秒 | 108.2〜110.8 秒 |
| T-080 base fixture 構築 | 15〜22 秒 | **84〜103 秒** |

base 構築の 4 倍化が最大の差である。[T-128] が 121.7 → 22.1 秒へ縮めた同じ fixture が、
`output/` の tracked 増加 (3437 ファイル / 151MB) と計測機の変更で戻っていた。

## 2. before の実測とばらつき (全走 2 走)

| 指標 | 走 1 (`874368`, bnode010) | 走 2 (`874389`, bnode009) |
|---|---|---|
| 全走 wall | 214.34 秒 | 200.72 秒 |
| 結果 | 4098 passed / 19 skipped | 4098 passed / 19 skipped |
| real-repo group 直列和 | 122.6 秒 | 98.1 秒 |
| 最長 ungrouped node | 110.8 秒 | 108.2 秒 |
| 全 instance work 合計 | 2294.2 秒 | 2078.3 秒 |
| t080 (oracle_driver 14 件) | 785.0 秒 | 842.1 秒 |

**group 直列和は 98〜123 秒で不安定**である。どの node が実 receipt 解決を払うかが走ごとに
変わるためで、before 値として使えない。**最長 ungrouped node は 108〜111 秒で安定**している。

素朴下界は `max(group 直列和, 最長単一 node, work/48)` であり、走 1 = 122.6 秒、走 2 = 108.2 秒。
**支配要因は走ごとに入れ替わる。**

## 3. 帰属 — 直列 probe で cold/warm を分離した (request `874371`)

`-n 0` の直列走で 5 node を順に実行し、cold と warm を分離した。

| node | 実測 | 意味 |
|---|---|---|
| `test_success_wal_order_budget_and_evaluate_contract` | 37.76 秒 | cold = 実 T-080 receipt 解決を払う |
| `test_verify_inconclusive_and_unknown_abort_reasons_are_fail_closed` | 0.09 秒 | warm memo = 自前の work は 0.1 秒 |
| `test_t080_..._remaining_section_1_4_..._b5` | 85.06 秒 | cold = base 構築 (default key) |
| `test_t080_full_valid_post_r_delete_..._f28` | 0.91 秒 | warm base = copy + body |
| `test_t080_stub_free_draft_finalize_..._b5` | 103.04 秒 | 別 key の base を自前構築 |

- 全走の 45 秒帯 (走 1、14 件) / 37 秒帯 (走 2、6 件) は **実 receipt 解決 1 回のコストと一致する**。
  帯の位置そのものが走ごとに 45.2 → 36.7 秒へ動いたことが、この帰属の裏取りである。
  ただし**呼出し証拠ではなく時間の一致による帰属**であり、その限界を明記する。
- t080 系のうち 60 秒超の cold builder は走 1 で 8 件 783.5 秒、走 2 で 9 件 835.0 秒 =
  t080 合計の **99.6%**。「t080 の work はほぼ全部が重複 base 構築」は成立する。

## 4. 施策は効かなかった — after 2 走の実測

段 5 で `_T080_E2E_BASE_CACHE` (process 内 dict) を、run 一意値 + 入力 manifest digest で
鍵付けした session 内共有 cache (staging → directory rename、非 blocking flock、
独立実体コピー、pickle 不使用、metadata は閉じた schema JSON) へ置き換えた。
本番コードは 0 byte 変更。実装差分は 3 ファイル / 167 行追加 + 新規 1909 行、
patch sha256 `2f71c770a71b26c5e99646cba56ddf9256c603ae057d8e4a0c8067f0d2c52915`。

| 指標 | before 1 | before 2 | after 1 (`874538`) | after 2 (`874540`) |
|---|---|---|---|---|
| ノード | bnode010 | bnode009 | bnode002 | bnode002 |
| 全走 wall | 214.34 | 200.72 | 205.10 | 207.42 |
| 全 work 合計 | 2294.2 | 2078.3 | 2173.3 | 2418.8 |
| t080 (oracle_driver 14 件) | 785.0 | 842.1 | **972.3** | **913.9** |
| cold builder (>60 秒) | 8 | 9 | 10 | 9 |
| 最長 node | 110.8 | 108.2 | **112.1** | **116.0** |

- **wall: before 平均 207.5 秒 → after 平均 206.3 秒 = 差 1.3 秒。** 走行間ばらつき 13.6 秒の
  中であり、効果を主張できない。
- **t080 合計と最長 node は after 2 走とも before 2 走を上回る (悪化)。** after は同一ノード
  (bnode002) 2 走なので、ノード差では説明できない。

### なぜ効かないか (機序、段 3 と段 6 が独立に予測し実測が一致した)

1. **消費者が 1 本しかない variant が 4/5 ある。** fixture の消費は 11 instance / 5 variant で、
   共有が原理的に効くのは既定 variant の 7 本だけである。**最長 node は
   `distinct_basis_blob=True` の唯一の instance** なので、full-key 共有では決して warm 化しない。
2. **待ち手は build と同じ時間ブロックする。** 消えた build が `flock` 待ちへ置き換わり、
   待ち時間が duration に載る。duration では builder と waiter を区別できない。
3. **計算機は CPU で律速していない。** 48 worker × 214 秒 = 10272 worker 秒に対し
   work は 2294 秒 = 稼働率 22%。約 240 CPU 秒の返却は wall へ写らない。
4. **新規コストが増える。** 入力 digest (154MB の sha256) が process あたり約 2.2 秒、
   新テスト自身が概算 +30〜45 秒 work。

## 5. 真の律速を特定した (本 wave 最大の収穫)

`issue_receipt=False` の variant が **10.63 秒**であることから、base 構築 90 秒の内訳は

- **子 python の migration 検証 = 約 80 秒 (89%)**
- 148MB の copytree + `git add -A` + submodule add = 約 10 秒

である。前者は本番 `t080_freeze_migration._history_touches_path` が
`git diff-tree -M -C --find-copies-harder` を **3437 ファイルの basis commit** に当てるコストで、
`[T-173]` の pickaxe と同じ「commit / ファイル数に対して伸びる」構造である。

**したがって in-scope のテスト側施策 (base 共有・共通 prefix 共有) では下限も wall も動かない。**
共通 prefix 共有を仮に入れても、節約は work 約 29 秒・最長 node 0 秒である
(prefix = basis commit までで 10.6 秒、残る 80 秒の suffix は variant ごとに必要)。

## 6. 段 3・段 6 の敵対検証 (codex `gpt-5.6-sol` reasoning=max 2 本 + Claude opus 2 本)

段 3 は plan と**親 brief 自身**を攻撃させ、段 6 は実装を攻撃させた。4 本すべて NO-GO。

**親 brief 自身の誤りが 6 件 real と確定した** (親が検算して確認)。

| 指摘 | 親の検算 |
|---|---|
| 走 2 の割当ノード未記録 | 走 1 = bnode010 / 走 2 = bnode009 で別ノードだった |
| 「走 2 の convoy 帯は 18 件」 | 同帯は **6 件**。18 件は 25〜50 秒帯の数で、親が帯を取り違えた |
| 「LPT 下限 122.6 秒はどの施策でも動かない」 | 親のシナリオが group を下げる施策を模擬していなかった。正しくは走 1 で 122.6 → 110.8 秒 |
| 「LPT 下限」という呼称 | LPT は上界推定であり下界ではない。`loadgroup` は test 数順 FIFO で LPT ではない |
| 「差 91.7 秒は全て scheduling 損失」 | collection・worker 起動・資源競合・flock 待ちを分離していない |
| 標本 2 での因果・安定性の断定 | `modify-revert` node は走 1 99.02 秒 → 走 2 **6.95 秒**。同 key が同 worker に載ると warm 化する |

**攻撃が失敗した (= 維持された) 主張**: 「t080 はほぼ全部が重複 base 構築」(99.6% で成立)、
「group 直列和 35 instance 対 golden 42 canonical」の不一致 (欠落 8 件は全 phase 0.005 秒未満で
pytest が隠したもの。group 直列和への影響は 0.04 秒以下)。

`DW-S03` の「親自身の実測値とその一般化も明示的にレンズへ入れる」が 2 wave 連続で機能した
([T-128] 所見 4 に続く 2 例目)。

## 7. 実装を破棄した理由 (段 6 裁定)

段 6 の 2 本は独立に NO-GO を返し、must-fix 12 件を挙げた。fix で閉じられるものも多いが、
**中核の E-01 (効果が出ない) は設計を変えても in-scope では閉じられない**。加えて次が確定した。

- **共有 entry を消す経路が無い。** TTL 6 時間、prune は publish 時のみ。`conftest.py` が
  `TMPDIR=/dev/shm` を設定するため、共有 base は **RAM に 1 走あたり約 1〜1.5GB 残る**。
  `/dev/shm` 空きが 1GiB を切ると conftest がディスク TMPDIR へ落ち、README が「数百倍遅くなる」と
  書く経路に入る。**測定計画そのものを自分の残骸で汚染する。**
- **共有が発火したかを全走から観測する手段が無い。** `origin` を捨てているため、
  flock 非対応 FS・ENOSPC・digest の割れで全 node が private へ落ちても**緑のまま遅い**。
- **独立検査が構造的に不十分。** `output/` 部分木の path + **size** しか見ないため、
  被検査対象である `orchestrator/` の本番コード・basis 複製物・git 履歴・receipt document・
  variant 次元は守られていない。
- **宣言 scope (P2「session を跨いで再利用しない」) と食い違う。** key の session 次元は
  `--testrunuid` だけで、これは呼出し側が固定でき entry は 6 時間残る。
- **事前登録変異 M7 の帰属が成立しない。** 「lock file を TTL prune 対象へ戻す」変異は、
  後続 2 層 (`is_entry or is_staging` の whitelist と `is_dir()`) に mask される。
  親が module 定数を import して検算し、`.lock` が `ENTRY_SUFFIX` にも `STAGING_PATTERN` にも
  一致しないことを確認した。**実装子の「8 変異すべて KILLED」は M7 について成立しない。**

以上より、1909 行の共有 cache 機構を「効果ゼロ・一部悪化・観測不能・残骸で測定を汚染」の
まま land するのは規律 5 (段階導入 / 盛らない) に反する。**破棄する。**

## 8. 副産物 — main に現存する欠陥 2 件

本 wave の変更とは無関係に、`orchestrator/tests/real_repo_receipt_memo.py` に現存する。

1. **`--testrunuid` 再利用で実 receipt payer が 0 回になる。** session cache の key は
   `PYTEST_XDIST_TESTRUNUID` + HEAD だが、`--testrunuid` は呼出し側が固定でき
   `tools/run_tests.py` は引数を素通しする。同じ UID・HEAD・TMPDIR で 6 時間以内に 2 回走らせると、
   2 回目は全 consumer が cache hit し、実解決が一度も走らない。
2. **`pickle.loads` が `isinstance` 判定より先に実行される。** 共有 tmp へ `__reduce__` を持つ
   pickle を置けば、型不一致で miss になっても副作用は既に発生する。`ReceiptResolution` の
   subclass、`refusals` が list、未知 `state` も `isinstance` を通る。

## 9. 受入と検査

- 全走 4 走 (before 2 / after 2) はすべて計算ノードで実行。after 2 = **4112 passed /
  19 skipped / 207.42 秒 / rc=0** (request `874540`、bnode002)
- after 1 の赤 1 件は `test_codex_worker_launch.py` の既知フレーク。同一ノードでの単独再走は
  1 passed / 2.55 秒 (request `874539`) で再現せず、直後の全走も 0 failed。
  `DW-O18` により実装差分へ帰属せず、**F57 の再発 (48 worker でも発生)** として台帳へ記録した
- **変異 matrix は実施していない。** 実装を破棄したため対象差分が存在しない (`DW-S04` の
  「実装しない」裁定と同じ射程)。段 5 実装子が報告した 8 変異のうち M7 の帰属不成立だけを
  検算で確定させ、本 insight §7 に記録した
- 本 wave の commit は docs のみ

## 9.5 追加実測 (段 9) — 同一ノードの連続 3 走で、実装は wall を約 90 秒**悪化**させていた

段 9 で main の前進 (`a85de57`) を wave 側 merge した tip `b912cd5` に対し受入全走を行った
(request `874541`、bnode002)。結果は **4098 passed / 19 skipped / 116.25 秒 / rc=0**。

この時点で実装は既に破棄されている。したがって bnode002 では同一ノードで 3 走が並ぶ。

| 順 | ノード | コード | wall |
|---|---|---|---|
| 1 (`874538`) | bnode002 | 実装あり | 205.10 秒 |
| 2 (`874540`) | bnode002 | 実装あり | 207.42 秒 |
| 3 (`874541`) | bnode002 | **baseline (実装破棄後)** | **116.25 秒** |

page cache の warm 化が支配要因なら 1 → 2 → 3 が単調に短縮するはずだが、1 と 2 はほぼ同値で、
**実装を戻した 3 走目だけが約 90 秒落ちた**。よって §4 の「効果なし」は控えめすぎた可能性が高く、
**実装は wall を約 1.8 倍に悪化させていた**と読むのが素直である。

機序の候補 (未分離): 9〜10 worker が `flock` で約 90 秒 slot を占有すること、
EX を握ったままの copytree の直列化 (段 6 E-02 / R-04)、および入力 digest が process ごとに
154MB を共有 FS から読むこと (48 worker で最大 7.4GB の読み)。

**同時に、この 3 走は before/after の wall 比較そのものが交絡していたことも示す。**
baseline の wall は bnode010 で 214.34 秒、bnode009 で 200.72 秒、bnode002 で 116.25 秒であり、
**同一コードでノード間に 1.8 倍の開きがある**。したがって §4 の before/after 表を
「施策の効果」として読んではならない。破棄の根拠は次の 4 点であり、wall 比較ではない。

1. 機序 (5 variant のうち 4 つが単一消費者、待ち手が build と同じ時間ブロックする)
2. duration 台帳の悪化 (t080 系が after 2 走とも before 2 走を上回る)
3. 段 6 の must-fix (共有 entry の leak、発火の観測不能、verify の被覆不足、宣言 scope 違反)
4. 事前登録変異 M7 の帰属不成立

段 3 の `REPRO-07` と段 6 の `MEASURE-01` が「1〜2 走の wall 比較では主張できない」と警告した
とおりであり、その警告が実測で裏付けられた。

## 9.7 段 9 の終端 — land は他セッションの handoff 契約違反で拒否された

`tools/dev_wave_land.py` は `status=rejected` / `reason=handoff state is unknown` を返した。
`docs/handoff/README.md` は handoff の `- 状態:` を `作業中` / `計測中` / `中断` の 3 値に限定するが、
並行セッション所有の `docs/handoff/2026-07-29-t126-sequential-stopping-resume.md` は
`段6 NO-GO / DW-O16 有界終端` を書いている。これは land protocol の control-plane 検査が
正しく fail-closed した結果であり、迂回すべき偽陽性ではない。

**他セッション所有物は編集しない** (`CLAUDE.md` 信頼境界、`DW-O23`)。rebase / force /
一回限り adapter も使わない。したがって本 wave の成果は branch
`worktree-dev-wave-t200-suite-floor` の tip `96c9f83` (受入 green、request `874542`) に留め置く。

再開条件: 当該 handoff の所有セッションが状態行を契約内の値へ直すか、ユーザーが扱いを裁定した後、
fresh context で受入を取り直して land を再試行する。

## 11. 付録 — `check_ai_provenance.py` の高速化余地 (計算ノード実測、[T-205])

ユーザー裁定 (2026-07-31)「cygnus は良いが pegasus は計算ノードに投げるべき」を受けて実行場所を
移した際に、あわせて高速化余地を実測した。**実装は 1 byte も変えず**、module を import して
2 方向を測る使い捨て probe を計算ノードへ qsub した (request `874712`、bnode041、
596 commit、HEAD `4d170eb`)。probe は job tmp に置き repo へは入れていない。

**全 arm で findings と forward-correction の結果が baseline と完全一致することを検査条件にした**
(速いだけで答えが変わる変更を採らないため)。

| arm | 並列 | wall | baseline 比 |
|---|---|---|---|
| baseline (現行・逐次) | 1 | **25.24 秒** | 1.00 |
| threads | 4 | 8.03 秒 | 3.1 |
| threads | 8 | 6.18 秒 | 4.1 |
| threads | 16 | 5.60 秒 | 4.5 |
| threads | 32 | 5.23 秒 | 4.8 |
| threads | 48 | 5.23 秒 | 4.8 |
| memory (祖先 bitset) | 1 | 15.40 秒 | 1.6 |
| **memory + threads** | 48 | **4.58 秒** | **5.5** |

- **コアが主因。** `_audit_history` は commit ごとに独立な `_normal_commit_audit` を素の
  list comprehension で回しており、thread pool 化だけで 4.8 倍になる。ただし **16 並列で頭打ち**で、
  32 以上は横ばい。git subprocess の fork/exec と I/O が律速なので 48 コアを使い切る意味はない。
- **メモリは主因ではない。** per-commit の pickaxe (`log --full-history --no-renames -S`) と
  `merge-base --is-ancestor` を祖先集合の bitset 演算へ畳む方向は単独 1.6 倍。596 commit の
  祖先集合でも数百 KB であり、**「大量のメモリ」は不要**である (グラフが小さい)。
- **実行場所の効果が最大。** ログインノードでは 130〜150 秒だったものが計算ノードの逐次で
  25.24 秒 = 5〜6 倍。高速化と併せると約 30 倍になる。
- スレッド安全性は確認済み。可変 module global (`TRAILER_PARSE_TEMP_ROOT`) は読み取りのみで、
  `_isolated_parsed_trailers` は呼び出しごとに専用 `TemporaryDirectory` を作る。

実装方針 (未実装、[T-205]): `_audit_history` の comprehension を既定 16 並列の thread pool にし、
`_has_co_authored_by_policy` / `_is_descendant` を bitset 祖先判定へ置換する。
material §3.1 が記録した内訳 (pickaxe 72% + `merge-base` 14% = 86%) と整合する。

## 10. 次への材料

下限を実際に下げるには、次のいずれかをユーザーが裁定する必要がある (詳細は
`s4-adjudication-plan-v2.md` §5)。

1. **本番 `_history_touches_path` の走査置換** — 唯一 90 秒中 80 秒へ直接効く。
   `[T-173]` と同型で、正しさ防壁の中核に触る
2. `output/` の tracked bytes 削減 — corpus が縮めば fixture 構築も検証も縮む
3. session を跨ぐ base cache — 初回 wall には効かない。stale 検出設計が必要
4. xdist の grouping / 順序化 — [T-120] は同型の group 分割を実測で棄却済み

**測定設計の教訓**: 効果 0 を差 13.6 秒のノイズの中で示すことはできない。今後この面で効果を
主張するなら、同一 allocation 内で A-B / B-A を組む paired 比較と、**builder 実呼出し回数**の
直接観測が要る。duration による代理は builder と waiter が同じ値を出すため原理的に使えない。
