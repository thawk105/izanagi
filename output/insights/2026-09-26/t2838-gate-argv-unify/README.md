# 受入門番の leader の数え方を argv 先頭一致に統一し、写し元を repo 外の雛形 1 本にした — 採用前に走行中の受入 1 本で見逃し 0・誤検出 0 を実測し、採用後の取り直し (雛形経由の門番 0 本の基準線で、採用の効果ではない) では 9/21 以降の leaders 起因閉門のうち記録上の走行 ≤ 1 は約 14% (診断時 約 49%、期間と門番の混在比が違う) だった。30 分以上の待ちは 11 区間残るが、択 B は採らず再提示の材料として記録する ([T-2838] 択 A、2026-09-26)

authority: none / default_effect: no-state-change (実施記録と測定値のスナップショット。可変状態の正本ではない)

wave `dev-wave-t2838-gate-argv-unify` (branch `worktree-t2838-gate-argv-unify`、ユーザー直接起動)。依頼の逐語は `verbatim/origin.md`。
裁定は D2211 項 4 (択 A だけ採る、写し元は repo 外 1 本、閾値の変更でなく記憶正本の徹底) と D2219 項 5 (A の後に同じ probe で取り直し、長い待ちが残れば B を改めて提示)。
一次資料は `output/insights/2026-09-21/acceptance-gate-wait-diagnosis/README.md` §3・§7。

**変えたもの:** repo 外の雛形 1 本 (`/work/1/SFC/tanab/dev-wave-jobs/_shared-templates/run-acceptance-gated.sh`) と記憶 `acceptance-gate-no-workers-threshold` (索引行を含む) だけ。
**変えていないもの:** 閾値 (他 leader ≤ 1、1 分 load ≤ 60、pigz ≤ 2)、周期 (100〜140 秒)、2 連続 → 0〜45 秒後の再カウント、lease TTL、待ち手 (`tools/dev_wave_wait.py`)、
lease primitive、他 wave の job dir にある既存の門番 script。repo の実装面の差分はゼロ。

## 結論 (最初に読む)

1. **雛形を 1 本置いた (14:36:53 JST、sha256 b30be0fbafe5ea9be50476becd37a102649c528272b2d9672d6cf0ca18726623)。**
   写し元は `dev-wave-t2273-shard0-local-copy/run-acceptance-gated.sh` (9/26 13:07、同日に green まで通った script、sha256 ae9af50d…) で、
   JOBDIR / WT / SLUG の 3 値を placeholder にし、先頭コメントを写し方の説明に替えただけである (論理・条件値・leader 行は bytes のまま。`verbatim/run-acceptance-gated.sh.md`)。
   leader 行は裁定の正規表現 `^(python3|[^ ]*/python3?) [^ ]*dev_wave_wait\.py acceptance` を逐語で使う。
2. **設置前は 3 系統が並んでいた。** 現存する門番 script の新しい 40 本 (9/21 22:30 〜 9/26 13:07) は、部分文字列一致 22 本、裁定の正規表現 6 本、
   `^python3( -u)? tools/dev_wave_wait.py acceptance` (絶対 path 起動を数えない) 12 本だった (14:1x に数えた値)。その時点で 9/26 に作られていた 3 本のうち 2 本も部分文字列一致だった。
   数えた後の 14:20 に [T-2864] の門番 (狭い形) が加わったので、設置時点の 9/26 の門番は 4 本 (部分文字列一致 2・裁定の正規表現 1・狭い形 1) である (§2)。
3. **採用前の一致実測 (14:36 JST):** 走行中の受入 1 本 (pid 2659242、[T-2864] wave) について、`/proc/<pid>/cmdline` を引数単位で読む独立の判定と、
   同時刻の `ps -eo args` への正規表現の一致が {2659242} で一致した。見逃し 0・誤検出 0 (§3、`verbatim/live-argv-match.md`)。
