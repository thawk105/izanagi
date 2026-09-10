---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-11
wave: dev-wave-t2563-calibration-runtime
seq: 1
title: T-2563の実時間を分解し、3コピー並行化の短縮効果を示せず候補を全撤回した
---

## 本文

- 要求時間増加を既定解にする方針を、今回のユーザー指示により変更した。裁定は
  {{D:calibration-runtime-no-adoption}}。要求時間・timeout・標本数を変えていない。
- 既存302秒の成功例と、上限式6610/6910/7870秒を区別した。旧copy85秒・検証22秒は
  login→NFSの実測でありcompute jobへ流用しなかった。復元不能な工程時間は未確定のまま示した。
- 親のgflags「未使用重複」仮説は、指定pinのtarget自動選択バグを独立planが発見して撤回した。
  gflags/glogのライブラリ選択変更は混ぜず、3copyだけの並行化をD95 authorが実装した。
- 同じ環境契約・workload・threads・toolchainでbefore/afterを各1回だけ実走し、両方accepted。
  scheduler186→182秒だが、未変更工程ですでに3秒差、copy周辺は両方約1秒。別ノード1対のため
  短縮効果を帰属できず、ユーザー指定どおりcode/testをD95 authorが全撤回した。
- 起動待ちは7→525秒で、job実行時間とは別に記録した。追加測定はしていない。
- 最小実行構成と費用は `output/insights/2026-09-11/t2563-calibration-runtime/README.md`。
  19標本のextime合計57秒とcooldown最低60秒を、build等の費用から分離した。
- 候補の親焦点走は74passedと69passed、consumer/metaは2passed。最終実装面差分ゼロなので
  DW-S04の変異免除を適用し、変異killや短縮効果の実証とは報告しない。
- 復元後の関連2fileは139passed/13.20秒、runner rc=0。文書/Codex設定検査・spool dry-runもrc=0。
- 独立reviewのsignal回収所見は制御フロー差として認めたが、非0終了後に較正やaccepted出力へ
  到達しないため、DW-G05とユーザーscopeにより仮想防壁の追加をmust-fixにしなかった。
  最終的に並行化候補自体を撤回している。
- T-2515の回収済み差分とT-2518のdocs-only所有を照合し、他waveのcode所有を上書きしていない。
  T-2564・較正対象拡大・改善実装・次wave・pushは行っていない。

## 次の一手差分

### 更新

- [T-2563] **P2・時間式再凍結は未完**: 実時間短縮を検討し、3copy並行化を1対比較したが
  効果帰属不能で全撤回。既存mocc/rr50/t48の実行可能な構成は186秒で認定成功。
  D1936項38の要求枠増加を既定解とする方針は今回ユーザー指示で変更。
  要求時間・timeout・標本数を維持し、既存最大経路の不整合を完了扱いにしない。
  正本 = `output/insights/2026-09-11/t2563-calibration-runtime/README.md`。
  base: 28d8aee28304956a893abc12740da5dcf04ad022a225d916bf54437ffeb723c5
