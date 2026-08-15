---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t402-flock-exechost
seq: 2
---

## {{D:qstat-grammar-mismatch}}. cross-node flock を確定できなかった原因は controller の実行時欠陥ではなく qstat parser の文法不一致である

**決定 (1): 旧 parser はこの scheduler の実出力に対して常に空を返していた。**
実際の `qstat -J -f` は `Request ID: <id>` 行のあとに `Batch Job Number = <n>` と
**単数形** `Execution Host = <host>` を出す。旧 `_execution_hosts` は見出し行
`Execution Hosts(JSVNO):` に fullmatch を要求し、さらに `=` を含む行で走査を打ち切っていた。
この見出し語は保存 evidence 全体で**出現 0 件**である。

**決定 (2): 決定打は「健全な走行でも空だった」ことである。** 2026-08-04 の request 887918 は
完走して authoritative と判定された attempt であり、`Execution Host = bnode023` を含む
qstat raw を繰り返し保存している。それでも `monitor.execution_hosts_raw_order` は `[]`、
`execution_hosts_raw_evidence` は `null` だった。2026-08-03 の flock attempt の保存 raw は
`rbudgetcheck` / `qsub` / `qwait` の 3 command だけで、**qstat には一度も到達していない**。
したがって同 attempt の空 host は「controller が NameError で落ちた」ことの帰結ではない。
**parser を直さない限り、素の再走は何度でも `dangerous: null` に終わっていた。**

**決定 (3): 実出力は位置順 list より強い束縛を与える。** `Request ID:` block ごとに
job number と host が対になるので、`{job_number: host}` の閉じた写像が直接得られる。
これは `one_to_one_job_number_host_binding` が本来必要としていた情報そのものである。
parser は「対象 request の block がちょうど 2 件・各 block に job number と host が各 1 件・
job number 集合が `{0,1}`・host が相異なる」を要求し、満たさなければ空写像を返す。
**canonical な非インデント header として parse できない `Request ID` 行は、
インデントの有無に依らず拒否する** (別名の有限列挙に依存しない)。

**決定 (4): 最終判定は authority へ束縛し、危険側は保持する。**
`A ∧ H ∧ S ∧ E ∧ B` が全成立したときだけ `dangerous: false`、
`A ∧ H ∧ S ∧ (¬E ∨ ¬B)` で `true`、`A`・`H`・`S` のいずれかが不成立なら `null`。
`E` (localflock 不在) と `B` (raw outcome が各 6 件・全件 BLOCKED) は危険側の条件であり、
不成立を `null` へ畳まない。`B` は producer の派生 field ではなく controller が raw から
再導出する。`attempt_safe` は authority 連言へ加えない (D161 の証拠 3 分離を維持し、
危険側の観測も authoritative になれる性質を守る)。

**決定 (5): 2 job 構成の実出力が未知のままでも、受理集合は広げない。**
手元には 1 job の実出力しか無く、2 block grammar は外挿である。過剰拒否を避けようとして
「1 block に 2 組」を受理する案を一度採ったが、これは (i) 凍結済み事前登録の `H`
(「対象 block がちょうど 2 件」) に反し、(ii) job number 列と host 列を出現順に zip するだけで
2 block 形式と同等の束縛を持たない。**撤回して凍結形へ戻した。**
過剰拒否で `null` に終わっても、**実物の 2 job raw が証拠として保存される**ため
次の判断材料になる。安全側へ倒すよりこちらを採る。

**理由:**
- 規律 3 は「正しさシグナルを後付けにしない」ことを求める。照合未確定の入力が
  安全側の受理集合へ入る経路は、実測前に塞がなければならない。
- `DW-S01` は「模擬対象と実との差を明記し、自己 hash / 参照 / pin 対象では模擬を裁定根拠に
  しない」と定める。2 job grammar の外挿はまさにこの型である。

**却下した選択肢:**
- **素の再走を先に試す** — 決定 (2) により結果が事前に分かっており、request 枠と node-min を
  捨てるだけである。
- **`Request ID` の別名を列挙して拒否する** — `RequestID:` / `Request Identifier:` /
  `Req ID:` を塞いでも、**インデントした同じ境界**で同型の抜け道が残ることを敵対レビューが
  実証した。構造規則 (非インデント行は canonical header 以外を拒否) へ置き換えた。
- **1 block 2 組を受理して過剰拒否を避ける** — 決定 (5) のとおり撤回した。
