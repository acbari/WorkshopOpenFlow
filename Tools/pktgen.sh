#!/bin/bash
#sleep 5
modprobe pktgen
if [ "$1" = "" ];then
   ethport='h1-eth0'
else
   ethport=$1
fi
if [ "$2" = "" ];then
   pktcount=3000
else
   pktcount=$2
fi
if [ "$3" = "" ];then
   pktsize=64
else
   pktsize=$3
fi

function pgset() {
    local result
    echo $1 > $PGDEV
    result=`cat $PGDEV | fgrep "Result: OK:"`
    if [ "$result" = "" ]; then
         cat $PGDEV | fgrep Result:
    fi
}



function pg() {
    echo inject > $PGDEV
    cat $PGDEV
}


echo "Adding devices to run".
PGDEV=/proc/net/pktgen/kpktgend_0
pgset "rem_device_all"
pgset "add_device $ethport"
#pgset "max_before_softirq 1"


# Configure the individual devices

echo "Configuring devices"



PGDEV=/proc/net/pktgen/$ethport



pgset "clone_skb 0"

pgset "pkt_size $pktsize"

#pgset "flag IPSRC_RND"

pgset "src_min 10.0.0.1"

pgset "src_max 10.0.0.1"

#pgset "src 192.168.90.122"

#pgset "src 10.0.0.1"

#pgset "dst 192.168.90.123"

#pgset "dst 10.50.50.2"

#pgset "flag IPDST_RND"

pgset "dst_min 10.0.0.2"

pgset "dst_max 10.0.20.254"

#pgset "flag MACSRC_RND"

pgset "src_mac 00:00:00:00:00:01"

#pgset "src_mac_count 1000000"

#pgset "flag MACDST_RND"

pgset "dst_mac 00:00:01:00:00:01"

#pgset "dst_mac_count 1000000"

#pgset "flag UDPSRC_RND"

pgset "udp_src_min 2000"

pgset "udp_src_max 9000"

#pgset "flag UDPDST_RND"

pgset "udp_dst_min 2000"

pgset "udp_dst_max 9000"

pgset "delay 1000000"

#delay in ns, 1000 000 ns = 1000 mikro = 1 ms 

#pkt count = 60 000 x 1 ms = 60 s = 1 minute

#pktsize = 64, delay 1ms => 1 K pkt per seconds

#pktsize = 64, delay 0.1ms => 10 K pkt per seconds

pgset "count $pktcount"



# Time to run



PGDEV=/proc/net/pktgen/pgctrl

echo "interface:$ethport"

echo "pktcount:$pktcount"

echo "pkgsize:$pktsize"

echo "Running... ctrl^C to stop"



pgset "start"



echo "Done"


