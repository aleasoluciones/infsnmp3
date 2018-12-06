# -*- coding: utf-8 -*-

import logging
from pysnmp.smi import builder, view, error
import infcommon
from infsnmp import exceptions



class MIBSymbol(infcommon.AttributesComparison):

    def __init__(self, base_oid, labels, node_suffixes):
        self.base_oid = base_oid
        self.labels = labels
        self.node_suffixes = node_suffixes

    @property
    def symbol(self):
        return self.labels[-1]

    def __str__(self):
        return '{symbol} {indexes}'.format(symbol=self.symbol, indexes=self._indexes or '-')

    @property
    def _indexes(self):
        return [str(suffix) for suffix in self.node_suffixes]


class PyOIDConverter(object):
    DEFAULT_MODULES = ['SNMPv2-MIB']

    def __init__(self, directory, modules_to_load):
        self.directory = directory
        self.modules_to_load = modules_to_load
        self.mib_view_controller = None

    def to_symbol(self, oid):
        self._initialize_mib_view_controller()
        base_oid, labels, node_suffixes = self._decompose_oid(oid)
        return MIBSymbol(self._make_oid_from_parts(base_oid), labels, self._convert_to_str_tuple(node_suffixes))

    def _convert_to_str_tuple(self, tuple_):
        return (str(part) for part in tuple_)

    def _make_oid_from_parts(self, parts):
        return '.'.join(self._convert_to_str_tuple(parts))

    def _decompose_oid(self, oid):
        try:
            return self.mib_view_controller.getNodeName(self._convert_to_tuple_oid(oid))
        except error.NoSuchObjectError:
            raise exceptions.InvalidOIDError()

    def _convert_to_tuple_oid(self, oid):
        return tuple(int(part) for part in oid.split('.'))

    def _initialize_mib_view_controller(self):
        if not self.mib_view_controller:
            mib_builder = builder.MibBuilder()
            mib_builder.setMibSources(*self._make_mib_sources(mib_builder))
            self._load_modules(mib_builder)
            self.mib_view_controller = view.MibViewController(mib_builder)

    def _make_mib_sources(self, mib_builder):
        return mib_builder.getMibSources() + (builder.DirMibSource(self.directory),)

    def _load_modules(self, mib_builder):
        for module in self.DEFAULT_MODULES + self.modules_to_load:
            self._load_mib_module(mib_builder, module)

    def _load_mib_module(self, mib_builder, module):
        try:
            mib_builder.loadModules(module)
        except error.SmiError as exc:
            logging.error("Error loading mib module {module} {exc}".format(module=module, exc=exc))
