## brief への異議

- **I1・(P1):** Q の txid を常に十進整数とする U0 書式のままでは、(P3) が求める「有効化後に txid を渡さない commit」を表せない。U0 照合器は Q の txid を整数として読む（`gate_check.py:41–45`）。**代案:** 正常時は U0 書式を維持し、欠落時だけ `Q - <thid> ...` とする。production 判定器は `-` を D1(c) 違反として数え、数値へ暗黙変換しない。
- **I2・(P4):** `require_gate_witness=False` を API の既定値にすると、要求を渡し忘れた新規 gen-opt 呼び出しが、gate file のない実行を認証し得る。現行 capability 呼び出しは `pipeline.py:683–694`、委譲先は `core.py:381–404`。**代案:** 公開 API では keyword の明示を必須にし、既存 campaign の呼び出し点だけ `False` を明記する。CLI は既存利用との互換性のため指定なしを `False` とし、gen-opt の実走は `--require-gate-witness` を必須引数として事前登録・起動器でも検査する。既存 campaign を暗黙に新方針へ切り替えない。
- **I3・(P5):** 全結果へ無条件に `meaning_version=v2` を追加すると、gate file のない既存 campaign の JSON が変わる。`result_to_dict` の現在の投影は `report.py:96–137`。**代案:** 既存投影をそのまま保ち、要求あり、または gate file を検出した結果にだけ `gate_witness` 節と意味版 `gen-opt-gate/v2` を追加する。既存の v1 判定は当時の記録として保持する。
- **I4・(P7):** 「32 本すべて v1」と「land 後の E1-stale」は同じ意味ではない。現行 closure は既に 96 path で、過去の exact path 群を別に持つ（`campaign_lock.py:47–74,151–203,245–269,312–336`）。**代案:** lock の schema・記録された blob 集合・現行 bytes との一致を別々に報告する。歴史 lock を新 bytes へ書き換えず、現行発行が必要な fixture だけ別途生成する。

(P2) の `id_`、(P3) の thread local 有効化、(P6) の integrity 分類には同意する。ただし `id_` を使う安全性は下記の全 protocol 確認と D297 実測を条件とする。

## U1 の計画 (file:line)

F `25898d00` の子 commit 一つを作り、変更は `include/trace.hh`、`include/ycsb.hh`、`cc/silo/transaction.cc` の TRACE 内に限る。gitlink、pin 定数、patch 登録簿には触れない（brief:9–11）。

| 場所（F の行） | 追加内容と TRACE=0 の行番号 |
|---|---|
| `include/trace.hh:25–35,65–78` | 既存の外側 `#if TRACE` 内へ `<vector>`、`GateOp`、`gate_stream(thid)`、Q/V emitter、thread local の「Silo YCSB 有効」状態と pending txid を追加。`gate_stream` は `gate_<thid>.log` を開き、Q は U0 §1.1 の `R/W/M:key:observed:written` を出す。pending txid は `take` で必ず消費し、未受領なら `-`。header 全体が既存の `#if TRACE` 内なので、新しい `#line` は不要。 |
| `include/ycsb.hh:15–17` | `#if TRACE` 内で `trace.hh` を include。直後、元の `gflags` include の前に `#line 17`。他の六 protocol の翻訳単位もこの header を読むため、この復元は必須。 |
| `include/ycsb.hh:106–109` | `run` に thread local の 48 bit 範囲を検査する書き手通番と、試行ごとの `GateOp` vector。`RETRY` の直後に vector を clear。追加区間の後は、次の元の行を指す `#line 108`、`#line 109` をそれぞれ置く。abort/retry の手順を Q へ混ぜない。 |
| `include/ycsb.hh:124–127` | READ 成功時、`t.id_` と key を R に記録。次の元の行へ `#line 127`。 |
| `include/ycsb.hh:129–133` | WRITE の `obj[i].ref()` 後、`t.id_ = ((thid+1)<<48)\|++seq`、W を記録。`tx.update` の前に `#line 132`。 |
| `include/ycsb.hh:137–143` | RMW は旧 `id_` を観測値として採り、`val_` コピー後、新しい `new_tuple.id_` を書き手刻印にして M を記録。`tx.update` の前に `#line 142`。 |
| `include/ycsb.hh:161–167` | `commit()` が true の直後、Silo 有効時だけ pending txid を消費して Q を一行出す。元の commit counter の前に `#line 166`。 |
| `cc/silo/transaction.cc:605–616` | Silo の YCSB/v2 枝（`izanagi_tx_type == 0`）でのみ gate を有効化し、C に使う `izanagi_txid` を pending として渡す。TPC-C/v3 枝には渡さない。既存の `#if TRACE` と、その後の `#line 635`（`transaction.cc:588–666`）の内側に置くため追加 `#line` は不要。 |
| `cc/silo/transaction.cc:677–699` | UPDATE の入力 `body_` 先頭 8 byte を `memcpy` で局所整数へ取り、`V txid key stamp` を **既存 TRACE 区間の `#endif` より前**に出す。条件は YCSB/v2 であること。元からある `#line 658` の前に置く。`#line 658` の後に追加してはいけない。 |

