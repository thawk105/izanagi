---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-t1784-prereg-admission-record
seq: 2
---

## {{D:prerun-admission-record}}. B-4 実走前に commit された admission record を controller の必須入力にする

**決定:** 閉じた critic invocation の production factory
`orchestrator/campaign/p3_b4_closed_critic.create_b4_closed_critic_pair` に、既定値なしの
必須 keyword `admission_record_path` を置く。record は canonical JSON schema
`p3-b4-prerun-admission/v1` とし、事前登録文書の (repository path, blob sha256, content commit) と、
`expected_claude_model_snapshot` / `expected_effective_critic_prompt_sha256` /
`expected_closed_critic_projection_closure_sha256` の 3 期待値を持つ。
検証は executable 探索・artifact 作成・provider 作成より**前**に行い、
projection は pair 作成時、prompt は provider 作成直後 (role query 前)、
model は envelope 検証直後 (decision parse 前) に照合して、不一致は例外で停止する。
警告・環境変数・CLI flag の逃がし道を作らない。

**理由:**
- 事前登録 §6 の前提条件 1 は「§5 の全欄が記入済みで、その版が commit されている」ことを
  実走の前提にする。3 期待値は controller が**実走後に** receipt へ書くだけだったため、
  走らせてから出てきた値を §5 へ書き写せた。§1 が自ら書いた ancestry の穴がそのまま残る。
- 既定値を持たせると既存の呼び手が黙って record 無しで通り、gate が恒真になる。
  受理集合が 1 件も変わらないなら実装した意味がない。
- 3 期待値のうち projection と prompt は repository の bytes だけから実走前に確定する。
  model は `modelUsage` からしか観測できないので、record は**期待値の宣言**を持ち、
  controller が実測と照合する。「予測」ではなく「事前宣言 + 実行時照合」がこの欄の意味である。

**却下した選択肢:**
- receipt schema を `/v3` へ上げて admission field を持たせる — `/v2` は既に 3 実測値と
  `evidence_class` を持っており、昇格は gate を 1 bit も強くしない。併走 wave が同じ
  dataclass と reader を編集面に持つため、合流の被害だけが増える。
- record を `projection_closure_manifest()` の entry に加える — 同 manifest は controller 自身の
  bytes を含むため、record を入れると「自分の hash を自分が宣言する」自己参照になり充足不能になる。
  代わりに**検証器の Python bytes だけ**を閉包へ入れた。検証器の後付け改変は projection 不一致で落ちる。

## {{D:admission-sidecar-not-receipt}}. 発効版 commit hash の記録は receipt でなく独立 sidecar で満たす

**決定:** provider query より前に、artifact root へ排他生成 (`O_EXCL`) する canonical JSON の
sidecar `p3-b4-prerun-admission-sidecar/v1` を書く。record の path と sha256、検証時 HEAD commit、
事前登録文書の path / content commit / content sha256、3 期待値を持たせ、CLI が sidecar の
path と hash を出す。certified pair の関門は、fresh な record から canonical bytes を再構築して
sidecar の bytes と hash の双方を照合する。success receipt の `schema_version` と field は変えない。

**理由:**
- 事前登録 §1 は逐語で「実走成果物にその発効版の commit hash を記録する。記録がない実走は
  事前登録された実験として扱わない」と要求する。receipt を変えない裁定と組み合わせると、
  gate は通るのに監査の跡が残らない状態になる。sidecar はその穴を receipt の形式を触らずに埋める。
- 後段の consumer は receipt と sidecar の組を必須入力にできる。receipt 単独を台帳へ載せて
  「事前登録済み」と分類する経路は誤受理になるため、sidecar hash の照合を必須にする。

**却下した選択肢:**
- receipt dataclass への field 追加 — 上の {{D:prerun-admission-record}} と同じ理由で却下。
- sidecar を projection 閉包へ入れる — record と同じく自己参照になる。

## {{D:section5-syntactic-scope}}. §5 の機械検査は構文的非空と期待値行の grammar に限り、名前で主張を越えない

**決定:** 事前登録 §5 の機械検査は次に限る。(a) 固定表の 10 label が重複なく揃い、
各値 cell が空でなく登録済み sentinel と一致しないこと、(b) model / prompt / projection の
1 行だけを exact grammar で読み、record の 3 期待値と一致すること。
**残り 9 欄の型・意味・artifact 実在・render 後の非空は検査しない。**
関数名・例外文言・docstring・テスト名は、この範囲を越える語を使わない
(`assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel`、
`[admission-preregistration] section 5 source cell contract failed`)。
証明範囲は repository-local な順序に限り、証明できないことを module docstring に逐語で列挙する。

**理由:**
- 絶対規律 2 は「正しさゲートを緩める変異を許さない」であり、検査していないものを
  検査したと読める名前は、後段の実装者に「10 欄すべてが照合された」と信じさせる。
  これは gate を緩めるのと同じ効果を持つ。
- 10 欄すべてに型検査を入れると、欄の書式を今まさに決めている併走 wave の記入を壊す。
  型が先に固定されると、文書側が型に合わせる義務を負い、事前登録の内容を実装が支配する。
- 証明できないこと (別経路で先に結果を知ってから record を commit する攻撃、
  Git timestamp による絶対時系列、model 不一致が critic query の後にしか検出できないこと) は、
  外部の append-only ledger か署名済み token が無い限り repository 内では閉じない。
  閉じないものを閉じたと書かないことが、この決定の中心である。

**却下した選択肢:**
- 10 欄の型検査を今 wave で入れる — 併走 wave の記入を壊す。文書の書式が確定した後の別 wave。
- 名前を変えず検査だけ足す — 名前が主張を越えたまま残る。
- 「§6 前提条件 1 を充足した」と読める名前 — 充足していない前提を緑に見せる。規律 2 違反。
