# [T-624] activation record の no-op 拒否 — 規則を明文化し、述語の実装は見送った wave

wave branch: `worktree-dev-wave-t624-activation-noop`
基準 commit: `bb824d8b` / 成果物: docs のみ (コード差分なし)
受入: **実装差分が無いため受入全走と変異 matrix は対象外**。docs 検査と関連テストのみ (worklog 参照)

## 何を実装し、何を実装しなかったか

**実装した (単位 1、docs のみ)。** ユーザー裁定 (a) の遷移規則
「全 env の delta ∈ {0,1} かつ少なくとも 1 env の delta == 1」を decisions へ明文化した。
全 env 据置の no-op activation record を拒否する意図を、条件として書ける形にした。

**実装しなかった (単位 2)。** 純 data-layer 述語 `is_valid_activation_mapping_transition` と
その表駆動テスト。段 2 は GO と判定したが、段 3 の 2 レンズが独立に NO-GO を返し、
親が裏取りして不採用に裁定した。

## この wave が確定させた事実

- **番号だけを見る述語では、裁定 D が塞ごうとした失敗を塞げない。** 裁定 D の元の懸念は
  「serial が増えているのに新規 run の contract hash が旧較正へ戻る受理が通る」であり、
  env→generation の数値 mapping しか見ない述語は、後継世代が旧較正を指す再束縛を受理する。
  D176 自身が「逆引き index は module 属性として再束縛可能であり authority として扱ってはならない」と
  明記しており、数値射影はその再束縛に対して無力である。
- **段 2 が提案した 20 行の表には検出力が無かった。** 親が実測した — 各 delta を見ずに
  「delta の総和が 1 以上かつ env 数以下」で判定する誤実装が、20 行すべての期待値と一致する。
  この誤実装は `(+2, −1)` の record を受理する。表を land していれば、検出力ゼロの gate が
  「no-op を拒否する保証」として台帳に残っていた。
- **`is_valid_successor` と新述語は同型ではない。** 前者は module 初期化の call chain に
  結線済みで、2 世代目が登録された瞬間に発火する。後者は consumer が 1 つも無い。
  「結線済み・未発火」と「結線なし」の差が、D176 の先例を援用できるかどうかを分ける。
- **`env_contract.py` の source sha は凍結成果物 2 種に pin されている。** silo evidence の
  path+sha 隣接 field と、t419 probe manifest の role 名 key `env_contract_sha256`。
  いずれも歴史記録であり、現行 bytes とは既に不一致 (live pin は 0 件)。
  親は段 1 でこれを「pin 0 件」と誤記録した (F30 の 4 度目の再発)。

## 一次資料

| ファイル | 内容 |
|---|---|
| `s1-brief.md` | 段 1 brief。前提実測 A〜E と親の provisional 裁定 (P1)〜(P3) |
| `s2-plan.md` | 段 2 プラン起草 (codex, read-only, reasoning=max) の逐語。判定は GO |
| `s3-lensA.md` | 段 3 敵対レンズ A (裁定境界と規律) の逐語。判定は NO-GO |
| `s3-lensB.md` | 段 3 敵対レンズ B (述語の意味と検出力) の逐語。判定は NO-GO |
| `s4-adjudication.md` | 段 4 裁定。親の裏取り実測 P〜S (実測 S の probe 判定部と出力を逐語で含む)、所見の real/refuted、ユーザーへ返す択一 α/β/γ |

## ユーザーへ返す択一

α (述語の入力粒度)、β (env membership migration)、γ (`DW-G04` の適用) の 3 件。
本文と親の推奨は `s4-adjudication.md` の同名節を正本とする。
