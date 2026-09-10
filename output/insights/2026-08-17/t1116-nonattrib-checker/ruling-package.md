# [T-1116] 裁定パッケージ — ユーザーへ返す 4 択

wave `dev-wave-t1116-nonattrib-checker` / 2026-08-17 / base `7c83eeac`

全択の根拠と実測は同 directory の `README.md`、所見の裁定表は
`verbatim/s4-adjudication.md` にある。

---

## #1 [T-1116] を終端してよいか

**事実。** 択 (2) の「対象 wave より前から main に存在する entry を批准と見なす」は、
registry ではなく live probe (`main 単独再走が赤 → non-attributable`) として
**`8a2b735b` より前から実装済み**だった。裁定が明示受容した「AI による 2 wave 事前登録が残る」
リスクは、registry が存在しないため別形 (赤を main へ land させる) に変わっている。
併合された [T-1055]「registry 由来 nodeid を非帰属と区別して受領証へ書く」は**未達**である
(`red_nodeids` は由来を区別しない)。

- (a) 終端する — 残存リスクと [T-1055] を no-op とする理由を明記して閉じる。
- (b) 未終端のまま残し、#2 の裁定に従属させる。

**親の推奨は (b)。** #2 が決まるまで [T-1055] の可否が決まらない。

---

## #2 R2 を実効化するか

**事実。** 現在フレークが 1 件でもあると受入全走 1 本が丸ごと捨てられる。
ユーザー裁定 R2「確率的なフレークで受入全走を何度も無駄にする構造は全てのセッションに
対して許さない」は一度も発効していない。実効化には次が要る。

- `tools/dev_wave_wait.py` の node exact 検査、outer receipt schema、
  `tools/dev_wave_land.py` の verdict 受理、3 つの test file、
  runbook と D371 / D389 の契約文の**同時**改訂。
- **残余の明示受容** — production code / `conftest.py` / 共有 fixture / pytest plugin の
  いずれかだけを変更して作られた全走限定赤は、単独再走が両側緑になるため
  `flake` として通る。この経路は差分到達可能性の完全な写像がない限り閉じられない。

- (a) 残余を受容して実効化する。
- (b) fail-closed を維持し、R2 を「現行構造では実装不能」として撤回する。
- (c) 中間 — flake を通すが、`red_nodeids` とは**別集合**として受領証・land 結果・台帳へ記録し、
  land 後に人間が読める形で残す。

**親の推奨は (c)。** R2 の目的 (受入窓を捨てない) を果たしつつ、[T-1055] が求めた
「区別して書く」も同時に満たし、残余を台帳で追跡可能にできる。(a) は残余が台帳から見えなくなり、
(b) は受入窓を捨て続ける現状維持になる。

---

## #3 受入証拠の自己証明を塞ぐか (新規・重大)

**事実。** [T-1131] は checker だけを tested main へ束縛した。
`tools/dev_wave_wait.py` は running bytes と **tip** blob の一致しか検査されず、
`tools/run_tests.py` は tip での存在しか検査されない。
したがって wave は待ち手または runner を書き換えるだけで、実 child rc=1 を
`child_rc=0 / verdict=child-green` として land できる。
[T-1131] が塞いだ穴と同型が、隣接 2 層で開いたままである。

- (a) 待ち手と runner も main 側 blob と照合する。
- (b) tested main 固定の外側 launcher を別途設ける。
- (c) 現状維持。

**親の推奨は (a)。** 代償 (これらを直す wave は次 wave からしか効かない) は
[T-1131] で既に受容済みの型であり、新しい機構を足す (b) より安い。

---

## #4 待ち手の rc 値 pin (小)

**事実。** `non-attributable` node の `rerun_rc` は構成上必ず 1 になるが、
`tools/dev_wave_wait.py:2803-2812` は `type(rerun_rc) is int` しか検査しないため、
0 / 2 / -1 でも通る。純粋な縮小で安全だが、#3 が開いている間は防御深度に留まる。

- (a) #3 と同じ wave で直す。
- (b) 単独起票する。

**親の推奨は (a)。**
