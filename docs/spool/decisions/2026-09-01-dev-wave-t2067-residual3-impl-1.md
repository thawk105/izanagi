---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-01
wave: dev-wave-t2067-residual3-impl
seq: 1
---

## {{D:floor-selection-consumer-enforcement-g1-only}}. load-only consumer への床値選択強制は g1 限定・選択規則限定の狭い API で行う

**決定:** 批准床値を静的 loader だけで読む consumer へ選択規則を強制するときは、
`launch_validate` を再利用せず、選択規則だけを課す狭い公開 API を使う。同 API は
`generation_number != 1` では何も観測せずに返り、g1 でだけ launch 側の強制点と同じ引数・
同じ拒否理由で選択 identity を課す。activation HEAD、current build admission、closure、
binding graph、live scan は持ち込まない。

同 API は選択 identity を呼ぶ前に、探索先 namespace を批准文書と記録 protocol へ束縛する。
official path の proto8 が記録 protocol の canonical hash 先頭 8 hex と一致すること、および
generation / path / protocol の env_tag が一致することを要求し、失敗は既存の
`floor-selection-unverifiable` へ畳む。新しい拒否理由は作らない。

selected certificate と path 起動秒の検証は行わない。launch 側の強制点が既定でそれを行わない
ためであり、consumer をそれより厳しくしない。

D1241 / D1313 の advisory / non-certifying 上限は解除しない。本規則の適用点が増えても
追加で主張してよいのは D1313 の (a)(b)(c) の 3 点のままである。

**理由:**
- 静的 loader は otherwise-valid な g2 を受理するが `launch_validate` は artifact I/O より前に
  g2 を拒否する。`launch_validate` を consumer へ足すと、各 consumer に g2 の新しい拒否挙動が
  生じる。これは g2 が実在してから設計すると定めた D1325 に反する。
- `launch_validate` は選択以外に current contract / build admission / closure / live scan を通す。
  D1312 は loader と historical へ current policy を持ち込まない境界を定めたものであり、
  load-only consumer 全体を full current admission へ昇格させる許可ではない。
- 選択 identity の helper は `selected_path_info['env_tag']` から探索 namespace を自分で
  組み立てる。`_launch_validate` では proto8 と env_tag 連鎖の束縛が選択呼出しの後段にあり
  合成として守られるが、選択規則だけを切り出すと後段が無い。束縛が無ければ、別 env の
  namespace を指す `floor_source.path` を持つ g1 は、真の namespace により早い導出適格 run が
  あっても探索から外せる。実測でも修正前は適格性導出の呼出しが 0 回で通った。

**却下した選択肢:**
- consumer から `launch_validate` を呼ぶ — 上記のとおり g2 拒否と full current admission を
  密輸する。
- 静的 loader へ選択検査を入れる — D1312 が却下済み。historical reverify が recorded semantics を
  選ぶ前に落ちる。
- 束縛の失敗に新しい拒否理由を割り当てる — 理由集合が増えると主張の水準が動いたと読まれる。
- selected certificate と起動秒も検証する — launch 側の強制点より厳しくなり、選択強制の範囲を
  超える。起動証明書の実時間性は別の未解決項目である。

## {{D:floor-residuals-not-implemented-scope}}. 床値残余のうち 3 件は現時点で実装しない

**決定:** D1313 が列挙した残余のうち、次の 3 件は現時点で実装しない。

1. **s8c C06 予算経路への選択強制。** gate は置けるが、実装前後とも budget ledger を生成できる
   入力集合は空である。変わるのは選択 error と C05 authority error のどちらが先に出るかだけで、
   成果物の値・受理集合・参照は変わらない。単一理由の変異も登録できない。C05 の実装が着地した
   時点で再評価する。
2. **起動証明書の実時間性。** 不能の理由は凍結時に再計算できないことではなく、launch 時点の
   独立した commitment が保存されていないことである。clean scan digest の preimage は
   certificate、journal、manifest、Git tree のいずれにも残らない。certificate 自身の値を
   expected にする形は D80 が恒真として禁じており、現在 scan を expected にすれば正当な drift を
   過剰拒否する。閉じるには署名、外部発行 nonce、一回性台帳のいずれかが要り、D1241 がそれらを
   禁じている。
3. **s8c production final claim 配線。** aggregate 点は特定できるが、judge が要求する
   exact 6 cell・反復 2 以上・6×n 観測の schedule、throughput と correctness/trace に独立束縛した
   attestation authority、判定パラメータの正本がいずれも production に存在しない。加えて
   3 表は repository 外の絶対 path へ書かれる一方、acceptance receipt schema は 3 表の path/hash を
   持たず、失敗原子的に束ねられない。設計メモに留める。

oracle manifest への同種の強制は設計上正しく実装可能だが、対応 test file を別 wave が保有して
未着地のため本 wave では着手しない。production へ test 専用の抜け道を入れて緑にすることはしない。

**理由:**
- 1 は成果物影響を 1 行で示せず、無効化しても受理集合も fail-closed 挙動も期待方向へ変わらない。
  死んだ gate と無効な変異証拠だけが増える。
- 2 は既存材料だけでは実時間順を証明できず、証明できる形にするには禁止された機構が要る。
  現行の full validation もその docstring で実時間順を保証しないと明記している。
- 3 は入力の正本が連言で欠けており、発火条件を満たす既存成果物 path を書けない。
- oracle manifest は、gate を入れると既存の 2 正例が必ず赤になる。fixture 追随には他 wave 所有の
  test file の編集が要る。

**却下した選択肢:**
- 到達不能でも先に配線しておく — 呼ばれない検査と殺せない変異が残り、証拠の水準を偽る。
- 起動証明書に厳格版検証をそのまま流用する — expected が無いため恒真か過剰拒否になる。
- production へ test 時だけ検査を飛ばす分岐を入れて oracle manifest を通す — 偽緑であり
  正しさゲートの弱体化にあたる。
