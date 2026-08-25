---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t1664-occupancy-blind-spot
seq: 2
---

## {{D:occupancy-blind-spot-undecidable}}. 同 uid の non-dumpable process が対象内に居るかは観測では決定不能であり、discharge は正の証拠でしか作れない

**決定:** `tools/check_worktree_occupancy.py` の same-uid unreadable-cwd blind spot について、
**「その process の cwd が対象内にあるか」を `/proc` の観測から判定する述語を今後採用しない。**
この blind spot を撤去拒否へ倒すか否かは、lease・delegated cgroup v2・特権 observer のいずれか
**正の証拠**を伴う設計とセットでのみ裁定する。checker 単独で fail-closed へ倒す変更は、
可用性の実測値を裁定へ書いたうえでユーザーが選ぶ。

**理由:**
- 同 uid の non-dumpable process では `cwd` / `exe` / `root` の 3 つだけが `PermissionError` になり、
  `cmdline` / `comm` / `status` (Uid, PPid) / `stat` (starttime) は読める。したがって
  **対象の中に居る process と外に居る process は、可読 field を完全に同一にできる。**
  「対象内は占有、同じ process が対象外なら撤去可」を同時に満たす述語は存在しない。
- 観測ベースの discharge 案は 3 つとも実測で反証された。
  (a) comm 固定 allowlist は F490 が `nqs_shpd` で反証済み。
  (b) argv と祖先 argv に対象 path が現れないことを根拠にする案は、cwd が worktree 内の
      実 worker 125 本のうち 78 本 (62.4%) を discharge する。落ちる側は wave manager の
      `claude bg-spare` 本体、launcher の bash、python3、待ち手の sleep / tail / timeout であり、
      いずれも `cd` で入るため argv に path を持たない。
  (c) 「対象 directory の作成より前に起動していれば discharge」する案は、107 本のうち 16 本を
      discharge し、その正体もやはり wave manager 本体である (manager は worktree を作る前に起動する)。
  (b)(c) はどちらも「自分が座っている worktree を消してよい」と判定する向きの誤りで、
  D706 が禁じた「値域を測らずに述語を採用する」の受理側の変種である。
- fail-closed 単独の運用コストも実測した。blind spot は 6 サンプルすべてで 3 で不変
  ((sd-pam) / sshd / ssh-agent) であり、`len(blind spot) == 0` はこの login node で到達不能である。
  現存 77 本の worktree のうち 59 本が rc=0 (撤去可) なので、倒した瞬間に 59 本が撤去不能化し
  自己撤去は 100% 失敗する。D706 の「満たせない gate は防壁ではなく停止装置であり、
  運用者に迂回の動機を与える」に該当する。
- 迂回は正味の安全性低下である。手動 `rm -rf` は occupancy だけでなく branch ancestry・
  clean tree・fold state・cwd 検査を同時に飛ばす。閉じない穴 1 つより、全部飛ばされる経路が危険である。

**却下した選択肢:**
- checker 単独で blind spot 非空を `indeterminate` へ倒す — 正しさとしては妥当だが、
  上記の実測どおり即座に停止装置になる。lease 等の正の証拠と対で入れる。
- 可読 field からの discharge を精緻化して続ける — (b)(c) の反証が示すとおり、
  可読 field は「対象内に居るか」と相関しない。精緻化しても向きが受理側へ倒れるだけである。
- blind spot を無視してよいと結論する — repo の Python コードに `PR_SET_DUMPABLE` 呼出しは 0 件で
  今日の izanagi 経路では発火しないが、worker executable は外部 path + digest で渡され、
  setuid bit・file capabilities・実行後 dumpable state は検査されていない。「発火しえない」とは言えない。
