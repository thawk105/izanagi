---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-18
wave: dev-wave-t1086-report-receipt
seq: 3
---

## 新規

### {{F:layered-defence-mutation-misattribution}}. 層状に守られた検査で、消す層を読み違えて変異を 2 度空振りさせた [テスト代表性] [手順漏れ]

- 事象: store path の symlink escape 拒否について、事前登録した変異が 2 回続けて
  「意図した負例を赤にできない」形になった。1 回目は resolve containment
  (`relative_to`) だけを消す登録で、敵対レビュー 2 本が独立に「後段の symlink 検査が
  先に拒否するので等価変異」と指摘した。2 回目は containment に加えて親と leaf の
  `S_ISLNK` 検査も同時に消したが、symlink 負例 2 件は依然として緑のままだった。
- 根本原因: **`S_ISLNK` 検査は `lstat` の型検査と冗長で、実際に拒否している層ではなかった。**
  `os.stat(..., follow_symlinks=False)` の結果に対する `S_ISDIR` / `S_ISREG` 検査は、
  symlink に対して偽を返すのでそれ自体が symlink を弾く。さらに `O_NOFOLLOW` が
  `ELOOP` で 3 番目の防壁になっている。親は「symlink を拒否する検査」を名前で探して
  `S_ISLNK` だけを層と数え、**同じ入力を拒否する層を最後まで数え上げなかった**。
- 恒久対応: `docs/dev-wave/mutation.md` の `DW-M01` (同じ入力を拒否する層が前後に無いことを
  コードで確認し、確認できなければ登録せず実効 gate へ再照準する) と `DW-M04` (両層変異は
  kill 期待を必ず事前登録する) が既に要求している手順を、**拒否の名前ではなく拒否の効果で
  層を数える**形で適用する。具体的には、変異登録の前に「この入力を拒否しうる述語」を
  型検査・flag・字句検査まで含めて列挙し、列挙した全層を同時に消す変異として登録する。
- 再発検知: 本 wave の変異台帳が実測記録として残る
  (`output/insights/2026-08-18_t1086-report-receipt/mutation/`)。attempt 1 と attempt 3 を
  erratum として保全し、attempt 2 (10 KILLED) と attempt 4 (残り 2 件 KILLED) で
  最終的に baseline PASSED・12/12 KILLED・SURVIVED 0・MISMATCH 0 に到達した経緯を残している。
- 併記する実測: 同じ wave で字句検査 (`..` の拒否) にも同型の重複があった。字句検査だけを
  消しても `..` の負例は resolve containment が受けて緑のままで、赤になったのは
  絶対 path・制御文字・backslash の 3 例だけだった。**多層防御は望ましいが、
  変異の期待 node を層ごとに書けると仮定してはいけない。**