4. **採用後の取り直し (同じ probe を逐語で、`--since 2026-09-21 --until 2026-09-26T14:38`):** 9/21 以降の leaders 起因閉門は 445 tick (推定 891.9 分)。
   そのうち記録上の走行 ≤ 1 は 61 tick (推定 122.9 分、約 13.8%) で、診断 (9/19〜9/21 07:37) の 502 tick (推定 1003.0 分、約 48.9%) より小さい。
   走行 0 本での閉門は 0 tick だった。数え方別では、部分文字列一致の門番 305 tick のうち 44 tick、argv 先頭一致の門番 140 tick のうち 17 tick が走行 ≤ 1 だった (§4)。
   **この差は雛形の効果ではない。** 取り直しの時点で雛形経由の門番 log は 0 本で (設置 14:36:53、締め 14:38)、差は期間と門番の混在比の違いを映す。
5. **長い待ちは残っている。** 9/21 以降の observed-wait は n=139 で、中央値 174 秒・p90 1,688 秒・最大 4,604 秒。30 分以上の待ちは 11 区間 (うち打切り 1)、
   飢餓候補は 1 件 (dev-wave-t2830-b5-node-local-lock、2,874 秒、再カウント拒否 2)。11 区間の門番は部分文字列一致 7・argv 先頭一致 4 だった。
   依頼どおり択 B (他 leader 上限 2 の期間限定試行) は採らず、再提示の材料を §5 にまとめた。
6. **argv 先頭一致でも説明できない閉門が残る。** 直近帯 (9/23 08:47 〜 9/26 14:35) の argv 先頭一致の門番 17 tick は、記録上の走行 1 本の時刻に leaders=2 を数えている。
   codex 子の prompt 文字列はこの数え方では数えないので、別の原因 (門番の記録を残さない受入、テストが起動する本物の waiter など) が要る。
   当時の process 一覧が無いので原因は決められない (§5.2)。

## 1. 何をしたか (順序)

| 時刻 (JST) | 操作 | 出所 |
|---|---|---|
| 14:0x | 開始 gate rc=0 (local main 74e6d2f2 と乖離 0) | job dir `startup-gate.log` |
| 14:03 | 生きた受入 leader の出現待ちを張る (その時点で受入 0 本) | `verbatim/live-argv-match.md` |
| 14:1x | 起動形の静的集計、門番 40 本の数え方の集計、固定 argv 8 行の正例・負例 | `verbatim/regex-fixture-and-launch-forms.md` |
| 14:14 | 採用前の基準として probe を 14:14 締めで走らせる (rc=0、self-check 4 件 passed) | job dir `probe/pre-0921-1414.md` |
| 14:1x | 雛形を job dir の staging に作る (cp + 3 値とコメントの置換、diff で確認) | `verbatim/run-acceptance-gated.sh.md` |
| 14:35〜14:36 | 受入 1 本の出現で一致を実測 (見逃し 0・誤検出 0) | `verbatim/live-argv-match.md` |
| 14:36:53 | 雛形を `_shared-templates/` に設置、記憶を更新 (= 採用) | 本 README §2 |
| 14:40 | 採用後の取り直し (14:38 締め、rc=0、self-check 4 件 passed) | `verbatim/probe-post-adoption.md` |
| 14:4x〜15:0x | 段 6 の独立 read-only レビュー 1 本 (Claude opus): 照合 47 行中 41 一致、条件付き GO。must-fix 2・should 5・nit 5 を全件 real と裁定し本文・記憶を訂正 | 本 README (訂正後)、worklog fragment |

段 2・3 (codex の起草・敵対相談) は軽量版として省いた (設計択一は裁定済み、正しさ防壁・受理集合に触れない、`verbatim/s4-ruling.md`)。
雛形は既存 script の写しと 3 値の置換だけで論理を変えないので、job dir の launcher を親が書く運用 (DW-C01・DW-O01) の範囲として親が作った (段 1 の (P1)、`verbatim/s1-brief.md`)。

## 2. 雛形と記憶

