## 所見

1. **must-fix — gate 登録だけでは Cicada を受理できない。** [brief-stage1.md:52](/work/1/SFC/tanab/tmp/vhash-forwarding-prototype-2026-09-29/brief-stage1.md:52) は登録簿への entry 追加だけを認めるが、[condition_meaning_gate.py:1122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/orchestrator/campaign/condition_meaning_gate.py:1122) は `protocol="cicada"` を拒否する。段 2 プランの [out.md:55](/work/1/SFC/tanab/tmp/vhash-forwarding-prototype-2026-09-29/codex/stage2r/out.md:55) の指摘は正しい。放置すると smoke は `request-contract-invalid` で止まり、計測値は得られない。**修正案:** Cicada の登録済み macro だけを許す変更を明示的な仕様差分として扱い、未登録 Cicada macro と既存 protocol の負例を保つ。

2. **must-fix — gate の緑を C/F の動作保証と呼べない。** [out.md:21](/work/1/SFC/tanab/tmp/vhash-forwarding-prototype-2026-09-29/codex/stage2r/out.md:21) は C/F を同じ `ENABLE=1` binary の実行時 flag で分ける。一方 meaning 腕が観測するのは owner TU の `#if` 選択である（[condition_meaning_gate.py:3675](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/orchestrator/campaign/condition_meaning_gate.py:3675)）。`ENABLE=1` の二つの翻訳単位が異なることは確認できても、C と F の各経路が発火する証拠にはならない。放置すると F が実質 stock でも「2 腕 admitted」の一次資料になり得る。**修正案:** gate receipt は compile 条件の証拠と記し、C/F それぞれの発火・abort・再試行は別の実行証拠で拘束する。

3. **must-fix — P2/P3 は B-3 の射程を実質的に迂回する。** 原依頼は ledger entry を要求する（[md_6.txt:21](/work/1/SFC/tanab/tmp/vhash-forwarding-prototype-2026-09-29/inputs/md_6.txt:21)）。rung1 契約は確かに entry 数を一件に固定する（[silo_ladder_rung1_contract.py:513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/orchestrator/campaign/silo_ladder_rung1_contract.py:513)）。しかし B-3 は `IZANAGI_` だけを抽出する（[test_p3_s4_loop.py:8681](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/orchestrator/tests/test_p3_s4_loop.py:8681)）。接頭辞を外して ledger も省けば、この検査による台帳拘束はなくなる。condition gate の登録は別の拘束であり、ledger の代替と同一視できない。放置すると patch の分類・所有・評価用途を機械的に結ぶ entry が成果物から欠ける。**修正案:** 共有 ledger と rung1 契約を別件として整合させるか、所有範囲内で機械検査可能な専用 manifest を定め、原依頼との差を裁定として明記する。

4. **should — 計測条件の規模と費用は未較正。** [brief-stage1.md:42](/work/1/SFC/tanab/tmp/vhash-forwarding-prototype-2026-09-29/brief-stage1.md:42) の 100 万件は Silo の較正値であり、Cicada の飽和下限を示さない。[out.md:88](/work/1/SFC/tanab/tmp/vhash-forwarding-prototype-2026-09-29/codex/stage2r/out.md:88) の 58 分は build・初期化を仮定した算術値で、実測ではない。放置すると小さすぎる作業集合で GC/版探索を評価したり、2 node 時間の上限を超えたりする。**修正案:** smoke で Cicada の build・初期化・一走の時間と cache miss を取り、条件数との積を投入前に再計算する。

5. **should —仕様とプランの macro 契約が食い違う。** [out.md:21](/work/1/SFC/tanab/tmp/vhash-forwarding-prototype-2026-09-29/codex/stage2r/out.md:21) は `COUNT=1` に `ENABLE=1` と `LONGTX=1` を要求するが、[out.md:62](/work/1/SFC/tanab/tmp/vhash-forwarding-prototype-2026-09-29/codex/stage2r/out.md:62) の `DefineSpec` は `ENABLE=1` しか companion にしない。放置すると gate が確認した構成と計数 binary の構成がずれる。**修正案:** 必須 companion と実 build flags を一致させ、receipt に最終 binary の flags と hash を結ぶ。

6. **nit — brief の仕様草案パスが誤っている。** [brief-stage1.md:8](/work/1/SFC/tanab/tmp/vhash-forwarding-prototype-2026-09-29/brief-stage1.md:8) は `/work/SFC/...`、実際に射影された file は `/work/1/SFC/...`。放置すると後続の読込が失敗する。**修正案:** 実在パスへ訂正する。

