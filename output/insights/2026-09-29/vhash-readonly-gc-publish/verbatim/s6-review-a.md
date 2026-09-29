## 1. 所見

1. **must-fix — [ro_gc_publish.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/vhash_forwarding_model/ro_gc_publish.py:23)**
   探索は 2 worker・1 key・ro read 1 回に固定され、裁定 A-1 の上限である 3 worker・2 key・ro read 2 回を扱わない。例えば A を保持したまま B を後で読む場合、現行の oracle は B の必要版を調べられない。**影響:** safe 腕の違反 0 を裁定の探索範囲全体の結論として使えない。**修正案:** 指定範囲を探索するか、結論を現行の一点に限定し、追加構成を未確認と明記する。

2. **must-fix — [ro_gc_publish.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/vhash_forwarding_model/ro_gc_publish.py:222)**
   bad-raise-slot は `State()` からではなく、`MinWts=40`、古い `A10` の保持、`GCFlag[0]=1` が同居する別の prefix から始まる。stock では R が flag を立てず、この prefix の到達性は示されていない。さらに現行の safe 系でも、最初の公開が R の flag を消費するため、この *同じ* prefix への到達は未証明。bad-clear-slot は `State()` から始まり、提示された 27 step はモデル内の到達列だが、flag を立てる変更も同時に含む。**影響:** 23 step の正例を通常実行からの最短反例と呼ぶと、一次資料の根拠が過大になる。**修正案:** 共通の初期状態から更新・公開・保持まで遷移させ、必要なら flag を再度立てる手続きも明示してから最短列を取り直す。bad-clear は「variant に slot clear を加えた正例」と明記する。

3. **must-fix — [ro_gc_publish.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/vhash_forwarding_model/ro_gc_publish.py:137)**
   safe 腕では `A10` を切る条件が `MinRts>30` だが、R の slot は初期値 9 または次の read の 19 に留まり、通常の遷移では 30 を超えない。したがって GC の境界 load や `gc_no_cut` は起こり得ても、古い版の切断は起きない。oracle 自体は回収境界と独立している一方、結果 JSON に回収 step の件数もない。**影響:** safe 腕の「GC 違反 0」は、危険な回収機会を通過した証拠にならない。**修正案:** safe 腕で適法な鎖切断が実際に起きる状態列を加え、腕ごとの boundary load・cut・no-cut 件数を出し、テストで非ゼロを要求する。

4. **should-fix — [ro_gc_publish.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/vhash_forwarding_model/ro_gc_publish.py:98)**
   J1 に渡す更新取引 U と版履歴は固定で、探索中の更新・読取手続きの履歴を構成していない。U の read log は常に空であり、この固定履歴の閉路 0 は並行履歴の探索結果ではない。begin の 3 手、leader の各 load/store、GC の境界 load と切断は別 step で、参照した Cicada の行順とは概ね対応する。**影響:** 「閉路 0」を裁定 A-3 の直列化可能性探索として図示すると根拠が弱い。**修正案:** 遷移で生成した取引履歴を J1 に渡すか、このモデルの閉路 0 を固定履歴の確認に限定する。

5. **must-fix — [vhash_ro_gc_publish.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/campaign/vhash_ro_gc_publish.py:299)、[plot_vhash_ro_gc_publish.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/plotting/plot_vhash_ro_gc_publish.py:28)**
   作図器は raw の `measurement_env.records/extime/workers` を必須とするが、driver はこれらを raw の最上位にのみ書く。`load_raw()` は欠けた `measurement_env` を `None` で埋めるため、正規の全量計測 raw でも `paired_values()` が拒否する。**影響:** 裁定 B-5 の 2 図を実測 raw から生成できない。**修正案:** driver と作図器の schema を一致させ、正規 raw を通す結合テストを加える。

6. **must-fix — [vhash_ro_gc_publish.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/campaign/vhash_ro_gc_publish.py:118)**
   `verify_acceptance()` は rc=3、indeterminate=1 を `accepted=True` にし、driver 全体も成功終了し得る。[verifier CLI](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/verifier/cli.py:11) の契約では rc=3 は認証不能で、正しさゲート通過は rc=0 のみ。裁定の「indeterminate に上限」と認証済みの判定を区別できていない。rc=1 の巡回、rc=2 のエラー、mismatch、COUNT=0 を拒否する部分は正しい。**影響:** 認証不能な trace が正しさの合格として記録される。**修正案:** 上限内の indeterminate は診断値として残し、正しさの `accepted` と成功終了には rc=0 を要求する。

7. **must-fix — [test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/tests/test_condition_meaning_gate.py:3865)**
   登録簿の文書は `Fifty-four` に更新されたが、テストは `Fifty-one` を assert したまま。静的に、この assert は失敗する。DefineSpec、分岐件数、header companion、screening 既定値、loop 許可表、materializer、spawn site、README の追加は差分上そろっており、`ycsb.hh` は owner TU の `ycsb_cicada.cc` に include される。**影響:** 登録簿のテストが赤になり、完了判定を妨げる。**修正案:** assert を `Fifty-four` に更新し、該当テストを実走する。

variant patch の `mainte()` は `read_set_.clear(); node_map_.clear();` の後にあり、macro 0 の前処理行番号は `#line` で stock に戻す構造である。COUNT は ro commit の前後で同一 thread の flag を確認し、終了時に owner TU で全 thread を合算する。workload patch も手続き選択を retry の前に置き、別乱数系列、非 ro の write 保証、読取後の worker 1 の待機を実装している。ただし **前処理の実一致、3 preimage への適用 rc=0、C++ build と実行時カウンタは未確認**。

## 2. 裁定との対応表

| 項目 | 判定 | 主な理由 |
|---|---|---|
| A-1 | 満たさない | 探索範囲が 2 worker・1 key・1 read のみ |
| A-2 | 一部 | oracle は独立、bad-raise の初期 prefix と安全側の回収発火が未立証 |
| A-3 | 一部 | 公開探索はあるが、J1 の履歴が固定 |
| A-4 | 一部 | 違反数・witness は出すが、正例の到達性と安全側の非空な GC 検査が不足 |
| A-5 | 満たす | 独立 module の CLI と JSON 出力を実装。実走は未確認 |
| B-1 | 一部 | patch の位置と計数構造は合う。build・実発火は未確認 |
| B-2 | 一部 | workload の構造は合う。3 build での実際の同一性は未確認 |
| B-3 | 一部 | 条件・均衡順序・macro 記録は実装。verify の認証扱いに穴 |
| B-4 | 一部 | 登録は概ねそろうが、文書件数のテストが失敗する |
| B-5 | 満たさない | raw と作図器の schema が合わず、図を生成できない |

## 3. GO / NO-GO

**NO-GO。** 小モデルの安全結論、verify の正しさ合格、実測図を現状のまま一次資料へ採用すべきではない。C++ patch は静的には裁定の挿入位置と workload の主要条件に沿うが、build と実行時の確認待ち。

## 総括

このレビューは静的検査のみ。実装子申告の **3 preimage 適用 rc=0、各腕の状態数・違反数、23/27 step の最短性は未確認**。親の pytest・C++ build・計算ノード実走の結果も、この結論には含めていない。