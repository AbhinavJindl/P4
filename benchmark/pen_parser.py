#!/usr/bin/env python

import os
from subprocess import call, Popen, PIPE
import shlex
import time
import p4gen
import argparse

from benchmark import P4Benchmark

class BenchmarkParser(P4Benchmark):

    def __init__(self, nb_header, offer_load):
        parent_dir = 'result/parser/'
        directory = '{0}/{1}/{2}'.format(parent_dir, nb_header, offer_load)
        super(BenchmarkParser, self).__init__(parent_dir, directory, offer_load)
        self.nb_header = nb_header
        self.nb_field = 1
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

    def run_packet_generator(self):
        cmd = 'sudo {0} -p {1} -i veth4 -c {2} -t {3}'.format(self.pktgen,
            'output/test.pcap', self.nb_packets, self.offer_load)
        print cmd
        args = shlex.split(cmd)
        out_file = '{0}/latency.csv'.format(self.directory)
        err_file = '{0}/loss.csv'.format(self.directory)
        out = open(out_file, 'w+')
        err = open(err_file, 'w+')
        p = Popen(args, stdout=out, stderr=err)
        p.wait()
        out.close()
        err.close()

    def compile_p4_program(self):
        ret = p4gen.bm_parser.benchmark_parser(self.nb_header, self.nb_field)
        assert (ret == True)
        prog = 'main'
        json_path = 'output/%s.json' % prog
        out_file = '{0}/p4c.log'.format(self.directory)
        with open(out_file, 'w+') as out:
            p = Popen([self.p4c, 'output/%s.p4' % prog , '--json', json_path],
                stdout=out, stderr=out)
            p.wait()
            assert (p.returncode == 0)

    def run_behavioral_switch(self):
        prog = 'main'
        json_path = 'output/%s.json' % prog
        commands = 'output/commands.txt'
        cmd = 'sudo {0} {1} -i0@veth0 -i1@veth2 -i 2@veth4 {2}'.format(self.switch_path,
                json_path, self.log_level)
        print cmd
        args = shlex.split(cmd)
        out_file = '{0}/bmv2.log'.format(self.directory)
        with open(out_file, 'w') as out:
            out.write('Number of packets: %d\n' % self.nb_packets)
            out.write('offered load:  %d\n' % self.offer_load)
            self.p = Popen(args, stdout=out, stderr=out, shell=False)
        assert (self.p.poll() == None)
        # wait for the switch to start
        time.sleep(2)
        # insert rules: retry 3 times if not succeed
        self.add_rules(json_path, commands, 3)


def main():
    parser = argparse.ArgumentParser(description='P4 Benchmark')
    parser.add_argument('-n', '--nb-headers', default=5, type=int,
                        help='number of headers from start')
    args = parser.parse_args()

    nb_headers = args.nb_headers

    while(nb_headers <= 40):
        offer_load = 100000
        p = BenchmarkParser(nb_headers, offer_load)
        # compile
        p.compile_p4_program()
        p.start()
        while (p.has_lost_packet() != True):
            offer_load += 100000
            p = BenchmarkParser(nb_headers, offer_load)
            p.start()

        nb_headers += 5
    p.run_analyser()

if __name__=='__main__':
    main()