U0 の F 版 patch（`instr-silo-gate-witness-F.patch:16–47,65–123,128–152`）との差は、Silo 限定の有効化と pending txid の消費、欠落を表す `-`、上記 `#line` 復元、V を既存 TRACE 区間へ移すことに絞る。U0 patch の `last_commit_txid()` 初期値 0 をそのまま使うと「渡し忘れ」を正常な txid 0 と取り違える（同 patch:26–42）。

`__LINE__` の確認対象は `ycsb.hh:146` の `ERR` と、`transaction.cc:739–740` の `ERR`、さらに header を展開する各 protocol の翻訳単位である。F の `transaction.cc` には `#line 635/658/679/700` が既にあり（`transaction.cc:665–666,697–699,727–729,751–753`）、V を `#line 658` の前へ置けば後続の行番号は戻る。`ycsb.hh` にはこの復元がないため、各追加区間の直後に元の次行を指定する。前 wave は `ERR` の展開行番号だけで D297 header 比較が失敗する例を確認した（`silo-intra-txn-fix/README.md:59–66`）。最終確認は文字列除去の推測ではなく D297 の全 consumer 比較とする。

`YCSB::id_` は先頭 8 byte、`val_` はその後である（`ycsb.hh:40–53`）。初期 load は `id_=i`（同:179–188）。F の YCSB 経路での `id_` 参照は宣言、未使用の instance `createKey()`、load 代入であり、`run` は毎回 static `YCSB::CreateKey(pro.key_,...)` を使う（同:40–50,117–120,185）。`external/ccbench/cc/{silo,mocc,si,tictoc,cicada,oze,ermia}` の `.cc/.hh` について `rg -n 'YCSB|\.id_'` を確認した範囲でも、load 後の YCSB payload `id_` 読みは見つからない。`createKey()` を将来の別経路で呼ぶと刻印を key と誤用し得るので、この前提と検索結果を commit の説明に固定する。V の 8 byte 取得は `sizeof(uint64_t)` と実 payload 長を確認してから行い、TPC-C 文脈で実行しない。

型特性で Silo を識別する案より thread local の有効化を採る。型特性だけでは「Silo の commit が txid を渡し忘れた」場合も Q を出せるが、`run` と Silo 専用型の結合が強くなる。ここでは Silo の v2 C emit と同じ場所で有効化し、Q 側で pending が空なら `-` を出す。SI/MOCC は独自の trace を持つがこの有効化を呼ばず、TicToc/Cicada/Oze/Ermia は共通 `run` だけを通っても gate file を開かない。Silo では pending を毎 commit で消費するため、古い txid の再利用も防ぐ。

受入手順は次のとおり。

1. 計算ノード上の U1 checkout で前 wave の `run_ci_build_v2.sh:21–45,96–152` を F→U1 tip に合わせ、Release 全体 build を rc=0 で走らせる。`check_format_ci.sh:13–19` で追跡対象 213 `.cc/.hh/.cpp` に clang-format 14 `--dry-run --Werror`、件数 213・rc=0 を要求する。
2. `python3 tools/check_trace0_preprocess_identity.py --repo <checkout> --old <F> --new <U1-tip> --cxx /usr/bin/g++-11 --header-cc /usr/bin/gcc-11 --third-party-cache <cache> --dependency-prefix <prefix> --scratch-root <scratch> --expect-paths cc/silo/transaction.cc include/trace.hh include/ycsb.hh` を GCC 11/12 で各一回。header の四引数を省くと checker が拒否する（`check_trace0_preprocess_identity.py:1076–1089`）。期待は双方 rc=0。差分 path 集合と header consumer が全件照合された report を保存する。
3. TRACE=0 の `ycsb_silo.exe` と、同じ U1 tip から作る性能用の各 YCSB binary に `buildcache._assert_no_trace_symbols`（`buildcache.py:3787–3815`）を適用する。TRACE=1 の binary へ掛けない。D297 は前処理同一性、記号検査は trace 名の残留という別の検査として記録する。

