---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-29
wave: dev-wave-land-cleanup-enforce
seq: 2
---

## {{D:child-archived-removal}}. dev-wave 段 9 の子木撤去に「退避してから撤去」の経路を足し、撤去中の main 前進では止めず、land 済み wave 木の終了時 hook を置く

**決定 (ユーザー依頼 2026-09-29「land に成功しつつワークツリーやブランチを掃除せずに終了する wave が多い。改善してくれ」、同日のユーザー裁定「自分で出したゴミは自分で掃除しろ」「価値の小さい残骸は退避してから消す」に基づく):**

1. `tools/dev_wave_cleanup.py remove-child` は、統合証明 (子の履歴が main 祖先、または所有 path の中身が main と一致) が不成立でも、
   次を全部満たせば `integration_basis="archived-unintegrated"` で撤去し、子 branch を削除する。
   (a) manifest の `wave_worktree` が現存し、その HEAD が `refs/heads/main` の祖先 (= wave が land 済み)。
   (b) 子の HEAD reflog・branch reflog の全 commit が main・子 branch tip・他の既存 branch のどれかから到達可能 (子 branch tip からだけ届く commit は history.bundle に入る)。
   (c) 子木の admin dir 配下の per-worktree ref が main 非到達 commit を指さない。
   (d) 占有・index flag・変換 filter・submodule・dirty 退避と再読照合・bundle verify の既存検査を全部通る。
   満たさなければ従来どおり rc=20 で木も branch も残す。D2163 の却下案「非祖先は退避して撤去する」をこの条件つきで採用し、
   D2197 の `-D` 経路を退避済みの子へ広げる。
2. 統合証明の後に main が前進しただけ (証明時の main tip が現 main の祖先) なら撤去を続ける。巻戻し・分岐・判定不能は従来どおり拒否する。
   所有 path の比較は証明時の tip のままとする。
3. 子 branch の削除は、削除直前の tip を条件にした compare-and-delete (`git update-ref -d <ref> <old>`) にする。
   `DW-O28` の「`-D`」は非統合 branch の強制削除という意味で読み、期待 OID の照合はその安全側の上乗せとする
   (同節は 996/997 bytes で表記を足せない)。退避経路の条件 (a) は証明時だけでなく、子木の削除直前と admin 再検査でも確かめる。
4. Claude Code の `Stop` hook `tools/dev_wave_cleanup_stop_hook.py` を置く (`.claude/settings.json` に timeout 10 秒で配線)。
   session の cwd が linked worktree で、その branch が作成点 (branch reflog の最古 entry) から前進し tip が
   `refs/heads/main` の祖先なら、終了を 1 回だけ止めて `DW-O28` の撤去を促す。`stop_hook_active` の再 Stop・判定不能・
   git 失敗・1 MiB 超や非 UTF-8 の入力は通す (注意喚起であって正しさ防壁ではない)。本体を `hooks/` の外に置くのは、
   `hooks/` が guard_write の自己保護で AI の直接書き込みを拒否され、変更に D427 の別 worktree 経路を要する防壁の置き場だからである。
   この hook は書込みや操作を防護しないので、AI が書き換えても防壁は弱まらない。D427 が退けた「`hooks/` の中身を script 越しに
   書く迂回」には当たらない。
5. `DW-S05-A`: fix は同じ子木と同じ branch を再利用し、補助・計測・probe 木も作成時に manifest へ登録する。

**理由:**
- 2026-09-29 に land した wave 約 35 本の transcript 集計で、wave 本体の木はおおむね撤去されていた。残骸の主因は子木の `remove-child` rc=20
  (fix 巡の途中版の木が所有 path 不一致、repo に入れない probe・作図の木が所有 path 空で、構造的に統合証明が成り立たない。約 10 wave)、
  撤去中の main 前進による rc=30 (4 wave)、撤去を呼ばず終了 (2 wave、うち 1 本は終了時に wave 木内) だった。
- 退避経路でも子の commit は history.bundle に、未 commit の差分と未追跡物は patch・tar に残り、撤去前に再読照合と `git bundle verify` を行う。
  失うものが無い状態でだけ消す、という D2163 の「main から到達可能なものだけ捨ててよい」の原理を「証拠 dir から復元可能なもの」へ広げる。
  ユーザーは損失ゼロの厳密さより残骸が消えることを求め、同時に退避を求めている。
- wave が land 済みであることを退避経路の条件にするのは、land 前の呼出しで作業中の子を消さないため。
- 証明時の main tip が現 main の祖先なら、「子の内容が証明時の main に存在した」という事実は main の履歴に残り続ける。

**却下した選択肢:**
- 退避の完全化 (木の全 entry 目録、index の生 bytes、stash、submodule admin の保存、空 repo での bundle 検証) — 実測した残骸の原因と対応せず、
  既存の patch・tar・bundle と重複する (段 3 過剰レンズ)。
- 途中停止 (rc=30) からの段階別再開の journal — 現行は木の削除後・受領証の前に止まると再実行で完了できない (実在する弱点) が、
  実測 4 件の主因は main の前進で本決定 2 が消す。残る頻度を測ってから設計する。
- land tool の成功出力に撤去の案内を足す — JSON 出力に consumer があり、終了時 hook の方が「撤去せず終了」に直接効く。
- 周期的な自動 sweep、他 wave の木の自動撤去 — D2163 と D204 の対象限定を維持する。
