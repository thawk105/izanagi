# 段 4 裁定 — md_15 (dev-wave-vhash-readonly-share、2026-09-29 15:2x JST、base 035fc11fa)

入力: brief.md、codex/out/s2-plan.md (plan)、codex/out/s3-consult.md (相談、条件付き GO)。
裁定 inbox の再走査 (15:19): md_15.txt (mtime 14:07)・common.txt (03:17) は wave 開始後に更新なし、local main は 035fc11fa のまま (wave 開始後の裁定なし)、ユーザーからの新指示なし (進捗の問い合わせ 1 件のみ)。
md_14 作業ツリー (dev-wave-vhash-gc-connection-prototype) と付随 file 10 本は 15:20 時点で内容一致 (重なりなし)。

## 所見の裁定

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| C-M1 | D-F は総差であって「ro のせい」の識別ではない | real | 採用: D-F を「条件間の総差と交互作用」と命名。各セルに実現 ro 試行率・commit 率、update commit/s、install/s、abort 率を併記。加えて境界保持 tx の種別を直接観測する (plan v2 の O-5) |
| C-M2 | D-C・見積り (b) を境界の前進量と呼べない | real | 採用: D-C =「観測走における flag 機会の時刻分割」、(b) =「公開間隔に対する局所的な機会量」。上下限・前進量と書かない。同値再公開 (MinRts 不変の公開) を別計数 |
| C-M3 | 見積り (a) は一般の上限ではない | real | 採用: 「観測鎖・先頭 K 版・既読区間に限定した楽観的適格率」。(1−f)×率 は独立を仮定した感度曲線。固定 snapshot 必須の tx には適用しない |
| C-M4 | plan の編集対象に依頼の所有外が含まれる | real (所有の明示漏れ) | 採用: 付随 file の所有を下の「所有」で親が明示 (契約上必須の登録簿・test・新規作図器・README entry)。ledger.json 不変更の理由は一次資料に書く |
| C-S1 | ro snapshot 年齢 ≠ 境界年齢 | real | 採用: 別軸で測り、乖離しうると書く。brief の「≒」は撤回 |
| C-S2 | 新計器の観測者効果 | real | 採用: anchor 2 条件で md_2 の公開回数・間隔・境界年齢と並べ、差を計器増分の目安として報告 (同時刻の対照ではない点も明記) |
| C-S3 | 既定 flag で md_2 と同一生成は実装後の検証条件 | real | 採用: (i) 既定値で抽選処理に入らないことを test で、(ii) macro 無効の inert witness を smoke で、(iii) anchor を md_2 と並べる、の 3 証拠を分けて残す |
| C-S4 | skew 0 の対照が要る | real | 採用: skew 0 対照 12 条件を追加 (下の条件表) |
| C-S5 | 2 種類の ro を定義表で分ける | real | 採用: 一次資料に定義表 (固定 snapshot 必須 / serializable で位置を選べる / YCSB で区別不能な割合 f) |
| C-N1 | 任意配列を増やさない | real | 採用: ro の read_zero 配列は作らない |
| C-N2 | ro_deep の分母 | real | 採用: 選択版を得た ro read 数 `readonly_reads` を同じ場所で数え分母にする |
| P-反論 (plan §brief への反論) | 指定率≠実現率、D-C は一次近似、D-F は交絡、(a) は上限でない | real | 採用 (上と同じ) |

## plan v2 (plan の設計を基に、差分だけ)

- O-1 (種別制御): plan どおり。`izanagi_ronly_pct` (int32、既定 −1、VLIFE block 内、transaction.cc)、`izanagi_long_kind` (int32、既定 0、LONGTX block 内)。新規手続きの初回 `begin()` だけで抽選・書換え (member flag を commit 成功で立てる)。既定値では抽選関数に入らない。不正値は起動時に停止。
- O-2 (D-C): plan どおり (世代付き二重 slot、atomic、leaderWork 前後の既存判定、三項の整数 µs 和、初回公開・欠損・世代不一致・時刻逆転は別計数、tie は thread ID の小さい方)。第 1 項の種別は {通常 update, 長い update, abort, ro, 長い ro, leader 自身の区別は種別と別に件数}。
- O-3 (厳密和): 境界年齢・公開間隔・ro snapshot 年齢の sum/count (+ ro snapshot 年齢のヒストグラム)。同値再公開件数。
- O-4 (ro 候補): `readonly_candidate[5]` と `readonly_reads`。ro 成功 read も L/U に反映 (update 側の既存計数は不変)。
- O-5 (新規・小): 公開ごとの境界保持 tx の種別。各 thread が begin で (rts, 種別, 世代) を自 slot に書き、leader は公開直後に slot の rts が公開 MinRts と等しい thread の種別を 1/n ずつ数える (n = 一致した thread 数)。一致なしは unresolved として別計数。
- 条件表: skew 0.9・update op の rratio 50・10 ops・48 worker の主格子 60 (R{0,25,50,75,95} × {none, wait1msU, wait10msU, wait10msR} × gc{10,1000,100000}) + skew 0 対照 12 (skew 0・rratio 50、R{0,50,95} × {none, wait10msU} × gc{10,100000}) + anchor 2 (既存 ID B-none-gc10・B-wait10ms-gc10、flag 既定) = 74 条件 × 3 反復 = 222 走。4 job に割る (gen_S の同時上限 3〜4)。smoke 実測で 1 走の所要を取り直し、合計 2 node 時間以上なら投入せず止める。
- 作図: 4 枚 (plan §作図)。図 3 は D-F と D-C を別パネル・別単位で、足し合わせない。
- JSON: 計器行 schema_version 2 (driver は schema 1 も読む)。新 measure は新 patch SHA の smoke だけ受理。

## 所有 (C-M4 の裁定)