- 置き場: `/work/1/SFC/tanab/dev-wave-jobs/_shared-templates/run-acceptance-gated.sh` (同 dir の既存 file は `run-land-chained.sh` だけ)。
- 使い方 (雛形の先頭コメントと記憶に書いた): wave の job dir へ `cp` し、`JOBDIR=__JOBDIR__` / `WT=__WT__` / `SLUG=__SLUG__` の 3 行だけ置換する。
  条件を締める一時措置 (例: 見送り中の `maxl=-1`) は job dir の `gate.conf` (毎周回 source) で行い、緩める変更は gate.conf でもユーザー裁定とした。
- 記憶 `acceptance-gate-no-workers-threshold` に 2026-09-26 節を足し、索引行に写し元の path を書いた。9/18 節の「部分文字列一致は正しい」という記述には、
  9/20 に誤りと判明した旨を先頭に付けた (記述は消していない)。
- probe (`gate_wait_probe.py`) は job dir の `run-acceptance-gated.sh` (または `gate-acceptance-loop.sh`) という file 名で門番 script を探し、
  `conditions()` が `maxl=` 等の行から条件値を、`ps -eo args` と `grep` を含む行から数え方を読む。条件値を書き換えても probe はその値を読むだけで警告しない。
  leader 行を部分文字列一致に戻せば `substring` に分類され、file 名を変えたり行の形を崩したりすると `unknown` になる。写すときは file 名と行の形を保つ。
- 既知の取りこぼし: 正規表現は `python3 -u …` と `python3.10 …` 起動を数えない。雛形の受入起動は `python3 tools/dev_wave_wait.py acceptance` なので該当しない。
  job dir 直下 script の全期間の起動形では、該当は 8/21 の 2 本 (`wave-t1403-walltime-sigterm`) だけだった (`verbatim/regex-fixture-and-launch-forms.md` §2)。

## 3. 採用前の一致実測

`verbatim/live-argv-match.md` に方法と結果を置いた。要点:

- 真の leader は正規表現と独立に、`/proc/<pid>/cmdline` の引数単位で「argv[0] が python*、ある引数の basename が `dev_wave_wait.py`、次の引数が `acceptance`」と定めた。
- 2 回取り、2 回目は ps の取得と cmdline の走査を同じ実行内 (14:36:23.44〜14:36:32.38) で行った。どちらも真の leader {2659242} と正規表現の一致が同じだった。
- 他 wave の門番を乱さないため、偽 leader の負例は live で作らず、固定 argv 8 行で確かめた (裁定の正規表現は正例 2 行だけを数え、包み shell と codex 子の prompt 文字列の負例を数えない。
  部分文字列一致は負例 2 行を数える)。

## 4. 採用後の取り直し (同じ probe、`verbatim/probe-post-adoption.md`)

probe は一次資料 `verbatim/gate_wait_probe.py.md` の code block をそのまま取り出したもの (sha256 796d1b65… 一致)。引数は一次資料 §10 と同じ形で、
`--since 2026-09-21 --recent-n 20 --until 2026-09-26T14:38:00+09:00 --exclude-wave dev-wave-t2838-gate-argv-unify --self-check`。
門番 file 140、wave 84、observed-wait 139、打切り 5、日付未解決 0、mtime 日付復元 5 (推定)。

### 4.1 leaders 起因閉門 (leaders-only + both) × 走行数 × 数え方 (tick 数 / 推定分)

| 母集合 | 数え方 | 走行 0 | 走行 1 | 走行 ≥ 2 | 計 |
|---|---|---|---|---|---|
| 診断 9/19 以降 (一次資料 §3.4) | 部分文字列一致 | 83 / 168.3 | 387 / 772.7 | 475 / 948.3 | 945 |
| 診断 9/19 以降 (一次資料 §3.4) | argv 先頭一致 | 0 / 0 | 32 / 61.9 | 51 / 98.1 | 83 |
| 取り直し 9/21 以降 | 部分文字列一致 | 0 / 0 | 44 / 88.4 | 261 / 524.3 | 305 |
| 取り直し 9/21 以降 | argv 先頭一致 | 0 / 0 | 17 / 34.5 | 123 / 244.7 | 140 |
| 取り直し 直近 20 | 部分文字列一致 | 0 / 0 | 12 / 24.1 | 58 / 119.1 | 70 |
| 取り直し 直近 20 | argv 先頭一致 | 0 / 0 | 17 / 34.5 | 40 / 80.8 | 57 |

