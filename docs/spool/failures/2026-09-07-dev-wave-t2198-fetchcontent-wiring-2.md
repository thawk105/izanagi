---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-t2198-fetchcontent-wiring
seq: 2
---

## 新規

### {{F:upstream-argv-wiring-blocked-by-downstream-closed-grammar}}. 上流への argv 追加が、下流の閉じた argv 文法に無効化される [手順漏れ] [恒真ゲート]

- 事象: 認証経路をオフライン依存へ配線する wave で、段 3 の敵対レンズが「配線しても A-6 は
  `indeterminate` のままである」ことを指摘した。親が実コードで裏を取り、段 4 で実装せずに
  ユーザー再裁定へ返した。段 1 の brief も段 2 のプランも、この阻害要因を見落としていた。
- 根本原因: 変更は共有 build 経路の configure argv を広げるものだった。この argv は WAL の
  `build_done.perf_configure_cmd` へ記録され、下流の認証 collector が
  `_exact_trace0_configure_argv` で**閉じた文法との完全一致**を検査する。文法は
  `expected = fixed + prefix + ordered_define_tokens` を完全に determine しており、
  token が 1 本増えるだけで不一致になる。**argv を作る側だけを見て、argv を検査する側を
  見なかった**ことが見落としの原因である。
- 波及: 文法は policy JSON の `trace0_cmake_argv` にあり `_protocol_preimage` に含まれるため、
  広げると A-2 / A-6 の `protocol_sha256` が動く。凍結された認証プロトコルの同一性であり、
  親の一存では変えられない。段 1 の pin 閉包は編集対象 4 file の内容 hash を値で走査して
  「literal pin 0 件」と結論したが、**policy JSON の golden 4 値を閉包に入れていなかった。**
  走査の射程が「編集すると決めた file」に限られており、「編集の結果 bytes が動く file」へ
  広がっていなかった。
- 恒久対応: {{D:a2-trace0-grammar-blocks-offline-wiring}} でユーザー再裁定へ返した。
  再発防止は memory `closure-and-search-discipline` の pin 閉包規律へ次を加える —
  **producer の出力 (argv・payload・record) を広げる変更では、その出力を読む consumer を
  1 つ残らず辿り、閉じた集合・完全一致・exact key 検査を持つものを列挙してから scope を決める。**
  path と内容 hash の走査は「編集する file」しか見つけないので、これを代替にしない。
- 再発検知: 段 3 の敵対レンズが独立に検出した (レンズ B 所見 1)。レンズに
  「成果物が実際に効く全層が scope に入るか」を必ず入れる `DW-S03` の規定がそのまま機能した。

## supersede 追記

- F808 **supersede: 2026-09-07** — 恒久対応の「共有 measurement pipeline への横断的な引数追加になる」という見立ては必要条件でしかない。引数を通しても下流の閉じた trace0 argv 文法が全 cell を拒否し `indeterminate` が続く。詳細と解消案は {{D:a2-trace0-grammar-blocks-offline-wiring}}。
