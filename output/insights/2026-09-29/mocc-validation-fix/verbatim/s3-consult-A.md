## 所見 — 修理の正しさ (1〜3)

- **should — 証明の範囲を限定する。** 長さ 2・両辺 rw の閉路について、案 A と案 B を検算した結果、指定された楽観読みの形では両方 commit する interleaving は残らない。T1 が `x` を読み `y` を書き、T2 が `y` を読み `x` を書くとする。両者は先に write lock を取る。T1 の `x` の lock 読みが T2 の施錠前なら、T2 の `y` の lock 読みは T1 の施錠後になるため、T2 が通るには T1 の公開・解錠後を読む必要があり、後続の版読みで abort する。T1 の lock 読みが T2 の解錠後なら、T1 自身の後続の版読みが T2 の新しい版を捉えて abort する。案 A は後続の再読、案 B は唯一の版読みがこの役割を持つ。根拠: `cc/mocc/transaction.cc:1014–1024,1031–1061,1306–1320`、一次資料 `t2872-mocc-g2-split/README.md:30–38`。ただしこれは別 key の楽観読み、自己 write なし、版の ABA なし、lock／版の観測が acquire・release の順序に従う、という範囲の論証である。範囲を書かずに「MOCC の G2 全般を排除」と記録すると、成果物の主張が実証範囲を超える。直し方: 修理 commit と記録の主張をこの witness の形に限定する。

- **should — 版の単調性は無条件には成立しない。** `Tidword` の `tid` は 31 bit、`epoch` は 32 bit で、`writePhase` は最大版の `tid++` 等から commit 版を選ぶ。通常の同一 record への連続公開は前進するが、周回と record の再生成まで含む ABA 不在は証明できない。根拠: `cc/mocc/include/tuple.hh:14–30,74–90`、`cc/mocc/transaction.cc:1141–1155,1250–1285,1306–1307`。ABA が起きれば案 A の V1=V2 は途中の公開を隠し、G2 排除の論証が崩れる。直し方: plan `s2-plan.md:28` の限定を採用し、無条件の保証とは書かない。

- **should — 案 A の「Silo 同値」は通過条件の同値に限る。** 案 A は元の V1 一致・lock 検査通過に V2 一致を足すため、同じ観測列での受理条件は縮む。案 B は元の版読みより前に lock 読みを移すため、L で未施錠を見た後、他者が施錠して版をまだ公開していない実行を受理し得る。元の順序なら後段の L が施錠を見て拒否し得るので、親 P1 の主張は正しい。一方、案 A では L 時点で旧版・未施錠だった後、他者が公開・解錠して V2 が新しい版を読むと abort する。Silo の単一 word 検査は L 時点なら通過するため、全スケジュールの受理結果は一致しない。根拠: `cc/mocc/transaction.cc:1031–1061`、`cc/silo/transaction.cc:453–478`、`s1-brief.md:9–10`、`s2-plan.md:24–26`。この余分な拒否が多ければ、修理後の版不一致 abort が増え、同条件の trace 無し commit 数が下がる方向に現れるはずだが、量は静的には言えない。直し方: 案 A を採り、「L の瞬間に成立する検査条件が Silo に対応する」と表記する。

- **nit — `max_rset_` を `check` から取る変更に反対する根拠は見つからなかった。** 自分の write set にもある read item は、validation 前に自分が write lock を取得し、lock 検査でも自己 write を例外扱いする。その間に別 writer が正当に公開する経路はない。元の無検査の再読は、別 record では L 後に公開された版を commit tid に取り込めるが、それは検査した読取版ではない。`check` を使えば Silo と同様、検査した版より大きい候補を `tid_a.tid++` で作る。根拠: `cc/mocc/transaction.cc:1014–1024,1045–1061,1141–1155`、`cc/silo/transaction.cc:453–478,561–586`。放置すると修理後も commit tid の根拠が未検査の版になり、記録の「検査した版から tid を決める」という主張とずれる。直し方: plan の `max_rset_ = max(max_rset_, check)` を維持する。元の再読を自己 write のために必要とした証拠は現物にない。

## 所見 — 残る経路 (4)

- **should — cold read の torn read は別経路として残る。** read phase は lock が `W_LOCKED` でないことを見て payload を複写し、前後の版一致を調べる。この前後で writer が payload を変更し、版公開前に複写が終わる経路は、validation の再読だけでは payload の一貫性を証明しない。既往の診断 patch も cold 側の lock 検査を別 hunk として含む。根拠: `cc/mocc/transaction.cc:315–363,1250–1251,1306–1320`、`mocc-close-version-counter-gap.patch:4–17`、一次資料 `t2872-mocc-g2-split/README.md:89–98`。**本 wave で同時修理する必要はない**。今回の成果物は validation の隙間を直した commit と、その形の G2 の観測に限定し、torn read 全般を直したとは書かない。

- **nit — hot read・自己 write・DELETE／INSERT・node set・MQLOCK へ証明を拡張できない。** hot read は read lock を取得し、自己 write は validation の lock 条件から除外される。DELETE／INSERT は absent と木の変更を伴い、node set は別検査である。今回の CMake は `RWLOCK` を指定し、`MQLOCK` 側は別の条件分岐にある。根拠: `cc/mocc/transaction.cc:279–313,355–363,458–476,485–524,1064–1071,1254–1285`、`cc/mocc/CMakeLists.txt:1–10`、`cc/mocc/include/tuple.hh:64–70`。NO_WAIT 相当の試行取得は RWLOCK 実装で失敗時 abort となるが、今回の楽観 read の窓とは別である（`cc/mocc/transaction.cc:769–798`、`cc/mocc/lock.cc:950–1001`）。放置時に変わるのは修理 commit の対象範囲ではなく、成果物の主張の上限。直し方: これらを今回の G2 排除の証明対象に含めない。

## 所見 — 検証の実効性 (5)

- **should — 修理後の commit 側 class A=0 は、ほぼ構造上の帰結である。** Vmid が V1 と違えば、版が単調に進む範囲では L 後の修理用 V2 も V1 と違い、当該取引は commit できない。したがって class A=0 だけでは修理が実際に割り込みを捕えて abort したことを測れない。根拠: `s2-plan.md:5–24,83–91`、一次資料 `t2872-mocc-g2-split/README.md:40–46`。放置すると記録が恒真に近い陰性値を修理効果の独立した証拠として扱う。直し方: 修理用 **V2≠V1 による abort 件数**を一つ記録し、同時刻の修正前 F の commit 側 class A 件数および修理後の G2 0/112 と並べる。件数の同一性までは要求しない。

## 推奨する修理の形 (実文) と理由

`cc/mocc/transaction.cc` の read set validation で、既存の V1 比較と RWLOCK 検査を残し、その直後に版を acquire で再読する。(epoch, tid) が V1 と違えば既存の版不一致と同じ経路で abort する。`max_rset_` には再読した未検査値ではなく V1 の `check` を使う。`s2-plan.md:7–22` の hunk がこの形に当たる。受理条件を追加で絞り、上記の G2 の窓を閉じるため、案 B より依頼の制約に合う。

## 総括

**must-fix に当たる破綻は、指定された RWLOCK・楽観読みの G2 については見つからなかった。** 案 A の実装形を支持する。修理効果の記録では、G2 0/112 と修理による版不一致 abort を主な観測にし、class A=0 は修理条件から予測される値として扱う。今回は静的検査のみで、ファイル変更・build・テストは行っていない。