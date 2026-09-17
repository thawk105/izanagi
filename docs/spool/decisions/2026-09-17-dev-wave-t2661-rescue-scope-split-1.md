---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2661-rescue-scope-split
seq: 1
---

## {{D:audit-offrepo-scan-mode-split}}. 到達不能監査の repo 外走査は掃除で明示 off、救出 triage で明示 full とし、掃除の 2 入口と rescue gate の子 process 環境を固定する

**決定:** `tools/audit_dangling_commits.py` に明示 mode `--offrepo-scan {off,full}` を置き (D2120 項 24 の実装)、
次を契約とする。

1. **掃除の規範入口は 2 箇所で、どちらも off。** `/cleanup-branches` §1 の単独実行は
   `python3 tools/audit_dangling_commits.py --offrepo-scan off`。`tools/check_branch_rescue.py --ledger-check` が
   起動する監査の子 process は argv に `--offrepo-scan off` を持ち、子 process 環境の allowlist から
   `IZANAGI_DEV_WAVE_JOBS_DIR` を外す (argv と環境の二重防壁。片方が退行しても走査は復活しない)。
   JSON の `ledger.audit.offrepo_scan` は `"off"` を示す (起動方針であり完走の証明ではない。完走は `complete`)。
2. **off は repo 外の同一実体を確認しない。** 探索根の検証・blob metadata・repo 外走査・cat-file のいずれにも
   触れず、core snapshot の findings をそのまま返す (抑止 0、`findings(full) ⊆ findings(off)` を同一 snapshot の
   (commit, path) 対で保証)。CLI の探索根と併用したら usage error (rc 2)、環境変数の探索根は無視し、その旨を
   専用の開示行に出す。開示行は「探索を未実施」「未指定」と別の文字列にし、「全走査して一致無し」と読める表示を
   しない。
3. **救出 triage は明示 full を単独実行する。** 探索根が CLI にも環境変数にも無ければ実行不能 (rc 2) で、
   黙って未実施にはならない。full の受理・抑止規則 (D247 の 5 条件) は変えない。
4. **flag 省略は互換経路として残す** (CLI の探索根が環境変数を上書き、どちらも無ければ未実施を開示)。
   固定するのは掃除の規範入口であり、任意の ad-hoc 実行の機械封鎖ではない。
5. **台帳への影響を開示する。** off では従来 full で抑止されていた (commit, path) 対も要確認に含まれうるため、
   `unledgered-audit-finding` が増え rescue gate の rc が 0 から 3 に変わりうる。追記候補集合は off で増える。
   通知された object の追記と状態遷移は既存の台帳契約 (追記対象、新規 `pending`) にそのまま従い、full の
   抑止行は §5 の報告と当該 entry の `resolution_note` の判断材料に残す。台帳 entry を免除する新しい運用例外・
   通知 kind・field は作らない。
6. **D970 / D1031 は当時の 28 件と追加 19 件についての裁定**であり、repo 外に控えがあれば新規 commit を
   破棄してよいという一般許可ではない。破棄の可否は対象 commit ごとの裁定に従う。

**理由:**
- 第 1 段 (並列化、D2115〜D2117) の後も走査強制 fixture の warm 6 走 max は 335.8 秒で所要上限 300 秒 (D958)
  を超え、掃除の `checker-timeout` の原因が残っていた。掃除の判断に要るのは「到達不能で未 land の変更が
  あるか」であり、repo 外の同一実体による抑止は救出 triage の判断材料である。用途で分ければ掃除は走査を
  要さず、findings は減らない (規律 2 を緩めない)。
- 段 1 の実測 (現行 tool、fixture): 親 env に探索根があると rescue gate の子 process が走査して抑止し rc 0、
  無ければ rc 3 + 通知 1 件。環境の継承だけで掃除の結果が変わる経路 (起票の二重走査) を argv と環境の両方で
  塞いだ。
- 「台帳 entry 不要」の文案は台帳 doc の追記契約 (`unledgered-audit-finding` を出した object も追記対象) と
  矛盾する (段 3 レンズ A の must-fix)。追記候補集合の増加は一次資料 §5 条件 3 が予期した通知の増加そのもの
  であり、免除ではなく開示で扱う。

**却下した選択肢:**
- **flag の必須化 (省略を拒否)** — 互換契約 (CLI 優先・環境既定・未指定の開示) を壊し、既存の CLI 例と test
  を全部変える。掃除の規範入口 2 箇所を固定すれば目的は足りる。
- **rescue gate の子で full を維持し、掃除の単独実行だけ off** — 子が走査すれば掃除 1 回で走査が残り、
  環境の継承だけで結果が変わる経路が残る。
- **full で全対が抑止された commit の台帳 entry を免除する** — 既存の追記契約と矛盾し、新しい運用例外の
  新設になる (scope 外)。
- **通知 kind・台帳 field の追加** — 追加の gate・台帳は依頼で scope 外。

## {{D:audit-elapsed-acceptance-cleanup-entry}}. 用途分離 wave の所要受理は掃除入口 (off) の所要で判定し、full の所要は再判定も上限達成の主張もしない

**決定:** 到達不能監査を用途分離した本 wave の D958 項 1 の判定対象は、**掃除の規範入口 (`--offrepo-scan off`)
の所要**とし、実 repo と走査強制 fixture の両方で D958 の形 (warm-up 1 走を捨てた独立 3 走、max/min > 1.5 なら
3 走追加、全走の max) を取る。off は走査しないので D2116 の「走査を強制した所要」は取れない — 本決定は
D2116 を満たしたと記録するものではなく、本 wave の受理対象を掃除入口に限定する明示の判断である。
救出 triage の full は本 wave で変更せず、所要の再判定も上限達成の主張もしない (第 1 段の実測 max 335.8 秒
がそのまま残る)。D2117 の追補は流用しない。

**理由:**
- D958 の上限が守ろうとしているのは掃除の `checker-timeout` であり、掃除が呼ぶのは off の入口である。
- 段 3 の両レンズが「掃除入口だけを所要受理の対象にするのは D958 / D2116 の読替えでは導けず、本 wave の判断
  として結果を見る前に固定する必要がある」と指摘した (A2 / B1)。結果を見てから条件を替えないため、段 4 で固定した。

**却下した選択肢:**
- **full の 3 走で判定する** — 本 wave は full を変えておらず、超過は既知 (D2117)。掃除の入口が改善したかを
  測らない。
- **off の所要で D2116 を満たしたと記録する** — 走査を測っていないので過大申告になる。
