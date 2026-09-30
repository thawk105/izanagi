1. **高 — P1 の受理集合は同値ではない。** 現行は cacheable と判定した最初の観測で実ファイルを SHA256 し、その値を process 内 cache に入れる。一方、提案は最初から index blob を値にする（`output_snapshot_ignores.py:603–629`）。具体的には、並行書込みや racy clean により、前観測時の実 bytes が A、index blob が B なのに `git status` が clean と答えた場合を作れる。後観測時に実 bytes を B とし、mode 変更で fallback させると、現行は A 対 B で赤、新比較器は blob B 対 bytes B で緑になる。逆に、前後の実 bytes が A で、前観測だけ誤って clean、後観測が fallback なら、現行は緑、新比較器は blob B 対 A で赤になる。**brief 3 の「同値」、plan P1.6 への反論。** D1709 に従い「同値」として land せず、こうした状態を契約から明示的に除けるか、実受入の wall 改善が走間ばらつきを超えるかを先に判定する。D1063/D1064 の ignore・tracked 規則を共有 iterator で保つ方針自体は妥当だが、この差は解消しない。

2. **中 — P1 の混在行照合は欠損 object と観測時刻で狭まる。** 前後とも実 bytes が同じで、前行だけ index、後行だけ SHA256 となる場合、前観測後に blob object が消えると、現行は実 bytes の digest 同士で緑になり得るが、plan P1.3 の `git cat-file` は赤になる。さらに他 test の `git add` が二観測間に index を更新すると、同じ実 bytes でも blob ID 比較が異なる結果を出し得る。根拠は現行の初回実読取（`output_snapshot_ignores.py:616–620`）と plan P1.3/P1.6。**修正:** 欠損 object・index 更新・並行 worker 書込み・racy status を同値性の例外として一次資料に列挙し、焦点テストにも前後の index 変化を入れる。blob ID のみの比較では二時点の実 bytes を証明できない。

3. **高 — P2 は consumer のない shard に新しい失敗経路を作る。** `_early_memo_selected` は shard の割付前に判定され（`conftest.py:2371–2388`）、選択は collection 後である（`acceptance_shards.py:895–912`）。したがって P2 は shard-1/2 でも二つの base を構築する。そこで builder が失敗すれば終了処理から赤になり、hang すれば thread の無期限 `join()` で停止し得る（現行終了形は `conftest.py:2491–2498,2538–2557,3027–3040`）。180 秒は可視 output の **完成待ちだけ**の上限で、builder の上限ではない（`test_s8b_oracle_driver.py:1012–1020`）。**brief 4、plan P2.3–4 への反論。** `check_acceptance_reds` の具体的な分類は射影資料から確認できなかったが、少なくとも shard の pytest rc／完走判定は変わる（`acceptance_shards.py:691–705`）。consumer 不在 shard の失敗と停止を事前登録の失敗分類に加え、builder の終了境界と cleanup を検証する。

4. **中 — P2 の lock 順は成立し得るが、終了順を実装で固定する必要がある。** controller が thread 前に `workers.lock` の共有 lock を取得し、worker は import 時に参加する設計は、早期に終わる worker による削除を防ぐ（`test_s8b_oracle_driver.py:924–943,975–993`）。key ごとの排他 lock も既存の `get()` が持つ（同 `:945–972`）。ただし controller thread が可視 output の `result.json` を待つ間に写しを先に cleanup すると失敗し、`join()` が返らない builder では controller の参加も撤去されない。**plan P2.2–4 への反論。** prewarm の join・error 回収・`bases.close()` を可視 output cleanup より前に行い、失敗時にもその順序をテストする。`_early_memo_selected` をそのまま使う限り、焦点走・単独走・絞り込み・非受入 xdist が従来経路になるという plan P2.5 の前提は反証できなかった。

