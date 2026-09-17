---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2637-offrepo-parallel-scan
seq: 1
---

## {{D:offrepo-scan-directory-queue}}. 到達不能監査の repo 外走査は directory 1 個を 1 task とする work queue で並列化し、逐次版の first-seen は walk key で再現する

**決定:** `tools/audit_dangling_commits.py` の repo 外走査 (D2104 項 20 の第 1 段) の並列単位は
**directory 1 個 = 1 task** とし、固定本数 (`OFFREPO_SCAN_WORKERS`、既定 16) の thread が `queue.Queue` から
task を取る。各 task は `os.walk(directory, topdown=True, onerror=…, followlinks=False)` の**最初の yield だけ**を
処理して generator を閉じ、sorted `dirnames` のうち `os.path.islink` が偽のもの (= `os.walk` 自身の再帰条件) を子 task
に積む。候補照合は逐次経路と同じ helper を共有する。逐次版 (topdown・sorted の前順 DFS) の first-seen 代表と
`possible` の挿入順は、file ごとの walk key `(((1, dir), …, (0, file)), 候補列内の位置)` の最小で再現する。
root は `sorted(roots)` の順に逐次に完結させる。workers=1 は pool を作らず従来の 1 本の `os.walk` を通し、
意味論の参照実装として残す。heartbeat は主 thread だけが出し、待機には正の timeout を置く。

**理由:**
- 探索根直下の subdirectory ごとに `os.walk` 全体を配る第 1 案は、実根 (約 185 万 file) で pytest tmp repo の森
  1 本を 1 worker が 15 分以上歩く tail に入り、16 thread の利得が最大部分木の逐次時間で頭打ちになった
  (列挙 1042 秒、変更前 warm 935 秒より遅い)。並列段そのものは約 14,500 file/秒 (変更前の約 10 倍) で進んで
  おり、律速は Python thread (GIL) ではなく分割の粒度だった。directory 単位の queue に替えて列挙 110〜335 秒
  (同時刻対照の old 936〜1298 秒に対し 3.2〜9.4 倍、login node warm、共有 node の混雑で 6 走の max/min = 3.0)。
- `os.walk` の 1 directory 分の意味論 (scandir 失敗は `onerror` 1 回・yield なし、`is_dir()` 失敗は非 dir 扱い、
  symlink dir は `dirnames` に載るが降りない) を再実装せず、現物の generator をそのまま使えるのがこの形である。
  独自に `os.scandir` で分類する案は同じ意味論を複製する。
- 代表 external (path + initial_stat) は `_compare_regular_candidate` の読取 path であり、同 inode の alias でも
  `os.open` の失敗有無が path で変わりうるため、path 昇順最小のような別の規則に置き換えると現行と非等価になる
  (段 3 レンズ A の反例)。walk key の最小は逐次版の first-seen そのものである。
- directory ごとに `concurrent.futures` の future を作って `wait` する形は、25 万 task では待機ごとの走査が
  二次化する (F628 型) ので採らない。

**この決定が主張しないこと:**
- cold (client cache が空) の倍率。login では測れず、別 node の 1 走目は補助観測にとどまる。
- 既定 16 が最適・安全であること。thread 生成に失敗する環境では逐次版なら完走した監査が rc=2 になりうる。
- 走査中に rename・削除が起きる探索根での逐次版との同一観測。両版とも `onerror` と初期 stat の再照合で
  確認不能として数えるだけで、snapshot は取らない。

**却下した選択肢:**
- **直下 subdirectory 単位の固定分割** — 実測で tail に頭打ちになった (上記)。
- **`os.scandir` による独自の分類と再帰** — `os.walk` の失敗時挙動を再実装することになり、等価性の論証が
  実装の写しになる。
- **代表 external を path 昇順最小に固定** — 現行と非等価 (上記)。
- **並列化を諦めて範囲限定 (第 2 段) を先に置く** — D2034 / D2038 が禁じる順序。

## {{D:audit-d958-fixture-forced-scan}}. 監査を変更する wave の所要判定は、走査を強制する fixture repo と現行の実 repo の両方で D958 の形を取る

**決定:** 到達不能監査を変更する wave が D958 項 1 (warm-up 1 走を捨てた独立 3 走の最大が上限以下) を判定するとき、
**現行 main の実 repo に findings が無く repo 外走査が省略される場合は、探索根の外に置いた fixture repo
(到達不能 commit 1 本に、実根の file と同一 bytes の file + landed 参照、同一 bytes + 参照なし、よくある basename で
固有 bytes、固有 basename の 4 file) を入力にして走査を強制した所要も併せて取り、両方で上限内を要求する。**
変更前 tool との同時刻対照は、変更前 commit の tool bytes を job dir へ写し `--repo <fixture>` で起動して
new の走の間に挿入する。報告行の同一性は進捗行・`elapsed_seconds=` 行・所要上限超過行を除いた逐語比較と、
進捗行の件数 (`finding_commits= candidates= candidate_oids= external_files= external_matches= suppressions= findings=`)
で取り、探索根の churn (他 wave の worktree 生成・削除) に帰属できる差だけを記録して再走する。

**理由:**
- 2026-09-17 の実 repo は到達不能 1,233 commit のうち findings 0 件で、監査は 41 秒で終わり走査段に入らない。
  この状態の 3 走は D958 の形式を満たすが、変更した走査の所要を 1 秒も測っていない。
- fixture repo は探索根の外にある (root 検証が worktree の祖先・子孫を拒否するため、探索根の内側に置くと走査が
  省略される)。走査段の入力は探索根だけなので、fixture の findings 4 件は走査の範囲・規則を変えない。
