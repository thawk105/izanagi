# Izanagi 作業ログ (worklog)

セッションごとの進捗を時系列で記録する。git 履歴や各正本に入らない協議・異常・持ち越しを束ねる
「作業の索引」であり、commit 内容の再説明はしない。役割分担:

- 設計判断と却下案 → `docs/decisions.md`
- CCBench の構造的事実 → `docs/ccbench-anatomy.md`
- CCBench のバグ等の知見 → `output/insights/`
- タスク分解 → `docs/phaseN.md`
- **このファイル = それらを束ねる日誌 (各セッションの索引)**

## 新規エントリの書式 (D35)

過去エントリは凍結し、次の規約は新規エントリに適用する。

- 本文化するのは、ユーザー承認・協議の決着、棄却 finding (refuted)、未コミット事象・セッション異常と
  救出、エージェント工数、人間判断待ち・持ち越し、次の一手など **git に入り得ない情報だけ**
- commit は「hash + 件名 (+ 位置づけ 1 行)」まで。連続群は「先頭..末尾 (N 本)」で表し、内容を再掲しない
- 監査の finding 全文と裁定は insight / audit JSON に凍結する。worklog はレンズ数、real/refuted 数、
  最重要 1〜3 件、一次資料ポインタの 10〜15 行に留める
- 論文素材になる段落は行頭に「素材:」を付ける。持ち越しは逐語再掲せず「変わらず (前エントリ参照)」
  とする
- docs(worklog) だけの commit は prose の body を付けず、件名 + 必須 trailer だけにする

### 次の一手の ID 規約 (D70)

「次の一手」の項目が黙って落ちる経路を塞ぐため、各項目に安定 ID を付け、`tools/check_docs.py` が
保存則を機械検査する。ID は角括弧で囲んだ `T-` + 連番で、**表記は 1 つに正規化する** —
1〜999 は 3 桁ゼロ埋め、1000 以上は先頭ゼロなしで書く。冗長なゼロ埋め (4 桁で 1 を表す等) は
同じ数値の二表記になるため**不正形式として赤にする**。

- **位置**: トップレベル list item (インデント無しの `1. ` または `- `) の**先頭**に置く。
  インデントされた子項目は原子として扱わない — **1 原子 = 1 トップレベル項目 = 1 ID** に平坦化する
  (子項目 `(a)(b)(c)` に原子を詰めると、その分は機械検査の網から外れる)
- **採番**: 現行 worklog (「ローテーション」節より後) + `docs/archive/worklog-*.md` + 見送り台帳に
  現存する有効 ID の最大値 + 1。並行セッションは番号を予約したとみなさず、統合直前に再走査して
  未統合側を振り直す (`landed` = main へ統合された時点)
- **不変性**: 一度 land した ID は変更・再利用しない
- **保存則 (機械検査)**: あるエントリの「次の一手」に現れた ID は、後続エントリのトップレベル項目
  (消化または継続) か、見送り台帳のトップレベル項目 (理由付き見送り) に現れなければ赤になる。
  ローテーション境界 (アーカイブ最新の末尾エントリ → 現行の先頭エントリ) も検査対象
- **この節と決定記録には有効 ID を書かない** (採番母集団と sink の自己汚染を避けるため、
  例示は `T-NNN` のようなプレースホルダで書く)

## ローテーション

Phase 境界または現行ファイルの肥大時 (`tools/check_docs.py` の閾値超過が
知らせる) に、過去分を `docs/archive/worklog-<範囲>.md` へ**移動**し、現行ファイルを軽く保つ
(ブート時に読むのは末尾エントリのみ、の運用を軽く保つため。2026-07-05 導入、D35)。
アーカイブは凍結 (訂正注記のみ追記可)。既存アーカイブの一覧は `docs/archive/README.md`。

---
## 2026-07-26 (1) — [T-091][T-092][T-093] receipt gate の検出力を独立 oracle へ引き上げ (テストのみ・本番 0 byte、branch worktree-dev-wave-t091-093-hardening、計測なし)

/dev-wave 1 回。2026-07-25 (7) でユーザーが前倒しを承認した hardening 3 件を消化した。
**本番コードは 1 byte も変えていない**ので、certified 選択・gate の受理集合・凍結成果物の bytes は
不変であり、変わったのは検出力だけである。材料レポートと逐語は
`output/insights/2026-07-26_t091-t093-hardening.md` / 同 `-verbatim.md`、変異台帳は
同ディレクトリの `2026-07-26_t091-t093-mutation-ledger.json` を正本とする。

- [T-091] **消化**。改竄 receipt を public `verify_receipt()` 経由で撃つ負例を新設。fixture は
  導出値反映後・canonical 化前に改竄 callback を 1 回だけ適用する (commit 後改竄では
  `receipt.issued_but_missing` が先に出て証拠にならない)。**stub のまま残した 4 gate を
  テスト内に明記**し、「全 gate を検証した」とは主張しない。
- [T-092] **消化**。real-repo test を post-R 固定にし R OID・R blob raw sha256・H_mig を literal pin。
  R 不在時は skip でなく明示 fail。削除した pre-R 分岐は post-R では**到達不能**であることを
  親が実測し、敵対相談 A-6「既存検査を弱める」を**部分 refuted**と裁定した。
- [T-093] **消化**。observed 15 cell を real-repo 専用の新定数へ literal pin し receipt からの zip を廃止。
  既存 3 要素 golden は不変 (同ファイルの stub-free E2E が 3 要素で比較しており、その basis は
  current source の複製のため H_mig literal を混ぜられない = 敵対相談 A-1/B-1)。
- **素材: literal 化だけでは検出力にならなかった。** 敵対相談 A-3 が「単一 real-repo vector では
  production が receipt を無視して実 repo の値を返す退化を検出できない (期待値が恒真化する)」と指摘。
  親は hermetic E2E の basis blob を fixture 内で分岐させる**第 2 vector**へ設計変更し、
  これが変異 M6 として実際に KILL した。当初案のままなら T-093 は固有帰属を持てなかった。
- **変異 matrix (親実測、統合 commit 後)**: 事前登録 M1〜M7 の **7/7 が実測と一致**。
  M1-M4=T-091 / M5=T-092 / M6=T-093 はいずれも新テストのみ KILL・旧テスト SURVIVE。
  M7 は事前登録どおり**帰属不成立** (新旧とも KILL) で新規検出力に計上しない。
  DW-M08 に従い各変異を新テストと変更前 HEAD 版テストの双方へ全走させた。
- **エージェント工数**: codex 子 9 本 (プラン 1・敵対相談 2・実装 2・レビュー 2・fix 1・焦点再 1)。
  段 3 は両レンズ NO-GO・所見 14、段 6 は A=GO / B=NO-GO・所見 4、焦点再は closed 3 / partial 1。
- **検査 (記録 commit 前の実測)**: 受入全走 **2995 passed / 18 skipped / 0 failed**
  (baseline `be40317` = 2994 passed / 18 skipped、node 消失 0)、`check_docs` rc=0、
  `check_ai_provenance` = 355 件・違反なし。
- **記録後検査 (F34)**: 記録 commit (`2e6b2ee`) の後に再走 = `check_docs` rc=0、
  焦点 (`test_check_docs` + repo scan invariant + real-repo serialization) **117 passed**、
  `check_ai_provenance` = **356 件・違反なし**。
- **スキル自己改善 (gate 発火・候補 3 / 採用 1 / 裁定送り 2)**: 採用は `DW-M01` への 1 行
  (テスト強化 wave は `DW-M08` の新旧両走も事前登録する)。今回この導線が無く、親が気づかなければ
  片走で M7 の先取り KILL を新規検出力と誤記録する経路が開いていた。予算は hard ceiling 24000 に対し
  HEAD 時点で 23986 (余裕 14 bytes) だったため、`DW-O15` が `DW-M07` 本文を複製していた無駄を
  取り (条件 dispatch は両節を同時に読ませる) 場所を作った。事故は発生していないので failures /
  decisions は変更しない。残り 2 件は予算に収まらず [T-104] として裁定へ送る (前例 = [T-101])。

### 次の一手
1. [T-088] **人間手番 (承認済み)**: `tools/pegasus/submit_floor.sh --dry-run` で receipt を確認し、
   続けて明示実行して実 job ID を得る。期待は driver rc=2 (official guard 生存)。手順は
   `tools/pegasus/README.md` §5 と `output/insights/2026-07-25_t088-floor-wrapper.md` §6。変わらず
2. [T-098] **承認済み・着手可能**: 選択理由欄の LP 族拒否を producer validator へ追加
   (`s8b_selector_output.py`)。検出語彙は `tools/check_docs.py` の台帳と共有するか要設計。変わらず
3. [T-102] **新規 (scope 外 real 所見)**: production の git runner が ambient `GIT_*` を継承する
   (`s1_known_axes_freeze.py:89`、`s8b_holdout_freeze.py:147`)。poisoned env の敵対走で 2 failed を
   実測済み。本 wave は本番 0 byte のため未修正。本番コードに触るので測定前後の扱いに裁定が要る
4. [T-103] **新規 (敵対相談 A-6 の対案、scope 外)**: never-issued 状態の real artifact 由来
   refusal vector を別 node で撃つテストの新設。pre-R 分岐削除で失った実効検出力は 0 だが、
   検出力の**追加**として価値がある
5. [T-011] 科学レーン floor 実測。残 gate = 上記 1 → 段階 3・4 → 実行 revision 束縛 → lineage。変わらず
6. [T-097] 裁定待ち: placeholder 検出の対象族拡張 (claim-bearing artifact 族の定義)。変わらず
7. [T-099] 裁定待ち: 凍結成果物に placeholder が入った場合の専用 waiver 契約。変わらず
8. [T-100] 裁定待ち: 検出語彙の拡張と予測値先書きの構造的検出。変わらず
9. [T-096] 裁定待ち: driver 予算定数の hard cap 化。変わらず
10. [T-101] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
11. [T-104] **新規・裁定待ち (dev-wave 自己改善)**: 予算に収まらなかった作法 2 件 —
    (i) decision 本文と要約の食い違いが別集合を指す場合に双方を brief へ書き分ける規則 (`DW-S01`)、
    (ii) 段 1 の前提実測を下流の子出力の独立検証に使える形で残す規則 (`DW-S01`)。
    `docs/dev-wave/**` は hard ceiling 24000 に対し 23966 で余裕 34 bytes しかない。
    [T-101] と併せ、予算値の引き上げ可否を独立審査するか、reference の再編で場所を作るかの裁定が要る
12. [T-089] **測定後の hardening と裁定** (前倒し対象外): 二重 reason-tag 描画。修正時に exact 期待値を
    同時更新する。変わらず
13. [T-090] **測定後の hardening と裁定** (前倒し対象外): `VerifiedFreeze.document` が mutable dict の
    まま返る (`s8b_freeze_io.py:30-38`)。変わらず
14. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
15. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
16. [T-009] 延期: AGENTS.md 追記は 1 cycle 後。変わらず
17. [T-060] 延期: WAL 用語運用の明文化は 1 cycle 後。変わらず
18. [T-010] 延期: B-008 再試験は 1 cycle 後に再評価。変わらず
19. [T-012] 延期: pilot 凍結維持。変わらず
20. [T-082] 延期: 全 caller 移行は 1 cycle 後。変わらず

## 2026-07-26 (2) — [T-098] selector の選択理由欄で literal placeholder を fail-closed 拒否 (本番 13 行、branch worktree-dev-wave-t091-093-hardening、計測なし)

/dev-wave 1 回。2026-07-25 (7) でユーザーが承認した「生成側で拒否」を実装した。本番差分は
`s8b_selector_output.py` の 13 行だけで、受理集合は「長さ 1〜2000 の既存受理文字列のうち LP を
含むもの」だけ縮小する。凍結成果物の bytes は不変。材料レポートと逐語は
`output/insights/2026-07-26_t098-selector-lp-reject.md` / 同 `-verbatim.md`、変異台帳は
同 `-mutation-ledger.json` を正本とする。commit = `ef9ef76`。
表記は D88 (6) を継承し、検出 3 語は LP-1 / LP-2 / LP-3 の記号参照で書く。