## 反例

- **`later_ver_` を残すと既読検証を飛ばせる。** T の旧 ts を 15、A のリストを `A30 → A20 → A10` とし、T が A10 を読んで `later_ver_=A20` を保持する。その後 ts を 25 に進め、A20 が可視なら本来 A10 は不一致である。検証が旧 `later_ver_` から始まると、先頭側の変更を見落とす経路がある（[transaction.cc:543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/external/ccbench/cc/cicada/transaction.cc:543)）。放置すると誤 commit か誤った計測値になる。**修正案:** 草案どおり read/write set の全 `later_ver_` を成功時に破棄し、この操作を変異として検査する。

- **`new_ver_->wts_` を旧 ts のままにすると、版の時刻と tx の検証時刻が分離する。** T が ts 15 で UPDATE 版を生成し、ts 25 へ前進して commit すると、生成時の wts は 15（[transaction.hh:217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/external/ccbench/cc/cicada/include/transaction.hh:217)）、検証・GC queue の時刻は 25（[transaction.cc:717](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/external/ccbench/cc/cicada/transaction.cc:717)）になる。放置すると後続 reader の版選択と GC の根拠が食い違う。**修正案:** 通常・再利用・inline の全 `new_ver_` の atomic wts を、設置前に書き換える。

- **特殊操作を後から混ぜると「未公開で前進」の前提が崩れる。** T が通常 read で前進した後に INSERT すると、`insert()` は commit 前に tuple を Masstree へ挿入する（[transaction.cc:313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/external/ccbench/cc/cicada/transaction.cc:313)）。[spec-draft-v1.md:14](/work/1/SFC/tanab/tmp/vhash-forwarding-prototype-2026-09-29/spec-draft-v1.md:14) の「INSERT/DELETE を含む tx は対象外」は過去の操作だけを調べても満たせない。放置すると対象外と称した tx が前進後に特殊操作へ入る。**修正案:** 段 2 プランどおり workload を READ/UPDATE/RMW に限定し、API 側でも前進済みの特殊操作を拒否する。

今回読んだ範囲では、**これらを仕様どおり処理した後にも serializability を破る確定的な interleaving は示せなかった**。ただし「最終 ts で stock validation を走らせる」だけでは、操作範囲、版の寿命、時刻の一意性を証明したことにはならない。

## 成立する主張

- 旧 `ThreadWtsArray` を据え置く設計は、GC 下限を前進させない方向である。leader は各 thread の最小 wts/rts を採り（[util.cc:281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/external/ccbench/cc/cicada/util.cc:281)）、GC は `MinRts` を基準にする（[transaction.cc:806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/external/ccbench/cc/cicada/transaction.cc:806)）。これは保守的な方向だが、stock の時刻・GC 不変条件を前提とする静的論証であり、実測済みの保証ではない。
- scan と read-only を除外する判断は必要である。scan も `read_internal` を呼び（[transaction.cc:445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/external/ccbench/cc/cicada/transaction.cc:445)）、read-only commit は validation を通らない（[transaction.cc:934](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/external/ccbench/cc/cicada/transaction.cc:934)）。
- gate 登録への**賛成論**は、patch の新しい `#if` を独立 inventory が検出し、未登録のままでは既存検査が赤になる点で強い（[test_ccbench_spawn_sites.py:2917](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/orchestrator/tests/test_ccbench_spawn_sites.py:2917)）。**反対論**は、所有外の gate と期待値を同じ作業で編集し、受理集合を広げる点である。patch を置かない案は依頼の実装目的を満たさず、別の置き場も D18 の inert patch 方針から外れる。**結論:** 必要最小限の登録を採る。ただし Cicada protocol 許可は「entry 追加だけ」ではない仕様変更としてレビューし、既存負例を維持する。件数の更新だけを緑の根拠にしない。

## 総括

最大の停止要因は **Cicada が現行 gate に拒否されること**と、**ledger 省略・接頭辞変更が B-3 の台帳拘束を外すこと**である。実装後の stock validation は重要な最終検査だが、C/F の発火、特殊操作の排除、時刻・版の整合までを単独で保証しない。今回の結論は指定資料と pin の静的検査に限り、build・テスト・計測は実施していない。