- 取り直し 9/21 以降の合計は 445 tick / 891.9 分で、走行 ≤ 1 は 61 tick / 122.9 分 (122.9 ÷ 891.9 ≈ 13.8%)。診断は 1028 tick / 2049.3 分のうち 502 tick / 1003.0 分 (≈ 48.9%)。
- 取り直しの `argv 先頭一致` には、裁定の正規表現と `^python3( -u)? tools/…` の狭い形の両方が入る (probe はこの 2 つを区別しない)。
- 記録 leaders − 走行数の差は、9/21 以降で部分文字列一致の走行 1 が差 1 に 39・差 2 に 5 tick、argv 先頭一致の走行 1 が 17 tick すべて差 1 だった。

### 4.2 閉門理由 (tick 数 / 推定分。直前 tick 配分であり因果寄与ではない)

| 理由 | 直近 20 | 9/21 以降 |
|---|---|---|
| open | 87 / 127.7 | 341 / 480.5 |
| leaders-only | 127 / 258.5 | 439 / 880.1 |
| load-only | 0 / 0 | 5 / 10.6 |
| both | 0 / 0 | 6 / 11.8 |
| pigz | 0 / 0 | 0 / 0 |
| unknown | 37 / 66.2 | 68 / 111.3 |

閉門の大半が leaders 条件であることは診断と同じだった。

### 4.3 待ちの分布 (秒、observed-wait、打切りは混ぜない)

| 母集合 | n | 中央値 | p90 | 最大 | 打切り | 再カウント拒否 | 30 分以上 | 飢餓候補 |
|---|---|---|---|---|---|---|---|---|
| 直近 20 (観測 9/23 08:47 〜 9/26 14:35) | 35 | 351 | 1,472 | 3,681 | 1 | 5 | 3 (打切り 1) | 0 |
| 9/21 以降 | 139 | 174 | 1,688 | 4,604 | 5 | 17 | 11 (打切り 1) | 1 |

### 4.4 読み方

- **雛形の効果はこの表に入っていない。** 雛形経由の門番 log は締めの時点で 0 本である。この表は「採用時点の基準線」であって、採用の効果の測定ではない。
- 診断との差 (48.9% → 13.8%) は、期間の違い (9/21 以降は 5 日分)、門番の数え方の混在比の違い (argv 先頭一致の門番の閉門が 8% → 31%)、
  部分文字列一致の門番でも走行 0 本の閉門が消えたこと (83 → 0 tick) を含む。どれがどれだけ効いたかは分けていない。
- 9/21 以降の母集合は log の mtime で選ぶので、9/21 00:00〜07:37 に書かれた log は診断の母集合と重なりうる。直近 20 (9/23 以降) は重ならない。
- probe の `since-2026-09-19` 行は、コードで固定された名前の母集合 (since かつ開始日 ≥ 9/19) で、今回は since と同じ集合になる。

## 5. 択 B 再提示の材料 (依頼により今は採らない)

### 5.1 残る長い待ち (30 分以上、9/21 以降の 11 区間)

`verbatim/probe-post-adoption.md` の「飢餓候補と長時間待ち」節の since 行。observed-wait は 1,840〜4,604 秒で、門番は部分文字列一致 7 本・argv 先頭一致 4 本、
区間中の走行最大は 2〜3 本だった。飢餓候補は dev-wave-t2830-b5-node-local-lock の 1 件 (2,874 秒、再カウント拒否 2、部分文字列一致の門番)。
直近 20 では 3 区間 (dev-wave-t2850-trial-prereg 3,681 秒、dev-wave-t2854-v3-existence 3,195 秒、dev-wave-t2847-corpus-gaps 1,826 秒の打切り)。

### 5.2 argv 先頭一致でも残る不一致 (原因は未確定)

直近帯の argv 先頭一致の門番で、記録上の走行 1 本の時刻に leaders=2 を数えた tick は時刻が固まっている。例:

