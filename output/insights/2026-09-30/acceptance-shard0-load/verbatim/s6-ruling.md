# 段 6 裁定 (review A / B) と事前登録の erratum — acceptance-shard0-load

固定時刻: 2026-09-30 (JST)。対照・変異は 1 件も走らせていない (結果を見る前の訂正)。統合 snapshot: wave commit 29d6693e5 = u1.patch (退避済み)。

## 所見の裁定

| 所見 | 裁定 | 処置 |
|---|---|---|
| A1 / B1 (must) join 超過でも生きた builder の足元で close が木を撤去しうる、非 daemon thread で上限が hang の歯止めにならない | real | F1: 構築 thread を daemon にする。finish は上限 900 秒で join し、生存 thread があれば **close せず** (lifetime lock と木を保持したまま) 例外を送出する。生存 thread が無い通常例は従来どおり join → error 回収 → close。受理: 通常終了は従来と同じ撤去。拒否: 生存 builder がいる間は撤去しない (プロセス終了で lock fd が閉じ、木は /tmp に残りうる。docstring に明記)。通る正例: 構築が終わった後の finish は即座に close して木を撤去する |
| A2 (must) thread 起動失敗時に 1 本目を無期限 join | real | F1: 起動失敗時も同じ上限付き終了手順を使い、生存 thread があれば close せず、元の起動例外を送出する。通る正例: 1 本目が完了済みで 2 本目の start が失敗した例は close して起動例外を返す |
| A3 (should) T6 が危険な撤去を検出しない | real | F1: T6 に「timeout 時点で session 木と controller の lifetime が保持されている」「release 後に明示 close で撤去できる」を足す |
| A4 (should) T1 が別参加者からの hit を検査しない | real | F1: T1 に、`PYTEST_XDIST_TESTRUNUID` を同じ run_id にして `_t080_join_shared_bases()` で得た別の参加者 object から 2 key を `get()` し、builder 回数が増えないことを足す (既存の同一 object での検査は維持) |
| A5 (should) M3・M5・M6 の単一理由性 | real | 変異登録を下の erratum のとおり改める。期待 node の完全集合は dispatch probe で観測してから final を走らせる (DW-M08) |
| A6 (should) 写しの撤去後に consumer が実 repo 複製へ進む | refuted | `_finish_memo_sessions` は controller の sessionfinish で全 worker の終了後にしか走らず、finish 後に consumer が動く順序は無い (conftest の呼出し位置で確認)。構築失敗時は prewarm の finish が可視 output の finish より前に例外を回収する |
| B2 (must) land 条件が T0 だけで W0 の悪化を許す | real | erratum の L4 を足す |
| B3 (must) 対 2 の正式受入を runner が扱わない | real | F2: A 腕だけを起動する単腕 launcher と、正式受入の shard dir を受領証・log から commit 照合つきで取り込む集計を足す |
| B4 (should) A/B の shard 割付の一致を照合しない | real | F2 + erratum: 共通 nodeid の shard-0 所属が A/B で完全一致しない対は「帰属不能」として無効 (D2284 E1' と同じ限定) |
| B5 (should) 対 1 の冷条件を検証しない | real | F2 + erratum: 対 1 は両腕の起動前 tests pyc = 0 を有効条件にする |

fix の分割: F1 (as0-u1、所有 = U1 と同じ 3 file) と F2 (as0-u2、所有 = scratch-as0 の 3 file) は素集合なので並列に投じる。

## 焦点再レビュー 1 巡 (codex/focus-review-out.md) の裁定

- A1〜A4・B1〜B5 closed、A6 refuted 維持、A5 partial (変異 probe で閉じる)。
- 新規 1 (should、起動失敗時の後片付け例外の喪失): real。ただし失われるのは診断だけで、起動例外は送出され session は赤になり受理集合・判定は変わらない (DW-G05: 成果物影響なし)。fix 巡を重ねず残課題として一次資料へ記録する。
- 新規 2 (nit、`Thread.start` 差し替えの範囲): real、残課題として記録。
- 残る NO-GO 理由 (変異 probe、対照、焦点走 2 の赤の帰属) は親の実走で閉じる。fix は 1 巡で閉じる (DW-O16)。

## 対照で判明した実在欠陥と fix 2 巡目 (F4)

- 事実: p1r の B (meas/out/p1r、shard dir b9af6d7a…) と対 2 の B (meas/out2/p1、shard dir 21076594…) がどちらも `acceptance shard gate failed: report-invalid` (rc=16)。両方とも T-080 consumer を持たない shard-2 で、controller の prewarm thread が可視 output の写しの `result.json` を 180 秒待って `RuntimeError: T080 visible output snapshot timed out` を出し、`_finish_t080_shared_base_prewarm` が session 終了時に送出して子 rc=1 ≠ report の pytest_rc=0 になった (dispatcher.log の traceback)。段 3 所見 3 の危険が実際に起きた。写しが 180 秒を超えたのは、親が同時に 12 shard job + 変異 job を流して Lustre を混ませたためもあるが、受入の混雑でも起こりうる。1 回目の対 1 の B (8066fe19…) は緑だった。
- 裁定: real、must。F4 を Codex fix で投じる。prewarm thread は写しの完成を固定 180 秒で打ち切らず、finish が立てる停止 event まで待つ。写しが `ok: false` なら構築せずに戻る (写しの失敗は既存の `_finish_t080_visible_output_snapshot` が従来どおり送出する)。構築開始前に停止 event が立てば例外なしで終える。builder の例外は従来どおり伝播、join 超過時は木と lock を保持して例外。受理: consumer の無い shard で写しが遅くても session は赤にならない。拒否: builder の実行時例外は session を赤にする。通る正例: 写しが 300 秒かかった shard-2 は prewarm が構築を始める前に finish が停止 event を立て、rc は pytest の結果どおり 0。
- T2 は本 wave の新設 test なので、`ok: false` で finish が例外を出さず builder も呼ばれない形へ期待を改める (既存 test の期待値ではない)。停止 event の正例 test を足す。
- 対照: 旧 B (6ec6c1f28) の対照は無効 (p1 は A の flaky 赤、p1r・対 2 は B の本欠陥)。F4 後の新 tip で対照 2 対を取り直す。旧走の A 腕 (p1r・対 2、どちらも緑) と p1 の B 腕 (緑) の値は診断として並記するだけで判定に使わない。
- 変異: F4 は実装の文面を変えるので、全 6 変異を新 tip で再照合して final を取り直す (DW-M07)。

## 対照の判定 (事前登録 L1〜L4、E1・E6・E8)

| 対 | A / B commit | W0 A / B (秒) | pre0 A / B | ΔT0 (A − B) | ΔT0 / T0(A) | ΔW0 | max(W1,W2) B − A | 群 A 合計 A / B |
|---|---|---|---|---:|---:|---:|---:|---|
| 対 1 (meas/out3/p1) | 4f412c67b / 4258b0c76 | 525.350 / 362.512 | 119.691 / 87.352 | +130.499 | +0.322 | +162.838 | −5.872 | 3045.4 / 2187.1 |
| 対 2 (meas/out4/p1r) | 4f412c67b / 7d20b2c1f | 283.538 / 295.224 | 67.715 / 68.728 | −10.673 | −0.049 | −11.686 | +12.738 | 2102.4 / 2194.9 |

- L1 (2 対とも ΔT0 > 0): **偽** (対 2 が負)。L2 (平均 ≥ 5%): 真 (0.136)。L3 (2 対とも max(W1,W2) の悪化 ≤ 20 秒): 真。L4 (2 対とも W0(B) ≤ W0(A)): **偽** (対 2)。
- 判定: 事前登録どおり **実装は land しない**。記録だけを land する (D2242 と同型)。実装は branch `worktree-dev-wave-acceptance-shard0-load` (tip c9af2b562、実装だけの系列は `as0-u1` の 7d20b2c1f) に残す。
- 読み (診断、判定には使わない): 対 1 は親が同時に流した変異・他対の負荷で collection (pre) が約 90〜120 秒と長く、写しの後に始まる構築 (約 100 秒) が test 開始前にかなり進み、T-080 群の合計が 858 秒縮んだ。対 2 は collection が約 68 秒と短く、構築が test 開始に間に合わず、群 A の合計は縮まなかった。効果は collection の長さに依存し、温の木の通常受入では出ないと読むのが整合的 (n=1 ずつで確定ではない)。

## 事前登録の erratum (s4-ruling.md「対照の事前登録」「変異の事前登録」への追補、結果を見る前)

- E1 (L4 追加): 対 1 (両腕とも fresh・冷) で W0(B1) − W0(A1) ≤ 0。対 2 は A2 (fresh・冷) と B2 (正式受入・温でありうる) の pyc の峰が違いうるので L4 の対象外とし、pre の峰と値を並記する。land 条件は L1 ∧ L2 ∧ L3 ∧ L4。
- E2 (割付一致): 各対で、A と B に共通する nodeid の shard-0 所属集合が完全一致しない対は「帰属不能」で無効。
- E3 (冷条件): 対 1 は両腕の起動前 tests pyc が 0 でなければ無効。
- E6 (対 2 の形の変更、2026-09-30 対 1 の結果を見る前に固定): 正式受入は記録 commit を含む最終 tip で走らせる必要がある (land は tested tip をそのまま取り込む、acceptance-discipline) ため、対 2 の B を正式受入で兼ねられない。対 2 は対 1 と同じ専用走 (A2 = 4f412c67b、B2 = 6ec6c1f28、両腕冷) とし、対 1 の木の `__pycache__` を消して tests pyc 0 を確認してから `run-pair-ab.sh` を別 output dir (`meas/out2/`) で pair id `p1` として走らせる。集計は `aggregate-ab.py` を対ごとに当てて値を出し、L1〜L3 は s4-ruling.md の式どおり 2 対から、L4 は **2 対とも** W0(B) − W0(A) ≤ 0 (E1 より厳しい側) とする。正式受入は land 用に別に 1 回走らせ、効果の判定には使わない。
- 対 1 の実走 (15:0x JST 起動、meas/out/p1): **無効**。(a) A 腕 (4f412c67b) が rc=1 (`test_b5_contrast_launch.py::test_v2_three_429s_restart_stock_then_accept_same_a_and_evaluate`、5000 tick × 1 ms の待ちループが負荷下で上限に届く時間依存の赤、本 wave の差分は到達しない、B 腕は同 test 緑)、(b) runner の shard 対応づけが専用走の request.json に無い `runner_binding` を要求して両腕とも missing。事前登録どおり対を無効とし、runner を F3 で直して `p1r` (同じ木を pycache 削除で冷に戻す) と対 2 (新しい木) を同時に取り直す。対 1 の B 腕の値は診断として並記するだけで判定に使わない。
- E8 (F4 後の対照、結果を見る前に固定): 対 1 = meas/out3/p1 (A1 = 4f412c67b、B1 = 4258b0c76、両腕冷・緑、有効)。対 2 = meas/out4/p1 は B が本 wave の新設 test の helper の競合 (`result.json` を直接書き、polling 中の thread が空を読む) で赤 → 無効。F5 (test helper を pending → replace にする test-only 修正、実装 conftest.py 不変) の後、対 2 を `meas/out4/p1r` で取り直す。B2 は `as0-u1` の 7d20b2c1f (= 4258b0c76 の実装 + F5、main の取り込みを含まない。4258b0c76 との差は test helper 4 行だけ)。L1〜L4 は対 1 (out3/p1) と対 2 (out4/p1r) で判定する。変異: F5 は変異の置換元 (conftest.py と `_t080_stub_free_e2e_repo`) に触れないので、置換元の一意性を新 tip (c9af2b562) で静的に再確認し、helper を経由して kill する M2 だけを新 tip で取り直す。
- E7 (M6 の期待集合の再登録): final-c (静的導出の期待 = T7 + returns_independent) は MISMATCH で、観測は 3 node (期待 2 + `test_t080_shared_base_separates_active_v2_and_reuses_legacy_identity`、複製をやめると同じ inode を返すことを検出する既存 test)。DW-M08 に従い final-c を初回 probe と明記し、期待を観測 3 node に再登録して final-c2 を同じ clone で走らせる。
- E5 (M5 の再照準): probe2 で M5 (起動を無条件にする) は実 session の configure_node で可視 output job 不在の例外を起こし pytest 全体が rc=3 になり、node 単位の赤にならなかった (単一理由性不成立)。M5′ = 可視 output job があるときだけ分岐外で起動する形に替え、期待 = T5。
- E4 (変異の再登録): M3 = `_start_t080_shared_base_prewarm` で `_T080SharedBases` 生成直後に controller の lifetime lock を `LOCK_UN` で外す (参加だけを外す)、期待 = T3。M5 = 起動行を `_early_memo_selected` 分岐の外 (無条件) へ移す、期待 = T5 ∪ probe で観測した「非選択 configure_node」test 群 (例: test_acceptance_schedule_order の configure_node 系)。M6 = 複製をやめ base_root を返す、期待 = T7 ∪ `test_t080_shared_base_returns_independent_repos_and_documents` ∪ probe で観測した copy 独立性 test。M1 → T1、M2 → T2、M4 → T4 は据え置き。いずれも fix 後の最終 commit で dispatch probe により観測 node を集め、期待集合を確定してから final を走らせる。
