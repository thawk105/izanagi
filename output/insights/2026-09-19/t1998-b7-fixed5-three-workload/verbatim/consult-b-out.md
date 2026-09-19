## real

以下、`brief`・`plan` は指定 job dir の資料、`M` は `orchestrator/campaign/paper_story_a2_certification.py` を指す。静的検査のみで、測定・pytest は実施していない。

1. **P1：source の一致を「同一 build の充足」へ読み替えている。**
   - **根拠：** [brief:52](/home/SFC/tanab/.claude/jobs/f6bf33bb/brief.md:52)。実装は `build_attempt_id` と binary digest を個別に持つ（[M:2856](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/orchestrator/campaign/paper_story_a2_certification.py:2856)）。さらに stock の `src_token` は digest ではなく文字列 `stock` である（`orchestrator/campaign/source_digest.py:102`）。09-16 稿 §1.4 も、stock の token と `source_bytes_sha256` を区別している。
   - **壊れ方：** stock token の一致では source bytes の一致を確認できない。source が一致しても、別々に生成された binary が同一とは言えない。stock と adopted 間では genome・define 自体も異なる。
   - **最小修正：** 比較単位を「**同じ arm の workload 間**」とし、実際の `source_bytes_sha256`、define、toolchain、configure 条件、binary digest を列挙する。稿では「同一候補・同一ソース条件から workload ごとに別 build」と書く。binary 不一致を同一 build と宣言しない。配布 build の新設は不要。

2. **P5・P7：同一 attempt は、arm 間隔が数分であることや同時期性を保証しない。**
   - **根拠：** [brief:56](/home/SFC/tanab/.claude/jobs/f6bf33bb/brief.md:56)。performance 検査と bench は別々に lock を取得する（`orchestrator/campaign/pipeline.py:1386,2395–2399`）。probe §3 の実測では、その間に別 request の処理が入っている。submitter も workload 順の逐次 qsub である（`tools/pegasus/submit_paper_story_a2_certification.sh:266`）。
   - **壊れ方：** stock の bench と adopted の bench の間に、adopted の build・検査・他 request の lock 待ちが入る。「直列化は所要だけを延ばし、対照の同時刻性を壊さない」は無条件には成立しない。request 開始時刻だけでは実際の性能測定の間隔が分からない。
   - **最小修正：** 「同一 campaign 内に stock 対照を置く設計」と記し、**各 arm の bench 時刻・arm 間隔・3 workload 全体の測定期間**を稿へ載せる。ユーザーが指定した既存経路による同時期対照には沿うが、文字どおりの同時実行、時間ドリフトの除去、workload 間の node 同一性までは主張しない。queue 分断後も機構上有効な attempt であることと、同時期性の主張は分ける。

3. **P3：欠損した `effects` に対する床値表の扱いが未固定。**
   - **根拠：** brief:45 は3 workload の判定を約束するが、[M:2661](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/orchestrator/campaign/paper_story_a2_certification.py:2661) は `unstable != false`、`rep_notes != []`、標本不備等で median を返さない。M:2901–2903 は correctness が certified、source が bound の場合だけ effect 用 median を採用する。anomaly は M:2873–2876 で reject。
   - **壊れ方：** 生標本から独自に比を作り直すと、「機構の `effects` そのもの」という約束を破る。欠損を退行なしとして扱うこともできない。
   - **最小修正：** 結果を見る前に次を明記する。これは既存出力の読み方であり、新 gate ではない。
     - median は受理された各 arm の5標本に対する `statistics.median`。個々の比の median ではない。
     - 機構の未丸め `effects[w]` と JSON の全桁 floor を比較し、表示の丸めは後。
     - 等号は退行に含めない。`effect == -floor` は strict inequality を満たさない。
     - effect が存在しない行は理由付きの「判定不能」。anomaly の reject は別欄に保持する。
     - 「退行なし」は「優越」「差がないことの証明」を意味しない。

4. **partial 時に「欠落明記で足りる」とする完了扱いは、成果物の約束と衝突する。**
   - **根拠：** brief:47,74–75 と、同:10–12,63–64。実装は全 workload の成功時だけ full manifest を作り、partial は exact 2 workload・1成功に限定する（[M:2296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/orchestrator/campaign/paper_story_a2_certification.py:2296)）。results 系列も完走した結果を単位とする（`docs/paper-story/README.md:254`）。
   - **壊れ方：** 1〜2 workload が失敗した場合、予定した collect 済み leaf と3 workload の床値判定は供給できない。欠落を正直に記録することは必要だが、当初の研究成果を完成させたことにはならない。
   - **最小修正：** partial 一般化は追加せず、欠落時は失敗記録・durable 証拠の所在を残し、**本 wave の予定成果は未達**と明記する。手作業の表を正規 collect 成果物として扱わない。再投入の判断は別にする。

5. **fp-* の共有 lock 競合は、job body に環境変数設定がないことからは導けない。**
   - **根拠：** brief:94。現 checkout の `tools/pegasus/submit_floor_pair.sh:185–189` は `fp-*` を `floor_pair_campaign.sh` へ投入する。同 body:158 は `floor_pair_driver` を起動し、[floor_pair_driver.py:1590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/orchestrator/campaign/floor_pair_driver.py:1590) は直接 `runner.measure_point` を呼ぶ。同 driver と runner に campaign の `bench_lock` 取得は見当たらず、runner:1194 は `run_once` を呼ぶ。
   - **壊れ方：** `IZANAGI_BENCH_LOCK` 未設定は、lock を取得する caller に対してだけ既定 path を意味する。「fp-* 3本も同 lock を使う」という前提で所要を見積もると誤る。
   - **最小修正：** 現 checkout の fp 経路については、その共有 lock 競合を前提から外す。稼働 request の投入 commit・job body・実行経路を照合してから確定する。本 wave 自身の3 request 間の競合可能性とは分ける。