- [T-098] **消化**。`parse_selector_output` に decode 済み `rationale` の LP 包含を拒否する
  fail-closed gate を追加した。新 code は `rationale_placeholder` の 1 個で、検査位置は
  `rationale_blank` / `rationale_too_long` の後。既存 code と既存拒否挙動は不変。
  語彙は parser 内に別名で持ち、本番から docs lint を import しない (parser bytes は selector
  journal header に pin される資産のため)。
- **裁定前提は成立**。親が実装前に実コードへ 6 パターンを投入し **6/6 受理**を実測した。
  既存 seal 済み 6 rows に LP は 0 件で、`_reparse_agent_raw` の再 parse 結果は不変。
- **親 brief の誤りを訂正 (段 3 レンズ A の A-1、real)**。brief は「floor / ratified の両検証は
  `pre_oracle_head` blob 射影なので worktree 編集に不感」と書いたが、これは parser の **hash pin** に
  だけ当てはまる。floor は `s8b_floor_campaign.py:1365-1367` で `verify_prediction_freeze` を呼び
  **現行 parser で raw を再 parse する**。既存 6 rows が無事なのは**データ依存**であって構造保証ではない。
- **素材: 正例が検出力になった。** 当初設計は負例だけだった。レビューが「承認外の**過剰拒否**も
  受理集合の改変である」と指摘し、全角山括弧・HTML entity・token 内空白・非承認の類似語・片側
  delimiter 欠落の**受理を固定する正例**を追加した。これらは変異 S2 / S7 / S8 で実際に KILL しており、
  正例なしでは検出できなかった。負例だけを数えて「検出力」と呼ぶ設計は片肺だった。
- **語彙束縛は 2 度否定された。** 親案 (ast でトップレベル `Assign` を 1 個取り docs と parser を等号
  照合) は `LITERAL_PLACEHOLDERS += (...)` を静かに取りこぼす (B-4)。改訂案 (テスト内独立 3 語との
  三者照合 + Store 個数検査) も `globals()["…"] += (…)` を捕まえられない (RB-2)。最終形は
  **ast 検査 + テストからの実行時 import による実効値照合**の併用。両経路は変異 S1 / S11 で実測 KILL。
- **変異 matrix (親実測、統合 commit 後)**: 事前登録 **23/23 が実測と一致**。帰属成立 22 件
  (新テストのみ KILL・変更前 HEAD 版テストは SURVIVE)、非帰属 control 1 件 (N1 = 最大長 3000、
  新旧とも KILL のため新規検出力に計上しない)。`DW-M08` に従い全 23 件を新旧両走した。
  harness は flock 単一走行・アンカー一意性 assert・注入 diffstat・内容比較による復元検査を持ち、
  全走後の tree は clean。
- **エージェント工数**: codex 子 9 本 (プラン 1・敵対相談 2・実装 1・レビュー 2・fix 2・焦点再 1)。
  段 3 は両レンズ NO-GO・所見 11、段 6 は A=GO 所見なし / B=NO-GO 所見 4、焦点再は closed 4 /
  partial 1 + 残存誤実装 2 で NO-GO、fix 巡 2 で全 closed。**相談・レビュー・再レビュー 4 本すべてが NO-GO**。
- **検査 (統合 commit 直前の実測)**: 受入全走 **3058 passed / 18 skipped / 0 failed**
  (基線 `c129e73` = 2995 passed / 18 skipped、node 消失 0)、`check_docs` rc=0、
  `check_ai_provenance` = 358 件・違反なし。
- **受入で 1 度だけ出た赤を差分へ帰属しなかった。** fix 巡 1 後の全走で
  `test_dev_waves_integration.py::test_artifact_aggregate_cap_stops_before_next_wave_side_effect` が
  `FileNotFoundError` で赤になった。単独再走 3/3 passed のフレークで、差分 4 ファイルに
  `tools/dev_waves/` を含まないため帰属しない。原因は [T-105] として起票した。
- **記録後検査 (F34)**: 記録 commit を作った直後に再走した = `check_docs` rc=0、
  `check_ai_provenance` = **359 件・違反なし**、焦点 (`test_check_docs` + selector output /
  selector freeze / prediction runner) **288 passed**。
  実測値を本欄へ埋めるため同 commit を `--amend` したので、記録 commit の hash は amend 後の値である
  (本欄は自己参照を持たない。手順の正本はこの記述であり、amend 前の hash は破棄されている)。
- **スキル自己改善 (gate 発火・候補 3 / 採用 1 / 裁定送り 2)**: 採用は `DW-S07` の 1 文置換
  (再走値は amend で埋め、hash 自己参照を書かない)。**今回これは near miss として実発現した** —
  F34 と F36 の恒久対応を両方守ると再走値は記録 commit 後にしか書けず、amend で埋めると
  欄に書いた記録 commit hash が amend 自身によって dangling になる。同 wave 内で是正したが、
  前 wave の欄も同型の自己参照を持つ。**F38 を新設**した (F36 とは機序が異なる — F36 は実測前の値、
  本件は実測値を埋める手順の副作用)。予算は合算 24000 に対し変更後 23987 (余裕 13 bytes)。
  残り 2 件は予算に収まらず [T-108] として裁定へ送る (前例 = [T-101] / [T-104])。

### 次の一手
1. [T-088] **人間手番 (承認済み)**: `tools/pegasus/submit_floor.sh --dry-run` で receipt を確認し、
   続けて明示実行して実 job ID を得る。期待は driver rc=2 (official guard 生存)。手順は
   `tools/pegasus/README.md` §5 と `output/insights/2026-07-25_t088-floor-wrapper.md` §6。変わらず
2. [T-106] **新規・裁定待ち (scope 外 real 所見)**: ratified proof chain が selector raw を再 parse
   しない (`s8b_ratified_freeze.py` に `verify_prediction_freeze` / `parse_selector_output` の呼び出しが
   grep 0 件)。floor は新 gate を実行するため両者で受理が分岐する。選択肢 = (a) 現状維持 + 射程の明記、
   (b) ratified にも再 parse を入れる (歴史射影の設計変更)、(c) 封印時点の parser 判定を artifact へ
   刻む。**(a) を推奨** — 生成経路は本 wave で閉じたので残余は偽造 evidence という別の脅威モデル。
   正本 = `output/insights/2026-07-26_t098-selector-lp-reject.md` §6-2 / §7
3. [T-107] **新規・裁定待ち (scope 外 real 所見)**: 出力 schema と selector role が新しい受理集合を
   表現していない。両者は封印済み prediction の `sources` に sha pin されるため bytes 変更が既存
   freeze の検証を割る。選択肢 = (a) parser-authoritative 契約の明文化、(b) versioned schema/role
   への移行。[T-106] の受理差を固定する境界テスト新設も同じ裁定に従属する
4. [T-105] **新規 (scope 外 real 所見)**: `tools/dev_waves/daemon.py:626-638` の
   `_run_artifact_bytes` が `os.walk` の列挙後に `path.lstat()` するため、atomic-write の一時ファイル
   (`*.tmp.<pid>.<tid>`) が列挙と lstat の間に消えると `FileNotFoundError` が素通しされ
   `DevWavesError` の fail-closed にならない。本 wave の受入で 1 度発現し単独再走 3/3 passed を実測。
   本番コードに触るので測定前後の扱いに裁定が要る
5. [T-102] **scope 外 real 所見**: production の git runner が ambient `GIT_*` を継承する
   (`s1_known_axes_freeze.py:89`、`s8b_holdout_freeze.py:147`)。本番コードに触るので測定前後の
   扱いに裁定が要る。変わらず
6. [T-103] **未着手**: never-issued 状態の real artifact 由来 refusal vector を別 node で撃つ
   テストの新設。検出力の追加として価値がある。変わらず
7. [T-011] 科学レーン floor 実測。残 gate = 上記 1 → 段階 3・4 → 実行 revision 束縛 → lineage。変わらず
8. [T-097] 裁定待ち: placeholder 検出の対象族拡張 (claim-bearing artifact 族の定義)。変わらず
9. [T-099] 裁定待ち: 凍結成果物に placeholder が入った場合の専用 waiver 契約。変わらず
10. [T-100] 裁定待ち: 検出語彙の拡張と予測値先書きの構造的検出。変わらず
11. [T-096] 裁定待ち: driver 予算定数の hard cap 化。変わらず
12. [T-101] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
13. [T-104] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。予算値の引き上げ可否の
    独立審査か reference 再編かの裁定が要る。変わらず
14. [T-108] **新規・裁定待ち (dev-wave 自己改善)**: 予算に収まらなかった作法 2 件 —
    (i) 差分が到達しえないファイルで出た赤の扱い (単独再走で再現性を実測し、帰属せず新規所見として
    起票する。`DW-O06` は submodule 由来の偽赤、`DW-O18` は import path 由来の偽赤しか扱っておらず、
    無関係モジュールのフレークに規則がない)、(ii) 受理集合を**縮小する** wave では、承認外の
    **過剰拒否**を検出する正例も変異事前登録に含める規則 (`DW-M01`)。本 wave では正例が
    変異 S2 / S7 / S8 を実際に KILL しており、負例だけでは検出できなかった。
    `docs/dev-wave/**` は hard ceiling 24000 に対し 23987 で余裕 13 bytes。[T-101] / [T-104] と
    併せ、予算値の引き上げ可否を独立審査するか reference を再編するかの裁定が要る
15. [T-089] **測定後の hardening と裁定** (前倒し対象外): 二重 reason-tag 描画。修正時に exact 期待値を
    同時更新する。変わらず
16. [T-090] **測定後の hardening と裁定** (前倒し対象外): `VerifiedFreeze.document` が mutable dict の
    まま返る (`s8b_freeze_io.py:30-38`)。変わらず
17. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
18. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
19. [T-009] 延期: AGENTS.md 追記は 1 cycle 後。変わらず
20. [T-060] 延期: WAL 用語運用の明文化は 1 cycle 後。変わらず
21. [T-010] 延期: B-008 再試験は 1 cycle 後に再評価。変わらず
22. [T-012] 延期: pilot 凍結維持。変わらず
23. [T-082] 延期: 全 caller 移行は 1 cycle 後。変わらず

## 2026-07-26 (3) — [T-109] クロスプロトコル対応: 実装可能性を調査し「実装しない」と裁定 (設計のみ・コード 0 byte、branch worktree-dev-wave-t091-093-hardening、計測なし)

/dev-wave 1 回 (引数「クロスプロトコル対応」)。段 4 で **実装しない**と裁定し `DW-S04` の
`4→7→8→9` を採った。**実装差分がないため変異 matrix と受入全走は対象外**である。
材料レポート = `output/insights/2026-07-26_s1-cross-protocol-gate-survey.md`、
逐語 = 同 `-consultations.md` (原文 sha256 併記) を正本とする。

- **裁定の骨子**: cross-protocol の実装経路が**すべて**ユーザー承認済みの決定で塞がっている。
  (i) D86(3)/D87 が AI の `qsub` を明示禁止するため、生死実験の実測自体が人間手番、
  (ii) D16 に trace-hook の out-of-tree patch 例外はなく (却下リストに「全て patch」がある)、
  branch へ置けば gitlink 前進で承認定数 `CCBENCH_FULL_SHA` と衝突、
  (iii) D32 (ユーザー承認 2026-07-03) が cross-protocol を主実験後へ降格し一歩目をカタログ化試作と定める。
- **最重要の発見 — 凍結 bytes を触らなくても承認済み手番は割れる。** 親は当初「`genome.py` を触らず
  gitlink も動かさなければ無害」と考えたが誤り。floor launch certificate の `clean_scan_digest` は
  **実 repository file 一覧を preimage に含む** (`s8b_floor_campaign.py:1597-1639`)。patch/driver を
  commit するだけで [T-088] receipt の `source_commit` と `clean_scan_digest` が承認時点から変わる。
  `submit_floor.sh:181-245` は `output/` 外の untracked と未 commit script を明示拒否し、
  PBS ログの既定戻り先 (投入 dir) がこれに抵触する。
- **素材: 移植順序は protocol の系統でなく版 ID の安定性で決まる。** OCC 同士の silo→tictoc は
  直感的に近いが、tictoc は validation の rts 拡張が delta overflow 時に**新版を書かずに wts を前進**
  させる (`cc/tictoc/transaction.cc:425-440`)。mocc は hybrid だが bitfield 抽出は恒等。
  ただしその恒等性も **UPDATE-only 限定**で、`absent`・INSERT/reinsert・scan で前提が崩れる。