5. **中 — 項 6 の全 hit 指紋は過剰で、提案範囲でも完全性を示せない。** P2 は既存の共有 base の producer を早めるだけで、consumer は従来どおり `copytree` と `deepcopy` を受ける（`test_s8b_oracle_driver.py:1041–1063`）。既存の独立コピー検査（同 `:1231` 以降）に、共有 base 自体の bytes／tree が二つの consumer の変異後も不変である検査を足すのが md_6 項 3 の最小形である。`git status`・HEAD・index・`lstat` の hit 指紋では ignored file の内容や同一 metadata に戻した変更を検出できない。一方、全 bytes の hash は各 hit に大きな読取費用を足す。**brief 6、plan 項 6 への反論。** hit 時指紋を採るなら検出範囲と実測費用を限定して記し、「全状態の改変検出」とは主張しない。

6. **中 — P1 と P2 の同時投入では効果を帰属できない。** 群 A/B の testcase 所要合計は、flock 待ち、CPU・I/O 競合、割付変化を含むため、各変更の wall 寄与には分解できない。D2271 は候補 (a) と (b) の同時投入を効果分離不能として退け、shard-1 が 313.0／267.8 秒に伸びた原因も未分離と記録している（`decisions.md:73083–73105`）。**brief 9、plan 総括への反論。** P1 のみ／P2 のみを含む段階的 tip、または同一 SHA の個別 opt-out を使い、各腕で shard-0 の W・span・占有と shard-1/2 の W、collection と base 構築の時刻、CPU／I/O、/tmp 使用量を測る。群合計は診断量として残す。約 1.7 node 時間という brief 9 の見積りには、この分離走、焦点走、変異 matrix、失敗時の再走を含めた再計算が必要である。

7. **中 — 総仕事量から最忙 worker の短縮は導けない。** baseline では最忙 worker 上の A+B は中央値 39.28 秒で、10 走中 4 走は 0 秒である（`baseline/result.txt:141–152`）。span 最大 worker と占有最大 worker が一致したのも 2/10 走だけ（`baseline/span_result.txt:32`）。list scheduling では総仕事量を減らすと平均負荷の下界は下がるが、長い別 item、排他待ち、割付順が決める最大値の短縮は保証しない。**brief 1–3、9 への反論。** 「約 500 秒／走」は shard-0 の仕事量の条件付き推定と書き、W と span の改善は対照実測だけで結論づける。

8. **中 — 実測値と推定値が混在している。** 201.3／213.1 秒と shard-1/2 の 160.0／160.6 秒は集計と一致する（`baseline/span_result.txt:32–34`）。67.44／30.47／31.62／0.10 秒、154.16／3.17／149.83／24.85／31.32 秒も log と一致する（`probe1/run.log:31–39`、`probe2/run.log:38–44`）。ただし probe4 の投影された `run.log` が直接示すのは単独走 112.99 秒だけで、98 秒と 47.4＋14.6＋33.4 秒の内訳はこの必読実測 file から照合できない（`probe4/run.log:20–31`）。1,000〜1,800 秒の flock 待ち、各 worker が初回約 37 秒を払い、約 500 秒減るという値も、`-n 0`／`-n 1` から 48 worker の受入への外挿である。**brief 2–4 への反論。** 内訳の直接計器を示し、推定には「外挿」と明記する。対照では work と wall を分けて測る。

9. **低 — P3 の見送り自体は合理的だが、成果物影響を明確にする。** active-v2 の emitter 共有は本波で実装しない判断に、反証できる根拠は提示されていない。一方で brief 5 の約 50 秒も単独 probe からの外挿である。**brief 5、11 への意見。** DW-G05 には「P3 未実装、nodeid・受理集合・成果物 bytes は不変、残る費用は受入で未測定」と書く。P1/P2 の実測改善と混ぜて達成済みとは記さない。

**反証できず:** D1063/D1064 の除外・tracked 規則を現行のまま共有する実装方針、P2 の既存 key と `get()` の再利用、非選択走を `_early_memo_selected` で外す方針、P3 を今回見送る判断。

## 総括

現 plan のまま P1/P2 を同時 author へ渡すことは推奨しない。
P1 は受理集合の非同値を明記し、D1709 の効果条件で採否を決める。
P2 は consumer 不在 shard の失敗・停止と終了順を先に検証する。
効果は個別の対照腕で測り、項 6 は共有 base の独立コピー検査を最小形とする。