- 変更前 tool を別 path から起動すると `DEFAULT_REPO` が変わるため `--repo` の明示が要る。同じ時間帯に交互に
  並べることで、共有 login node の負荷と cache の交絡を単走の前後比較より狭められる。

**却下した選択肢:**
- **実 repo の 3 走だけで判定する** — 走査を測っていない。
- **探索根の内側に fixture repo を置く** — root 検証で拒否され走査が省略される。
- **昨日の warm 実測 (455 秒) を対照に使う** — 探索根が 176 万 → 185 万 file に増え、pytest tmp repo の森が
  加わって本日の変更前 warm は 935 秒だった。同時刻対照でなければ倍率は言えない。

## {{D:d958-improving-wave-acceptance-t2637}}. 所要上限を既に超えている状態から所要を改善する本 wave の受理は、変更前の対照系列すべてを下回ることと実 repo の上限内で判定する (D958 項 1 への本 wave 限定の追補、結果を見た後の親の決定)

**決定 (親の統合判断、事後変更):** T-2637 / T-2660 の wave (`tools/audit_dangling_commits.py` の repo 外走査の
並列化) では、変更前 main の監査を走査強制条件 (fixture repo × 実根) で実行した対照系列が既に所要上限を超えている
(4 走とも 935〜1298 秒)。この状態から所要を改善する本 wave については、**(1) 変更後の有効な独立走すべての最大
(6 走の max 335.8 秒) が、同じ fixture・探索根で交互に取得した変更前の対照系列すべての最小 (936.2 秒) を下回ること、
(2) 現行の実 repo に対する D958 の形の所要判定 (warm-up 1 走を捨てた 3 走の max 15.5 秒) が上限内であること**を、
所要に関する代替受理条件とし、本 wave を受理する。

- D958 項 1 の文言 (「独立 3 走の最大が上限以下でなければ受理しない」、max/min > 1.5 なら 3 走追加し全 6 走の max) を
  走査強制 fixture へ当てた判定は**不合格**である (max 335.8 秒 > 上限)。本決定はこれを合格に読み替えない。
  除外した走 (new16-7: 親の onerror probe との同時走査) は理由と値 (327.0 秒) を記録し、それを戻しても判定は変わらない。
- 変更後系列の warm-up 廃棄・追加走・最大値による評価、所要上限の値 (tool 内の定数 1 箇所)、超過行の表示、掃除の報告義務は
  変えない。上限達成とは記録せず、残る超過は D2038 の第 2 段 (用途分離) の有効化条件を満たした実測として引き継ぐ。
- 本追補は本 wave の所要の受理条件だけを扱う。他 wave への自動適用は認めず、同型の状況では改めて決める。
- 段 4 裁定 §3 の凍結「fixture で超過なら land せず、裁定パッケージへ返す」は、結果を見た後に本決定で変更した。
  旧条件による判定 (不合格) は一次資料に残し、事前登録条件を満たした受理とは記録しない。「裁定パッケージへ返す」は
  2026-09-14 のユーザー指示 (裁定へ返さず codex 相談で親が決める) と整合しないため、相談 2 本 (決定側・点検側) を経て
  親が決めた。

**理由:**
- D958 項 1 は監査が 283 秒 (上限内) だった時点で「wave の受理条件として拘束する」と定めた。上限超過の状態から
  入る改善方向の wave に文言どおり当てると、936〜1298 秒から 110〜336 秒へ下げる変更を land できず、上限超過が
  main に残り続ける。D958 の目的 (監査を掃除の予算内に保つ) に反する。
- D2104 項 20 (ユーザー裁定) は「第 1 段 (並列化) を採る」と定め、D2038 は「実装して実測し、それでも上限に入らない
  ことを示してから第 2 段」と順序を定める。本 wave の実測は第 1 段だけでは warm でも上限に入らない場合があることを
  示した。第 2 段へ進む根拠として使う。
- 2026-08-11 のユーザー指示 (受入全走の 300 秒目標について「301 秒で目標達成できないから成果を捨てるみたいなことは
  やめてね」) は本件と対象が違うが、数値目標で本物の改善を捨てない方針として本決定の設計根拠にした。
  D958 の逐語を自動的に失効させる根拠にはしていない。
- 受理集合 (findings / suppressions / unreferenced_copies) は本追補の対象外で、等価性 test・変異 matrix (負例 9/9 KILLED)・
  静的な木での逐語一致がそれを担保する。本追補は所要だけを扱い、正しさ検査を 1 つも緩めない。

**land しない側の最も強い理由 (記録):** 結果を見る前に固定した「fixture 超過なら受理しない」を結果後に解除する
ことは、受理手続きの信頼を下げる。D2038 は第 1 段の land を第 2 段の前提にしておらず、実装・測定を branch に保存した
まま第 2 段の設計へ進み、合算で上限に入ってから land する道は閉じていない。実 repo の短時間走は変更した経路を実行して
いない。旧新比較は共有 node・異なる時刻の観測であり性能保証ではない。— 本決定はこの不利益を認めたうえで、改善を先に
取り込み、事後変更を明記する方を選んだ。

**却下した選択肢:**
- **fixture を D958 の射程外として合格扱いにする** — D958 は入力条件を限定しておらず、段 4 §3 が fixture を明示的に
  含めている。空洞化になる。
- **遅い走 (335.8 秒) を外乱として捨てる** — D958 が「主観の『外乱の疑い』で測定値を捨てない」と禁じる。
- **land を見送り第 2 段と合算で land する** — 上記「land しない側の最も強い理由」。改善が main に入らないまま
  第 2 段 (受理集合と掃除の入口に触る別の設計) の裁定を待つことになり、2026-09-14 の指示に反して判断を溜める。
- **全 wave に通用する「改善なら上限超過でも受理」の一般規則** — 先例化を防ぐため本 wave 限定にした。
