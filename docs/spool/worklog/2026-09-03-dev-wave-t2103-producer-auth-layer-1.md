---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-03
wave: dev-wave-t2103-producer-auth-layer
seq: 1
title: 凍結 closure 外 raw-record producer の認証層を比較実験で決めた (コード + 実測、branch worktree-dev-wave-t2103-producer-auth-layer)
---

## 本文

D1345 が求めた比較実験を実施した。候補 3 層 (issuer / raw assembly / frozen consumer) へ
同一の変異集合を当て、拒否能力を数字で出した。結論は {{D:producer-auth-layer-not-the-frozen-closure}}。
一次資料は `output/insights/2026-09-03_t2103-producer-auth-layer/`。

- **事前期待が実測で覆った。** 段 2 plan の事前期待は issuer 3/12、raw 9/12、frozen 6/12 だったが、
  実測は issuer 0/6、raw 3/6、frozen 3/6 で **raw と frozen は同点**であった。
  差の主因は R 系の帰属である。plan は既存 `evidence_binding:source_rederivation` gate の拒否を
  候補の能力として数えていた。baseline と prototype の両方を測った結果、
  R 系は両 phase で観測が完全一致し、増分ゼロであることが data に出た。
- **段 6 の敵対レビュー 2 本が、初版の測定機構が実際には測っていないことを独立に指摘した。**
  raw の probe が認証不一致以外の拒否を潰していたため、attempt artifact を作らずに assembly を
  呼んだ結果の既存拒否が「受理」と読まれ、raw の増分 3 件が偽陽性になっていた。
  他に baseline の合成、prereg の自己生成 (D1531 違反)、欠測のまま勝者を出せる点、
  scratch 不可時に skip して測定ゼロで緑になる点を指摘した。計 15 件を fix で閉じた。
- **親の裁定が 1 度誤り、追補で撤回した。** 実行時間が 1 時間枠を超えたため fixture を
  最小 block 数へ縮小するよう指示したが、`p3_b4_analysis_ledgers.py:1158` が
  `design_not_feasible: fewer than 201 eligible registry rows` を投げるため、
  201 は事前登録された設計の下限であって調整値ではなかった。追補 2 で撤回し、
  縮小でなく候補 x phase の 6 shard 分割で解いた。
- **測定の過程で、より重い事実が出た。** B-4 の production 分析経路は現時点でいかなる入力に対しても
  有効な分析を返さない ({{D:b4-production-analysis-path-returns-no-valid-analysis}})。
  併せて closure receipt に production の呼び手が存在しないことも実測した。
- 実装面は Codex `role=author` が 4 巡で書いた。うち fix 第 2・3 巡は親の誤指示とその撤回に
  費やしたものであり、子が所見を閉じ損ねた巡ではない。
- fix 第 1 巡は前セッションの終了で子ごと落ちた。1026 行の未検証差分が残っていたため採用せず、
  job dir へ `s6-fix1b-partial-UNATTESTED.patch` として保全したうえで worktree を統合 commit へ戻し、
  job-id を変えて投入し直した。
- **実測 (親が実走した値)。** 焦点走は fix 前 4 failed / 24 passed (238.92s)、
  fix 後 **47 passed / 44.05s**。重い測定を pytest から harness へ移したことで、
  2 時間超だった走行が 44 秒に収まり 5 分予算を満たした。
  6 shard は候補 x phase で並列実行し全て rc=0、`combine` も rc=0。
  候補別の既存 producer test 29 node は 3 候補とも緑 (28.7-29.6 秒)。
- **測定機構自身の変異検査 (DW-M01)。** W01-W09 を事前登録し、W01-W08 は適用可能な exact mutant を
  持つ。`test_wave_mutant_kills_exactly_one_registered_node[w01..w08]` が各 mutant がちょうど 1 つの
  登録 node を殺すことを実測しており、8 件とも焦点走に含まれて緑である。W09 は正例で mutant を持たない。
- 主 worktree の bytes は測定中も一度も変わっていない。候補の一時差分は repo 外 scratch の
  使い捨て tree の中だけに存在させた。5-file pin の恒久変更は行っていない。

## 次の一手差分

### 完了

- [T-2103] D1345 の比較実験を完了した。拒否能力は raw assembly と closure 拡張で同一 (ともに 3/6、
  同じ case 集合) であり、差は変更閉包だけであった。closure 拡張は最小ではないため採らない。
  認証層の本採用実装は行っていない。
  remaining: none
  base: d611c97c1ebddcadce749dc026d81fd79378acd1f3a46f958269eeaf8a5abff1

### 新規

- {{T:b4-post-assembly-authenticity}} **P2・新規**: D 系 (assembly 後に raw analysis の判断値だけを
  書き換える形) は候補 3 層すべてが素通しする共通の穴である。raw judgment と source object の
  judgment を相互照合する下流の payload-binding 層を設計するか、非保証として確定するかを決める。
- {{T:b4-authoritative-floor-artifact}} **P2・新規**: B-4 の production 分析経路は
  `floor=None` を渡すため、いかなる入力でも `floor_domain_error` を返す。権威ある floor 成果物の
  発行と配線を、D1530 に従い実 producer の接続と同じ変更単位で行う。
- {{T:b4-closure-receipt-production-caller}} **P3・新規**: closure receipt を production 経路へ
  接続する呼び手が存在しない。frozen 候補を将来採るなら前提になる。単独では建てない (D1530)。