- **素材: 「移植した」と「同じ強度で検証できる」は別である。** `Integrity.clean()` の 9 カウンタのうち
  `lock_coverage_violations` と `permutation_violations` は **silo の `#if TRACE` assert が emit する
  X 行 / P 行だけが検出源**。si 型の最小 hook を移植すると同 2 項は常時 0 の恒真ゲートになり、
  同じ lockskip を silo は indeterminate、mocc は certified としうる受理集合の非対称が生じる。
- **親 brief の誤りを 10 件 real と認めた。** P4 (AI qsub 可) / P5 (D16 例外) / P1・P2 (一歩目は S1) /
  P6 (patches 追加は無害) / P7 (live 軸 2 本) / 実測2 (verifier に silo 出現 0) /
  実測3 (`is_clean()` が 4 カウンタ) / 実測6 (恒等写像) / R-1 (手動 cmake は gate 迂回でない)。
  特に R-1 は親が段 2 の blocker 指摘に反論したものだが、レンズ A が「s5 の手動 build は trusted な
  HEAD 済み hook の上に broken 差分を重ねるもので、新規 hook を作る本件と非同型」と否定した。
- **エージェント工数**: codex 子 3 本 (プラン 1・敵対レンズ 2)。**3 本すべて NO-GO**。
  段 2 が blocker 2 件、段 3 が must-fix 17 件。実装子・レビュー子は起動していない (実装しない裁定のため)。
- **検査**: 逐語・材料レポート凍結前に検出語 gate を機械検査した = literal placeholder **hit 0**
  (語彙 3 件)、三軸 conjunction **hit 0** (holdout rr80/rr20 の両方、走査 3 ファイル)。
  可逆 defang と erratum は不要だった。`check_docs` rc=0。
- **スキル自己改善 (gate 発火・候補 3 / 採用 1 / 裁定送り 2)**: 採用は **F39 の起票** (routing 1) —
  「凍結 bytes を触らない」を安全条件と誤認し、ファイル追加が `clean_scan_digest` 経由で
  承認済み手番を割ることを見落とした near miss。実害なし (段 3 が実装前に検出) だが、
  親は誤前提を handoff へ「解決済み」と凍結までしていた。残り 2 件 (`DW-S01` の依存棚卸しが
  別ノード実行を扱っていない / 同節に「未実行の承認済み手番を自分の変更が失効させないか」の
  逆向き照合が無い) と F39 の恒久対応は、`docs/dev-wave/**` が上限 24000 に対し 23987
  (余裕 13 bytes) で収まらないため [T-109] に束ねて裁定へ送る (前例 = [T-101] / [T-104] / [T-108])。

### 次の一手
1. [T-088] **人間手番 (承認済み)**: `tools/pegasus/submit_floor.sh --dry-run` で receipt を確認し、
   続けて明示実行して実 job ID を得る。期待は driver rc=2 (official guard 生存)。
   **[T-109] により優先度が上がった** — 本手番より先に repo へファイルを足すと
   `source_commit` / `clean_scan_digest` が変わり再承認が要る
2. [T-109] **新規・裁定待ち (本 wave の成果)**: クロスプロトコル対応の裁定パッケージ 6 件 —
   (a) D16 の prototype 例外 (一回限りの trace-hook patch) の可否、(b) [T-088] との順序
   (**AI 推奨 = [T-088] を先に完了**)、(c) 最小 trace-hook smoke の scope、
   (d) observer-effect baseline の protocol 拡張 (手動 cmake 経路が規律 1 の機械防壁を通らない)、
   (e) MOCC lock coverage package、(f) 本物の cross-protocol package の順序 (D32 の一歩目 =
   カタログ化試作)。正本 = `output/insights/2026-07-26_s1-cross-protocol-gate-survey.md` §5。
   併せて dev-wave 自己改善 3 件も同裁定に束ねる — (g) F39 の恒久対応 (`DW-O09` の pin 閉包既定対象へ
   「ファイル集合を pin する digest」を追加)、(h) `DW-S01` の依存棚卸しが別ノード実行を扱っておらず
   ログインノードの値で偽充足しうる、(i) `DW-S01` に「未実行の承認済み手番を自分の変更が失効させないか」
   の逆向き照合が無い (F35 は stale 検出の一方向のみ)。いずれも予算 13 bytes に収まらない
3. [T-106] 裁定待ち: ratified proof chain が selector raw を再 parse しない。**(a) 現状維持 + 射程明記**
   を推奨。変わらず
4. [T-107] 裁定待ち: 出力 schema と selector role が新しい受理集合を表現していない。変わらず
5. [T-105] scope 外 real 所見: `tools/dev_waves/daemon.py` の `_run_artifact_bytes` が
   `FileNotFoundError` を素通しする。変わらず
6. [T-102] scope 外 real 所見: production の git runner が ambient `GIT_*` を継承する。変わらず
7. [T-103] 未着手: never-issued 状態の real artifact 由来 refusal vector を別 node で撃つテスト。変わらず
8. [T-011] 科学レーン floor 実測。残 gate = 上記 1 → 段階 3・4 → 実行 revision 束縛 → lineage。変わらず
9. [T-097] 裁定待ち: placeholder 検出の対象族拡張。変わらず
10. [T-099] 裁定待ち: 凍結成果物に placeholder が入った場合の専用 waiver 契約。変わらず
11. [T-100] 裁定待ち: 検出語彙の拡張と予測値先書きの構造的検出。変わらず
12. [T-096] 裁定待ち: driver 予算定数の hard cap 化。変わらず
13. [T-101] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
14. [T-104] 裁定待ち (dev-wave 自己改善): 予算値の引き上げ可否の独立審査か reference 再編か。変わらず
15. [T-108] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
16. [T-089] 測定後の hardening と裁定 (前倒し対象外): 二重 reason-tag 描画。変わらず
17. [T-090] 測定後の hardening と裁定 (前倒し対象外): `VerifiedFreeze.document` が mutable dict。変わらず
18. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
19. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
20. [T-009] 延期: AGENTS.md 追記は 1 cycle 後。変わらず
21. [T-060] 延期: WAL 用語運用の明文化は 1 cycle 後。変わらず
22. [T-010] 延期: B-008 再試験は 1 cycle 後に再評価。変わらず
23. [T-012] 延期: pilot 凍結維持。変わらず
24. [T-082] 延期: 全 caller 移行は 1 cycle 後。変わらず

## 2026-07-26 (4) — /rulings: 裁定待ち 16 件を索引化しユーザーが 4 件を裁定 + 再承認コストの誤報告を訂正 (docs-only・コード 0 byte、branch worktree-dev-wave-t091-093-hardening、計測なし)

`/rulings` 1 回。索引 16 件・詳説 5 件を提示し、ユーザーが 4 件を裁定した。あわせて、直前エントリ
2026-07-26 (3) が報告した「ファイル追加が [T-088] の承認前提を変える」を**過大報告として訂正**する。

- **ユーザー裁定 (2026-07-26)**:
  - **[T-106] = (a) 現状維持 + 射程の明記。** ratified 側に再 parse を入れず、適用範囲を文書化する。
  - **[T-107] = (a) parser-authoritative 契約の明文化。** 出力 schema と selector role の bytes は変えない。
  - **[T-105] = 計測後に回す。** 本番コードに触るため [T-011] の後。
  - **[T-109] の順序 = クロスプロトコル対応を先行してよい (親の推奨を却下)。** 判断の前提として
    ユーザーが再承認コストを問い、親が実測して「不要」と回答した (下記訂正)。作業は新セッションで行う。
- **訂正 (erratum) — 直前エントリの「承認前提が変わる」は過大報告だった。**
  `clean_scan_digest()` (`s8b_floor_campaign.py:1597-1639`) は**投入時にその場で計算して記録する値**で、
  承認済み定数との照合を持たない。`s8b_approved.py` の承認定数一覧 (`:42-67`) に
  `clean_scan_digest` も `source_commit` も無い。`source_commit` は `submit_floor.sh:183` の
  `git rev-parse --verify HEAD` を投入時に取るだけで、同一投入内の pre/receipt 一致
  (`test_pegasus_floor_tools.py:806`) しか見ていない。
  `submit_floor.sh:181-245` が実際に要求するのは (i) tracked 作業ツリーが clean、(ii) index が clean、
  (iii) `output/` 外に untracked が無い、(iv) job script が tracked かつ作業ツリー bytes = commit 済み
  blob、の 4 点であり、**いずれも人間の再署名ではない**。
  したがって **repo へファイルを足しても [T-088] の再承認は発生しない。**
  親は段 3 レンズ B の指摘を裏取りせずに受け入れ、worklog・材料レポート・F39 へ書いた。
  **retroactive に直さない** (F38 の前例に従う) — 既 land エントリは本 erratum で訂正する。
- **訂正後も残る真の制約 (こちらは実在する)**:
  - **gitlink 前進は別物。** submodule ブランチへ置くと `CCBENCH_FULL_SHA` (承認定数、
    「現在値の追認を拒否」) と衝突し、`test_ccbench_full_sha_matches_real_gitlink` が赤になる。
    解消にはユーザーによる新 pin の承認と、`known_axes_freeze` / `floor_protocol` の再凍結を要する。
    **これは実際に手間がかかる。**
  - 新規ファイルは三軸 conjunction に一致してはならない (本 wave の 4 ファイルは hit 0 を実測済み)。
  - `output/s8b-freeze/` 配下に未知 file を置けない。
  - PBS ログの既定戻り先は投入 dir なので、`#PBS -o/-e` を `output/` 配下へ向ける必要がある。
- **F39 の射程も縮む。** 「ファイル追加が承認済み手番を割る」の部分は誤りで、正しくは
  「ファイル集合が digest の preimage に入るのは事実だが、その digest は事前承認されていない」。
  F39 本文の恒久対応 (`DW-O09` へ「ファイル集合を pin する digest」を加える) は、
  **pin 一般の見落としとしては依然有効**だが、緊急度は下がる。[T-109]-(g) として裁定へ残す。

### 次の一手
1. [T-109] **新セッションで着手 (ユーザー裁定済み)**: `/dev-wave クロスプロトコル対応` を再実行する。
   **着手前に (a) の裁定が要る** — trace-hook の置き場所を out-of-tree patch (D16 の一回限りの例外)
   とするか、submodule ブランチ (gitlink 前進 → 承認定数の再承認 + 再凍結) とするか。
   **AI 推奨 = patch 例外を許す** (ブランチ側は再承認と再凍結という実コストが確定しているため)。
   残る (c)〜(i) は次セッションの段 1 で scope 化する。正本 =
   `output/insights/2026-07-26_s1-cross-protocol-gate-survey.md` §5
2. [T-088] **人間手番 (承認済み)**: `tools/pegasus/submit_floor.sh --dry-run` → 明示実行。
   期待は driver rc=2。**[T-109] との順序制約は解消した** (再承認は不要) ため、どちらが先でもよい
3. [T-106] **裁定済み → 実施待ち**: (a) 現状維持 + 射程の明記。ratified が selector raw を再 parse
   しない事実と、その適用範囲を文書化する
