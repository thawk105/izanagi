set terminal pngcairo size 900,540 noenhanced font "sans,11"
set output "calibration_t48_skew0p9_rr50_rmw0_sweep.png"
set title "Calibration sweep (linux-baremetal, 48 threads)"
set xlabel "records (ycsb_tuple_num, log2)"
set ylabel "LLC miss rate"
set grid
set key outside right top
set logscale x 2
set y2label "maxrss (kB)"
set y2tics
set ytics nomirror
plot "calibration_t48_skew0p9_rr50_rmw0_sweep.dat" using 1:2 with linespoints axes x1y1 title "miss rate", \
     "calibration_t48_skew0p9_rr50_rmw0_sweep.dat" using 1:3 with linespoints axes x1y2 title "maxrss (kB)"