## U2 の計画 (file:line、擬似コード)

**配置。** `orchestrator/verifier/parse.py:534–540,875–905` に `gate_<thid>.log` の列挙・厳密 parser を追加し、`core.py:29–53,174–191` で compact trace の参照と突き合わせる。新 module は作らない。これなら現在の D442 enforcement closure（`campaign_lock.py:49–74`）の path 集合は変わらず、歴史用 exact path 定数（同:151–336）と `test_campaign_lock_codec.py:875–905` の golden path 列を編集する必要もない。gate がない非要求呼び出しは、現行 `_parse_trace_dir_compact` の経路を通した後、追加照合を起動しない。gate が一部でもある場合は、全 thread 分を要求して照合する。

compact 側は `_CompactTrace.files` と `winner_path_index/winner_row`（`parse.py:181–245,829–850`）から thread 内の C…E 順と R/W の key/version を取り出す。`parse_trace_dir()` の全 `Txn` 化を常用しない。gate は thread ごとに逐次読んで一取引分の V と Q を保持し、producer の `(key, version)→V stamp` と後で解決する初回読みだけを保持する。200k 取引・各 5 操作ではおおむね O(取引数＋操作数＋R/W 数) 時間、メモリは producer index と未解決読みが支配する。Q 全件の Python object と trace 全件の `Txn` を二重保持しない。まず 200k 規模の peak RSS・wall time を計算ノードで測り、既存 compact verifier の上限に収まることを受入に含める。

**照合順。** 書式・到達可能性に失敗しても parser 例外を「検査なしの緑」へ変えない。判定上は integrity の到達不能計数と位置付き note に落とし、巡回が見つかれば既存 `VerifyResult.verdict` の non-serializable 優先（`model.py:554–567`）を維持する。

```text
trace = 既存 compact parser の全 C…E 枠
gate_paths = gate_<整数>.log
if require または gate_paths が一つ以上:
    trace の thread 集合 == gate の thread 集合 == {0..n-1} を確認
    各 thread で Q の順序・txid・thidを C…E 枠と一対一で照合
    Q の n、R/W/M、16 桁小文字 hex key、十進 uint64、
      R/W/M ごとの '-' の位置を厳密検査
    Q txid='-' は D1(c) 違反、数値 Q の重複・欠落・余分も D1(c)
    V は同一 thread・同一 txid の UPDATE W と (txid,key) で一対一
    V の欠落・重複・余分、非 UPDATE、書式破損は到達不能
    書き手刻印は上位16bit=thid+1、下位48bit=1..2^48-1
    genesis 刻印は上位16bit=0、期待値は key_hex を整数化した値
    到達不能なら D1/D2 を合格として計上しない
    各 txn:
        q_write = {key | Q op W/M}
        q_read  = {key | Q op R/M}
        first_read = {key | その key の最初の Q op が R/M}
        D1(a): q_write == W_keys
        D1(b1): first_read ⊆ R_keys
        D1(b2): R_keys ⊆ q_read
        D1(c): 上の枠/Q 対応に違反なし
        last_own_write = {}
        Q を順にたどる:
            初回 R/M 読み:
                対応する R の version を記録
                version=(1,0) なら observed == int(key_hex) [D2a]
                それ以外は producer の同 key/version の V と
                    observed を比較 [D2a]
            既に自分が書いた key の R/M 読み:
                observed == last_own_write[key] [D2b(i)]
            W/M: last_own_write[key] = written
        全 key で last_own_write[key] == V(txid,key) [D2b(ii)]
```

D2a で初回 R/M と R の対応が一意でない場合は推測せず到達不能にする。同一 key の重複した読みは版を一つに畳む Silo の仕様を踏まえ、最初の外部読みを照合する。`D1` が key 集合である理由と D2 の全 key 要求は設計正本 `gen-opt-correctness-gate/README.md:121–134,206–209` に従う。発生条件は `own_write_read_transactions`、`written_transactions`、重複 key・各手順型を production 結果へ計数する。「0 の走行は判定に使わない」は verifier の certified 条件へ固定せず、事前登録した生死確認の呼び出し側が `not-exercised` として採否を決める。通常の読みだけ workload を 0 件のため不正扱いしない。

