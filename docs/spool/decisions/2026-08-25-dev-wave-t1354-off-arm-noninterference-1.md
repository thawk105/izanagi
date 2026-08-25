---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t1354-off-arm-noninterference
seq: 1
---

## {{D:offarm-noninterference-claim-scope}}. off arm 非干渉性の主張は、閉じた領域ごとに分けて書く

**決定:** 8c 事前登録 §4 が非干渉性を 3 領域へ分解して規定している以上、実装と記録も
領域ごとに「閉じた」「閉じていない」を分けて書く。まとめて「非干渉性が成立した」と書かない。

現時点で言えるのは次だけである。領域 (i) role 入力 bytes は先行実装で閉じた。
領域 (ii) provider へ送る request の本体は、**supervisor から Claude CLI への launch contract
(argv / stdin / env / cwd / その他 kwargs) の範囲で、generation 1 の off arm について**
機械検査を持つ。実 CLI が組み立てる outbound request bytes は含まない。
領域 (iii) の除外 field は**候補列挙**をコード側に持つだけで、凍結事前登録本文への反映は未了である。

したがって §6 前提条件 2 は **open のまま**とし、閉じたと記録しない。

**理由:**
- 事前登録は領域ごとの個別規定を明示的に要求し、「列挙されていない field を除外根拠なしに
  (iii) へ分類してはならない」と書いている。領域を跨いだ一括の主張はこの要求を満たさない。
- 検査の届く範囲より広い主張を記録へ残すと、証拠台帳が存在しない被覆を参照し、
  受理根拠を過大計上する。8c 6 cell の on/off 差を descriptor 効果として解釈する根拠が汚れる。
- 絶対規律 2 が守るのは正しさの gate である。主張を縮小する方向の訂正は規律を強める。

**却下した選択肢:**
- 条件 2 の評価器 (`s8c_preregistration_evidence.py`) まで scope を広げて充足へ遷移させる —
  条件 2 の証拠契約は arm binding の単射性しか required_evidence に持たず、非干渉性を表す
  field を 1 つも持たない。接続には証拠契約の改訂 = 受理意味の変更が要り、
  `DECIDER_VERSION` の bump と次世代 record の発行を伴う。既成事実にしない。
- test double の runner 境界で見た同一性を「provider request の byte 同一性」と呼ぶ —
  Claude CLI を black box のまま使う限り、CLI が cwd・mcp path・ambient state を
  内部 system prompt や remote request へ再投影しないことは source から示せない。

## {{D:transport-metadata-exclusion-is-candidate-only}}. 領域 (iii) の除外集合はコード側の候補列挙にとどめ、根拠に未証明を明記する

**決定:** 比較から除外してよい transport metadata を production module の閉じた集合として置き、
同じ key 集合を持つ不変な根拠 mapping を対にして import 時に一致を検査する。
ただしこれを**事前登録本文への field 列挙の代替と見なさない**。docstring と各根拠に
「候補列挙である」「role からの不可視性は未証明である」と書く。

除外の根拠は次の 4 点で構成し、「ランダムだから安全」という形にしない。

1. 導出が holdout / workload / arm / binding digest を入力に持たない (source の行で示す)
2. 実際の値が holdout 名・workload 名・binding digest の部分文字列を含まないことをテストが実測する
3. prefix・leaf・親子関係・repository 外であることを pin し、ランダムな最終要素だけを落とす
4. role からの不可視性は未証明である

**理由:**
- 除外を丸ごと落とす案は採れない。比較する 2 つは別 run であり temp path は必ず異なるため、
  そこへ byte 同一を要求する検査は無条件に赤くなる。無条件に赤い検査は gate ではなく壁であり、
  検出力を持たない。
- 一方「ランダムだから対象別ラベルにならない」は成立しない。乱数由来の identity でも、
  provider 生存期間や cell を安定して区別するラベルになりうる。根拠は導出の非依存性と
  実測に置く必要がある。
- 凍結文書への反映は再凍結セレモニーを伴う別手番である。コード側の列挙で本文の要求を
  満たしたことにすると、凍結の意味が失われる。

**却下した選択肢:**
- 除外 2 field を比較対象へ戻す — 上記のとおり無条件に赤くなる。
- 除外の根拠を「invocation ごとの nonce だから」とする — 実測と食い違う。
  mcp config path の neutral root は provider 構築時に 1 度だけ作られ、provider 生存期間で固定である。

## {{D:projected-provider-env-order-must-be-deterministic}}. projected provider の env は固定順で構築する

**決定:** `ClaudeProjectedRoleProvider` が subprocess へ渡す env を、allowlist 集合の反復順ではなく
決定的な固定順から構築する。受理 key/value、必須 key の検査、transport env の上書き規則は変えない。

**理由:**
- allowlist は `frozenset` であり、str の hash 乱択化により反復順が process ごとに変わる。
  親が 4 process で実測し 4 通りの順序を観測した。env は dict のまま subprocess へ渡され
  envp 順に反映されるため、**同一入力でも request の envp 順が run ごとに変わっていた**。
- これは非干渉性以前の非決定性である。request の byte 同一性を主張する前に閉じる必要がある。
- 順序の固定は受理集合を変えず拒否力も変えない。純粋な強化である。

**却下した選択肢:**
- allowlist 定数自体を順序付き型へ変える — 定数は別 module が所有し、同じ集合を使う
  s8b 側の provider へも波及する。s8b の freeze への影響は独立裁定が要るため、別 wave の残件とした。
- env を領域 (iii) へ除外する — env は holdout 由来の値を持ちうる経路であり、
  除外すれば検査の中身が消える。順序込みで比較し、差は赤にする。
