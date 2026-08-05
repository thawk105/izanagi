# [T-244] P2 実装 wave — 裁定パッケージ 5 件 (ユーザー判断待ち)

いずれも本 wave の裁定 (段 4 決定 (1)〜(7)) の**外側**にあり、実装していない。
親推奨は付けてあるが、確定はユーザーの手番である。

| # | 択一 | 親の推奨 | 根拠の所在 |
|---|---|---|---|
| V-1 | **U-1 の「origin scope の不透明 ID」の解釈。** (a) 1 campaign (= cap=1 では 1 origin) の中でだけ意味を持つ不透明 ID で暫定充足とする、(b) reflux origin authority の `origin_id` へ束縛する形を正とし U-10 解決後に再実装する | **(a) を暫定充足とし、U-10 解決後に (b) へ昇格。** 本 wave は (a) を実装し、U-1 完了は名乗っていない。どちらの読みでも pseudonymization 層は必要なので実装は無駄にならない | `s4-adjudication.md` 決定 (1)、段 3 の両レンズが独立に (b) と読んだ |
| V-2 | **declassification account の fail-open を閉じるか。** (i) role payload / report を次版へ上げ、auditor attempt で account を必須化し canonical payload bytes へ cross-bind する、(ii) 自己申告 annotation のまま残す | **(i)。** ただし report schema・trial registry・acceptance receipt hash へ波及するため独立 wave とする。現状は「会計はしたが強制はしていない」ことを名乗りの上限に含めている | `s6-reviewR2.md` must-fix 2、`s6-refocus.md` must-fix 4 |
| V-3 | **IR の複合 identity を artifact へ搭載するか** (trigger binding record / origin manifest)。搭載すると WAL 受理集合と既存 record の exact key 集合が変わる | **搭載する。** ただし後方互換の設計が要るため独立 wave。現状は checkout 限定の変更検出器であり、artifact identity ではないと明記済み | `s6-reviewR2.md` must-fix 2 / nit 8、`s6-refocus.md` must-fix 5 |
| V-4 | **liveness `extra` の開集合を critic recipient schema で閉じるか。** 現状は producer が任意 key を merge でき、renderer が全値を描画する。識別子 2 key は射影したが、他の key 経由の候補依存文字列は閉じていない | **閉じる (未知 key 拒否)。** 本 wave の射程外の残余として明記済み | `s3-lensB.md` MAJOR-3 |
| V-5 | **production の diff-quarantine evidence が候補由来の短縮 hash と行長を載せる経路を閉じるか。** (i) critic 向けには固定 reason code と行位置へ閉じる、(ii) 明示的 declassification として会計する、(iii) 受容残余として明記する | **(i)。** 32 点の閉じた候補集合では短縮 hash も表引きで復元できる。本 wave の関係検査は fixture 経路しか通しておらず、**production のこの経路は閉じていない** | `s6-reviewR1.md` must-fix 1、`s6-refocus.md` must-fix 1 |

## 併せて記録する scope 外の real 所見 (裁定を要さないもの)

- **critic CLI が `load_diff_rejections()` を renderer へ渡さない**ため、diff-quarantine だけの campaign を
  「rejection なし — 全 variant 緑」と描く。**本 wave が作った退行ではなく既存欠落**である。
  fix では触らず、`s6-refocus.md` must-fix 3 として残した。
- **production の outcome と admitted WAL terminal を照合する検査がない。** fixture 側は本 wave で
  正直な形へ直したが、production 側の照合追加は scope 外とした。
- **critic-facing consumer の網羅検査が固定 path リストである。** 現存 caller は全件入っているが、
  将来の新規 caller は自動発見されない (`s6-refocus.md` should-fix 1)。
- **docs の追随が未了。** `docs/axis-onboarding.md` の projector 必須、各 runbook の
  `candidate_label` / schema 版 / sentinel、`docs/phase3.md` の P2 境界は本 wave では更新していない
  (`s6-refocus.md` should-fix 2)。次の P2 wave または docs wave が所有する。
