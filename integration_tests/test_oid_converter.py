# -*- coding: utf-8 -*-

import os.path
import unittest
from hamcrest import *
from infsnmp import oid_converter, exceptions

PYMIBSDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../pymibs/'))


class PyOIDConverterTest(unittest.TestCase):

    def setUp(self):
        self.converter = oid_converter.PyOIDConverter(PYMIBSDIR, ['JUNIPER-VLAN-MIB', 'IP-MIB'])

    def test_converts_oid_to_symbol(self):
        mib_symbol = self.converter.to_symbol('1.3.6.1.2.1.4.20.1.4.192.168.112.1')

        assert_that(mib_symbol.symbol, is_('ipAdEntBcastAddr'))
        assert_that(mib_symbol.base_oid, is_('1.3.6.1.2.1.4.20.1.4'))
        assert_that(mib_symbol.node_suffixes, has_items('192', '168', '112', '1'))

    def test_converts_invalid_oid_raises_exception(self):
        self.assertRaises(exceptions.InvalidOIDError, self.converter.to_symbol, '9')