4. [T-107] **裁定済み → 実施待ち**: (a) parser-authoritative 契約の明文化。[T-106] と同じ wave で扱う
5. [T-105] **裁定済み → [T-011] の後**: `_run_artifact_bytes` の `FileNotFoundError` 素通し修正
6. [T-102] scope 外 real 所見: production の git runner が ambient `GIT_*` を継承する。変わらず
7. [T-103] 未着手: never-issued 状態の real artifact 由来 refusal vector を別 node で撃つテスト。変わらず
8. [T-011] 科学レーン floor 実測。残 gate = [T-088] → 段階 3・4 → 実行 revision 束縛 → lineage。変わらず
9. [T-097] 裁定待ち: placeholder 検出の対象族拡張。変わらず
10. [T-099] 裁定待ち: 凍結成果物に placeholder が入った場合の専用 waiver 契約。変わらず
11. [T-100] 裁定待ち: 検出語彙の拡張と予測値先書きの構造的検出。変わらず
12. [T-096] 裁定待ち: driver 予算定数の hard cap 化。変わらず
13. [T-101] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
14. [T-104] 裁定待ち (dev-wave 自己改善): 予算値の引き上げ可否の独立審査か reference 再編か。変わらず
15. [T-108] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
16. [T-089] 測定後の hardening と裁定 (前倒し対象外): 二重 reason-tag 描画。変わらず
17. [T-090] 測定後の hardening と裁定 (前倒し対象外): `VerifiedFreeze.document` が mutable dict。変わらず
18. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
19. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
20. [T-009] 延期: AGENTS.md 追記は 1 cycle 後。**条件見直しを /rulings で提起済み** (16 番)
21. [T-060] 延期: WAL 用語運用の明文化は 1 cycle 後。同上
22. [T-010] 延期: B-008 再試験は 1 cycle 後に再評価。同上
23. [T-012] 延期: pilot 凍結維持。同上
24. [T-082] 延期: 全 caller 移行は 1 cycle 後。同上

## 2026-07-26 (5) — [T-106][T-107] parser-authoritative 契約を確定し受理差を境界テストで固定 (テストのみ・本番 0 byte、branch worktree-dev-wave-t091-093-hardening、計測なし)

/dev-wave 1 回。2026-07-26 にユーザーが裁定した (a)/(a) を実施した。差分は
`test_s8b_ratified_verify.py` の 199 行 (純追加) だけで、production・schema・role・凍結成果物の
bytes は不変、受理集合は拡大も縮小もしない。設計裁定は D90、材料は
`output/insights/2026-07-26_t106-t107-parser-authoritative.md`、逐語は同 `-verbatim.md`、
変異台帳は同 `-mutation-ledger.json`。実装 commit = `c4efa3b`。
検出 3 語は D88 (6) を継承し LP-1 / LP-2 / LP-3 の記号参照で書く。

- [T-106] **消化**。ratified に再 parse を入れず、射程を D90 (3)(4) に明記した。
- [T-107] **消化**。受理集合の正本を **parser module** (関数単体でなく module) と明文化した。
  定数・helper で受理集合が動くため関数名では抜け道が残る、という段 3 の指摘 (A-5) を採用した。
- **裁定前提は実ファイル編集で実測した (模擬なし)**。role と output_schema に 1 byte 追記すると
  既存封印 prediction の検証が実際に割れ (`sources.*.sha256 が実ファイルと不一致`)、
  `git checkout --` 復元後に緑へ戻ることを確認した。これが [T-107] の根拠である。
- **親の実測を段 3 が訂正した (A-6、real)**。親は「ratified は parser の blob sha を照合するだけ」と
  書いたが、ratified は selector freeze module を import し、それが parser module を module-level で
  import する。**ratified は parser の import 可能性には感応**し、非感応なのは raw 分類の意味論だけ。
- **D89 の射程漏れを補完した**。D89 は floor だけを挙げていたが、parser 感応は生成層
  (`record_agent_attempt`) と検証層 (`verify_prediction_freeze`) の 2 層で、検証層の消費者は 4 経路。
  **うち floor は dormant** (official が core で無条件拒否される)。
- **scope 外として 2 件を不採用にした**。consumer 閉集合の AST テスト (構文形状しか固定せず
  `if False`・alias・`getattr` を見逃す一方、無害な refactor で偽赤になる) と、D90 の統治機構
  (「全受理集合変更に新 D 必須」「新 consumer は必ず verify 経由」)。後者はユーザー裁定 2 件の射程外の
  新設で、DW-G03 の独立 2 例も無い。裁定パッケージへ送る ([T-110])。
- **素材: レビューが実在の検出漏れを見つけた。** 当初実装は private 関数 `_reparse_agent_raw` を
  直呼びして「status 照合の変異を殺す」と主張していたが、公開経路では `valid` 行の
  `parser_error_code` が手前で `None` に強制されるため**等価変異**であり、偽の KILL だった (RA-1)。
  実効的な変異 (記録 error code の照合を消す) は当時**誰も捕まえていなかった**。公開経路の負例
  (`invalid` + 誤 code) へ差し替えた結果、この変異が新テスト固有の KILL になった。
- **変異 matrix (親実測、統合 commit 前)**: 事前登録 **5/5 が実測と一致**。帰属 3 (S3 = 記録 error code の
  照合、S4 = 正例による過剰拒否検出、S6 = 診断シグナル pin)、非帰属 control 2 (S1 / S2 は既存テストも
  KILL)。control は**変更前 Git HEAD のテスト集合**とし、本差分が純追加であることを利用して
  新 node の `--deselect` で exact に再現した。harness は アンカー一意性 assert・注入 diffstat 記録・
  `git checkout --` 復元 + 内容一致検査・flock 単一走行を持ち、全走後の tree は clean。
- **事前登録の誤りが 3 件あり、erratum として台帳に残した** (材料 §8)。S3 の等価変異 (RA-1 が検出)、
  S5 の到達不能 (RA-2 が検出。`_fixed_commit_all` へ戻すと直後の base commit が空 commit で先に落ちる)、
  S6 の期待値誤り (親の誤り。本走で判明)。**S1 が非帰属だった**ことも収穫で、ratified に再 parse を
  足すと既存 42 node が落ちる — この性質は本 wave 以前から既存テスト群が厚く守っていた。
- **エージェント工数**: codex 子 6 本 (プラン 1・敵対相談 2・実装 1・レビュー 2 は max/high、fix 1・
  焦点再 1)。**相談 2 本・レビュー 2 本・焦点再 1 本のすべてが NO-GO**。親の provisional 裁定は
  (P2) が否定され、「delta 4 点」も水増し (実質 3 点) と判定された。
- **検査 (統合 commit 直前の実測)**: 受入全走 **3059 passed / 18 skipped / 0 failed** (1811.26s)。
  基線 3058 (前 wave 実績) に対し +1 = 本 wave の新テスト 1 本、node 消失 0。`check_docs` rc=0。
- **task-run pilot は非発火** ([T-012] で凍結維持のため。DW-O07 の発火条件を満たさない)。
- **スキル自己改善 (gate 発火・候補 3 / 採用 1 / 裁定送り 2)**: 採用は `DW-S03` の 1 語置換
  (「変異位置の誤り」→「変異の帰属不成立」、+3 bytes)。**F28 の同型再発**を実測したための是正で、
  同 F へ再発を追記した。F28 自身の「再発検知」欄が既に「相談・レビューのレンズに事前登録変異の
  kill 帰属を含めれば実測前に落とせる」と書いていたが、レンズ項目として明示されていなかったため
  今回は段 3 をすり抜け段 6 で捕まった。予算は 23987 → **23990 / 24000 (余裕 10)**。
  残り 2 件は予算に収まらず [T-111] として裁定へ送る (前例 = [T-101] / [T-104] / [T-108])。

### 次の一手
1. [T-109] **新セッションで着手 (ユーザー裁定済み)**: `/dev-wave クロスプロトコル対応` を再実行する。
   **着手前に (a) の裁定が要る** — trace-hook の置き場所を out-of-tree patch (D16 の一回限りの例外)
   とするか、submodule ブランチ (gitlink 前進 → 承認定数の再承認 + 再凍結) とするか。
   **AI 推奨 = patch 例外を許す**。正本 = `output/insights/2026-07-26_s1-cross-protocol-gate-survey.md` §5
2. [T-088] **人間手番 (承認済み)**: `tools/pegasus/submit_floor.sh --dry-run` → 明示実行。
   期待は driver rc=2。[T-109] との順序制約は解消済み。変わらず
3. [T-110] **新規・裁定待ち**: 本 wave が scope 外として不採用にした 2 件の扱い。
   (i) parser 感応 consumer の閉集合を機械的に固定するか (現行 AST 案は構文形状しか固定できず不採用。
   到達意味論を固定する別機構が要る)、(ii) 受理集合変更時の手続義務 (新 D・境界テスト同時更新) を
   制度化するか。どちらも DW-G03 の独立 2 例が無いため、制度化には裁定が要る。正本 =
   `output/insights/2026-07-26_t106-t107-parser-authoritative.md` §6 と D90 (6)
4. [T-111] **新規・裁定待ち (dev-wave 自己改善)**: 予算に収まらなかった作法 2 件 —
   (i) `DW-S01` の「裁定前提は実ファイル編集で測る」と `DW-O19` の「一時変異の本走は統合 commit 後だけ」の
   関係が入口・reference から一意に読めない (本 wave は「段 1 前の前提実測は本走ではない」と解釈し、
   `DW-O19` の復元規律だけを借りた)、(ii) 段 3 のレンズに「親自身の実測値の再検証」を明示する規則
   (本 wave では親が prompt へ明示的に書いたため A-6 が親の過大表現を捕まえたが、`DW-S03` には暗黙にしかない)。
   `docs/dev-wave/**` は hard ceiling 24000 に対し 23990 で余裕 10。[T-101] / [T-104] / [T-108] と併せ、
   予算値の引き上げ可否を独立審査するか reference を再編するかの裁定が要る
5. [T-105] **裁定済み → [T-011] の後**: `_run_artifact_bytes` の `FileNotFoundError` 素通し修正。変わらず
6. [T-102] scope 外 real 所見: production の git runner が ambient `GIT_*` を継承する。変わらず
7. [T-103] 未着手: never-issued 状態の real artifact 由来 refusal vector を別 node で撃つテスト。変わらず
8. [T-011] 科学レーン floor 実測。残 gate = [T-088] → 段階 3・4 → 実行 revision 束縛 → lineage。変わらず
9. [T-097] 裁定待ち: placeholder 検出の対象族拡張。変わらず
10. [T-099] 裁定待ち: 凍結成果物に placeholder が入った場合の専用 waiver 契約。変わらず
11. [T-100] 裁定待ち: 検出語彙の拡張と予測値先書きの構造的検出。変わらず
12. [T-096] 裁定待ち: driver 予算定数の hard cap 化。変わらず
13. [T-101] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
14. [T-104] 裁定待ち (dev-wave 自己改善): 予算値の引き上げ可否の独立審査か reference 再編か。変わらず
15. [T-108] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
16. [T-089] 測定後の hardening と裁定 (前倒し対象外): 二重 reason-tag 描画。変わらず
17. [T-090] 測定後の hardening と裁定 (前倒し対象外): `VerifiedFreeze.document` が mutable dict。変わらず
18. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
19. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
20. [T-009] 延期: AGENTS.md 追記は 1 cycle 後。変わらず
21. [T-060] 延期: WAL 用語運用の明文化は 1 cycle 後。変わらず
22. [T-010] 延期: B-008 再試験は 1 cycle 後に再評価。変わらず
23. [T-012] 延期: pilot 凍結維持。変わらず
24. [T-082] 延期: 全 caller 移行は 1 cycle 後。変わらず

## 2026-07-26 (6) — [T-103] never-issued vector: 調査の結果「実装しない」と裁定 (設計のみ・コード 0 byte、branch worktree-dev-wave-t091-093-hardening、計測なし)

/dev-wave 1 回 (引数なし)。worklog 候補から唯一の AI 手番として [T-103] を選び、段 4 で
**実装しない**と裁定して `DW-S04` の `4→7→8→9` を採った。**実装差分がないため変異 matrix と
受入全走は対象外**である。材料レポート = `output/insights/2026-07-26_t103-never-issued-vector.md`、
逐語 = 同 `-verbatim.md` (原文 SHA-256・byte 数・defang 箇所を併記)。

- **裁定の骨子は `DW-G02`。** 初回 E2E cycle 前の hardening は correctness 判定・selected/tie・数値・
  proof 参照・試行欠落を実際に変える欠陥だけを blocker とし、それ以外は 1 cycle 後へ送る。
  レンズ B が層ごとに棚卸しした結果、T-103 が守るのは **standalone gate の診断文字列だけ**だった。
  実 freeze は v1 (floor/budget が null) なので active-valid receipt が legacy 2 拒否を消しても
  floor/budget の 2 拒否が必ず残り、gate は常に `allowed=False`。legacy 呼出しが丸ごと消えても
  campaign も試行も 1 件も増えない。