**結果と証拠面。** `model.py:475–519` の `Integrity` に D1(a/b1/b2/c)、D2a、D2b(i/ii)、到達不能の計数を追加し、`clean()` はいずれか非ゼロなら false。`notes` は現行 `List[str]` を保ち、各違反を `check=D1.b1 txid=... thid=... key=... expected=... observed=...` の一定書式で、上限付き sample と総数にする。機械可読の詳細は gate 結果節に `{check,txid,thid,key,expected,observed}` の exact fields として別投影し、規律 3 の帰属を保つ。`report.py:96–137` と `core.py:194–215` で gate 有効時だけ投影する。receipt は判定結果全体の digest を取る（`core.py:284–293`）ので内容変更は digest に入るが、`commit_receipt.py:345–361,426–479` の receipt **外側の exact key 集合**は増やさない。gate を要求したか、意味版、発生条件は verifier result digest 内に入れ、別 key を receipt に足す必要はない。

**API と D5。** `core.py:29–36,381–404` に明示 keyword `require_gate_witness` を通し、CLI `cli.py:38–75` に `--require-gate-witness` を追加する。`pipeline.py:683–694` の現行 campaign 呼び出しは `False` を明示する。将来の U5 は `True` を渡さなければならない。D5 は既存 `ProofSurfaceAssessment` の X/P/I `as_record()`（`model.py:57–91`）に無条件の第四 key を足さず、gate 専用 assessment を別に持つ。理由は既存 VERIFY_DONE と receipt 周辺の exact projection を保存するため。

D5 は Silo `ycsb_silo.cc` が `ycsb.hh` を include する実物（`external/ccbench/cc/silo/ycsb_silo.cc:18`）、`ycsb.hh` の Q emitter、`transaction.cc` の txid 受け渡しと V emitter が literal `#if TRACE` 内にあることを source text で見る。現行 `compiled_protocol_source_texts` は CMake `SOURCES` の `.cc` しか取らない（`model.py:119–180`）。capability 経路で後から mutable header を読むことは避け、`CompiledProtocolSourceSnapshot`（同:183–201）に対象 YCSB header の正規化済み text を明示 field として束縛し、`source_digest.py:129–177` の exact serialize/deserialize schema と fanout の再水和テストも更新する。旧 snapshot は gate 非要求時には受理し、要求時は header 不在を D5 unavailable とする。source text は D5 の必要条件であり、実際の発火は Q/C…E の照合で確かめる（設計正本:126）。この部分は brief の「verifier と最小 pipeline だけ」という見積りを広げるが、build に結び付いた証拠面を守るため必要である。

**意味版と再検証。** 定数 `GATE_MEANING_VERSION = "gen-opt-gate/v2"` を `model.py` に置き、gate 結果節へ記す。結果を見る前に次の文を `prereg.md` と commit に固定する。「v1 の歴史記録は再発行・昇格しない。v2 再検証の対象は、事前に列挙し保存した gate file を持つ trace のみ。gen-opt 候補の certified は v2、要求あり、D1/D2/D3/D5 と発生条件の事前登録を全て満たす場合に限る」。設計正本 §5.4 と brief:18,31 に沿う。

## test と変異の計画

`orchestrator/tests/test_verifier.py` の既存 fixture 形式と test seam（同:59–67,1393–1426,1723–1760）を使い、まず実走 trace の小さい切り出しを正常系の基準にする。異常を一条件ずつ作るものは小さな手製 fixture にする。各 test は `verdict`、該当計数、`notes` の txid/key、他の新計数が 0 であることを確認する。

