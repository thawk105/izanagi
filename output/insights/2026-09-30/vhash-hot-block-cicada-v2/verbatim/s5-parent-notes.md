# 段 5 親メモ — B-post の pointer 再利用 (ABA) の論証 (統合 1 = 2ee178f32 の post overlay を親が読んで書いた)

## 懸念
REUSE_VERSION=1 では GC が切り離した版の object が同じ address のまま新しい版として再利用され、別の wts で列へ再挿入されうる。
B-post の読み手は hot の copy から X = ptr[i] を選び、隣接確認 `ptr[i-1]->next_ == ptr[i]` を pointer の等値で行う。
もし copy の後に X が GC で切り離され、同じ address が新しい版 X' として ptr[i-1] の直後へ再挿入されると、隣接確認が通って
読み手は X' (wts は hot の wts[i] と違い、trts より新しいかもしれない) を X として扱う。

## 親の論証 (攻撃対象)
1. X が読み手の生存中に再利用されるには、GC の切り離し点 D (確定版、D.wts < MinRts) が X より物理的に新しい必要がある。
2. D.wts < MinRts ≤ 読み手の rts (読み手は begin で rts を ThreadRtsArray に公開済み)。MinWts は各 thread の現 wts の最小なので、
   読み手の rts = (begin 時の MinWts) − 1 ≥ D.wts ならば、その MinWts の計算時点で D の書き手はすでに次の tx へ進んでいた
   (D の書き手の tx の間は ThreadWtsArray = D.wts で MinWts ≤ D.wts)。よって D の書き手の tx は読み手の begin より前に終わっている。
3. B-post の書き手は CAS 後の hot への挿入を validation の中 (commit / abort の確定より前) で終える。よって D は読み手の begin より前に hot に入っている。
4. D が読み手の copy より前に hot から消えるのは、より新しい切り離し点 D2 による trim (D.wts < D2.wts) か、満杯で落とされる場合 (D より新しい版が K 個以上) だけ。
   前者なら D2 に同じ論証を当てる。後者なら hot の全件が D より新しいので X (D より古い) も hot に居ない。
5. よって読み手の copy には D (か D2) が X より前に居る。D.wts ≤ rts ≤ trts なので、読み手は D か D より新しい版を選び、X を選ばない。矛盾。
6. 同じ論証で、隣接確認で読む ptr[i-1] (wts > trts ≥ rts ≥ MinRts > 切り離し点) も再利用されない。

## 確かめていないこと
- MinWts の単調性 (leader の計算の並行性)、ThreadWtsArray / ThreadRtsArray の公開と leader の読みの memory order。stock の寿命前提と同じで、独立には証明していない。
- INLINE_VERSION_OPT の inline_ver_ の再利用 (GC で unused に戻り、次の write で同じ address が使われる) も同じ論証に入るか (入ると考えるが未確認)。