- **入れることに害があると判定した。** 提案 node は `assert actual != recorded` を通じて
  「**legacy artifact が修復されるとテストが失敗する**」逆向きの圧力を作る。重い一体試験が
  無関係な正当変更で落ちれば exact assert を prefix 化・削除する誘因になり、
  絶対規律 2 に対する構造的リスクの新設になる。
- **前例と整合させた。** 初回 cycle 前に実装したテスト強化 ([T-091]/[T-092]/[T-093]/[T-098]/
  [T-106]/[T-107]) は**すべてユーザーが名指しで裁定済み**。[T-103] は「未着手」で裁定を受けておらず、
  `DW-G02` の既定が生きる。親が独断で既定を上書きしない。
- **親 brief の 6 前提のうち 5 件が否定された。** (P3) 「N2 は scope 内」= **refuted** (kill set が
  N1 の部分集合で限界検出力ゼロ、かつ live worktree に対する非原子的 sentinel)。
  (P5) 「走査順依存で非決定的かもしれない」= **refuted、方向が逆** (`_iter_sources` の
  depth-first insertion order と固定 JSON 順により決定的)。(P1)(P2)(P6) は部分 refuted。
  妥当は (P4) のみで、それも「この snapshot の fail-fast 表示が 4 件」という限定付き。
- **素材: 「stub していない」と「fixture に対する実 verifier」は別である。**
  `_t080_stub_free_e2e_repo` は receipt 発行経路でだけ隔離 subprocess を起動して全 module の
  `ROOT` が fixture を指すことを assert するが、`issue_receipt=False` は**その手前で return する**。
  `s1_known_axes_freeze.verify_document` で注入 resolver を使うのは source 走査だけで、
  generator hash・`frozen_at_head` ancestor・`ccbench_pin`・末尾の機械再構成は
  **module-level `ROOT` 束縛**である。本 vector は source loop で先に raise するため到達しないが、
  「fixture に実 verifier を通した」という表現は成立しない ([T-112])。
- **素材: root-isolation 変異を誰も殺していない。** driver の
  `source_resolver=lambda relative: root / relative` を `ROOT / relative` に変える変異は、
  提案 N1/N2・既存 hermetic primary states・既存 g7 の**すべてが SURVIVE** する。
  殺すには fixture 側だけ bytes を分岐させる control が要る ([T-113])。
- **素材: 事前登録しようとした変異はほぼ帰属不成立だった。** legacy 呼出しの削除、floor/budget
  refusal の削除、`allowed` の退化、observation 漏出、never-issued 判定の変更、design/known 比較の
  無効化は、いずれも既存テストが先に殺す。新テスト固有になり得たのは診断 payload の suffix 欠落と
  診断順の変更だけで、受理境界の変異ではない。
- **親の実測の一般化が過大だった (段 3 が訂正)。** known の drift は unique path 3 件だが
  source **record は 12 件**。holdout の drift は `design_source` だけでなく **`generator` にもある**。
  「refusal ちょうど 4 件」は fail-fast 表示が 4 件という意味であって潜在欠陥が 4 個ではない。
- **素材: 逐語の凍結が holdout 未既知性 gate を自己発火させかけた。** レンズ A の所見 A-7 が
  三軸の canonical encoding を名指ししたため、**defang なしの逐語は rr80 で conjunction hit 1**
  になることを反実仮想で実測した。D88 (6) と同型の 1:1 可逆置換 (三軸 key 直後の半角 `=` を全角へ)
  を **3 箇所**に適用し、置換後 0 hit を機械確認した。**defang は装飾ではなく実際の発火を 1 件防いだ。**
- **エージェント工数**: codex 子 3 本 (プラン 1・敵対レンズ 2、いずれも `gpt-5.6-sol` /
  `reasoning=max` / read-only)。**3 本すべて NO-GO または要修正判定**。段 2 が親前提 4 件を要修正、
  段 3 が blocker 6 件・must-fix 6 件・nit 2 件。実装子・レビュー子は起動していない (実装しない裁定)。
- **検査 (記録 commit 前の実測)**: 三軸 conjunction = 走査 5 ファイル・rr80/rr20 両方で **hit 0**
  (per-axis も全軸 0)、literal placeholder = `check_docs` **rc=0**。
  **受入全走と変異 matrix は実装差分 0 byte のため対象外**である。
- **記録後検査 (F34、記録 commit の後に再走した実測)**: `check_docs` **rc=0**、
  `check_ai_provenance` = **366 件・違反なし**、焦点 (repo scan invariant + `test_check_docs` +
  real-repo serialization) = **117 passed**。
- **worklog をローテーションした**。102KB > 閾値 100KB のため 2026-07-25 (1)〜(7) を
  `docs/archive/worklog-phase3-0725.md` へ移動した (現行 58KB)。ID 保存則はローテーション境界を
  越えて成立している (`check_docs` rc=0 が機械確認)。
- **task-run pilot は非発火** ([T-012] で凍結維持のため `DW-O07` の発火条件を満たさない)。
- **スキル自己改善 (gate 発火・候補 3 / 採用 3 / 裁定送り 0)**。**本 wave で初めて予算が足りた** —
  入口が既に全条件を名指しで持つ巻き戻し規則が `DW-O08`/`O09`/`O10`/`O13` へ 4 重に複製されており
  (routing 5 違反)、これを取って **412 bytes を回収**した。義務は入口に無傷で残る。
  (i) `DW-G05` を「must-fix の成果物影響」から「成果物影響」へ広げ、**段 1 の scope にも**
  成果物影響を 1 行で書く義務を課した。書けなければ `DW-G02` に従い子を起動せずその場で
  1 cycle 後へ送る。本 wave は段 4 で初めて `DW-G02` の適用に気づき、codex 子 3 本 (max) を
  投入した後に「実装しない」へ倒れた。**段 1 でこの 1 行を書いていれば投入前に判明していた。**
  (ii) `DW-S01` へ「検査・テストを増やす wave では既存被覆を brief 前に確認し、純増する検出力だけを
  scope に書く。既存被覆を確認せずに子を起動しない」を追加。本 wave は親が偶然 grep して
  既存 g7 を発見したが、遅れれば段 2〜5 が既存テストの複製を作る経路が開いていた。
  予算は 23990 → **23984 / 24000 (余裕 16)**。事故は発生していないので failures / decisions は
  変更しない。**[T-101] / [T-104] / [T-108] / [T-111] の裁定待ちは解消していない** — 本 wave が
  作った余裕は 16 bytes で、それらを収容できる量ではない。

### 次の一手
1. [T-109] **新セッションで着手 (ユーザー裁定済み)**: `/dev-wave クロスプロトコル対応` を再実行する。
   **着手前に (a) の裁定が要る** — trace-hook の置き場所を out-of-tree patch (D16 の一回限りの例外)
   とするか、submodule ブランチ (gitlink 前進 → 承認定数の再承認 + 再凍結) とするか。
   **AI 推奨 = patch 例外を許す**。正本 = `output/insights/2026-07-26_s1-cross-protocol-gate-survey.md` §5
2. [T-088] **人間手番 (承認済み)**: `tools/pegasus/submit_floor.sh --dry-run` → 明示実行。
   期待は driver rc=2。変わらず
3. [T-103] **裁定待ちへ差し戻し (本 wave の成果)**: (a) 1 cycle 後へ送る (**AI 推奨**)、
   (b) レンズ B 案の最小 node (軽量 fixture + `design_source` のみ) を今実装、(c) 取り下げ。
   正本 = `output/insights/2026-07-26_t103-never-issued-vector.md` §4 と §6
4. [T-112] **新規・裁定待ち (本 wave の real 所見)**: `s1_known_axes_freeze` の root 束縛が不完全で、
   generator hash・`frozen_at_head` ancestor・`ccbench_pin`・末尾の機械再構成が module-level `ROOT` を
   読む。注入 `source_resolver` と分岐しうる。**本番コードに触る**ため測定前後の扱いに裁定が要る
5. [T-113] **新規・裁定待ち (本 wave の real 所見)**: driver の `source_resolver` を `ROOT` 固定へ
   変える root-isolation 変異を、既存テスト・提案テストの**いずれも殺せない**。fixture 側だけ
   bytes を分岐させる control が要る。テストのみだが `DW-G02` の判断が要る
6. [T-114] **新規・裁定待ち (本 wave の real 所見)**: never-issued の全層 scope 漏れ。
   `run_block` の campaign-start / result / WAL と report の never-issued 歴史照合が未被覆
   (report 側は autouse monkeypatch で Git 履歴から隔離されている)
7. [T-110] **裁定待ち**: parser 感応 consumer の閉集合を機械的に固定するか、受理集合変更時の
   手続義務を制度化するか。変わらず
8. [T-111] **裁定待ち (dev-wave 自己改善)**: 予算に収まらなかった作法 2 件。変わらず
9. [T-105] **裁定済み → [T-011] の後**: `_run_artifact_bytes` の `FileNotFoundError` 素通し修正。変わらず
10. [T-102] scope 外 real 所見: production の git runner が ambient `GIT_*` を継承する。変わらず
11. [T-011] 科学レーン floor 実測。残 gate = [T-088] → 段階 3・4 → 実行 revision 束縛 → lineage。変わらず
12. [T-097] 裁定待ち: placeholder 検出の対象族拡張。変わらず
13. [T-099] 裁定待ち: 凍結成果物に placeholder が入った場合の専用 waiver 契約。変わらず
14. [T-100] 裁定待ち: 検出語彙の拡張と予測値先書きの構造的検出。変わらず
15. [T-096] 裁定待ち: driver 予算定数の hard cap 化。変わらず
16. [T-101] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
17. [T-104] 裁定待ち (dev-wave 自己改善): 予算値の引き上げ可否の独立審査か reference 再編か。変わらず
18. [T-108] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
19. [T-089] 測定後の hardening と裁定 (前倒し対象外): 二重 reason-tag 描画。変わらず
20. [T-090] 測定後の hardening と裁定 (前倒し対象外): `VerifiedFreeze.document` が mutable dict。変わらず
21. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
22. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
23. [T-009] 延期: AGENTS.md 追記は 1 cycle 後。変わらず
24. [T-060] 延期: WAL 用語運用の明文化は 1 cycle 後。変わらず
25. [T-010] 延期: B-008 再試験は 1 cycle 後に再評価。変わらず
26. [T-012] 延期: pilot 凍結維持。変わらず
27. [T-082] 延期: 全 caller 移行は 1 cycle 後。変わらず

## 2026-07-26 (7) — /rulings: 裁定待ち 26 件を索引化 — 見送り台帳の発火 1 件と繰り越し条件の見直しを新規に立てた (docs-only・コード 0 byte、branch worktree-dev-wave-t091-093-hardening、計測なし)

`/rulings` 1 回。索引 26 件・詳説 5 件を提示した。**ユーザー裁定はまだ無い** (提示のみ)。
自己改善 gate が発火したためクラス 2 へ昇格し、起動手順を完了してから編集した。

- **新規に立てた 3 件**:
  - **[T-057] の発火を確認した (見送り台帳)。** 述語 `P6_source := full_suite_duration_s > 180` は
    worklog 記録の全走 **239s (2026-07-25) と 1811.26s (2026-07-26) の両方で成立**しており、
    2026-07-19 の事実状態「180 秒を大幅に下回る」は現状と一致しない。**再走はせず記録値の照合のみ**で、
    239s → 1811s の 7.6 倍差が runner/env・並列度の違いによるかは未確認。台帳行へ発火を追記した。
  - **[T-115] 「1 cycle 完走まで凍結」条件の見直し**。収集規則 6 (条件が未成立のまま後続が塞がって
    いるなら条件の見直し自体を裁定待ちに立てる) の発火。凍結の解除条件である 1 cycle は [T-088] の
    人間手番で止まっており、2026-07-25 と本日の 2 回、AI 手番がほぼ空になった。
  - **push 判断**: local main (`09c9f91`) に未 push **29 commit**。AI は push しない規約のため提示のみ。
- **前回の収集はこの発火を拾えていなかった。** [T-057] の条件は 2026-07-25 時点で既に成立していたが、
  2026-07-26 (4) の `/rulings` は surface していない。
