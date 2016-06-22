#!/usr/bin/env python

from scapy.all import *
import sys
import argparse


def client(itf):
    msg = "HELLO WORLD"
    eth = Ether(src=" 7e:a9:71:40:ef:9c", dst="1e:1a:3c:ae:5f:95")
    ip = IP(src="10.0.0.1", dst="10.0.0.2")
    udp = UDP(sport=34951, dport=34952)
    p = eth / ip / udp / "Hello"
    hexdump(p)
    sendp(p, iface = itf)

def handle(x):
    hexdump(x)

def server(itf):
    sniff(iface = itf, prn = lambda x: handle(x))

def main():
    parser = argparse.ArgumentParser(description='receiver and sender to test P4 program')
    parser.add_argument("-s", "--server", help="run as server", action="store_true")
    parser.add_argument("-c", "--client", help="run as client", action="store_true")
    parser.add_argument("-i", "--interface", default='veth1', help="bind to specified interface")
    args = parser.parse_args()

    if args.server:
        server(args.interface)
    elif args.client:
        client(args.interface)
    else:
        parser.print_help()

if __name__=='__main__':
    main()