---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-29
wave: dev-wave-t1629-rescue-discard
seq: 2
---

## {{D:ratification-rescue-discard}}. 批准機構の救出候補 7 file は全件破棄する

**決定:** 救出材料 `/work/1/SFC/tanab/dev-wave-jobs/rescue-20260829/` の t1629-u1 / u2 / u4 が
持つ untracked 7 file は、1 件も着地させず全件破棄する。worktree 3 本も畳む。
処遇と理由は file ごとに次のとおりである。

| file | 処遇 | 理由 |
|---|---|---|
| `orchestrator/campaign/ed25519_verify.py` | 破棄 | D1139 が機構を廃止済み。着地版が `c986c1459` で main から撤去され、main に consumer はゼロ。ed25519 検証は別機構 `orchestrator/campaign/mocc_trace_pair_anchor.py` が独自実装を持つため、着地させても孤立コードになる |
| `orchestrator/tests/test_ed25519_verify.py` | 破棄 | 被検査対象が破棄されるため |
| `orchestrator/campaign/enforcement_source_ratification_receipt.py` | 破棄 | D1139 が廃止した批准突き合わせの受領証そのもの。着地版が撤去済みで consumer ゼロ |
| `orchestrator/tests/test_enforcement_source_ratification_receipt.py` | 破棄 | 同上 |
| `orchestrator/campaign/enforcement-source-ratification-receipts.v2.jsonl` | 破棄 | 0 byte の空 file。7 件で唯一一度も着地していないが、内容が無いため救出する対象が存在しない |
| `tools/ratification_broker.py` | 破棄 | D1139 が「却下した選択肢」として名指しした「批准行の発行を署名 broker で機械化する」の実装そのもの |
| `orchestrator/tests/test_ratification_broker.py` | 破棄 | 同上 |

**理由:**

- D1139 (ユーザー裁定) が enforcement source closure の批准突き合わせを廃止し、D905 を明示的に
  上書きして「命じられた実行主体は今後も作らない」と定めた。同裁定の却下した選択肢は
  「批准行の発行を署名 broker で機械化する (D905 が命じ、別 wave が実装済み)」を名指しし、
  採らない理由を「ユーザーの逐語が不要としているのは blockage だけでなく束縛の粒度そのもの
  だから」と書いている。今回の救出候補はこの「別 wave が実装済み」の実体である。
  したがって着地は既裁定の否認になる。
- 7 file のうち 6 file は既に一度着地しており (`5107ced3c` / `abd3390af` / `647acd2d7`)、
  `c986c1459`「merge: main を取り込み、批准機構の撤去を 27 path 世界へ広げる」で撤去された。
  救出とは「失われた成果を取り戻す」操作だが、ここで取り戻す対象は**意図して撤去されたもの**である。
- worktree 内の untracked copy は着地版より前の段 5 author 草稿であり、着地版の部分集合的な
  前身にすぎない (broker 250 行 対 着地版 1039 行、受領証 474 行 対 1035 行、
  ed25519 138 行 対 144 行)。仮に機構が生きていたとしても、救出すべきは草稿ではなく
  main の履歴に恒久的に残る着地版である。
- 撤去による損失はゼロと実測した。削除損失閉包が commit 0 件・complete=true、
  3 worktree の HEAD `9463bcbcb` は main の祖先、untracked 7 file は
  `/work/1/SFC/tanab/dev-wave-jobs/rescue-20260829/` に sha256 一致で repo 外退避済みである。

**成果物影響:** 着地させた場合、廃止済み機構の実装 3 本と試験 4 本が main へ戻る。
これらは D1139 が撤去した批准経路の判定器と受領証であり、campaign 初期化の受理集合を
再び批准集合との照合に依存させる方向へ引き戻す。破棄はこの引き戻しを起こさない。

**却下した選択肢:**

- **`ed25519_verify.py` だけ汎用ライブラリとして救出する** — main の
  `mocc_trace_pair_anchor.py` が既に自前の ed25519 検証を持ち、新しい呼び手は無い。
  呼び手のいない検証子を足すのは、要求外の一般化を repo へ入れることになる。
- **worktree を残して判断を次 wave へ送る** — 破棄は既裁定の適用であって新しい設計判断ではない。
  残せば同じ調査を次の担当が繰り返し、その間 worktree 3 本 (計 1.1GB) が居座る。
- **着地履歴を確かめずに依頼の前提どおり「未着地」として扱う** — 前提は実測で誤りだった。
  誤った前提のまま救出すると、撤去済み機構の草稿版を main へ入れることになる。
