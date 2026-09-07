---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t1799-post-oracle-regen-ban
seq: 1
title: [T-1799] oracle 判定後の材料再生成を禁止した — 検査した木と build する木を build 前に一致させ、その木だけを build 中に書込み不能にする (コード + テスト、branch worktree-dev-wave-t1799-post-oracle-regen-ban、変異 matrix = baseline PASSED・KILLED 5・SURVIVED 0・MISMATCH 0・期待 node 完全一致 5/5)
---

## 本文

D984 の最小形を実装した。設計判断は {{D:post-oracle-regen-ban-narrow-protection}}、
実施記録と逐語は `output/insights/2026-09-08_t1799-post-oracle-regen-ban/`。

- **D953 が塞いだのは判定後の「再取得」であって「再生成」ではなかった。** D953 自身が
  「実効的な排他は process 間 lock を要し、書込み権威の変更として別審査に属する」と書いており、
  D984 がその別審査にあたる。前後の hash 照合は**検出**であって禁止ではない —
  判定済み材料が同一 bytes で作り直されると、manifest・`config.h`・archive・HEAD の照合は
  すべて同じ値を見るため通ってしまう。
- **段 3 の 2 レンズが親の brief の成果物影響を独立に反証した。** brief は
  「A-2 / A-6 の certification が材料の同一性を主張できるようになる」と書いたが、
  A-2 / A-6 は別 driver で generic `run_campaign()` を通り post-oracle binding を渡さない。
  本変更が直接改善するのは **S8b floor の `sort_best` cell の proof chain** である。
  brief は確定裁定の一覧から D954 も落としていた。
- **段 3 が段 2 案の中心を差し戻した。** 段 2 は既存の汎用 tree 保護 primitive の as-is 再利用を
  提案したが、同関数は対象の親 (= `FETCHCONTENT_BASE_DIR` そのもの) まで凍結し、
  `<base>` 直下への新規 entry 作成を巻き添えで壊す ({{F:reused-tree-primitive-freezes-parent}})。
  段 2 の「configure 後に読んだ実効根を後段でも再利用する」も、build 後の root drift 検査を
  実質的に消して受理を広げるため撤回した (絶対規律 2)。
- **段 6 のレビュー B が、親が段 4 で「限界として明記」と裁定した項目を must-fix へ格上げさせた。**
  同じ根への二重保護は、一時的な保護 gap だけでなく**最終状態の破壊** (根が恒久的に読取専用)
  を伴う。親の裁定は gap しか見ていなかった。official floor は cell を逐次 build するので
  この交差は届かないが、本変更が自ら持ち込んだ破れなので直した
  ({{F:self-inflicted-shared-state-poison}})。直し方は「保護に入る時点で根 directory 自身が
  書込み可能であることを要求する」の 1 条件だけで、process 間 lock は作っていない。
- **段 6 のレビュー A が、事前登録した変異 1 件の単一理由性を実測で否定した。**
  「書込み不能化の呼出しを no-op にする」変異は、同じ関数の**内側**にある write bit 残存検査に
  `yield` の前で先取りされ、狙った同一 bytes 再書込みまで到達しない
  ({{F:mutation-preempted-by-inner-guard}})。「保護後検査を通過した直後、`yield` の直前に
  復元を挿入する」形へ再照準し、KILLED を実測した。
- **実測 2 件。** (1) この platform で `os.chmod in os.supports_follow_symlinks` は `False` で、
  regular file と directory の `chmod(follow_symlinks=False)` は成功するが symlink だけ
  `NotImplementedError` になる。したがって tree 内に symlink があれば機構全体が fail-closed する。
  (2) 実物の masstree source tree は 2 か所とも 144 node・symlink 0 件だった。
  過剰拒否は実材料では発火しない。
- **protected な実 CMake build は本 wave で実走していない。** 段 2 が正例の根拠に挙げた
  real material test は build を fake に差し替えており、段 6 レビュー A がこれを指摘した。
  根拠は静的機序と保存済みの非 protected build log の正例である。
- 開示する限界: 同一 uid の協調的 process に対する discretionary-mode 保護であること、
  強制終了で復元が走らないこと、復元失敗が本来の build 例外を最上位から置き換えること、
  読取専用 mount・別 owner の node・symlink を含む根を新たに拒否すること。
  いずれも insight README に書いた。

## 次の一手差分

### 完了

- [T-1799] oracle 判定後の材料再生成を禁止した。実効 build 根を build 前に判定根へ固定し、
  その根と配下だけを `cmake --build` の間だけ書込み不能にする。
  remaining: none
  base: 894883faa5107fc3519df2c57c09742036703001de28433e85e0881af3fe2401