- **スキル自己改善 (gate 発火・候補 1 / 採用 1 / 裁定送り 0)**: 原因は収集規則 5 が
  「前回以降の wave が新設・変更した gate / validator / producer / 検査の**語**に触れる述語だけを
  照合する」と定めていたことにある。**観測量の閾値を述語とする項 (時間・件数・サイズ) には
  語の照合では構造的に到達できない**。規則 5 を是正し、閾値述語は worklog が記録した実測値と
  直接照合すると明記した。あわせて誤った一般化「発火は wave が起こす」を削った。
  予算は `docs/skill-self-improvement.md` の rulings 節と**逐語同一の 1 文**が command 側にも
  複製されていた無駄を取って作り、4421 → **4479 / 4500 (余裕 21)**。
  事故は発生していないので failures / decisions は変更しない。
- **検査**: `check_docs` rc=0。テスト差分が無いため受入全走は対象外。

### 次の一手
1. [T-088] **人間手番 (承認済み・未実行)**: `tools/pegasus/submit_floor.sh --dry-run` → 明示実行。
   期待は driver rc=2。**現在 AI 手番が空になっている根本原因**であり、[T-115] の解除条件でもある
2. [T-115] **新規・裁定待ち**: 「8b + 層3 の 1 cycle 完走まで プロセス系を凍結」([T-083] 裁定) の
   条件見直し。**AI 推奨 = 解除条件を「[T-088] の実行まで」に付け替える** (測定が始まっていない間は
   交絡が生じないため)。保留中は [T-009] / [T-060] / [T-010] / [T-012] / [T-082] と自己改善群が塞がる
3. [T-109] **新セッションで着手 (ユーザー裁定済み)**: `/dev-wave クロスプロトコル対応` を再実行する。
   **着手前に (a) の裁定が要る** — trace-hook の置き場所を out-of-tree patch (D16 の一回限りの例外)
   とするか、submodule ブランチ (gitlink 前進 → 承認定数の再承認 + 再凍結) とするか。
   **AI 推奨 = patch 例外を許す**。正本 = `output/insights/2026-07-26_s1-cross-protocol-gate-survey.md` §5
4. [T-057] **新規・裁定待ち (見送り台帳の発火)**: 全走時間が閾値を超えている。
   **AI 推奨 = (a) まず原因を実測する小さい調査を 1 回**。述語の正本 =
   `output/insights/2026-07-19_backlog-triage.md` B-055、台帳行 = `docs/phase3.md` テスト衛生
5. [T-103] **裁定待ち**: (a) 1 cycle 後へ送る (**AI 推奨**)、(b) 最小 node を今実装、(c) 取り下げ。
   正本 = `output/insights/2026-07-26_t103-never-issued-vector.md` §4 と §6。変わらず
6. [T-112] 裁定待ち: `s1_known_axes_freeze` の root 束縛が不完全 (本番コードに触る)。変わらず
7. [T-113] 裁定待ち: root-isolation 変異を殺す control が無い。変わらず
8. [T-114] 裁定待ち: never-issued の全層 scope 漏れ。変わらず
9. [T-110] 裁定待ち: parser 感応 consumer の閉集合固定か手続義務の制度化か。変わらず
10. [T-111] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
11. [T-105] **裁定済み → [T-011] の後**: `_run_artifact_bytes` の `FileNotFoundError` 素通し。変わらず
12. [T-102] scope 外 real 所見: production の git runner が ambient `GIT_*` を継承する。変わらず
13. [T-011] 科学レーン floor 実測。残 gate = [T-088] → 段階 3・4 → 実行 revision 束縛 → lineage。変わらず
14. [T-097] 裁定待ち: placeholder 検出の対象族拡張。変わらず
15. [T-099] 裁定待ち: 凍結成果物に placeholder が入った場合の専用 waiver 契約。変わらず
16. [T-100] 裁定待ち: 検出語彙の拡張と予測値先書きの構造的検出。変わらず
17. [T-096] 裁定待ち: driver 予算定数の hard cap 化。変わらず
18. [T-101] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
19. [T-104] 裁定待ち (dev-wave 自己改善): 予算値の引き上げ可否の独立審査か reference 再編か。変わらず
20. [T-108] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
21. [T-089] 測定後の hardening と裁定 (前倒し対象外): 二重 reason-tag 描画。変わらず
22. [T-090] 測定後の hardening と裁定 (前倒し対象外): `VerifiedFreeze.document` が mutable dict。変わらず
23. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
24. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
25. [T-009] 延期: AGENTS.md 追記は 1 cycle 後。**[T-115] の裁定対象**
26. [T-060] 延期: WAL 用語運用の明文化は 1 cycle 後。**[T-115] の裁定対象**
27. [T-010] 延期: B-008 再試験は 1 cycle 後に再評価。**[T-115] の裁定対象**
28. [T-012] 延期: pilot 凍結維持。**[T-115] の裁定対象**
29. [T-082] 延期: 全 caller 移行は 1 cycle 後。**[T-115] の裁定対象**

## 2026-07-26 (8) — /rulings: ユーザーが 2 件を裁定 — プロセス系 freeze の解除と D16 の一回限り例外 (docs-only・コード 0 byte、branch worktree-dev-wave-t091-093-hardening、計測なし)

`/rulings` の続き。直前エントリ 2026-07-26 (7) が提示した索引からユーザーが 2 件を裁定した。
本エントリに実装は含まない (コード 0 byte)。

- **ユーザー裁定 (2026-07-26)**:
  - **[T-115] = (a) 推奨どおり。** プロセス系 freeze の解除条件を「8b + 層3 の 1 cycle 完走」から
    **「[T-088] の実行 (床値実測の開始)」**へ付け替える。**[T-088] 実行までは freeze を解除**し、
    実測開始後に再び効かせる。正本 = `docs/phase3.md` の 2026-07-26 改訂。
  - **[T-109] (a) = 例外を許す。** cross-protocol の trace-hook 試作を、D16 の分岐表に反して
    **out-of-tree patch** に置いてよい。**射程は試作 1 回限り**で D16 の表そのものは改訂しない。
    記録 = D16 の「一回限りの試作例外」欄。
- **[T-115] の適用範囲を親が限定して記録した (裁定文の射程確認)。** 解除されるのは
  **本番コードに触らない**項 ([T-009] / [T-060] / [T-012] / dev-wave 自己改善 / 新規裁定パッケージ化)。
  本番コードに触る項 ([T-082] / [T-089] / [T-090] / [T-102] / [T-105] / [T-112]) は `DW-G02`
  (初回 cycle 前 hardening の限定) が**別規則として生きる**ため引き続き測定後に回す。
  freeze は [T-083] 裁定、`DW-G02` は dev-wave reference が正本で、両者は別物である。
  この区別は裁定文に明示されていないため親の解釈であり、異なる意図なら再裁定を要する。
- **[T-109] (a) の記録先を D16 本文の拡張欄にした。** 前例 (第4類 D18 / 第5類 D20 の追加) と同形で、
  新 D を起票していない。射程 (試作 1 回限り・inert 要件・本採用時の再裁定) を欄内に明記した。
- **これにより AI 手番が復活した** — [T-009] / [T-060] / [T-012] と `/dev-wave クロスプロトコル対応`
  が着手可能になった。2026-07-25 と 2026-07-26 (7) の 2 回、AI 手番がほぼ空だった状態は解消する。
- **検査**: `check_docs` rc=0。テスト差分が無いため受入全走は対象外。

### 次の一手
1. [T-109] **着手可能 (裁定完了)**: `/dev-wave クロスプロトコル対応` を新セッションで実行する。
   (a) は 2026-07-26 に裁定済み (patch 例外)。残る (c)〜(i) は同 wave の段 1 で scope 化する。
   正本 = `output/insights/2026-07-26_s1-cross-protocol-gate-survey.md` §5、D16 の一回限り例外欄
2. [T-088] **人間手番 (承認済み・未実行)**: `tools/pegasus/submit_floor.sh --dry-run` → 明示実行。
   期待は driver rc=2。**実行した時点で [T-115] のプロセス系 freeze が再び効く**
3. [T-057] **裁定待ち (見送り台帳の発火)**: 全走時間が閾値を超えている。
   **AI 推奨 = (a) まず原因を実測する小さい調査を 1 回**。変わらず
4. [T-103] **裁定待ち**: (a) 1 cycle 後へ送る (**AI 推奨**)、(b) 最小 node を今実装、(c) 取り下げ。変わらず
5. [T-112] 裁定待ち: `s1_known_axes_freeze` の root 束縛が不完全 (本番コードに触る)。変わらず
6. [T-113] 裁定待ち: root-isolation 変異を殺す control が無い。変わらず
7. [T-114] 裁定待ち: never-issued の全層 scope 漏れ。変わらず
8. [T-110] 裁定待ち: parser 感応 consumer の閉集合固定か手続義務の制度化か。変わらず
9. [T-009] **着手可能 ([T-115] により解除)**: dev-wave 実装子が負う規律の所在を AGENTS.md へ明文化する
10. [T-060] **着手可能 ([T-115] により解除)**: WAL 用語運用の明文化
11. [T-012] **着手可能 ([T-115] により解除)**: task-run pilot の凍結解除可否を再評価する
12. [T-104] 裁定待ち (dev-wave 自己改善): 予算値の引き上げ可否の独立審査か reference 再編か。
    **[T-101] / [T-108] / [T-111] の前提**であり、freeze 解除後も予算が塞いでいる
13. [T-101] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
14. [T-108] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
15. [T-111] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
16. [T-105] **裁定済み → [T-011] の後**: `_run_artifact_bytes` の `FileNotFoundError` 素通し。変わらず
17. [T-102] scope 外 real 所見: production の git runner が ambient `GIT_*` を継承する。変わらず
18. [T-011] 科学レーン floor 実測。残 gate = [T-088] → 段階 3・4 → 実行 revision 束縛 → lineage。変わらず
19. [T-097] 裁定待ち: placeholder 検出の対象族拡張。変わらず
20. [T-099] 裁定待ち: 凍結成果物に placeholder が入った場合の専用 waiver 契約。変わらず
21. [T-100] 裁定待ち: 検出語彙の拡張と予測値先書きの構造的検出。変わらず
22. [T-096] 裁定待ち: driver 予算定数の hard cap 化。変わらず
23. [T-089] 測定後の hardening と裁定: 二重 reason-tag 描画。変わらず
24. [T-090] 測定後の hardening と裁定: `VerifiedFreeze.document` が mutable dict。変わらず
25. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
26. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
27. [T-115] **消化**。freeze 解除条件を [T-088] 実行までに付け替えた (上記)
28. [T-010] 延期: B-008 再試験は新規 background session が発火条件。**[T-115] により凍結は解けたが、
    発火条件そのものは別途成立が要る**
29. [T-082] 延期: prefix 容認 reader の用途別移行。**本番コードのため測定後** (上記の射程限定)

## 2026-07-26 (9) — /rulings: ユーザーが 5 件を推奨どおり一括裁定 — push 承認と hardening 4 件の配置確定 (docs-only・コード 0 byte、branch worktree-dev-wave-t091-093-hardening、計測なし)

`/rulings` の続き。2026-07-26 (8) の詳説 5 件をユーザーが「推奨どおり」で一括裁定した。
本エントリに実装は含まない (コード 0 byte)。実行系 (push) は Pegasus 規約でユーザー手番。

- **ユーザー裁定 (2026-07-26)**: 5 件すべて AI 推奨案。
  - **push = 承認 → ユーザー実行。** local main (`66cc3d8`、未 push 31 commit) の push を承認。
    **AI は push しない** (Pegasus 規約、前例 = 2026-07-25 (4) / (7))。コマンドは提示済み。
  - **[T-112] = (a) 床値実測の後に直す。** `s1_known_axes_freeze` の root 束縛不完全は本番コードに
    触るため、測定直前の変更で原因切り分けが濁るのを避ける。現に実害が出ていない
    (検証が手前で停止するため到達しない) ことが根拠。
  - **[T-113] = (a) 対照テストを今足す。** fixture 側の bytes だけを分岐させ、root-isolation 変異を
    KILL する control を新設する。**この裁定は `DW-G02` の既定を上書きする** — 本 control は
    成果物の値を変えないため規則どおりなら実測後送りだが、ユーザーが前倒しを承認した
    (前例 = [T-091] / [T-092] / [T-093] の前倒し承認、2026-07-25 (7))。
  - **[T-114] = (a) 一巡後に統合テストとして足す。** 上流 3 層 (campaign 起動 / WAL / report) は
    一巡すれば実データが通るため、作り物の環境を組むより実物で検査する方が安く確実。
  - **[T-110] = (a) 手続きの義務化だけ入れる。** 「受理集合を変える改修は新しい設計判断の記録を
    起こし、境界テストを同時に更新する」を規約化する。**機械検査は新設しない** —
    AST 案は構文形状しか固定できず不採用済み、到達意味論の機械固定は `DW-G03` の独立 2 例が無い。