| test 名の案 | 入力・殺す変異 |
|---|---|
| `test_gate_b1_missing_initial_read` | 初回 R/M の R 欠落。B1、C1、C2、D1(b1) 比較除去。 |
| `test_gate_b2_unregistered_write` | Q の W/M に対応する W 欠落。B2、D1(a) 比較除去。 |
| `test_gate_b3_readonly_without_frame` | Q だけある読み専用 commit。B3、D1(c)・D3。 |
| `test_gate_b4_wrong_version_payload` | R が指す版と観測刻印が違う。B4、C3、D2a 比較除去。 |
| `test_gate_b5_corrupted_installed_payload` | 後続取引が読む V の刻印と観測値を違わせる。B5、C3。 |
| `test_gate_b6_stale_own_read` | W→R の古い観測値。B6、C3b、D2b(i) 比較除去。 |
| `test_gate_b7_missing_emitter_source` | 有効な Q/V と C…E、Q emitter のない source。B7、C5、D5 のみ。 |
| `test_gate_last_write_wins` | 同一 key を二度書き、V を最初の書きにする。C3b、D2b(ii) 比較除去。 |
| `test_gate_q_missing_or_extra_or_reordered` | Q と枠の一対一・順序を各一条件で破る。C4、到達可能性比較除去。 |
| `test_gate_v_missing_duplicate_or_extra` | V/W の一対一を各一条件で破る。到達可能性比較除去。 |
| `test_gate_thread_missing_and_bad_format` | thread file の一部欠落、未知 tag、非 ASCII、overflow、不正 key、不正 sentinel、不正 stamp を個別に拒否。 |
| `test_gate_n1_fixed_stock` ほか N2/N3/N4 | 修正済み stock、手書き方策、blind write、読み専用多数を緑にする。各々必要な発生条件の実数も確認。 |
| `test_gate_legacy_projection_unchanged` | gate file のない既存 fixture に明示 `False` を渡し、従前の `result_to_dict_v3`、verdict、receipt digest 入力を旧期待値と byte 単位で比較。 |

B8/B9 は verifier fixture ではなく、設計正本 §3.4 の文法拒否テストを既存検疫側で維持する。DW-M01 の単一理由性のため、C5 は B7 の「Q 欠落」fixture を流用しない。D2a・D2b・到達可能性の比較を一つずつ外す変異は上表の専用 test がそれぞれ殺す。巡回と gate 違反を併発させる test では non-serializable 優先だけを確認する。

## 生死確認の計画と事前登録の案

前 wave の `launch_gate_liveness_v2.py:53–215` を一条件一 job の起動器に分ける。四つの source 条件は **F の素の TRACE=1**、**U1 tip**、**U1 tip＋Silo 修正 patch**、**U1 tip＋B1**。各条件で W-rmw と W-blind を同じ build から一回ずつ走らせるので 4 job・8 run。flags は `thread_num=4, ycsb_tuple_num=200, ycsb_zipf_skew=0.9, ycsb_rratio=50, ycsb_max_ope=5, extime=1, clocks_per_us=1800, KEY_SORT=0`、rmw だけ true/false（`gen-opt-gate-liveness/README.md:74–83`、起動器:149–173）。job は別ノードへ割り、checkout・patch SHA・binary SHA・trace/gate archive SHA・stdout/stderr・commit/abort 数を保存する。

F の素の build には gate file がないので production CLI は要求なしで既存判定を取り、U1 の三条件には `--require-gate-witness --protocol silo --ccbench-root <実 checkout> --expected-commits <counter> --json` を使う。U0 `gate_check.py` は独立の二重確認として同じ trace/gate archive に実行し、D1/D2b・発生条件の件数を production と比較する。U0 には D2a と D5 がないので、その一致を全検査の一致とは呼ばない。B1 の pin 用 patch は F の `transaction.cc` の整形・行位置にそのまま当たらない可能性が高い。U1 tip 上で `git apply --check` を通る B1 を作り直し、初回 R/M key の登録省略が **commit した取引数**を独立に数える（元 patch:43–75、U0 実測:115–120）。

結果を見る前の登録文は次の形にする。

| 条件 | 採用条件・期待 |
|---|---|
| F 素の TRACE build | gate file なし。U1 有無による commit・abort の差を記述し、性能値の判断に使わない。 |
| U1 tip 修正なし | 到達可能性 pass、D1 全項 0、D2b(i) または (ii) が各 workload で ≥1、production は indeterminate。 |
| U1 tip＋修正 | 到達可能性 pass、D1/D2a/D2b 全項 0、D2b(i)(ii) の発生条件が各 ≥1、既存巡回 0、commit counter 一致、D5 成立、certified。 |
| U1 tip＋B1 | B1 committed ≥1、D1(b1) ≥1、両者の件数一致を独立に確認。production は indeterminate。 |

発生条件 0、trace/gate 欠落、build 失敗、U0 との不一致はいずれも期待一致と数えず、原因を残す。F と U1 の commit・abort 差は観測者効果の記述値であり、差が 0 という事前期待を作らない。

## 計算の見積り

U0 は一条件の trace build と二 workload が約 112–143 秒、四 job の既往合計 420 秒だった（`gen-opt-gate-liveness/README.md:85–92`）。本 wave の四条件は各 **約 2–4 分、合計 8–16 分＝0.13–0.27 node 時間**を見込む。production verifier の D2a と archive 処理の余裕を含め、trace job 枠は 0.4 node 時間とする。

