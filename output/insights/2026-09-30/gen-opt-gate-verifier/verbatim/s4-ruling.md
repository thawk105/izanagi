# 段 4 裁定 — [T-2884] 正しさ関門の記録 (U1) と判定器 (U2)

- 作成: 2026-09-30 12:34 JST (親、file の mtime。初稿の「13:20」は推定の誤記で訂正)。入力: `s1-brief.md`、`plan.md` (受理 rc=0)、`consult-a.md`・`consult-b.md` (受理 rc=0)。
- 裁定 inbox (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/`) を再走査: 本件に関わる新着なし (最新 2026-09-30 03:00 は D2305 の控え)。local main は 4f412c67b のまま (HEAD..main 0)。

## 1. 所見の裁定

| ID | 裁定 | 採否・処置 |
|---|---|---|
| plan I1 (Q の txid 欠落を `-`) | real | 採用。R4 と合わせて §2.1 |
| plan I2 (要求 keyword を公開 API で必須) | refuted (今回) | 不採用。`verify_trace_dir` の test 呼び出し約 118 箇所を書き換える割に、gen-opt の呼び出し元 (U5) が未実在で必須化の効果を今は確かめられない。`require_gate_witness: bool = False` (keyword-only)。U5 が True を渡す義務は scope 外の裁定パッケージ候補として一次資料に記す |
| plan I3 (legacy 投影を変えない) | real | 採用。gate が無く要求もない結果の `result_to_dict` / `result_to_dict_v3` は byte 単位で従前と同一 |
| plan I4 (lock の schema と E1-stale を分ける) | real | 採用 (記述の正確化)。歴史 lock は書き換えない |
| A-R1 (D5 を `clean()` へ接続) | real must-fix | 採用。要求時に D5 不成立・unavailable は `clean()` が偽 |
| A-R2 (不正な gate file 名) | real must-fix | 採用。`gate_` で始まる file のうち `gate_<非負十進、先頭 0 なし>.log` でないものが 1 つでもあれば到達不能 (要求の有無に依らず gate 有効として扱う) |
| A-R3 (legacy parse 経路) | real must-fix | 採用。gate が有効 (在るか要求) で parse が `_LegacyTrace` に落ちたら到達不能 = indeterminate (照合を省略しない)。legacy 経路での照合実装はしない (限界に記す) |
| A-R4 (pending txid の状態) | real (一部) | 採用: CCBench 側は「Q 出力で消費、試行開始 (RETRY 直後) で破棄、未受領なら `-`」だけ。二重の受け渡し・渡し残りの検出は判定器の Q↔C…E 枠 1 対 1 (D1(c)) が担う (枠だけ・Q だけ・txid 不一致のいずれも違反)。CCBench に別の異常行は足さない |
| A-R5 (thid の 16 bit 上限) | real must-fix | 採用。CCBench 側は TRACE 内で `thid+1 <= 0xFFFF` と `1 <= seq < 2^48` を検査し、破れたら書き手刻印を出さずに停止 (TRACE build のみ)。判定器は書き手刻印の上位 16 bit が `1..(thread 数)`、下位 48 bit が非 0 であることを検査 |
| A-R6 (B2 fixture の単一理由) | real | 採用。D1(a) 用は後続読みの無い履歴、D2a 用は D1 が整合する履歴に分ける。B4・B5 fixture は既存の版・frame 検査が緑であることを test 内で固定 |
| A-R7 (素の F の certified を並べない) | real | 採用。B01 で F 条件自体を刻印なし条件へ置き換える |
| A-R8 (D297 の主張範囲) | real | 採用。report の consumer と macro context を一次資料へ列挙し「選定文脈での同一性」と書く。記号検査は検査した binary を列挙 |
| B01 (刻印単独の比較) | real must-fix | 採用。生死確認の第 4 条件を「素の F」から「U1 tip + 刻印だけを外す patch (`id_` の代入 2 か所を除く、Q/V は残す)」に替える。commit・abort の差は 1 回ずつの記述値で、判断に使わない |
| B02 (capability・snapshot 拡張の後送) | real | 採用。D5 は `verify_trace_dir` の `ccbench_root` から直接読む経路 (CLI) だけに実装。`verify_trace_dir_with_capability` と `pipeline.py`・`source_digest.py`・fanout は変えない (gate は presence 起動だけ効く)。capability 経路で要求を通す仕事は U5 へ |
| B03 (詳細投影の重複) | real | 採用。`Integrity` の計数 + 位置付き notes (上限付き sample: check・thid・txid・key・expected・observed) だけ。別の機械可読の詳細 list は作らない |
| B04 (発生条件の恒久 API) | real | 採用 (縮小)。発生条件は 4 つに限る: 自分の書きの後の読みを含む取引数、書きのある取引数、同じ key を 2 回以上書いた取引数、D2a で照合した外部読みの数。0 の走行を採らない判断は呼び出し側 (事前登録) が持つ |
| B05 (U1 の最小化) | real (一部) | 採用: 有効化 + pending の最小形 (§2.1)。全 protocol の `id_` 読み手の rg 確認は残す (安価で、刻印の安全性の前提) |
| B06 (U0 照合器の位置付け) | real | 採用。U0 照合器は U1 条件 3 つで D1・D2b の件数を並べる診断だけ (同じ parser を共有するので独立の証拠と呼ばない)。主証拠は fixture・変異・production CLI |
| B07 (判定器の変異を実際に走らせる) | real must-fix | 採用。§4 の事前登録 |
| B08 (fail-closed の CLI 終了値) | real | 採用。要求時の gate 全欠落・一部欠落・読取不能で `certified=false` かつ CLI rc≠0 を test で固定 |
| B09 (再検証対象を結果前に固定) | real | 採用。§3 を `prereg.md` として計算の投入前に wave branch へ commit |
| B10 (`A` 名の訂正と [T-2889] の更新) | real | 採用。設計資料 `gen-opt-correctness-gate/README.md` の末尾へ追記だけの訂正節 (本文は書き換えない)、[T-2889] の前提と計算見積りを worklog fragment へ |
| B11 (再見積り) | real | 採用。§5 |

## 2. plan v2

### 2.1 記録の形 (両実装子に先に固定する)

- file: trace dir 直下の `gate_<thid>.log` (thid は十進・先頭 0 なし、trace の `trace_<thid>.log` と同じ集合)。Silo の YCSB 経路の commit を持つ thread だけが開く (lazy open)。
- `Q <txid|-> <thid> <n> <step>{n}` (空白区切り)。step = `<op>:<key>:<observed>:<written>`、op ∈ {`R`,`W`,`M`}、key = 16 桁小文字 hex (`key_to_hex`)、R は `<観測刻印>:-`、W は `-:<書いた刻印>`、M は両方。刻印は十進 uint64。1 run 内で commit に成功した試行の手順だけ (retry で clear)。commit 成功の直後に 1 行。txid は Silo writePhase の YCSB/v2 枝が C 行に使った txid を pending で渡したもの。未受領なら `-`。
- `V <txid> <key> <stamp>`: Silo writePhase の YCSB/v2 枝で、UPDATE 要素の `memcpy` 直前に、据える `body_` の先頭 8 byte (`YCSB::id_`) を出す。write set の順。既存の `#line 658` より前 (既存 TRACE 区間の内側) に置く。
- 刻印: `YCSB::id_` (値の先頭 8 byte、`val_` は不変)。書き手 = `((thid+1)<<48) | seq` (seq は thread 内の通し番号 1 から、W・M ごとに増やす)。初期 load は既存の `id_ = key id` → genesis の期待刻印 = key hex の整数値。
- 有効化: thread_local の状態を Silo の writePhase (YCSB/v2 枝、C 行を出す箇所) が「有効 + pending txid」にする。`run` は有効な thread でだけ Q を出す。pending は Q 出力で消費、RETRY 直後で破棄。
- `A`・`S` は使わない。

### 2.2 U1 (CCBench、Codex author 1)

- F `25898d00` の子 commit 1 つ (親が作る)。編集は `include/trace.hh`・`include/ycsb.hh`・`cc/silo/transaction.cc` の `#if TRACE` の内側 + TRACE=0 の行番号を戻す `#line` だけ。plan の表 (U1) の位置に従う。規模の上限: 3 file 合計の追加 150 行。
- TRACE=0 の前処理出力が F と同一 (`__LINE__` を含む): ycsb.hh の追加区間の直後に `#line <元の次行>`、transaction.cc の V は `#line 658` の前。子は `IZ_ERR_AT(__LINE__)` 型の probe か `g++ -E` の TRACE=0 比較で自己確認、最終は親の D297 (GCC 11・12、header 4 引数、`--expect-paths` 3 file、期待 rc=0)。
- clang-format 14 で 213 file rc=0、Release 全体 build rc=0、TRACE=0 の各 `ycsb_*.exe` に `_assert_no_trace_symbols`。
- `id_` を load 後に読む経路が全 protocol の YCSB 経路に無いことを rg で確かめ file:line で報告。
- 同じ実装子が repo 外の使い捨て物も作る: B1 の U1 tip 用 patch (初回 R/M key の登録省略、発火計数 = commit した取引数)、刻印だけ外す patch、commit message、生死確認の起動器 v3 (4 条件 1 job ずつ、判定器は wave の production CLI `--require-gate-witness`、U0 照合器を診断で並べる)、D297 と CI build の job script (前 wave v2 を F→U1 tip に合わせる)。

### 2.3 U2 (判定器、Codex author 2)

- 所有: `orchestrator/verifier/{parse,model,core,report,cli}.py`、新 test file `orchestrator/tests/test_verifier_gate_witness.py` と fixture dir (名は子が決める)、新 test の登録に要る inventory・ledger (子が meta-test を洗い出して名指し)。`__init__.py`・`dsg.py`・`commit_receipt.py`・`pipeline.py`・`source_digest.py`・`campaign_lock.py` は変えない。新 module は作らない (D442 の閉包の path 集合を変えない)。規模の上限: production 追加 600 行、test 追加 900 行。
- gate 有効 = gate namespace の file が 1 つでも在るか、`require_gate_witness=True`。有効なら: (1) 到達可能性 (file 名、thread 集合 = trace の thread 集合、書式、刻印の形、V↔UPDATE の W 行 1 対 1、compact 経路であること)、(2) D1 (a)(b1)(b2)(c)、(3) D2a、(4) D2b (i)(ii) を全 key、(5) 要求時は D5 (ccbench_root の `include/ycsb.hh` の Q emitter と `cc/silo/transaction.cc` の V emitter・txid 受け渡しが literal `#if TRACE` 内に在る。ycsb_silo が ycsb.hh を include することも見る)。照合の定義は plan の擬似コード。到達不能なら D1/D2 を合格に数えない。
- 結果: `Integrity` に計数 (到達不能、D1a・D1b1・D1b2・D1c、D2a、D2b_i・D2b_ii、D5 状態) と §1 B04 の発生条件 4 つ、`clean()` は違反・到達不能・(要求時の) D5 不成立で偽。notes に上限付きの位置付き sample。`result_to_dict` は gate 有効時だけ `gate_witness` 節 (意味の版・要求の有無・計数・発生条件) を足す。巡回があれば non-serializable 優先は不変。
- 意味の版: `orchestrator/verifier/model.py` に `MEANING_VERSION = 2` (本 wave 前の判定器 = 1)。gate 節に載せる。legacy 投影は変えない。
- CLI: `--require-gate-witness`。要求時の gate 全欠落・一部欠落・読取不能で `certified=false` かつ rc≠0。
- 既存 test は期待値を変えない。赤が出たら実装を直すか報告して止まる。閉包系 test (`test_campaign_lock_codec.py` 等) が判定器 bytes で赤になるなら内容を報告して止まる (親が裁定)。

## 3. 再検証の発火条件 (結果を見る前に決める、`prereg.md` として commit)

1. 本 wave の land 前に判定器 (意味の版 1) が出した判定は、記録どおり残す。再判定も certified への昇格もしない。
2. 意味の版 2 で読み直す対象は、gate file を持つ trace に限る。repo 内の campaign (pin C) の trace は gate file を持たないので対象外 (版 2 でも要求しない呼び出しは同じ判定を返すことを test で固定する)。repo 外の U0 (md_5) と Silo 修正 wave (md_12 系) の trace archive は gate file を持つが certified の主張に使われていないので、今は読み直さない。後の wave がそれらを主張に使うときは版 2 以上で読み直す。
3. 本 wave の生死確認 4 条件 × 2 workload は版 2 (要求あり) で判定する。
4. 意味の版が上がるたびに、それより前の版の記録は昇格させず、新しい版を要する主張は原 trace + gate archive から読み直す (archive は保持する)。
5. gen-opt の候補の certified は、版 2 以上・要求あり・D5 成立・D1/D2a/D2b 全 key 違反 0・既存の D3/D4/X/P と巡回なし、をすべて満たすときだけ。

## 4. 事前登録

### 4.1 生死確認 (計算ノード、各条件 1 job、W-rmw・W-blind 各 1 回、U0 と同じ flags)

| 条件 | 期待 (両 workload とも) |
|---|---|
| S = U1 tip | 到達不能 0、D1 全項 0、D2a 0、D2b (i)+(ii) ≥ 1、巡回 0、verdict indeterminate |
| X = U1 tip + 修正 patch (sha256 2fca9651…、厳密適用) | 到達不能 0、D1・D2a・D2b 全項 0、発生条件 (自分の書きの後の読み・書きのある取引) 各 ≥ 1、D5 成立、commit 件数一致、certified |
| B = U1 tip + B1-U1 | B1 committed ≥ 1、D1(b1) 違反取引数 = B1 committed、verdict indeterminate |
| N = U1 tip + 刻印を外す patch | 記述だけ (commit・abort を S と並べる)。判定に使わない |

発生条件 0・archive 欠落・build 失敗は期待一致に数えず、原因を記す。U0 照合器の件数は診断で、食い違えば調べて記す (緩めない)。

### 4.2 判定器の変異 (DW-M01、`tools/mutation_harness.py`、各 1 条件だけ外す)

| # | 外す条件 | 殺す test (子が実名で確定) |
|---|---|---|
| M1 | D1(a) の比較 | B2 型 (後続読みなし) |
| M2 | D1(b1) の比較 | B1 型 |
| M3 | D1(b2) の比較 | Q に無い key の R 行 |
| M4 | D1(c) (Q↔枠の 1 対 1) | 枠だけ・Q だけ・txid `-` の各 fixture |
| M5 | D2a の非 genesis 比較 | B4 型 (D1 整合) |
| M6 | D2a の genesis 比較 | genesis を読んで刻印が key 整数と違う fixture |
| M7 | D2b(i) の比較 | B6 型 |
| M8 | D2b(ii) を「最初の書き」と照合 | 2 度書きで V = 最初の書き |
| M9 | V↔UPDATE W の 1 対 1 | V 欠落 |
| M10 | thread 集合の一致 | gate file の一部欠落 |
| M11 | 要求時の gate 全欠落を合格扱い | 要求 + gate 0 file |
| M12 | 要求時の D5 を `clean()` から外す | B7 型 (Q/V 整合、emitter 無し source) |
| M13 | 不正な gate file 名を無視 | `gate_x.log` の在る trace |
| M14 | gate 有効時の legacy 経路を素通し | legacy に落ちる trace + gate |
| M15 | presence 起動を外す (要求なしで gate を読まない) | 要求なし + gate 在り + B1 型 |

KILLED は期待 node の完全一致だけ (DW-M08)。各変異は実装後に単一理由性を確かめ、成り立たなければ fixture を差し替える。

## 5. 計算の見積り (投入前、2 node 時間未満)

生死確認 4 job ≈ 4 × 3〜5 分 ≈ 0.2〜0.35、D297 GCC 11・12 ≈ 0.55〜0.7、CI build + 記号検査 ≈ 0.1〜0.2 (前 wave 実測 build 22 秒)、変異 15 本の dispatch ≈ 0.2〜0.4。合計 ≈ 1.05〜1.65 node 時間。受入の全走は land 用で数えない。実測が 2 に近づけば投入前に止めて示す。

## 6. scope 外 (一次資料に裁定パッケージ候補として記す)

- U5: gen-opt driver と capability 経路で `require_gate_witness=True` を通し、D5 を build の source snapshot に束縛する。
- gitlink 前進: U1 と Silo 修正を評価対象 pin に入れ、そこで D297・生死確認を取り直す。U1 だけ先に pin へ入れると、修正前の Silo の trace は presence 起動の D2b で全部 indeterminate になる (規律 2 どおり、ただし順序を gitlink wave が決める)。
- D442: 判定器 4 file の bytes 変更で既存 E1 lock は E1-stale。md_11 の本走は submit checkout 固定で影響を受けないが、land 後の main から再開すると CERTIFIED_ACCEPTANCE で拒否されうる → land 時に md_11 へ通知。
