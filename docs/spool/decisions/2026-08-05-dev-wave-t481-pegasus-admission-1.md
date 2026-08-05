---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-05
wave: dev-wave-t481-pegasus-admission
seq: 1
---

## {{D:pegasus-admission-registry}}. [T-481] Pegasus 実行体の login 受理を三値 registry で決め、証拠のない昇格を禁じる

`hooks/guard_bash.py` が `tools/pegasus/` 配下を prefix 一致で一律に扱い、必要な entry を
1 件ずつ sanctioned 化していた運用をやめる。ユーザー裁定 (2026-08-05 /rulings、択 (b)) に従う
族再設計であり、D103 決定 5 の「`tools/pegasus/*` の glob 許可はしない」は維持する。

**決定 (1): admission は path ごとの三値とし、`local-ok` だけを許可する。**
registry は `path → {class, reason, primary_gate, evidence}` を持ち、class は
`local-ok` / `dispatch-required` / `unknown`。`unknown`・`dispatch-required`・未登録
(subdirectory を含む) はすべて拒否する。`_SANCTIONED_PATHS` は registry の `local-ok` から
導出し、二重表を作らない。判定に prefix を使うのは「pegasus 配下だが未登録」を拒否する側だけで、
許可側には使わない。

**決定 (2): 証拠状態を class と別 field に持ち、未実測を実測済みと読ませない。**
現在 `local-ok` の 5 本のうち `docs/pegasus-runbook.md` §7.0 の手順で実測されているのは
`fetch_third_party.py` だけである。残り 4 本 (`dispatch_compute.py` /
`submit_certify.sh` / `submit_floor.sh` / `submit_silo_ladder_rung1.sh`) は
`legacy-admitted (未実測)` と明記して現状を記録する。**これは実測の代替ではない** —
規範を厳格適用すれば現在通っている 4 本は落ちる。厳格化するか grandfather を追認するかは
ユーザー裁定に残す。

**決定 (3): 本 wave では許可へ反転させる entry を作らない。**
族の症状として起票された `collect_receipt.py` は、scheduler stderr の全読み・JSON 全読み・
`rglob` の全件 materialize を持ち、§7.0 が定める「入力サイズに上限が無い」= `unknown` に該当する。
実測なしに `local-ok` と記録することは防壁を緩める方向の変異であり、規律 2 に反する。
入力 cap ([T-482] 択 (c)) と cap 下の実測が揃うまで拒否のまま残す。

**決定 (4): 分類の測定はユーザー端末でしか行えないことを明示する。**
§7.0 の測定手順 (`systemd-run --user --scope` + `memory.current` sampling) は計算ノードで
成立しない (PBS ジョブに user systemd session が無い。2026-08-05 実測)。一方 hook は未登録の
実行体をログインノードで拒否する。したがって「登録には実測が要る / 実測には登録が要る」という
循環がある。迂回は禁止で、hook の管轄外であるユーザー端末が現行唯一の正規経路である。
恒久的な測定経路は裁定待ちとする。

**決定 (5): `-m <module>` の実行体は module であり、位置引数は原則データとする。**
例外は後続 script を実際に実行・import する module の閉集合
(`cProfile` / `profile` / `pdb` / `trace` / `runpy` / `coverage` / `pydoc` / `doctest` / `unittest`)
で、そこでは位置引数を実行対象として分類する。module identity は `pytest` / `pytest.__main__` /
`_pytest.main` を同一視する。これで [T-483] の sanctioned 借用が閉じる。

**決定 (6): 受理集合の変更は単調性で縛る。** 変更前に拒否していた綴りを許可へ変えず、
変更前に許可していた綴りも本決定が列挙した「意図した縮小」以外では拒否へ変えない。
段 6 で密着形 `-m py_compile <path>` を許可へ広げる案が出たが、単調性を優先して撤回した
(分離形は従来どおり許可なので静的検査は失われない)。

**却下:** `tools/pegasus/*` の glob 許可 (D103 決定 5 を維持)、hook が argv を検査する admission
([T-482] 択 (b)。hook から入力サイズは見えず偽の安心を作る)、`^#PBS` の有無による自動分類
(`dispatch_compute.py` が生成テンプレ内に同 directive を持ち誤判定する)、
未実測 entry の役割ベース昇格。

**研究状態への影響:** campaign の受理集合、certified 選択、proof chain、既存凍結 bytes は不変。
変わるのは開発 harness の Bash 面における Pegasus 実行体の受理集合だけである。
