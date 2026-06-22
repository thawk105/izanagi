set terminal pngcairo size 900,540 noenhanced font "sans,11"
set output "p2-2-fitness-write-heavy.png"
set title "P2-2 silo fitness — write-heavy (skew0.9, 48t, 1,000,000 rec)"
set xlabel "genome (B=BACK_OFF, L/T=no-wait policy, W=WAL)"
set ylabel "median throughput (tps)"
set grid
set key outside right top
set style fill solid 0.6
set boxwidth 0.6 relative
set yrange [0:*]
set xtics rotate by -30
unset key
plot "p2-2-fitness-write-heavy.dat" using 2:xtic(1) with boxes axes x1y1 title "median tps"
