---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-23
wave: dev-wave-codex-sol-xhigh
seq: 1
---

## {{D:codex-sol-xhigh-all-stages}}. dev-wave の codex を全段 `gpt-5.6-sol` @ `reasoning=xhigh` にする — D514 の supersede であり、根拠はユーザー裁定であって A/B 証拠ではない

**決定:** dev-wave が起動する codex の model を、全段・全 lane 単一の `gpt-5.6-sol` に戻す。
`reasoning` は段 2 / 段 3 / 段 5 / 段 6 のすべてを `xhigh` に揃える。
lane 名 `sol` / `luna` はレンズ識別子のまま残し、`--lane` 呼び出しの意味は反転させない。
D514 (全段 `gpt-5.6-luna` @ `max`) を supersede する。

**この採用の根拠はユーザー裁定であり、品質同等性や非劣性の証拠ではない。**
ユーザーは「研究が壊れそうなくらい進捗がおかしくなっている」を理由に、
model と effort の双方を明示指示した。D423 が「supersede はユーザー裁定にだけ属する」と定めた
権限を、ユーザー自身が行使した経路であり、D514 が通ったのと同じ道である。

**effort の向きを正直に記録する。**

- D514 が `max` を採った理由は「luna は愚かだから luna を使う段はすべて max」という補償だった。
  sol へ戻す本決定では補償の前提が消える。
- 一方、`xhigh` は `CODEX_REASONING_EFFORTS` (low < medium < high < xhigh < max) で `max` の 1 段下である。
  D514 直前の値と比べると全段 1 段下がる。
- D514 より前の sol 期の値 (段 2 / 3 = `max`、段 5 / 6 = `high`) と比べると、
  **段 2 / 3 は 1 段下がり、段 5 / 6 は 1 段上がる。**
- 段 2 / 3 の引き下げは D207 が「引き下げの可否は paired・blind・非劣性 A/B だけが決める」と
  定めた領域に当たる。本決定はその手続きを経ていない。ユーザー裁定による supersede である。
- **検出力への正味の影響は測っていない。** model 軸の上げが effort 軸の下げを上回るという
  期待はあるが、それは仮説であって実測ではない。

**この決定が回復するもの:**

- 段 3 の敵対相談 2 レンズと段 6 の敵対レビュー 2 本が、D241 が「sol にしか出せない所見を落とす」
  として不採用にした「全 luna」の形から抜ける。
- 本 wave 自身が実証点になった。sol @ xhigh で走らせた段 6 の 2 レンズと焦点再レビューは、
  親が独立に見つけた 2 件を再現し、親が見落としていた 1 件 (pin の finding 文が D207 帰属のまま)
  を追加検出した。

**機械化した内容:**

- model 権威行は `DW-O01` の v2 文法のまま値だけを差し替えた。v1 文法と過去 commit の
  再構成監査経路、`AuthoritySnapshot` の digest 構造は 1 bit も変えていない。
- effort pin は削除せず張り替えた。visible literal / sentence 定数、finding 文、
  `_check_dev_wave_reasoning_effort_pins()` の expected 値という 4 要素を揃えて更新した。
  1 つでも旧値が残ると pin は常時緑か常時赤へ退化する。
- 段 2 / 3 の finding 文から「D207 に基づく」という帰属と「paired・blind・非劣性 A/B」という
  手続き要求を外し、「採用裁定 (A/B 証拠またはユーザー裁定) と pin の同時更新が必要」へ改めた。
  張り替え後の値の根拠は D207 ではないため、そのままでは checker が将来の正当な更新へ
  誤った手続きを案内する。

**却下した選択肢:**

- **effort を `max` のまま model だけ sol へ戻す** — ユーザー指示が「全て extra high」であり、
  effort を明示的に含んでいた。
- **段 2 / 3 だけ `max` を維持する** — 同じ理由で指示に反する。なお段 2 / 3 の effort は
  argv へ機械強制されておらず、pin は親向けの契約である ({{T:plan-consult-effort-argv-wiring}})。
- **権威行の sol / luna 位置を入れ替える flip trick** — D423 / D514 が挙げた
  `--lane` 呼び出しの意味反転という footgun がそのまま残る。
- **byte 予算超過を予算引き上げで吸収する** — 予算値の変更は独立審査対象であり通常の
  自己改善に含めない。同文書が既に使っている綴りへの表記統一 2 箇所 (`プロンプト`→`prompt`、
  `プラン`→`plan`) で 9 bytes を吸収し、安全義務は 1 つも削っていない。

**rollback:** 権威行 1 行と `workers.md` の 5 語を戻し、`check_docs.py` の pin literal・
finding 文・expected 値と追随テストを戻せば旧挙動へ戻る。v1 文法は残っているため
過去 receipt の監査経路は影響を受けない。