## refuted

1. **「既存稿で足りるので wave に純増がない」は反証された。**  
   09-16 稿:387以降は、10 / 5 / 2 µs の別候補であり、同一 variant の横断比較でも床値判定でもないと明記する。A-1 sized 稿:98–100 も同じ別候補で、同:153–157 の解析は30対の対差平均と3%床である。本 wave は **fixed 5 µs を rr5・rr95 にも適用し、同時期 stock 対照に対する median 比を指定の workload 別床で判定する**。D2044 項3が挙げた不足へ直接材料を足す。純増なしを理由に止める根拠はない。ただし B-7 充足、再現性、統計的有意性までは得ない。

2. **P3 の直接比較そのものはユーザー裁定に整合する。**  
   `rulings-verbatim.md:5,13–26` が量と用途を分けている。D1639 単独が二群比較の統計的閾値を保証するわけではないが、今回のユーザー裁定はその CV を直接使う記述的判定を明示している。実 JSON の `between_run.cv` は次のとおりで、brief と一致した。

   | workload | floor |
   |---|---:|
   | rr5 | 0.009536033056996148 |
   | rr50 | 0.00725042525457718 |
   | rr95 | 0.0022283754708938273 |

   √2補正や別 floor への置換は不要。床は旧 stock の session-median の変動の**下限**であり、本 attempt の effect の標準誤差・有意水準ではない、と限定する。

3. **P2 は「既存手順の別 study instance」という意味なら支持される。**  
   A-6 先例 `60605bec3` は、別 workload・別採用値を既存 A-2 protocol に追加している。一方、[M:344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression/orchestrator/campaign/paper_story_a2_certification.py:344) の `_protocol_preimage` は study・workloads・cells を含むので、新 policy の **protocol identity/hash は新しくなる**。「schema が同じだから同一 protocol hash」という説明は不可。新しい判定手順を設計しない、という読みで既存先例と整合する。既存2 policy を無変更のまま使うと rr5=10、rr95=2 となり、fixed5 横断という依頼を満たせない。

4. **3 workload の full collect を成立させるための partial 拡張は不要。**  
   M:2302、M:2972–2998、M:4848 は policy の workload 集合に従う。性能退行による outer `reject` と driver failure は別であり、`driver_rc` は reject に0を返す（M:3182–3187）。plan の全件経路テストは必要な確認であり、scope 外の一般化ではない。

5. **P6 の「図の材料＝表＋leaf」は成果の範囲に合う。**  
   ユーザーは図の完成ではなく材料を求めている。README:258 の凍結図・provenance 規則は図を伴う場合に適用される。新 plotter は不要。新旧は別表とし、旧値も再掲するなら09-16稿の表を権威にせず、その一次資料へ戻る。新稿には raw／WAL／floor JSON の path・field・SHA-256 と計算式を付ける。機構の `a4_noise_floor_status=open` や outer status を、稿で行う床値判定によって書き換えない。

## 未確認

- **稼働中 fp-* の実際の経路と lock。** qstat は本相談では採取していない。親が request ID ごとの投入 receipt、`expected_head`、job body digest・実行 checkout を照合する。現 checkout と同じ経路なら共有 bench lock 競合の根拠はない。別経路なら、環境変数だけでなく lock 取得 caller まで追う。
- **nodes=5・12hでの完走所要。** probe の680/728秒は rr5/rr50 の別候補、A-6 の約73分は fixed2 の実績であり、fixed5・3 request の予測値ではない。親は投入直前の queue・quota・15 nodes の割当可能性、投入後の queue待ち・実測期間を記録する。予約上限は合計180 node時間。12h内の完走保証にはしない。
- **同一 source 条件と測定間隔の成立。** 回収後、arm別の source bytes・toolchain・binary digest、head identity、bench 時刻を比較する。job 開始差だけで済ませない。
- **旧 canonical 床と現 stock の実行同一性。** JSON に `BACKOFF_FIXED=-1` はなく、現在の patch は既定−1を定める（`patches/silo-backoff-fixed.patch:9–12`）。これは設定上の説明にはなるが、旧 binary・toolchain の同一性証明ではない。床の出自をそのまま記し、現 attempt で再較正した床とは呼ばない。指定 floor は変更しない。
- **新 policy の全件 materialize 実測。** 静的経路は適合するが、まだ成功の証拠ではない。親の実装後テストと実際の finish／collect で確認する。

## 裁定パッケージ候補

**現時点で必須のものはなし。**

ただし「同一 build」が同一 binary bytes を必須とする意味、または「新 protocol 禁止」が新しい `protocol_sha256` 自体を禁じる意味なら、現案では満たせない。その厳密な意味を要求する場合だけ裁定対象となる。語義の曖昧さを理由に配布 build、新 gate、partial 一般化、job body 変更を先行追加しない。

## 総括

本 wave には、同一 fixed5 の他 workload への適用と指定床値判定という研究上の純増がある。  
修正すべきは、同一 build・同時刻性の過大な説明、判定不能行の扱い、partial 時の完了扱いである。  
fp-* の共有 lock 競合は、現 checkout の実行経路からは支持されない。  
判定式は緩めず、既存機構・指定 floor・全 workload 報告を維持して進められる。