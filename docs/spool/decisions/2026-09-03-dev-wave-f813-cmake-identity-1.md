---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-03
wave: dev-wave-f813-cmake-identity
seq: 1
---

## {{D:cmake-identity-bound-to-green-record}}. 判定器が環境から解決した実体の identity は green record へ束縛する。ただし束縛は拒否ではない

**決定:** condition gate の green record は、gate が実行した CMake の実 path・内容 SHA-256・
stat identity・実行した configure argv を保存する。supply arm と、CMake を実行する
compile-time meaning proof の双方が対象で、schema は exact (欠落も余剰も reject) とする。
旧形式の record を受理する後方互換経路は作らない。

**同時に、この機構が何をしないかを正本として固定する。** identity を**記録すること**と、
未承認の実体を**拒否すること**は別である。本機構は後者をしない。安定した (自分を書き換えない)
CMake wrapper は、変更後も green を返す。拒否するには「承認済み CMake identity」の権威が要るが、
repo 内に存在しない。この限界は主張せず明記する (規律 7、D387)。

**受理集合が狭まるのは次の 4 つに限る。**

1. cmake 証拠を持たない旧形式の record。
2. 2 つの arm が異なる CMake 実体で作られた record。
3. 1 回の configure の前後で CMake 実体が入れ替わった走行。
4. configure argv が記録された cmake path に束縛されていない record。

**保存する argv は「この gate が実行した argv」であり、wrapper の内側 argv ではない。**
wrapper が委譲先へ渡した argv は観測していない。ただし wrapper が compile entry を
書き換えた効果は、既存の `requested_replay_argv` (compile_commands 由来) に現れる。

**理由:**

- F813 の恒久対応は「gate 側に wrapper hash と configure argv を束縛する変更が要る」と書き、
  同時に「機械的な検出器は無い」と明記していた。本決定は前者を実装し、後者の限界を保つ。
- 判定器が環境から実体を解決する設計では、PATH・環境変数・生成された入力が受理集合の一部である。
  実体が判定の証拠へ残らなければ、事後に certified の値がどのビルドから出たか言えない。
- 承認済み identity の権威を新設すると、登録簿・更新手順・機体差の扱いが必要になる。
  発火条件を満たす既存 artifact path も計測 ID も書けないため、設計メモに留める (DW-G04)。

**却下した選択肢:**

- **未承認の CMake を拒否する。** これが穴を実際に閉じる唯一の道だが、承認済み identity の
  権威が repo に無い。実装すれば「承認済み」の定義を wave が自分で決めることになる。
- **旧形式 record を受理し続ける互換経路を置く。** 受理集合を広げる。移行対象の
  historical record は現に存在せず、必要がない。
- **configure argv の位置を pin する** (`-S` / `-B` の添字、export flag の位置)。
  production 経路では常に真になり、受理集合を狭めない。手組み record に対しても
  `argv[0] == cmake_path` 以上の判別力を持たない。

## {{D:record-validator-is-the-acceptance-authority}}. condition gate の受理権威は record validator 一本とし、production 層の同型検査は診断として扱う

**決定:** condition gate の CMake identity 検査は 4 箇所にあるが、**受理権威は record validator
だけ**とする。production 層 (configure 直後の before/after 比較、supply の requested/control 比較、
configured-command validator、compile-time meaning の requested/default 比較) は、より早く固有の
reason code で落ちる**冗長 gate**であり、受理集合の決定はしていない。

変異検査では、単独変異の KILLED 期待を record validator の行へ登録する。production 層の単独変異は
受理集合を変えないため kill として数えず、diagnostic sensitivity pin として別枠に記録する。
冗長性の主張は両層同時変異の KILLED 期待で裏取りする。

**恒真だから消してよいという意味ではない。** fail-fast と診断の質のために残す。

**理由:**

- `_arm_record` は生成した record を `require_issuer=False` で validator へ通す。公開 field から
  手組みした record にも同じ validator が適用されるため、validator は production 経路を
  迂回した入力に対しても効く唯一の層である。
- production 層の単独変異は 3 層に mask され、赤理由が 1 つに絞れない。DW-M01 の単一理由性を
  満たさないまま KILLED と数えると、変異台帳が実効検出力を過大申告する。
- 層を数えずに「検査が 4 箇所ある」と報告すると、実際には 1 箇所しか受理を決めていない事実が隠れる。

**却下した選択肢:**

- **production 層の単独変異も KILLED として数える。** mask されているため帰属が成立しない。
- **production 層の同型検査を削って層を 1 つにする。** 早い段階の固有 reason code を失い、
  診断が劣化する。受理集合は変わらないが、失敗の切り分けが遅くなる。
- **両層同時変異だけを登録する。** どちらの層が効いたかを分離できず、単独変異の帰属も得られない。
