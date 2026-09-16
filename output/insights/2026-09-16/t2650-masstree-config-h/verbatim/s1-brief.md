# 段 1 brief — [T-2650] condition gate へ masstree の config.h を供給する

**研究前進:** official 床値 campaign が 3 走行とも cell build 段で止まり、論文の床値主張に要る
「試行台帳側 gate の実値域」が 1 件も取れていない。止めている実測 = official 床値走行、
最小差分 = condition gate の cmake configure へ offline define を渡す配線 1 本。
完了判定 = supply arm が `preprocess-failed` を出さず cell build 段を越えること。

**確定済みユーザー裁定:** Codex author = D95。本題の供給実装だけ。仮想リスク向けの gate・検査・
台帳・一般化の追加は scope 外。規律 2 を緩めない。[T-1851] 着地済みにつき local main から fresh。

**根本原因 (一次資料で確定):**
1. `external/ccbench/cmake/ThirdParty.cmake:57-78` — masstree の `config.h` は `add_custom_command`
   の OUTPUT で **build 時生成物**。同 85 行が masstree source dir を include path へ足す。
2. `orchestrator/campaign/condition_meaning_gate.py:1868` — gate は使い捨て build dir へ configure
   だけ行い、同 2210 行〜で owner TU を **前処理する**。build は一切しない。
3. `orchestrator/campaign/s8b_floor_campaign.py:3426` — 床値 campaign は
   `buildcache.prepare_masstree_fetchcontent` で masstree を **既に prebuild している**。
4. 同 4332-4358 の `floor_prepare` は `prepare_cell` へ `condition_configure_args` を渡さない。
   既定は `()` (`s1_direct_comparison.py:836`) なので gate の configure は prebuild を見ない。
5. 先例: `p3_s4_loop.py:346` の `_condition_gate_offline_configure_args` が同じ定義群を組み立て
   同 1919 行で gate へ渡す。`test_p3_s4_loop.py:8296` が「gate argv の offline token 集合 ==
   campaign build argv の同集合、ちょうど 5 本」を pin 済み。D1495 が本欠陥を未解決として記録。

**scope (DW-G05):** 放置すると床値 campaign は 1 cell も build できず、certified 選択の床値と
材料レポートの floor 欄が空のまま。scope = prebuild が使った `fetchcontent_base_dir` と 3 依存の
staged source dir (および `dependency_prefix` があればそれ) を `prepare_cell` へ渡す配線と、
その一致を pin する test。それ以外を足さない。

**(P1) 親の provisional 裁定 — 段 3 の攻撃対象:**
- (P1-a) 5 定義の生成は先例 `p3_s4_loop` の形を再利用してよく、新規の一般化ではない。
- (P1-b) D424 の「base 注入は `sort_best` に限定」は **cell build** への注入の射程であり、
  gate の使い捨て configure には及ばない。非 sort cell の cache identity と binary 参照は不変。
- (P1-c) 本変更は repo 内の凍結 bytes を変えない (`DW-O09`)。gate argv は `FROZEN_MANIFEST`
  (`test_frozen_artifacts.py:41`) に無く、記録側の構造検査 (`condition_meaning_gate.py:3718-3726`
  の argv[1]=="-S"・argv[2] 比較) は末尾追加で不変。
- (P1-d) 生死確認は既存実測を継承する。login node に gflags/glog が無く
  (`external/ccbench/CMakeLists.txt:33-34` が `REQUIRED`)、実 CMake 再現には [T-548] 面の
  gflags/glog build が要る。実機の床値再投入は本 wave の scope 外。

**不変条件:** gate の受理集合を広げない。red の判定式と reason code を変えない。gate に build を
肩代わりさせない (prebuild は campaign 側の既存段のまま)。`tools/pegasus/*.sh` を編集面に入れない
([T-548] が同時走行中)。新しい `cmake --build` 起動点を足すなら `materializer_admission.py` の
登録簿へ入れる (`test_s8b_floor_campaign.py:7793`)。既存 test を消さない・緩めない。

**変更面 (実アンカー):**
| file | anchor | 予定 |
|---|---|---|
| `orchestrator/campaign/s8b_floor_campaign.py` | 3395-3426、4332-4358 | prebuild が使った base と 3 source dir を binding で持ち回し `prepare_cell` へ渡す |
| `orchestrator/tests/test_s8b_floor_campaign.py` | 新規 test 関数 | gate の configure argv の offline token が prebuild の値と一致することを pin |

**成果物:** 上記 2 file の差分、変異 matrix、worklog / insights / decisions の spool fragment。

**並列分割:** 段 2 plan 1 本。段 3 敵対 2 レンズ (A: 凍結・受理集合・規律 2、B: 実行環境と D424
射程・先例との差)。段 5 実装子 1 本 (所有 = 上記 2 file)。

**受入・実測環境:** 受入全走は login node で `tools/dev_wave_wait.py acceptance`。