- [T-115] **は前エントリ 2026-07-26 (8) で消化済み** (freeze 解除条件を [T-088] 実行までに
  付け替えた)。ここでの再掲は ID 保存則の sink としてであり、新しい作業ではない。
- **AI 手番が 6 件になった** — [T-109] (cross-protocol wave)、[T-113]、[T-110]、[T-009]、[T-060]、
  [T-012]。2026-07-25 と 2026-07-26 (7) の 2 回、AI 手番がほぼ空だった状態は解消した。
- **検査**: `check_docs` rc=0。テスト差分が無いため受入全走は対象外。

### 次の一手
1. [T-109] **着手可能 (裁定完了)**: `/dev-wave クロスプロトコル対応` を新セッションで実行する。
   (a) = patch 例外は裁定済み (D16 の一回限り例外欄)。残る (c)〜(i) は同 wave の段 1 で scope 化する
2. [T-088] **人間手番 (承認済み・未実行)**: `tools/pegasus/submit_floor.sh --dry-run` → 明示実行。
   **実行した時点で [T-115] のプロセス系 freeze が再び効く**
3. [T-113] **裁定済み → 着手可能 (前倒し承認)**: fixture 側 bytes を分岐させ root-isolation 変異を
   KILL する control を新設する。正本 = `output/insights/2026-07-26_t103-never-issued-vector.md` §5-2
4. [T-110] **裁定済み → 着手可能**: 受理集合を変える改修の手続義務を規約化する (機械検査は新設しない)。
   正本 = `output/insights/2026-07-26_t106-t107-parser-authoritative.md` §6 と D90 (6)
5. [T-009] **着手可能 ([T-115] により解除)**: dev-wave 実装子が負う規律の所在を AGENTS.md へ明文化する
6. [T-060] **着手可能 ([T-115] により解除)**: WAL 用語運用の明文化
7. [T-012] **着手可能 ([T-115] により解除)**: task-run pilot の凍結解除可否を再評価する
8. [T-057] **裁定待ち (見送り台帳の発火)**: 全走時間が閾値を超えている。
   **AI 推奨 = (a) まず原因を実測する小さい調査を 1 回**。変わらず
9. [T-103] **裁定待ち**: (a) 1 cycle 後へ送る (**AI 推奨**)、(b) 最小 node を今実装、(c) 取り下げ。変わらず
10. [T-104] **裁定待ち (dev-wave 自己改善)**: 予算値の引き上げ可否の独立審査か reference 再編か。
    **[T-101] / [T-108] / [T-111] の前提**。変わらず
11. [T-097] 裁定待ち: placeholder 検出の対象族拡張。変わらず
12. [T-100] 裁定待ち: 検出語彙の拡張と予測値先書きの構造的検出。変わらず
13. [T-099] 裁定待ち: 凍結成果物に placeholder が入った場合の専用 waiver 契約。変わらず
14. [T-096] 裁定待ち: driver 予算定数の hard cap 化。変わらず
15. [T-101] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
16. [T-108] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
17. [T-111] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。変わらず
18. [T-112] **裁定済み → 床値実測の後**: `s1_known_axes_freeze` の root 束縛が不完全
19. [T-114] **裁定済み → 一巡後**: never-issued の全層 scope 漏れを統合テストで塞ぐ
20. [T-105] **裁定済み → [T-011] の後**: `_run_artifact_bytes` の `FileNotFoundError` 素通し。変わらず
21. [T-102] scope 外 real 所見: production の git runner が ambient `GIT_*` を継承する。変わらず
22. [T-011] 科学レーン floor 実測。残 gate = [T-088] → 段階 3・4 → 実行 revision 束縛 → lineage。変わらず
23. [T-089] 測定後の hardening と裁定: 二重 reason-tag 描画。変わらず
24. [T-090] 測定後の hardening と裁定: `VerifiedFreeze.document` が mutable dict。変わらず
25. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
26. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
27. [T-010] 延期: B-008 再試験は新規 background session が発火条件。変わらず
28. [T-082] 延期: prefix 容認 reader の用途別移行。**本番コードのため測定後**。変わらず

## 2026-07-26 (10) — /rulings: ユーザーが 4 件を裁定 + [T-096] の説明誤りをユーザーが指摘し一次資料で訂正 (docs-only・コード 0 byte、branch worktree-dev-wave-t091-093-hardening、計測なし)

`/rulings` の続き。2026-07-26 (9) の詳説 5 件のうち 4 件をユーザーが「推奨どおり」で裁定し、
**[T-096] は AI の説明が誤っているとユーザーが指摘して保留**した。本エントリに実装は含まない。

- **ユーザー裁定 (2026-07-26)**: 4 件すべて AI 推奨案。
  - **[T-104] = (a) まず reference の再編を 1 回試す。** 予算上限 24000 は据え置き。本日 412 bytes を
    重複除去で回収した実績があるため、体系的な再編で 8 件分 (約 800 bytes) の捻出を試みる。
  - **[T-097] = (a) 変異台帳 JSON だけを対象族に足す。** ここは実際に受入結果を書く場所で同型欠陥が
    現に成立しうる。残り 4 族 (phase3 / decisions / failures / handoff) は claim を書く場所とは
    限らず、無差別拡張は誤検出を増やすため足さない。
  - **[T-100] = (a) 表記ゆれ・HTML entity だけ語彙に足す。** 「結果の先書き」の構造的検出は新設しない
    (結果欄の識別が曖昧で誤検出が多く、`DW-G03` の独立 2 例も無い)。
  - **[T-099] = (c) 「起きたら止めてユーザー裁定へ返す」を仕様として明記するだけ。** 専用 waiver 機構は
    作らない。起きていない事象のために例外機構を先に作ると、それ自体が抜け道になる
    (D88 (2) が「装飾による除外は opt-out」として否定した論理と同型)。
- **[T-096] はユーザーの指摘により保留 → 訂正後に再提示する。** ユーザーが「測定は一回 120 秒という
  説明が分からない。3〜5 秒実行ではないか」と問い、**親が一次資料で実測して指摘が正しいと確認した**。
- **erratum — [T-096] の数値の意味を訂正する。** 2026-07-25 (6) の起票文
  「測定は rep ごと 120 秒 × 5 rep」は **timeout の話**であって実行時間ではない。実測した内訳:
  - `APPROVED_EXTIME_S = 5` / `APPROVED_REPS = 5` (`s8b_experiment_numbers.py:14-15`) →
    **通常の実測は 5 秒 × 5 rep = 25 秒**/attempt。ユーザーの理解が正しい。
  - 120 秒は `_FLOOR_VERIFY_CAP_PER_ATTEMPT_S` (`s8b_floor_campaign.py:169`) で、同行のコメントが
    「bench extime×reps とは**分離する**」と明記している。binary receipt + strict pre/post probe の枠。
  - 「145 秒/attempt」の内訳が判明した = **25 秒 (実測) + 120 秒 (検証枠)**。
  - 別に `measure_point` が `timeout_s: float = 120.0` を持ち (`calibrator/runner.py:401`)、
    floor campaign は**これを渡していない**ため既定が効く。**rep ごと 120 秒**なので最悪 600 秒/attempt。
  - build 側は `timeout_s=_FLOOR_BUILD_CAP_PER_CELL_S` (900) を渡すが (`s8b_floor_campaign.py:980`)、
    `buildcache` が configure と build に**各々**適用する (`buildcache.py:500-501`) ため最悪 1800 秒/セル。
- **訂正後の [T-096] の実体**: 予約式が積む 1 セル = `900 + (8+2) × 145` = **2350 秒**に対し、
  強制される timeout の最悪 = `1800 + 10 × 720` = **9000 秒** (約 3.8 倍)。
  n_sessions=8 / retry_slots_per_cell=2 は `output/s8b-freeze/floor_protocol.json` の実値。
  **schedule は投入時に導出されるため、セル数と 1 セルあたり attempt 数は投入まで確定しない** (未実測)。
- **推奨を (b) から (a) へ改める。** 訂正前は「walltime を厚めに取る」を推奨したが、差が 3.8 倍では
  厚めに取る量が現実的でない。かつ walltime 超過で job が kill されると **試行欠落**が生じるため、
  `DW-G02` の blocker 基準 (試行欠落を実際に変える欠陥) に該当し、測定前に直すのが規則に沿う。
- **検査**: `check_docs` rc=0。テスト差分が無いため受入全走は対象外。

### 次の一手
1. [T-109] **着手可能 (裁定完了)**: `/dev-wave クロスプロトコル対応` を新セッションで実行する。変わらず
2. [T-088] **人間手番 (承認済み・未実行)**: floor 投入。**[T-096] の裁定が先に要る可能性がある**
   (walltime の取り方が変わるため)
3. [T-096] **裁定待ち (訂正後に再提示)**: 予約式と強制 timeout の 3.8 倍差。
   **AI 推奨 = (a) 測定前に driver 側の timeout を予約式と整合させる** (blocker 該当)。
   正本 = 本エントリの erratum
4. [T-113] **裁定済み → 着手可能 (前倒し承認)**: root-isolation 変異を KILL する control を新設する
5. [T-110] **裁定済み → 着手可能**: 受理集合を変える改修の手続義務を規約化する
6. [T-104] **裁定済み → 着手可能**: dev-wave reference の再編で 8 件分の予算を捻出する。
   **[T-101] / [T-108] / [T-111] の前提**
7. [T-097] **裁定済み → 着手可能**: placeholder 検出の対象族へ変異台帳 JSON を足す
8. [T-100] **裁定済み → 着手可能**: 検出語彙へ表記ゆれ・HTML entity を足す
9. [T-099] **裁定済み → 着手可能**: 凍結成果物に placeholder が入った場合は止める仕様を明記する
10. [T-009] **着手可能 ([T-115] により解除)**: dev-wave 実装子の規律の所在を AGENTS.md へ明文化する
11. [T-060] **着手可能 ([T-115] により解除)**: WAL 用語運用の明文化
12. [T-012] **着手可能 ([T-115] により解除)**: task-run pilot の凍結解除可否を再評価する
13. [T-057] **裁定待ち (見送り台帳の発火)**: 全走時間が閾値を超えている。
    **AI 推奨 = (a) まず原因を実測する小さい調査を 1 回**。変わらず
14. [T-103] **裁定待ち**: (a) 1 cycle 後へ送る (**AI 推奨**)、(b) 最小 node を今実装、(c) 取り下げ。変わらず
15. [T-101] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。**[T-104] の実施後に再評価**
16. [T-108] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。同上
17. [T-111] 裁定待ち (dev-wave 自己改善): 予算に収まらなかった作法 2 件。同上
18. [T-112] **裁定済み → 床値実測の後**: `s1_known_axes_freeze` の root 束縛が不完全。変わらず
19. [T-114] **裁定済み → 一巡後**: never-issued の全層 scope 漏れを統合テストで塞ぐ。変わらず
20. [T-105] **裁定済み → [T-011] の後**: `_run_artifact_bytes` の `FileNotFoundError` 素通し。変わらず
21. [T-102] scope 外 real 所見: production の git runner が ambient `GIT_*` を継承する。変わらず
22. [T-011] 科学レーン floor 実測。残 gate = [T-088] → 段階 3・4 → 実行 revision 束縛 → lineage。変わらず
23. [T-089] 測定後の hardening と裁定: 二重 reason-tag 描画。変わらず
24. [T-090] 測定後の hardening と裁定: `VerifiedFreeze.document` が mutable dict。変わらず
25. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
26. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
27. [T-010] 延期: B-008 再試験は新規 background session が発火条件。変わらず
28. [T-082] 延期: prefix 容認 reader の用途別移行。**本番コードのため測定後**。変わらず