- 9/23 10:16〜10:21: dev-wave-t2273-acceptance-bottleneck-diag・dev-wave-t2850-trial-prereg・dev-wave-t2854-mocc-v3-emitter の 3 門番が同時に leaders=2。記録上の走行は dev-wave-t2847-corpus-gaps の 1 本。
- 9/23 21:22〜21:40: dev-wave-paper-story-20260923 の門番が leaders=2。記録上の走行は rulings-all-20260923c の 1 本 (dev-wave-t2853-rerun-plan の受入は 21:18:51 に finished、
  dev-wave-t2858-mocc-xp-pin の受入は 21:53:43 開始で、どちらもこの窓の外)。同じ窓に更新された受入関連 file を job dir 全体から探したが、2 本目の走行記録は見つからなかった。

走行 wave ごとの偏り (段 6 レビューの指摘を親が再計算): argv 先頭一致の門番の tick のうち記録上の走行がちょうど 1 本のものを、その走行 wave 別に
leaders=2 の割合で数えると、dev-wave-t2847-corpus-gaps 8/8、dev-wave-t2853-rerun-plan 6/6、dev-wave-t2860-k2-round4-reflux 4/6、rulings-all-20260923c 5/12、
dev-wave-t2851-tpcc-prereg 1/8 で、他の 32 wave は 0 だった (jq で全 tick を数えた値。閉門理由の分類前なので §4.1 の 17 tick とは母数が違う)。
特定の走行の間だけ 2 本目が見えている。corpus-gaps と rerun-plan の受入は、どちらも門番 script から標準形 `python3 tools/dev_wave_wait.py acceptance` で起動しており、
script からは 1 本が 2 本に数えられる仕組みは見えない。

候補 (断定しない): (a) 門番の記録 (started.txt) を残さない受入の起動、(b) login で走るテストが起動する本物の waiter
(`orchestrator/tests/test_dev_wave_wait.py`・`test_dev_wave_land.py` は `sys.executable <tmp>/tools/dev_wave_wait.py acceptance …` を子で起動し、login の `sys.executable` は
`/usr/bin/python3` なので正規表現に一致する。ただし短命なので 18 分続く 2 本目の説明には弱い)、(c) probe の走行区間の推定 (finished の欠落補完) の誤差、
(d) 当時 (9/23) の waiter の版で、1 本の受入の子 process が `dev_wave_wait.py acceptance` を含む argv を持っていた可能性 (本 wave が確かめたのは現行版の
`_LAUNCHER_BOOTSTRAP` だけで、9/23 時点の版は確かめていない)。
当時の process 一覧が無いので決められない。門番 log に leader の pid と argv を残せば次回は帰属できるが、それは門番への記録の追加であり、
本 wave の scope (仮想リスク向けの検査・台帳の追加は scope 外) では入れていない。再提示時の選択肢として挙げるに留める。

### 5.3 再提示の材料の読み方 (親の案。裁定の条件ではない)

再提示の条件は D2219 項 5 の「A の実施後に同じ probe で閉門の内訳を取り直し、なお長い待ちが残る場合に B を改めて提示する (試すときは待ち・受入 wall・赤率を
同時刻対照で比べる)」だけである。本 wave の取り直し (§4) で 30 分以上の待ちは 11 区間残っているので、条件そのものはこの記録で満たされうる。以下は提示の際に
材料を読むための案で、提示を遅らせる関門ではない。

1. 雛形の効果を見たいときは、同じ probe を `--since 2026-09-26` と提示直前の `--until` で走らせる (probe の取り出しは一次資料 §10 の手順 1)。
2. 雛形の門番は `leaders_grep = argv-anchored` に分類されるが、probe は裁定の正規表現と狭い形を区別しないので、雛形経由かどうかは job dir の script と雛形の差分 (3 値だけか) で見る。
   probe の wave 表の green-receipt 列は `acceptance-receipt-green.json` だけを見るので、受領証を `acceptance-receipt-<TAG>-green.json` に書く雛形の wave は常に `no` と出る。