- 依頼の所有: `patches/instr-cicada-version-lifetime.patch`、`orchestrator/campaign/vhash_cicada_vlife.py`、一次資料 `output/insights/2026-09-29/vhash-readonly-share/`、spool fragment。
- 契約上必須の付随 (親が許可): `orchestrator/tests/test_vhash_cicada_vlife.py`、`tools/plotting/plot_vhash_readonly_share.py` (新規)、`orchestrator/campaign/condition_meaning_gate.py` の VLIFE/LONGTX 件数 pin、`orchestrator/tests/test_condition_meaning_gate.py` の同 pin、`orchestrator/tests/test_p3_s4_loop.py` の patch token 許可集合 (新しい裸 `IZANAGI_*` token を作る場合だけ)、`patches/README.md` の本 patch の entry (14 行・845〜869 行の節)。
- 変更しない: `patches/ledger.json` (D18 第 4 類専用・entry 数 1 固定)、md_2 の一次資料・raw・図・`tools/plotting/plot_vhash_cicada_vlife.py`、`materializer_admission.py`・`screening_driver.py`・`test_ccbench_spawn_sites.py`・`test_p3_build_authority_cli.py` (起動関数・登録名を増やさない。増やす必要が出たら止めて親へ)、所有外 (patches/cicada-forwarding-*、vhash_forwarding_prototype.py、tools/vhash_forwarding_model/、docs/paper-story-vhash/、gitlink)。

## 変異の事前登録 (DW-M01、位置と単一理由性は実装後に確認し、できなければ再照準)

| ID | 対象 | 変異 | 殺すべき test (予定) |
|---|---|---|---|
| MUT-1 | driver parse | schema 2 の必須新 field 1 つの欠落を受理する | schema 2 欠落拒否 test |
| MUT-2 | driver parse | D-C 三項の足し戻し検査を外す | 三項恒等式の不一致拒否 test |
| MUT-3 | driver summarize | D-F 交互作用の符号を 1 項反転 | D-F 式の既知値 test |
| MUT-4 | driver CONDITIONS | 主格子から wait10msR を落とす (条件数 60→45) | 条件直積・件数 test |
| MUT-5 | driver _flags | 旧 24 ID に `izanagi_ronly_pct=0` を渡す (−1 でなく) | 旧 ID の argv test (md_2 互換) |
| MUT-6 | driver summarize | ro 深部割合の分母を readonly_reads でなく全 read site 数にする | 分母定義 test |
| MUT-7 | patch | 抽選を新規手続き flag の guard 外へ出す (retry で再抽選) | patch の begin block 構造 test |
| MUT-8 | patch | ro commit 経路で GCFlag を書く (観測のみの不変条件破り) | ro commit block に GCFlag への store が無いことの test |
| MUT-9 | driver summarize | 境界保持種別の 1/n 重みを 1 にする | 保持種別の和 = 有効公開数 test |
| EQ-1 | driver | 等価変異 (検証の `x < 0` を `not x >= 0` に) | 赤なし (SURVIVED が正) |

MUT-7・MUT-8 は patch 文字列を見る test で殺す。C++ の実行時挙動は計算ノードの smoke と計測で確かめた範囲に限ると一次資料に書く。

## 分割

実装は Codex author 1 単位 (patch・driver・test・作図・登録簿 pin・README entry は bytes 契約で結合)。段 6 は review 1 本 + 焦点再レビュー。受入全走は段 7 後。

## 段 4 補遺 (15:3x、段 5 投入直前の midflight で判明した新事実)

- 事実: midflight gate で local main が 11 commit 先行 (035fc11fa..ce124f388)。所有・付随 file への変更は 0 件 (`git diff --stat` 空)。入ったのは md_11 の着地 (`output/insights/2026-09-29/vhash-cicada-baseline-tuning/README.md` §1)。
- 新事実 1: レコード数は 1M (D15 第二基準、md_2 と同じ)。条件表は変えない。
- 新事実 2: 調整済み Cicada の最良設定 (rr5・rr50・rr95 共通) は `BACK_OFF=0, INLINE_VERSION_OPT=1, INLINE_VERSION_PROMOTION=0, REUSE_VERSION=1, WRITE_LATEST_ONLY=0` で、既定比 2.2〜4.5 倍。GC 間隔は 10〜100 µs が最良付近。論文の主比較は調整済み Cicada。`INLINE_VERSION_OPT` は Cicada 自身の hot 配置であり、「ro の深い探索が調整済み Cicada でも残るか」は H1 の伸びしろの判断に直結する。
- 裁定 (scope 追加、研究前進に必要): 調整済み genome の計器 build を 1 本足し、小格子 T = skew 0.9・rratio 50・R{0,50,95} × {none, wait10msU} × gc{10,100000} = 12 条件を追加。合計 86 条件 × 3 反復 = 258 走。genome の CMake 変数は `orchestrator.campaign.model.cmake_cache_variable_for_axis('cicada', axis)` で引き (md_11 の `tools/vhash_cicada_tuning/driver.py` 250 行と同じ写像)、build ごとに compile_commands.json の cicada TU の -D を期待値と照合する。smoke は既定 genome に加え調整済み genome の計器 build と短い走も通す。INLINE_VERSION_OPT=1 では版の 1 つが tuple 内にあるので「位置」は鎖上の位置のままで、cache 上の近さは別物と一次資料に書く。
- 変異の追加登録: MUT-10 = T 条件の build 引数から `INLINE_VERSION_OPT=1` を落とす (既定 genome で走る) → T 条件の genome 束縛 test で殺す。
- 所要: smoke で 1 走の実時間を取り直し、合計 2 node 時間以上なら投入せず止める (見積りの上限目安 258 走 × 8 s + build 3 本 × 4 job)。
