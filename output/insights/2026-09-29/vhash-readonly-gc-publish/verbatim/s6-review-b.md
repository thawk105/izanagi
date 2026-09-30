## 1. 所見

1. **must-fix — [test_condition_meaning_gate.py:3862](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/tests/test_condition_meaning_gate.py:3862)**
   test は旧文言 `Fifty-one` を期待するが、対象の [condition_meaning_gate.py:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/campaign/condition_meaning_gate.py:12) は `Fifty-four` に更新済み。実走前でも、この assertion は失敗すると分かる。**放置すると受入 test が赤になる。** 関数名と期待文言を 72／54 件へ更新する。

2. **must-fix — [ro_gc_publish.py:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/vhash_forwarding_model/ro_gc_publish.py:98)**
   探索中の J1 入力は固定の版集合と、read が空の更新 tx から作られる。実探索での「閉路 0」は、GC flag の各 interleaving に応じた直列化可能性の検査になっていない。手作り履歴を渡す [adapter test:115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/tests/test_vhash_forwarding_model_rogc.py:115) は adapter 単体だけを検査する。**放置すると全探索が serializability を示したと読める成果物になる。** 状態から実際の read／write 履歴を構成して J1 に渡すか、探索の結論を GC 安全と公開到達に限定する。

3. **must-fix — [ro_gc_publish.py:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/vhash_forwarding_model/ro_gc_publish.py:186)、[test:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/tests/test_vhash_forwarding_model_rogc.py:99)**
   段 4 裁定は「ro 途中の flag だけ」は公開前進しない予想で、前進したら停止・再裁定としている。実装子は前進ありと報告し、test も `assert result["progress"]` としている。**放置すると事前登録した陰性対照の反証を緑として通す。** まず witness の flag・slot・公開時点を確認し、裁定どおり停止してモデルまたは前提を再裁定する。モデルの `progress` は境界値の変化であり、公開回数とは別である点も明記する。

4. **must-fix — [plot_vhash_ro_gc_publish.py:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/plotting/plot_vhash_ro_gc_publish.py:48)**
   wait10msR の stock が公開 0 回なら境界年齢平均は未定義になり、作図器は対差を `None` にする。さらに図は variant−stock だけで、段 4 が (b) の観測値と定めた「variant の wait10msR 対 none の境界年齢差」と公開時の ro 保持者割合を出さない。両値の材料は [driver の `vlife` と `summary`:235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/campaign/vhash_ro_gc_publish.py:235) の raw にある。**放置すると図 2 枚から (b) を再計算・確認できず、公開 0 の条件の境界年齢も空欄になる。** stock 公開 0 は回数として明示し、(b) の条件間差と保持者割合を raw から集計して図または数表へ出す。保持時間そのものは未測定と記す。

5. **should-fix — [vhash_ro_gc_publish.py:276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/campaign/vhash_ro_gc_publish.py:276)、[同:375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/campaign/vhash_ro_gc_publish.py:375)**
   smoke は default genome の bare stock／variant と trace／vlife variant の **4 build** と短走を記録するが、tuned build、verify、再走余地を含む 2 node 時間の判定値は算出しない。本計測は measure と throughput が各 2 genome×2 arm＝計 8 build、各 12 条件×6 対×2 run＝各 144 run。verify は variant 2 build・最大 24 run で、分割 job ごとに準備と build が増える。**放置すると smoke が成功しても時間予算内と判断できない。** build 時間、run 壁時間、依存準備時間を使い、予定 job 数・verify・再走余地を含む見積りを smoke receipt に記録する。`--conditions` で条件単位の分割は可能だが、予定分割表も残す。

6. **should-fix — [vhash_ro_gc_publish.py:299](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/campaign/vhash_ro_gc_publish.py:299)**
   raw は hostname と開始・終了時刻を持つので、md_18・md_20・md_21 の receipt があれば事後の重複照合は可能。ただし driver 内に他 job の receipt、node 割当て、非同居の判定結果は無い。**放置すると raw 単体では「同じノード・同じ時刻に測っていない」と証明できない。** 親の投入前 qstat 記録と他 wave の receipt を一次資料に結び、hostname と時間区間の照合結果を保存する。

7. **should-fix — [test_vhash_ro_gc_publish.py:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/tests/test_vhash_ro_gc_publish.py:78)、[同:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/tests/test_vhash_ro_gc_publish.py:84)**
   patch test は `mainte();` の位置と write 保証の**文字列**を確認する。MB2・MB8 の字面を消す変異には反応する見込みだが、同じ字面を残して順序や write の実効を壊す変更は検出しない。**放置すると構造 test の緑を挙動の証拠と誤認する。** 前処理済み ro 分岐と workload の実走カウンタ・非 ro の実際の write を、焦点走で確認する。