3. 長い待ちの区間が実在する受入との競合 (走行 ≥ 2) か、記録との不一致 (走行 ≤ 1) かを分けて示すと、B (上限を上げる) が効く待ちかどうかを読み手が判断できる。

## 6. 限界・言わないこと

- 採用前の一致実測は 1 回で、走っていた受入は 1 本 (`python3 tools/…` の主形) だけだった。絶対 path 起動の実走は観測していない (固定 argv でだけ確認)。
- 真の leader の判定も「argv が waiter の acceptance 起動に見えるか」を見るだけで、それが本物の受入か (テストの子か) は区別しない。
- 採用後の取り直しは雛形の効果を測っていない (§4.4)。待ちが減るかどうかは保証しない (D2211 項 4)。
- 既存の job dir の門番 script は書き換えていない。走行中・待機中の wave は旧来の数え方のまま門番を回し続ける。雛形は次に門番を写す wave から効く。
  ただし設置後の 14:42 に作られた rulings-all-20260926 の門番は雛形を写していない (独自の関数型で、leader 行は裁定の正規表現と同じ)。写し元の統一は記憶に頼る運用で、機械的には強制されない。
- 採用前実測の process 表 2 本は job dir へ写した時刻 (14:36:39) の mtime を持つ。取得時刻 (14:36:14 / 14:36:23) の裏付けは file 名と実行時の `date` 出力だけである。
- 雛形の placeholder を置換し忘れると、`cd __WT__` が失敗して `.done` も書けず (JOBDIR も placeholder)、待ち手が完了を検出できない。置換は写す側の責任で、検査は足していない。

## 7. この dir の中身

- `README.md`: 本文。
- `verbatim/origin.md`: 依頼の逐語。
- `verbatim/s1-brief.md` / `verbatim/s4-ruling.md`: 段 1 brief と段 4 裁定。
- `verbatim/run-acceptance-gated.sh.md`: 雛形の逐語 (sha256 b30be0fb…)。
- `verbatim/regex-fixture-and-launch-forms.md`: 固定 argv の正例・負例、受入起動形の静的集計、門番 40 本の数え方の集計。
- `verbatim/live-argv-match.md`: 採用前の一致実測。
- `verbatim/probe-post-adoption.md` / `probe-post-adoption-stdout.md`: 採用後の取り直しの出力と stdout。出力 md は `git diff --check` の末尾空行に当たるため、
  末尾の改行 1 byte だけを除いた (原本 job dir `probe/post-0921-1438b.md`、104,587 bytes、sha256 64209a81828b0029634a119ae994c587a55b1877d014dcda3a34de996260436d。
  復元は末尾に `\n` を 1 byte 足す。可視文字は不変)。
- repo に入れないもの (job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2838-gate-argv-unify/`): 取り出した probe (`probe/gate_wait_probe.py`)、機械可読の全区間 record
  (`probe/post-0921-1438b.json`、約 5.6 MB)、採用前の基準線 (`probe/pre-0921-1414.md` / `.json`。9/21 以降の母集合は採用後と t2864 の 1 file (開門 2 tick) の差だけだが、直近 20 は構成が違う:
採用後は t2847-patch-verify が抜けて t2864 が入り、leaders-only 132 → 127、open 91 → 87、observed-wait n 36 → 35)、process 表の全文 (`probe-pre/ps-snap-*.txt`)。

## 8. 再現手順

1. 一次資料 `output/insights/2026-09-21/acceptance-gate-wait-diagnosis/verbatim/gate_wait_probe.py.md` の code block (6〜850 行目) を repo 外へ `gate_wait_probe.py` として取り出し、sha256 796d1b65… を確かめる。
2. `python3 <dir>/gate_wait_probe.py --jobs-root /work/1/SFC/tanab/dev-wave-jobs --claude-jobs-root /home/SFC/tanab/.claude/jobs --since 2026-09-21 --recent-n 20 --until 2026-09-26T14:38:00+09:00 --exclude-wave dev-wave-t2838-gate-argv-unify --out-json <out>.json --out-md <out>.md --self-check`
   (login、読むだけ、数十秒)。log は job dir の削除で消えるので、後日の再走は完全には再現しない。
