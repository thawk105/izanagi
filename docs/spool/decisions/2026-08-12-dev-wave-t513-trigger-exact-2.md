---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-12
wave: dev-wave-t513-trigger-exact
seq: 2
---

## {{D:trigger-admission-exact-bytes}}. materialized trigger predicate の受理を物理行の raw bytes 一致にする

**決定:** build admission は materialized source の hole を、`PREDICATE_HOLE_INDENT + emit_predicate(mask)`
の UTF-8 bytes と**物理行 raw bytes で完全一致**するときだけ受理する。骨格由来のインデントは
`axis_trigger_gating.PREDICATE_HOLE_INDENT` として pin し、その pin が骨格 patch の実バイトと
一致することを独立したテストで固定する。比較は共有 parser の text 復号結果ではなく、
同じファイルを binary で読み直した bytes に対して行う。

**理由:**
- 正規の materializer は骨格 hole 行のインデントを前置して書く。したがって「emitter 出力そのもの」を
  期待する素朴な exact 比較は、正規経路を全拒否する。exact の期待値には骨格インデントが要る。
- text mode の universal-newline 変換は `\r` を比較前に落とす。共有 parser の復号結果で比較すると、
  CRLF / CR-only の source が exact 比較を素通りする。raw bytes で比べて初めて
  「emitter が生成しうる bytes だけを受理する」という主張が成立する。
- インデントを patch から実行時に導出する案は、admission に patch ファイルへの実行時依存を作る。
  期待値は結局同じなので、pin + drift 検査の方が依存が少ない。

**却下した選択肢:**
- 先頭空白だけ許して末尾空白を閉じる部分 exact — 任意インデントと tab を受理したままで、
  受理集合の穴が残る。exact とは呼べない。
- 共有 parser の `newline` 挙動を変える — quarantine 経路の全 consumer へ波及する。
  admission 1 箇所の受理集合を狭めるために、読み取り層の意味を全体で変えるのは範囲が広すぎる。

**限定:** この受理集合は `trigger_gate_binding` を伴う評価にだけ適用される。binding を渡さない
呼び出しはこの検査に到達しないため、trigger source 一般の受理集合を狭めたことにはならない。