8. **should-fix — [ro_gc_publish.py:222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/vhash_forwarding_model/ro_gc_publish.py:222)**
   bad-raise-slot は `MinWts=40`・古い保持 pointer から直接開始する。実装子自身も stock 遷移からの到達性を未証明としている。**放置すると 23 step witness が Cicada の通常実行から到達可能な正例として引用されうる。** 初期 prefix の到達 witness を追加するか、「仮定した状態からの条件付き反例」と限定する。

## 2. 削除・縮小の提案

| 要素 | 判定 | 一次資料への作用と最小形 |
|---|---|---|
| 小モデルの安全 oracle、2 つの危険腕、最短 witness | **残す** | GC 安全と危険な slot 操作の区別に必要。規模は module 301／test 153 行で上限内。 |
| 小モデルの固定履歴 J1 と「閉路 0」の主張 | **縮小** | 現状の全探索結果には効かない。状態由来の履歴に直せない場合は adapter 単体 test を残し、探索結果から serializability の主張を外す。 |
| variant patch と workload patch | **残す** | 公開介入と、計器あり／なしで共通の ro 手続きに必要。各 43／142 行で上限内。 |
| COUNT 計器 | **残す** | verify で variant 経路を踏んだ証拠に必要。性能 build から外す現形が最小。 |
| driver の `--records`・`--extime` | **削除候補** | measure／throughput を変えても作図器は 1M・3 秒以外を拒否する。固定値にし、短走規模は smoke／verify 内に残す。 |
| throughput macro 検査の二箇所 | **縮小** | [事前検査:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/campaign/vhash_ro_gc_publish.py:112) と [記録時検査:211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/campaign/vhash_ro_gc_publish.py:211) が重複する。記録時の fail-closed を残し、MB4 の test をそこへ向けられる。 |
| smoke／verify／measure／throughput | **残す** | preimage、経路発火、診断、性能のそれぞれに使用経路がある。driver 411／test 131 行で上限内。 |
| 作図器の 2 図と layout 検査 | **残す・補う** | 図の再生成と図規約に必要。作図器 219 行。ただし所見 4 の (b) 集計を追加する。 |
| 登録簿、spawn-site、build authority の追加 | **残す** | 新 macro と subprocess／build の既存ゲートを閉じるために必要。旧件数 test の修正が必要。 |

## 3. 変異の殺傷予測

| 変異 | 予測 | 根拠・不足 |
|---|---|---|
| MA1 | **殺す見込み** | 危険腕の `gc_violations > 0` と固定 witness。 |
| MA2 | **殺す見込み** | bad-raise-slot の最短 step 列を固定。ただし初期 prefix の到達性は別問題。 |
| MA3 | **殺す見込み** | stock の公開前進 0 を検査。 |
| MA4 | **殺す見込み** | safe-mainte の公開前進を検査。 |
| MA5 | **殺せない可能性が高い** | 参照解放前の GC 実行が実害を生まなければ等価変異。段 4 の規定どおり発火確認後に除外・再照準。 |
| MA6 | **adapter 単体では殺す見込み** | 手作り rw 閉路 test がある。ただし探索履歴の J1 接続は検査しない。 |
| MB1 | **未確認** | gate の前処理検査は反応する可能性があるが、新 test は既定 macro の stock 前処理一致を直接検査していない。単一理由の殺傷とは言えない。 |
| MB2 | **字面の移動なら殺す見込み** | `node_map_.clear()` 後の `mainte();` 探索が失敗する。ただし失敗理由は位置 assertion ではなく検索例外になりうる。 |
| MB3 | **殺す見込み** | DefineSpec の inert 値 `("0",)` を明示比較する。 |
| MB4 | **殺す見込み** | `check_throughput_macros` の単体 test が VLIFE を渡す。 |
| MB5 | **一部のみ** | stock 先行が 3 回でなくなる変更は殺す。別の均衡順序なら test が `P.ORDER` をそのまま期待値に使うため生存する。事前固定列を独立に固定すべき。 |
| MB6 | **殺す見込み** | rc=1 を拒否する test 入力がある。 |
| MB7 | **殺す見込み** | flag_raises=0 だけを変えた test 入力がある。 |
| MB8 | **字面の削除なら殺す見込み** | write 保証の文字列を探す。実際に write が発生することは未検査。 |

上記は静的予測であり、変異実走の結果ではない。

## 4. GO / NO-GO

**NO-GO（一次資料の結論を確定する段階）。** 少なくとも所見 1 の確定 test 失敗、所見 2 の serializability 主張、所見 3 の陰性対照と裁定の不一致を解消する必要がある。公開回数の条件内対差は raw の `vlife`、条件、反復、順序から再計算できる設計だが、(b) の図示と時間予算・非同居の証拠を補う必要がある。

## 総括

静的に確認できたのは差分の全 16 file、規模上限、raw の主要項目、作図器の計算経路、test の assertion まで。実装子が報告した 3 preimage への実適用、C++ build、pytest、smoke、verify、性能値、図の実データ layout、最良 genome の trace 網羅は**本レビューでは未確認**。親の実走結果と突き合わせて最終判定する。