D297 は header consumer 展開が支配し、前 wave の一比較は GCC ごと約 965–971 秒だった（`silo-intra-txn-fix/README.md:53–65`）。GCC 11/12 の二本で約 0.55–0.7 node 時間を予約する。Release 全体 CI build と format は cache の効き方次第なので 0.3–0.5 node 時間、合計 **約 1.25–1.6 node 時間**を事前見積りとする。2 node 時間に近づく兆候があれば job 投入前に再見積りする（`common-4.txt:27–30`）。D297 と CI を同一 job にまとめても node 時間は各 job の実経過の合計で数える。

## 閉包の分類と赤になる test

DW-O09 の生出力 `s1-pin-closure.log:1–93` と brief:41–43 を次のように扱う。

| 分類 | hit と扱い |
|---|---|
| **live copy** | `campaign_lock.py:49–74` の現行 closure と `qualification/contract.py:75–81` の現行コード identity。判定器 bytes の変更を新たな発行に反映する。新 module を作らないため path 数は維持。 |
| **独立 golden** | `test_campaign_lock_codec.py:875–905` 等の過去 epoch 用 exact path 列、`test_artifact_admission.py`、`test_t126_pegasus_tools.py`、`test_t671_source_binding.py`、`test_p3_b4_producer_auth_experiment.py` の拒否期待。過去の path 数・hash を現行値へ一括置換しない。現行 closure を生成して比べる test だけ新 bytes に更新する。 |
| **凍結 snapshot** | `fixtures/b10_backoff_shape_locks/{balanced,read-heavy,write-heavy}.campaign.lock` にある旧 `report.py`・`__init__.py` hash、`output/env/pegasus/silo_ladder_rung1/*.json`、`acceptance_duration_ledger.json` の記録済み値。歴史的入力として維持し、必要なら現行 lock fixture を新規に作る。 |
| **歴史記録** | `output/insights` の identity・bundle・compare・prerun、mocc-g2 receipt。旧判定の証拠なので再発行しない。`s1-pin-closure.log:9–93` の hash hit は参照であり、現行 bytes への更新指示ではない。 |

赤になり得るのは、現行 closure hash を固定した `test_campaign_lock_codec.py` の live copy 検査、旧 fixture を「現在の発行物」と仮定する `test_artifact_admission.py` と `test_t671_source_binding.py`、T126 と ladder の現行 identity 検査である。各 test の失敗を「現行発行の期待が古い」か「凍結物を誤って現行扱いした」かで分類し、前者だけ更新する。歴史 decoder の拒否 test と凍結 JSON の hash は触らない。`__init__.py` を変更しなければ、その hash hit 自体は今回の差分では赤にならない。

## 所有の分け方 (実装子 2 本が触る file の排他)

- **U1 実装子:** F からの CCBench 新 branch の `include/trace.hh`、`include/ycsb.hh`、`cc/silo/transaction.cc` のみ。B1 の作り直しと計算 node 起動器は repo 外の生死確認担当へ渡す。Silo 修正 branch、gitlink、`patches/` は所有しない。
- **U2 実装子:** `orchestrator/verifier/{parse,model,core,report,cli}.py` と `orchestrator/tests/test_verifier.py`。D5 の build 束縛に必要な `orchestrator/campaign/source_digest.py`、fanout snapshot codec の test、`pipeline.py` の明示 `False` は U2 側にまとめる。`campaign_lock.py` の path 集合と歴史 fixture は変更しない。
- **親:** Q/V schema、`-` sentinel、gate result の exact fields を二実装子へ先に固定して伝える。prereg の commit、CI/D297、四 job、独立 U0 照合、閉包 test の判定と最終受領を担当する。共有 file の同時編集を作らない。

## 総括

実装上の要点は、Silo だけが Q を出す有効化、txid 欠落を隠さない `-`、F の `#line` を保つ V の配置、build に結び付いた `ycsb.hh` の D5 証拠面である。判定器は gate 入力がある実行を常に厳密照合し、既存の gate file なし campaign は明示非要求で従前どおりにする。計算前に期待と再検証対象を commit し、四条件・二 workload の実走で D1、D2a、全 key の D2b、発生条件、certified を確認する。ここで述べた build・D297・テスト・計算結果は計画であり、この read-only 段では実行していない。