## 2026-07-26 (11) — /rulings: [T-096] を条件つきで裁定 — 測定前に driver を直すが計算時間予算を無駄にしない (docs-only・コード 0 byte、branch worktree-dev-wave-t091-093-hardening、計測なし)

`/rulings` の続き。訂正後に再提示した [T-096] をユーザーが条件つきで裁定した。実装は含まない。

- **ユーザー裁定 (2026-07-26)**: **[T-096] = (a) 測定前に driver 側の timeout を予約式と整合させる。
  ただし「計算時間予算の無駄遣いを避けられるなら」を条件とする。**
- **条件を実装制約として展開する (親の解釈)**。実装 wave はこの 3 点を満たすこと:
  1. **締めすぎない。** 打ち切り時間を実所要より短くすると健全な run を殺し、再投入で予算を二重に
     使う。値は記録済みの実所要時間から根拠づけて決め、根拠を材料レポートへ書く。
     根拠なしの直感値を入れてはならない。
  2. **厚取りしない。** walltime は修正後の予約式で取る。3.8 倍差を厚取りで吸収する案 (旧 (c)) は
     採らない。
  3. **修正の検証で計算機を使わない。** 本番 driver の変更は既存の合成 fixture で検証し、
     Pegasus へのジョブ投入を伴わない。
- **未確定として残る点**: セル数と 1 セルあたり attempt 数は投入時に導出されるため、
  総 walltime は投入まで確定しない。1 セル分の予約 2350 秒 / 強制上限 9000 秒は
  `output/s8b-freeze/floor_protocol.json` の `n_sessions=8` / `retry_slots_per_cell=2` からの計算値。
- **[T-088] との順序が確定した** — [T-096] の修正が [T-088] の投入より先になる。
  walltime の取り方が修正結果に依存するため。
- **次の 5 件の提示にあたり、全件を一次資料で検証した** ([T-096] の説明誤りの再発防止)。
  - [T-102] **確認 = real**。`s1_known_axes_freeze.py:89` と `s8b_holdout_freeze.py:147` の
    `_run_git` はいずれも `subprocess.run` に **`env=` を渡していない**ため ambient env を継承する。
    同 repo のテストは `_sanitized_git_env()` を使うが production は使っていない。
  - [T-089] **確認 = real**。`RatifiedFreezeError.__init__` が
    `super().__init__(f"[{reason}] {detail}")` で既に tag を付ける
    (`s8b_ratified_freeze.py:275`) 一方、driver が `error = f"[{exc.reason}] {exc}"`
    (`s8b_oracle_driver.py:389`) で再度付けるため **`[reason] [reason] detail`** になる。
    診断文字列のみで受理値は不変。
  - [T-090] **確認 = real**。`VerifiedFreeze` は `@dataclass(frozen=True)` だが
    `document: dict` は **mutable** (`s8b_freeze_io.py:30-38`)。frozen は再束縛だけを禁じ、
    dict の in-place 変更は通る。
- **検査**: `check_docs` rc=0。テスト差分が無いため受入全走は対象外。

### 次の一手
1. [T-096] **裁定済み → 着手可能 (条件つき、[T-088] より先)**: driver 側 timeout を予約式と整合させる。
   条件 = 締めすぎない / 厚取りしない / 検証で計算機を使わない (上記)
2. [T-088] **人間手番 (承認済み・未実行)**: floor 投入。**[T-096] の修正後**に行う
3. [T-109] **着手可能 (裁定完了)**: `/dev-wave クロスプロトコル対応`。変わらず
4. [T-057] **裁定待ち**: 全走時間が閾値を超えている。**AI 推奨 = (a) 原因調査を 1 回**。変わらず
5. [T-103] **裁定待ち**: (a) 1 cycle 後へ送る (**AI 推奨**)、(b) 最小 node、(c) 取り下げ。変わらず
6. [T-102] **裁定待ち (real 確認済み)**: production の `_run_git` 2 箇所が ambient env を継承する。
   **AI 推奨 = [T-096] と同じ wave で直す** (同じ driver 系統・本番コード・測定前)
7. [T-101] 裁定待ち (dev-wave 自己改善): 作法 2 件の採否。**[T-104] の再編で場所ができ次第**
8. [T-108] 裁定待ち (dev-wave 自己改善): 作法 2 件の採否。同上
9. [T-111] 裁定待ち (dev-wave 自己改善): 作法 2 件の採否。同上
10. [T-089] **測定後の hardening と裁定 (real 確認済み)**: 二重 reason-tag。変わらず
11. [T-090] **測定後の hardening と裁定 (real 確認済み)**: `VerifiedFreeze.document` が mutable。変わらず
12. [T-113] **裁定済み → 着手可能 (前倒し承認)**: root-isolation 変異の control を新設する
13. [T-110] **裁定済み → 着手可能**: 受理集合を変える改修の手続義務を規約化する
14. [T-104] **裁定済み → 着手可能**: dev-wave reference の再編で予算を捻出する
15. [T-097] **裁定済み → 着手可能**: 変異台帳 JSON を placeholder 検出の対象族へ足す
16. [T-100] **裁定済み → 着手可能**: 検出語彙へ表記ゆれ・HTML entity を足す
17. [T-099] **裁定済み → 着手可能**: 凍結成果物の placeholder は止める仕様を明記する
18. [T-009] **着手可能**: dev-wave 実装子の規律の所在を AGENTS.md へ明文化する
19. [T-060] **着手可能**: WAL 用語運用の明文化
20. [T-012] **着手可能**: task-run pilot の凍結解除可否を再評価する
21. [T-112] **裁定済み → 床値実測の後**: `s1_known_axes_freeze` の root 束縛が不完全。変わらず
22. [T-114] **裁定済み → 一巡後**: never-issued の全層 scope 漏れ。変わらず
23. [T-105] **裁定済み → [T-011] の後**: `_run_artifact_bytes` の `FileNotFoundError` 素通し。変わらず
24. [T-011] 科学レーン floor 実測。残 gate = [T-096] → [T-088] → 段階 3・4 → 実行 revision 束縛
25. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
26. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
27. [T-010] 延期: B-008 再試験は新規 background session が発火条件。変わらず
28. [T-082] 延期: prefix 容認 reader の用途別移行。**本番コードのため測定後**。変わらず

## 2026-07-26 (12) — /rulings: 残り 5 件を推奨どおり裁定 + テスト改善を最優先とユーザーが指示 — 裁定待ちが実質ゼロに (docs-only・コード 0 byte、branch worktree-dev-wave-t091-093-hardening、計測なし)

`/rulings` の完結。2026-07-26 (11) の詳説 5 件をユーザーが「推奨どおり」で一括裁定し、
あわせて**着手順の指示**を出した。実装は含まない (コード 0 byte)。

- **ユーザー裁定 (2026-07-26)**: 5 件すべて AI 推奨案。
  - **[T-057] = (a) 原因を測る調査を 1 回入れる。**
  - **[T-103] = (a) 1 cycle 後へ送る。** never-issued 検査は成果物を何も変えないため。
  - **[T-102] = (a) [T-096] と同じ wave で直す。** 同じ driver 系統の本番コードで、
    測定前に本番へ触る回数を 1 回に抑えるため。
  - **[T-101] / [T-108] / [T-111] = (a) 作法 6 件すべて採用。** [T-104] の reference 再編で
    場所を作り、そこへ入れる。すべて実際に起きた事象への対処で、想像上の懸念は含まない。
  - **[T-089] / [T-090] = (a) 測定後のまま据え置く。** [T-089] は診断表示のみ、[T-090] は現に
    書き換えている箇所が無い。測定前に本番へ触る回数は [T-096] + [T-102] の 1 回に留める。
- **ユーザー指示: テストの改善を最優先とする。** これにより着手順が
  **[T-057] → [T-096] + [T-102] → [T-088] 投入 → 以降**に変わった。
  副次的な利点として、全走 30 分が短縮されれば [T-096] wave 自身の受入全走も安くなる。
- **[T-057] の射程を親が読み替えた (要確認)**。裁定した (a) は「原因調査のみ」だが、
  ユーザーの「改善を最優先でやりたい」を踏まえ、**原因が特定でき、かつ修正がテストのみ
  (本番 0 byte) で済むなら同 wave で改善まで進める**と解釈する。本番コードに触る改善が必要と
  判明した場合は実装せず裁定へ戻す。異なる意図なら再裁定を要する。
- **裁定待ちが実質ゼロになった。** 残るのは測定後に自動的に回ってくる項
  ([T-089] / [T-090] / [T-112] / [T-105] / [T-082] / [T-085] / [T-087]) と、
  発火条件待ちの [T-010] だけである。本セッションの `/rulings` で計 16 件が裁定された。
- **検査**: `check_docs` rc=0。テスト差分が無いため受入全走は対象外。

### 次の一手
1. [T-057] **最優先・着手可能 (ユーザー指示)**: 全走 1811 秒の原因を実測する。
   重い fixture (`_t080_stub_free_e2e_repo`、1 回約 27MB の copytree + submodule add) が
   11 回呼ばれている点が既知の手がかり。239 秒 → 1811 秒の差が runner/env・並列度の違いに
   よるかも未確認。テストのみで済む改善なら同 wave で実施する
2. [T-096] **裁定済み → 着手可能 (条件つき)**: driver 側 timeout を予約式と整合させる。
   条件 = 締めすぎない / 厚取りしない / 検証で計算機を使わない
3. [T-102] **裁定済み → [T-096] と同じ wave**: production `_run_git` 2 箇所の ambient env 継承を
   sanitized env へ揃える
4. [T-088] **人間手番 (承認済み・未実行)**: floor 投入。**[T-096] の修正後**に行う
5. [T-109] **着手可能 (裁定完了)**: `/dev-wave クロスプロトコル対応`。変わらず
6. [T-113] **裁定済み → 着手可能 (前倒し承認)**: root-isolation 変異の control を新設する
7. [T-110] **裁定済み → 着手可能**: 受理集合を変える改修の手続義務を規約化する
8. [T-104] **裁定済み → 着手可能**: dev-wave reference の再編で作法 6 件分の場所を作る
9. [T-101] **裁定済み → [T-104] の後**: 作法 2 件を採用する
10. [T-108] **裁定済み → [T-104] の後**: 作法 2 件を採用する
11. [T-111] **裁定済み → [T-104] の後**: 作法 2 件を採用する
12. [T-097] **裁定済み → 着手可能**: 変異台帳 JSON を placeholder 検出の対象族へ足す
13. [T-100] **裁定済み → 着手可能**: 検出語彙へ表記ゆれ・HTML entity を足す
14. [T-099] **裁定済み → 着手可能**: 凍結成果物の placeholder は止める仕様を明記する
15. [T-009] **着手可能**: dev-wave 実装子の規律の所在を AGENTS.md へ明文化する
16. [T-060] **着手可能**: WAL 用語運用の明文化
17. [T-012] **着手可能**: task-run pilot の凍結解除可否を再評価する
18. [T-103] **裁定済み → 1 cycle 後**: never-issued 検査は先送り
19. [T-089] **裁定済み → 測定後**: 二重 reason-tag 描画。変わらず
20. [T-090] **裁定済み → 測定後**: `VerifiedFreeze.document` が mutable。変わらず
21. [T-112] **裁定済み → 床値実測の後**: `s1_known_axes_freeze` の root 束縛が不完全。変わらず
22. [T-114] **裁定済み → 一巡後**: never-issued の全層 scope 漏れ。変わらず
23. [T-105] **裁定済み → [T-011] の後**: `_run_artifact_bytes` の `FileNotFoundError` 素通し。変わらず
24. [T-011] 科学レーン floor 実測。残 gate = [T-096] → [T-088] → 段階 3・4 → 実行 revision 束縛
25. [T-085] PKG-1 採用裁定済 → floor 実測後の hardening wave で実装。変わらず
26. [T-087] W-e 着手時に整合を決める裁定済 (延期)。変わらず
27. [T-010] 延期: B-008 再試験は新規 background session が発火条件。変わらず
28. [T-082] 延期: prefix 容認 reader の用途別移行。**本番コードのため測定後**。変わらず
