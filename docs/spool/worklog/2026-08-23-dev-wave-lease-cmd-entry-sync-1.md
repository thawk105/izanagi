---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-lease-cmd-entry-sync
seq: 1
title: dev-wave commandの段6lease claim待ち文言をD662/DW-O27へ整合させ受入lease直列化ボトルネックの再発を防ぐ (コード+テスト、branch worktree-dev-wave-lease-cmd-entry-sync)
---

## 本文

- ユーザー依頼: 「今日lease直列化で研究開発が著しく遅滞した。再発しないよう改善せよ。並行
  セッションと通信すると学びがあるかも」。ListAgentsで51並行セッションを確認し、関連しそうな
  3セッションへSendMessageで直接照会した。
- 「acceptance lease staleness quantification」(T-1469) から実測データ (claim待ち中央値42分・
  最大74分、当夜は11wave同時待機・最古48分待ち、後に自分のfork調査では9wave・最古2時間超も観測)
  を得た。「orphan-hold race conditions」は対象が別機構 (PBS dispatch側のhold) と確認し無関係
  だった。「t-1458 admission registry orchestration」(T-1458) が本丸対応
  (`tools/dev_wave_wait.py acceptance`への`--lease-optional`実装、`docs/dev-wave/operations.md`
  へのDW-O27新設) を進行中で、15回以上の受入投入に難航していると判明。重複回避のため直接連絡し
  scopeを分担した (相手のcommit 0c89ec77, 25614f86)。
- T-1458のcommitは条件dispatch表 行18だけを更新しており、`.claude/commands/dev-wave.md`の
  9段状態機械 項6本文自体 (常時読まれる箇所、条件dispatch表とは別位置) は旧文言のまま残って
  いると発見した。T-1458へ確認し、この箇所は相手のscope外・本waveが引き取ることで合意した。
- 項6書き換えを試みたところ `tools/check_docs.py` の `_check_dev_wave_waiter_consumer_pins` が
  この文言をbyte-exactにpinしており ([T-773]/[T-786]、2026-08-11導入、commit
  c7cc0fd1/d32a072c)、F153 (受入コマンドへの余分な引数混入が事前検査を黙って無効化する) の
  再発防止も兼ねる設計だと判明した。単純なdocs修正では済まないと判断し、段2 codex plan・
  段3敵対相談2本 (F153保存レンズ、scope境界レンズ)・段4裁定・段5実装 (Codex role=author、
  `tools/check_docs.py`+`orchestrator/tests/test_check_docs.py`)・段6敵対レビュー2本、という
  正規の重い経路で進めた。
- 段3敵対相談で `docs/pegasus-runbook.md` (958-1129行目付近5箇所) にも同種の矛盾文言が広範囲に
  存在すると新たに判明したが、958-961行目だけの修正では他4箇所との不整合が残るため本wave
  scope外とし、follow-upを{{D:pegasus-runbook-lease-optional-followup}}へ送った。
- 段6敵対レビューで、既存checkerの構造的な弱点 (disclaimer regexが英語語彙を検出しない、H2内へ
  正規文言を重複配置するとpinを回避できる) を実演付きで確認した。今回のD662対応が生んだ
  regressionではないが、audit-foundの既存防壁の破れとして{{F:waiter-consumer-pin-hardening-gap}}
  へ記録した。
- 段4裁定で「項9 (`release`) の文言は不変」と判断したが、根拠 (T-1458の設計上unclaimedでも
  安全) は伝聞のみで未検証と段3敵対相談レンズAが指摘した。T-1458 main着地後に実装を読んで
  確認することを自分の受入投入・land前提条件とした (本wave内で解決予定、次の一手には送らない)。
- commit `e6b2c0ed`。`tools/check_docs.py` rc=0、`orchestrator/tests/test_check_docs.py`
  504 passed/3 skipped (計算ノードdispatch、既知GROWTH_HOLD3件)。`python3
  tools/check_ai_provenance.py` (full-history) rc=0、新規違反なし。MUT-1
  (定数から`--lease-optional`削除)・MUT-2 (`decoy-lease-optional-omitted`のregistration除去)
  をDW-O19の一時変異手順で検証し、いずれも単独理由でKILL、`git checkout --`で復元し
  HEAD一致を確認した。
- T-1458のmain着地待ち (自分の受入投入・段9 landの前提条件)。着地通知はT-1458からもらう
  取り決め。着地後、main取り込み→項9 P1検証→`--lease-optional`込みで自分の受入全走→land。
- **回収 wave による補記 (2026-08-23)。** 本 branch は受入前に取り残され、main が 303 commit
  進んだ後に別セッションが回収した。回収時の独立監査 (read-only Codex) は、実装 3 file の是正が
  main へ未着地でいまも必要である一方、記録側の follow-up (runbook 全面改訂) が main 側
  commit `c5e81e0c` で完了済みであることを実測した。そのまま fold すると完了済みの作業が
  新規採番されるため、{{D:pegasus-runbook-lease-optional-followup}}の結論を現況へ改め、
  対応する新規タスクを取り下げた。
- 回収時に main を取り込んだところ、受入全走が 1 件だけ赤になった
  (`test_dev_wave_command_budget_literal_is_exact`、14,639 passed / 1 failed)。本 wave が項 6 を
  3 行から 1 行へ縮めた結果、入口が 9,584 byte から 9,520 byte になり、取り残し中に main 側 D704 が
  引き上げたばかりの予算と食い違った。Codex `role=author` が pin 5 箇所を現物へ揃え、
  焦点走 `orchestrator/tests/test_check_docs.py` は 511 passed / 3 skipped で緑。
  追加の変異 2 件 (M1: 予算を 9_584 へ戻す、M2: 予算を 9_521 へ) はいずれも単独理由で KILLED。

## 次の一手差分

### 新規

- {{T:waiter-consumer-pin-hardening}} **P3**: `tools/check_docs.py`の
  `DEV_WAVE_WAITER_DISCLAIMER_RE`が英語語彙 (optional/manual/do not use等) を検出しない件と、
  H2内へ正規文言を重複配置すると`_check_dev_wave_waiter_consumer_pins`のpinを回避できる
  構造的な穴 (段6レビューで実演確認済み) を修正する。checker設計そのものの改修のため
  専用waveで行う。既存9件のnegative controlを壊さない設計を段2 codex planから起こす。
