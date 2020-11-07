#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: NBFM_2
# GNU Radio version: 3.8.0.0

from gnuradio import analog
from gnuradio import audio
from gnuradio import blocks
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import osmosdr
import time

class NBFM_2(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "NBFM_2")

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 1.5e6
        self.quadrature = quadrature = 240e3

        ##################################################
        # Blocks
        ##################################################
        self.rtlsdr_source_0 = osmosdr.source(
            args="numchan=" + str(1) + " " + "rtl=0"
        )
        self.rtlsdr_source_0.set_time_unknown_pps(osmosdr.time_spec_t())
        self.rtlsdr_source_0.set_sample_rate(1500015)
        self.rtlsdr_source_0.set_center_freq(154.355e6, 0)
        self.rtlsdr_source_0.set_freq_corr(0, 0)
        self.rtlsdr_source_0.set_gain(20, 0)
        self.rtlsdr_source_0.set_if_gain(20, 0)
        self.rtlsdr_source_0.set_bb_gain(20, 0)
        self.rtlsdr_source_0.set_antenna('', 0)
        self.rtlsdr_source_0.set_bandwidth(100e3, 0)
        self.rational_resampler_xxx_2 = filter.rational_resampler_ccc(
                interpolation=4,
                decimation=25,
                taps=None,
                fractional_bw=None)
        self.rational_resampler_xxx_1 = filter.rational_resampler_fff(
                interpolation=7,
                decimation=8,
                taps=None,
                fractional_bw=None)
        self.rational_resampler_xxx_0 = filter.rational_resampler_fff(
                interpolation=21,
                decimation=20,
                taps=None,
                fractional_bw=None)
        self.low_pass_filter_0 = filter.fir_filter_ccf(
            1,
            firdes.low_pass(
                1,
                240000,
                110e3,
                10e3,
                firdes.WIN_HAMMING,
                6.76))
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_ff(.4)
        self.audio_sink_0 = audio.sink(44100, "pulse", True)
        self.analog_pwr_squelch_xx_0 = analog.pwr_squelch_cc(-47, 1e-4, 0, False)
        self.analog_nbfm_rx_0 = analog.nbfm_rx(
        	audio_rate=48000,
        	quad_rate=240000,
        	tau=75e-6,
        	max_dev=5e3,
          )
        self.analog_ctcss_squelch_ff_0 = analog.ctcss_squelch_ff(48e3, 136.5, 0.005, 0, 0, False)



        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_ctcss_squelch_ff_0, 0), (self.rational_resampler_xxx_0, 0))
        self.connect((self.analog_nbfm_rx_0, 0), (self.analog_ctcss_squelch_ff_0, 0))
        self.connect((self.analog_pwr_squelch_xx_0, 0), (self.analog_nbfm_rx_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.audio_sink_0, 0))
        self.connect((self.low_pass_filter_0, 0), (self.analog_pwr_squelch_xx_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.rational_resampler_xxx_1, 0))
        self.connect((self.rational_resampler_xxx_1, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.rational_resampler_xxx_2, 0), (self.low_pass_filter_0, 0))
        self.connect((self.rtlsdr_source_0, 0), (self.rational_resampler_xxx_2, 0))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate

    def get_quadrature(self):
        return self.quadrature

    def set_quadrature(self, quadrature):
        self.quadrature = quadrature



def main(top_block_cls=NBFM_2, options=None):
    tb = top_block_cls()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()
    while True:
        time.sleep(3600)
    tb.stop()
    tb.wait()


if __name__ == '__main__':
    main()
